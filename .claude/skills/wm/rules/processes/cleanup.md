# CLEANUP Process

Process to follow for file cleanup/deletion.

---

## Plan Template (Copy to Plan Document)

Copy this entire block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **CLEANUP** type.

Execute directly in Main context:

- [ ] 1. Confirm deletion targets
- [ ] 2. Execute file deletion/move with Bash
- [ ] 3. Confirm results with git status
- [ ] 4. Cleanup (invoke plan-cleanup skill)

**Note**: Only perform file deletion/move without code logic changes.
If code modification is included, classify as MODIFICATION.

### Verification Checklist (CLEANUP)

File operations only - no code changes:

- [ ] **Build success**: No build errors after cleanup
- [ ] **Tests pass**: Existing tests still pass
- [ ] **Git status clean**: Changes are as expected
- [ ] **No broken references**: Deleted files not referenced elsewhere

---

### ⚠️ CLEANUP Exception Rules (IMPORTANT)

> **CLEANUP is the ONLY process where Main Context executes directly.**
> All other processes (NEW_DEVELOPMENT, MODIFICATION, BUG_FIX, etc.) MUST use Agents.

**When to reclassify to MODIFICATION (requires Agents):**
- File deletion + import fixes = **MODIFICATION**
- File move + code updates = **MODIFICATION**
- Any logic changes = **MODIFICATION**

### Execution Pattern (Main Context Direct)

```python
# CLEANUP ONLY: Main context executes directly (NO agents)

# Step 1: Confirm deletion targets
Read("path/to/file")  # Or confirm with Explore

# Step 2: Delete/move files
Bash("rm path/to/unused-file.ts")
Bash("mv old/path new/path")

# Step 3: Confirm results
Bash("git status")

# Step 4: Cleanup
Skill(skill="plan-cleanup", args=f"{plan_name}")
```
```

---

## Characteristics

- **Execute directly in Main context**: Don't use Agents
- **Use Bash commands**: rm, mv, git, etc.
- **No code logic changes**: Only file deletion/move

---

## CLEANUP vs MODIFICATION Distinction

| Task | Type |
|------|------|
| Delete unused files | CLEANUP |
| Move file location (no code changes) | CLEANUP |
| Delete file + fix imports | MODIFICATION |
| Includes code refactoring | MODIFICATION |

---

## Execution Pattern

```python
# 1. Confirm deletion targets
Read("path/to/file")  # Or confirm with Explore

# 2. Delete/move files
Bash("rm path/to/unused-file.ts")
Bash("mv old/path new/path")

# 3. Confirm results
Bash("git status")
```

---

## Safe Deletion Pattern

```bash
# Confirm before deletion
ls -la path/to/target

# Execute deletion
rm path/to/target

# Confirm results
git status
```

---

## Notes

1. **No code modification allowed**: Reclassify as MODIFICATION if code changes needed
2. **Confirm before deletion**: Verify deletion targets are correct
3. **git status required**: Confirm changes
4. **Check references**: Verify files to delete are not referenced elsewhere

---

## Task Cleanup (Post-Workflow)

After any workflow completes, delete remaining feature tasks to keep TaskList clean:

```python
# After workflow completion, delete all Tasks for this feature
all_tasks = TaskList()
for task in all_tasks:
    if task.metadata.get("feature") == feature_name:
        current = TaskGet(taskId=task.id)     # Staleness prevention
        TaskUpdate(taskId=task.id, status="deleted")
```

> **Reference**: [Task Deletion Guide](../components/task-deletion-guide.md)

---

## Shared Rules

> See [process-base.md](process-base.md) for Plan Cleanup.
