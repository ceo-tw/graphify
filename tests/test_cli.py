"""Tests for Phase 4 CLI surface — build, resolve, callers, callees, blast, init-ignore, and --out-dir."""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def _ts_fixture_available() -> bool:
    try:
        import tree_sitter_typescript  # noqa: F401
        from tree_sitter import Language, Parser  # noqa: F401
        return True
    except Exception:
        return False


def _write(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "graphify", *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


# ───── build subcommand ─────────────────────────────────────────────────


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_build_no_semantic_writes_graph_json(tmp_path: Path):
    """AST+routes+http only build should produce graph.json without LLM."""
    _write(tmp_path / "app" / "portal" / "page.tsx", "export default function P() {}")
    _write(tmp_path / "app" / "layout.tsx", "export default function L() {}")

    result = _run_cli("build", str(tmp_path), "--no-semantic")
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    out = tmp_path / "graphify-out"
    assert (out / "graph.json").exists()


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_build_emits_url_and_api_overlay_nodes(tmp_path: Path):
    """A Next.js app with page.tsx + route.ts should produce URL and API
    nodes in graph.json via the build command."""
    _write(tmp_path / "app" / "portal" / "page.tsx", "export default function P() {}")
    _write(tmp_path / "app" / "layout.tsx", "export default function L() {}")
    _write(tmp_path / "app" / "api" / "ping" / "route.ts",
           "export async function GET() { return new Response('ok'); }")
    result = _run_cli("build", str(tmp_path), "--no-semantic", "--directed")
    assert result.returncode == 0, result.stderr
    data = json.loads((tmp_path / "graphify-out" / "graph.json").read_text())
    kinds = {n.get("kind") for n in data["nodes"]}
    assert "url" in kinds, "expected at least one URL overlay node"
    assert "api" in kinds, "expected at least one API overlay node"


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_build_rejects_unknown_flag(tmp_path: Path):
    result = _run_cli("build", str(tmp_path), "--no-semantic", "--nope")
    assert result.returncode != 0
    assert "--nope" in (result.stderr + result.stdout)


def test_init_ignore_line_equality_not_substring(tmp_path: Path):
    """If existing file contains 'foo/node_modules/', the default
    'node_modules/' line must still be appended — substring-match-based
    check would incorrectly skip it."""
    ig = tmp_path / ".graphifyignore"
    ig.write_text("foo/node_modules/\n", encoding="utf-8")
    _run_cli("init-ignore", str(tmp_path))
    lines = {l.strip() for l in ig.read_text().splitlines()}
    assert "node_modules/" in lines
    assert "foo/node_modules/" in lines  # user content preserved


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_build_directed_flag_produces_directed_graph(tmp_path: Path):
    _write(tmp_path / "app" / "page.tsx", "export default function P() {}")
    _write(tmp_path / "app" / "layout.tsx", "export default function L() {}")

    result = _run_cli("build", str(tmp_path), "--no-semantic", "--directed")
    assert result.returncode == 0
    data = json.loads((tmp_path / "graphify-out" / "graph.json").read_text())
    assert data.get("directed") is True


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_build_out_dir_writes_to_alternate_location(tmp_path: Path):
    _write(tmp_path / "app" / "page.tsx", "export default function P() {}")
    _write(tmp_path / "app" / "layout.tsx", "export default function L() {}")

    alt = tmp_path / "custom" / "graphify-out"
    result = _run_cli("build", str(tmp_path), "--no-semantic", "--out-dir", str(alt))
    assert result.returncode == 0
    assert (alt / "graph.json").exists()
    # Default location may carry a cache/ folder (internal), but must not
    # carry user-visible graph artifacts.
    default = tmp_path / "graphify-out"
    assert not (default / "graph.json").exists()
    assert not (default / "graph.html").exists()


# ───── resolve subcommand ───────────────────────────────────────────────


def _seed_resolve_graph(tmp_path: Path) -> Path:
    graph = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {
                "id": "url_portal_agents_id",
                "label": "URL /portal/agents/:id",
                "file_type": "route",
                "kind": "url",
                "url_pattern": "/portal/agents/:id",
                "source_file": "app/portal/agents/[id]/page.tsx",
            },
            {
                "id": "api_get_portal_agents_id",
                "label": "GET /portal/agents/:id",
                "file_type": "route",
                "kind": "api",
                "method": "GET",
                "url_pattern": "/portal/agents/:id",
            },
            {
                "id": "handler_get",
                "label": "handler",
                "file_type": "route",
                "kind": "handler",
            },
        ],
        "links": [
            {"source": "api_get_portal_agents_id", "target": "handler_get", "relation": "handled_by"},
        ],
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    return graph_path


def test_resolve_matches_concrete_url(tmp_path: Path):
    graph_path = _seed_resolve_graph(tmp_path)
    result = _run_cli(
        "resolve", "/portal/agents/172",
        "--graph", str(graph_path), "--json",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    match_ids = {m["id"] for m in payload["matches"]}
    assert "url_portal_agents_id" in match_ids


def test_resolve_method_filter(tmp_path: Path):
    graph_path = _seed_resolve_graph(tmp_path)
    result = _run_cli(
        "resolve", "/portal/agents/172",
        "--graph", str(graph_path), "--method", "GET", "--json",
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    match_ids = {m["id"] for m in payload["matches"]}
    assert "api_get_portal_agents_id" in match_ids


def test_resolve_no_match_returns_empty(tmp_path: Path):
    graph_path = _seed_resolve_graph(tmp_path)
    result = _run_cli(
        "resolve", "/nowhere",
        "--graph", str(graph_path), "--json",
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["matches"] == []


# ───── callers / callees / blast ────────────────────────────────────────


def _seed_impact_graph(tmp_path: Path) -> Path:
    graph = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "A", "label": "A", "source_file": "a.ts", "file_type": "code"},
            {"id": "B", "label": "B", "source_file": "b.ts", "file_type": "code"},
            {"id": "C", "label": "C", "source_file": "c.ts", "file_type": "code"},
        ],
        "links": [
            {"source": "A", "target": "B", "relation": "calls"},
            {"source": "B", "target": "C", "relation": "calls"},
        ],
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    return graph_path


def test_callers_cli_json(tmp_path: Path):
    graph_path = _seed_impact_graph(tmp_path)
    result = _run_cli("callers", "C", "--graph", str(graph_path), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    ids = {r["id"] for r in payload["results"]}
    assert ids == {"A", "B"}


def test_callees_cli_json(tmp_path: Path):
    graph_path = _seed_impact_graph(tmp_path)
    result = _run_cli("callees", "A", "--graph", str(graph_path), "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ids = {r["id"] for r in payload["results"]}
    assert ids == {"B", "C"}


def test_blast_cli_json(tmp_path: Path):
    graph_path = _seed_impact_graph(tmp_path)
    result = _run_cli("blast", "A", "--graph", str(graph_path), "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["total"] == 2
    assert "a.ts" not in payload["by_file"]


def test_impact_requires_directed_error(tmp_path: Path):
    graph = {
        "directed": False,
        "multigraph": False,
        "graph": {},
        "nodes": [{"id": "A"}, {"id": "B"}],
        "links": [{"source": "A", "target": "B", "relation": "calls"}],
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    result = _run_cli("callers", "B", "--graph", str(graph_path), "--json")
    assert result.returncode != 0
    assert "--directed" in (result.stderr + result.stdout)


def test_callers_max_hops(tmp_path: Path):
    graph_path = _seed_impact_graph(tmp_path)
    result = _run_cli("callers", "C", "--graph", str(graph_path), "--max-hops", "1", "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ids = {r["id"] for r in payload["results"]}
    assert ids == {"B"}


def test_callers_edge_types_filter(tmp_path: Path):
    graph = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "X"},
            {"id": "Y"},
            {"id": "Z"},
        ],
        "links": [
            {"source": "X", "target": "Y", "relation": "calls"},
            {"source": "Y", "target": "Z", "relation": "imports"},
        ],
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    result = _run_cli("callers", "Z", "--graph", str(graph_path),
                      "--edges", "calls", "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ids = {r["id"] for r in payload["results"]}
    # Only 'calls' allowed; Y→Z is 'imports' → blocked, so no caller reaches Z.
    assert ids == set()


# ───── init-ignore ─────────────────────────────────────────────────────


def test_init_ignore_writes_graphifyignore(tmp_path: Path):
    _write(tmp_path / "package.json", '{"name":"demo"}')
    _write(tmp_path / "next.config.js", "module.exports = {};")
    result = _run_cli("init-ignore", str(tmp_path))
    assert result.returncode == 0
    ig = tmp_path / ".graphifyignore"
    assert ig.exists()
    contents = ig.read_text()
    assert "node_modules" in contents
    assert ".next" in contents


def test_init_ignore_includes_graphify_output_folders(tmp_path: Path):
    _write(tmp_path / "package.json", "{}")
    result = _run_cli("init-ignore", str(tmp_path))
    assert result.returncode == 0
    contents = (tmp_path / ".graphifyignore").read_text()
    assert ".claude/architecture/graph/*/corpus" in contents or \
           ".claude/architecture/graph/*/graphify-out" in contents


def test_init_ignore_preserves_existing_content(tmp_path: Path):
    ig = tmp_path / ".graphifyignore"
    ig.write_text("# user custom\nmy-secret/\n", encoding="utf-8")
    _run_cli("init-ignore", str(tmp_path))
    new_contents = ig.read_text()
    assert "my-secret/" in new_contents
    assert "node_modules" in new_contents


# ───── --out-dir on update ──────────────────────────────────────────────


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_rebuild_prunes_stale_route_nodes(tmp_path: Path):
    """If a page file is deleted, its URL overlay node must not persist in
    graph.json after the next build/update. Previously the 'preserve
    non-code nodes' branch kept old overlay nodes indefinitely."""
    page = tmp_path / "app" / "portal" / "page.tsx"
    layout = tmp_path / "app" / "layout.tsx"
    _write(page, "export default function P() {}")
    _write(layout, "export default function L() {}")

    # First build: URL overlay for /portal exists.
    r1 = _run_cli("build", str(tmp_path), "--no-semantic")
    assert r1.returncode == 0, r1.stderr
    data1 = json.loads((tmp_path / "graphify-out" / "graph.json").read_text())
    urls1 = {n.get("url_pattern") for n in data1["nodes"] if n.get("kind") == "url"}
    assert "/portal" in urls1

    # Remove the page file and rebuild.
    page.unlink()
    r2 = _run_cli("build", str(tmp_path), "--no-semantic")
    assert r2.returncode == 0, r2.stderr
    data2 = json.loads((tmp_path / "graphify-out" / "graph.json").read_text())
    urls2 = {n.get("url_pattern") for n in data2["nodes"] if n.get("kind") == "url"}
    assert "/portal" not in urls2, "stale URL overlay persisted after page deletion"


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_update_with_out_dir_writes_to_alternate(tmp_path: Path):
    _write(tmp_path / "sample.ts", "export function foo() { return 1; }")
    alt = tmp_path / "elsewhere" / "out"
    result = _run_cli("update", str(tmp_path), "--out-dir", str(alt))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # User-visible graph artifacts must land in the alternate location.
    assert (alt / "graph.json").exists()
    assert (alt / "graph.html").exists()
    # The default location must not contain graph artifacts (a cache/
    # folder may still be populated under the default root; that is
    # internal and acceptable).
    default = tmp_path / "graphify-out"
    assert not (default / "graph.json").exists()
    assert not (default / "graph.html").exists()
