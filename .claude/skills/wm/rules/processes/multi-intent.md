# MULTI_INTENT Process

> **Status**: ACTIVE
> **Usage**: Activated 2026-02-06
> **Activation**: Directly detected in wm Step 2 (Type Classification). Independently detects MULTI_INTENT based on request content.

Master template for requests containing multiple intents (e.g., "Fix bug AND add feature").

---

## Plan Template (Copy to Plan Document)

Copy and adapt this block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **MULTI_INTENT** type containing the following intents:

| Intent | Type | Priority | Dependencies |
|--------|------|----------|--------------|
| {description1} | {TYPE1} | 1 | - |
| {description2} | {TYPE2} | 2 | Intent 1 |

### Intent 1: {TYPE1} - {description1}

Execute the {TYPE1} process:

- [ ] 1.1 {step from type's process file}
- [ ] 1.2 {step from type's process file}
- [ ] ...

### Intent 2: {TYPE2} - {description2}

Execute the {TYPE2} process:

- [ ] 2.1 {step from type's process file}
- [ ] 2.2 {step from type's process file}
- [ ] ...

### Combined Verification

After all intents complete:

- [ ] Final integration test across all changes
- [ ] Verify no regressions between intents
- [ ] Cleanup (invoke plan-cleanup skill)

## Agent Execution Log

### Intent 1: {TYPE1}
| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| {agents from type's process} | - | pending | - | {purpose} |

### Intent 2: {TYPE2}
| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| {agents from type's process} | - | pending | - | {purpose} |
```

---

## When to Use

Use this process when:
- Request contains multiple distinct intents (detected via "AND", "also", "plus", etc.)
- Each intent maps to a different process type
- Intents have execution order dependencies

---

## Multi-Intent Detection

### Intent Markers
- Explicit: "AND", "also", "plus", "as well as", "in addition to"
- Implicit: Comma-separated tasks, numbered lists in request
- Korean: "geurigo" (and), "ttohan" (also), "chugaro" (additionally), "~do" (too)

### Classification Output

```python
classification = {
    "is_multi_intent": True,
    "intents": [
        {"type": "BUG_FIX", "description": "Fix login error", "priority": 1},
        {"type": "NEW_DEVELOPMENT", "description": "Add logout feature", "priority": 2}
    ],
    "execution_order": ["BUG_FIX", "NEW_DEVELOPMENT"],
    "dependencies": {
        "NEW_DEVELOPMENT": ["BUG_FIX"]  # Must complete bug fix first
    }
}
```

---

## Template Composition Rules

### Step 1: Identify Each Intent's Process

Read the corresponding process file for each intent:
- NEW_DEVELOPMENT / MODIFICATION → `development-process.md`
- BUG_FIX (Complex) → `bug-fix-complex.md`
- BUG_FIX (Simple) → `bug-fix-simple.md`
- INQUIRY → `inquiry.md`
- REPORT → `report.md`
- CLEANUP → `cleanup.md`

### Step 2: Determine Execution Order

Priority rules:
1. **BUG_FIX** before **NEW_DEVELOPMENT** (fix before build)
2. **INQUIRY/REPORT** before code changes (understand before modify)
3. **MODIFICATION** can parallel with unrelated intents
4. **CLEANUP** typically last

### Step 3: Number Steps by Intent

Use `{intent_number}.{step_number}` format:
- Intent 1 steps: 1.1, 1.2, 1.3...
- Intent 2 steps: 2.1, 2.2, 2.3...

### Step 4: Add Combined Verification

Always include a final "Combined Verification" section that:
- Runs integration tests across all changes
- Verifies no regressions between intents
- Validates the combined result meets all requirements

---

## Worktree Strategy (Optional)

> Strategy for when worktree usage has been decided. Skip this section if not using worktrees.

### Shared Worktree (Recommended for Related Intents)

When intents are related (e.g., fix auth bug + add auth feature):
- Use single worktree for all intents
- Simpler merge, unified history

```python
Skill(skill="worktree-manager", args=f"create {plan_name}")
# All intents execute in same worktree
```

### Separate Worktrees (For Independent Intents)

When intents are independent:
- Consider separate worktrees
- Parallel execution possible
- More complex merge

```python
Skill(skill="worktree-manager", args=f"create {plan_name}-intent1")
Skill(skill="worktree-manager", args=f"create {plan_name}-intent2")
# Merge sequentially at end
```

---

## Notes

1. **Sequential by default**: Execute intents in priority order unless explicitly parallel
2. **Shared context**: Each intent's agents receive context from previous intents
3. **Fail-fast**: If a high-priority intent fails, pause before starting dependent intents
4. **Combined QA**: Final verification tests all changes together

---

## Intent Abandonment (Task Deletion)

When the user cancels some intents within a MULTI_INTENT, delete the Tasks belonging to that intent.

### Detection

- User explicitly requests intent cancellation (e.g., "skip the feature addition")
- Preceding intent failure makes subsequent intents meaningless (after user confirmation)

### Deletion Pattern

```python
# Execute intent cancellation after user confirmation
abandoned_intent = "NEW_DEVELOPMENT"  # Cancelled intent

all_tasks = TaskList()
for task in all_tasks:
    if (task.metadata.get("feature") == feature_name and
        task.metadata.get("intent") == abandoned_intent):
        current = TaskGet(taskId=task.id)     # Staleness prevention
        TaskUpdate(taskId=task.id, status="deleted")

# Mark the intent checkbox as cancelled in plan document
Edit(
    file_path=plan_path,
    old_string=f"### Intent N: {abandoned_intent}",
    new_string=f"### Intent N: {abandoned_intent} (ABANDONED)"
)
```

### Precautions

- **User confirmation required**: Must confirm via AskUserQuestion before cancelling an intent
- **metadata.intent needed**: planner-task must include `intent` key in metadata when creating Tasks
- **Dependency check**: If the cancelled intent is a prerequisite for other intents, review subsequent intents as well

> **Reference**: [Task Deletion Guide](../components/task-deletion-guide.md)

---

## Shared Rules

> See [process-base.md](process-base.md) for Agent Execution Guidelines, Agent Invocation Rules, and Plan Cleanup.
> **Note**: For MULTI_INTENT, checkpoint uses v4.0 multi-checkpoint structure.
> **Review Gate**: 각 intent의 Review Gate는 review-orchestrator 단일 호출로 위임됨 (navigator recommendation 반영).
