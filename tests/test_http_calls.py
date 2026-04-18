"""Tests for graphify.http_calls — wrapper-aware HTTP call-site extractor."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from graphify.http_calls import scan, HttpCallsResult


def _ts_fixture_available() -> bool:
    try:
        import tree_sitter_typescript  # noqa: F401
        from tree_sitter import Language, Parser  # noqa: F401
        return True
    except Exception:
        return False


# ───── Fixture helpers ──────────────────────────────────────────────────


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _mk_wrapper_project(tmp_path: Path) -> None:
    """A minimal Next.js-style project with tsconfig `@/*` alias, a wrapper
    module ``@/lib/api-client``, and a hook file that calls it."""
    _write(tmp_path / "tsconfig.json", textwrap.dedent("""
        {
          "compilerOptions": {
            "baseUrl": ".",
            "paths": { "@/*": ["src/*"] }
          }
        }
    """).strip())
    _write(tmp_path / "src" / "lib" / "api-client.ts", textwrap.dedent("""
        const BASE = process.env.API_BASE_URL;
        export async function get(endpoint: string, init?: RequestInit) {
          return fetch(`${BASE}${endpoint}`, { method: 'GET', ...init });
        }
        export async function post(endpoint: string, body: any, init?: RequestInit) {
          return fetch(`${BASE}${endpoint}`, { method: 'POST', body: JSON.stringify(body), ...init });
        }
        export async function del(endpoint: string, init?: RequestInit) {
          return fetch(`${BASE}${endpoint}`, { method: 'DELETE', ...init });
        }
        export default { get, post, del };
    """).strip())


# ───── Basic API node emission ──────────────────────────────────────────


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_detects_named_wrapper_call(tmp_path: Path):
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-agent-actions.ts", textwrap.dedent("""
        import { post } from '@/lib/api-client';
        export async function startAgent(id: string) {
          return post(`/agents/${id}/start`, {});
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("POST", "/agents/:id/start") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_detects_default_import_object_call(tmp_path: Path):
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-agents.ts", textwrap.dedent("""
        import apiClient from '@/lib/api-client';
        export async function listAgents() {
          return apiClient.get('/agents');
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/agents") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_template_literal_param_normalized(tmp_path: Path):
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-plans.ts", textwrap.dedent("""
        import { post, del } from '@/lib/api-client';
        export async function bulk(planId: string) {
          await post(`/plans/${planId}/bulk-provider`, {});
          await del(`/plans/${planId}`);
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("POST", "/plans/:planId/bulk-provider") in api_pairs
    assert ("DELETE", "/plans/:planId") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_raw_fetch_fallback(tmp_path: Path):
    """Plain fetch() calls outside the wrapper still produce API nodes."""
    _write(tmp_path / "src" / "hooks" / "raw.ts", textwrap.dedent("""
        export async function ping() {
          return fetch('/api/health');
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/api/health") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_fetch_with_method_option(tmp_path: Path):
    _write(tmp_path / "src" / "page.tsx", textwrap.dedent("""
        export default function Page() {
          async function doit() {
            await fetch('/api/tasks/123', { method: 'DELETE' });
          }
          return null;
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("DELETE", "/api/tasks/123") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_fetch_external_url_skipped(tmp_path: Path):
    _write(tmp_path / "src" / "hooks" / "external.ts", textwrap.dedent("""
        export async function loadMap() {
          return fetch('https://maps.example.com/tiles');
        }
    """).strip())
    result = scan(tmp_path)
    # External URLs must not produce API nodes (they would be unresolvable
    # inside the project graph).
    for n in result.nodes:
        if n.get("kind") == "api":
            assert not n["url_pattern"].startswith("http")


# ───── Wrapper identification ───────────────────────────────────────────


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_non_wrapper_module_call_is_ignored(tmp_path: Path):
    """post() imported from a non-wrapper module must NOT produce an API.

    api-client-looking imports are auto-trusted, but generic utility modules
    named e.g. 'utils/date' are not. Otherwise importing a helper named
    `post` from an unrelated module would produce bogus endpoints.
    """
    # No tsconfig / no @-alias. Users may still import relative utilities.
    _write(tmp_path / "src" / "utils" / "format.ts", textwrap.dedent("""
        export function post(text: string) { return '[' + text + ']'; }
    """).strip())
    _write(tmp_path / "src" / "page.tsx", textwrap.dedent("""
        import { post } from './utils/format';
        export default function Page() {
          return post('hello');
        }
    """).strip())
    result = scan(tmp_path)
    api_nodes = [n for n in result.nodes if n.get("kind") == "api"]
    assert api_nodes == []


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_explicit_override_via_graphify_dir(tmp_path: Path):
    """.graphify/http-wrappers.json overrides detection — a module that
    would not be auto-detected can be registered as a wrapper explicitly."""
    _write(tmp_path / "tsconfig.json", textwrap.dedent("""
        {"compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}}
    """).strip())
    _write(tmp_path / "src" / "services" / "custom-http.ts", textwrap.dedent("""
        export async function send(endpoint: string, body: any) {
          return fetch(endpoint, { method: 'POST', body: JSON.stringify(body) });
        }
    """).strip())
    _write(tmp_path / ".graphify" / "http-wrappers.json", textwrap.dedent("""
        {"modules": {"@/services/custom-http": ["send"]}}
    """).strip())
    _write(tmp_path / "src" / "hooks" / "use-send.ts", textwrap.dedent("""
        import { send } from '@/services/custom-http';
        export async function submit(text: string) {
          return send('/custom/submit', { text });
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    # send has no standard method name; fall back to AMBIGUOUS method 'ANY'
    methods = {m for (m, _) in api_pairs}
    assert any(p == "/custom/submit" for (_, p) in api_pairs)
    assert "ANY" in methods or "POST" in methods


# ───── calls_http edge targets ─────────────────────────────────────────


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_calls_http_edge_relation_is_correct(tmp_path: Path):
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-x.ts", textwrap.dedent("""
        import { post } from '@/lib/api-client';
        export async function go(id: string) { return post(`/x/${id}`, {}); }
    """).strip())
    result = scan(tmp_path)
    calls_http = [e for e in result.edges if e.get("relation") == "calls_http"]
    assert calls_http, "expected at least one calls_http edge"
    # Edge must carry method attr matching the wrapper name
    assert all(e.get("method") for e in calls_http)
    assert any(e.get("method") == "POST" for e in calls_http)


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_api_node_id_matches_routes_scheme(tmp_path: Path):
    """API:<METHOD> <path> node IDs must match graphify.routes._api_node_id
    so http_calls edges land on the same target nodes routes.py emits."""
    from graphify.routes import _api_node_id
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-y.ts", textwrap.dedent("""
        import { get } from '@/lib/api-client';
        export async function load() { return get('/items'); }
    """).strip())
    result = scan(tmp_path)
    api_nids = {n["id"] for n in result.nodes if n.get("kind") == "api"}
    assert _api_node_id("GET", "/items") in api_nids


# ───── Result type shape ────────────────────────────────────────────────


def test_scan_empty_project_returns_empty_result(tmp_path: Path):
    result = scan(tmp_path)
    assert isinstance(result, HttpCallsResult)
    assert result.nodes == []
    assert result.edges == []


# ───── Test-file skip (mirror of routes.py behavior) ────────────────────


# ───── Codex feedback: query stripping, binary concat, class methods, typed miss ──


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_query_string_stripped_from_endpoint(tmp_path: Path):
    """Real openclaw call: del(`/settings/plans/${id}?country_code=${cc}`).
    The BE route is path-only, so we must dedupe by stripping ?query."""
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-del.ts", textwrap.dedent("""
        import { del } from '@/lib/api-client';
        export async function remove(id: string, cc: string) {
          await del(`/settings/plans/${id}?country_code=${cc}`);
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("DELETE", "/settings/plans/:id") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_binary_concat_url_normalized(tmp_path: Path):
    """Openclaw uses `'/users/' + userId + '/reset-password'` for some ops.
    Extract this into /users/:userId/reset-password."""
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-reset.ts", textwrap.dedent("""
        import { post } from '@/lib/api-client';
        export async function resetPassword(userId: string) {
          return post('/users/' + userId + '/reset-password', {});
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("POST", "/users/:userId/reset-password") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_env_base_template_fetch(tmp_path: Path):
    """`fetch(`${ADMIN_API_URL}/api/legal/terms`)` — the base URL is a
    template substitution and should not be treated as an external URL;
    the rest of the path should be extracted exactly."""
    _write(tmp_path / "src" / "lib" / "legal.ts", textwrap.dedent("""
        const ADMIN_API_URL = process.env.ADMIN_API_URL || '';
        export async function getTerms() {
          return fetch(`${ADMIN_API_URL}/api/legal/terms`);
        }
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("GET", "/api/legal/terms") in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_env_base_only_no_path_is_skipped(tmp_path: Path):
    """A fetch that resolves to just an env-base placeholder (no real path)
    must NOT emit an API node — it is unresolvable."""
    _write(tmp_path / "src" / "lib" / "bootstrap.ts", textwrap.dedent("""
        const BASE = process.env.BASE || '';
        export async function ping() { return fetch(`${BASE}`); }
    """).strip())
    result = scan(tmp_path)
    api_nodes = [n for n in result.nodes if n.get("kind") == "api"]
    assert api_nodes == []


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_binary_concat_non_plus_not_rendered(tmp_path: Path):
    """Subtract/multiply chains must not be misinterpreted as URL building."""
    _mk_wrapper_project(tmp_path)
    _write(tmp_path / "src" / "hooks" / "use-math.ts", textwrap.dedent("""
        import { post } from '@/lib/api-client';
        export async function go(n: number) {
          // Contrived: first arg is not a URL at all — we expect post() to be
          // ignored because its first arg isn't a string/template/+-concat.
          return post(('x' * n) as any, {});
        }
    """).strip())
    result = scan(tmp_path)
    api_nodes = [n for n in result.nodes if n.get("kind") == "api"]
    assert api_nodes == []


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_class_method_caller_id_matches_ast(tmp_path: Path):
    """A raw fetch inside a class method must anchor to the AST class
    method id (_make_id(_make_id(stem, class), method)), not just
    _make_id(stem, method), so the edge does not dangle."""
    from graphify.extract import _make_id
    _write(tmp_path / "src" / "services" / "manager.ts", textwrap.dedent("""
        class Manager {
          async sync() {
            return fetch('/api/manager/sync', { method: 'POST' });
          }
        }
    """).strip())
    result = scan(tmp_path)
    # Expected caller id uses class-scoped _make_id scheme
    stem = "manager"
    expected = _make_id(_make_id(stem, "Manager"), "sync")
    call_edges = [e for e in result.edges if e.get("relation") == "calls_http"]
    assert any(e["source"] == expected for e in call_edges), \
        f"expected caller id {expected} among {[e['source'] for e in call_edges]}"


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_typed_client_method_documented_miss(tmp_path: Path):
    """apiClient.fetchMilestones() is a typed client method, not an HTTP
    verb — Phase H v1 does not inspect the method body, so this shape is
    a documented miss."""
    _write(tmp_path / "tsconfig.json", textwrap.dedent("""
        {"compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}}
    """).strip())
    _write(tmp_path / "src" / "lib" / "api-client.ts", textwrap.dedent("""
        export const apiClient = {
          fetchMilestones: async () => fetch('/api/milestones'),
          search: async (q: string) => fetch('/api/search?q=' + encodeURIComponent(q)),
        };
    """).strip())
    _write(tmp_path / "src" / "hooks" / "use-typed.ts", textwrap.dedent("""
        import { apiClient } from '@/lib/api-client';
        export async function load() { return apiClient.fetchMilestones(); }
    """).strip())
    result = scan(tmp_path)
    # No HTTP-verb property is called at the usage site → no API node emitted
    # at that call. Document the limitation; future work can resolve method
    # bodies.
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    # Wrapper internals do not bubble up; only caller-site calls generate
    # endpoints. Caller uses fetchMilestones which is not a verb.
    assert ("GET", "/api/milestones") not in api_pairs


@pytest.mark.skipif(not _ts_fixture_available(), reason="tree-sitter-typescript not available")
def test_scan_skips_test_files(tmp_path: Path):
    _write(tmp_path / "tsconfig.json", textwrap.dedent("""
        {"compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}}
    """).strip())
    _write(tmp_path / "src" / "lib" / "api-client.ts", textwrap.dedent("""
        export async function post(endpoint: string) {
          return fetch(endpoint, { method: 'POST' });
        }
    """).strip())
    _write(tmp_path / "src" / "__tests__" / "api.test.ts", textwrap.dedent("""
        import { post } from '@/lib/api-client';
        test('it posts', async () => { await post('/fake-endpoint'); });
    """).strip())
    result = scan(tmp_path)
    api_pairs = {(n["method"], n["url_pattern"]) for n in result.nodes if n.get("kind") == "api"}
    assert ("POST", "/fake-endpoint") not in api_pairs
