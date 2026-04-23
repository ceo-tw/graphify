# v4.0 Restoration Process

## Purpose

Handle restoration from v4.0 FIFO array checkpoint format.

## v4.0 Checkpoint Structure

```json
{
  "version": "4.0",
  "max_checkpoints": 5,
  "checkpoints": [
    {
      "slot": 0,
      "timestamp": "2026-01-25T10:00:00Z",
      "session_id": "session-older",
      "summary": "older-plan (qa)",
      "current_work": {...}
    },
    {
      "slot": 1,
      "timestamp": "2026-01-25T12:00:00Z",
      "session_id": "session-newer",
      "summary": "newer-plan (dev-executor)",
      "current_work": {...}
    }
  ]
}
```

## Key Concepts

### FIFO Array
- Maximum 5 checkpoints (configurable via `max_checkpoints`)
- Oldest checkpoint removed when limit exceeded
- `slot` field indicates position (0 = oldest)

### Display Order
- User sees checkpoints newest-first (reverse of array)
- Slot 1 in UI = array[-1] (most recent)
- Slot 2 in UI = array[-2] (second most recent)

## Restoration Steps

### 1. Interactive Selection

```python
# Build options for AskUserQuestion (max 4 due to UI limit)
checkpoints = checkpoint_file.get("checkpoints", [])
display_checkpoints = list(reversed(checkpoints))[:4]

options = []
for cp in display_checkpoints:
    timestamp = cp.get("timestamp", "unknown")
    relative_time = calculate_relative_time(timestamp)
    summary = cp.get("summary", "작업 정보 없음")
    options.append({
        "label": f"{summary} - {relative_time}",
        "description": f"저장 시각: {timestamp}"
    })

# For single checkpoint, add cancel option
if len(checkpoints) == 1:
    options.append({"label": "복원 취소", "description": "체크포인트를 유지하고 취소"})
```

### 2. Process Selection

```python
# Map user selection to array index
# selected_index 0 = newest = checkpoints[-1]
array_index = checkpoint_count - 1 - selected_index
selected_checkpoint = checkpoints[array_index]
```

### 3. Build Restoration Context

```python
current_work = selected_checkpoint.get("current_work", {})

restoration_context = f"""
[Restoration Mode - v4.0]
restoration_mode: true
selected_slot: {selected_slot}
saved_state:
  plan_path: {current_work.get('plan_path')}
  status: {current_work.get('status')}
  last_agent: {current_work.get('last_agent')}
  last_agent_id: {current_work.get('last_agent_id')}
  timestamp: {selected_checkpoint.get('timestamp')}

Resume workflow from selected checkpoint.
"""
```

### 4. Cleanup After Success

```python
if remaining_count == 0:
    # Last checkpoint - delete file
    os.remove(checkpoint_path)
else:
    # Remove selected checkpoint from array
    jq_cmd = f"""jq 'del(.checkpoints[{array_index}]) |
        .checkpoints = [.checkpoints | to_entries[] | .value + {{"slot": .key}}]'
        {checkpoint_path} > {checkpoint_path}.tmp &&
        mv {checkpoint_path}.tmp {checkpoint_path}"""
    subprocess.run(jq_cmd, shell=True)
```

## Display Summary

```
📋 v4.0 체크포인트 정보

| 항목 | 값 |
|------|-----|
| 선택된 슬롯 | {selected_slot} / {total_count} |
| 계획 이름 | {plan_name} |
| 상태 | {status} |
| 저장 시각 | {timestamp} |
```

## Edge Cases

1. **Empty checkpoints array**: Display error and suggest deletion
2. **Single checkpoint**: Add "복원 취소" option
3. **More than 4 checkpoints**: Only show 4 most recent (UI limit)
