# v1.0 Restoration Process

## Purpose

Handle restoration from legacy v1.0 checkpoint format.

## v1.0 Checkpoint Structure

```json
{
  "version": "1.0",
  "timestamp": "2026-01-25T12:00:00Z",
  "plan_name": "my-feature",
  "current_phase": 2,
  "phase_status": "in_progress",
  "worktree_path": "/path/to/worktree"  // optional
}
```

## Restoration Steps

### 1. Extract Checkpoint Data

```python
plan_name = checkpoint.get("plan_name", "unknown")
current_phase = checkpoint.get("current_phase", 1)
phase_status = checkpoint.get("phase_status", "unknown")
timestamp = checkpoint.get("timestamp", "unknown")
worktree_path = checkpoint.get("worktree_path")
```

### 2. Build Restoration Context

```python
restoration_context = f"""
[Restoration Mode - v1.0 Legacy]
restoration_mode: true
saved_state:
  plan_name: {plan_name}
  worktree_path: {worktree_path}
  current_phase: {current_phase}
  phase_status: {phase_status}

Resume from PHASE {current_phase}.
Skip classification and confirmation steps.
"""
```

### 3. Display Summary

```
📋 v1.0 체크포인트 정보

| 항목 | 값 |
|------|-----|
| 계획 이름 | {plan_name} |
| 현재 PHASE | PHASE {current_phase} ({phase_status}) |
| 저장 시각 | {timestamp} |
```

## Migration Note

v1.0 checkpoints are automatically migrated to v4.0 by `hook-utils.sh` when:
1. PreCompact hook runs and adds a new checkpoint
2. The `migrate_checkpoint_to_v4()` function is called

After migration, the checkpoint file will be v4.0 format with the v1.0 data preserved in the first checkpoint entry.
