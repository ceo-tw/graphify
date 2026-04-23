# Agent Execution Log Component

Standard template for tracking agent execution in plan documents.

---

## Purpose

- Enable context restoration after context compression
- Track agent execution status and agentId for resume capability
- Provide visibility into workflow progress

---

## Template

Include this table in every plan document:

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| {agent-name} | - | pending | - | {brief description} |
```

### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Not yet started |
| `in_progress` | Currently running |
| `completed` | Successfully finished |
| `failed` | Failed (with reason in notes) |

---

## Logging Pattern

### On Agent Start

```python
from datetime import datetime

result = Task(
    subagent_type="{agent-name}",
    prompt="...",
    run_in_background=True
)
agent_id = result.agent_id
timestamp = datetime.now().isoformat()[:16]

# Update log immediately
Edit(
    file_path=plan_path,
    old_string="| {agent-name} | - | pending | - |",
    new_string=f"| {{agent-name}} | {agent_id} | in_progress | {timestamp} |"
)
```

### On Agent Completion

```python
# Wait for completion
TaskOutput(task_id=agent_id, block=True, timeout=300000)

# Update status
Edit(
    file_path=plan_path,
    old_string=f"| {{agent-name}} | {agent_id} | in_progress |",
    new_string=f"| {{agent-name}} | {agent_id} | completed |"
)
```

### On Agent Failure

```python
Edit(
    file_path=plan_path,
    old_string=f"| {{agent-name}} | {agent_id} | in_progress |",
    new_string=f"| {{agent-name}} | {agent_id} | failed |"
)
# Add failure reason as note below the table
```

---

## Type-Specific Templates

### NEW_DEVELOPMENT / MODIFICATION

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| design | - | pending | - | Architecture design |
| planner-task | - | pending | - | Task decomposition + self-validation |
| dev-executor | - | pending | - | Implementation |
| qa | - | pending | - | Test verification |
```

### BUG_FIX (Complex)

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| root-cause-finder | - | pending | - | 5 Whys analysis |
| bug-fixer | - | pending | - | TDD-style fix |
| qa | - | pending | - | Test verification |
| knowledge-keeper | - | pending | - | Document resolution |
```

### BUG_FIX (E2E)

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| playwright-test-healer | - | pending | - | Test diagnosis and fix |
| playwright-test-generator | - | pending | - | New test generation |
| qa | - | pending | - | Full verification |
```

### INQUIRY / REPORT

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| Explore | - | pending | - | Codebase analysis |
```

---

## Restoration Usage

When resuming workflow after context compression:

1. Read Agent Execution Log from plan document
2. Identify last agent with `in_progress` or `completed` status
3. Use `resume` parameter if agent has `agentId`
4. Skip already `completed` agents

```python
# Example: Resume from last agent
if agent_status == "in_progress" and agent_id:
    result = Task(
        subagent_type=agent_name,
        prompt="Continue from previous state...",
        resume=agent_id
    )
```

---

## Applicability

| Type | Agent Execution Log |
|------|---------------------|
| NEW_DEVELOPMENT | ✅ REQUIRED |
| MODIFICATION | ✅ REQUIRED |
| BUG_FIX | ✅ REQUIRED |
| INQUIRY | ✅ REQUIRED |
| REPORT | ✅ REQUIRED |
| CLEANUP | ❌ Not needed (no agents) |
| RESTORATION | ✅ Use existing log |

**MUST include for all types that use agents.**
