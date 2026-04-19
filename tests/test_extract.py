from pathlib import Path

import pytest

from graphify.extract import extract_python, extract, collect_files, _make_id

FIXTURES = Path(__file__).parent / "fixtures"


def _ts_parser_available() -> bool:
    try:
        import tree_sitter_typescript  # noqa: F401
        from tree_sitter import Language, Parser  # noqa: F401
        return True
    except Exception:
        return False


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_make_id_strips_dots_and_underscores():
    assert _make_id("_auth") == "auth"
    assert _make_id(".httpx._client") == "httpx_client"


def test_make_id_consistent():
    """Same input always produces same output."""
    assert _make_id("foo", "Bar") == _make_id("foo", "Bar")


def test_make_id_no_leading_trailing_underscores():
    result = _make_id("__init__")
    assert not result.startswith("_")
    assert not result.endswith("_")


def test_extract_python_finds_class():
    result = extract_python(FIXTURES / "sample.py")
    labels = [n["label"] for n in result["nodes"]]
    assert "Transformer" in labels


def test_extract_python_finds_methods():
    result = extract_python(FIXTURES / "sample.py")
    labels = [n["label"] for n in result["nodes"]]
    assert any("__init__" in l or "forward" in l for l in labels)


def test_extract_python_no_dangling_edges():
    """All edge sources must reference a known node (targets may be external imports)."""
    result = extract_python(FIXTURES / "sample.py")
    node_ids = {n["id"] for n in result["nodes"]}
    for edge in result["edges"]:
        assert edge["source"] in node_ids, f"Dangling source: {edge['source']}"


def test_structural_edges_are_extracted():
    """contains / method / inherits / imports edges must always be EXTRACTED."""
    result = extract_python(FIXTURES / "sample.py")
    structural = {"contains", "method", "inherits", "imports", "imports_from"}
    for edge in result["edges"]:
        if edge["relation"] in structural:
            assert edge["confidence"] == "EXTRACTED", f"Expected EXTRACTED: {edge}"


def test_extract_merges_multiple_files():
    files = list(FIXTURES.glob("*.py"))
    result = extract(files)
    assert len(result["nodes"]) > 0
    assert result["input_tokens"] == 0


def test_collect_files_from_dir():
    files = collect_files(FIXTURES)
    supported = {".py", ".js", ".ts", ".tsx", ".go", ".rs",
                 ".java", ".c", ".cpp", ".cc", ".cxx", ".rb",
                 ".cs", ".kt", ".kts", ".scala", ".php", ".h", ".hpp",
                 ".swift", ".lua", ".toc", ".zig", ".ps1", ".ex", ".exs",
                 ".m", ".mm"}
    assert all(f.suffix in supported for f in files)
    assert len(files) > 0


def test_collect_files_skips_hidden():
    files = collect_files(FIXTURES)
    for f in files:
        assert not any(part.startswith(".") for part in f.parts)


def test_collect_files_follows_symlinked_directory(tmp_path):
    real_dir = tmp_path / "real_src"
    real_dir.mkdir()
    (real_dir / "lib.py").write_text("x = 1")
    (tmp_path / "linked_src").symlink_to(real_dir)

    files_no = collect_files(tmp_path, follow_symlinks=False)
    files_yes = collect_files(tmp_path, follow_symlinks=True)

    assert [f.name for f in files_no].count("lib.py") == 1
    assert [f.name for f in files_yes].count("lib.py") == 2


def test_collect_files_handles_circular_symlinks(tmp_path):
    sub = tmp_path / "pkg"
    sub.mkdir()
    (sub / "mod.py").write_text("x = 1")
    (sub / "cycle").symlink_to(tmp_path)

    files = collect_files(tmp_path, follow_symlinks=True)
    assert any(f.name == "mod.py" for f in files)


def test_no_dangling_edges_on_extract():
    """After merging multiple files, no internal edges should be dangling."""
    files = list(FIXTURES.glob("*.py"))
    result = extract(files)
    node_ids = {n["id"] for n in result["nodes"]}
    internal_relations = {"contains", "method", "inherits", "calls"}
    for edge in result["edges"]:
        if edge["relation"] in internal_relations:
            assert edge["source"] in node_ids, f"Dangling source: {edge}"
            assert edge["target"] in node_ids, f"Dangling target: {edge}"


def test_calls_edges_emitted():
    """Call-graph pass must produce INFERRED calls edges."""
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = [e for e in result["edges"] if e["relation"] == "calls"]
    assert len(calls) > 0, "Expected at least one calls edge"


def test_calls_edges_are_extracted():
    """AST-resolved call edges are deterministic and should be EXTRACTED/1.0."""
    result = extract_python(FIXTURES / "sample_calls.py")
    for edge in result["edges"]:
        if edge["relation"] == "calls":
            assert edge["confidence"] == "EXTRACTED"
            assert edge["weight"] == 1.0


def test_calls_no_self_loops():
    result = extract_python(FIXTURES / "sample_calls.py")
    for edge in result["edges"]:
        if edge["relation"] == "calls":
            assert edge["source"] != edge["target"], f"Self-loop: {edge}"


def test_run_analysis_calls_compute_score():
    """run_analysis() calls compute_score() - must appear as a calls edge."""
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}
    node_by_label = {n["label"]: n["id"] for n in result["nodes"]}
    src = node_by_label.get("run_analysis()")
    tgt = node_by_label.get("compute_score()")
    assert src and tgt, "run_analysis or compute_score node not found"
    assert (src, tgt) in calls, f"run_analysis -> compute_score not found in {calls}"


def test_run_analysis_calls_normalize():
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}
    node_by_label = {n["label"]: n["id"] for n in result["nodes"]}
    src = node_by_label.get("run_analysis()")
    tgt = node_by_label.get("normalize()")
    assert src and tgt
    assert (src, tgt) in calls


def test_method_calls_module_function():
    """Analyzer.process() calls run_analysis() - cross class→function calls edge."""
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}
    node_by_label = {n["label"]: n["id"] for n in result["nodes"]}
    src = node_by_label.get(".process()")
    tgt = node_by_label.get("run_analysis()")
    assert src and tgt
    assert (src, tgt) in calls


def test_calls_deduplication():
    """Same caller→callee pair must appear only once even if called multiple times."""
    result = extract_python(FIXTURES / "sample_calls.py")
    call_pairs = [(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"]
    assert len(call_pairs) == len(set(call_pairs)), "Duplicate calls edges found"


# ───── TS namespace-import cross-file resolution (v0.5.2) ───────────────


def _calls_edges(result) -> set[tuple[str, str]]:
    return {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}


def _label_to_id(result) -> dict[str, str]:
    return {n["label"]: n["id"] for n in result["nodes"]}


@pytest.mark.skipif(not _ts_parser_available(), reason="tree-sitter-typescript not available")
def test_namespace_import_member_call_emits_calls_edge(tmp_path: Path):
    """``import * as authService from './auth-service'`` + ``authService.login()``
    must produce a cross-file ``calls`` edge."""
    _write(tmp_path / "auth-service.ts",
           "export function login(u: string) { return u; }\n")
    _write(tmp_path / "caller.ts",
           "import * as authService from './auth-service';\n"
           "export function handler(u: string) { return authService.login(u); }\n")
    result = extract(collect_files(tmp_path))
    label_to_id = _label_to_id(result)
    handler_id = label_to_id["handler()"]
    # login() is defined inside auth-service.ts; it's a top-level function so
    # it should appear as a node with label "login()".
    login_id = label_to_id["login()"]
    assert (handler_id, login_id) in _calls_edges(result)


@pytest.mark.skipif(not _ts_parser_available(), reason="tree-sitter-typescript not available")
def test_namespace_import_arrow_function_export(tmp_path: Path):
    """The real openclaw service pattern: ``export const login = async (…) => {}``.
    The generic JS extra walker registers this via
    ``lexical_declaration -> variable_declarator -> arrow_function``."""
    _write(tmp_path / "auth-service.ts",
           "export const login = async (u: string) => { return u; };\n")
    _write(tmp_path / "caller.ts",
           "import * as authService from './auth-service';\n"
           "export function handler(u: string) { return authService.login(u); }\n")
    result = extract(collect_files(tmp_path))
    label_to_id = _label_to_id(result)
    handler_id = label_to_id["handler()"]
    login_id = label_to_id.get("login()")
    assert login_id is not None, "arrow-function export should register a 'login()' node"
    assert (handler_id, login_id) in _calls_edges(result)


@pytest.mark.skipif(not _ts_parser_available(), reason="tree-sitter-typescript not available")
def test_namespace_import_disambiguates_same_name_across_files(tmp_path: Path):
    """Two files each export ``login``. The caller imports one via namespace
    and calls ``X.login()`` — the edge must point at that file's ``login``,
    not the other."""
    _write(tmp_path / "auth-service.ts",
           "export function login() { return 'auth'; }\n")
    _write(tmp_path / "user-service.ts",
           "export function login() { return 'user'; }\n")
    _write(tmp_path / "caller.ts",
           "import * as authService from './auth-service';\n"
           "export function handler() { return authService.login(); }\n")
    result = extract(collect_files(tmp_path))
    # Find the login node whose source_file is auth-service.ts specifically.
    auth_login_id = next(
        n["id"] for n in result["nodes"]
        if n["label"] == "login()" and n.get("source_file", "").endswith("auth-service.ts")
    )
    handler_id = _label_to_id(result)["handler()"]
    # The edge must go to auth-service's login, not user-service's.
    edges = _calls_edges(result)
    assert (handler_id, auth_login_id) in edges
    # There must be no edge from handler to user-service's login.
    user_login_id = next(
        n["id"] for n in result["nodes"]
        if n["label"] == "login()" and n.get("source_file", "").endswith("user-service.ts")
    )
    assert (handler_id, user_login_id) not in edges


@pytest.mark.skipif(not _ts_parser_available(), reason="tree-sitter-typescript not available")
def test_namespace_import_no_global_fallback(tmp_path: Path):
    """If the namespace-aliased file does NOT define the callee, no edge
    must be emitted — even if a same-named function exists elsewhere."""
    _write(tmp_path / "auth-service.ts",
           "export function signin() { return 0; }\n")  # no 'login'
    _write(tmp_path / "other.ts",
           "export function login() { return 1; }\n")   # not imported
    _write(tmp_path / "caller.ts",
           "import * as authService from './auth-service';\n"
           "export function handler() { return authService.login(); }\n")
    result = extract(collect_files(tmp_path))
    handler_id = _label_to_id(result)["handler()"]
    other_login_id = next(
        n["id"] for n in result["nodes"]
        if n["label"] == "login()" and n.get("source_file", "").endswith("other.ts")
    )
    # No wrong-file attribution via global fallback.
    assert (handler_id, other_login_id) not in _calls_edges(result)


@pytest.mark.skipif(not _ts_parser_available(), reason="tree-sitter-typescript not available")
def test_member_call_without_namespace_alias_falls_back_to_global(tmp_path: Path):
    """``foo.bar()`` where ``foo`` is an arbitrary local variable (not a
    namespace alias) must still resolve via the existing global label pass
    — the namespace fix is additive."""
    _write(tmp_path / "helpers.ts",
           "export function formatName(x: string) { return x; }\n")
    _write(tmp_path / "caller.ts",
           "const foo = { someMethod: () => 1 };\n"
           "export function handler() { formatName('a'); return foo.someMethod(); }\n")
    result = extract(collect_files(tmp_path))
    handler_id = _label_to_id(result)["handler()"]
    format_id = next(
        n["id"] for n in result["nodes"]
        if n["label"] == "formatName()"
    )
    # formatName() resolution via global label fallback still works.
    assert (handler_id, format_id) in _calls_edges(result)


@pytest.mark.skipif(not _ts_parser_available(), reason="tree-sitter-typescript not available")
def test_namespace_import_shadowed_by_local_symbol(tmp_path: Path):
    """A local ``login()`` in the caller file must NOT shadow
    ``authService.login()`` — the namespace branch bypasses local
    label_to_nid and scopes the lookup to the aliased file."""
    _write(tmp_path / "auth-service.ts",
           "export function login() { return 'auth'; }\n")
    _write(tmp_path / "caller.ts",
           "import * as authService from './auth-service';\n"
           "function login() { return 'local'; }\n"  # local shadow
           "export function handler() { return authService.login(); }\n")
    result = extract(collect_files(tmp_path))
    auth_login_id = next(
        n["id"] for n in result["nodes"]
        if n["label"] == "login()" and n.get("source_file", "").endswith("auth-service.ts")
    )
    local_login_id = next(
        n["id"] for n in result["nodes"]
        if n["label"] == "login()" and n.get("source_file", "").endswith("caller.ts")
    )
    handler_id = _label_to_id(result)["handler()"]
    edges = _calls_edges(result)
    assert (handler_id, auth_login_id) in edges, "namespace call must resolve to auth-service.login"
    assert (handler_id, local_login_id) not in edges, "local login() must not shadow namespace call"
