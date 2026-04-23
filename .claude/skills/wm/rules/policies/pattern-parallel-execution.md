# Parallel Execution Pattern (MUST)

> **Directive**: Independent agents/tasks MUST execute in parallel.
> Sequential execution of independent work is a process violation.

---

## 1. MUST Directive

When executing workflow steps, you **MUST**:

1. **Analyze Dependencies**: Before each step, identify dependencies
2. **Parallel Execution**: If no dependencies exist, execute in parallel
3. **Concurrent Task Calls**: Use simultaneous Task tool calls for independent work

**Violation**: Sequential execution of independent agents is a **process violation**.

---

## 2. Independence Test

Two agents are **INDEPENDENT** when ALL of the following are true:

- [ ] Agent A's output is NOT Agent B's input
- [ ] No shared files being modified
- [ ] No shared external resources (DB writes, API mutations)
- [ ] No shared module imports that could cause type conflicts

### `is_executable()` Function Definition

A task is executable when all its dependencies are satisfied:

```python
def is_executable(task):
    """A task is executable if all blockedBy tasks are completed."""
    if not task.blockedBy:
        return True  # No dependencies
    for dep_id in task.blockedBy:
        dep_task = TaskGet(taskId=dep_id)
        if dep_task.status != "completed":
            return False
    return True
```

### Deadlock Detection

Before executing the parallel loop, check for circular dependencies:

```python
def detect_deadlock(tasks):
    """Detect circular dependencies using DFS cycle detection."""
    visited = set()
    in_stack = set()
    
    def dfs(task_id):
        if task_id in in_stack:
            return True  # Cycle found!
        if task_id in visited:
            return False
        visited.add(task_id)
        in_stack.add(task_id)
        task = get_task(task_id)
        for dep_id in (task.blockedBy or []):
            if dfs(dep_id):
                return True
        in_stack.remove(task_id)
        return False
    
    for task in tasks:
        if dfs(task.id):
            # ESCALATE: Report circular dependency to user
            report_to_user(f"Circular dependency detected involving {task.id}")
            return True
    return False

# Usage in development-process.md:
all_tasks = TaskList()
if detect_deadlock(all_tasks):
    # Stop execution, user must resolve
    pass
```

### Decision Matrix

| Scenario | Parallel? | Rationale |
|----------|-----------|-----------|
| Multiple TASKs with no file overlap | **YES (MUST)** | Independent file modifications |
| `qa` + `knowledge-keeper` | **YES (MUST)** | No dependencies |
| `qa` + `security-reviewer` | **YES (MUST)** | Independent review perspectives (DB review integrated into qa) |
| `performance-optimizer` | **YES** | Independent post-QA task |
| `dev-executor` on same file | NO | Conflict risk |
| Multiple `dev-executor` on different files | **YES (MUST)** | Independent modifications |
| `dev-executor` after `planner-task` | NO | Implementation needs task output |
| `design` (includes Type Design Checklist) | NO | Sequential, part of design workflow |
| `planner-task` (includes Test Strategy Check 5) | NO | Sequential, part of planning workflow |

---

## 3. Task Tool Parallel Pattern

### Correct: Parallel Independent Agents

```python
# Launch all independent agents simultaneously
task_a = Task(
    subagent_type="dev-executor",
    prompt="TASK-001: Implement feature A in file_a.ts",
    run_in_background=True
)
task_b = Task(
    subagent_type="dev-executor",
    prompt="TASK-002: Implement feature B in file_b.ts",
    run_in_background=True
)

# Wait for all to complete
TaskOutput(task_id=task_a.agent_id, block=True, timeout=300000)
TaskOutput(task_id=task_b.agent_id, block=True, timeout=300000)
```

### Wrong: Sequential When Independent (VIOLATION)

```python
# WRONG: Unnecessary sequential execution
task_a = Task(subagent_type="dev-executor", prompt="TASK-001...")
TaskOutput(task_id=task_a.agent_id, block=True)  # Unnecessary wait!
task_b = Task(subagent_type="dev-executor", prompt="TASK-002...")  # Should have started with task_a
```

---

## 4. Common Parallel Scenarios

### 4.1 Multiple TASK Implementation

When multiple TASKs have no file dependencies:

```markdown
## Execution Plan

TASKs to execute in parallel:
- TASK-001: file_a.ts, file_b.ts
- TASK-002: file_c.ts, file_d.ts
- TASK-003: file_e.ts

File overlap check: None → **Parallel execution REQUIRED**
```

### 4.2 QA + Documentation

After implementation, QA and knowledge recording can run in parallel:

```python
qa_task = Task(subagent_type="qa", prompt="...", run_in_background=True)
kb_task = Task(subagent_type="knowledge-keeper", prompt="...", run_in_background=True)

# Both complete independently
```

### 4.3 Research/Exploration

Multiple exploration agents can run in parallel:

```python
explore_a = Task(subagent_type="Explore", prompt="Find auth patterns", run_in_background=True)
explore_b = Task(subagent_type="Explore", prompt="Find API routes", run_in_background=True)
```

### 4.4 Planning Stage Parallelization

When planning work has no dependencies, execute in parallel:

**Scenario 1: Independent PHASE Decomposition**
```python
# Multiple PHASEs with no dependencies → parallel planner-task
phase_a = Task(subagent_type="planner-task", prompt="PHASE-1: Auth module", run_in_background=True)
phase_b = Task(subagent_type="planner-task", prompt="PHASE-2: Logging module", run_in_background=True)
```

**Scenario 2: Multi-Area Design Analysis**
```python
# Independent design areas → parallel design agents
design_ui = Task(subagent_type="design", prompt="UI layer design", run_in_background=True)
design_api = Task(subagent_type="design", prompt="API layer design", run_in_background=True)
```

**Scenario 3: Parallel Document Creation/Modification**
```python
# Multiple independent documents → parallel creation
doc_prd = Task(subagent_type="design", prompt="Write Design for Feature A", run_in_background=True)
doc_design = Task(subagent_type="design", prompt="Write Design for Feature B", run_in_background=True)
```

**Scenario 4: Multiple Explore Agents**
See Section 4.3 above. Independent exploration targets enable parallel Explore agents.

> **Reference**: For detailed Task tool usage in planning, see [Task Tool Planning Guide](../components/task-tool-planning-guide.md)

---

## 5. Sequential Required Cases

These scenarios **MUST** remain sequential:

| Pipeline Stage | Reason |
|----------------|--------|
| `design` → `planner-task` | Task decomposition requires architecture |
| `planner-task` → `dev-executor` | Implementation requires task definitions |
| HARD GATE failures | Must stop and resolve before continuing |

---

## 6. Progress Tracking for Parallel Execution

When tracking parallel agents:

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| dev-executor (TASK-001) | abc123 | in_progress | 14:30 | Implementation |
| dev-executor (TASK-002) | def456 | in_progress | 14:30 | Implementation |
| dev-executor (TASK-003) | ghi789 | in_progress | 14:30 | Implementation |
```

Update all to `completed` only after ALL parallel agents finish.

---

## 7. Infrastructure Notes

- Claude Code 2.1.16+ supports 5+ parallel agents reliably
- Memory/stability issues resolved
- Context window ~98% utilization achievable
- Use `run_in_background=True` for all parallel agents
