# PRD Template

> **Source**: Migrated from `planning-guide-for-phase/references/prd-template.md`
> **Purpose**: Template for PLAN documents.
> **Used by**: wm (Plan Writing)

---

Use this template for PLAN documents.

```markdown
# PLAN: {Feature Name}

> **Version**: 0.1.0
> **Status**: Draft | In Progress | Complete
> **Created**: {date}
> **Author**: Claude (with User collaboration)

---

## Overview

### Background

Describe why this feature is needed:
- Current problem or limitation
- User pain points
- Business value

### Objectives

| Objective | Success Metric |
|-----------|----------------|
| Primary goal | Measurable outcome |
| Secondary goal | Measurable outcome |

### Success Criteria

- [ ] Criterion 1: {specific, measurable}
- [ ] Criterion 2: {specific, measurable}
- [ ] Criterion 3: {specific, measurable}

### Guidelines

| Guideline | Rationale |
|-----------|-----------|
| TDD required | Quality assurance |
| Clean Architecture | Maintainability |
| ≥80% test coverage | Business logic reliability |

---

## Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| {Decision 1} | {Why this approach} | {What we're giving up} |
| {Decision 2} | {Why this approach} | {What we're giving up} |

---

## Test Strategy

### TDD Principle
Write tests FIRST, then implement to make them pass.

### Test Pyramid

| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | ≥80% | Business logic, models, core algorithms |
| **Integration Tests** | Critical paths | Component interactions, data flow |
| **E2E Tests** | Key user flows | Full system behavior validation |

### Test Naming Convention
```
// describe/group: Feature or component name
//   test/it: Specific behavior being tested
//     Arrange → Act → Assert pattern
```

---

## PHASE Overview

| # | PHASE | Goal | Est. Time | Dependencies |
|---|-------|------|-----------|--------------|
| 1 | {Name} | {Goal} | {hours}h | None |
| 2 | {Name} | {Goal} | {hours}h | PHASE 1 |
| 3 | {Name} | {Goal} | {hours}h | PHASE 2 |

---

## PHASE Details

### PHASE 1: {Name}

**Goal**: {Clear deliverable description}
**Estimated Time**: {hours}h
**Status**: ⏳ Pending | 🔄 In Progress | ✅ Complete

#### Tasks (TDD Workflow)

**🔴 RED: Write Failing Tests First**
- [ ] **Test 1.1**: Write unit tests for {functionality}
  - File: `test/unit/{feature}/{component}_test.*`
  - Expected: Tests FAIL (feature doesn't exist yet)
  - Scenarios:
    - Happy path
    - Edge cases
    - Error conditions

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 1.2**: Implement {component}
  - File: `src/{layer}/{component}.*`
  - Goal: Make Test 1.1 pass with minimal code

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 1.3**: Refactor for code quality
  - [ ] Remove duplication (DRY)
  - [ ] Improve naming
  - [ ] Add documentation

#### Quality Gate ✋

> For detailed quality checklist, see [Quality Gate Template](template-quality-gate.md)

**⚠️ STOP: Do NOT proceed to PHASE 2 until ALL checks pass**

**TDD Compliance**:
- [ ] Tests written FIRST and initially failed
- [ ] Production code written to make tests pass
- [ ] Code improved while tests still pass
- [ ] Coverage meets requirements

**Build & Tests**:
- [ ] Project builds without errors
- [ ] All tests pass (no skipped tests)
- [ ] No flaky tests

**Code Quality**:
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Formatting consistent

**Functionality**:
- [ ] Feature works as expected
- [ ] Edge cases handled
- [ ] No regressions

#### Rollback Strategy

**Code Changes to Revert**:
- File: {path} - Remove/modify {description}

**Verification**:
- Run: {test command}
- Expected: {outcome}

---

### PHASE 2: {Name}

**Goal**: {Clear deliverable description}
**Estimated Time**: {hours}h
**Status**: ⏳ Pending | 🔄 In Progress | ✅ Complete

#### Tasks (TDD Workflow)

**🔴 RED: Write Failing Tests First**
- [ ] **Test 2.1**: Write tests for {functionality}

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 2.2**: Implement {component}

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 2.3**: Refactor for quality

#### Quality Gate ✋

{Same checklist as PHASE 1}

#### Rollback Strategy

{Same structure as PHASE 1}

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| {Risk 1} | Low/Med/High | Low/Med/High | {Specific steps} |
| {Risk 2} | Low/Med/High | Low/Med/High | {Specific steps} |

---

## Progress Tracking

### Completion Status

- **PHASE 1**: ⏳ 0%
- **PHASE 2**: ⏳ 0%
- **PHASE 3**: ⏳ 0%

**Overall Progress**: 0%

### Time Tracking

| PHASE | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| PHASE 1 | {hours}h | - | - |
| PHASE 2 | {hours}h | - | - |
| **Total** | {hours}h | - | - |

---

## Notes & Learnings

### Implementation Notes
- {Add insights during implementation}

### Blockers Encountered
- **Blocker 1**: {Description} → {Resolution}

---

## Final Checklist

**Before marking COMPLETE**:
- [ ] All PHASEs completed with quality gates passed
- [ ] Full integration testing performed
- [ ] Documentation updated
- [ ] All stakeholders notified
```
