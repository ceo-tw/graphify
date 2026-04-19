# assemble node+edge dicts into a NetworkX graph, preserving edge direction
#
# Node deduplication — three layers:
#
# 1. Within a file (AST): each extractor tracks a `seen_ids` set. A node ID is
#    emitted at most once per file, so duplicate class/function definitions in
#    the same source file are collapsed to the first occurrence.
#
# 2. Between files (build): NetworkX G.add_node() is idempotent — calling it
#    twice with the same ID overwrites the attributes with the second call's
#    values. Nodes are added in extraction order (AST first, then semantic),
#    so if the same entity is extracted by both passes the semantic node
#    silently overwrites the AST node. This is intentional: semantic nodes
#    carry richer labels and cross-file context, while AST nodes have precise
#    source_location. If you need to change the priority, reorder extractions
#    passed to build().
#
# 3. Semantic merge (skill): before calling build(), the skill merges cached
#    and new semantic results using an explicit `seen` set keyed on node["id"],
#    so duplicates across cache hits and new extractions are resolved there
#    before any graph construction happens.
#
from __future__ import annotations
import re
import sys
import networkx as nx
from .validate import VALID_FILE_TYPES, validate_extraction


def _normalize_id(s: str) -> str:
    """Normalize an ID string the same way extract._make_id does.

    Used to reconcile edge endpoints when the LLM generates IDs with slightly
    different punctuation or casing than the AST extractor.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    return cleaned.strip("_").lower()


# Primitive/built-in type names that semantic subagents sometimes promote to
# standalone nodes. They have empty source_file (no real definition in the
# corpus) and pollute the graph with 100+ spurious INFERRED edges. Filtered in
# build_from_json when source_file is empty so real user-defined symbols named
# `str` etc. are preserved.
_PRIMITIVE_IDS = frozenset({
    "str", "int", "float", "bool", "list", "dict", "tuple", "set",
    "none", "any", "optional", "object", "bytes", "frozenset",
})


# Map filename extensions to file_type for semantic nodes that omit the field.
_FILE_TYPE_BY_EXT = {
    ".md": "document", ".txt": "document", ".rst": "document",
    ".pdf": "paper",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image", ".gif": "image",
}


def _infer_file_type(source_file: str) -> str:
    """Best-effort file_type from source_file extension. Defaults to 'code'."""
    if not source_file:
        return "code"
    from pathlib import PurePosixPath
    ext = PurePosixPath(source_file).suffix.lower()
    return _FILE_TYPE_BY_EXT.get(ext, "code")


def _normalize_extraction(extraction: dict) -> dict:
    """Normalize an extraction dict in-place-ish before validation.

    Handles schema drift across graphify versions and subagent variation:
    - Drops primitive nodes (str/int/…) that have no source_file.
    - Defaults file_type on nodes missing it (uses source_file extension).
    - Maps legacy 'classification' field to 'confidence' on edges.
    - Fills edge source_file from the source node's source_file when empty.

    Hyperedges are passed through unchanged; report.py already reads them with
    safe defaults (`h.get("confidence", "INFERRED")`). Extend this function if
    a future consumer requires strict schema on hyperedges.

    Pure function; does not mutate the input dict. Returns a shallow copy with
    normalized 'nodes' and 'edges' lists.
    """
    nodes_in = extraction.get("nodes", [])
    nodes_out: list[dict] = []
    for node in nodes_in:
        nid = node.get("id", "")
        if nid.lower() in _PRIMITIVE_IDS and not node.get("source_file"):
            continue
        # Always work on a shallow copy so field defaults don't leak back into
        # the caller's extraction dict (protects cache entries loaded by ref).
        node = dict(node)
        # Subagents occasionally drop source_file on semantic concept nodes;
        # default to empty string so validate's "field present" check passes
        # without silently inventing a path.
        node.setdefault("source_file", "")
        ft = node.get("file_type")
        if not ft or ft not in VALID_FILE_TYPES:
            # Remap subagent variants like 'markdown'/'text' to the schema-valid
            # vocabulary by extension. Falls back to 'code' when unknown.
            node["file_type"] = _infer_file_type(node.get("source_file", ""))
        nodes_out.append(node)

    # Build lookup once so edge source_file fallback is O(1).
    src_file_by_id = {n["id"]: n.get("source_file", "") for n in nodes_out if "id" in n}

    edges_in = extraction.get("edges", extraction.get("links", []))
    edges_out: list[dict] = []
    for edge in edges_in:
        e = dict(edge)
        if "source" not in e and "from" in e:
            e["source"] = e.pop("from")
        if "target" not in e and "to" in e:
            e["target"] = e.pop("to")
        if "source" not in e or "target" not in e:
            continue
        if "confidence" not in e and "classification" in e:
            e["confidence"] = e.pop("classification")
        if not e.get("source_file"):
            e["source_file"] = src_file_by_id.get(e["source"], "")
        edges_out.append(e)

    out = dict(extraction)
    out["nodes"] = nodes_out
    out["edges"] = edges_out
    return out


def build_from_json(extraction: dict, *, directed: bool = False) -> nx.Graph:
    """Build a NetworkX graph from an extraction dict.

    directed=True produces a DiGraph that preserves edge direction (source→target).
    directed=False (default) produces an undirected Graph for backward compatibility.
    """
    # NetworkX <= 3.1 serialised edges as "links"; remap to "edges" for compatibility.
    if "edges" not in extraction and "links" in extraction:
        extraction = dict(extraction, edges=extraction["links"])
    # Normalize first so validate doesn't warn on drift that we can heal.
    extraction = _normalize_extraction(extraction)
    errors = validate_extraction(extraction)
    # Dangling edges (stdlib/external imports) are expected - only warn about real schema errors.
    real_errors = [e for e in errors if "does not match any node id" not in e]
    if real_errors:
        print(f"[graphify] Extraction warning ({len(real_errors)} issues): {real_errors[0]}", file=sys.stderr)
    G: nx.Graph = nx.DiGraph() if directed else nx.Graph()
    for node in extraction.get("nodes", []):
        G.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
    node_set = set(G.nodes())
    # Normalized ID map: lets edges survive when the LLM generates IDs with
    # slightly different casing or punctuation than the AST extractor.
    # e.g. "Session_ValidateToken" maps to "session_validatetoken".
    norm_to_id: dict[str, str] = {_normalize_id(nid): nid for nid in node_set}
    for edge in extraction.get("edges", []):
        src, tgt = edge["source"], edge["target"]
        # Remap mismatched IDs via normalization before dropping the edge.
        if src not in node_set:
            src = norm_to_id.get(_normalize_id(src), src)
        if tgt not in node_set:
            tgt = norm_to_id.get(_normalize_id(tgt), tgt)
        if src not in node_set or tgt not in node_set:
            continue  # skip edges to external/stdlib nodes - expected, not an error
        attrs = {k: v for k, v in edge.items() if k not in ("source", "target")}
        # Preserve original edge direction - undirected graphs lose it otherwise,
        # causing display functions to show edges backwards.
        attrs["_src"] = src
        attrs["_tgt"] = tgt
        G.add_edge(src, tgt, **attrs)
    hyperedges = extraction.get("hyperedges", [])
    if hyperedges:
        G.graph["hyperedges"] = hyperedges
    return G


def build(extractions: list[dict], *, directed: bool = False) -> nx.Graph:
    """Merge multiple extraction results into one graph.

    directed=True produces a DiGraph that preserves edge direction (source→target).
    directed=False (default) produces an undirected Graph for backward compatibility.

    Extractions are merged in order. For nodes with the same ID, the last
    extraction's attributes win (NetworkX add_node overwrites). Pass AST
    results before semantic results so semantic labels take precedence, or
    reverse the order if you prefer AST source_location precision to win.
    """
    combined: dict = {"nodes": [], "edges": [], "hyperedges": [], "input_tokens": 0, "output_tokens": 0}
    for ext in extractions:
        combined["nodes"].extend(ext.get("nodes", []))
        combined["edges"].extend(ext.get("edges", []))
        combined["hyperedges"].extend(ext.get("hyperedges", []))
        combined["input_tokens"] += ext.get("input_tokens", 0)
        combined["output_tokens"] += ext.get("output_tokens", 0)
    return build_from_json(combined, directed=directed)
