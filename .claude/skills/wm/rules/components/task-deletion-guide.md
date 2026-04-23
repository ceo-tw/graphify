# Task Deletion Guide

Patterns and decision criteria for using `TaskUpdate(status="deleted")` (available since Claude Code 2.1.20).

---

## 1. When to Delete vs Complete

| Situation | Action | Reason |
|-----------|--------|--------|
| Task was created incorrectly | **Delete** | No valid history to preserve |
| User changed intent / abandoned | **Delete** | Intent itself is invalid |
| Workflow completed, cleanup needed | **Delete** | Archive cleanup |
| Task failed but may retry | Keep as `in_progress` | Preserve attempt record |
| Task became unnecessary but was valid | `completed` | Document the decision |

---

## 2. Staleness Rule (CRITICAL)

**Every `TaskUpdate` call MUST be preceded by `TaskGet`.**

```python
# CORRECT
current = TaskGet(taskId=task.id)
TaskUpdate(taskId=task.id, status="deleted")

# WRONG - never do this
TaskUpdate(taskId=task.id, status="deleted")  # Stale!
```

---

## 3. Deletion Patterns

### 3.1 Single Task Deletion

```python
current = TaskGet(taskId=task_id)
if current.status in ["pending", "in_progress"]:
    TaskUpdate(taskId=task_id, status="deleted")
```

### 3.2 Feature-Scoped Bulk Deletion

Delete all tasks belonging to a specific feature:

```python
all_tasks = TaskList()
for task in all_tasks:
    if task.metadata.get("feature") == feature_name:
        current = TaskGet(taskId=task.id)
        if current.status != "completed":
            TaskUpdate(taskId=task.id, status="deleted")
```

### 3.3 Phase-Scoped Deletion (partial_fix)

Delete tasks from specific phases before regeneration:

```python
all_tasks = TaskList()
for task in all_tasks:
    if (task.metadata.get("feature") == feature_name and
        task.metadata.get("phase") in affected_phases):
        current = TaskGet(taskId=task.id)
        TaskUpdate(taskId=task.id, status="deleted")
# Then re-invoke planner-task for affected phases
```

### 3.4 Intent-Scoped Deletion (MULTI_INTENT)

Delete tasks belonging to an abandoned intent:

```python
all_tasks = TaskList()
for task in all_tasks:
    if (task.metadata.get("feature") == feature_name and
        task.metadata.get("intent") == abandoned_intent):
        current = TaskGet(taskId=task.id)
        TaskUpdate(taskId=task.id, status="deleted")
```

---

## 4. Safety Rules

1. **Always filter by feature + additional condition**: Never delete by status alone
2. **Log before deleting**: Record task subject and reason for deletion
3. **Check blockedBy references**: Deleting a task that blocks others may leave orphaned dependencies
4. **Never delete completed tasks** unless explicitly cleaning up after workflow completion

---

## 5. Logging Format

When deleting tasks, log them for progress tracking:

```markdown
### Deleted Tasks
| Task ID | Subject | Reason | Timestamp |
|---------|---------|--------|-----------|
| task-3 | [PHASE 2] API endpoint | Phase regenerated (partial_fix) | 2026-01-28T14:30 |
| task-7 | [PHASE 3] UI component | Intent abandoned by user | 2026-01-28T14:35 |
```

---

## 6. Integration Points

| Component | How Deletion is Used |
|-----------|---------------------|
| `SKILL.md` | partial_fix: delete + regenerate affected phase tasks |
| `cleanup.md` | Post-workflow: delete all feature tasks |
| `multi-intent.md` | Intent abandonment: delete intent-scoped tasks |
| `progress-tracking.md` | Deletion logging format |
