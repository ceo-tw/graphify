# Pattern: Planner Invocation

## Purpose

Standard pattern for invoking the planner with restoration context.

## Restoration Context Format

```python
restoration_context = f"""
[Restoration Mode]
restoration_mode: true
saved_state:
  plan_name: {checkpoint['plan_name']}
  worktree_path: {checkpoint.get('worktree_path')}
  current_phase: {checkpoint['current_phase']}
  phase_status: {checkpoint['phase_status']}
  pending_agents: {checkpoint.get('pending_agents', [])}
  completed_agents: {checkpoint.get('completed_agents', [])}
  context_summary: {checkpoint.get('context_summary', '')}
  classification: {checkpoint.get('classification', {})}

Resume from PHASE {checkpoint['current_phase']}.
Skip classification and confirmation steps.
Verify worktree exists and continue workflow.
"""
```

## Task Tool Invocation

### Basic Invocation

```python
task_params = {
    "subagent_type": "general-purpose",
    "prompt": restoration_context
}

result = Task(**task_params)
```

### With Agent Resume

```python
task_params = {
    "subagent_type": "general-purpose",
    "prompt": restoration_context
}

if last_agent_id:
    task_params["resume"] = last_agent_id
    print(f"🔄 Resuming with agentId: {last_agent_id}")

result = Task(**task_params)
```

## Pre-Invocation Messages

```
🚀 Planner를 복원 모드로 실행합니다...
```

## Post-Invocation Handling

### Success

```python
if result.get("status") == "success":
    # Proceed to cleanup
    pass
```

### Failure

```python
if result.get("status") == "error":
    print(f"""
❌ Planner 복원 중 오류가 발생했습니다.

오류: {result.get("error", "unknown")}

체크포인트는 보존됩니다. 다시 시도하거나 수동 복구하세요.
""")
    return {"status": "error", "reason": "planner_invocation_failed"}
```

## Important Notes

1. **Checkpoint Preservation**: On failure, checkpoint is NOT deleted
2. **Resume Best-Effort**: agentId resume may fail if session expired
3. **Skip Confirmation**: Restoration mode skips user confirmation prompts
4. **Continue Workflow**: Planner should pick up from saved phase
