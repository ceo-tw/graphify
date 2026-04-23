# TASKS Template

> **Source**: Migrated from `planning-guide-for-task/references/tasks-template.md`
> **Purpose**: Template for TASKS documents.
> **Used by**: planner-task agent

---

Use this template for TASKS documents:

```markdown
# TASKS: PHASE {N} - {Name}

> **PHASE Goal**: {Goal from PLAN}
> **Total Tasks**: {count}
> **Estimated Time**: {total hours}h

---

## Task Overview

| ID | Task | Layer | TDD | Est. | Independent |
|----|------|-------|-----|------|-------------|
| TASK-0101 | {Name} | Domain | RED | 30m | ✅ |
| TASK-0102 | {Name} | Domain | GREEN | 30m | ❌ (needs 0101) |

---

## Task Details

### TASK-0101: {Name}

**Layer**: Domain
**TDD Phase**: RED
**Estimated Time**: 30 min
**Independent**: ✅

**Description**:
{What this task accomplishes}

**Files**:
- Create: `src/domain/entities/User.ts`
- Create: `tests/domain/entities/User.test.ts`

**Acceptance Criteria**:
- [ ] Test file exists
- [ ] Test fails with expected error
- [ ] No implementation code

**Completion Checklist**:
- [ ] Files created
- [ ] Test runs and fails
- [ ] Committed

---

### TASK-0102: {Name}

**Layer**: Domain
**TDD Phase**: GREEN
**Estimated Time**: 30 min
**Independent**: ❌ (depends on TASK-0101)

**Description**:
{What this task accomplishes}

**Files**:
- Modify: `src/domain/entities/User.ts`

**Acceptance Criteria**:
- [ ] Implementation complete
- [ ] TASK-001 test passes
- [ ] Minimal code only

**Completion Checklist**:
- [ ] Implementation added
- [ ] Test passes
- [ ] Committed
```
