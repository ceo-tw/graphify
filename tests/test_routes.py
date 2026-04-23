"""Tests for graphify.routes — URL/route overlay extraction.

Uses tmp_path synthetic Next.js / Hono fixtures, not the openclaw-cloud
project. Assertions stay resilient to tree-sitter availability — Hono scan
is skipped gracefully if tree-sitter is not installed.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from graphify.routes import (
    RouteScanResult,
    scan,
    scan_nextjs,
    scan_hono,
    _segment_to_url,
    _path_to_url,
    _normalize_url_pattern,
    _join_mount,
    _url_node_id,
    _api_node_id,
)


# ───── Unit tests on pure helpers ───────────────────────────────────────────


def test_segment_literal():
    assert _segment_to_url("portal") == ("portal", {})


def test_segment_dynamic():
    assert _segment_to_url("[id]") == (":id", {})


def test_segment_catch_all():
    assert _segment_to_url("[...slug]") == ("*slug", {})


def test_segment_optional_catch_all():
    assert _segment_to_url("[[...slug]]") == ("*?slug", {})


def test_segment_route_group_is_invisible():
    piece, attrs = _segment_to_url("(marketing)")
    assert piece is None
    assert attrs == {"route_group": "marketing"}


def test_segment_parallel_slot_is_invisible():
    piece, attrs = _segment_to_url("@modal")
    assert piece is None
    assert attrs == {"parallel_slot": "modal"}


def test_segment_intercepting_is_invisible():
    piece, attrs = _segment_to_url("(.)")
    assert piece is None
    assert attrs["intercepting"] == "."


def test_path_to_url_simple():
    url, _ = _path_to_url(["portal", "agents", "[id]"])
    assert url == "/portal/agents/:id"


def test_path_to_url_with_route_group():
    url, attrs = _path_to_url(["(auth)", "login"])
    assert url == "/login"
    assert attrs.get("route_group") == "auth"


def test_path_to_url_root():
    url, _ = _path_to_url([])
    assert url == "/"


def test_normalize_url_pattern_adds_slash():
    assert _normalize_url_pattern("agents") == "/agents"
    assert _normalize_url_pattern("/agents") == "/agents"
    assert _normalize_url_pattern("") == "/"


def test_normalize_url_pattern_collapses_slashes():
    assert _normalize_url_pattern("/foo//bar//") == "/foo/bar/"


def test_join_mount_root_base():
    assert _join_mount("/", "/foo") == "/foo"


def test_join_mount_nested():
    assert _join_mount("/settings", "/plans") == "/settings/plans"


def test_join_mount_with_trailing_and_leading_slashes():
    assert _join_mount("/settings/", "/plans/bulk") == "/settings/plans/bulk"


# ───── Next.js App Router scan — synthetic fixture ──────────────────────────


def _write_page(tmp_path: Path, *segments: str, body: str = "export default function Page() {}") -> Path:
    p = tmp_path.joinpath(*segments)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_scan_nextjs_root_page(tmp_path: Path):
    _write_page(tmp_path, "app", "page.tsx")
    # Presence of layout.tsx qualifies the app directory
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    url_ids = {n["id"] for n in result.nodes if n.get("kind") == "url"}
    assert _url_node_id("/") in url_ids


def test_scan_nextjs_portal_agents_dynamic(tmp_path: Path):
    _write_page(tmp_path, "app", "portal", "agents", "[id]", "page.tsx")
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    urls = {n["url_pattern"] for n in result.nodes if n.get("kind") == "url"}
    assert "/portal/agents/:id" in urls


def test_scan_nextjs_route_group_excluded_from_url(tmp_path: Path):
    _write_page(tmp_path, "app", "(auth)", "login", "page.tsx")
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    urls = {n["url_pattern"] for n in result.nodes if n.get("kind") == "url"}
    assert "/login" in urls
    assert "/(auth)/login" not in urls


def test_scan_nextjs_catch_all(tmp_path: Path):
    _write_page(tmp_path, "app", "api", "proxy", "[...path]", "route.ts",
                body="export async function GET(req: Request) { return new Response('ok'); }")
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    api_ids = {n["id"] for n in result.nodes if n.get("kind") == "api"}
    assert _api_node_id("GET", "/api/proxy/*path") in api_ids


def test_scan_nextjs_route_exports_all_methods(tmp_path: Path):
    body = textwrap.dedent("""
        export async function GET() {}
        export async function POST() {}
        export const DELETE = async () => {};
    """).strip()
    _write_page(tmp_path, "app", "api", "agents", "[id]", "route.ts", body=body)
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    api_nodes = [n for n in result.nodes if n.get("kind") == "api"]
    methods = {n["method"] for n in api_nodes}
    assert {"GET", "POST", "DELETE"} <= methods
    # Each API node must emit a handled_by edge
    api_ids = {n["id"] for n in api_nodes}
    handled_sources = {e["source"] for e in result.edges if e.get("relation") == "handled_by"}
    assert api_ids <= handled_sources


def test_scan_nextjs_layout_emits_wraps_edge(tmp_path: Path):
    _write_page(tmp_path, "app", "portal", "page.tsx")
    _write_page(tmp_path, "app", "portal", "layout.tsx")
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    rels = {e.get("relation") for e in result.edges}
    assert "wraps" in rels
    assert "renders" in rels


def test_scan_nextjs_route_nodes_carry_file_type_route(tmp_path: Path):
    _write_page(tmp_path, "app", "portal", "page.tsx")
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    for n in result.nodes:
        assert n["file_type"] == "route"


def test_scan_nextjs_ignores_python_app_directory(tmp_path: Path):
    """A bare directory literally named ``app`` without Next.js convention
    files (e.g. a Python package) must not be treated as an app router."""
    py_app = tmp_path / "api" / "app"
    py_app.mkdir(parents=True)
    (py_app / "__init__.py").write_text("")
    (py_app / "main.py").write_text("def handler(): pass")
    result = scan_nextjs(tmp_path)
    assert result.nodes == []


def test_scan_nextjs_proxy_forwards_to_service(tmp_path: Path):
    proxy_body = textwrap.dedent("""
        export async function GET(request: Request) {
          const base = process.env.ADMIN_API_URL;
          return fetch(base + '/x');
        }
    """).strip()
    _write_page(tmp_path, "app", "api", "proxy", "[...path]", "route.ts", body=proxy_body)
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    service_nodes = [n for n in result.nodes if n.get("kind") == "service"]
    assert service_nodes, "expected at least one SERVICE node from proxy forward detection"
    assert any(e.get("relation") == "forwards_to" for e in result.edges)


# ───── Hono BE scan — synthetic fixture (skip if tree-sitter unavailable) ──


def _ts_fixture_available() -> bool:
    try:
        import tree_sitter_typescript  # noqa: F401
        from tree_sitter import Language, Parser  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_direct_route(tmp_path: Path):
    hono = tmp_path / "admin-api"
    hono.mkdir(parents=True)
    (hono / "index.ts").write_text(textwrap.dedent("""
        import { Hono } from 'hono';
        const app = new Hono();
        app.get('/agents', async (c) => c.json({ ok: true }));
        app.post('/agents/:id/start', async (c) => c.json({ ok: true }));
        export default app;
    """).strip(), encoding="utf-8")
    result = scan_hono(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/agents") in api_pairs
    assert ("POST", "/agents/:id/start") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_same_file_route_mount(tmp_path: Path):
    """Covers ``app.route('/settings', settings)`` mount within one file."""
    hono = tmp_path / "admin-api"
    hono.mkdir(parents=True)
    (hono / "index.ts").write_text(textwrap.dedent("""
        import { Hono } from 'hono';
        const app = new Hono();
        const settings = new Hono();
        settings.put('/plans/bulk-provider', async (c) => c.json({ ok: true }));
        app.route('/settings', settings);
        export default app;
    """).strip(), encoding="utf-8")
    result = scan_hono(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("PUT", "/settings/plans/bulk-provider") in api_pairs


# ───── Cluster integration — overlay nodes go to synthetic community ────────


def test_cluster_places_route_nodes_in_synthetic_community():
    import networkx as nx
    from graphify.cluster import cluster

    G = nx.DiGraph()
    # Normal code cluster: 3 connected nodes
    for n in ("a", "b", "c"):
        G.add_node(n, file_type="code")
    G.add_edge("a", "b")
    G.add_edge("b", "c")
    # Overlay cluster: 2 route nodes with an edge to code
    G.add_node("URL:/x", file_type="route")
    G.add_node("API:GET /x", file_type="route")
    G.add_edge("URL:/x", "a")  # would otherwise bridge if not excluded

    communities = cluster(G)
    # Every node is accounted for
    all_assigned = {n for nodes in communities.values() for n in nodes}
    assert all_assigned == set(G.nodes)

    # Route nodes share one community; no code node is in the same community.
    route_cid = None
    for cid, members in communities.items():
        if "URL:/x" in members:
            route_cid = cid
            break
    assert route_cid is not None
    route_members = set(communities[route_cid])
    assert route_members == {"URL:/x", "API:GET /x"}


def test_cluster_without_route_nodes_behaves_same_as_before():
    import networkx as nx
    from graphify.cluster import cluster

    G = nx.Graph()
    for n in ("a", "b", "c"):
        G.add_node(n, file_type="code")
    G.add_edge("a", "b")
    G.add_edge("b", "c")
    communities = cluster(G)
    all_assigned = {n for nodes in communities.values() for n in nodes}
    assert all_assigned == set(G.nodes)


# ───── Public scan() resilience ─────────────────────────────────────────────


def test_scan_returns_empty_for_irrelevant_directory(tmp_path: Path):
    (tmp_path / "readme.md").write_text("hello")
    result = scan(tmp_path)
    assert isinstance(result, RouteScanResult)
    # Empty project: no URL or API nodes
    assert result.nodes == []


# ───── Codex feedback: intercepting prefix, page ID alignment, proxy
#       multi-target, cluster edgeless, false positives, cross-file Hono ────


def test_segment_intercepting_with_prefix():
    """App Router convention allows (.)photo — the segment should produce
    'photo' visible URL piece with an intercepting attr."""
    piece, attrs = _segment_to_url("(.)photo")
    assert piece == "photo"
    assert attrs.get("intercepting") == "."


def test_segment_intercepting_parent_prefix():
    piece, attrs = _segment_to_url("(..)photo")
    assert piece == "photo"
    assert attrs.get("intercepting") == ".."


def test_segment_intercepting_root_prefix():
    piece, attrs = _segment_to_url("(...)photo")
    assert piece == "photo"
    assert attrs.get("intercepting") == "..."


def test_scan_nextjs_intercepting_prefix_in_url(tmp_path: Path):
    """(.)photo folder produces '/photo' URL (not '/(.)photo')."""
    _write_page(tmp_path, "app", "(.)photo", "[id]", "page.tsx")
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    urls = {n["url_pattern"] for n in result.nodes if n.get("kind") == "url"}
    assert "/photo/:id" in urls


def test_renders_target_id_matches_ast_file_node_id(tmp_path: Path):
    """URL renders edge must target the same ID that extract._make_id
    produces for the page file path. Otherwise the overlay never connects
    to real code nodes."""
    from graphify.extract import _make_id
    page_file = _write_page(tmp_path, "app", "portal", "page.tsx")
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    expected_target = _make_id(str(page_file))
    # The rendered target for /portal must equal _make_id(page_file path)
    targets = {
        e["target"]
        for e in result.edges
        if e.get("relation") == "renders"
    }
    assert expected_target in targets


# ── Hono false positives ───────────────────────────────────────────────


def _write_ts(tmp_path: Path, rel: str, body: str) -> Path:
    p = tmp_path.joinpath(*rel.split("/"))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_does_not_emit_api_for_headers_get(tmp_path: Path):
    """headers.get('authorization') must NOT be treated as GET /authorization.
    Require receiver to be a confirmed Hono binding (local new Hono() or
    import-resolved router)."""
    _write_ts(tmp_path, "admin-api/src/index.ts", textwrap.dedent("""
        function auth(req: Request) {
          const value = req.headers.get('authorization');
          return value;
        }
    """).strip())
    result = scan_hono(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/authorization") not in api_pairs
    # no API nodes at all in this fixture
    assert not any(n.get("kind") == "api" for n in result.nodes)


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_does_not_emit_api_for_map_get(tmp_path: Path):
    _write_ts(tmp_path, "admin-api/src/x.ts", textwrap.dedent("""
        const cache = new Map();
        cache.get('some-key');
        cache.delete('some-key');
    """).strip())
    result = scan_hono(tmp_path)
    assert not any(n.get("kind") == "api" for n in result.nodes)


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_alias_import_not_supported_but_no_crash(tmp_path: Path):
    """``import { Hono as H } from 'hono'; const app = new H();`` is not a
    target of Phase 1 — we only detect `new Hono()`. The test guards against
    regression (must not emit a false API) and documents the limitation."""
    _write_ts(tmp_path, "admin-api/x.ts", textwrap.dedent("""
        import { Hono as H } from 'hono';
        const app = new H();
        app.get('/items', async (c) => c.json({ ok: true }));
    """).strip())
    result = scan_hono(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    # Not detected today (documented limitation). If a future Phase fixes
    # this, flip the assertion.
    assert ("GET", "/items") not in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_chained_basepath(tmp_path: Path):
    """``new Hono().basePath('/api').get(...)`` bound to a variable should
    still register routes (even if basePath() is currently not composed
    into the final URL — document that limitation too)."""
    _write_ts(tmp_path, "admin-api/y.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const app = new Hono().basePath('/api');
        app.get('/health', async (c) => c.json({ ok: true }));
    """).strip())
    result = scan_hono(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    # Current limitation: basePath not composed. URL is '/health' not '/api/health'.
    # This test asserts the binding is still recognized (no false-negative
    # on all routes for chained constructors).
    assert ("GET", "/health") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_mounted_child_does_not_emit_root_version(tmp_path: Path):
    """When a child router is mounted under /settings/plans, its own routes
    should NOT also appear rooted at /. The unmounted /bulk-provider would
    be a lie — the child is never reachable at that path in openclaw."""
    _write_ts(tmp_path, "admin-api/src/routes/settings-plans.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const plans = new Hono();
        plans.put('/bulk-provider', async (c) => c.json({ ok: true }));
        export default plans;
    """).strip())
    _write_ts(tmp_path, "admin-api/src/index.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        import settingsPlans from './routes/settings-plans';
        const app = new Hono();
        app.route('/settings/plans', settingsPlans);
        export default app;
    """).strip())
    result = scan_hono(tmp_path)
    paths = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("PUT", "/settings/plans/bulk-provider") in paths
    assert ("PUT", "/bulk-provider") not in paths, \
        "mounted child should not also emit the root-less version"


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_unmounted_top_app_still_at_root(tmp_path: Path):
    """A top-level ``app`` (never mounted) must still register routes at /."""
    _write_ts(tmp_path, "admin-api/src/index.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const app = new Hono();
        app.get('/health', async (c) => c.json({ ok: true }));
        export default app;
    """).strip())
    result = scan_hono(tmp_path)
    paths = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/health") in paths


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_skips_test_files(tmp_path: Path):
    """``*.test.ts`` and files under ``__tests__/`` must not produce API
    nodes — they commonly build throwaway Hono apps for testing."""
    _write_ts(tmp_path, "admin-api/src/middleware/__tests__/rbac.test.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const app = new Hono();
        app.get('/agents', async (c) => c.json({ ok: true }));
    """).strip())
    _write_ts(tmp_path, "admin-api/src/unit.test.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const app = new Hono();
        app.post('/mock', async (c) => c.json({ ok: true }));
    """).strip())
    result = scan_hono(tmp_path)
    assert not any(n.get("kind") == "api" for n in result.nodes), \
        "test-file Hono apps should be skipped"


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_on_method_not_mistaken_for_path(tmp_path: Path):
    """``app.on("GET", "/x", handler)`` has METHOD as first arg, not a path.
    Our scanner must either drop this shape or correctly interpret it.
    The floor behavior: never emit an API with method ``ON`` or a fake URL."""
    _write_ts(tmp_path, "admin-api/src/x.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const app = new Hono();
        app.on("GET", "/x", async (c) => c.json({ ok: true }));
    """).strip())
    result = scan_hono(tmp_path)
    methods = {n["method"] for n in result.nodes if n.get("kind") == "api"}
    assert "ON" not in methods
    # Not also a bogus "GET" at "/GET" path (that would be the arg mis-read):
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/GET") not in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_dual_mount_under_versioned_prefixes(tmp_path: Path):
    """A child router mounted at both /v1/plans and /v2/plans must produce
    both composed URLs for every route it registers."""
    _write_ts(tmp_path, "admin-api/src/routes/plans.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const plans = new Hono();
        plans.get('/list', async (c) => c.json({ ok: true }));
        export default plans;
    """).strip())
    _write_ts(tmp_path, "admin-api/src/index.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        import plans from './routes/plans';
        const app = new Hono();
        app.route('/v1/plans', plans);
        app.route('/v2/plans', plans);
        export default app;
    """).strip())
    result = scan_hono(tmp_path)
    paths = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/v1/plans/list") in paths
    assert ("GET", "/v2/plans/list") in paths
    # Unmounted duplicate should not exist
    assert ("GET", "/list") not in paths


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_factory_pattern_documented_miss(tmp_path: Path):
    """``app.route('/preferences', buildPreferencesApp(db))`` — the child is a
    call expression, not an identifier. Document that we miss this shape
    today so future work can revisit."""
    _write_ts(tmp_path, "admin-api/src/routes/preferences.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        export function buildPreferencesApp(db: any) {
          const app = new Hono();
          app.get('/dashboard-layout', async (c) => c.json({ ok: true }));
          return app;
        }
    """).strip())
    _write_ts(tmp_path, "admin-api/src/index.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        import { buildPreferencesApp } from './routes/preferences';
        const app = new Hono();
        const db: any = {};
        app.route('/preferences', buildPreferencesApp(db));
        export default app;
    """).strip())
    result = scan_hono(tmp_path)
    paths = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    # Current limitation: factory pattern is not composed. Routes inside
    # buildPreferencesApp are emitted at the root of the factory's internal
    # app, not under /preferences. If we later resolve factory returns,
    # flip this test.
    assert ("GET", "/preferences/dashboard-layout") not in paths


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_hono_cross_file_mount(tmp_path: Path):
    """index.ts imports ./routes/settings-plans (default Hono binding) and
    mounts it under /settings/plans; inside that file plans.put('/bulk-provider')
    registers a route. Full path must compose to /settings/plans/bulk-provider."""
    _write_ts(tmp_path, "admin-api/src/routes/settings-plans.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        const plans = new Hono();
        plans.get('/', async (c) => c.json({ ok: true }));
        plans.put('/bulk-provider', async (c) => c.json({ ok: true }));
        export default plans;
    """).strip())
    _write_ts(tmp_path, "admin-api/src/index.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        import settingsPlans from './routes/settings-plans';
        const app = new Hono();
        app.route('/settings/plans', settingsPlans);
        export default app;
    """).strip())
    result = scan_hono(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("PUT", "/settings/plans/bulk-provider") in api_pairs
    assert ("GET", "/settings/plans") in api_pairs


# ── Cluster edgeless overlay ──────────────────────────────────────────


def test_cluster_edgeless_graph_still_separates_overlay():
    """Even when G has zero edges, route-typed nodes must share one synthetic
    community and not be interleaved with singleton code communities."""
    import networkx as nx
    from graphify.cluster import cluster

    G = nx.Graph()
    G.add_node("a", file_type="code")
    G.add_node("b", file_type="code")
    G.add_node("URL:/x", file_type="route")
    G.add_node("API:GET /x", file_type="route")
    # no edges
    communities = cluster(G)
    all_assigned = {n for nodes in communities.values() for n in nodes}
    assert all_assigned == set(G.nodes)
    # find the community containing route nodes
    route_cids = [cid for cid, nodes in communities.items()
                  if any(n.startswith("URL:") or n.startswith("API:") for n in nodes)]
    assert len(route_cids) == 1, "route nodes must be in one synthetic community"
    assert set(communities[route_cids[0]]) == {"URL:/x", "API:GET /x"}


# ── Proxy multi-service detection ─────────────────────────────────────


def test_scan_nextjs_proxy_emits_multiple_services(tmp_path: Path):
    """A proxy handler referencing two env API URLs should produce a
    SERVICE anchor for each."""
    proxy_body = textwrap.dedent("""
        export async function GET(request: Request) {
          const admin = process.env.ADMIN_API_URL;
          const billing = process.env.BILLING_API_URL;
          if (request.url.includes('billing')) return fetch(billing + '/x');
          return fetch(admin + '/x');
        }
    """).strip()
    _write_page(tmp_path, "app", "api", "proxy", "[...path]", "route.ts", body=proxy_body)
    _write_page(tmp_path, "app", "layout.tsx")
    result = scan_nextjs(tmp_path)
    service_nodes = [n for n in result.nodes if n.get("kind") == "service"]
    service_labels = {n["label"] for n in service_nodes}
    assert len(service_labels) >= 2, f"expected at least 2 services, got {service_labels}"


# ── AMBIGUOUS unresolved receiver ─────────────────────────────────────


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_ambiguous_unresolved_receiver_emits_handled_by(tmp_path: Path):
    """A Hono method call whose receiver is imported from a non-existent
    external module (so _resolve_binding_key returns None) must emit:
      - one API node (kind='api') with the correct route pattern
      - one placeholder handler node with kind='handler' and
        confidence='AMBIGUOUS'
      - one handled_by edge from the API node to the placeholder node
        with confidence='AMBIGUOUS' and reason='unresolved_receiver'

    Previously this call was silently skipped (continue). Now it must
    produce an AMBIGUOUS overlay so the route is visible in the graph
    without falsely attributing it to a concrete handler.
    """
    _write_ts(tmp_path, "admin-api/src/index.ts", textwrap.dedent("""
        import { Hono } from 'hono';
        import externalRouter from 'some-external-package-that-does-not-exist';
        const app = new Hono();
        externalRouter.get('/external/resource', async (c) => c.json({ ok: true }));
        app.get('/local', async (c) => c.json({ ok: true }));
        export default app;
    """).strip())
    result = scan_hono(tmp_path)

    # The /local route (resolved receiver) must still appear as EXTRACTED
    extracted_edges = [
        e for e in result.edges
        if e.get("confidence") == "EXTRACTED" and e.get("relation") == "handled_by"
    ]
    assert extracted_edges, "resolved routes must still emit EXTRACTED handled_by edges"

    # The /external/resource route (unresolved receiver) must now emit an
    # API node rather than being silently dropped
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/external/resource") in api_pairs, (
        "unresolved-receiver route must produce an API node with confidence=AMBIGUOUS"
    )

    # There must be an AMBIGUOUS handled_by edge sourced from that API node
    from graphify.routes import _api_node_id
    ambiguous_api_nid = _api_node_id("GET", "/external/resource")
    ambiguous_edges = [
        e for e in result.edges
        if e.get("source") == ambiguous_api_nid
        and e.get("relation") == "handled_by"
        and e.get("confidence") == "AMBIGUOUS"
    ]
    assert ambiguous_edges, (
        "unresolved-receiver route must emit a handled_by edge with confidence='AMBIGUOUS'"
    )
    assert ambiguous_edges[0].get("reason") == "unresolved_receiver", (
        "AMBIGUOUS handled_by edge must carry reason='unresolved_receiver'"
    )


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_ambiguous_handler_node_ids_distinct_across_files(tmp_path: Path):
    """Regression: two files with the same basename (e.g. index.ts) in different
    directories must NOT produce colliding ambiguous handler node IDs when they
    both call the same unresolved receiver on the same line number.

    Before the fix, ``_ambiguous_handler_node_id`` used only ``file_path.stem``
    (``"index"``), causing both placeholders to share the same node ID and
    NetworkX's ``add_node`` last-write-wins behaviour to silently merge them.
    After the fix, the full posix path is used so the IDs are distinct.
    """
    # Both files: same basename ("index.ts"), same receiver ("externalRouter"),
    # same method call line (line 4 in each file after dedent strip).
    shared_body = textwrap.dedent("""
        import { Hono } from 'hono';
        import externalRouter from 'some-external-package-that-does-not-exist';
        const app = new Hono();
        externalRouter.get('/items', async (c) => c.json({ ok: true }));
        export default app;
    """).strip()

    _write_ts(tmp_path, "apps/admin-api/src/index.ts", shared_body)
    _write_ts(tmp_path, "apps/billing-api/src/index.ts", shared_body)

    result = scan_hono(tmp_path)

    # There must be exactly 2 handler nodes with kind="handler" and AMBIGUOUS
    # confidence implied by the unresolved receiver path.
    handler_nodes = [n for n in result.nodes if n.get("kind") == "handler"]
    assert len(handler_nodes) == 2, (
        f"expected 2 distinct placeholder handler nodes, got {len(handler_nodes)}: "
        f"{[n['id'] for n in handler_nodes]}"
    )

    # The two handler node IDs must be distinct.
    handler_ids = [n["id"] for n in handler_nodes]
    assert handler_ids[0] != handler_ids[1], (
        "ambiguous handler node IDs must differ when source files share only the basename; "
        f"both resolved to: {handler_ids[0]!r}"
    )

    # Each placeholder node must preserve its own source_file attribute.
    source_files = {n.get("source_file") for n in handler_nodes}
    assert len(source_files) == 2, (
        f"each handler node must record its own source_file; got: {source_files}"
    )

    # Both handled_by edges must carry AMBIGUOUS confidence.
    ambiguous_edges = [
        e for e in result.edges
        if e.get("relation") == "handled_by" and e.get("confidence") == "AMBIGUOUS"
    ]
    assert len(ambiguous_edges) == 2, (
        f"expected 2 AMBIGUOUS handled_by edges, got {len(ambiguous_edges)}"
    )
