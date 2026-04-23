# Task Integration

Task Management, Task Tool 통합 참조, planner 연동.

---

## Task Management

### Initial Task Creation

At the start of `/solve`, create tracking tasks for the workflow:

```python
# Create problem solving tasks
problem_id = generate_problem_id()  # PROB-{timestamp}

TaskCreate(
    subject=f"[SOLVE] Phase 1: Problem Definition - {problem_id}",
    description="Define and document the problem with symptoms, reproduction steps, and impact scope.",
    activeForm="Defining problem...",
    metadata={"skill": "solve", "problem_id": problem_id, "phase": "1"}
)

TaskCreate(
    subject=f"[SOLVE] Phase 2: Information Gathering - {problem_id}",
    description="Collect git history, related files, and error logs.",
    activeForm="Gathering information...",
    metadata={"skill": "solve", "problem_id": problem_id, "phase": "2"}
)

TaskCreate(
    subject=f"[SOLVE] Phase 2.5: Decision Gate - {problem_id}",
    description="Analyze complexity and get user decision on approach.",
    activeForm="Analyzing complexity...",
    metadata={"skill": "solve", "problem_id": problem_id, "phase": "2.5"}
)
```

### Task Status Updates (CRITICAL: Staleness Prevention)

**RULE**: Always call `TaskGet` before `TaskUpdate` to read latest state.

```python
# CORRECT Pattern
task_id = get_current_task_id()
current = TaskGet(taskId=task_id)           # Read latest state
if current.status == "pending":
    TaskUpdate(taskId=task_id, status="in_progress")

# ... do phase work ...

current = TaskGet(taskId=task_id)           # Read latest state again
TaskUpdate(taskId=task_id, status="completed")

# WRONG Pattern (Never do this)
TaskUpdate(taskId=task_id, status="completed")  # Stale!
```

### Dynamic Task Creation Based on User Choice

After Phase 2.5, create additional tasks based on user selection:

```python
user_choice = get_user_selection()

if user_choice in ["Standard", "Full Pipeline", "Analysis Only"]:
    TaskCreate(
        subject=f"[SOLVE] Phase 3: Root Cause Analysis - {problem_id}",
        description="Invoke root-cause-finder agent for 5 Whys analysis.",
        activeForm="Analyzing root cause...",
        metadata={"skill": "solve", "problem_id": problem_id, "phase": "3"}
    )
    TaskCreate(
        subject=f"[SOLVE] Phase 4: Hypothesis Verification - {problem_id}",
        description="Form and verify hypotheses based on root cause.",
        activeForm="Verifying hypotheses...",
        metadata={"skill": "solve", "problem_id": problem_id, "phase": "4"}
    )

if user_choice in ["Standard", "Full Pipeline"]:
    TaskCreate(
        subject=f"[SOLVE] Phase 5: Resolution - {problem_id}",
        description="Invoke bug-fixer agent for TDD-based fix.",
        activeForm="Implementing fix...",
        metadata={"skill": "solve", "problem_id": problem_id, "phase": "5"}
    )

if user_choice in ["Quick Fix + QA", "Full Pipeline"]:
    TaskCreate(
        subject=f"[SOLVE] QA Verification - {problem_id}",
        description="Invoke qa agent for comprehensive validation.",
        activeForm="Running QA validation...",
        metadata={"skill": "solve", "problem_id": problem_id, "phase": "qa"}
    )

# Phase 6 is always created
TaskCreate(
    subject=f"[SOLVE] Phase 6: Documentation - {problem_id}",
    description="Generate resolution report and update knowledge base.",
    activeForm="Documenting resolution...",
    metadata={"skill": "solve", "problem_id": problem_id, "phase": "6"}
)
```

### Task Cleanup on Completion

```python
# After successful completion, delete all solve tasks for this problem
all_tasks = TaskList()
solve_tasks = [t for t in all_tasks if t.metadata.get("problem_id") == problem_id]

for task in solve_tasks:
    current = TaskGet(taskId=task.id)       # Staleness prevention
    TaskUpdate(taskId=task.id, status="deleted")
```

---

## Task Tool Integration Reference

### Task Status Flow

```
  Phase      Status Transition
  ---------  ----------------------------------------
  Phase 1    pending -> in_progress -> completed
  Phase 2    pending -> in_progress -> completed
  Phase 2.5  pending -> in_progress -> completed
  Phase 3    pending -> in_progress -> completed (if selected)
  Phase 4    pending -> in_progress -> completed (if selected)
  Phase 5    pending -> in_progress -> completed (if selected)
  QA         pending -> in_progress -> completed (if selected)
  Phase 6    pending -> in_progress -> completed -> deleted (cleanup)
  ---------  ----------------------------------------
```

### Staleness Prevention Rule (CRITICAL)

Every `TaskUpdate` call **MUST** be preceded by a `TaskGet` call:

```python
# CORRECT
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="in_progress")

# WRONG
TaskUpdate(taskId=task_id, status="in_progress")
```

### Metadata Schema

```python
metadata = {
    "skill": "solve",           # Always "solve" for this skill
    "problem_id": "PROB-xxx",   # Unique problem identifier
    "phase": "1|2|2.5|3|4|5|6|qa"  # Phase identifier
}
```

---

## Integration with planner

### Called for Simple Bugs

From planner Step 2-B-Simple:

```python
Skill(skill="solve", args=bug_description)
```

### Called for Error Recovery

From planner Error Recovery flow:

```python
Skill(skill="solve", args="--hypothesis")
```
