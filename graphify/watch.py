# monitor a folder and auto-trigger --update when files change
from __future__ import annotations
import json
import logging
import sys
import time
from pathlib import Path


from graphify.detect import CODE_EXTENSIONS, DOC_EXTENSIONS, PAPER_EXTENSIONS, IMAGE_EXTENSIONS

_WATCHED_EXTENSIONS = CODE_EXTENSIONS | DOC_EXTENSIONS | PAPER_EXTENSIONS | IMAGE_EXTENSIONS
_CODE_EXTENSIONS = CODE_EXTENSIONS


def _load_persisted_labels(out: Path, communities: dict) -> dict:
    """Read community labels from .graphify_labels.json if present.

    Falls back to {cid: "Community N"} on missing file or corrupt JSON.
    """
    labels_path = out / ".graphify_labels.json"
    fallback = {cid: f"Community {cid}" for cid in communities}
    if not labels_path.exists():
        return fallback
    try:
        raw = json.loads(labels_path.read_text(encoding="utf-8"))
        loaded = {int(k): v for k, v in raw.items() if int(k) in communities}
        return loaded or fallback
    except (json.JSONDecodeError, ValueError) as exc:
        logging.warning("[graphify watch] Corrupt .graphify_labels.json (%s); using fallback", exc)
        return fallback


def _rebuild_code(
    watch_path: Path,
    *,
    follow_symlinks: bool = False,
    out_dir: Path | None = None,
    directed: bool = False,
    cache_dir: Path | None = None,
) -> bool:
    """Re-run AST extraction + build + cluster + report for code files. No LLM needed.

    Returns True on success, False on error. ``out_dir`` overrides the
    default ``<watch_path>/graphify-out`` location so callers can direct
    output into a shared overlay directory (for example
    ``.claude/architecture/graph/_global/graphify-out``). ``directed``
    forwards to ``build_from_json`` so reverse-reachability queries on
    the resulting ``graph.json`` stay meaningful. ``cache_dir`` overrides
    the parser cache location; when omitted it defaults to
    ``<out_dir>/cache/`` so cache never pollutes the source tree when the
    caller redirects outputs.
    """
    watch_path = watch_path.resolve()
    try:
        from graphify.extract import extract
        from graphify.detect import detect
        from graphify.build import build_from_json
        from graphify.cluster import cluster, score_all
        from graphify.analyze import god_nodes, surprising_connections, suggest_questions
        from graphify.report import generate
        from graphify.export import to_json, to_html
        from graphify.cache import cache_dir as _resolve_cache_dir

        detected = detect(watch_path, follow_symlinks=follow_symlinks)
        code_files = [Path(f) for f in detected['files']['code']]

        if not code_files:
            print("[graphify watch] No code files found - nothing to rebuild.")
            return False

        # Resolve out + cache locations up-front so cache follows --out-dir
        # automatically, and eagerly materialize the cache dir so the per-file
        # extract loop hits an existing path. Cache keys still use watch_path
        # for relative-path stability (see cache.file_hash).
        out = out_dir.resolve() if out_dir is not None else (watch_path / "graphify-out")
        cache_location = _resolve_cache_dir(
            watch_path,
            cache_override=cache_dir if cache_dir is not None else (out / "cache"),
        )

        result = extract(code_files, cache_root=watch_path, cache_override=cache_location)

        # Merge route / HTTP overlay nodes and edges produced by
        # graphify.routes and graphify.http_calls. These scanners walk the
        # source root independently of `detect()` but skip the same set of
        # heavy directories (node_modules, .next, …). Overlay results stack
        # on top of AST nodes so FE/BE bridges are visible in graph.json.
        try:
            from graphify.routes import scan as _scan_routes
            routes_res = _scan_routes(watch_path)
            result["nodes"].extend(routes_res.nodes)
            result["edges"].extend(routes_res.edges)
        except Exception as exc:
            print(f"[graphify watch] routes scan skipped: {exc}")
        try:
            from graphify.http_calls import scan as _scan_http_calls
            http_res = _scan_http_calls(watch_path)
            result["nodes"].extend(http_res.nodes)
            result["edges"].extend(http_res.edges)
        except Exception as exc:
            print(f"[graphify watch] http_calls scan skipped: {exc}")

        # Preserve semantic nodes/edges from a previous full run.
        # AST-only rebuild replaces code nodes; doc/paper/image nodes are kept.
        existing_graph = out / "graph.json"
        if existing_graph.exists():
            try:
                existing = json.loads(existing_graph.read_text(encoding="utf-8"))
                code_ids = {n["id"] for n in existing.get("nodes", []) if n.get("file_type") == "code"}
                # Preserve only doc/paper/image semantic nodes — NOT route/URL/API
                # overlay nodes, which are regenerated from source on every build.
                # Preserving stale overlay would leak deleted pages/endpoints into
                # the rebuilt graph.
                sem_nodes = [
                    n for n in existing.get("nodes", [])
                    if n.get("file_type") not in ("code", "route")
                ]
                sem_node_ids = {n["id"] for n in sem_nodes}
                # Preserve edges between preserved semantic nodes or from code
                # to semantic (INFERRED/AMBIGUOUS). Drop any edge that touches
                # a non-preserved, non-code node (i.e. stale route/API node).
                sem_edges = []
                for e in existing.get("links", existing.get("edges", [])):
                    src, tgt = e.get("source"), e.get("target")
                    if src not in code_ids and src not in sem_node_ids and src is not None:
                        continue
                    if tgt not in code_ids and tgt not in sem_node_ids and tgt is not None:
                        continue
                    if e.get("confidence") in ("INFERRED", "AMBIGUOUS") \
                       or (src not in code_ids and tgt not in code_ids):
                        sem_edges.append(e)
                result = {
                    "nodes": result["nodes"] + sem_nodes,
                    "edges": result["edges"] + sem_edges,
                    "hyperedges": existing.get("hyperedges", []),
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            except Exception:
                pass  # corrupt graph.json - proceed with AST-only

        detection = {
            "files": {"code": [str(f) for f in code_files], "document": [], "paper": [], "image": []},
            "total_files": len(code_files),
            "total_words": detected.get("total_words", 0),
        }

        G = build_from_json(result, directed=directed)
        communities = cluster(G)
        cohesion = score_all(G, communities)
        gods = god_nodes(G)
        surprises = surprising_connections(G, communities)

        # Load persisted labels if they exist; fall back to numeric "Community N"
        labels = _load_persisted_labels(out, communities)
        questions = suggest_questions(G, communities, labels)

        out.mkdir(parents=True, exist_ok=True)

        report = generate(G, communities, cohesion, labels, gods, surprises, detection,
                          {"input": 0, "output": 0}, str(watch_path), suggested_questions=questions)
        (out / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
        to_json(G, communities, str(out / "graph.json"))

        # to_html raises ValueError for graphs > MAX_NODES_FOR_VIZ (5000).
        # Wrap so core outputs (graph.json + GRAPH_REPORT.md) always land.
        html_written = False
        try:
            to_html(G, communities, str(out / "graph.html"), community_labels=labels or None)
            html_written = True
        except ValueError as viz_err:
            print(f"[graphify watch] Skipped graph.html: {viz_err}")
            stale = out / "graph.html"
            if stale.exists():
                stale.unlink()

        # Persist labels for next run (preserves across cleanup)
        (out / ".graphify_labels.json").write_text(
            json.dumps({str(k): v for k, v in labels.items()}, indent=2),
            encoding="utf-8",
        )

        # clear stale needs_update flag if present
        flag = out / "needs_update"
        if flag.exists():
            flag.unlink()

        print(f"[graphify watch] Rebuilt: {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges, {len(communities)} communities")
        products = "graph.json" + (", graph.html" if html_written else "") + " and GRAPH_REPORT.md"
        print(f"[graphify watch] {products} updated in {out}")
        return True

    except Exception as exc:
        print(f"[graphify watch] Rebuild failed: {exc}")
        return False


def _notify_only(watch_path: Path) -> None:
    """Write a flag file and print a notification (fallback for non-code-only corpora)."""
    flag = watch_path / "graphify-out" / "needs_update"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text("1", encoding="utf-8")
    print(f"\n[graphify watch] New or changed files detected in {watch_path}")
    print("[graphify watch] Non-code files changed - semantic re-extraction requires LLM.")
    print("[graphify watch] Run `/graphify --update` in Claude Code to update the graph.")
    print(f"[graphify watch] Flag written to {flag}")


def _has_non_code(changed_paths: list[Path]) -> bool:
    return any(p.suffix.lower() not in _CODE_EXTENSIONS for p in changed_paths)


def watch(watch_path: Path, debounce: float = 3.0) -> None:
    """
    Watch watch_path for new or modified files and auto-update the graph.

    For code-only changes: re-runs AST extraction + rebuild immediately (no LLM).
    For doc/paper/image changes: writes a needs_update flag and notifies the user
    to run /graphify --update (LLM extraction required).

    debounce: seconds to wait after the last change before triggering (avoids
    running on every keystroke when many files are saved at once).
    """
    try:
        from watchdog.observers import Observer
        from watchdog.observers.polling import PollingObserver
        from watchdog.events import FileSystemEventHandler
    except ImportError as e:
        raise ImportError("watchdog not installed. Run: pip install watchdog") from e

    last_trigger: float = 0.0
    pending: bool = False
    changed: set[Path] = set()

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            nonlocal last_trigger, pending
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix.lower() not in _WATCHED_EXTENSIONS:
                return
            if any(part.startswith(".") for part in path.parts):
                return
            if "graphify-out" in path.parts:
                return
            last_trigger = time.monotonic()
            pending = True
            changed.add(path)

    handler = Handler()
    # Use polling observer on macOS — FSEvents can miss rapid saves in some editors
    observer = PollingObserver() if sys.platform == "darwin" else Observer()
    observer.schedule(handler, str(watch_path), recursive=True)
    observer.start()

    print(f"[graphify watch] Watching {watch_path.resolve()} - press Ctrl+C to stop")
    print(f"[graphify watch] Code changes rebuild graph automatically. "
          f"Doc/image changes require /graphify --update.")
    print(f"[graphify watch] Debounce: {debounce}s")

    try:
        while True:
            time.sleep(0.5)
            if pending and (time.monotonic() - last_trigger) >= debounce:
                pending = False
                batch = list(changed)
                changed.clear()
                print(f"\n[graphify watch] {len(batch)} file(s) changed")
                if _has_non_code(batch):
                    _notify_only(watch_path)
                else:
                    _rebuild_code(watch_path)
    except KeyboardInterrupt:
        print("\n[graphify watch] Stopped.")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Watch a folder and auto-update the graphify graph")
    parser.add_argument("path", nargs="?", default=".", help="Folder to watch (default: .)")
    parser.add_argument("--debounce", type=float, default=3.0,
                        help="Seconds to wait after last change before updating (default: 3)")
    args = parser.parse_args()
    watch(Path(args.path), debounce=args.debounce)
