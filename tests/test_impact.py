"""Tests for graphify.analyze directed impact functions (callers / callees / blast_radius)."""
from __future__ import annotations

import networkx as nx
import pytest

from graphify.analyze import callers, callees, blast_radius


# ───── Fixture builders ─────────────────────────────────────────────────


def _chain_digraph() -> nx.DiGraph:
    """A → B → C → D with extra branch B → E, and unrelated X → Y."""
    G = nx.DiGraph()
    G.add_node("A", label="A", source_file="a.py", file_type="code")
    G.add_node("B", label="B", source_file="b.py", file_type="code")
    G.add_node("C", label="C", source_file="c.py", file_type="code")
    G.add_node("D", label="D", source_file="d.py", file_type="code")
    G.add_node("E", label="E", source_file="e.py", file_type="code")
    G.add_node("X", label="X", source_file="x.py", file_type="code")
    G.add_node("Y", label="Y", source_file="y.py", file_type="code")
    G.add_edge("A", "B", relation="calls")
    G.add_edge("B", "C", relation="calls")
    G.add_edge("C", "D", relation="calls")
    G.add_edge("B", "E", relation="calls")
    G.add_edge("X", "Y", relation="imports")
    return G


def _mixed_edge_types() -> nx.DiGraph:
    """FE → URL → API → handler demo to exercise edge_types filtering."""
    G = nx.DiGraph()
    G.add_node("use_hook", label="useHook", file_type="code")
    G.add_node("API:POST /x", label="POST /x", file_type="route")
    G.add_node("handler", label="handler", file_type="code")
    G.add_node("service", label="service", file_type="code")
    G.add_edge("use_hook", "API:POST /x", relation="calls_http")
    G.add_edge("API:POST /x", "handler", relation="handled_by")
    G.add_edge("handler", "service", relation="calls")
    return G


# ───── callers() ────────────────────────────────────────────────────────


def test_callers_simple_chain():
    G = _chain_digraph()
    result = callers(G, "C")
    caller_ids = {r["id"] for r in result}
    # A → B → C : ancestors of C are A and B.
    assert caller_ids == {"A", "B"}


def test_callers_excludes_self_and_unrelated():
    G = _chain_digraph()
    result = callers(G, "C")
    ids = {r["id"] for r in result}
    assert "C" not in ids
    assert "X" not in ids
    assert "Y" not in ids


def test_callers_max_hops_limits_depth():
    G = _chain_digraph()
    result = callers(G, "D", max_hops=1)
    ids = {r["id"] for r in result}
    # With hop=1 only direct ancestor C should appear.
    assert ids == {"C"}


def test_callers_edge_types_filter():
    G = _mixed_edge_types()
    result = callers(G, "service", edge_types=["calls"])
    ids = {r["id"] for r in result}
    # Only handler reaches service via 'calls'; use_hook is behind 'calls_http' + 'handled_by'.
    assert ids == {"handler"}


def test_callers_combined_edge_types():
    G = _mixed_edge_types()
    result = callers(G, "service", edge_types=["calls", "calls_http", "handled_by"])
    ids = {r["id"] for r in result}
    assert ids == {"handler", "API:POST /x", "use_hook"}


def test_callers_requires_directed():
    G = _chain_digraph().to_undirected()
    with pytest.raises(ValueError, match=r"--directed"):
        callers(G, "C")


def test_callers_unknown_node_returns_empty():
    G = _chain_digraph()
    assert callers(G, "Z_not_present") == []


def test_callers_returns_node_attrs():
    G = _chain_digraph()
    [first] = [r for r in callers(G, "C") if r["id"] == "A"]
    assert first["label"] == "A"
    assert first["source_file"] == "a.py"


# ───── callees() ────────────────────────────────────────────────────────


def test_callees_simple_chain():
    G = _chain_digraph()
    result = callees(G, "B")
    ids = {r["id"] for r in result}
    assert ids == {"C", "D", "E"}


def test_callees_max_hops():
    G = _chain_digraph()
    result = callees(G, "A", max_hops=1)
    ids = {r["id"] for r in result}
    assert ids == {"B"}


def test_callees_edge_types_filter():
    G = _mixed_edge_types()
    result = callees(G, "use_hook", edge_types=["calls"])
    # calls_http/handled_by are excluded, so nothing is reachable via 'calls' only.
    assert result == []


def test_callees_requires_directed():
    G = _chain_digraph().to_undirected()
    with pytest.raises(ValueError, match=r"--directed"):
        callees(G, "A")


# ───── blast_radius() ───────────────────────────────────────────────────


def test_blast_radius_groups_by_file():
    G = _chain_digraph()
    radius = blast_radius(G, "B")
    # Returned type should group reachable nodes by source_file.
    by_file = radius["by_file"]
    assert "c.py" in by_file
    assert "d.py" in by_file
    assert "e.py" in by_file
    assert "a.py" not in by_file  # upstream only in callers, not blast


def test_blast_radius_total_count():
    G = _chain_digraph()
    radius = blast_radius(G, "B")
    assert radius["total"] == 3  # C, D, E


def test_blast_radius_edge_types_filter():
    G = _mixed_edge_types()
    radius = blast_radius(G, "use_hook", edge_types=["calls_http"])
    assert radius["total"] == 1  # only API node reachable via calls_http
    assert {n["id"] for n in radius["nodes"]} == {"API:POST /x"}


def test_blast_radius_requires_directed():
    G = _chain_digraph().to_undirected()
    with pytest.raises(ValueError, match=r"--directed"):
        blast_radius(G, "B")
