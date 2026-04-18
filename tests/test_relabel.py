"""Tests for graphify.relabel module.

Covers directed/undirected reconstruction, stale wiki cleanup,
report shallow rewrite, labels.json fallback, and to_graphml
community_name injection.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import networkx as nx
import pytest


# ---------- Fixtures ----------

def _write_graph_json(path: Path, *, directed: bool = False) -> None:
    """Write a minimal graph.json with 2 communities."""
    data = {
        "directed": directed,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "n1", "community": 0, "source_file": "src/a.py", "file_type": "code"},
            {"id": "n2", "community": 0, "source_file": "src/b.py", "file_type": "code"},
            {"id": "n3", "community": 1, "source_file": "src/c.py", "file_type": "code"},
            {"id": "n4", "community": 1, "source_file": "src/d.py", "file_type": "code"},
        ],
        "links": [
            {"source": "n1", "target": "n2"},
            {"source": "n3", "target": "n4"},
            {"source": "n1", "target": "n3"},
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _make_graphify_out(
    base: Path,
    *,
    directed: bool = False,
    with_labels_file: bool = False,
) -> Path:
    """Create a temporary graphify-out directory with graph.json and stubs."""
    out = base / "graphify-out"
    out.mkdir(parents=True, exist_ok=True)
    _write_graph_json(out / "graph.json", directed=directed)
    # Create stale wiki files that should be cleared on relabel
    wiki = out / "wiki"
    wiki.mkdir(exist_ok=True)
    (wiki / "Community_0.md").write_text("# Community 0\n", encoding="utf-8")
    (wiki / "Community_1.md").write_text("# Community 1\n", encoding="utf-8")
    (wiki / "_COMMUNITY_0.md").write_text("legacy", encoding="utf-8")
    (wiki / "unrelated.md").write_text("keep me", encoding="utf-8")
    # GRAPH_REPORT.md with Community N tokens
    (out / "GRAPH_REPORT.md").write_text(
        '### Community 0 - "Community 0"\n\n'
        'See [Community 1] for details.\n\n'
        'Wiki: [link](wiki/Community_0.md)\n',
        encoding="utf-8",
    )
    if with_labels_file:
        (out / ".graphify_labels.json").write_text(
            json.dumps({"0": "[FE/portal] Alpha", "1": "[BE/api] Beta"}, indent=2),
            encoding="utf-8",
        )
    return out


# ---------- Tests ----------

def test_relabel_undirected_basic(tmp_path):
    """Labels applied, stale wiki deleted, no Community N in outputs."""
    from graphify.relabel import run

    out = _make_graphify_out(tmp_path)
    labels = {"0": "[FE/portal] Alpha", "1": "[BE/api] Beta"}
    labels_file = tmp_path / "labels.json"
    labels_file.write_text(json.dumps(labels), encoding="utf-8")

    summary = run(out, labels_file)

    # Stale wiki files are gone
    assert not (out / "wiki" / "Community_0.md").exists()
    assert not (out / "wiki" / "Community_1.md").exists()
    assert not (out / "wiki" / "_COMMUNITY_0.md").exists()
    # Unrelated wiki file untouched
    assert (out / "wiki" / "unrelated.md").exists()
    # graph.html should exist and contain labels
    assert (out / "graph.html").exists()
    html = (out / "graph.html").read_text(encoding="utf-8")
    assert "[FE/portal] Alpha" in html or "Alpha" in html
    # graph.json has community_label field
    gj = json.loads((out / "graph.json").read_text(encoding="utf-8"))
    assert any(n.get("community_label") for n in gj["nodes"])
    # Persisted labels
    persisted = json.loads((out / ".graphify_labels.json").read_text(encoding="utf-8"))
    assert persisted["0"] == "[FE/portal] Alpha"
    assert summary["labels"] == 2
    assert summary["stale_wiki_removed"] >= 2


def test_relabel_directed_preserves_direction(tmp_path):
    """Fixture with directed:true yields nx.DiGraph reconstruction (observable via graph.html data)."""
    from graphify.relabel import run

    out = _make_graphify_out(tmp_path, directed=True)
    labels = {"0": "[FE] Alpha", "1": "[BE] Beta"}
    labels_file = tmp_path / "labels.json"
    labels_file.write_text(json.dumps(labels), encoding="utf-8")

    summary = run(out, labels_file)

    assert summary["directed"] is True
    # Reload graph.json and ensure directed flag round-trips
    gj = json.loads((out / "graph.json").read_text(encoding="utf-8"))
    # networkx json_graph.node_link_data writes "directed": true when DiGraph
    assert gj.get("directed") is True


def test_relabel_report_shallow_replace(tmp_path):
    """GRAPH_REPORT.md gets Community N tokens replaced."""
    from graphify.relabel import run

    out = _make_graphify_out(tmp_path)
    labels = {"0": "[FE/portal] Alpha", "1": "[BE/api] Beta"}
    labels_file = tmp_path / "labels.json"
    labels_file.write_text(json.dumps(labels), encoding="utf-8")

    run(out, labels_file)

    report = (out / "GRAPH_REPORT.md").read_text(encoding="utf-8")
    assert "### Community 0" not in report
    assert "[FE/portal] Alpha" in report
    assert "[BE/api] Beta" in report
    assert "Community_0.md" not in report
    # The replaced wiki link uses _safe_filename of the label
    assert "FE_portal" in report or "[FE/portal]" in report


def test_relabel_missing_labels_json_falls_back_to_persisted(tmp_path):
    """When --labels omitted, reads <dir>/.graphify_labels.json."""
    from graphify.relabel import run

    out = _make_graphify_out(tmp_path, with_labels_file=True)
    summary = run(out, None)  # no explicit labels path

    assert summary["labels"] == 2
    persisted = json.loads((out / ".graphify_labels.json").read_text(encoding="utf-8"))
    assert persisted["0"] == "[FE/portal] Alpha"


def test_relabel_to_graphml_injects_community_name(tmp_path):
    """Verifies P0-3 integration: graph.graphml has community_name attribute."""
    from graphify.relabel import run

    out = _make_graphify_out(tmp_path)
    labels = {"0": "[FE] X", "1": "[BE] Y"}
    labels_file = tmp_path / "labels.json"
    labels_file.write_text(json.dumps(labels), encoding="utf-8")

    run(out, labels_file)

    graphml_path = out / "graph.graphml"
    assert graphml_path.exists()
    xml = graphml_path.read_text(encoding="utf-8")
    assert "community_name" in xml
    assert "[FE] X" in xml or "[BE] Y" in xml


def test_clean_stale_wiki_idempotent(tmp_path):
    """Empty dir / missing dir / mixed files -> only Community_*.md removed."""
    from graphify.relabel import _clean_stale_wiki

    # Missing dir -> 0
    assert _clean_stale_wiki(tmp_path / "does_not_exist") == 0

    # Empty dir -> 0
    empty = tmp_path / "empty_wiki"
    empty.mkdir()
    assert _clean_stale_wiki(empty) == 0

    # Mixed dir
    mixed = tmp_path / "mixed_wiki"
    mixed.mkdir()
    (mixed / "Community_0.md").write_text("x")
    (mixed / "Community_42.md").write_text("y")
    (mixed / "_COMMUNITY_0.md").write_text("z")
    (mixed / "unrelated.md").write_text("keep")
    (mixed / "index.md").write_text("keep")
    removed = _clean_stale_wiki(mixed)
    assert removed == 3
    assert (mixed / "unrelated.md").exists()
    assert (mixed / "index.md").exists()
    assert not (mixed / "Community_0.md").exists()


# ---------- CLI smoke test (runs after T0-5 lands) ----------

@pytest.mark.skipif(
    "relabel"
    not in subprocess.run(
        [sys.executable, "-m", "graphify", "--help"],
        capture_output=True,
        text=True,
    ).stdout,
    reason="graphify relabel subcommand not wired yet (T0-5 may be pending)",
)
def test_relabel_cli_smoke(tmp_path):
    """python -m graphify relabel <dir> --labels <labels.json> exits 0."""
    out = _make_graphify_out(tmp_path)
    labels = {"0": "[FE] Alpha", "1": "[BE] Beta"}
    labels_file = tmp_path / "labels.json"
    labels_file.write_text(json.dumps(labels), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "graphify", "relabel", str(out), "--labels", str(labels_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stdout={result.stdout}, stderr={result.stderr}"
    assert "Relabeled" in result.stdout
