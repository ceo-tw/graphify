# per-file extraction cache - skip unchanged files on re-run
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


# Bump this when the extractor output schema changes in a way that makes
# cached 0.x.y results incompatible with the current extractor logic.
# Mixed into file_hash() so the new code automatically misses old entries.
# Shared by both AST and semantic cache entries (same cache_dir, same hash key).
#
# v3 (rev 3): semantic edges now normalized to {confidence, source_file} in
# build_from_json, and semantic nodes default file_type when missing; older
# entries may contain 'classification' field or lack file_type on nodes.
# v2 (0.5.2): AST extractor emits namespace_aliases and raw_calls with
# namespace_target_source_file hints.
_CACHE_SCHEMA_VERSION = b"v3"


def _body_content(content: bytes) -> bytes:
    """Strip YAML frontmatter from Markdown content, returning only the body."""
    text = content.decode(errors="replace")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].encode()
    return content


def file_hash(path: Path, root: Path = Path(".")) -> str:
    """SHA256 of file contents + path relative to root.

    Using a relative path (not absolute) makes cache entries portable across
    machines and checkout directories, so shared caches and CI work correctly.
    Falls back to the resolved absolute path if the file is outside root.

    For Markdown files (.md), only the body below the YAML frontmatter is hashed,
    so metadata-only changes (e.g. reviewed, status, tags) do not invalidate the cache.
    """
    p = Path(path)
    raw = p.read_bytes()
    content = _body_content(raw) if p.suffix.lower() == ".md" else raw
    h = hashlib.sha256()
    h.update(content)
    h.update(b"\x00")
    try:
        rel = p.resolve().relative_to(Path(root).resolve())
        h.update(str(rel).encode())
    except ValueError:
        h.update(str(p.resolve()).encode())
    h.update(b"\x00")
    h.update(_CACHE_SCHEMA_VERSION)
    return h.hexdigest()


def cache_dir(root: Path = Path("."), cache_override: Path | None = None) -> Path:
    """Returns the cache directory - creates it if needed.

    If ``cache_override`` is given, it is used verbatim as the cache directory
    (so callers can relocate the cache out of the source tree — e.g. when
    ``graphify build`` is invoked with ``--out-dir`` pointing at a shared
    overlay). Otherwise falls back to ``<root>/graphify-out/cache/`` for
    backwards compatibility.
    """
    if cache_override is not None:
        # Skip .resolve() if already absolute — extract() calls this per file,
        # and the watch layer already resolves once up-front.
        p = Path(cache_override)
        d = p if p.is_absolute() else p.resolve()
    else:
        d = Path(root).resolve() / "graphify-out" / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_cached(
    path: Path,
    root: Path = Path("."),
    cache_override: Path | None = None,
) -> dict | None:
    """Return cached extraction for this file if hash matches, else None.

    Cache key: SHA256 of file contents + path relative to ``root``.
    Cache value: stored as ``<cache_dir>/{hash}.json``.
    Returns None if no cache entry or file has changed.
    """
    try:
        h = file_hash(path, root)
    except OSError:
        return None
    entry = cache_dir(root, cache_override=cache_override) / f"{h}.json"
    if not entry.exists():
        return None
    try:
        return json.loads(entry.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_cached(
    path: Path,
    result: dict,
    root: Path = Path("."),
    cache_override: Path | None = None,
) -> None:
    """Save extraction result for this file.

    Stores as ``<cache_dir>/{hash}.json`` where hash = file_hash(path, root).
    result should be a dict with 'nodes' and 'edges' lists.
    """
    h = file_hash(path, root)
    entry = cache_dir(root, cache_override=cache_override) / f"{h}.json"
    tmp = entry.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(result), encoding="utf-8")
        try:
            os.replace(tmp, entry)
        except PermissionError:
            # Windows: os.replace can fail with WinError 5 if the target is
            # briefly locked. Fall back to copy-then-delete.
            import shutil
            shutil.copy2(tmp, entry)
            tmp.unlink(missing_ok=True)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def cached_files(root: Path = Path("."), cache_override: Path | None = None) -> set[str]:
    """Return set of file paths that have a valid cache entry (hash still matches)."""
    d = cache_dir(root, cache_override=cache_override)
    return {p.stem for p in d.glob("*.json")}


def clear_cache(root: Path = Path("."), cache_override: Path | None = None) -> None:
    """Delete all cached *.json entries from the active cache directory."""
    d = cache_dir(root, cache_override=cache_override)
    for f in d.glob("*.json"):
        f.unlink()


def check_semantic_cache(
    files: list[str],
    root: Path = Path("."),
    cache_override: Path | None = None,
) -> tuple[list[dict], list[dict], list[dict], list[str]]:
    """Check semantic extraction cache for a list of absolute file paths.

    Returns (cached_nodes, cached_edges, cached_hyperedges, uncached_files).
    Uncached files need Claude extraction; cached files are merged directly.
    """
    cached_nodes: list[dict] = []
    cached_edges: list[dict] = []
    cached_hyperedges: list[dict] = []
    uncached: list[str] = []

    for fpath in files:
        result = load_cached(Path(fpath), root=root, cache_override=cache_override)
        if result is not None:
            cached_nodes.extend(result.get("nodes", []))
            cached_edges.extend(result.get("edges", []))
            cached_hyperedges.extend(result.get("hyperedges", []))
        else:
            uncached.append(fpath)

    return cached_nodes, cached_edges, cached_hyperedges, uncached


def save_semantic_cache(
    nodes: list[dict],
    edges: list[dict],
    hyperedges: list[dict] | None = None,
    root: Path = Path("."),
    cache_override: Path | None = None,
) -> int:
    """Save semantic extraction results to cache, keyed by source_file.

    Groups nodes and edges by source_file, then saves one cache entry per file.
    Returns the number of files cached.
    """
    from collections import defaultdict

    by_file: dict[str, dict] = defaultdict(lambda: {"nodes": [], "edges": [], "hyperedges": []})
    for n in nodes:
        src = n.get("source_file", "")
        if src:
            by_file[src]["nodes"].append(n)
    for e in edges:
        src = e.get("source_file", "")
        if src:
            by_file[src]["edges"].append(e)
    for h in (hyperedges or []):
        src = h.get("source_file", "")
        if src:
            by_file[src]["hyperedges"].append(h)

    saved = 0
    for fpath, result in by_file.items():
        p = Path(fpath)
        if not p.is_absolute():
            p = Path(root) / p
        if p.exists():
            save_cached(p, result, root=root, cache_override=cache_override)
            saved += 1
    return saved
