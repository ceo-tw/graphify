# Smoke tests for graphify CLI subcommands: query / path / explain.
#
# These cover the code paths that currently live inline in graphify/__main__.py
# and are about to be extracted to graphify/cli_graph_query.py. The tests
# invoke the CLI as a subprocess so they catch dispatcher regressions (missing
# imports, broken sys.argv parsing, changed exit codes) end-to-end.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tiny_graph(tmp_path: Path) -> Path:
    """Minimal node-link graph with enough structure to exercise query/path/explain."""
    g = {
        "directed": False,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "a", "label": "detect", "file_type": "code",
             "source_file": "graphify/detect.py", "source_location": "L10",
             "community": 0},
            {"id": "b", "label": "cluster", "file_type": "code",
             "source_file": "graphify/cluster.py", "source_location": "L5",
             "community": 0},
            {"id": "c", "label": "build", "file_type": "code",
             "source_file": "graphify/build.py", "source_location": "L40",
             "community": 1},
        ],
        "links": [
            {"source": "a", "target": "b", "relation": "calls",
             "confidence": "EXTRACTED", "source_file": "graphify/detect.py"},
            {"source": "b", "target": "c", "relation": "uses",
             "confidence": "EXTRACTED", "source_file": "graphify/cluster.py"},
        ],
    }
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(g))
    return p


def _run(args: list[str], graph_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "graphify", *args, "--graph", str(graph_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_query_returns_subgraph(tiny_graph: Path) -> None:
    r = _run(["query", "detect"], tiny_graph)
    assert r.returncode == 0, r.stderr
    assert "detect" in r.stdout.lower()


def test_query_missing_graph_exits_nonzero(tmp_path: Path) -> None:
    r = _run(["query", "anything"], tmp_path / "no-such.json")
    assert r.returncode != 0
    assert "not found" in r.stderr.lower() or "error" in r.stderr.lower()


def test_path_between_connected_nodes(tiny_graph: Path) -> None:
    r = _run(["path", "detect", "build"], tiny_graph)
    assert r.returncode == 0, r.stderr
    assert "Shortest path" in r.stdout
    # The path a → b → c should appear in output.
    assert "detect" in r.stdout and "build" in r.stdout


def test_path_source_not_found_exits_nonzero(tiny_graph: Path) -> None:
    """cmd_path returns non-zero and prints to stderr when source label matches no node."""
    r = _run(["path", "nonexistent-source-xyz", "build"], tiny_graph)
    assert r.returncode != 0
    assert "No node matching" in r.stderr


def test_path_no_path_exits_cleanly(tmp_path: Path) -> None:
    g = {
        "directed": False, "multigraph": False, "graph": {},
        "nodes": [
            {"id": "x", "label": "alpha", "file_type": "code",
             "source_file": "a.py"},
            {"id": "y", "label": "omega", "file_type": "code",
             "source_file": "b.py"},
        ],
        "links": [],
    }
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(g))
    r = _run(["path", "alpha", "omega"], p)
    assert r.returncode == 0
    assert "No path" in r.stdout


def test_explain_dumps_node_info(tiny_graph: Path) -> None:
    r = _run(["explain", "detect"], tiny_graph)
    assert r.returncode == 0, r.stderr
    assert "Node:" in r.stdout
    assert "detect" in r.stdout
    # Should show connections since degree > 0.
    assert "Connections" in r.stdout or "-->" in r.stdout


def test_explain_no_match_prints_message(tiny_graph: Path) -> None:
    r = _run(["explain", "nonexistent-symbol-xyz"], tiny_graph)
    assert r.returncode == 0
    assert "No node" in r.stdout


# ---------------------------------------------------------------------------
# PHASE 2 tests — R2.1 fuzzy fallback, R2.2 --min-confidence flag
# ---------------------------------------------------------------------------

def _seed_query_graph(tmp_path: Path) -> Path:
    """Graph for PHASE 2 tests.

    Nodes:
      - session_validate   (label: "sessionValidate",  source_file: "auth/session.py")
      - audit_log          (label: "auditLog",          source_file: "audit/log.py")
      - build_graph_fn     (label: "buildGraph",        source_file: "graphify/build.py")
    Edges:
      - session_validate → audit_log    confidence=AMBIGUOUS  relation=triggers
      - session_validate → build_graph  confidence=INFERRED   relation=calls
    """
    g = {
        "directed": False,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "session_validate", "label": "sessionValidate",
             "source_file": "auth/session.py", "source_location": "L12", "community": 0},
            {"id": "audit_log", "label": "auditLog",
             "source_file": "audit/log.py", "source_location": "L5", "community": 0},
            {"id": "build_graph_fn", "label": "buildGraph",
             "source_file": "graphify/build.py", "source_location": "L40", "community": 1},
        ],
        "links": [
            {"source": "session_validate", "target": "audit_log",
             "relation": "triggers", "confidence": "AMBIGUOUS"},
            {"source": "session_validate", "target": "build_graph_fn",
             "relation": "calls", "confidence": "INFERRED"},
        ],
    }
    p = tmp_path / "phase2_graph.json"
    p.write_text(json.dumps(g))
    return p


def test_query_fuzzy_fallback(tmp_path: Path) -> None:
    """R2.1 — a typo/truncated query "sesion validate" must still surface sessionValidate
    via fuzzy matching when exact substring scoring returns < 3 results."""
    graph = _seed_query_graph(tmp_path)
    r = _run(["query", "sesion validate"], graph)
    assert r.returncode == 0, r.stderr
    # Fuzzy match should find sessionValidate despite the typo
    assert "sessionvalidate" in r.stdout.lower() or "session_validate" in r.stdout.lower(), (
        f"Expected fuzzy match for 'sesion validate' to surface sessionValidate.\n"
        f"stdout: {r.stdout!r}\nstderr: {r.stderr!r}"
    )


def test_query_min_confidence_excludes_ambiguous(tmp_path: Path) -> None:
    """R2.2 — --min-confidence INFERRED must omit the AMBIGUOUS edge to auditLog
    while still including the INFERRED edge to buildGraph."""
    graph = _seed_query_graph(tmp_path)
    # Without filter: auditLog should appear (reachable via AMBIGUOUS edge)
    r_all = _run(["query", "sessionValidate"], graph)
    assert r_all.returncode == 0, r_all.stderr
    assert "auditlog" in r_all.stdout.lower() or "audit_log" in r_all.stdout.lower(), (
        f"Baseline: expected auditLog in unrestricted output.\nstdout: {r_all.stdout!r}"
    )

    # With --min-confidence INFERRED: auditLog must NOT appear
    r_filtered = _run(["query", "sessionValidate", "--min-confidence", "INFERRED"], graph)
    assert r_filtered.returncode == 0, r_filtered.stderr
    assert "auditlog" not in r_filtered.stdout.lower() and "audit_log" not in r_filtered.stdout.lower(), (
        f"Filtered: auditLog should be excluded by --min-confidence INFERRED.\n"
        f"stdout: {r_filtered.stdout!r}\nstderr: {r_filtered.stderr!r}"
    )


# ---------------------------------------------------------------------------
# PHASE 3 tests — R2.1.5: --json output for query / path
# ---------------------------------------------------------------------------

def test_query_json_output_structure(tiny_graph: Path) -> None:
    """R2.1.5 — graphify query --json must emit valid JSON with required keys."""
    r = _run(["query", "detect", "--json"], tiny_graph)
    assert r.returncode == 0, r.stderr
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"--json output is not valid JSON: {exc}\nstdout: {r.stdout!r}")
    # Required top-level keys
    assert "nodes" in data, f"Missing 'nodes' key in JSON output: {data.keys()}"
    assert "edges" in data, f"Missing 'edges' key in JSON output: {data.keys()}"
    assert "subgraph_node_count" in data, f"Missing 'subgraph_node_count' key: {data.keys()}"
    assert "subgraph_edge_count" in data, f"Missing 'subgraph_edge_count' key: {data.keys()}"
    # At least one node returned (query matched 'detect')
    assert data["subgraph_node_count"] >= 1, "Expected at least one node in subgraph"


def test_query_json_text_output_unchanged(tiny_graph: Path) -> None:
    """R2.1.5 — text output (no --json) must still work exactly as before."""
    r = _run(["query", "detect"], tiny_graph)
    assert r.returncode == 0, r.stderr
    assert "detect" in r.stdout.lower()
    # Must NOT be JSON (text mode)
    try:
        json.loads(r.stdout)
        pytest.fail("Without --json, output should be plain text, not JSON")
    except json.JSONDecodeError:
        pass  # expected


def test_path_json_output_structure(tiny_graph: Path) -> None:
    """R2.1.5 — graphify path --json must emit valid JSON with 'found', 'hops', 'path'."""
    r = _run(["path", "detect", "build", "--json"], tiny_graph)
    assert r.returncode == 0, r.stderr
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"--json output is not valid JSON: {exc}\nstdout: {r.stdout!r}")
    assert "found" in data, f"Missing 'found' key: {data.keys()}"
    assert data["found"] is True, f"Expected found=True for connected nodes, got: {data}"
    assert "hops" in data, f"Missing 'hops' key: {data.keys()}"
    assert "path" in data, f"Missing 'path' key: {data.keys()}"
    assert isinstance(data["path"], list), f"'path' must be a list, got: {type(data['path'])}"
    assert data["hops"] == 2, f"Expected 2 hops (a→b→c), got: {data['hops']}"


def test_path_json_no_path_found(tmp_path: Path) -> None:
    """R2.1.5 — graphify path --json on disconnected graph must emit found=False."""
    g = {
        "directed": False, "multigraph": False, "graph": {},
        "nodes": [
            {"id": "x", "label": "alpha", "file_type": "code", "source_file": "a.py"},
            {"id": "y", "label": "omega", "file_type": "code", "source_file": "b.py"},
        ],
        "links": [],
    }
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(g))
    r = _run(["path", "alpha", "omega", "--json"], p)
    assert r.returncode == 0, r.stderr
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"--json output is not valid JSON: {exc}\nstdout: {r.stdout!r}")
    assert "found" in data, f"Missing 'found' key: {data.keys()}"
    assert data["found"] is False, f"Expected found=False for disconnected graph, got: {data}"
