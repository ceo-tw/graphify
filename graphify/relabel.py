"""Relabel an existing graphify-out directory with new community labels.

Reconstructs the NetworkX graph from graph.json, clears stale wiki files,
then re-exports HTML/JSON/GraphML/wiki with the provided labels. Also
shallow-rewrites GRAPH_REPORT.md since full regeneration requires
intermediate analysis artifacts that cleanup removes.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import networkx as nx

from graphify.build import build_from_json
from graphify.export import to_html, to_json, to_graphml
from graphify.wiki import to_wiki

STALE_WIKI_GLOBS = ("Community_*.md", "_COMMUNITY_*.md")


def _safe_filename(label: str) -> str:
    """Mirror graphify.wiki._safe_filename (kept private there).

    Replace characters unsafe for filesystems with the same rules as wiki.py.
    """
    # Keep in sync with wiki.py's _safe_filename.
    return label.replace("/", "-").replace(" ", "_").replace(":", "-")


def _load_graph_and_labels(
    directory: Path,
    labels_path: Path | None,
) -> tuple[nx.Graph, dict[int, list[str]], dict[int, str], bool]:
    """Load graph.json, reconstruct NetworkX graph, and resolve labels source.

    Returns (G, communities, labels, directed).
    """
    graph_json = directory / "graph.json"
    if not graph_json.exists():
        raise FileNotFoundError(f"graph.json not found at {graph_json}")

    raw = json.loads(graph_json.read_text(encoding="utf-8"))
    directed = bool(raw.get("directed", False))
    G = build_from_json(raw, directed=directed)

    # Labels: explicit path wins, else fall back to in-directory persisted file.
    if labels_path is None:
        labels_path = directory / ".graphify_labels.json"
    if not labels_path.exists():
        raise FileNotFoundError(
            f"labels.json not found: specify --labels or create {directory / '.graphify_labels.json'}"
        )
    labels_raw = json.loads(labels_path.read_text(encoding="utf-8"))
    labels = {int(k): v for k, v in labels_raw.items()}

    communities = _communities_from_graph(G)
    return G, communities, labels, directed


def _communities_from_graph(G: nx.Graph) -> dict[int, list[str]]:
    """Reconstruct communities dict from node 'community' attributes."""
    communities: dict[int, list[str]] = {}
    for node_id, data in G.nodes(data=True):
        cid = data.get("community", -1)
        if cid == -1:
            continue
        communities.setdefault(int(cid), []).append(str(node_id))
    return communities


def _clean_stale_wiki(wiki_dir: Path) -> int:
    """Remove stale Community_*.md and _COMMUNITY_*.md files.

    Returns number of files deleted. Idempotent on missing dir.
    """
    if not wiki_dir.exists():
        return 0
    count = 0
    for pattern in STALE_WIKI_GLOBS:
        for f in wiki_dir.glob(pattern):
            f.unlink()
            count += 1
    return count


def _post_process_graph_json(graph_json_path: Path, labels: dict[int, str]) -> None:
    """Inject community_label field into graph.json nodes (to_json lacks the seam)."""
    raw = json.loads(graph_json_path.read_text(encoding="utf-8"))
    for node in raw.get("nodes", []):
        cid = node.get("community", -1)
        if isinstance(cid, int) and cid in labels:
            node["community_label"] = labels[cid]
    graph_json_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def _replace_report_in_place(report_path: Path, labels: dict[int, str]) -> bool:
    """Shallow-replace 'Community N' tokens in GRAPH_REPORT.md.

    Returns True if the file was modified. If the file doesn't exist, returns False
    (full regeneration not possible without intermediate analysis artifacts).
    """
    if not report_path.exists():
        return False
    text = report_path.read_text(encoding="utf-8")
    original = text

    def _sub_header(m: re.Match) -> str:
        cid = int(m.group(1))
        label = labels.get(cid, f"Community {cid}")
        return f'### {label} - "{label}"'

    def _sub_ref(m: re.Match) -> str:
        cid = int(m.group(1))
        label = labels.get(cid, f"Community {cid}")
        return f"[{label}]"

    def _sub_wiki_link(m: re.Match) -> str:
        cid = int(m.group(1))
        label = labels.get(cid, f"Community {cid}")
        return f"{_safe_filename(label)}.md"

    text = re.sub(r'### Community (\d+) - "[^"]*"', _sub_header, text)
    text = re.sub(r"\[Community (\d+)\]", _sub_ref, text)
    text = re.sub(r"Community_(\d+)\.md", _sub_wiki_link, text)

    if text != original:
        report_path.write_text(text, encoding="utf-8")
        return True
    return False


def _persist_labels(directory: Path, labels: dict[int, str]) -> None:
    """Write labels to .graphify_labels.json for future survive-across-cleanup runs."""
    path = directory / ".graphify_labels.json"
    path.write_text(
        json.dumps({str(k): v for k, v in labels.items()}, indent=2),
        encoding="utf-8",
    )


def run(directory: Path, labels_path: Path | None = None) -> dict[str, int | str]:
    """Perform relabel in-place on a graphify-out directory.

    Returns a summary dict. Raises on precondition failures (missing graph.json,
    missing labels).
    """
    directory = directory.resolve()
    G, communities, labels, directed = _load_graph_and_labels(directory, labels_path)

    wiki_dir = directory / "wiki"
    stale_removed = _clean_stale_wiki(wiki_dir)

    # Re-export
    graph_html = directory / "graph.html"
    graph_json = directory / "graph.json"
    graph_graphml = directory / "graph.graphml"
    report_md = directory / "GRAPH_REPORT.md"

    to_html(G, communities, str(graph_html), community_labels=labels or None)
    to_json(G, communities, str(graph_json))
    _post_process_graph_json(graph_json, labels)
    to_graphml(G, communities, str(graph_graphml), community_labels=labels or None)
    to_wiki(G, communities, str(wiki_dir), community_labels=labels)

    report_modified = _replace_report_in_place(report_md, labels)

    _persist_labels(directory, labels)

    return {
        "directory": str(directory),
        "communities": len(communities),
        "labels": len(labels),
        "stale_wiki_removed": stale_removed,
        "report_modified": report_modified,
        "directed": directed,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: graphify relabel <dir> [--labels labels.json]."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help"):
        print("usage: graphify relabel <graphify-out-dir> [--labels labels.json]")
        return 1 if not argv else 0

    directory = Path(argv[0])
    labels_path: Path | None = None
    i = 1
    while i < len(argv):
        if argv[i] == "--labels" and i + 1 < len(argv):
            labels_path = Path(argv[i + 1])
            i += 2
        else:
            print(f"unknown argument: {argv[i]}", file=sys.stderr)
            return 2

    try:
        summary = run(directory, labels_path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Relabeled {summary['communities']} communities in {summary['directory']} "
        f"(stale wiki removed: {summary['stale_wiki_removed']}, "
        f"report modified: {summary['report_modified']}, directed: {summary['directed']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
