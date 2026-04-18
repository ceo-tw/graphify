"""Community detection on NetworkX graphs. Uses Leiden (graspologic) if available, falls back to Louvain (networkx). Splits oversized communities. Returns cohesion scores."""
from __future__ import annotations
import contextlib
import inspect
import io
import sys
import networkx as nx


def _suppress_output():
    """Context manager to suppress stdout/stderr during library calls.

    graspologic's leiden() emits ANSI escape sequences (progress bars,
    colored warnings) that corrupt PowerShell 5.1's scroll buffer on
    Windows (see issue #19). Redirecting stdout/stderr to devnull during
    the call prevents this without losing any graphify output.
    """
    return contextlib.redirect_stdout(io.StringIO())


def _partition(G: nx.Graph) -> dict[str, int]:
    """Run community detection. Returns {node_id: community_id}.

    Tries Leiden (graspologic) first — best quality.
    Falls back to Louvain (built into networkx) if graspologic is not installed.

    Output from graspologic is suppressed to prevent ANSI escape codes
    from corrupting terminal scroll buffers on Windows PowerShell 5.1.
    """
    try:
        from graspologic.partition import leiden
        # Suppress graspologic output to prevent ANSI escape codes from
        # corrupting PowerShell 5.1 scroll buffer (issue #19)
        old_stderr = sys.stderr
        try:
            sys.stderr = io.StringIO()
            with _suppress_output():
                result = leiden(G)
        finally:
            sys.stderr = old_stderr
        return result
    except ImportError:
        pass

    # Fallback: networkx louvain (available since networkx 2.7).
    # Inspect kwargs to stay compatible across NetworkX versions — max_level
    # was added in a later release and prevents hangs on large sparse graphs.
    kwargs: dict = {"seed": 42, "threshold": 1e-4}
    if "max_level" in inspect.signature(nx.community.louvain_communities).parameters:
        kwargs["max_level"] = 10
    communities = nx.community.louvain_communities(G, **kwargs)
    return {node: cid for cid, nodes in enumerate(communities) for node in nodes}


_MAX_COMMUNITY_FRACTION = 0.25   # communities larger than 25% of graph get split
_MIN_SPLIT_SIZE = 10             # only split if community has at least this many nodes

# Nodes with these file_type values are pulled out of Leiden clustering and
# placed into a synthetic community. Route/URL/API/SERVICE overlays would
# otherwise become FE↔BE "bridges" that distort community structure once the
# DiGraph is converted to undirected for Leiden.
_OVERLAY_FILE_TYPES = frozenset({"route"})
_OVERLAY_COMMUNITY_LABEL = "Routes"


def _is_overlay_node(G: nx.Graph, node_id: str) -> bool:
    """Return True if this node carries an overlay ``file_type`` attribute."""
    attrs = G.nodes[node_id]
    return attrs.get("file_type") in _OVERLAY_FILE_TYPES


def cluster(G: nx.Graph) -> dict[int, list[str]]:
    """Run Leiden community detection. Returns {community_id: [node_ids]}.

    Community IDs are stable across runs: 0 = largest community after splitting.
    Oversized communities (> 25% of graph nodes, min 10) are split by running
    a second Leiden pass on the subgraph.

    Overlay nodes (``file_type`` in ``_OVERLAY_FILE_TYPES`` — currently
    ``"route"``) are excluded from Leiden and placed into a single synthetic
    "Routes" community after clustering. This prevents URL/API nodes from
    acting as FE↔BE bridges once the DiGraph is collapsed to undirected for
    Leiden. Callers that want the label for the synthetic community can
    import ``_OVERLAY_COMMUNITY_LABEL``.

    Accepts directed or undirected graphs. DiGraphs are converted to undirected
    internally since Louvain/Leiden require undirected input.
    """
    if G.number_of_nodes() == 0:
        return {}
    if G.is_directed():
        G = G.to_undirected()

    # Separate overlay nodes *before* the edgeless fast-path so they share one
    # synthetic community instead of becoming singleton communities.
    overlay_nodes = [n for n in G.nodes() if _is_overlay_node(G, n)]
    non_overlay_nodes = [n for n in G.nodes() if n not in set(overlay_nodes)]

    if G.number_of_edges() == 0:
        result: dict[int, list[str]] = {
            i: [n] for i, n in enumerate(sorted(non_overlay_nodes))
        }
        if overlay_nodes:
            overlay_cid = len(result)
            result[overlay_cid] = sorted(overlay_nodes)
        return result

    # Work on a copy of the non-overlay subgraph so degree/isolate checks
    # reflect the graph Leiden will actually see.
    clust_graph = G.subgraph(non_overlay_nodes).copy() if overlay_nodes else G

    raw: dict[int, list[str]] = {}
    if clust_graph.number_of_nodes() > 0:
        # Leiden warns and drops isolates - handle them separately
        isolates = [n for n in clust_graph.nodes() if clust_graph.degree(n) == 0]
        connected_nodes = [n for n in clust_graph.nodes() if clust_graph.degree(n) > 0]
        connected = clust_graph.subgraph(connected_nodes)

        if connected.number_of_nodes() > 0:
            partition = _partition(connected)
            for node, cid in partition.items():
                raw.setdefault(cid, []).append(node)

        # Each isolate becomes its own single-node community
        next_cid = max(raw.keys(), default=-1) + 1
        for node in isolates:
            raw[next_cid] = [node]
            next_cid += 1

    # Split oversized communities (relative to the clustered subgraph size)
    clustered_n = max(1, clust_graph.number_of_nodes())
    max_size = max(_MIN_SPLIT_SIZE, int(clustered_n * _MAX_COMMUNITY_FRACTION))
    final_communities: list[list[str]] = []
    for nodes in raw.values():
        if len(nodes) > max_size:
            final_communities.extend(_split_community(clust_graph, nodes))
        else:
            final_communities.append(nodes)

    # Re-index by size descending for deterministic ordering
    final_communities.sort(key=len, reverse=True)
    result = {i: sorted(nodes) for i, nodes in enumerate(final_communities)}

    # Append overlay nodes as a single synthetic community at the tail so the
    # cid is stable across runs (always max_real_cid + 1). When there are no
    # real communities this still produces cid=0 for the overlay.
    if overlay_nodes:
        overlay_cid = (max(result.keys()) + 1) if result else 0
        result[overlay_cid] = sorted(overlay_nodes)

    return result


def _split_community(G: nx.Graph, nodes: list[str]) -> list[list[str]]:
    """Run a second Leiden pass on a community subgraph to split it further."""
    subgraph = G.subgraph(nodes)
    if subgraph.number_of_edges() == 0:
        # No edges - split into individual nodes
        return [[n] for n in sorted(nodes)]
    try:
        sub_partition = _partition(subgraph)
        sub_communities: dict[int, list[str]] = {}
        for node, cid in sub_partition.items():
            sub_communities.setdefault(cid, []).append(node)
        if len(sub_communities) <= 1:
            return [sorted(nodes)]
        return [sorted(v) for v in sub_communities.values()]
    except Exception:
        return [sorted(nodes)]


def cohesion_score(G: nx.Graph, community_nodes: list[str]) -> float:
    """Ratio of actual intra-community edges to maximum possible."""
    n = len(community_nodes)
    if n <= 1:
        return 1.0
    subgraph = G.subgraph(community_nodes)
    actual = subgraph.number_of_edges()
    possible = n * (n - 1) / 2
    return round(actual / possible, 2) if possible > 0 else 0.0


def score_all(G: nx.Graph, communities: dict[int, list[str]]) -> dict[int, float]:
    return {cid: cohesion_score(G, nodes) for cid, nodes in communities.items()}
