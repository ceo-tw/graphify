# v3.0 Restoration Process

## Purpose

Handle restoration from v3.0 single checkpoint format.

## v3.0 Checkpoint Structure

```json
{
  "version": "3.0",
  "timestamp": "2026-01-25T12:00:00Z",
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "current_work": {
    "plan_path": ".claude/plans/my-feature.md",
    "design_path": ".claude/plans/my-feature-DESIGN.md",
    "tasks_path": ".claude/plans/my-feature-TASKS-PHASE-1.md",
    "status": "in_progress",
    "last_agent": "dev-executor",
    "last_agent_id": "agent-123"
  },
  "completed_phases": [
    {"name": "phase-0", "completed_at": "2026-01-24", "path": "..."}
  ],
  "plans_tree": "..."
}
```

## Restoration Steps

### 1. Extract Current Work

```python
current_work = checkpoint.get("current_work", {})

plan_path = current_work.get("plan_path", "")
plan_name = os.path.basename(plan_path).replace(".md", "") if plan_path else "unknown"
status = current_work.get("status", "unknown")
last_agent = current_work.get("last_agent")
last_agent_id = current_work.get("last_agent_id")
```

### 2. Build Restoration Context

```python
restoration_context = f"""
[Restoration Mode - v3.0]
restoration_mode: true
saved_state:
  plan_name: {plan_name}
  plan_path: {plan_path}
  status: {status}
  last_agent: {last_agent}
  completed_phases: {len(checkpoint.get('completed_phases', []))}

Resume workflow with last agent: {last_agent}.
"""
```

### 3. Optional Agent Resume

If `last_agent_id` is available:

```python
task_params = {
    "subagent_type": "general-purpose",
    "prompt": restoration_context
}

if last_agent_id:
    task_params["resume"] = last_agent_id
    print(f"🔄 Resuming with agentId: {last_agent_id}")
```

### 4. Display Summary

```
📋 v3.0 체크포인트 정보

| 항목 | 값 |
|------|-----|
| 계획 이름 | {plan_name} |
| 상태 | {status} |
| 마지막 Agent | {last_agent} |
| 완료된 Phase | {completed_count}개 |
```

## Cleanup

After successful restoration, delete the checkpoint file:

```bash
rm .claude/workflow-checkpoint.json
```
