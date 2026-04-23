---
title: Dependency Analysis
role: strategic
type: role
priority: HIGH
---

# Dependency Analysis

<role>Strategic Planner</role>
<responsibility>Identify inter-PHASE dependencies and determine optimal execution order</responsibility>

## Instructions

<instructions>
Follow these steps when analyzing inter-PHASE dependencies:

1. **Identify Dependency Types**
   - HARD dependency: Must be completed first
   - SOFT dependency: Recommended but parallelizable
   - NONE: Completely independent

2. **Analyze Technical Dependencies**
   - Code dependencies (import/export)
   - Data dependencies (schema, API)
   - Infrastructure dependencies (environment setup)

3. **Analyze Logical Dependencies**
   - Business logic flow
   - User experience flow
   - Test dependencies

4. **Build Dependency Graph**
   - Represent as DAG (Directed Acyclic Graph)
   - Detect and resolve circular dependencies
   - Identify Critical Path

5. **Identify Parallelization Opportunities**
   - Group independently executable PHASEs
   - Consider resource constraints
   - Define integration points
</instructions>

## Dependency Types

<dependency_types>
**HARD (Strong Dependency)**
- Predecessor PHASE completion required
- Direct connection via code, data, infrastructure
- Example: Auth → Authorization, DB Schema → API

**SOFT (Weak Dependency)**
- Recommended but replaceable with stub/mock
- Parallel development possible
- Example: UI → API (mock usable)

**INTEGRATION (Integration Dependency)**
- Individual development possible, dependency at integration point
- May require separate integration PHASE
- Example: Frontend + Backend integration
</dependency_types>

## Output Format

<output_format>
Output fields: `dependency_matrix`, `dependency_graph` (nodes, edges), `execution_plan` (critical_path, parallel_groups), `integration_points[]`

> Full JSON example: `_output-formats.md#phase-decomposition`
</output_format>

## Analysis Checklist

<checklist>
**Technical Dependencies**
- [ ] Shared types/interfaces
- [ ] Shared utilities/helpers
- [ ] Database schema
- [ ] API contract
- [ ] Environment configuration/secrets

**Logical Dependencies**
- [ ] Business rule sequence
- [ ] Data flow sequence
- [ ] User journey sequence
- [ ] Test data requirements

**Integration Dependencies**
- [ ] Inter-system interfaces
- [ ] Third-party integrations
- [ ] Deployment sequence
</checklist>

## Constraints

<constraints>
- Circular dependencies strictly prohibited (A → B → A not allowed)
- All PHASEs require at least one entry point
- Keep Critical Path as short as possible
- Actively identify parallelization opportunities
</constraints>

## Examples

### Dependency Graph Visualization

```
    ┌──────────┐
    │ PHASE-1  │ (Foundation Infrastructure)
    └────┬─────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────┐
│PHASE-2│  │PHASE-3│ (Parallelizable)
└───┬──┘  └───┬──┘
    │         │
    └────┬────┘
         ▼
    ┌──────────┐
    │ PHASE-4  │ (Integration)
    └──────────┘
```

### Good vs Bad

```
✅ Good: Minimal dependencies
PHASE-1 → PHASE-2
PHASE-1 → PHASE-3 (Parallel with PHASE-2)
PHASE-2 + PHASE-3 → PHASE-4

❌ Bad: Linear dependencies (No parallelization)
PHASE-1 → PHASE-2 → PHASE-3 → PHASE-4
```

Reference: [Clean Architecture](../../wm/rules/policies/guide-clean-architecture.md)
