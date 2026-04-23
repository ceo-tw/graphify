# PRD → TASK Conversion Rules

> **Source**: Migrated from `planning-guide-for-task/references/prd-to-task-mapping.md`
> **Purpose**: Reference when converting PRD document sections to TASKs
> **Used by**: planner-task agent

---

## Field Mapping Table

| PRD Element | TASK Field | Conversion Method | Example |
|-------------|------------|-------------------|---------|
| 🔴 RED: Test X.Y | `task_id`, `tdd_stage` | `TASK-{PHASE:02d}{SEQ:02d}`, "RED" | Test 1.1 → TASK-0101, RED |
| 🟢 GREEN: Task X.Z | `task_id`, `tdd_stage` | `TASK-{PHASE:02d}{SEQ:02d}`, "GREEN" | Task 1.2 → TASK-0102, GREEN |
| 🔵 REFACTOR: Task X.W | `task_id`, `tdd_stage` | `TASK-{PHASE:02d}{SEQ:02d}`, "REFACTOR" | Task 1.3 → TASK-0103, REFACTOR |
| File: `path` | `files.create` / `files.modify` | Distinguish by file existence | New file → create |
| Scenarios | `acceptance_criteria` | Convert to list format | - Happy path → AC 1 |
| Expected | `verification_criteria` | Specify expected result | "Tests FAIL" → Confirm test failure |
| Quality Gate | `completion_checklist` | Add common items per PHASE | Include TDD checklist |
| Goal (Task description) | `description` | Use PRD text as-is | "Tab expansion" → description |

---

## TASK ID Generation Rules

**Format**: `TASK-{PHASE}{SEQUENCE}`

- **PHASE**: 2-digit number (01, 02, ...)
- **SEQUENCE**: 2-digit number (01, 02, ...)

**Examples**:
```
First Task of PHASE 1 → TASK-0101
Second Task of PHASE 1 → TASK-0102
First Task of PHASE 2 → TASK-0201
```

**Independence Determination Rules**:

| TDD Stage | Independent | Depends On |
|-----------|-------------|------------|
| 🔴 RED | ✅ Generally independent | Related Task from previous PHASE |
| 🟢 GREEN | ❌ Depends on RED Task | RED Task for same feature |
| 🔵 REFACTOR | ❌ Depends on GREEN Task | GREEN Task for same feature |

---

## TDD Stage Mapping

| PRD Marker | TASK `tdd_stage` | Description | Verification Criteria |
|------------|------------------|-------------|----------------------|
| 🔴 RED | `"RED"` | Test writing stage | Test file exists, test fails |
| 🟢 GREEN | `"GREEN"` | Implementation stage | Test passes, minimal implementation |
| 🔵 REFACTOR | `"REFACTOR"` | Improvement stage | Tests maintained, code quality improved |

---

## PRD Scenarios → Acceptance Criteria Conversion

**PRD Input**:
```markdown
- Scenarios:
  - Verify terminals tab rendering
  - Verify requests tab rendering
  - Tab switching behavior
```

**TASK Output**:
```markdown
**Acceptance Criteria**:
- [ ] Terminals tab renders correctly
- [ ] Requests tab renders correctly
- [ ] Content changes correctly when switching tabs
```

---

## PRD Files → TASK Files Conversion

**PRD Input**:
```markdown
- File: `dashboard/src/components/monitoring/monitoring-page-client.tsx`
- File: `dashboard/src/components/monitoring/__tests__/monitoring-page-client.test.tsx`
```

**TASK Output**:
```markdown
**Files**:
- Modify: `dashboard/src/components/monitoring/monitoring-page-client.tsx`
- Create: `dashboard/src/components/monitoring/__tests__/monitoring-page-client.test.tsx`
```

**Judgment Criteria**:
- File already exists → `Modify`
- File newly created → `Create`
- New test file in `__tests__/` path → `Create`

---

## Quality Gate → Completion Checklist Conversion

PRD Quality Gate applies to entire PHASE, so each TASK's `completion_checklist` includes only items relevant to that Task.

### PHASE Quality Gate (PRD Original)
```markdown
**TDD Compliance**:
- [ ] Tests written FIRST and initially failed
- [ ] Production code written to make tests pass
- [ ] Code improved while tests still pass

**Build & Tests**:
- [ ] Project builds without errors
- [ ] All tests pass
```

### RED Task Completion Checklist
```markdown
- [ ] Test file created
- [ ] Test fails as expected when run
- [ ] No implementation code yet
```

### GREEN Task Completion Checklist
```markdown
- [ ] Implementation complete
- [ ] Corresponding RED test passes
- [ ] Build succeeds
```

### REFACTOR Task Completion Checklist
```markdown
- [ ] Code cleanup complete
- [ ] All tests still pass
- [ ] Lint/type check passes
```
