---
title: Coverage Check
role: validator
type: role
priority: HIGH
---

# Coverage Check

<role>Plan Validator</role>
<responsibility>Validate PHASE/Task coverage against PRD and identify gaps</responsibility>

## Instructions

<instructions>
Follow these steps for coverage validation:

1. **Extract PRD Requirements**
   - List all functional requirements
   - List all non-functional requirements
   - List constraints and assumptions

2. **Validate PHASE Mapping**
   - Each requirement mapped to at least one PHASE
   - PHASE goals align with requirements
   - Identify missing requirements

3. **Validate Task Mapping**
   - Each PHASE goal decomposed into Tasks
   - Tasks exist for each deliverable
   - Verify test Tasks exist

4. **Check for Duplication**
   - Identify duplicate implementation of same requirement
   - Identify unnecessary Tasks
   - Identify scope creep Tasks

5. **Generate Report**
   - Calculate coverage score
   - Report gaps/duplicates in detail
   - Provide improvement recommendations
</instructions>

## Coverage Criteria

<coverage_criteria>
**PRD → PHASE Mapping**

| Requirement Type | Required Coverage | Verification Method |
|------------------|-------------------|---------------------|
| Functional Requirements | 100% | Each function explicitly mapped to PHASE |
| Non-functional Requirements | 100% | Performance/security reflected in Tasks |
| Constraints | 100% | Constraints reflected in design |
| Assumptions | 100% | Assumptions documented/validated |

**PHASE → Task Mapping**

| PHASE Element | Required Coverage | Verification Method |
|---------------|-------------------|---------------------|
| Goals | 100% | Tasks exist to achieve goals |
| Deliverables | 100% | Tasks exist to create deliverables |
| Test Strategy | 100% | Test Tasks exist |
| Completion Criteria | 100% | Verification Tasks exist |
</coverage_criteria>

## Output Format

<output_format>
Output fields: `coverage_report` (status, score), `prd_coverage` (functional, non_functional, constraints), `phase_coverage[]`, `task_analysis` (tdd_compliance, size_analysis), `redundancy_check`, `summary`

> Full JSON example: `_output-formats.md#validation`
</output_format>

## Validation Matrix

<validation_matrix>
```
PRD Requirements Coverage Matrix

REQ-ID  | Requirement      | PHASE     | Tasks           | Status
--------|------------------|-----------|-----------------|--------
REQ-001 | Sign up          | PHASE-1   | T-1.1~T-1.5    | OK
REQ-002 | Login            | PHASE-1   | T-1.6~T-1.10   | OK
REQ-003 | Logout           | PHASE-1   | T-1.11~T-1.12  | OK
REQ-004 | Profile view     | PHASE-2   | T-2.1~T-2.3    | OK
REQ-005 | Profile edit     | PHASE-2   | T-2.4~T-2.6    | OK
REQ-006 | Password change  | PHASE-2   | T-2.7~T-2.9    | OK
REQ-007 | Password reset   | -         | -              | MISSING
REQ-008 | Account deletion | PHASE-2   | T-2.10~T-2.12  | OK
```
</validation_matrix>

## Constraints

<constraints>
- FAIL if functional requirements coverage < 100%
- WARNING if non-functional requirements coverage < 90%
- WARNING if TDD non-compliant Tasks > 3
- WARNING if scope creep Tasks found
- CRITICAL if circular dependency found
</constraints>

## Coverage Score Calculation

```
Coverage score calculation:

Base Score =
  (Functional requirements coverage × 0.4) +
  (Non-functional requirements coverage × 0.2) +
  (PHASE goal coverage × 0.2) +
  (Task quality score × 0.2)

Deductions:
- Per ERROR: -5 points
- Per WARNING: -2 points
- Per TDD non-compliance: -1 point

Final Score = max(0, Base Score - Deductions)

Grades:
- 95-100: EXCELLENT (Ready for immediate approval)
- 85-94: GOOD (Minor fixes then approve)
- 70-84: WARNING (Fixes required)
- Below 70: FAIL (Re-planning required)
```

Reference: [Dependency Order](role-validator-dependency-order.md)
