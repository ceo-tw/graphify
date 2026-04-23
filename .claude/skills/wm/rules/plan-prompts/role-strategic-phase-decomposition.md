---
title: Phase Decomposition
role: strategic
type: role
priority: HIGH
---

# Phase Decomposition

<role>Strategic Planner</role>
<responsibility>Decompose PRD requirements into independently deployable PHASE units</responsibility>

## Instructions

<instructions>
Follow these steps when decomposing PRD into PHASEs:

1. **Understand Full Scope of Requirements**
   - Identify all functional requirements in PRD
   - Confirm non-functional requirements (performance, security)
   - Understand constraints and assumptions

2. **Group Functions**
   - Group related features logically
   - Identify domain boundaries
   - Classify core features vs. supplementary features

3. **Determine PHASE Boundaries**
   - Verify independent deployability
   - Confirm each PHASE delivers value
   - Review if PHASE size is completable within 1-2 weeks

4. **Define Goals per PHASE**
   - Set clear completion criteria
   - Define measurable deliverables
   - Establish test strategy

5. **Determine Sequence**
   - Consider technical dependencies
   - Reflect business priorities
   - Verify high-risk items first
</instructions>

## Phase Criteria

<phase_criteria>
Characteristics of a good PHASE:

**Independence**
- Deployable without completing other PHASEs
- Self-testable
- Clear interface boundaries

**Value Delivery**
- Provides real value to users or system
- Delivers meaningful functionality standalone
- Enables feedback collection

**Right-sizing**
- Completable within 1-2 weeks
- Decomposable into 3-7 Tasks
- Understandable scope for one developer
</phase_criteria>

## Output Format

<output_format>
Output fields: `phases[]` (id, name, goal, deliverables, acceptance_criteria, test_strategy, estimated_complexity, dependencies), `summary`

> Full JSON example: `_output-formats.md#phase-decomposition`
</output_format>

## Constraints

<constraints>
- Each PHASE must include at least one testable deliverable
- Recommended 3-7 PHASEs (too few = scope overload, too many = management difficulty)
- No circular dependencies
- No "miscellaneous" or "remaining" PHASEs - clear goals required
</constraints>

## Anti-patterns

**Patterns to Avoid**:

```
❌ Too Large PHASE
   - "Implement entire backend" → Decompose into smaller units

❌ Excessive Dependencies
   - All PHASEs depend on previous → Identify parallelizable parts

❌ Unclear Completion Criteria
   - "Improve features" → Provide specific measurable criteria

❌ PHASE Without Tests
   - "Refactoring only" → Include verification method
```

## Examples

### Good Decomposition

```
PRD: Implement User Authentication System

PHASE-1: Authentication Infrastructure Foundation
  - Goal: Build JWT-based authentication flow
  - Deliverables: Login/Logout API, Token management
  - Tests: Authentication flow E2E tests

PHASE-2: User Management
  - Goal: Registration and profile management
  - Deliverables: Registration API, Profile CRUD
  - Tests: User lifecycle tests

PHASE-3: Authorization System
  - Goal: Role-based access control
  - Deliverables: RBAC implementation, Middleware
  - Tests: Authorization verification tests
```

Reference: [PRD Template](../../planner/references/prd-template.md)
