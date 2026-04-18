"""URL/Route overlay extraction.

Produces three node kinds that sit alongside the AST graph:

  - ``URL:<pattern>``     — an FE route pattern (Next.js App/Pages Router).
  - ``API:<METHOD> <pattern>`` — a backend endpoint (Hono, Next.js Route Handler).
  - ``SERVICE:<name>``   — a remote service anchor referenced by proxies.

And the edges that connect them to code nodes produced by ``extract.py``:

  - ``renders``              URL → FE page component (default export of page.tsx)
  - ``wraps``                URL → layout.tsx default export
  - ``loads``                URL → loading.tsx default export
  - ``handles_error_for``    URL → error.tsx default export
  - ``handled_by``           API → BE handler function
  - ``forwards_to``          API → SERVICE (proxy rewrites)

All nodes emitted here carry ``file_type: "route"`` so ``cluster.py`` can
exclude them from Leiden and put them into the synthetic "Routes" community.
"""
from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .extract import _make_id


# ───── Node / edge construction helpers ─────────────────────────────────────


def _url_node_id(url: str) -> str:
    return _make_id("url", url)


def _api_node_id(method: str, path: str) -> str:
    return _make_id("api", method.lower(), path)


def _service_node_id(name: str) -> str:
    return _make_id("service", name)


def _page_component_id(page_file: Path) -> str:
    """Stable ID for the page/layout/loading/error file.

    Aligned with ``extract._make_id(str(path))`` — the AST extractor emits
    a file-level node with that exact ID for every source file it sees.
    By using the same ID we let the ``renders``/``wraps`` edges point at
    real AST file nodes when the overlay is merged into the main graph.
    """
    return _make_id(str(page_file))


@dataclass
class RouteScanResult:
    nodes: list[dict] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    raw_calls: list[dict] = field(default_factory=list)

    def extend(self, other: "RouteScanResult") -> None:
        self.nodes.extend(other.nodes)
        self.edges.extend(other.edges)
        self.raw_calls.extend(other.raw_calls)


# ───── Next.js App Router — filesystem scanner ──────────────────────────────

_PAGE_BASENAMES = {"page.tsx", "page.ts", "page.jsx", "page.js"}
_LAYOUT_BASENAMES = {"layout.tsx", "layout.ts", "layout.jsx", "layout.js"}
_LOADING_BASENAMES = {"loading.tsx", "loading.ts", "loading.jsx", "loading.js"}
_ERROR_BASENAMES = {"error.tsx", "error.ts", "error.jsx", "error.js"}
_ROUTE_BASENAMES = {"route.ts", "route.tsx", "route.js", "route.jsx"}

_NEXTJS_HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")

# Detect exported HTTP method handlers in route.ts files.
# Matches:
#   export async function GET(...)
#   export function GET(...)
#   export const GET = async (...) =>
#   export const GET = handler
_ROUTE_EXPORT_RE = re.compile(
    r"export\s+(?:async\s+)?(?:function\s+(?P<fn>[A-Z]+)|const\s+(?P<const>[A-Z]+)\s*=)",
    re.MULTILINE,
)


_INTERCEPTING_PREFIX_RE = re.compile(r"^\((?P<dots>\.+)\)(?P<rest>.*)$")


def _segment_to_url(segment: str) -> tuple[str | None, dict[str, str]]:
    """Convert one filesystem segment to a URL segment.

    Returns (url_segment_or_None, attrs). ``None`` means the segment is
    invisible in URLs (route group / parallel slot). ``attrs`` is merged
    onto the owning URL node.
    """
    attrs: dict[str, str] = {}
    if not segment:
        return "", attrs
    # Intercepting-route prefix: (.)name, (..)name, (...)name. The rest of
    # the segment is visible in the URL; only the dotted prefix is stripped.
    m = _INTERCEPTING_PREFIX_RE.match(segment)
    if m:
        rest = m.group("rest")
        attrs["intercepting"] = m.group("dots")
        if not rest:
            # Pure "(.)" segment — no URL piece. Fall through to return None.
            return None, attrs
        # Recurse so dynamic/catch-all patterns inside the rest still work.
        sub_piece, sub_attrs = _segment_to_url(rest)
        for k, v in sub_attrs.items():
            attrs.setdefault(k, v)
        return sub_piece, attrs
    # Route groups: (marketing) → does not contribute to URL
    if segment.startswith("(") and segment.endswith(")"):
        stripped = segment[1:-1]
        return None, {"route_group": stripped}
    # Parallel routes: @modal
    if segment.startswith("@"):
        return None, {"parallel_slot": segment[1:]}
    # Optional catch-all: [[...slug]]
    m = re.fullmatch(r"\[\[\.\.\.(\w+)\]\]", segment)
    if m:
        return f"*?{m.group(1)}", {}
    # Catch-all: [...slug]
    m = re.fullmatch(r"\[\.\.\.(\w+)\]", segment)
    if m:
        return f"*{m.group(1)}", {}
    # Dynamic: [id]
    m = re.fullmatch(r"\[(\w+)\]", segment)
    if m:
        return f":{m.group(1)}", {}
    # Literal
    return segment, {}


def _path_to_url(rel_segments: list[str]) -> tuple[str, dict[str, str]]:
    """Convert a list of filesystem segments (between the ``app`` directory and
    the page file) into a URL pattern plus aggregated attributes.

    Examples:
      []                                → "/"
      ["portal", "agents", "[id]"]      → "/portal/agents/:id"
      ["(auth)", "login"]               → "/login"
      ["@modal", "dialog"]              → "/dialog"  (parallel_slot=modal)
    """
    pieces: list[str] = []
    attrs: dict[str, str] = {}
    for seg in rel_segments:
        piece, seg_attrs = _segment_to_url(seg)
        for k, v in seg_attrs.items():
            attrs.setdefault(k, v)  # first match wins
        if piece is None:
            continue
        if piece == "":
            continue
        pieces.append(piece)
    url = "/" + "/".join(pieces)
    if url == "":
        url = "/"
    return url, attrs


def _find_app_directories(project_root: Path) -> list[Path]:
    """Find every Next.js ``app`` directory under the project.

    A directory qualifies if it is literally named ``app`` and contains any
    of the Next.js convention files (layout/page/route/...). This tolerates
    monorepos with multiple Next.js packages (``admin-portal``, ``homepage``)
    without dragging in unrelated ``app`` folders from e.g. Python projects.
    """
    matches: list[Path] = []
    skip_dirs = {"node_modules", ".next", ".git", "dist", "build"}
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        p = Path(dirpath)
        if p.name != "app":
            continue
        # Require a convention file somewhere under this directory so we do
        # not mistake e.g. a python "app" package for a Next.js app router.
        for _, _, fs in os.walk(p):
            hit = any(
                fn in _PAGE_BASENAMES
                or fn in _LAYOUT_BASENAMES
                or fn in _ROUTE_BASENAMES
                for fn in fs
            )
            if hit:
                matches.append(p)
                break
    return matches


def _find_pages_directories(project_root: Path) -> list[Path]:
    """Find Next.js legacy ``pages`` directories (Pages Router)."""
    matches: list[Path] = []
    skip_dirs = {"node_modules", ".next", ".git", "dist", "build"}
    for dirpath, dirnames, _ in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        p = Path(dirpath)
        if p.name != "pages":
            continue
        # Heuristic: adjacent ``app`` directory, or parent has ``next.config.*``
        parent = p.parent
        if (parent / "next.config.js").exists() or (parent / "next.config.mjs").exists() or \
           (parent / "next.config.ts").exists() or (parent / "app").exists():
            matches.append(p)
    return matches


def _rel_segments_from_app(app_dir: Path, file_path: Path) -> list[str]:
    """Segments between the app directory and the file, excluding the basename."""
    rel = file_path.relative_to(app_dir).parent
    parts = [p for p in rel.parts if p not in (".", "")]
    return parts


def scan_nextjs(project_root: Path) -> RouteScanResult:
    """Scan Next.js conventions (App Router + Pages Router + Route Handlers)."""
    result = RouteScanResult()

    # ── App Router pages / layouts / loading / error ────────────────────
    app_dirs = _find_app_directories(project_root)
    for app_dir in app_dirs:
        for dirpath, dirnames, filenames in os.walk(app_dir):
            dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".next"}]
            d = Path(dirpath)
            segs = _rel_segments_from_app(app_dir, d / "_placeholder")
            url, attrs = _path_to_url(segs)
            url_nid = _url_node_id(url)

            # Emit URL node + edge to the AST file node (never duplicate the
            # file node itself — it carries file_type="code" from the AST pass
            # and must not be overwritten with file_type="route").
            for fn in filenames:
                if fn in _PAGE_BASENAMES:
                    comp = d / fn
                    result.nodes.append({
                        "id": url_nid,
                        "label": f"URL {url}",
                        "file_type": "route",
                        "source_file": str(comp),
                        "source_location": "",
                        "kind": "url",
                        "url_pattern": url,
                        **attrs,
                    })
                    result.edges.append({
                        "source": url_nid, "target": _page_component_id(comp),
                        "relation": "renders", "confidence": "EXTRACTED",
                    })
                elif fn in _LAYOUT_BASENAMES:
                    comp = d / fn
                    result.edges.append({
                        "source": url_nid, "target": _page_component_id(comp),
                        "relation": "wraps", "confidence": "EXTRACTED",
                    })
                elif fn in _LOADING_BASENAMES:
                    comp = d / fn
                    result.edges.append({
                        "source": url_nid, "target": _page_component_id(comp),
                        "relation": "loads", "confidence": "EXTRACTED",
                    })
                elif fn in _ERROR_BASENAMES:
                    comp = d / fn
                    result.edges.append({
                        "source": url_nid, "target": _page_component_id(comp),
                        "relation": "handles_error_for", "confidence": "EXTRACTED",
                    })
                elif fn in _ROUTE_BASENAMES:
                    route_file = d / fn
                    result.extend(_scan_nextjs_route_handler(app_dir, route_file))

    # ── Pages Router ────────────────────────────────────────────────────
    for pages_dir in _find_pages_directories(project_root):
        for dirpath, dirnames, filenames in os.walk(pages_dir):
            dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".next"}]
            d = Path(dirpath)
            for fn in filenames:
                if not any(fn.endswith(ext) for ext in (".tsx", ".ts", ".jsx", ".js")):
                    continue
                if fn.startswith("_") or fn == "middleware.ts":
                    continue
                # Reject obvious non-page files
                if fn in {"index.d.ts"}:
                    continue
                page_file = d / fn
                rel = page_file.relative_to(pages_dir)
                parts = list(rel.parts)
                # Drop extension from last piece; "index" means the parent dir URL
                last = Path(parts[-1]).stem
                segs = parts[:-1] + ([] if last == "index" else [last])
                # Pages Router does not have route groups / parallel slots
                # but dynamic patterns match ([id], [...slug], [[...slug]]).
                url_pieces: list[str] = []
                for s in segs:
                    piece, _ = _segment_to_url(s)
                    if piece:
                        url_pieces.append(piece)
                url = "/" + "/".join(url_pieces) if url_pieces else "/"
                url_nid = _url_node_id(url)
                result.nodes.append({
                    "id": url_nid,
                    "label": f"URL {url}",
                    "file_type": "route",
                    "source_file": str(page_file),
                    "source_location": "",
                    "kind": "url",
                    "url_pattern": url,
                    "router": "pages",
                })
                result.edges.append({
                    "source": url_nid, "target": _page_component_id(page_file),
                    "relation": "renders", "confidence": "EXTRACTED",
                })

    return result


def _scan_nextjs_route_handler(app_dir: Path, route_file: Path) -> RouteScanResult:
    """Extract API:METHOD nodes from one Next.js app/**/route.ts file."""
    result = RouteScanResult()
    # Derive URL pattern from the directory containing route.ts
    segs = _rel_segments_from_app(app_dir, route_file)
    url, attrs = _path_to_url(segs)

    try:
        source = route_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return result
    methods: set[str] = set()
    for m in _ROUTE_EXPORT_RE.finditer(source):
        name = m.group("fn") or m.group("const")
        if name in _NEXTJS_HTTP_METHODS:
            methods.add(name)

    for method in sorted(methods):
        api_nid = _api_node_id(method, url)
        result.nodes.append({
            "id": api_nid,
            "label": f"{method} {url}",
            "file_type": "route",
            "source_file": str(route_file),
            "source_location": "",
            "kind": "api",
            "method": method,
            "url_pattern": url,
            "framework": "nextjs",
            **attrs,
        })
        # Handler anchor points at the route.ts file node from the AST pass.
        result.edges.append({
            "source": api_nid, "target": _page_component_id(route_file),
            "relation": "handled_by", "confidence": "EXTRACTED",
        })

        # Proxy detection: if the file path matches app/api/proxy/[...path]/route.ts
        # emit a forwards_to edge per inferred service. Multiple service anchors
        # are emitted when the proxy switches on a condition (admin vs billing).
        if "proxy" in str(route_file).lower() and "[..." in str(route_file):
            for svc_nid, svc_label in _detect_forward_targets(source):
                result.nodes.append({
                    "id": svc_nid,
                    "label": svc_label,
                    "file_type": "route",
                    "source_file": str(route_file),
                    "source_location": "",
                    "kind": "service",
                })
                result.edges.append({
                    "source": api_nid, "target": svc_nid,
                    "relation": "forwards_to", "confidence": "INFERRED",
                })

    return result


_ENV_VAR_RE = re.compile(r"process\.env\.([A-Z][A-Z0-9_]+)")


def _detect_forward_targets(source: str) -> list[tuple[str, str]]:
    """Best-effort service anchors from proxy source content.

    Returns a list of (node_id, label) for every API-ish env var referenced
    in the proxy file. Empty when none found.
    """
    envs = _ENV_VAR_RE.findall(source)
    api_urls = [e for e in envs if "API" in e or "URL" in e]
    if not api_urls:
        return []
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for e in api_urls:
        svc_name = e.lower().replace("_url", "").replace("_api", "")
        svc_name = svc_name.replace("next_public_", "").replace("public_", "")
        if not svc_name:
            svc_name = e.lower()
        if svc_name in seen:
            continue
        seen.add(svc_name)
        out.append((_service_node_id(svc_name), f"SERVICE {svc_name}"))
    return out


# ───── Hono backend scanner (tree-sitter) ───────────────────────────────────


def _load_ts_parser():
    """Return a (parser, language) tuple for TypeScript (non-JSX).

    Returns (None, None) if tree-sitter is unavailable. Caller should
    gracefully skip Hono scanning in that case.
    """
    try:
        mod = importlib.import_module("tree_sitter_typescript")
        from tree_sitter import Language, Parser
        lang_fn = getattr(mod, "language_typescript", None)
        if lang_fn is None:
            return None, None
        language = Language(lang_fn())
        return Parser(language), language
    except Exception:
        return None, None


_HONO_METHODS = {"get", "post", "put", "patch", "delete", "all", "options", "head"}
# Note: ``on`` is intentionally excluded — Hono's ``on(method|methods, path, handler)``
# shape puts METHOD as the first arg, not a path, and correctly interpreting it
# needs multi-method fan-out that Phase 1 skips.

# Skip files that are unlikely to register production endpoints. Test-local
# Hono apps in ``__tests__/`` or ``*.test.ts`` commonly bind routes that do
# not exist at runtime.
_TEST_PATH_MARKERS = ("__tests__",)
_TEST_FILENAME_MARKERS = (".test.", ".spec.")


def _is_test_file(path: Path) -> bool:
    parts = set(path.parts)
    if any(m in parts for m in _TEST_PATH_MARKERS):
        return True
    name = path.name
    return any(m in name for m in _TEST_FILENAME_MARKERS)


def _ts_files_under(project_root: Path) -> Iterable[Path]:
    skip = {"node_modules", ".next", ".git", "dist", "build"}
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if fn.endswith((".ts", ".tsx")) and not fn.endswith(".d.ts"):
                p = Path(dirpath) / fn
                if _is_test_file(p):
                    continue
                yield p


def _get_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _is_hono_new_expression(node, source_bytes: bytes) -> bool:
    """Return True iff node represents ``new Hono(...)``. ``node`` is a
    tree-sitter ``new_expression``."""
    if node.type != "new_expression":
        return False
    # constructor field
    for child in node.children:
        if child.type in ("identifier", "type_identifier"):
            return _get_text(child, source_bytes) == "Hono"
    return False


def _string_literal_value(node, source_bytes: bytes) -> str | None:
    """Extract a plain string value from a tree-sitter string/template literal.

    Template literals with substitutions are normalized by replacing
    ``${expr}`` with ``:param`` when a simple identifier, else ``:arg``.
    """
    if node.type == "string":
        raw = _get_text(node, source_bytes)
        if len(raw) >= 2 and raw[0] in ("'", '"', "`") and raw[-1] in ("'", '"', "`"):
            return raw[1:-1]
        return raw
    if node.type == "template_string":
        # Walk children, concatenate text; replace ${expr}
        out = []
        for child in node.children:
            t = child.type
            text = _get_text(child, source_bytes)
            if t in ("`",):
                continue
            if t == "template_substitution":
                inner = text.strip("${}")
                inner_ident = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", inner.strip())
                out.append(f":{inner.strip()}" if inner_ident else ":param")
            else:
                out.append(text)
        s = "".join(out)
        # Normalize common template patterns like "id" → ":id" when preceded by "/"
        return s
    return None


def _normalize_url_pattern(p: str) -> str:
    """Normalize a path so FE and BE match path-to-regexp style."""
    if not p:
        return "/"
    if not p.startswith("/"):
        p = "/" + p
    # collapse //
    p = re.sub(r"/+", "/", p)
    return p


def _join_mount(base: str, child: str) -> str:
    base = _normalize_url_pattern(base or "/")
    child = _normalize_url_pattern(child or "/")
    if base == "/":
        return child
    if child == "/":
        return base
    return _normalize_url_pattern(base.rstrip("/") + "/" + child.lstrip("/"))


def _iter_tree(node):
    """Pre-order DFS over a tree-sitter subtree."""
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        for c in reversed(n.children):
            stack.append(c)


def _resolve_ts_import(source_file: Path, spec: str) -> Path | None:
    """Resolve a relative TS import specifier to an on-disk file.

    Handles the common suffixes: ``.ts``, ``.tsx``, ``/index.ts`` — does
    not cover tsconfig ``paths`` (that lives in tsconfig_paths.py for H).
    Returns ``None`` if no candidate exists.
    """
    if not (spec.startswith("./") or spec.startswith("../")):
        return None
    base = (source_file.parent / spec).resolve()
    candidates = [
        base.with_suffix(".ts"),
        base.with_suffix(".tsx"),
        base / "index.ts",
        base / "index.tsx",
    ]
    if base.suffix:
        candidates.insert(0, base)
    for c in candidates:
        if c.is_file():
            return c
    return None


_STRING_LITERAL_TYPES = {"string", "template_string"}


def _scan_ts_file_for_hono(ts_file: Path, source: bytes, root) -> dict:
    """Extract Hono-relevant structure from one TS file.

    Returns a dict with keys:
      bindings:       {local_name: "new_hono"}
      imports:        {local_alias: (resolved_path: Path | None, import_kind: "default" | "named", exported_name: str)}
      default_export: local_name or None
      named_exports:  {export_name: local_name}     (for ``export { plans }``)
      method_calls:   [{receiver, method, path, line}]
      mount_calls:    [{receiver, mount_path, child_ident, line}]
    """
    bindings: dict[str, str] = {}
    imports: dict[str, tuple[Path | None, str, str]] = {}
    default_export: str | None = None
    named_exports: dict[str, str] = {}
    method_calls: list[dict] = []
    mount_calls: list[dict] = []

    for node in _iter_tree(root):
        t = node.type

        # ─ variable_declarator: catches `const plans = new Hono()` and any
        #   re-binding like `const plans = rawPlans;` which we do not resolve.
        if t == "variable_declarator":
            name_node = node.child_by_field_name("name")
            value_node = node.child_by_field_name("value")
            if name_node is None or value_node is None:
                continue
            if name_node.type != "identifier":
                continue
            if _is_hono_new_expression(value_node, source):
                bindings[_get_text(name_node, source)] = "new_hono"
            # Handle `new Hono().basePath(...).get(...)` only for the
            # trivial case where the declarator is bound to the final
            # result of a chained method call whose root is `new Hono()`.
            elif value_node.type == "call_expression":
                # Find the deepest receiver chain; if any ancestor is
                # `new Hono()`, still treat as Hono binding.
                r = value_node
                while r is not None and r.type == "call_expression":
                    fn = r.child_by_field_name("function")
                    if fn is None:
                        break
                    if fn.type == "member_expression":
                        obj = fn.child_by_field_name("object")
                        r = obj
                    else:
                        break
                if r is not None and _is_hono_new_expression(r, source):
                    bindings[_get_text(name_node, source)] = "new_hono_chain"

        # ─ import_statement: build alias → (resolved file, kind, exported name)
        if t == "import_statement":
            src_node = node.child_by_field_name("source")
            if src_node is None:
                continue
            raw = _get_text(src_node, source).strip("'\"`")
            resolved = _resolve_ts_import(ts_file, raw)
            # Find import_clause → default specifier / named specifiers
            for child in node.children:
                if child.type != "import_clause":
                    continue
                for sub in child.children:
                    if sub.type == "identifier":
                        # default import: `import X from '...'`
                        imports[_get_text(sub, source)] = (resolved, "default", "default")
                    elif sub.type == "named_imports":
                        for spec in sub.children:
                            if spec.type != "import_specifier":
                                continue
                            name_node = spec.child_by_field_name("name")
                            alias_node = spec.child_by_field_name("alias")
                            if name_node is None:
                                continue
                            exported = _get_text(name_node, source)
                            local = _get_text(alias_node, source) if alias_node else exported
                            imports[local] = (resolved, "named", exported)

        # ─ export_statement: catch `export default plans` and `export { plans }`
        if t == "export_statement":
            # default export: export default <ident>
            for child in node.children:
                if child.type == "identifier":
                    default_export = _get_text(child, source)
                # export { a, b } — children include export_specifier
                if child.type == "export_clause":
                    for spec in child.children:
                        if spec.type != "export_specifier":
                            continue
                        name_node = spec.child_by_field_name("name")
                        alias_node = spec.child_by_field_name("alias")
                        if name_node is None:
                            continue
                        local = _get_text(name_node, source)
                        exported = _get_text(alias_node, source) if alias_node else local
                        named_exports[exported] = local

        # ─ call_expression: distinguish <recv>.METHOD(path) and .route(...)
        if t == "call_expression":
            fn_node = node.child_by_field_name("function")
            args_node = node.child_by_field_name("arguments")
            if fn_node is None or args_node is None or fn_node.type != "member_expression":
                continue
            obj_node = fn_node.child_by_field_name("object")
            prop_node = fn_node.child_by_field_name("property")
            if obj_node is None or prop_node is None or obj_node.type != "identifier":
                continue
            receiver = _get_text(obj_node, source)
            method = _get_text(prop_node, source)
            line = node.start_point[0] + 1

            arg_children = [c for c in args_node.children
                            if c.type not in (",", "(", ")")]
            if not arg_children:
                continue
            first_arg = arg_children[0]

            if method == "route" and len(arg_children) >= 2:
                mount = _string_literal_value(first_arg, source)
                if mount is None:
                    continue
                child_node = arg_children[1]
                # Only record cross-file mounts when child is a plain identifier.
                # Inline `app.route('/x', new Hono()...)` falls through to routes
                # parsed directly on that throwaway receiver (rare; ignore).
                if child_node.type != "identifier":
                    continue
                child_ident = _get_text(child_node, source)
                mount_calls.append({
                    "receiver": receiver,
                    "mount_path": _normalize_url_pattern(mount),
                    "child_ident": child_ident,
                    "line": line,
                })
                continue

            if method in _HONO_METHODS:
                # First arg must be a string/template literal; otherwise
                # this is almost certainly not a router method call.
                if first_arg.type not in _STRING_LITERAL_TYPES:
                    continue
                path = _string_literal_value(first_arg, source)
                if path is None:
                    continue
                method_upper = method.upper() if method != "all" else "ANY"
                method_calls.append({
                    "receiver": receiver,
                    "method": method_upper,
                    "path": _normalize_url_pattern(path),
                    "line": line,
                })

    return {
        "bindings": bindings,
        "imports": imports,
        "default_export": default_export,
        "named_exports": named_exports,
        "method_calls": method_calls,
        "mount_calls": mount_calls,
    }


def _resolve_exported_binding(
    file_info: dict[Path, dict],
    target_file: Path,
    import_kind: str,
    exported_name: str,
) -> str | None:
    """Given a target TS file and the name exported from it, return the
    local Hono binding that is actually referenced (if the export is a
    Hono router). Returns ``None`` if the export does not correspond to a
    known Hono binding — caller should then skip that import.
    """
    info = file_info.get(target_file)
    if info is None:
        return None
    if import_kind == "default":
        local = info.get("default_export")
    else:
        local = info["named_exports"].get(exported_name, exported_name)
    if local is None:
        return None
    if local in info["bindings"]:
        return local
    # Re-export of an import: follow one hop. e.g.
    #   export { default as settingsPlans } from './settings-plans'
    # Not currently common in openclaw; leave for follow-up if needed.
    return None


def scan_hono(project_root: Path) -> RouteScanResult:
    """Extract API endpoints registered with Hono routers across files.

    Strict receiver policy: only method calls whose receiver resolves (either
    via local ``new Hono()`` binding or via an imported alias that ultimately
    points at a ``new Hono()`` in a known local file) produce API nodes. This
    rules out false positives such as ``headers.get('auth')`` or
    ``map.get('key')``.

    Cross-file mount composition: ``app.route('/settings', settingsPlans)``
    with ``import settingsPlans from './routes/settings-plans'`` routes
    registered on that imported binding into the correct full URL.
    """
    parser, _ = _load_ts_parser()
    if parser is None:
        return RouteScanResult()

    # Pass 1 — gather per-file structural info.
    file_info: dict[Path, dict] = {}
    for ts_file in _ts_files_under(project_root):
        try:
            source = ts_file.read_bytes()
        except OSError:
            continue
        try:
            tree = parser.parse(source)
        except Exception:
            continue
        root = tree.root_node
        if root is None:
            continue
        file_info[ts_file.resolve()] = _scan_ts_file_for_hono(ts_file, source, root)

    # Pass 2 — compute effective mount paths for each (file, local binding).
    # effective_mount: (file_path, local_binding) → list[str]   (can be mounted
    # at multiple parent paths; we keep all of them).
    effective_mounts: dict[tuple[Path, str], list[str]] = {}

    # First, seed every known binding with mount "/" so unmounted routers
    # (top-level `app.get`) still produce URLs that start at "/".
    for file_path, info in file_info.items():
        for binding in info["bindings"]:
            effective_mounts.setdefault((file_path, binding), ["/"])

    # Track which bindings receive an incoming mount so we can later drop the
    # default "/" seed for them (a mounted child is not also reachable at
    # the root-less path in openclaw-style apps).
    mounted_children: set[tuple[Path, str]] = set()

    # Iterate until no new mount paths get added (fixed point). In practice
    # two passes cover the vast majority of real codebases.
    for _ in range(6):
        changed = False
        for file_path, info in file_info.items():
            for mount in info["mount_calls"]:
                receiver = mount["receiver"]
                child_ident = mount["child_ident"]
                # Parent binding must resolve to an effective-mount key in the
                # current file — either a local binding or an imported one.
                parent_key = _resolve_binding_key(file_info, file_path, receiver)
                child_key = _resolve_binding_key(file_info, file_path, child_ident)
                if parent_key is None or child_key is None:
                    continue
                mounted_children.add(child_key)
                parent_bases = effective_mounts.get(parent_key, ["/"])
                for base in parent_bases:
                    full = _join_mount(base, mount["mount_path"])
                    existing = effective_mounts.setdefault(child_key, [])
                    if full not in existing:
                        existing.append(full)
                        changed = True
        if not changed:
            break

    # For bindings that have incoming mounts, drop the default "/" seed so
    # their child routes are only emitted at mounted paths.
    for key in mounted_children:
        bases = effective_mounts.get(key)
        if bases is None:
            continue
        filtered = [b for b in bases if b != "/"]
        if filtered:
            effective_mounts[key] = filtered

    # Pass 3 — emit API nodes using effective mounts.
    result = RouteScanResult()
    for file_path, info in file_info.items():
        for call in info["method_calls"]:
            receiver = call["receiver"]
            # Only accept receivers that resolve to a Hono binding.
            target = _resolve_binding_key(file_info, file_path, receiver)
            if target is None:
                # Strict: receiver not a known Hono binding → skip. This is
                # what prevents `headers.get(...)` false positives.
                continue
            bases = effective_mounts.get(target, ["/"])
            for base in bases:
                full_path = _join_mount(base, call["path"])
                _emit_api_node(result, call["method"], full_path, file_path, call["line"])
    return result


def _resolve_binding_key(
    file_info: dict[Path, dict],
    current_file: Path,
    ident: str,
) -> tuple[Path, str] | None:
    """Resolve an identifier in ``current_file`` to the (file, binding) that
    hosts the underlying ``new Hono()`` declaration.

    Returns ``None`` when ``ident`` is not a known Hono binding (imported or
    local). This is the strictness gate for receiver acceptance.
    """
    info = file_info.get(current_file)
    if info is None:
        return None
    # Local binding first
    if ident in info["bindings"]:
        return (current_file, ident)
    # Imported alias
    if ident in info["imports"]:
        target_file, kind, exported = info["imports"][ident]
        if target_file is None:
            return None
        target_file = target_file.resolve()
        bound = _resolve_exported_binding(file_info, target_file, kind, exported)
        if bound is None:
            return None
        return (target_file, bound)
    return None


def _emit_api_node(
    result: RouteScanResult,
    method: str,
    path: str,
    source_file: Path,
    line: int,
) -> None:
    api_nid = _api_node_id(method, path)
    result.nodes.append({
        "id": api_nid,
        "label": f"{method} {path}",
        "file_type": "route",
        "source_file": str(source_file),
        "source_location": f"L{line}",
        "kind": "api",
        "method": method,
        "url_pattern": path,
        "framework": "hono",
    })
    # Handler anchor is the source file node produced by AST extraction.
    # If the AST pass has not yet run (standalone routes scan), this edge
    # will be dangling and build_from_json will drop it silently.
    result.edges.append({
        "source": api_nid, "target": _page_component_id(source_file),
        "relation": "handled_by", "confidence": "EXTRACTED",
    })


# ───── Public entrypoint ────────────────────────────────────────────────────


def scan(project_root: str | Path) -> RouteScanResult:
    """Scan a project root for URL/route/API overlays.

    Non-fatal by design: any sub-scanner that fails returns an empty result
    so that ``extract.py`` can merge whatever did succeed.
    """
    root = Path(project_root).resolve()
    result = RouteScanResult()
    try:
        result.extend(scan_nextjs(root))
    except Exception:
        pass
    try:
        result.extend(scan_hono(root))
    except Exception:
        pass
    # Deduplicate nodes by id (later occurrences discarded) and edges by tuple.
    seen_nodes: set[str] = set()
    dedup_nodes = []
    for n in result.nodes:
        if n["id"] in seen_nodes:
            continue
        seen_nodes.add(n["id"])
        dedup_nodes.append(n)
    result.nodes = dedup_nodes
    seen_edges: set[tuple[str, str, str]] = set()
    dedup_edges = []
    for e in result.edges:
        key = (e["source"], e["target"], e.get("relation", ""))
        if key in seen_edges:
            continue
        seen_edges.add(key)
        dedup_edges.append(e)
    result.edges = dedup_edges
    return result
