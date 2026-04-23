---
title: Validator Role Index
role: validator
type: index
version: 1.0.0
---

# Validator Role - Validation Analysis

> Validate plan completeness and consistency

## Role Overview

<role>Plan Validator</role>
<primary_agent>planner-task (Self-Validation)</primary_agent>

**Core Responsibilities**:
- Verify PHASE coverage against PRD goals
- Verify Task coverage against PHASE goals
- Validate dependency order
- Identify gaps and duplicates

## Available Prompts

| Prompt | File | Priority | Description |
|--------|------|----------|-------------|
| Coverage Check | `role-validator-coverage-check.md` | HIGH | Coverage validation |
| Dependency Order | `role-validator-dependency-order.md` | HIGH | Dependency order verification |

## Quick Reference

> See `_common-criteria.md` → Validator Role Criteria for detailed XML definitions

## Recommended Enhancers

| Enhancer | Purpose | When to Use |
|----------|---------|-------------|
| investigate-before-answering | Document verification required | Always |
| verbosity-control | Validation result detail level | Detailed reports |

## Usage Example

> **Template Reference**: See [plan-types-reference.md](../../wm/rules/components/plan-types/plan-types-reference.md) VALIDATOR section for complete invocation template.

```python
# Validate plan coverage
role_prompt = Read("plan-prompts/rules/role-validator-coverage-check.md")
enhancers = [
    Read("plan-prompts/rules/enhancer-investigate-before-answering.md")
]
combined_enhancers = "\n\n".join(enhancers)

Task(
    subagent_type="planner-task",  # VALIDATOR type → planner-task agent (Self-Validation)
    description="Validate plan coverage",  # Required: 3-5 word description
    prompt=f"""
## Validation Goal
Validate full PRD-PHASE-Task coverage and dependencies

## Input Documents
- PRD: {prd_content}
- PHASEs: {phases}
- Tasks: {tasks}

## Role Prompt
{role_prompt}

## Enhancers
{combined_enhancers}

## Expected Output
- validation_summary: status, coverage_percentage
- coverage_analysis: requirement coverage
- dependency_analysis: dependency validation
- issues[]: level, description, recommendation

## Validation Depth: Standard
""",
    model="haiku",  # haiku is sufficient for checklist validation
    run_in_background=False  # Validation typically fast, background optional
)
```

## Output Format

Output: `validation_summary`, `coverage_analysis`, `dependency_analysis`, `issues[]`

> Full example: `_output-formats.md#validation`

## Validation Checklist

```
PRD → PHASE Validation
├── [ ] All functional requirements covered
├── [ ] All non-functional requirements covered
├── [ ] Constraints reflected
└── [ ] Priorities reflected

PHASE → Task Validation
├── [ ] All PHASE goals decomposed into Tasks
├── [ ] Tasks exist for all deliverables
├── [ ] TDD order applied
└── [ ] Layer order applied

Dependency Validation
├── [ ] No circular dependencies
├── [ ] All predecessor conditions specified
├── [ ] Critical Path identified
└── [ ] Parallelization opportunities identified

Quality Validation
├── [ ] Task size appropriate (30min-2hours)
├── [ ] Completion criteria clear
├── [ ] Test strategy exists
└── [ ] Risk mitigation plan exists
```

## Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| CRITICAL | Issue prevents plan execution | Fix immediately |
| ERROR | Serious gap or error | Fix before plan approval |
| WARNING | Potential issue or improvement needed | Review and decide |
| INFO | Informational recommendation | Optional implementation |
