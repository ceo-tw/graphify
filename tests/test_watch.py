"""Tests for watch.py - file watcher helpers (no watchdog required)."""
import time
from pathlib import Path
import pytest

from graphify.watch import _notify_only, _WATCHED_EXTENSIONS


# --- _rebuild_code persisted labels ---

def test_rebuild_code_reads_persisted_labels(tmp_path, monkeypatch):
    """When .graphify_labels.json exists, rebuild uses those labels instead of 'Community N'."""
    import graphify.watch as watch_mod

    watch_path = tmp_path / "repo"
    out = watch_path / "graphify-out"
    out.mkdir(parents=True)
    (watch_path / "sample.py").write_text("def foo():\n    pass\n")
    # Seed labels before rebuild
    (out / ".graphify_labels.json").write_text('{"0": "[BE/api] Sample Module"}')

    # Minimal stub graph data (one node, one edge, community 0)
    stub_extract_result = {
        "nodes": [{"id": "sample.foo", "label": "foo", "file": "sample.py", "file_type": "code"}],
        "edges": [{"source": "sample.foo", "target": "sample.foo", "type": "DEFINES"}],
        "hyperedges": [],
        "input_tokens": 0,
        "output_tokens": 0,
    }

    monkeypatch.setattr("graphify.watch._rebuild_code.__module__", "graphify.watch")

    # Patch extract to avoid tree-sitter dependency
    import graphify.extract as extract_mod
    monkeypatch.setattr(extract_mod, "extract", lambda files, **kwargs: stub_extract_result)

    from graphify.watch import _rebuild_code
    ok = _rebuild_code(watch_path)
    assert ok
    # Verify labels survived in the output
    html = (out / "graph.html").read_text()
    assert "[BE/api] Sample Module" in html or "Community 0" not in html


# --- _rebuild_code cache relocation ---

def _stub_extract(captured):
    """Build an extract() stub that captures the cache_override kwarg it sees."""
    def _fake(files, **kwargs):
        captured["cache_root"] = kwargs.get("cache_root")
        captured["cache_override"] = kwargs.get("cache_override")
        return {
            "nodes": [{"id": "sample.foo", "label": "foo", "file": "sample.py", "file_type": "code"}],
            "edges": [{"source": "sample.foo", "target": "sample.foo", "type": "DEFINES"}],
            "hyperedges": [],
            "input_tokens": 0,
            "output_tokens": 0,
        }
    return _fake


def test_rebuild_code_cache_follows_out_dir(tmp_path, monkeypatch):
    """When out_dir is set and cache_dir is omitted, cache defaults to <out_dir>/cache/ — NOT <src>/graphify-out/cache/."""
    import graphify.extract as extract_mod
    captured: dict = {}
    monkeypatch.setattr(extract_mod, "extract", _stub_extract(captured))

    watch_path = tmp_path / "repo"
    watch_path.mkdir()
    (watch_path / "sample.py").write_text("def foo():\n    pass\n")

    out = tmp_path / "elsewhere" / "graphify-out"
    from graphify.watch import _rebuild_code
    assert _rebuild_code(watch_path, out_dir=out)

    assert captured["cache_override"] == (out / "cache").resolve()
    assert captured["cache_root"] == watch_path.resolve(), "hash root stays at source tree"


def test_rebuild_code_cache_dir_override(tmp_path, monkeypatch):
    """Explicit cache_dir beats the <out_dir>/cache default."""
    import graphify.extract as extract_mod
    captured: dict = {}
    monkeypatch.setattr(extract_mod, "extract", _stub_extract(captured))

    watch_path = tmp_path / "repo"
    watch_path.mkdir()
    (watch_path / "sample.py").write_text("def bar():\n    pass\n")
    out = tmp_path / "out"
    explicit_cache = tmp_path / "shared-cache"

    from graphify.watch import _rebuild_code
    assert _rebuild_code(watch_path, out_dir=out, cache_dir=explicit_cache)

    assert captured["cache_override"] == explicit_cache.resolve()


def test_rebuild_code_default_cache_is_back_compat(tmp_path, monkeypatch):
    """Without out_dir or cache_dir, cache stays at <watch_path>/graphify-out/cache/ — identical to pre-fix behavior."""
    import graphify.extract as extract_mod
    captured: dict = {}
    monkeypatch.setattr(extract_mod, "extract", _stub_extract(captured))

    watch_path = tmp_path / "repo"
    watch_path.mkdir()
    (watch_path / "sample.py").write_text("def baz():\n    pass\n")

    from graphify.watch import _rebuild_code
    assert _rebuild_code(watch_path)

    expected = (watch_path / "graphify-out" / "cache").resolve()
    assert captured["cache_override"] == expected


# --- _notify_only ---

def test_notify_only_creates_flag(tmp_path):
    _notify_only(tmp_path)
    flag = tmp_path / "graphify-out" / "needs_update"
    assert flag.exists()
    assert flag.read_text() == "1"

def test_notify_only_creates_flag_dir(tmp_path):
    # graphify-out dir does not exist yet
    assert not (tmp_path / "graphify-out").exists()
    _notify_only(tmp_path)
    assert (tmp_path / "graphify-out").is_dir()

def test_notify_only_idempotent(tmp_path):
    _notify_only(tmp_path)
    _notify_only(tmp_path)
    flag = tmp_path / "graphify-out" / "needs_update"
    assert flag.read_text() == "1"


# --- _WATCHED_EXTENSIONS ---

def test_watched_extensions_includes_code():
    assert ".py" in _WATCHED_EXTENSIONS
    assert ".ts" in _WATCHED_EXTENSIONS
    assert ".go" in _WATCHED_EXTENSIONS
    assert ".rs" in _WATCHED_EXTENSIONS

def test_watched_extensions_includes_docs():
    assert ".md" in _WATCHED_EXTENSIONS
    assert ".txt" in _WATCHED_EXTENSIONS
    assert ".pdf" in _WATCHED_EXTENSIONS

def test_watched_extensions_includes_images():
    assert ".png" in _WATCHED_EXTENSIONS
    assert ".jpg" in _WATCHED_EXTENSIONS

def test_watched_extensions_excludes_noise():
    assert ".json" not in _WATCHED_EXTENSIONS
    assert ".pyc" not in _WATCHED_EXTENSIONS
    assert ".log" not in _WATCHED_EXTENSIONS


# --- watch() import error without watchdog ---

def test_watch_raises_without_watchdog(tmp_path, monkeypatch):
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "watchdog.observers" or name == "watchdog.events":
            raise ImportError("mocked missing watchdog")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    from graphify.watch import watch
    with pytest.raises(ImportError, match="watchdog not installed"):
        watch(tmp_path)
