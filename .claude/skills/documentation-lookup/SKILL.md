# Documentation Lookup Skill

## When to Use

- When you need accurate, up-to-date API documentation for libraries used in this project
- When unsure about function signatures, configuration options, or best practices
- When implementing features that depend on specific library versions
- Auto-loaded by: `design`, `dev-executor` agents

## How It Works

Uses the Context7 MCP server to fetch live documentation. Two-step process:

1. **Resolve library ID**: `mcp__context7__resolve-library-id` — find the correct library identifier
2. **Query documentation**: `mcp__context7__query-docs` — search docs with your specific question

Maximum 3 Context7 calls per question to avoid excessive lookups.

## Supported Libraries (graphify)

| Library | Version | Use Case |
|---------|---------|----------|
| networkx | latest | Graph data structure (core) |
| tree-sitter | latest | Multi-language AST parsing (25+ grammars) |
| graspologic | latest | Leiden community detection (Python <3.13) |
| faster-whisper | optional | Audio/video transcription (optional extra) |
| pypdf | optional | PDF ingestion (optional extra) |
| neo4j | optional | Graph export (optional extra) |
| mcp | optional | MCP stdio server (optional extra) |
| pytest | latest | Test framework |
| ruff | latest | Python linter + formatter |

Target codebases analyzed by graphify may use any language/framework. When
graphify itself needs documentation for a target codebase's library, resolve
that library via Context7 directly — graphify does not constrain the target's
tech stack.

## Usage Pattern

```python
# Step 1: Resolve the library
result = mcp__context7__resolve-library-id(libraryName="networkx")
# Returns: library ID for NetworkX

# Step 2: Query specific documentation
docs = mcp__context7__query-docs(
    libraryId=result.id,
    query="directed graph adjacency iteration"
)
# Returns: relevant documentation sections
```

## Examples

### Looking up NetworkX DiGraph operations
```python
lib = mcp__context7__resolve-library-id(libraryName="networkx")
docs = mcp__context7__query-docs(libraryId=lib.id, query="DiGraph successors predecessors")
```

### Looking up tree-sitter language bindings
```python
lib = mcp__context7__resolve-library-id(libraryName="tree-sitter")
docs = mcp__context7__query-docs(libraryId=lib.id, query="python binding query pattern")
```

### Looking up graspologic Leiden clustering
```python
lib = mcp__context7__resolve-library-id(libraryName="graspologic")
docs = mcp__context7__query-docs(libraryId=lib.id, query="leiden community detection seed")
```

## Rules

1. Always resolve the library ID first — don't guess IDs
2. Be specific in your query — "hono zod validator" not just "validation"
3. Maximum 3 Context7 calls per question
4. If Context7 returns no results, fall back to your training knowledge
5. Cross-reference documentation with project's current version (check package.json)
