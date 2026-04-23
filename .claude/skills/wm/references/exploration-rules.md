# File Exploration Rules (Detail)

> **Guide**: Use [Explore Prompt Guide](../rules/components/explore-prompt-guide.md) for structured exploration prompts.

When file exploration is needed, **prefer the Explore agent** for broad codebase searches. Reading known file paths with `Read()` is allowed.

## Explore Type System

The Explore agent uses 4 types based on purpose:

| Type | Purpose | Thoroughness |
|------|---------|--------------|
| **LOCATE** | File/structure location | Quick |
| **ANALYZE** | Pattern/implementation analysis | Medium |
| **COLLECT** | Data/statistics collection | Quick |
| **ASSESS** | Impact range assessment | Medium |

> **Templates & examples**: See [explore-types-reference.md](../rules/components/explore-types/explore-types-reference.md)

## Process-to-Type Mapping

| Process | Primary Type | Secondary Type |
|---------|--------------|----------------|
| NEW_DEVELOPMENT | LOCATE | ANALYZE |
| MODIFICATION | LOCATE | ASSESS |
| BUG_FIX (Complex) | LOCATE | ANALYZE |
| INQUIRY | ANALYZE | - |
| REPORT | COLLECT | - |

## Correct vs Forbidden

| Action | Status | Tool |
|--------|--------|------|
| Search via Explore agent | Allowed | `Task(subagent_type="Explore", model="haiku")` |
| Read known file path | Allowed | `Read("/path/to/known/file.ts")` |
| Direct Glob | Forbidden | - |
| Direct Grep | Forbidden | - |
| Read for exploration | Forbidden | - |

**Model**: Always use `model="haiku"` (exception: `sonnet` for architecture deep-dive only)

> **Templates**: See [Explore Prompt Guide](../rules/components/explore-prompt-guide.md) for structured prompts and examples
