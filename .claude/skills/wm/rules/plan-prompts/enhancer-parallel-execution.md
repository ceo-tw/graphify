---
title: Parallel Execution
type: enhancer
source: .claude/docs/claude-code-prompt/04-tool-usage/parallel-tool-calling.md
applicable_to: all
priority: HIGH
---

# Enhancer: Parallel Execution

> Maximize efficiency by executing independent operations in parallel

## Purpose

- Speed improvement through parallel execution of independent operations
- Ensure correct sequential execution for dependent operations
- Optimize resource utilization

## Pattern

<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the
tool calls, make all of the independent tool calls in parallel. Prioritize
calling tools simultaneously whenever the actions can be done in parallel
rather than sequentially.

For example, when reading 3 files, run 3 tool calls in parallel to read all
3 files into context at the same time.

Maximize use of parallel tool calls where possible to increase speed and
efficiency.

However, if some tool calls depend on previous calls to inform dependent
values like the parameters, do NOT call these tools in parallel and instead
call them sequentially. Never use placeholders or guess missing parameters
in tool calls.
</use_parallel_tool_calls>

## Decision Tree

```
Are operations independent?
├── YES: Can run in parallel
│   └── Are there system stability concerns?
│       ├── YES: Consider sequential or batched
│       └── NO: Run all in parallel
│
└── NO: Operations have dependencies
    └── Run sequentially in dependency order
```

## When to Use

- Reading multiple files simultaneously
- Searching multiple patterns
- Performing independent analysis tasks
- Exploring multiple directories

## Parallel Scenarios

| Scenario | Operations | Parallel? |
|----------|------------|-----------|
| Reading multiple files | Read A, Read B, Read C | Yes |
| Searching multiple patterns | Grep X, Grep Y, Grep Z | Yes |
| Getting multiple API responses | Fetch URL1, Fetch URL2 | Yes |
| Running independent tests | Test suite A, Test suite B | Yes |

## Sequential Scenarios

| Scenario | Operations | Sequential? |
|----------|------------|-------------|
| Create then use | mkdir → touch file | Yes |
| Read then edit | Read file → Edit based on content | Yes |
| Build then test | npm build → npm test | Yes |
| Query then process | DB query → process results | Yes |

## Integration Example

```python
# Architect analysis with parallel exploration
role_prompt = Read("rules/role-architect-component-design.md")
enhancer = Read("rules/enhancer-parallel-execution.md")

combined = f"""
{role_prompt}

{enhancer}

Read multiple related files in parallel to understand existing architecture patterns.
"""

Task(subagent_type="design", prompt=combined, model="opus")  # or planner-task, dev-executor
```

## Balanced Approach

For complex workflows, combine both:

<balanced_tool_calling>
Use parallel execution for independent operations and sequential for dependencies.

Example workflow - Setting up a feature:
1. [Parallel] Read all relevant files (5 files simultaneously)
2. [Sequential] Analyze patterns → Make decision
3. [Parallel] Make independent edits (3 files simultaneously)
4. [Sequential] Run tests → Fix if needed → Run again
5. [Parallel] Update docs and add tests

This maximizes efficiency while respecting dependencies.
</balanced_tool_calling>

## Efficiency Guidelines

| Phase | Approach |
|-------|----------|
| Discovery | Parallel (glob, grep, read) |
| Analysis | Parallel reads, sequential analysis |
| Changes | Parallel edits if independent |
| Verification | Sequential (build → test → lint) |

## Batched Parallel

When dealing with many items:

<batched_parallel>
Process in batches to balance speed and stability:

Large file set (20 files):
- Batch 1: Files 1-5 [parallel]
- Batch 2: Files 6-10 [parallel]
- Batch 3: Files 11-15 [parallel]
- Batch 4: Files 16-20 [parallel]

This prevents overwhelming the system while still gaining parallel benefits.
</batched_parallel>

## Related

- [Investigate Before Answering](enhancer-investigate-before-answering.md)
- [Verbosity Control](enhancer-verbosity-control.md)

## Source

Extracted from: `.claude/docs/claude-code-prompt/04-tool-usage/parallel-tool-calling.md`
