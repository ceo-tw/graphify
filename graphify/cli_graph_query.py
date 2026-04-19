# CLI handlers for graph-traversal subcommands: query / path / explain.
#
# Split out of __main__.py to keep the dispatcher thin. Each handler takes the
# raw argv tail (the subcommand name already stripped) and returns an int exit
# code. Dispatch from __main__.py with a single-line delegation.
#
# Keeping these together (rather than one module per command) mirrors their
# shared plumbing: argv parsing for --graph/--budget, graph loading via
# networkx.readwrite.json_graph, and scoring helpers from graphify.serve.

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence


def _load_graph(graph_path: str):
    """Load a node-link JSON graph, handling NetworkX <= 3.1 'links' fallback.

    Exits the process with a clear error if the file is missing or unparseable.
    """
    from networkx.readwrite import json_graph

    gp = Path(graph_path).resolve()
    if not gp.exists():
        print(f"error: graph file not found: {gp}", file=sys.stderr)
        sys.exit(1)
    if gp.suffix != ".json":
        print("error: graph file must be a .json file", file=sys.stderr)
        sys.exit(1)
    try:
        raw = json.loads(gp.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"error: could not load graph: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        return json_graph.node_link_graph(raw, edges="links")
    except TypeError:
        return json_graph.node_link_graph(raw)


def _parse_graph_flag(args: Sequence[str], default: str = "graphify-out/graph.json") -> str:
    """Scan argv tail for `--graph <path>` and return the resolved value."""
    args = list(args)
    for i, a in enumerate(args):
        if a == "--graph" and i + 1 < len(args):
            return args[i + 1]
    return default


def cmd_query(argv: Sequence[str]) -> int:
    """graphify query "<question>" [--dfs] [--budget N] [--graph path]"""
    if len(argv) < 1:
        print(
            'Usage: graphify query "<question>" [--dfs] [--budget N] [--graph path]',
            file=sys.stderr,
        )
        return 1

    from graphify.serve import _bfs, _dfs, _score_nodes, _subgraph_to_text  # noqa: F401

    question = argv[0]
    use_dfs = "--dfs" in argv
    budget = 2000
    graph_path = "graphify-out/graph.json"

    rest = list(argv[1:])
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok == "--budget" and i + 1 < len(rest):
            try:
                budget = int(rest[i + 1])
            except ValueError:
                print("error: --budget must be an integer", file=sys.stderr)
                return 1
            i += 2
        elif tok.startswith("--budget="):
            try:
                budget = int(tok.split("=", 1)[1])
            except ValueError:
                print("error: --budget must be an integer", file=sys.stderr)
                return 1
            i += 1
        elif tok == "--graph" and i + 1 < len(rest):
            graph_path = rest[i + 1]
            i += 2
        else:
            i += 1

    G = _load_graph(graph_path)
    terms = [t.lower() for t in question.split() if len(t) > 2]
    scored = _score_nodes(G, terms)
    if not scored:
        print("No matching nodes found.")
        return 0
    start = [nid for _, nid in scored[:5]]
    nodes, edges = (_dfs if use_dfs else _bfs)(G, start, depth=2)
    print(_subgraph_to_text(G, nodes, edges, token_budget=budget))
    return 0


def cmd_path(argv: Sequence[str]) -> int:
    """graphify path "<source>" "<target>" [--graph path]"""
    if len(argv) < 2:
        print(
            'Usage: graphify path "<source>" "<target>" [--graph path]',
            file=sys.stderr,
        )
        return 1

    import networkx as _nx
    from graphify.serve import _score_nodes

    source_label = argv[0]
    target_label = argv[1]
    graph_path = _parse_graph_flag(argv[2:])

    G = _load_graph(graph_path)
    src_scored = _score_nodes(G, [t.lower() for t in source_label.split()])
    tgt_scored = _score_nodes(G, [t.lower() for t in target_label.split()])
    if not src_scored:
        print(f"No node matching '{source_label}' found.", file=sys.stderr)
        return 1
    if not tgt_scored:
        print(f"No node matching '{target_label}' found.", file=sys.stderr)
        return 1
    src_nid, tgt_nid = src_scored[0][1], tgt_scored[0][1]
    try:
        path_nodes = _nx.shortest_path(G, src_nid, tgt_nid)
    except (_nx.NetworkXNoPath, _nx.NodeNotFound):
        print(f"No path found between '{source_label}' and '{target_label}'.")
        return 0

    hops = len(path_nodes) - 1
    segments: list[str] = []
    for i in range(len(path_nodes) - 1):
        u, v = path_nodes[i], path_nodes[i + 1]
        edata = G.edges[u, v]
        rel = edata.get("relation", "")
        conf = edata.get("confidence", "")
        conf_str = f" [{conf}]" if conf else ""
        if i == 0:
            segments.append(G.nodes[u].get("label", u))
        segments.append(f"--{rel}{conf_str}--> {G.nodes[v].get('label', v)}")
    print(f"Shortest path ({hops} hops):\n  " + " ".join(segments))
    return 0


def cmd_explain(argv: Sequence[str]) -> int:
    """graphify explain "<node>" [--graph path]"""
    if len(argv) < 1:
        print('Usage: graphify explain "<node>" [--graph path]', file=sys.stderr)
        return 1

    from graphify.serve import _find_node

    label = argv[0]
    graph_path = _parse_graph_flag(argv[1:])
    G = _load_graph(graph_path)

    matches = _find_node(G, label)
    if not matches:
        print(f"No node matching '{label}' found.")
        return 0

    nid = matches[0]
    d = G.nodes[nid]
    print(f"Node: {d.get('label', nid)}")
    print(f"  ID:        {nid}")
    print(f"  Source:    {d.get('source_file', '')} {d.get('source_location', '')}".rstrip())
    print(f"  Type:      {d.get('file_type', '')}")
    print(f"  Community: {d.get('community', '')}")
    print(f"  Degree:    {G.degree(nid)}")
    neighbors = list(G.neighbors(nid))
    if neighbors:
        print(f"\nConnections ({len(neighbors)}):")
        for nb in sorted(neighbors, key=lambda n: G.degree(n), reverse=True)[:20]:
            edata = G.edges[nid, nb]
            rel = edata.get("relation", "")
            conf = edata.get("confidence", "")
            print(f"  --> {G.nodes[nb].get('label', nb)} [{rel}] [{conf}]")
        if len(neighbors) > 20:
            print(f"  ... and {len(neighbors) - 20} more")
    return 0
