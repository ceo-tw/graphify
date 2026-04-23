# Feature: Interactive Checkpoint Selection

## Purpose

Use `AskUserQuestion` tool to provide an interactive checkpoint selection UI.

## Design Principles

1. **User-Friendly Labels**: Show summary and relative time, not technical details
2. **Limited Options**: Max 4 options (AskUserQuestion UI constraint)
3. **Cancel Option**: Always provide a way to cancel (for single checkpoint case)
4. **Korean Language**: All labels and descriptions in Korean

## Implementation

### Building Options

```python
def build_checkpoint_options(checkpoints):
    """Build options for AskUserQuestion."""
    # Reverse to show newest first
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

    # Single checkpoint: add cancel option
    if len(checkpoints) == 1:
        options.append({
            "label": "복원 취소",
            "description": "체크포인트를 유지하고 취소합니다"
        })

    return options
```

### AskUserQuestion Call

```python
answer = AskUserQuestion(questions=[{
    "question": "어떤 체크포인트로 복원할까요?",
    "header": "체크포인트",
    "options": options,
    "multiSelect": False
}])
```

### Processing Response

```python
selected_label = answer.get("questions", [{}])[0].get("answer", "")

# Handle cancellation
if selected_label == "복원 취소":
    return {"status": "cancelled"}

# Handle "Other" input
if selected_label.startswith("Other"):
    custom_input = extract_custom_input(selected_label)
    # Try parsing as slot number...

# Find selected option index
for i, opt in enumerate(options):
    if opt["label"] == selected_label:
        array_index = checkpoint_count - 1 - i
        break
```

## UI Example

```
┌─ 어떤 체크포인트로 복원할까요? ─────────────────────┐
│ ○ e2e-test (dev-executor) - 방금 전                │
│ ○ code-quality (qa) - 2시간 전                     │
│ ○ ci-cd-foundation (완료) - 5시간 전               │
│ ○ Other...                                         │
└────────────────────────────────────────────────────┘
```

## Constraints

1. **Min 2 Options**: AskUserQuestion requires at least 2 options
2. **Max 4 Options**: UI displays up to 4 options clearly
3. **Other Input**: User can type slot number (1-based) in "Other"
