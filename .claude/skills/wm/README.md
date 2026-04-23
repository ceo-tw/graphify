# wm (Workflow Manager) Design Philosophy

This document explains the **design intent** of the wm process and the **rationale** for each mechanism.

> **Target audience**: wm process maintainers, those adding new constraints, developers needing process understanding

---

## Overview

wm (Workflow Manager) is a skill that systematically manages AI agent tasks.
The core goal is to ensure **predictable, trackable, and recoverable** workflows.

### Fundamental Problems Addressed

| Problem | Consequence | wm's Solution |
|---------|-------------|---------------|
| AI's improvised execution | Hard-to-reverse mistakes | Separate planning/execution with Plan Mode |
| Unlimited exploration | Analysis paralysis, cost explosion | Purpose-driven exploration via Explore agent |
| Skipping steps | Missing quality verification | Force steps via process template injection |
| Ambiguous completion criteria | Subjective "done" judgment | Track individual items with checkboxes |
| Context loss | Unable to recover progress state | Persist state with Agent Execution Log |
| Sequential execution inefficiency | Unnecessary wait time | Force parallel execution of independent tasks |

---

## Core Design Principles

### 1. "Think Before Acting" (Plan Mode Required)

**Problem**: Immediate code modifications cause hard-to-reverse mistakes. AI agents in particular tend to prefer fast execution, risking partial modifications without seeing the full picture.

**Solution**: **Immediately call `EnterPlanMode()`** when `/wm` is executed.
- Plan Mode is **read-only** (code modification forbidden)
- Only plan document writing is allowed
- Execution phase only after user approval

**If this constraint is removed**:
- Modifications begin without context understanding
- "What was the original state?" situations occur after modifications
- Change scope becomes unpredictable

```
Correct flow: /wm -> EnterPlanMode -> Explore -> Write plan -> Approval -> Execute
Risky flow: /wm -> Immediately modify code
```

---

### 2. "Structured Exploration" (Explore Agent Required)

**Problem**: Unlimited search causes three issues:
1. **Analysis paralysis**: No boundary on how much to examine
2. **Cost increase**: Loading unnecessary files into context
3. **Inconsistency**: Different exploration methods each time

**Solution**: Only allow purpose-driven exploration through the **Explore agent**.

| Explore Type | Purpose | Example |
|-------------|---------|---------|
| **LOCATE** | Find file/structure location | "Find User-related files" |
| **ANALYZE** | Analyze patterns/implementation | "Understand auth approach" |
| **COLLECT** | Collect data/statistics | "List test files" |
| **ASSESS** | Assess impact range | "Impact of User changes" |

**Directly forbidden tools**: Direct calls to `Glob`, `Grep`, `Read(for exploration)` in Plan Mode

**If this constraint is removed**:
- "Let's read everything first" -> context explosion
- No criteria for exploration scope -> infinite expansion
- Inconsistent result formats -> hard to integrate with subsequent steps

```python
# Allowed: structured exploration with clear purpose
Task(subagent_type="Explore", prompt="LOCATE: Find User domain file locations", model="haiku")

# Forbidden: purposeless search
Glob(pattern="**/*.ts")  # Direct call forbidden in Plan Mode
```

---

### 3. "Process Enforcement" (Template Injection)

**Problem**: AI agents tend to skip verification steps for "efficiency". Similar to how human developers skip tests thinking "this should be enough".

**Solution**: wm **directly injects type-specific execution process** in Step 4 (Plan Writing).

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

HARD REQUIREMENT - DO NOT SKIP
...
- [ ] 1. design -> Architecture design
- [ ] 2. planner-task -> Task decomposition (includes Self-Validation)
...
```

**Key mechanisms**:
1. Type classification + MULTI_INTENT/code file detection in wm Step 2
2. **Directly inject** process file template into plan document in wm Step 4
3. Proceed to execution phase immediately after `ExitPlanMode` approval
4. All steps enforced via checkboxes

**If this constraint is removed**:
- "Simple fix, skip tests" -> bug introduction
- "Implement without design" -> architecture consistency destroyed
- "Skip verification" -> quality assurance impossible

---

### 4. "Individual Accountability" (Checkboxes Required)

**Problem**: The expression "requirements met" is unverifiable. You cannot distinguish what was met and what was not.

**Solution**: Separate all requirements, execution steps, and verification items into **individual checkboxes**.

```markdown
## 2. Detailed Requirements

- [ ] Implement login API (/api/auth/login)
- [ ] Implement logout API (/api/auth/logout)
- [ ] Implement JWT token refresh (/api/auth/refresh)

## 4. Verification

- [ ] Login succeeds with valid credentials
- [ ] Returns 401 with wrong password
- [ ] Refresh fails with expired token
```

**Checkbox rules**:
- Each item must be **independently verifiable**
- Catch-all expressions like "etc.", "and others" are forbidden
- Completion criteria must be clear

**If this constraint is removed**:
- "API implementation complete" -> Which APIs?
- "Tests added" -> Which cases?
- Untrackable -> frequent rework

---

### 5. "Recoverable State" (Agent Execution Log)

**Problem**: When conversation context is compressed (context window limits), it's impossible to know current progress. If an Agent's `agentId` is lost, resume is also impossible.

**Solution**: Permanently record execution state in the **Agent Execution Log** within the Plan document.

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| design | def456 | completed | 2025-01-30T14:45 | Architecture design |
| planner-task | abc123 | completed | 2025-01-30T14:50 | Task decomposition + Self-Validation |
| dev-executor | ghi789 | in_progress | 2025-01-30T15:00 | Implementation |
```

**Recovery mechanism**:
1. Execute `/restore-context`
2. Find `in_progress` status Agent in Plan document
3. `resume` that Agent with `agentId`
4. Or restart from next `pending` step

**If this constraint is removed**:
- Progress state lost on context compression
- "Where did we leave off?" -> start over
- Agent resume impossible -> duplicate execution

---

### 6. "Mandatory Parallelization" (Parallel Execution Policy)

**Problem**: Sequential execution of independent tasks causes unnecessary wait time. AI tends to process "one at a time".

**Solution**: **Force parallel execution of independent agents/tasks as MUST**.

**Independence criteria**:
- Agent A's output is not Agent B's input
- Modified files do not overlap
- No shared resources (DB writes, API mutations)

```python
# MUST: Parallel execution of independent Tasks
task_a = Task(subagent_type="dev-executor", prompt="TASK-001: file_a.ts", run_in_background=True)
task_b = Task(subagent_type="dev-executor", prompt="TASK-002: file_b.ts", run_in_background=True)

# VIOLATION: Sequential execution of independent tasks
task_a = Task(...)
TaskOutput(task_id=task_a.agent_id, block=True)  # Unnecessary wait!
task_b = Task(...)  # Unrelated to task_a but waiting
```

**If this constraint is removed**:
- 10 independent Tasks execute serially
- Total time = sum of each Task's time
- Reduced efficiency, increased cost

---

### 7. Built-in Agents Deep Dive

The wm process leverages three core Built-in Agent/Tool categories:

| Category | Name | Purpose | Process Impact |
|----------|------|---------|----------------|
| Exploration | Explore | Purpose-driven codebase exploration | Plan Mode required entry point |
| Progress Tracking | Task tools | Task creation/tracking/status management | Parallel execution coordination |
| Planning | Plan agents | Planning phase automation | PRD->Design->Task pipeline |

#### 7.1 Task Tools (TaskCreate, TaskList, TaskUpdate, TaskGet)

**Problem**: Complex workflows encounter these issues:
1. Cannot track which tasks are in progress
2. Dependency management difficult during parallel execution
3. Cannot identify resume point after context compression

**Solution**: 4 Task tools manage the task lifecycle:

| Tool | Purpose | Key Pattern |
|------|---------|-------------|
| TaskCreate | Create task | Classify with metadata (`planning: true`) |
| TaskList | Query executable tasks | Filter pending + no blockedBy tasks |
| TaskGet | Query latest state | Prevent staleness (CRITICAL) |
| TaskUpdate | State transition | pending -> in_progress -> completed |

**Staleness Prevention (CRITICAL)**:

> **Rule**: Always check latest state with `TaskGet` before every `TaskUpdate` call

```python
# CORRECT
current = TaskGet(taskId=task.id)  # Query latest state
if current.status == "pending":
    TaskUpdate(taskId=task.id, status="in_progress")

# WRONG - Race condition risk
TaskUpdate(taskId=task.id, status="in_progress")  # Stale!
```

**Process impact**:
- Track parallel planning agents
- Concurrent decomposition of independent PHASEs
- Determine resume point after context compression

#### 7.2 Plan Agents (4 types)

**Problem**: Manual plan creation lacks consistency and steps get skipped:
1. PRD decomposition varies each time
2. Implementation starts without design
3. Task size criteria unclear
4. No plan completeness verification

**Solution**: 4 Core Development agents share responsibilities:

| Agent | Model | Role |
|-------|-------|------|
| design | sonnet | Architecture/component design |
| planner-task | sonnet | PHASE -> Task decomposition + Self-Validation |
| dev-executor | sonnet | Implementation |
| qa | sonnet | Verification |

> PHASE decomposition is performed directly by wm in Step 4 (Plan Writing).

**Background execution rules**:

| Agent | Expected Duration | Background |
|-------|------------------|------------|
| design | 1-2 min | REQUIRED |
| planner-task | 1-2 min | REQUIRED |
| dev-executor | 2-5 min | REQUIRED |
| qa | 1-3 min | REQUIRED |

**Process impact**:

| Process Type | Agents Used |
|--------------|-------------|
| NEW_DEVELOPMENT | design -> planner-task -> dev-executor -> qa |
| MODIFICATION | design -> planner-task -> dev-executor -> qa |
| BUG_FIX (Complex) | planner-task -> dev-executor -> qa |
| INQUIRY | Explore |

#### 7.3 Independence Tests and Dependency Chains

**Parallel execution possible (MUST)**:

| Scenario | Rationale |
|----------|-----------|
| Multiple PHASE decomposition (no dependencies) | Independent scope analysis |
| Multiple area design (different domains) | No architecture overlap |
| Multiple Explore agents (different targets) | Independent information collection |
| Multiple dev-executor (different files) | No file conflicts |

**Sequential execution required**:

| Pipeline | Reason |
|----------|--------|
| design -> planner-task | Task decomposition needs architecture |
| planner-task -> dev-executor | Implementation needs Task definitions |
| dev-executor -> qa | Verification needs implementation complete |
| HARD GATE failure | Cannot proceed until resolved |

---

## Process Type Flows

### NEW_DEVELOPMENT / MODIFICATION

```
1. design           -> Architecture design
2. planner-task     -> Task decomposition (includes Self-Validation)
3. worktree-start   -> Create isolated workspace
5. dev-executor     -> Implementation (parallel execution!)
6. qa               -> Verification
7. cleanup          -> Cleanup
8. worktree-complete -> Merge to main
```

### BUG_FIX (Complex)

```
1. root-cause-finder -> 5 Whys analysis
2. bug-fixer         -> TDD-based fix
3. qa                -> Verification
4. knowledge-keeper  -> Record resolution pattern
```

### INQUIRY / REPORT

```
1. Explore -> Data collection
2. Report  -> Report to user
```

---

## Maintenance Guide

### Checklist for Adding New Constraints

- [ ] **Problem definition**: What specific problem does this constraint solve?
- [ ] **Adverse effect analysis**: Specify problems that occur without the constraint
- [ ] **Consistency**: Does it not conflict with existing 7 principles?
- [ ] **Minimal invasiveness**: Can the problem be solved with minimum changes?
- [ ] **Documentation**: Record "problem-solution" relationship in README.md

### Checklist for Modifying Existing Constraints

- [ ] **Confirm original intent**: Why was this constraint introduced?
- [ ] **Impact scope**: Which processes/agents are affected?
- [ ] **Testing**: Does the original problem not recur after modification?
- [ ] **Documentation update**: Sync README.md

### When Considering Constraint Removal

> **Warning**: Before removing a constraint, always confirm that the problem it solved no longer exists.

1. **Reproduce the problem** the constraint was solving
2. If the problem still occurs -> cannot remove
3. If the problem doesn't occur -> analyze why
4. Only approve removal if the root cause has been resolved

---

## Related File References

| Topic | File |
|-------|------|
| Main skill definition | [SKILL.md](./SKILL.md) |
| Parallel execution policy | [pattern-parallel-execution.md](./rules/policies/pattern-parallel-execution.md) |
| Agent Execution Log | [agent-execution-log.md](./rules/components/agent-execution-log.md) |
| Type classification functions | [type-classification-functions.md](./rules/components/type-classification-functions.md) |
| Explore type guide | [explore-prompt-guide.md](./rules/components/explore-prompt-guide.md) |
| Task tool planning guide | [task-tool-planning-guide.md](./rules/components/task-tool-planning-guide.md) |
| Plan agent guide | [plan-prompt-guide.md](./rules/components/plan-prompt-guide.md) |
| Development process | [development-process.md](./rules/processes/development-process.md) |

---

## Key Summary

```
wm's reason for existence: Force AI agents to prioritize "correct execution" over "fast execution"

7 Core Principles:
1. Plan Mode required     -> Think before acting
2. Explore required       -> Purpose-driven exploration
3. Template Injection     -> Direct process injection
4. Checkboxes required    -> Individual tracking
5. Agent Execution Log    -> State persistence
6. Parallel execution     -> Efficiency guarantee
7. Built-in Agents        -> Task tools + Plan agents

Each constraint is justified by "what problem occurs if removed?"
```
