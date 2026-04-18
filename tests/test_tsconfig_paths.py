"""Tests for graphify.tsconfig_paths — TypeScript ``paths``/``baseUrl`` alias resolver.

Fixtures use tmp_path so we never depend on external projects.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from graphify.tsconfig_paths import (
    TsconfigResolver,
    resolve_import,
)


# ───── Low-level resolver ────────────────────────────────────────────────


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolver_no_tsconfig_returns_none(tmp_path: Path):
    resolver = TsconfigResolver(tmp_path)
    assert resolver.resolve_alias("@/lib/foo") is None


def test_resolver_simple_paths_alias(tmp_path: Path):
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {
            "baseUrl": ".",
            "paths": {"@/*": ["src/*"]},
        }
    }))
    _write(tmp_path / "src" / "lib" / "api-client.ts", "export const x = 1;")
    resolver = TsconfigResolver(tmp_path)
    resolved = resolver.resolve_alias("@/lib/api-client")
    assert resolved is not None
    assert resolved == (tmp_path / "src" / "lib" / "api-client.ts").resolve()


def test_resolver_alias_without_wildcard(tmp_path: Path):
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {
            "baseUrl": ".",
            "paths": {"@shared": ["packages/shared/index.ts"]},
        }
    }))
    _write(tmp_path / "packages" / "shared" / "index.ts", "export {};")
    resolver = TsconfigResolver(tmp_path)
    assert resolver.resolve_alias("@shared") == (
        tmp_path / "packages" / "shared" / "index.ts"
    ).resolve()


def test_resolver_tsx_resolution(tmp_path: Path):
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
    }))
    _write(tmp_path / "src" / "Button.tsx", "export {};")
    resolver = TsconfigResolver(tmp_path)
    resolved = resolver.resolve_alias("@/Button")
    assert resolved == (tmp_path / "src" / "Button.tsx").resolve()


def test_resolver_index_file_resolution(tmp_path: Path):
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
    }))
    _write(tmp_path / "src" / "lib" / "index.ts", "export {};")
    resolver = TsconfigResolver(tmp_path)
    resolved = resolver.resolve_alias("@/lib")
    assert resolved == (tmp_path / "src" / "lib" / "index.ts").resolve()


def test_resolver_baseurl_without_paths(tmp_path: Path):
    """baseUrl alone still allows non-relative imports like `lib/foo`."""
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": "src"}
    }))
    _write(tmp_path / "src" / "lib" / "util.ts", "export {};")
    resolver = TsconfigResolver(tmp_path)
    resolved = resolver.resolve_alias("lib/util")
    assert resolved == (tmp_path / "src" / "lib" / "util.ts").resolve()


def test_resolver_external_import_returns_none(tmp_path: Path):
    """Bare module names that do not match baseUrl/paths must be skipped
    (they are npm packages)."""
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": "src", "paths": {"@/*": ["src/*"]}}
    }))
    resolver = TsconfigResolver(tmp_path)
    assert resolver.resolve_alias("react") is None
    assert resolver.resolve_alias("@tanstack/react-query") is None


def test_resolver_caches_tsconfig_once(tmp_path: Path):
    """Subsequent resolutions should not re-read the file."""
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
    }))
    _write(tmp_path / "src" / "a.ts", "export {};")
    _write(tmp_path / "src" / "b.ts", "export {};")
    resolver = TsconfigResolver(tmp_path)
    a = resolver.resolve_alias("@/a")
    b = resolver.resolve_alias("@/b")
    assert a is not None and b is not None


def test_resolver_handles_tsconfig_comments(tmp_path: Path):
    """Many editors leave // line comments in tsconfig.json. Resolver should
    tolerate them (JSON with comments is common in TS tooling)."""
    tsconfig_with_comments = """
    {
      // Next.js path aliases
      "compilerOptions": {
        "baseUrl": ".",
        "paths": {
          "@/*": ["src/*"]  // alias for src
        }
      }
    }
    """
    _write(tmp_path / "tsconfig.json", tsconfig_with_comments)
    _write(tmp_path / "src" / "x.ts", "export {};")
    resolver = TsconfigResolver(tmp_path)
    assert resolver.resolve_alias("@/x") == (tmp_path / "src" / "x.ts").resolve()


def test_resolver_package_scoped_tsconfig_wins_over_root(tmp_path: Path):
    """Monorepo: a package subdirectory has its own tsconfig.json. Resolving
    a path inside that package should use the package-level paths."""
    # Root tsconfig: different alias
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": ".", "paths": {"@root/*": ["root/*"]}}
    }))
    # Package tsconfig with a different alias
    pkg = tmp_path / "packages" / "frontend"
    _write(pkg / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
    }))
    _write(pkg / "src" / "Button.tsx", "export {};")
    resolver = TsconfigResolver(tmp_path)
    # From a file inside packages/frontend/src, the package tsconfig applies.
    resolved = resolver.resolve_alias("@/Button", from_file=pkg / "src" / "Button.tsx")
    assert resolved == (pkg / "src" / "Button.tsx").resolve()


# ───── resolve_import() convenience ─────────────────────────────────────


def test_resolve_import_relative_path(tmp_path: Path):
    _write(tmp_path / "src" / "a.ts", "export {};")
    _write(tmp_path / "src" / "b.ts", "export {};")
    source_file = tmp_path / "src" / "a.ts"
    # Without tsconfig, relative imports still resolve.
    resolved = resolve_import(source_file, "./b", project_root=tmp_path)
    assert resolved == (tmp_path / "src" / "b.ts").resolve()


def test_resolve_import_parent_path(tmp_path: Path):
    _write(tmp_path / "src" / "lib" / "util.ts", "export {};")
    _write(tmp_path / "src" / "lib" / "inner" / "child.ts", "export {};")
    source_file = tmp_path / "src" / "lib" / "inner" / "child.ts"
    resolved = resolve_import(source_file, "../util", project_root=tmp_path)
    assert resolved == (tmp_path / "src" / "lib" / "util.ts").resolve()


def test_resolve_import_alias_through_tsconfig(tmp_path: Path):
    _write(tmp_path / "tsconfig.json", json.dumps({
        "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
    }))
    _write(tmp_path / "src" / "lib" / "api.ts", "export {};")
    source_file = tmp_path / "src" / "pages" / "home.tsx"
    resolved = resolve_import(source_file, "@/lib/api", project_root=tmp_path)
    assert resolved == (tmp_path / "src" / "lib" / "api.ts").resolve()


def test_resolve_import_with_dot_js_suffix(tmp_path: Path):
    """TS code often imports ``./foo.js`` referencing ``./foo.ts`` on disk.
    The resolver must accept this rewrite."""
    _write(tmp_path / "src" / "a.ts", "export {};")
    source_file = tmp_path / "src" / "b.ts"
    _write(source_file, "export {};")
    resolved = resolve_import(source_file, "./a.js", project_root=tmp_path)
    assert resolved == (tmp_path / "src" / "a.ts").resolve()


def test_resolve_import_external_returns_none(tmp_path: Path):
    source_file = tmp_path / "src" / "a.ts"
    _write(source_file, "export {};")
    assert resolve_import(source_file, "react", project_root=tmp_path) is None
    assert resolve_import(source_file, "@tanstack/react-query", project_root=tmp_path) is None
