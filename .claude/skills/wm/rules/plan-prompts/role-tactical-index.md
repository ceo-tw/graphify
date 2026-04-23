---
title: Tactical Role Index
role: tactical
type: index
version: 1.0.0
---

# Tactical Role - Tactical Analysis

> Decompose PHASEs into executable Tasks and determine implementation order

## Role Overview

<role>Tactical Planner</role>
<primary_agent>planner-task</primary_agent>

**Core Responsibilities**:
- Decompose PHASE goals into Tasks
- Apply TDD sequence (RED→GREEN→REFACTOR)
- Infer and order layers
- Define expected deliverables for each Task

## Available Prompts

| Prompt | File | Priority | Description |
|--------|------|----------|-------------|
| Task Breakdown | `role-tactical-task-breakdown.md` | HIGH | PHASE to Task decomposition |
| TDD Ordering | `role-tactical-tdd-ordering.md` | HIGH | TDD workflow ordering |
| Layer Inference | `role-tactical-layer-inference.md` | MEDIUM | Layer order inference |

## Quick Reference

> See `_common-criteria.md` → Tactical Role Criteria for detailed XML definitions

## Recommended Enhancers

| Enhancer | Purpose | When to Use |
|----------|---------|-------------|
| investigate-before-answering | Code verification required | Always |
| code-exploration | Explore existing structure | Pattern analysis |
| parallel-execution | Identify parallel Tasks | Multi-task phases |

## Usage Example

> **Template Reference**: See [plan-types-reference.md](../../wm/rules/components/plan-types/plan-types-reference.md) TACTICAL section for complete invocation template.

```python
# Task breakdown for a PHASE
role_prompt = Read("plan-prompts/rules/role-tactical-task-breakdown.md")
enhancers = [
    Read("plan-prompts/rules/enhancer-investigate-before-answering.md"),
    Read("plan-prompts/rules/enhancer-code-exploration.md")
]
combined_enhancers = "\n\n".join(enhancers)

Task(
    subagent_type="planner-task",  # TACTICAL type → planner-task agent
    description="Break down PHASE into Tasks",  # Required: 3-5 word description
    prompt=f"""
## Planning Goal
Decompose PHASE goals into Tasks based on TDD workflow

## Input Context
- PHASE: {phase_description}
- Existing Code: {relevant_files}
- Constraints: {constraints}

## Role Prompt
{role_prompt}

## Enhancers
{combined_enhancers}

## Expected Output
- phase_id: PHASE identifier
- tasks[]: id, subject, tdd_stage, layer, description
- execution_order: task sequence
- parallel_groups[]: tasks that can run in parallel

## Planning Depth: Standard
""",
    model="opus",  # Tactical planning requires strongest model
    run_in_background=True  # Recommended for complex PHASEs
)
```

## Output Format

Output: `phase_id`, `tasks[]`, `execution_order`, `parallel_groups[]`, `layer_sequence`

> Full example: `_output-formats.md#task-breakdown`

## TDD Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TDD Cycle                                 │
│                                                                  │
│     ┌───────────┐                                               │
│     │    RED    │  1. Write failing test                        │
│     │  (Test)   │  2. Confirm clear failure                     │
│     └─────┬─────┘                                               │
│           │                                                      │
│           ▼                                                      │
│     ┌───────────┐                                               │
│     │   GREEN   │  3. Minimal code to pass test                 │
│     │  (Code)   │  4. "Just make it work"                       │
│     └─────┬─────┘                                               │
│           │                                                      │
│           ▼                                                      │
│     ┌───────────┐                                               │
│     │ REFACTOR  │  5. Improve code quality                      │
│     │ (Clean)   │  6. Confirm tests still pass                  │
│     └─────┬─────┘                                               │
│           │                                                      │
│           └──────────────► Repeat for next feature              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Implementation Order

```
Implementation order (minimize dependencies):

1. Domain Layer (Foundation)
   └── Does not depend on other layers
   └── Core of business rules

2. Application Layer (Logic)
   └── Depends only on Domain
   └── Define use cases

3. Infrastructure Layer (Implementation)
   └── Implements Domain, Application interfaces
   └── External system integration

4. Presentation Layer (Interface)
   └── Integrates all layers
   └── User interface
```
