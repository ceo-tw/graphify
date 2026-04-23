# Feature: Cleanup After Restore

## Purpose

Remove used checkpoint from the checkpoint file after successful restoration.

## Strategy by Version

### v4.0 - Remove Single Entry

For v4.0 FIFO arrays, remove only the used checkpoint:

```python
if remaining_count == 0:
    # Last checkpoint - delete entire file
    os.remove(checkpoint_path)
    cleanup_status = "파일 삭제됨 (마지막 체크포인트)"
else:
    # Remove specific checkpoint and reindex slots
    jq_command = f"""
    jq 'del(.checkpoints[{array_index}]) |
        .checkpoints = [.checkpoints | to_entries[] | .value + {{"slot": .key}}]'
        {checkpoint_path} > {checkpoint_path}.tmp &&
        mv {checkpoint_path}.tmp {checkpoint_path}
    """
    subprocess.run(jq_command, shell=True)
    cleanup_status = f"슬롯 {selected_slot} 제거됨 ({remaining_count}개 남음)"
```

### v3.0/v1.0 - Delete File

For older single-checkpoint formats, delete the entire file:

```bash
rm .claude/workflow-checkpoint.json
```

## Slot Reindexing

After removing a checkpoint, slot numbers must be reindexed:

**Before removal (slot 1 removed):**
```json
{
  "checkpoints": [
    {"slot": 0, "summary": "a"},
    {"slot": 1, "summary": "b"},  // ← removed
    {"slot": 2, "summary": "c"}
  ]
}
```

**After removal:**
```json
{
  "checkpoints": [
    {"slot": 0, "summary": "a"},
    {"slot": 1, "summary": "c"}   // ← reindexed from 2 to 1
  ]
}
```

## Error Handling

If cleanup fails:

```python
try:
    # cleanup code...
except Exception as e:
    print(f"""
⚠️ 체크포인트 정리 실패: {str(e)}

워크플로우는 복원되었지만 checkpoint가 남아있습니다.
수동으로 정리하세요:

rm .claude/workflow-checkpoint.json
""")
```

## Success Message

```
✅ 워크플로우가 성공적으로 복원되었습니다.

| 항목 | 값 |
|------|-----|
| 복원된 계획 | {plan_name} |
| 재개 PHASE | PHASE {current_phase} |
| 체크포인트 | {cleanup_status} |
```
