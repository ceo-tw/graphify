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

## Supported Libraries

| Library | Version | Use Case |
|---------|---------|----------|
| Hono | 4.x | Backend API framework (admin-api, billing-api) |
| Next.js | 15.x | Frontend framework with App Router (admin-portal) |
| React | 19.x | UI library |
| shadcn/ui | latest | UI component library (Radix UI + Tailwind CSS) |
| Tailwind CSS | 4.x | Utility-first CSS |
| postgres.js | latest | PostgreSQL driver |
| ioredis | latest | Redis client |
| NATS | latest | JetStream messaging |
| Zod | latest | Schema validation |
| react-hook-form | latest | Form management |
| @tanstack/react-query | latest | Server state management |
| Zustand | latest | Client state management |
| @polar-sh/sdk | latest | Global billing SDK |
| Playwright | latest | E2E testing |
| Vitest | latest | Unit/integration testing (admin-portal) |

## Usage Pattern

```python
# Step 1: Resolve the library
result = mcp__context7__resolve-library-id(libraryName="hono")
# Returns: library ID for Hono

# Step 2: Query specific documentation
docs = mcp__context7__query-docs(
    libraryId=result.id,
    query="how to use zod-validator middleware"
)
# Returns: relevant documentation sections
```

## Examples

### Looking up Hono middleware patterns
```python
lib = mcp__context7__resolve-library-id(libraryName="hono")
docs = mcp__context7__query-docs(libraryId=lib.id, query="zod validator middleware")
```

### Looking up Next.js App Router server actions
```python
lib = mcp__context7__resolve-library-id(libraryName="next.js")
docs = mcp__context7__query-docs(libraryId=lib.id, query="server actions app router")
```

### Looking up shadcn/ui component usage
```python
lib = mcp__context7__resolve-library-id(libraryName="shadcn-ui")
docs = mcp__context7__query-docs(libraryId=lib.id, query="data table with pagination")
```

## Rules

1. Always resolve the library ID first — don't guess IDs
2. Be specific in your query — "hono zod validator" not just "validation"
3. Maximum 3 Context7 calls per question
4. If Context7 returns no results, fall back to your training knowledge
5. Cross-reference documentation with project's current version (check package.json)
