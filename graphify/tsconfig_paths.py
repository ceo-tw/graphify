"""TypeScript ``tsconfig.json`` ``paths``/``baseUrl`` alias resolver.

openclaw-cloud (and every non-trivial Next.js project) uses ``@/...``
style aliases declared in ``tsconfig.json``. Without alias resolution,
imports such as ``import { post } from '@/lib/api-client'`` degrade
to a last-segment match in ``graphify/extract.py`` and downstream phases
(especially Phase H) cannot identify the concrete wrapper module.

This module intentionally stays small:

  * No full TypeScript compiler host.
  * No tsconfig ``extends`` resolution (follow-up — most monorepos rely
    on path aliases that are defined at the package level directly).
  * Tolerant of JSON-with-comments since editors frequently leave them in —
    the stripper is string-aware so ``/*`` inside a value like ``"@/*"`` is
    not mistaken for a comment (v0.5.2 fix).

Entry points:

  * ``TsconfigResolver(project_root)``: lazy resolver used by callers that
    want to translate aliases repeatedly.
  * ``resolve_import(source_file, spec)``: convenience for one-off import
    resolution that transparently handles relative paths, the ``.js``→TS
    suffix quirk common in Next.js, and alias fallthrough via
    ``TsconfigResolver``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


_JS_TS_SUFFIXES = (".ts", ".tsx", ".js", ".jsx")
_INDEX_CANDIDATES = ("index.ts", "index.tsx", "index.js", "index.jsx")


# ───── JSONC tolerance ──────────────────────────────────────────────────


def _strip_jsonc(text: str) -> str:
    """Strip ``//`` line comments, ``/* */`` block comments, and trailing
    commas from JSON-with-comments text while leaving string values intact.

    A single character-level pass with four states (code / string /
    line-comment / block-comment) — a regex that ignores JSON string context
    silently corrupts real tsconfigs that contain ``/*`` inside a string
    value (e.g. ``"@/*"`` in ``paths``).

    An unterminated block comment is re-emitted verbatim so ``json.loads``
    fails loudly instead of silently accepting truncated input.
    """
    n = len(text)
    out: list[str] = []
    i = 0
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        # String literal — preserve verbatim, honour \-escapes.
        if c == '"':
            out.append(c)
            i += 1
            while i < n:
                ch = text[i]
                out.append(ch)
                i += 1
                if ch == "\\" and i < n:
                    out.append(text[i])
                    i += 1
                    continue
                if ch == '"':
                    break
            continue
        # // line comment — skip to (but not including) newline.
        if c == "/" and nxt == "/":
            i += 2
            while i < n and text[i] != "\n":
                i += 1
            continue
        # /* block comment */ — find matching */ or re-emit verbatim at EOF.
        if c == "/" and nxt == "*":
            start = i
            i += 2
            closed = False
            while i < n:
                if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                    i += 2
                    closed = True
                    break
                i += 1
            if not closed:
                # Preserve the original so json.loads fails, not silently ok.
                out.append(text[start:])
                i = n
            continue
        # Trailing comma: in code state, drop a ',' that's only whitespace
        # away from a closing ']' or '}'. Strings/comments never reach here.
        if c == ",":
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if j < n and text[j] in "}]":
                i += 1  # drop the comma, keep whitespace + closer
                continue
        out.append(c)
        i += 1
    return "".join(out)


def _parse_jsonc(text: str) -> dict:
    """Parse JSON-with-comments and trailing commas, as tsconfig.json allows.

    Returns an empty dict on unparseable input — callers treat that as "no
    tsconfig applicable here" rather than raising, because a broken tsconfig
    in the user's project should not abort graphify.
    """
    stripped = _strip_jsonc(text)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


# ───── File existence helpers ───────────────────────────────────────────


def _resolve_candidate(base: Path) -> Optional[Path]:
    """Given a base path that may or may not already carry an extension,
    try the conventional TS resolution order and return the first hit."""
    base = base.resolve(strict=False)
    if base.suffix and base.is_file():
        return base
    for ext in _JS_TS_SUFFIXES:
        candidate = base.with_suffix(ext)
        if candidate.is_file():
            return candidate
    if base.is_dir():
        for idx in _INDEX_CANDIDATES:
            candidate = base / idx
            if candidate.is_file():
                return candidate
    return None


def _rewrite_js_suffix(base: Path) -> Path:
    """Drop a ``.js``/``.jsx`` suffix so the resolver can match ``.ts`` files.

    TS NodeNext and Next.js both allow (or require) importing with the
    runtime ``.js`` extension even though the source file is ``.ts``.
    """
    if base.suffix in (".js", ".jsx"):
        return base.with_suffix("")
    return base


# ───── Resolver ─────────────────────────────────────────────────────────


class TsconfigResolver:
    """Lazy ``tsconfig.json`` alias resolver rooted at a project directory.

    Walks up from each ``from_file`` when given, then falls back to the
    project root, finding the nearest ``tsconfig.json`` and caching the
    parsed content.
    """

    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root).resolve()
        # {tsconfig_path: parsed_dict}
        self._cache: dict[Path, dict] = {}

    # Lookup helpers ─────────────────────────────────────────────────

    def _find_tsconfig(self, from_file: Path | None) -> Optional[Path]:
        start = (from_file.resolve() if from_file else self.project_root)
        if start.is_file():
            start = start.parent
        current = start
        # Stop at project root (inclusive) — do not escape above it.
        try:
            current.relative_to(self.project_root)
        except ValueError:
            current = self.project_root
        while True:
            candidate = current / "tsconfig.json"
            if candidate.is_file():
                return candidate
            if current == self.project_root:
                return None
            if current.parent == current:
                return None
            current = current.parent
            # Prevent escaping above project root.
            try:
                current.relative_to(self.project_root)
            except ValueError:
                return None

    def _load(self, tsconfig_path: Path) -> dict:
        cached = self._cache.get(tsconfig_path)
        if cached is not None:
            return cached
        try:
            data = _parse_jsonc(tsconfig_path.read_text(encoding="utf-8"))
        except OSError:
            data = {}
        self._cache[tsconfig_path] = data
        return data

    # Alias resolution ───────────────────────────────────────────────

    def resolve_alias(
        self,
        spec: str,
        *,
        from_file: Path | None = None,
    ) -> Optional[Path]:
        """Translate an import specifier that might be an alias into an
        on-disk path. Returns ``None`` for relative imports (caller handles
        those), external packages, or when no tsconfig applies."""
        if not spec or spec.startswith(".") or spec.startswith("/"):
            # Relative and absolute paths are not aliases.
            return None
        tsconfig_path = self._find_tsconfig(from_file)
        if tsconfig_path is None:
            return None
        data = self._load(tsconfig_path)
        compiler = data.get("compilerOptions") or {}
        base_url = compiler.get("baseUrl") or "."
        base_dir = (tsconfig_path.parent / base_url).resolve()
        paths = compiler.get("paths") or {}

        # 1) Try paths patterns (alias → targets).
        alias_hit = self._resolve_via_paths(spec, base_dir, paths)
        if alias_hit is not None:
            return alias_hit

        # 2) Fall back to baseUrl — allows non-relative imports like `lib/foo`
        #    that map to `<baseUrl>/lib/foo`. External packages (react, …)
        #    are filtered out by requiring the resolved path to exist.
        base_candidate = base_dir / spec
        resolved = _resolve_candidate(_rewrite_js_suffix(base_candidate))
        return resolved

    @staticmethod
    def _resolve_via_paths(
        spec: str,
        base_dir: Path,
        paths: dict[str, list[str]],
    ) -> Optional[Path]:
        """Match ``spec`` against each ``paths`` pattern and resolve."""
        for pattern, targets in paths.items():
            if not isinstance(targets, list):
                continue
            remainder = _match_path_pattern(pattern, spec)
            if remainder is None:
                continue
            for target in targets:
                expanded = target.replace("*", remainder) if "*" in target else target
                candidate = base_dir / expanded
                resolved = _resolve_candidate(_rewrite_js_suffix(candidate))
                if resolved is not None:
                    return resolved
        return None


def _match_path_pattern(pattern: str, spec: str) -> Optional[str]:
    """Return the matched wildcard portion of ``spec`` under ``pattern``.

    ``@/*`` vs ``@/lib/foo``  → ``lib/foo``
    ``@shared`` vs ``@shared``  → ``""`` (exact match)
    ``@/*`` vs ``react``  → ``None`` (no match)
    """
    if "*" in pattern:
        before, _, after = pattern.partition("*")
        if spec.startswith(before) and spec.endswith(after) and \
           len(spec) >= len(before) + len(after):
            return spec[len(before): len(spec) - len(after) if after else None]
        return None
    return "" if pattern == spec else None


# ───── One-off convenience ──────────────────────────────────────────────


def resolve_import(
    source_file: Path,
    spec: str,
    *,
    project_root: Path | str | None = None,
) -> Optional[Path]:
    """Resolve a TypeScript/JavaScript import specifier to an on-disk file.

    Handles three categories in order:

      1. Relative paths (``./foo``, ``../bar``) — rewritten if they carry a
         ``.js`` suffix so ``./foo.js`` resolves to ``./foo.ts`` on disk.
      2. Aliases via ``tsconfig.json`` (``@/...``, ``@shared``, …) resolved
         through a :class:`TsconfigResolver` rooted at ``project_root``.
      3. ``baseUrl``-rooted non-relative imports (e.g. ``lib/foo``) also
         resolved by :class:`TsconfigResolver`.

    External packages (``react``, ``@tanstack/react-query`` …) return
    ``None``.
    """
    source_file = Path(source_file)
    if spec.startswith("./") or spec.startswith("../"):
        base = (source_file.parent / spec).resolve()
        return _resolve_candidate(_rewrite_js_suffix(base))
    if project_root is None:
        project_root = source_file.parent
    resolver = TsconfigResolver(project_root)
    return resolver.resolve_alias(spec, from_file=source_file)
