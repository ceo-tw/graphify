# Stack Conventions

> Project-specific rules for the **graphify** project (Python CLI + library, v0.5.x).
>
> graphify is a deterministic knowledge-graph tool — not a web service, not multi-tenant,
> no database, no frontend. Any legacy rule referencing Next.js, Hono, postgres.js,
> multi-tenant, RBAC, React Query, admin-portal/admin-api/billing-api does NOT apply here.

## Project Nature

- **CLI + library**: primary surface is `graphify` CLI (`graphify/__main__.py`) and the
  Python package consumed by MCP clients, Claude Code Skills, and direct imports.
- **Pure Python 3.10+**: no TypeScript, no JavaScript in the `graphify/` package.
- **Deterministic-first**: AST + route scanning via `tree-sitter` and regex; optional
  semantic paths (Whisper transcribe, document ingest) are opt-in only.
- **No server, no DB**: artifacts are files under `--out-dir` / `--cache-dir`.

## Naming

| Context | Convention | Example |
|---------|-----------|---------|
| Python modules & files | snake_case | `graph_builder.py`, `http_calls.py` |
| Python classes | PascalCase | `GraphBuilder`, `AnalyzerResult` |
| Python functions / vars | snake_case | `build_graph()`, `parse_ast_node` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_DEPTH`, `CACHE_TTL` |
| Environment variables | SCREAMING_SNAKE_CASE | `GRAPHIFY_DEBUG`, `GRAPHIFY_CACHE_DIR` |
| CLI subcommands | kebab-case | `cluster-only`, `build`, `watch` |
| Output files | kebab-case + extension | `graph.json`, `GRAPH_REPORT.md` |
| Graphify edge tags | SCREAMING_SNAKE_CASE (canonical) | `EXTRACTED`, `INFERRED`, `AMBIGUOUS` |

## Testing

- **Framework**: `pytest` (discovery in `tests/`).
- **TDD preferred**: non-trivial features should land a failing test first, then the
  implementation. Bug fixes should land a regression test before the fix.
- **Coverage priorities**: graph structure invariants, node deduplication, route/HTTP
  extraction edge cases, cache correctness, determinism (same input → identical
  `graph.json` hash across runs).
- **Tree-sitter grammar changes**: add fixture files under `tests/fixtures/` so language
  regressions are caught.

## Output & Caching

- **`--out-dir`** controls artifact location (default `./graphify-out/`).
- **`--cache-dir`** relocates the parser cache (v0.5.4+); default follows `--out-dir`.
- Every run emits: `graph.json`, `graph.html`, `GRAPH_REPORT.md`.
- **Edge tag vocabulary** is canonical: `EXTRACTED` / `INFERRED` / `AMBIGUOUS`. New tags
  require a CHANGELOG entry with rationale; consumers depend on this three-value set.
- **Incremental rebuild** via SHA256 cache (schema v3). Cache invalidates on CLI
  version bump or parser upgrade.
- **Cache schema version bumps** (v3 → v4 etc.) must update the version constant AND
  add a CHANGELOG entry in the same commit range.

## Determinism Contract

- AST + route + HTTP extraction **must** be deterministic — same input produces an
  identical `graph.json` byte-for-byte (up to deterministic ordering).
- Non-deterministic paths (Whisper transcription, OCR, semantic embedding) are opt-in
  via explicit CLI flags and **never** participate in the deterministic core pipeline
  (`extract.py`, `build.py`, `routes.py`, `http_calls.py`, `analyze.py`,
  `cli_graph_query.py`).
- Leiden community detection (`cluster.py`) uses a fixed seed; changing the seed
  requires a CHANGELOG + migration note.
- Forbidden in the deterministic pipeline: `random.*` without injected seed,
  `time.time()`, `datetime.now()`, `uuid.uuid4()`, and any wall-clock sort key.

## Logging

- Use `logging` stdlib with module-scoped loggers
  (`logger = logging.getLogger(__name__)`).
- `print()` allowed only for CLI user output on **stdout** in `__main__.py` and
  `cli_*.py`.
- Progress / warnings → **stderr**; graph-pipeable output (e.g., JSON) → **stdout**,
  so `--out-dir` redirect semantics hold.
- Never log full file contents or user absolute paths at INFO — gate on `--debug`.
- Never log target-codebase secrets (API keys, tokens) discovered during analysis —
  redact before logging.

## Dependencies & Packaging

- Pin majors in `pyproject.toml`; keep heavy deps (`faster-whisper`, `pypdf`, `neo4j`,
  `mcp`) as optional extras.
- Optional extras must be gated behind `try / ImportError` so missing extras degrade
  to "feature unavailable", never crash the CLI.
- `.venv/`, `__pycache__/`, `*.pyc`, `graphify-out/` must be in `.gitignore`.
- Never commit cache directories or generated graphs.
- New top-level dependency → update `pyproject.toml` in the same commit.

## Security

- **No eval / exec**: graphify must never execute analyzed target code.
  `eval(...)`, `exec(...)`, `subprocess.run(..., shell=True)`, `os.system(...)` on
  analyzed content are forbidden.
- **Path traversal**: all file writes must stay under the resolved `--out-dir` /
  `--cache-dir`. Canonicalize user-provided paths before writing.
- **Ingest SSRF**: URL fetching in `ingest.py` must allowlist `http` / `https`,
  reject loopback / link-local / metadata ranges, cap redirects, enforce content-type.
- **Secrets stripping**: analyzed source may contain API keys / tokens. These must not
  appear in `graph.json` / `graph.html` / `GRAPH_REPORT.md`.

## Prohibited

- Magic numbers / hardcoded absolute paths in library code (use constants / CLI args).
- Direct push to `main` (PR + CI required — see recent v0.5.x release hygiene).
- `eval()` / `exec()` on analyzed code (security boundary).
- `subprocess.run(..., shell=True)` with analyzed content as input.
- Modifying deployed CHANGELOG entries (append-only; amend with a new entry instead).
- JavaScript / TypeScript under the `graphify/` package (pure Python core — if a
  front-end artifact is needed, gate behind an optional extra with a separate package).
- Breaking the edge-tag vocabulary (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`) without
  a CHANGELOG + version bump.
- Whisper / OCR / semantic embedding in deterministic pipeline paths.
- Non-deterministic calls (`random.*`, `time.time()`, `datetime.now()`,
  `uuid.uuid4()`) in the deterministic pipeline.
- `print()` in library modules (non-CLI code).
- Unbounded network fetches (no redirect cap, no timeout, no content-type check).

## References

- `CHANGELOG.md` — version-by-version capability log (append-only)
- `GETTING_STARTED.md` — URL-centric workflow primer
- `ARCHITECTURE.md` — module responsibility map
- `README.md` — primary documentation (multilingual support)
- `.claude/skills/knowledge-graph/SKILL.md` — CLI wrapper skill
- `pyproject.toml` — package metadata, dependencies, CLI entry points
