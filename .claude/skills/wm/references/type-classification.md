# Request Type Classification (Detail)

## Type Table

| Type | Description | Example | Worktree |
|------|-------------|---------|----------|
| NEW_DEVELOPMENT | New feature development | "Add authentication feature" | Optional (recommended) |
| MODIFICATION | Modify existing feature | "Change login method" | Optional (recommended) |
| BUG_FIX (Complex) | Complex bug fix | "Fix login error with refactor" | Optional |
| BUG_FIX (Simple) | Simple bug fix | "Fix typo in error message" | No |
| INQUIRY | Analysis/Investigation | "Analyze code structure" | No |
| REPORT | Status report | "Show test coverage" | No |
| CLEANUP | File cleanup | "Delete unnecessary files" | No |
| **DOCUMENTATION** | Single doc file change | "Add status header to md file" | No |
| **DOCUMENTATION_BATCH** | Multiple doc files change | "Update all AGENTS.md files" | No |
| **MULTI_INTENT** | Multiple intents combined | "Fix bug AND add feature" | Depends |
| **RESTORATION** | Resume from checkpoint | Triggered by `/restore-context` | Inherit |

## Code Change Detection (Worktree Recommendation)

> **Core Rule**: Code file modification (`.ts`, `.py`, `.swift`, etc.) -> Worktree recommended (optional)

| Code Changes? | Type | Worktree |
|---------------|------|----------|
| **Yes** | NEW_DEVELOPMENT, MODIFICATION, BUG_FIX(Complex) | **Optional (recommended)** |
| **No** | DOCUMENTATION, INQUIRY, REPORT, CLEANUP | Not required |

**Key Rules**:
- **Code files** = `.ts`, `.tsx`, `.py`, `.swift`, `.go`, `.java`, `.sql`, etc.
- **Doc files** = `.md`, `.mdx`, `.txt` (except when bundled with code changes)
- If `.md` + code file modified -> **MODIFICATION** (worktree recommended)
- If only `.md` files -> **DOCUMENTATION** (no worktree)

## DOCUMENTATION Sub-Classification

| Condition | Sub-Type | Execution |
|-----------|----------|-----------|
| Single file | `DOCUMENTATION` | Main Context Direct Edit |
| 2+ files | `DOCUMENTATION_BATCH` | Task Tool + Parallel Agents |

**Detection Logic**:
- Count unique `.md` file references in plan requirements
- 1 file -> `DOCUMENTATION` (minimal validation, direct edit)
- 2+ files -> `DOCUMENTATION_BATCH` (Task tools, Agent Execution Log)

## Multi-Intent Detection

Check for multiple intents when request contains: "AND", "also", "plus", comma-separated tasks, numbered lists, or multiple distinct action verbs.

When multiple intents detected, classify as `MULTI_INTENT`. See [multi-intent.md](../rules/processes/multi-intent.md) for template composition rules.

## RESTORATION Type Detection

Detect RESTORATION when:
- `/restore-context` skill triggered the wm invocation
- Checkpoint file exists at `.claude/workflow-checkpoint.json`
- Previous plan document exists with incomplete checkboxes

When RESTORATION detected:
1. Skip normal classification
2. Read checkpoint file for last state
3. Read Plan document for in_progress agentId
4. Resume from last known position

## BUG_FIX Sub-Classification

BUG_FIX has 3 sub-types: **Simple**, **Complex**, **E2E/Frontend**. Classification is performed by wm in Step 2 using the functions in [type-classification-functions.md](../rules/components/type-classification-functions.md).

Quick heuristic: E2E keywords (Playwright, UI, browser, spec.ts) -> E2E, single-file typo/config -> Simple, everything else -> Complex.
