---
title: Architect Role Index
role: architect
type: index
version: 1.0.0
---

# Architect Role - Architecture Analysis

> Design system architecture and define component structure

## Role Overview

<role>Software Architect</role>
<primary_agent>design</primary_agent>

**Core Responsibilities**:
- Explore and analyze existing architecture patterns
- Design component structure for new features
- Define inter-layer communication methods
- Analyze trade-offs and provide recommendations

## Available Prompts

| Prompt | File | Priority | Description |
|--------|------|----------|-------------|
| Component Design | `role-architect-component-design.md` | HIGH | Component structure design |
| Data Flow | `role-architect-data-flow.md` | HIGH | Data flow design |
| Integration Points | `role-architect-integration-points.md` | MEDIUM | Integration point definition |

## Quick Reference

> See `_common-criteria.md` → Architect Role Criteria for detailed XML definitions

## Recommended Enhancers

| Enhancer | Purpose | When to Use |
|----------|---------|-------------|
| investigate-before-answering | Code verification required | Always |
| code-exploration | Explore existing patterns | Pattern analysis |
| verbosity-control | Adjust detail level | Complex designs |

## Usage Example

> **Template Reference**: See [plan-types-reference.md](../../wm/rules/components/plan-types/plan-types-reference.md) ARCHITECT section for complete invocation template.

```python
# Architecture design for new feature
role_prompt = Read("plan-prompts/rules/role-architect-component-design.md")
enhancers = [
    Read("plan-prompts/rules/enhancer-investigate-before-answering.md"),
    Read("plan-prompts/rules/enhancer-code-exploration.md")
]
combined_enhancers = "\n\n".join(enhancers)

Task(
    subagent_type="design",  # ARCHITECT type → design agent
    description="Design feature architecture",  # Required: 3-5 word description
    prompt=f"""
## Planning Goal
Design feature component structure and data flow

## Input Context
- Design Target: {design_target}
- Existing Architecture: {existing_patterns}
- Constraints: {constraints}

## Role Prompt
{role_prompt}

## Enhancers
{combined_enhancers}

## Expected Output
- architecture: pattern, layers
- components[]: name, responsibility, interfaces
- data_flow: component interactions
- integration_points[]: external system connections
- trade_offs[]: decision rationale

## Planning Depth: Standard
""",
    model="opus",  # Architecture design requires strongest model
    run_in_background=True  # Recommended for complex designs
)
```

## Output Format

Output: `architecture`, `components[]`, `data_flow`, `integration_points[]`, `trade_offs[]`

> Full example: `_output-formats.md#component-design`

## Layer Conventions

```
┌────────────────────────────────────┐
│          Presentation              │  UI Components, Pages
├────────────────────────────────────┤
│          Application               │  Use Cases, Services
├────────────────────────────────────┤
│            Domain                  │  Entities, Value Objects
├────────────────────────────────────┤
│         Infrastructure             │  DB, External APIs
└────────────────────────────────────┘

Dependency direction: Always inward (Domain depends on nothing)
```
