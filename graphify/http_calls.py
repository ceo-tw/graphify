"""Wrapper-aware HTTP call-site extractor.

openclaw-cloud and most Next.js apps route browser→server traffic through a
wrapper module (``@/lib/api-client`` or similar) rather than calling
``fetch``/``axios`` directly in component files. Detecting only raw
``fetch`` calls produces a gap that severs the FE→BE graph edge almost
everywhere. This module closes that gap.

Outputs two kinds of artefacts consumable by the existing graphify pipeline:

  * ``API:<METHOD> <pattern>`` nodes with ``file_type="route"`` — the same
    shape :mod:`graphify.routes` emits for backend routes, so edges produced
    here deduplicate naturally against routes.scan() output.
  * ``calls_http`` edges pointing from a caller anchor (the enclosing
    function id using the AST ``_make_id(stem, name)`` convention, falling
    back to the file-level id) to the API node.

Wrapper discovery:

  1. Automatic heuristics. Any TS file whose name matches common
     api-client patterns and whose exported functions actually contain
     ``fetch(``/``axios.`` are treated as wrappers.
  2. Explicit override: ``<project>/.graphify/http-wrappers.json`` with the
     shape ``{"modules": {"<module-spec>": ["<fn-name>", ...]}}``. Overrides
     win over detection and may register wrappers that would not match any
     heuristic (for example ``send`` or ``request`` in a custom service).
"""
from __future__ import annotations

import importlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .extract import _make_id
from .routes import _api_node_id, _normalize_url_pattern, _is_test_file
from .tsconfig_paths import resolve_import, TsconfigResolver


# ───── Data ─────────────────────────────────────────────────────────────


@dataclass
class HttpCallsResult:
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)


# ───── Method + URL normalisation helpers ──────────────────────────────


_HTTP_METHOD_NAMES = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
    "del": "DELETE",           # common alias (openclaw uses this)
    "head": "HEAD",
    "options": "OPTIONS",
}

# Wrapper filename heuristics. A file matching any of these is considered
# a candidate api-client unless explicitly excluded.
_WRAPPER_FILE_PATTERNS = (
    re.compile(r"(^|/)api-client\.(ts|tsx|js|jsx)$"),
    re.compile(r"(^|/)api\.(ts|tsx|js|jsx)$"),
    re.compile(r"(^|/)(lib|src)/api(-[\w-]+)?(\.ts|\.tsx|\.js|\.jsx)$"),
    re.compile(r"(^|/)services/api([\w-]*)(\.ts|\.tsx|\.js|\.jsx)$"),
    re.compile(r"(^|/)http(-[\w-]+)?\.(ts|tsx|js|jsx)$"),
)

# Methods we will treat as "definitely HTTP" in a wrapper module body.
_FETCH_AXIOS_SENTINELS = ("fetch(", "axios.", "axios(")


def _method_from_name(name: str) -> Optional[str]:
    return _HTTP_METHOD_NAMES.get(name)


def _is_external_url(url: str) -> bool:
    return url.startswith(("http://", "https://", "//"))


def _strip_query_and_hash(url: str) -> str:
    """Drop ``?query`` and ``#hash`` suffixes so FE calls with query params
    dedupe cleanly against BE route nodes which never carry a query string."""
    for sep in ("?", "#"):
        idx = url.find(sep)
        if idx != -1:
            url = url[:idx]
    return url


def _strip_env_base_prefix(url: str) -> Optional[str]:
    """If ``url`` begins with a ``:name`` substitution placeholder produced
    by template-literal normalisation of ``${ADMIN_API_URL}`` style base
    prefixes, drop it so the remaining path matches BE route patterns.

    Returns ``None`` when the URL is purely an env-base placeholder with no
    tangible path (``:ADMIN_API_URL``, ``:BASE``) — caller should skip the
    call rather than emit a meaningless API node.
    """
    if url.startswith(":") and "/" in url:
        # e.g. ':ADMIN_API_URL/api/legal/terms' → '/api/legal/terms'
        _, _, rest = url.partition("/")
        if not rest:
            return None
        return "/" + rest
    if url.startswith(":") and "/" not in url:
        return None
    return url


# ───── tree-sitter setup ────────────────────────────────────────────────


def _load_ts_parser():
    try:
        mod = importlib.import_module("tree_sitter_typescript")
        from tree_sitter import Language, Parser
        lang_fn = getattr(mod, "language_typescript", None)
        if lang_fn is None:
            return None, None
        return Parser(Language(lang_fn())), Language(lang_fn())
    except Exception:
        return None, None


def _load_tsx_parser():
    try:
        mod = importlib.import_module("tree_sitter_typescript")
        from tree_sitter import Language, Parser
        lang_fn = getattr(mod, "language_tsx", None)
        if lang_fn is None:
            return None, None
        return Parser(Language(lang_fn())), Language(lang_fn())
    except Exception:
        return None, None


def _get_text(node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _iter_tree(node):
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        for c in reversed(n.children):
            stack.append(c)


def _string_literal_value(node, source: bytes) -> Optional[str]:
    """Return the text of a string/template/binary literal with interpolated
    identifiers normalised to ``:name``.

    Accepts three shapes:

      * ``string`` —   'abc' / "abc"
      * ``template_string`` —  `/foo/${id}`  → ``/foo/:id``
      * ``binary_expression`` (``+`` chains) —  '/foo/' + id + '/x' → ``/foo/:id/x``
    """
    if node is None:
        return None
    if node.type == "string":
        raw = _get_text(node, source)
        if len(raw) >= 2 and raw[0] in ("'", '"', "`") and raw[-1] in ("'", '"', "`"):
            return raw[1:-1]
        return raw
    if node.type == "template_string":
        out: list[str] = []
        for child in node.children:
            t = child.type
            if t in ("`",):
                continue
            text = _get_text(child, source)
            if t == "template_substitution":
                inner = text.strip("${}").strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", inner):
                    out.append(f":{inner}")
                elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\??\.[A-Za-z_][A-Za-z0-9_]*", inner):
                    # `state.id` → `:id`
                    out.append(f":{inner.rsplit('.', 1)[-1]}")
                else:
                    out.append(":param")
            else:
                out.append(text)
        return "".join(out)
    if node.type == "binary_expression":
        return _binary_concat_to_url(node, source)
    return None


def _binary_concat_to_url(node, source: bytes) -> Optional[str]:
    """Normalise ``'/foo/' + id + '/bar'`` to ``/foo/:id/bar``.

    Operand types we accept:

      * nested ``binary_expression`` with operator ``+`` (recurse)
      * ``string`` literal (take its raw value)
      * ``identifier`` (normalise to ``:name``)
      * ``member_expression`` with identifier property (normalise to ``:prop``)

    Returns ``None`` when the expression is not a pure ``+`` concatenation,
    so non-URL arithmetic is not misinterpreted.
    """
    op_node = node.child_by_field_name("operator")
    if op_node is not None and _get_text(op_node, source).strip() != "+":
        return None
    left = node.child_by_field_name("left")
    right = node.child_by_field_name("right")
    if left is None or right is None:
        return None

    def _render(operand) -> Optional[str]:
        t = operand.type
        if t == "string":
            return _string_literal_value(operand, source)
        if t == "template_string":
            return _string_literal_value(operand, source)
        if t == "identifier":
            return f":{_get_text(operand, source)}"
        if t == "member_expression":
            prop = operand.child_by_field_name("property")
            if prop is not None and prop.type in ("property_identifier", "identifier"):
                return f":{_get_text(prop, source)}"
            return ":param"
        if t == "binary_expression":
            return _binary_concat_to_url(operand, source)
        if t == "call_expression":
            return ":param"
        return None

    left_s = _render(left)
    right_s = _render(right)
    if left_s is None or right_s is None:
        return None
    return left_s + right_s


def _extract_method_option(arg_node, source: bytes) -> Optional[str]:
    """Look for ``{ method: "POST" }`` inside a fetch init object literal."""
    if arg_node is None or arg_node.type != "object":
        return None
    for child in arg_node.children:
        if child.type != "pair":
            continue
        key_node = child.child_by_field_name("key")
        val_node = child.child_by_field_name("value")
        if key_node is None or val_node is None:
            continue
        key_text = _get_text(key_node, source).strip("'\"`")
        if key_text != "method":
            continue
        val = _string_literal_value(val_node, source)
        if val:
            return val.upper()
    return None


# ───── File discovery ───────────────────────────────────────────────────


def _ts_files_under(project_root: Path) -> Iterable[Path]:
    skip = {"node_modules", ".next", ".git", "dist", "build"}
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if not fn.endswith((".ts", ".tsx", ".js", ".jsx")):
                continue
            if fn.endswith(".d.ts"):
                continue
            p = Path(dirpath) / fn
            if _is_test_file(p):
                continue
            yield p


def _file_matches_wrapper_heuristic(p: Path) -> bool:
    rel = str(p).replace("\\", "/")
    for pat in _WRAPPER_FILE_PATTERNS:
        if pat.search(rel):
            return True
    return False


# ───── Wrapper discovery ────────────────────────────────────────────────


def _exported_top_level_fn_names(source_bytes: bytes, root) -> set[str]:
    """Return names exported from the file body (top-level ``export`` and
    ``export default { ... }``)."""
    names: set[str] = set()
    for child in root.children:
        t = child.type
        if t != "export_statement":
            continue
        # export (async) function NAME
        for sub in child.children:
            if sub.type in ("function_declaration",):
                name_node = sub.child_by_field_name("name")
                if name_node is not None:
                    names.add(_get_text(name_node, source_bytes))
            elif sub.type in ("lexical_declaration", "variable_declaration"):
                for v in sub.children:
                    if v.type == "variable_declarator":
                        nm = v.child_by_field_name("name")
                        if nm is not None and nm.type == "identifier":
                            names.add(_get_text(nm, source_bytes))
            elif sub.type == "object":
                # export default { a, b }
                for pair in sub.children:
                    if pair.type == "shorthand_property_identifier":
                        names.add(_get_text(pair, source_bytes))
                    elif pair.type == "pair":
                        k = pair.child_by_field_name("key")
                        if k is not None and k.type in ("property_identifier", "identifier"):
                            names.add(_get_text(k, source_bytes))
    return names


def _auto_detect_wrappers(
    project_root: Path,
    parser_ts,
    parser_tsx,
) -> dict[Path, set[str]]:
    """Find wrapper modules by filename + body-content heuristic.

    Returns ``{resolved_path: {exported_fn_name, …}}``.
    """
    wrappers: dict[Path, set[str]] = {}
    for p in _ts_files_under(project_root):
        if not _file_matches_wrapper_heuristic(p):
            continue
        try:
            source = p.read_bytes()
        except OSError:
            continue
        body_text = source.decode("utf-8", errors="replace")
        if not any(s in body_text for s in _FETCH_AXIOS_SENTINELS):
            continue
        parser = parser_tsx if p.suffix == ".tsx" else parser_ts
        if parser is None:
            continue
        try:
            tree = parser.parse(source)
        except Exception:
            continue
        root = tree.root_node
        if root is None:
            continue
        names = _exported_top_level_fn_names(source, root)
        if not names:
            continue
        wrappers[p.resolve()] = names
    return wrappers


def _load_explicit_wrappers(project_root: Path) -> dict[str, set[str]]:
    """Return ``{module_spec: {fn_name, …}}`` from .graphify/http-wrappers.json.

    Module spec is kept as-is (e.g. ``@/lib/api-client``). Callers resolve
    aliases to concrete files via :func:`tsconfig_paths.resolve_import`.
    """
    path = project_root / ".graphify" / "http-wrappers.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    modules = data.get("modules", {})
    if not isinstance(modules, dict):
        return {}
    out: dict[str, set[str]] = {}
    for spec, names in modules.items():
        if isinstance(names, list):
            out[spec] = {str(n) for n in names if isinstance(n, str)}
    return out


# ───── Enclosing-function tracking ──────────────────────────────────────


_FUNCTION_BOUNDARY_TYPES = {
    "function_declaration",
    "function",
    "arrow_function",
    "method_definition",
    "method_signature",
    "generator_function",
    "generator_function_declaration",
}


def _enclosing_callsite_info(node, source: bytes) -> tuple[Optional[str], Optional[str]]:
    """Walk up the tree returning ``(function_name, class_name)``.

    ``class_name`` is populated when the call sits inside a ``method_definition``
    nested in a ``class_declaration`` / ``class_body``. The AST extractor
    uses ``_make_id(_make_id(stem, class), method)`` for class methods
    (``graphify/extract.py`` around L890), so callers must build the same
    shape to avoid dangling edges.
    """
    cur = node.parent
    fn_name: Optional[str] = None
    while cur is not None:
        t = cur.type
        if fn_name is None:
            if t == "function_declaration":
                nm = cur.child_by_field_name("name")
                if nm is not None:
                    fn_name = _get_text(nm, source)
            elif t == "method_definition":
                nm = cur.child_by_field_name("name")
                if nm is not None:
                    fn_name = _get_text(nm, source)
            elif t == "variable_declarator":
                nm = cur.child_by_field_name("name")
                if nm is not None and nm.type == "identifier":
                    fn_name = _get_text(nm, source)
        if t == "class_declaration":
            nm = cur.child_by_field_name("name")
            if nm is not None:
                return fn_name, _get_text(nm, source)
            return fn_name, None
        cur = cur.parent
    return fn_name, None


def _enclosing_fn_name(node, source: bytes) -> Optional[str]:
    """Back-compat wrapper: returns only the function/method name."""
    fn_name, _ = _enclosing_callsite_info(node, source)
    return fn_name


def _caller_anchor_id(
    node,
    source: bytes,
    ts_file: Path,
    file_nid: str,
) -> str:
    """Pick the AST-compatible caller anchor ID for a call-expression.

    - Class method:    _make_id(_make_id(stem, class), method)
    - Free function:   _make_id(stem, fn_name)
    - Top level:       _make_id(str(path))  (file node)
    """
    fn_name, class_name = _enclosing_callsite_info(node, source)
    stem = ts_file.stem
    if fn_name and class_name:
        return _make_id(_make_id(stem, class_name), fn_name)
    if fn_name:
        return _make_id(stem, fn_name)
    return file_nid


# ───── Main scan ────────────────────────────────────────────────────────


def _append_api_and_edge(
    result: HttpCallsResult,
    method: str,
    url: str,
    source_file: Path,
    line: int,
    caller_id: str,
) -> None:
    # Strip query/hash so calls dedupe against BE path-only route nodes.
    cleaned = _strip_query_and_hash(url)
    # Template-literal env bases (e.g. :ADMIN_API_URL/api/...) become bogus
    # URL prefixes; drop the first placeholder segment. A pure env-base URL
    # with no path portion yields None — skip emission entirely.
    stripped = _strip_env_base_prefix(cleaned)
    if stripped is None:
        return
    cleaned = _normalize_url_pattern(stripped)
    api_nid = _api_node_id(method, cleaned)
    result.nodes.append({
        "id": api_nid,
        "label": f"{method} {cleaned}",
        "file_type": "route",
        "source_file": str(source_file),
        "source_location": f"L{line}",
        "kind": "api",
        "method": method,
        "url_pattern": cleaned,
    })
    result.edges.append({
        "source": caller_id,
        "target": api_nid,
        "relation": "calls_http",
        "method": method,
        "confidence": "EXTRACTED",
        "source_location": f"L{line}",
    })


def scan(project_root: Path | str) -> HttpCallsResult:
    """Extract wrapper-aware HTTP call-site nodes/edges under ``project_root``."""
    root = Path(project_root).resolve()
    parser_ts, _ = _load_ts_parser()
    parser_tsx, _ = _load_tsx_parser()
    if parser_ts is None:
        return HttpCallsResult()

    # 1) Wrapper discovery.
    auto_wrappers = _auto_detect_wrappers(root, parser_ts, parser_tsx)
    explicit_wrappers = _load_explicit_wrappers(root)

    # Resolve explicit module specs to file paths via tsconfig paths.
    resolver = TsconfigResolver(root)
    for spec, names in explicit_wrappers.items():
        resolved = resolver.resolve_alias(spec) if not spec.startswith(".") else None
        if resolved is None and (spec.startswith("./") or spec.startswith("../")):
            # Relative to the project root as a convenience.
            resolved = resolve_import(root / "dummy.ts", spec, project_root=root)
        if resolved is None:
            continue
        auto_wrappers.setdefault(resolved.resolve(), set()).update(names)

    # 2) Scan FE files for wrapper/raw-fetch calls.
    result = HttpCallsResult()
    for ts_file in _ts_files_under(root):
        if ts_file.resolve() in auto_wrappers:
            # Skip the wrapper module itself — its own fetch calls are
            # implementation detail, not endpoint usage.
            continue
        try:
            source = ts_file.read_bytes()
        except OSError:
            continue
        parser = parser_tsx if ts_file.suffix == ".tsx" else parser_ts
        if parser is None:
            continue
        try:
            tree = parser.parse(source)
        except Exception:
            continue
        root_node = tree.root_node
        if root_node is None:
            continue

        # First pass: build import table (alias → (resolved_file, kind, exported_name))
        import_table: dict[str, tuple[Path | None, str, str]] = {}
        for node in _iter_tree(root_node):
            if node.type != "import_statement":
                continue
            src_node = node.child_by_field_name("source")
            if src_node is None:
                continue
            raw_spec = _get_text(src_node, source).strip("'\"`")
            resolved = resolve_import(ts_file, raw_spec, project_root=root)
            for child in node.children:
                if child.type != "import_clause":
                    continue
                for sub in child.children:
                    if sub.type == "identifier":
                        import_table[_get_text(sub, source)] = (resolved, "default", "default")
                    elif sub.type == "named_imports":
                        for spec in sub.children:
                            if spec.type != "import_specifier":
                                continue
                            nm = spec.child_by_field_name("name")
                            alias = spec.child_by_field_name("alias")
                            if nm is None:
                                continue
                            exported = _get_text(nm, source)
                            local = _get_text(alias, source) if alias else exported
                            import_table[local] = (resolved, "named", exported)

        # File-level caller fallback when a call sits outside any function.
        file_nid = _make_id(str(ts_file))

        # Second pass: call_expressions.
        for node in _iter_tree(root_node):
            if node.type != "call_expression":
                continue
            fn_node = node.child_by_field_name("function")
            args_node = node.child_by_field_name("arguments")
            if fn_node is None or args_node is None:
                continue
            line = node.start_point[0] + 1
            arg_children = [c for c in args_node.children
                            if c.type not in (",", "(", ")")]
            if not arg_children:
                continue
            caller_id = _caller_anchor_id(node, source, ts_file, file_nid)

            # Case 1: direct identifier call, e.g. post('/x', body)
            if fn_node.type == "identifier":
                fn_name = _get_text(fn_node, source)
                # Must be imported from a wrapper module.
                imp = import_table.get(fn_name)
                if imp is None or imp[0] is None:
                    continue
                if imp[0].resolve() not in auto_wrappers:
                    continue
                if fn_name not in auto_wrappers[imp[0].resolve()]:
                    continue
                method = _method_from_name(fn_name) or "ANY"
                url = _string_literal_value(arg_children[0], source)
                if url is None or _is_external_url(url):
                    continue
                _append_api_and_edge(
                    result, method, url,
                    ts_file, line, caller_id,
                )
                continue

            # Case 2: member call, e.g. apiClient.get('/x') OR fetch(...)
            if fn_node.type == "member_expression":
                obj = fn_node.child_by_field_name("object")
                prop = fn_node.child_by_field_name("property")
                if obj is None or prop is None:
                    continue
                if obj.type != "identifier":
                    continue
                obj_name = _get_text(obj, source)
                prop_name = _get_text(prop, source)

                imp = import_table.get(obj_name)
                if imp is None or imp[0] is None:
                    continue
                if imp[0].resolve() not in auto_wrappers:
                    continue
                # For default-imported object wrappers we accept any method
                # property whose name maps to an HTTP verb.
                method = _method_from_name(prop_name)
                if method is None:
                    continue
                url = _string_literal_value(arg_children[0], source)
                if url is None or _is_external_url(url):
                    continue
                _append_api_and_edge(
                    result, method, url,
                    ts_file, line, caller_id,
                )
                continue

            # Case 3: fetch(url, init?) — bare identifier "fetch"
            if fn_node.type == "identifier" and _get_text(fn_node, source) == "fetch":
                # Not reachable (handled above when fn_name == 'fetch' but we
                # only accept wrapper-imported fn names); explicit handling
                # below.
                pass

        # Case 3 (fetch) separately — handled outside the generic branch.
        for node in _iter_tree(root_node):
            if node.type != "call_expression":
                continue
            fn_node = node.child_by_field_name("function")
            args_node = node.child_by_field_name("arguments")
            if fn_node is None or args_node is None:
                continue
            if fn_node.type != "identifier":
                continue
            if _get_text(fn_node, source) != "fetch":
                continue
            line = node.start_point[0] + 1
            caller_id = _caller_anchor_id(node, source, ts_file, file_nid)
            arg_children = [c for c in args_node.children
                            if c.type not in (",", "(", ")")]
            if not arg_children:
                continue
            url = _string_literal_value(arg_children[0], source)
            if url is None or _is_external_url(url):
                continue
            method = "GET"
            if len(arg_children) >= 2:
                explicit = _extract_method_option(arg_children[1], source)
                if explicit:
                    method = explicit
            _append_api_and_edge(
                result, method, url,
                ts_file, line, caller_id,
            )

    # Deduplicate nodes by id, edges by (source, target, relation, method).
    seen: set[str] = set()
    uniq_nodes: list[dict] = []
    for n in result.nodes:
        if n["id"] in seen:
            continue
        seen.add(n["id"])
        uniq_nodes.append(n)
    result.nodes = uniq_nodes

    seen_e: set[tuple[str, str, str, str]] = set()
    uniq_edges: list[dict] = []
    for e in result.edges:
        key = (e["source"], e["target"], e.get("relation", ""), e.get("method", ""))
        if key in seen_e:
            continue
        seen_e.add(key)
        uniq_edges.append(e)
    result.edges = uniq_edges
    return result
