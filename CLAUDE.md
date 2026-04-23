# graphify — Repository Instructions

## What This Repo Is

**graphify** is a deterministic knowledge-graph CLI and Python library. It ingests
codebases (via tree-sitter AST across 25+ languages), PDFs, markdown, and media
(Whisper-transcribed), builds a NetworkX graph, detects communities (Leiden via
graspologic), and emits `graph.json` + `graph.html` + `GRAPH_REPORT.md` per run.
Current version: v0.5.4.

**This is NOT** a web service, multi-tenant SaaS, Next.js app, or database-backed
system. Any rule or example under `.claude/` that references `admin-portal`,
`admin-api`, `billing-api`, Hono, postgres.js, `tenant_id`, RBAC, React Query, or
multi-tenant middleware does NOT apply here — treat such content as legacy
contamination to be ignored or flagged for cleanup (see
`.claude/plans/mighty-floating-cook.md`).

## Stack

- **Language**: Python 3.10+ (pure Python, no TypeScript/JS in core)
- **Core**: `networkx`, `tree-sitter` + 25 parsers, `graspologic` (Python <3.13)
- **Optional extras**: `faster-whisper`, `pypdf`, `neo4j`, `mcp` (stdio server)
- **Build**: `pyproject.toml` (setuptools); CLI entry `graphify = graphify.__main__:main`
- **Test**: `pytest tests/ -q`

## Key Entrypoints

- `graphify/__main__.py` — CLI dispatcher (`build`, `resolve`, `callees`, `callers`,
  `blast`, `watch`, `update`, `cluster-only`, `query`, `path`)
- `graphify/extract.py` — per-file AST extraction (multi-language, deterministic)
- `graphify/build.py` — graph construction pipeline (NetworkX DiGraph or Graph)
- `graphify/routes.py` — Next.js App Router + Hono route scanner (for *target*
  codebases being analyzed; graphify itself has no HTTP server)
- `graphify/cli_graph_query.py` — query commands (`resolve`, `callers`, `callees`, `blast`)
- `graphify/cache.py` — SHA256 parser cache (v3 schema)

## Output Conventions

- Default output: `graphify-out/{graph.json, graph.html, GRAPH_REPORT.md, cache/}`
- `--out-dir` relocates artifacts; `--cache-dir` relocates the 13MB parser cache
  (v0.5.4+; defaults to follow `--out-dir`)
- `.graphifyignore` at repo root (gitignore syntax) controls exclusion

## Skills

- **`/graphify`** (`~/.claude/skills/graphify/SKILL.md`) — invoke via
  `Skill("graphify")` on user trigger. When the user types `/graphify`, invoke
  the Skill tool with `skill: "graphify"` before doing anything else.
- `.claude/rules/stack-conventions.md` — graphify-specific conventions (naming,
  testing, output, determinism, prohibited patterns).

## Determinism Contract

The AST + route + HTTP extraction pipeline MUST be deterministic: same input →
identical `graph.json`. Non-deterministic paths (Whisper transcription, OCR) are
opt-in only and never participate in the deterministic core.
