# Task Tool Planning Guide

This guide provides detailed patterns for using Task tools (TaskCreate, TaskList, TaskUpdate, TaskGet) during planning stages, not just implementation.

---

## 0. Prerequisite: Deferred Tool Loading (CRITICAL)

Task tools (TaskCreate, TaskUpdate, TaskGet, TaskList) are classified as **deferred tools** in the Claude Code platform.
They must be **explicitly loaded** via `ToolSearch` before they can be called.

```python
# FIRST ACTION - Must run before using Task tools
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")
```

> **`allowed-tools` vs `ToolSearch` difference**:
> - Registered in `allowed-tools` = **Auto-approve permissions** (skip user confirmation UI)
> - Loaded via `ToolSearch` = **Actually activate the tool** (make it callable)
> - Both are needed. `allowed-tools` alone does not make tools callable.

**Note**: `Agent` (Agent spawning tool) and `TaskCreate/TaskUpdate/TaskGet/TaskList` (progress tracking tools) are **different tools**.
- `Agent` = Agent tool that creates subagents (always available)
- `TaskCreate/Update/Get/List/Output/Stop` = Tools for tracking work progress (require ToolSearch loading)

---

## 1. Why Task Tools in Planning?

Task tools are not just for tracking implementation work. They enable:

| Benefit | Description |
|---------|-------------|
| **Parallel Planning** | Execute independent planning agents simultaneously |
| **Progress Tracking** | Visual progress for complex planning pipelines |
| **Dependency Management** | Clear dependency chains between planning steps |
| **Resume Capability** | Resume planning after context compression |

---

## 2. Independence Criteria for Planning

Before parallelizing planning work, verify independence:

### Planning Independence Test

Two planning tasks are **INDEPENDENT** when ALL are true:

- [ ] Output of Task A is NOT input for Task B
- [ ] No shared document being modified
- [ ] No shared data sources being analyzed
- [ ] No architectural decisions that affect the other

### Planning Dependency Matrix

| Planning Scenario | Parallel? | Rationale |
|-------------------|-----------|-----------|
| Multiple PHASEs (no dependency) | **YES** | Independent scope decomposition |
| Multi-area design (different domains) | **YES** | No architectural overlap |
| Multiple Explore agents (different targets) | **YES** | Independent information gathering |
| Multiple document creation (different docs) | **YES** | No content dependency |
| `design` → `planner-task` | NO | Task decomposition needs architecture |
| `planner-task` → `dev-executor` | NO | Implementation needs task definitions |

---

## 3. TaskList-Based Planning Pattern

### Pattern: Parallel Planning Agents

```python
# 1. Create planning tasks
TaskCreate(
    subject="Decompose PHASE-1: Auth Module",
    description="Break down auth module into executable tasks",
    activeForm="Decomposing Auth Module",
    metadata={"planning": True, "phase": "PHASE-1"}
)
TaskCreate(
    subject="Decompose PHASE-2: Logging Module",
    description="Break down logging module into executable tasks",
    activeForm="Decomposing Logging Module",
    metadata={"planning": True, "phase": "PHASE-2"}
)

# 2. Get all planning tasks
all_tasks = TaskList()
planning_tasks = [t for t in all_tasks if t.metadata.get("planning")]

# 3. Execute independent tasks in parallel
agents = []
for task in planning_tasks:
    if task.status == "pending" and not task.blockedBy:
        current = TaskGet(taskId=task.id)          # Staleness prevention
        if current.status != "pending":
            continue
        TaskUpdate(taskId=task.id, status="in_progress")
        agent = Agent(
            subagent_type="planner-task",
            prompt=f"Execute planning task: {task.subject}\n{task.description}",
            run_in_background=True
        )
        agents.append((task.id, agent))

# 4. Wait for all and update status
for task_id, agent in agents:
    TaskOutput(task_id=agent.agent_id, block=True, timeout=300000)
    current = TaskGet(taskId=task_id)              # Staleness prevention
    TaskUpdate(taskId=task_id, status="completed")
```

---

## 4. Planning Stage Use Cases

### 4.1 Parallel PHASE Decomposition

When a PRD has multiple independent PHASEs:

```python
# After wm creates PHASE list in Plan Writing
phases = ["PHASE-1: Auth", "PHASE-2: Logging", "PHASE-3: Monitoring"]

# Create parallel planner-task agents
agents = []
for phase in phases:
    agent = Agent(
        subagent_type="planner-task",
        prompt=f"Decompose {phase} into executable tasks",
        run_in_background=True
    )
    agents.append(agent)

# Wait for all
for agent in agents:
    TaskOutput(task_id=agent.agent_id, block=True, timeout=300000)
```

### 4.2 Parallel Design Analysis

When design areas are independent:

```python
# Independent design domains
design_areas = [
    ("UI Layer", "Design component architecture"),
    ("API Layer", "Design endpoint structure"),
    ("Data Layer", "Design database schema")
]

agents = []
for area, prompt in design_areas:
    agent = Agent(
        subagent_type="design",
        prompt=f"{area}: {prompt}",
        run_in_background=True
    )
    agents.append(agent)

# Wait for all
for agent in agents:
    TaskOutput(task_id=agent.agent_id, block=True, timeout=300000)
```

### 4.3 Parallel Document Modification

When modifying multiple independent documents:

```python
# Independent document updates
documents = [
    ("PRD", "prd.md", "Update requirements section"),
    ("Design", "design.md", "Update architecture diagram"),
    ("Tasks", "tasks.md", "Update task dependencies")
]

agents = []
for doc_name, path, change in documents:
    agent = Agent(
        subagent_type="general-purpose",
        prompt=f"Update {doc_name} ({path}): {change}",
        run_in_background=True
    )
    agents.append(agent)

# Wait for all
for agent in agents:
    TaskOutput(task_id=agent.agent_id, block=True, timeout=300000)
```

---

## 5. Task Tool Quick Reference

| Tool | Purpose | Planning Use |
|------|---------|--------------|
| `TaskCreate` | Create new task | Track planning work items |
| `TaskList` | List all tasks | Find executable planning tasks |
| `TaskGet` | Get task details | Retrieve planning task context |
| `TaskUpdate` | Update task status | Mark planning progress |
| `TaskOutput` | Read agent output | Retrieve completed agent results |
| `TaskStop` | Stop running agent | Cancel in-progress agent |

---

## 6. Integration with WM Processes

This guide is referenced by:
- [Development Process](../processes/development-process.md) - Task Tool Checklist
- [Parallel Execution Pattern](../policies/pattern-parallel-execution.md) - Section 4.4
- [Plan Prompt Guide](plan-prompt-guide.md) - Task Tool Integration
- [WM SKILL.md](../../SKILL.md) - Section 4, 6

---

## 7. Staleness Prevention (CRITICAL)

Every `TaskUpdate` call **MUST** be preceded by a `TaskGet` call to read the latest state.

> **Rule**: Make sure to read a task's latest state using `TaskGet` before updating it.

### Why Staleness Matters

- Tasks may be updated by other agents running in parallel
- Status may change between `TaskList()` call and `TaskUpdate()` call
- Stale updates can cause race conditions or invalid state transitions

### Correct Pattern

```python
# ✅ CORRECT: Always TaskGet before TaskUpdate
current = TaskGet(taskId=task.id)          # Read latest state
if current.status == "pending":            # Verify expected state
    TaskUpdate(taskId=task.id, status="in_progress")

# ... agent work ...

current = TaskGet(taskId=task.id)          # Read latest state again
TaskUpdate(taskId=task.id, status="completed")
```

### Anti-Pattern (NEVER DO THIS)

```python
# ❌ WRONG: TaskUpdate without TaskGet
TaskUpdate(taskId=task.id, status="in_progress")  # Stale!

# ❌ WRONG: Using TaskList status directly for update
tasks = TaskList()
for t in tasks:
    TaskUpdate(taskId=t.id, status="completed")    # Stale!
```

---

## 8. Task Deletion (since 2.1.20)

Tasks can be permanently removed using `TaskUpdate(status="deleted")`.

### When to Delete

| Scenario | Example |
|----------|---------|
| **partial_fix** | planner-task self-validation found issues -> delete phase tasks -> recreate |
| **Workflow cleanup** | After workflow completion -> delete all feature tasks |
| **Intent abandonment** | User cancels intent in MULTI_INTENT -> delete tasks for that intent |

### Quick Pattern

```python
# Must follow Staleness rules even when deleting
current = TaskGet(taskId=task.id)
TaskUpdate(taskId=task.id, status="deleted")
```

> **Full Guide**: [Task Deletion Guide](task-deletion-guide.md)

---

## 9. TaskCompleted Hook (v2.1.33)

Automatically runs quality gates when an Agent completes a Task.

**Behavior**:
- Receives `{ task_id, task_name, task_status, agent_id, team_name }` JSON via stdin
- Automatically runs ESLint + TypeScript type checking on changed TS/TSX files
- exit 0: Allow completion / exit 2: Block completion + send stderr feedback to team lead

**Configuration**: `hooks.TaskCompleted` in `.claude/settings.json`
**Script**: `.claude/hooks/task-completed-quality-gate.sh`

> When lint/type errors are detected after an Agent modifies code and attempts Task completion, the completion is blocked and fix feedback is sent to the agent.

---

## 10. Best Practices

1. **Always check independence** before parallelizing planning agents
2. **Use metadata** to categorize and filter planning tasks
3. **Log agentId** for resume capability after context compression
4. **TaskGet before TaskUpdate** (CRITICAL): Always read latest state before updating
5. **Prefer parallel** when independence criteria are met
6. **Use deletion** for invalid/abandoned tasks, not completion
