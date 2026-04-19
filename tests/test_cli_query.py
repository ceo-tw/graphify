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
