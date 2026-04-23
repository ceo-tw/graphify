# Execution Guide (Detail)

> MANDATORY: After ExitPlanMode approval, complexity-based branching executes.
> Complex types load context and proceed to agent pipeline. Simple types execute directly.

## Step 1: Load Context (FIRST ACTION after approval)

### 1-A: Complexity-Based Branching

After ExitPlanMode approval, execution flow is determined by the plan type's complexity (classified in Step 2 during planning).

| Type | Complexity | Flow |
|------|-----------|------|
| NEW_DEVELOPMENT | **Complex** | Load Context -> Agent Pipeline (design -> planner-task -> dev-executor -> qa) |
| MODIFICATION | **Complex** | Load Context -> Agent Pipeline (design -> planner-task -> dev-executor -> qa) |
| BUG_FIX (Complex) | **Complex** | Load Context -> Agent Pipeline |
| BUG_FIX (E2E) | **Complex** | Load Context -> Agent Pipeline |
| MULTI_INTENT | **Complex** | Load Context -> Agent Pipeline |
| BUG_FIX (Simple) | **Simple** | Direct execution (solve skill) |
| DOCUMENTATION | **Simple** | Direct edit (no agent pipeline) |
| DOCUMENTATION_BATCH | **Simple** | Task-based parallel edits |
| INQUIRY | **Simple** | Analysis only (Explore agent) |
| REPORT | **Simple** | Collection only |
| CLEANUP | **Simple** | File ops |

### 1-B: Load Deferred Tools (CRITICAL - FIRST ACTION)

Task tools are deferred tools and must be loaded via ToolSearch:

```python
# 0. Load Task tools (deferred tools - calling without loading will fail)
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")
```

> **NOTE**: Even if Task tools are registered in `allowed-tools`, that only handles **automatic permission approval**.
> To actually use the tools, **explicit loading** via ToolSearch is required.

### 1-C: Load Execution Context (Complex types, BEFORE any agent call)

```python
# 1. Re-read plan (ensure latest version)
plan_content = Read(plan_path)
# VERIFY: "## 0. Execution Process (MUST" exists

# 2. Compute process file path from classified type
process_file_path = "${CLAUDE_SKILL_DIR}/" + process_file

# 3. Read process file (contains Agent Invocation Pattern)
process_content = Read(process_file_path)
# VERIFY: "### Agent Invocation Pattern (MANDATORY)" exists
```

### 1-D: Verify Plan Enrichment (SAFETY RAIL)

```python
enriched_plan = Read(plan_path)

# CHECK 1: Section 0 with numbered steps
assert "## 0. Execution Process (MUST" in enriched_plan

# CHECK 2: Agent Execution Log (Complex types)
assert "## Agent Execution Log" in enriched_plan

# CHECK 3: Development types need >= 5 checkboxes
if detected_type in ["NEW_DEVELOPMENT", "MODIFICATION"]:
    assert enriched_plan.count("- [ ]") >= 5
```

> **If any check fails**: wm must re-inject the process template from Step 4 of planning.

## Step 2: Execution Mode Branch

PHASE decomposition is performed in wm Step 4 (Plan Writing).

### 2-A: Determine Execution Mode

Analyze the PHASE structure in the plan document to determine execution mode.

```python
# Analyze PHASE count and dependencies in plan document
phase_count = count_phases_in_plan(plan_content)

if phase_count >= 5:
    execution_mode = "agent_teams"
else:
    execution_mode = "task_based"  # default
```

- `"agent_teams"` -> Step 3 Path A (Agent Teams)
- `"task_based"` or null -> Step 3 Path B (Task-based, default)

> **NOTE (Worktree temporarily disabled)**: Worktree isolation is not used until a conflict prevention strategy is established. Do not pass `isolation="worktree"` option.

## Step 3: Execution

### Path A -- Agent Teams Execution

```python
plan_name = extract_plan_name(plan_path)

# 1. Create team
TeamCreate(team_name=f"{plan_name}-team", description=f"Executing {plan_name}")

# 2. Spawn team members
Agent(subagent_type="design", name="architect", team_name=f"{plan_name}-team",
     model="opus", mode="plan", prompt="...")
Agent(subagent_type="dev-executor", name="dev-1", team_name=f"{plan_name}-team",
     model="sonnet", mode="plan", prompt="...")

# 3. Distribute tasks
for phase in phases:
    TaskCreate(subject=phase.name, description=phase.goal)
    TaskUpdate(taskId=task.id, owner=phase.assigned_role)

# 4. Lead (wm) monitors progress
# SendMessage for team communication, TaskList for progress tracking

# 5. Cleanup after completion
# All members shutdown -> TeamDelete()
```

> **Note**: Agent Execution Log recording is MANDATORY in Agent Teams pattern too.

### Path B -- Default Task-based Execution

> **EXECUTION RULE**: Follow the **Agent Invocation Pattern (MANDATORY)** from the process file loaded in Step 1-B exactly.

**B-1. Identify remaining steps**: Check Section 0 checkboxes in plan for pending steps.

**B-2. Execute each step per process file's Agent Invocation Pattern**:

```python
# REFERENCE: Agent Invocation Pattern is in process_content
# (loaded via Read() in Step 1-C)
# Do NOT modify. Follow the process file's invocation pattern.
# NOTE: ToolSearch already completed in Step 1-B

# Step 1: design
agent1 = Agent(subagent_type="design",
    model="opus",
    prompt=f"Plan path: {plan_path}\nCreate architecture...",
    run_in_background=True)
# Log agentId -> Agent Execution Log | Mark checkbox [x] | Wait

# Step 2: planner-task (includes self-validation)
agent2 = Agent(subagent_type="planner-task",
    model="opus",
    prompt=f"Plan path: {plan_path}\nCreate task breakdown...",
    run_in_background=True)
# Log | Mark | Wait
# planner-task performs self-validation (PHASE coverage, dependency order,
# architecture order, domain info) before returning

# Step 3: dev-executor (PARALLEL REQUIRED)
executable_tasks = [t for t in TaskList() if is_executable(t)]
for task in executable_tasks:
    Agent(subagent_type="dev-executor",
         prompt=f"Task: {task.id}\n...",
         run_in_background=True)

# Step 4: Review Gate — single review-orchestrator call
# qa + security-reviewer + performance-optimizer are invoked internally
# (no direct calls from main context). Returns JSON verdict.
review = Agent(subagent_type="review-orchestrator",
    prompt=json.dumps({
        "plan_path": plan_path, "phase": N, "total_phases": TOTAL,
        "baseline_commit": BASELINE,
        "scope": "phase",
        "triggers": {"security": has_security, "performance": has_perf,
                     "ui": has_ui, "docs": has_docs}
    }),
    run_in_background=True)
verdict = TaskOutput(task_id=review.agent_id, block=True, timeout=900000)
# Parse JSON verdict; on LGTM/FIX_APPLIED proceed, on ESCALATE AskUserQuestion
# See FALLBACK_VERDICT in process file for timeout/malformed-JSON handling

# Step 5: Cleanup
Skill(skill="plan-cleanup", args=f"{plan_name}")
```

**B-3. Log all agents**: After each Agent() execution, immediately log agentId + timestamp in Agent Execution Log table.

**B-4. Update checkboxes**: After each step completion, mark `- [x]` in plan's Section 0.

> **NOTE (non-development types)**: BUG_FIX, INQUIRY, REPORT etc. have simpler Agent Invocation Patterns in their process files. Same principle applies: load process file in Step 1-B -> execute Agent Invocation Pattern as-is.

## RESTORATION Type

When resuming from checkpoint:
1. Read checkpoint file (`.claude/workflow-checkpoint.json`)
2. Find last `in_progress` agentId from Plan's Agent Execution Log
3. Resume with `Agent(resume=agent_id)` or start next pending step

> **Details**: See [Agent Execution Log - Restoration Usage](../rules/components/agent-execution-log.md#restoration-usage)

## Key References

| Topic | Reference |
|-------|-----------|
| agentId logging pattern | [Agent Execution Log](../rules/components/agent-execution-log.md) |
| Full execution flow | [Development Process](../rules/processes/development-process.md) |
| TaskList-based parallel | [Task Tool Planning Guide](../rules/components/task-tool-planning-guide.md) |
| Task deletion (partial_fix) | [Task Deletion Guide](../rules/components/task-deletion-guide.md) |
| Parallel execution policy | [Parallel Execution Pattern](../rules/policies/pattern-parallel-execution.md) |

## Execution Rules

| Rule | Description |
|------|-------------|
| Background execution | Use `run_in_background=True` for long-running agents |
| Code changes | Through Agents only (no direct Edit/Write in main context) |
| Parallel execution | **REQUIRED** for independent agents/tasks |
| agentId logging | Log to Plan document before proceeding |
| Staleness prevention | `TaskGet` before every `TaskUpdate` |
| dev-executor / Parallel | See SKILL.md EXECUTION INVARIANTS (single source of truth) |
