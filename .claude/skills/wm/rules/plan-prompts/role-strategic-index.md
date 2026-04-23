---
title: Strategic Role Index
role: strategic
type: index
version: 1.0.0
---

# Strategic Role - Strategic Analysis

> Decompose PRD requirements into PHASE units and establish strategic plans

## Role Overview

<role>Strategic Planner</role>
<primary_agent>wm (Plan Writing)</primary_agent>

**Core Responsibilities**:
- Understand the full scope of requirements
- Decompose into independently deployable PHASE units
- Identify dependencies between PHASEs
- Assess risks and establish mitigation strategies

## Available Prompts

| Prompt | File | Priority | Description |
|--------|------|----------|-------------|
| Phase Decomposition | `role-strategic-phase-decomposition.md` | HIGH | PRD to PHASE decomposition |
| Dependency Analysis | `role-strategic-dependency-analysis.md` | HIGH | Inter-PHASE dependency analysis |
| Risk Assessment | `role-strategic-risk-assessment.md` | MEDIUM | Risk identification and mitigation |

## Quick Reference

> See `_common-criteria.md` → Strategic Role Criteria for detailed XML definitions

## Recommended Enhancers

| Enhancer | Purpose | When to Use |
|----------|---------|-------------|
| investigate-before-answering | Prevent speculation | Always |
| structured-research | Hypothesis-based analysis | Complex requirements |
| parallel-execution | Parallel exploration | Large codebases |

## Usage Example

> **Template Reference**: See [plan-types-reference.md](../../wm/rules/components/plan-types/plan-types-reference.md) STRATEGIC section for complete invocation template.

```python
# Strategic analysis for PRD
role_prompt = Read("plan-prompts/rules/role-strategic-phase-decomposition.md")
enhancers = [
    Read("plan-prompts/rules/enhancer-investigate-before-answering.md"),
    Read("plan-prompts/rules/enhancer-structured-research.md")
]
combined_enhancers = "\n\n".join(enhancers)

Task(
    subagent_type="design",  # STRATEGIC type → design agent (PHASE decomposition done by wm)
    description="Decompose PRD into PHASEs",  # Required: 3-5 word description
    prompt=f"""
## Planning Goal
Decompose PRD requirements into independently deployable PHASE units

## Input Context
- PRD Path: {prd_path}
- Constraints: {constraints}
- Project Type: {project_type}

## Role Prompt
{role_prompt}

## Enhancers
{combined_enhancers}

## Expected Output
- phases[]: id, name, goal, deliverables, acceptance_criteria
- dependency_graph: phase dependencies
- risks[]: description, probability, impact, mitigation

## Planning Depth: Standard
""",
    model="opus",  # Strategic analysis requires strongest model
    run_in_background=True  # Recommended for complex PRDs
)
```

## Output Format

Output: `phases[]`, `dependency_graph`, `risks[]`

> Full example: `_output-formats.md#phase-decomposition`
