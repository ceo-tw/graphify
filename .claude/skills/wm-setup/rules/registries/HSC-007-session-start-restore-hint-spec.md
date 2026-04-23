---
id: HSC-007
name: Session Start Restore Hint
script: session-start-restore-hint.sh
event: Stop
impact: MEDIUM
blocking: false
dependencies:
  - hook-utils.sh
usedBy:
  - all-skills
  - wm skill
---

# Session Start Restore Hint Specification

## Purpose

Displays a restore hint at the start of new sessions when previous session state
is available. Guides users to restore their previous working context, improving
continuity between sessions.

## Event Binding

| Field | Value |
|-------|-------|
| Event | Stop |
| Matcher | (empty - session end) |
| Timeout | 3000ms |

## Input Parameters

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| CLAUDE_PROJECT_DIR | string | env | Project root directory |
| SESSION_ID | string | env | Current session identifier |

## Trigger Conditions

```bash
# Shows hint when:
# 1. Checkpoint file exists from previous session
# 2. Previous session had active tasks or plans
# 3. Less than 24 hours since last checkpoint

should_show_hint() {
    local checkpoint=".claude/checkpoints/latest.json"
    if [[ -f "$checkpoint" ]]; then
        local age=$(file_age_hours "$checkpoint")
        [[ $age -lt 24 ]]
    fi
}
```

## Output Format

```
==================================================
 [SESSION START] 컨텍스트 복원 안내
==================================================
 마지막 체크포인트: 2시간 전
   이벤트: session_end
 이전 목표: Feature: Add user authentication
 이전 작업 컨텍스트가 존재합니다.

 '/restore-context' 명령으로
   이전 작업을 이어갈 수 있습니다.
==================================================
```

## Validation Checklist

- [x] Script exists at `.claude/hooks/session-start-restore-hint.sh`
- [x] Script is executable (chmod +x)
- [x] hook-utils.sh dependency present
- [x] Hook registered in settings.json Stop
- [x] Checkpoint detection works
- [x] Korean message formatting correct
- [x] Age calculation accurate

## Test Cases

### TC-001: Show hint with recent checkpoint
- Input: Session start with checkpoint <24h old
- Expected: Restore hint displayed
- Status: [x] PASS [ ] FAIL

### TC-002: Skip hint with old checkpoint
- Input: Session start with checkpoint >24h old
- Expected: No hint displayed
- Status: [x] PASS [ ] FAIL

### TC-003: Skip hint with no checkpoint
- Input: Session start with no checkpoint file
- Expected: No hint displayed
- Status: [x] PASS [ ] FAIL

### TC-004: Handle corrupted checkpoint
- Input: Session start with invalid JSON checkpoint
- Expected: No hint displayed, no error
- Status: [x] PASS [ ] FAIL

## Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | Hint shown or skipped | Continue |
| 1 | Error reading checkpoint | Skip hint, continue |
| 2 | N/A (non-blocking) | N/A |

## Dependencies

| Dependency | Type | Required |
|------------|------|----------|
| hook-utils.sh | Library | Yes |
| jq | Binary | Optional |

## Checkpoint Detection

```bash
get_checkpoint_info() {
    local checkpoint=".claude/checkpoints/latest.json"

    if [[ ! -f "$checkpoint" ]]; then
        return 1
    fi

    local timestamp=$(jq -r '.timestamp' "$checkpoint" 2>/dev/null)
    local goal=$(jq -r '.checkpoint.description // "목표 설정 대기"' "$checkpoint" 2>/dev/null)
    local event=$(jq -r '.event // "unknown"' "$checkpoint" 2>/dev/null)

    echo "timestamp=$timestamp"
    echo "goal=$goal"
    echo "event=$event"
}
```

## Localization

Messages are displayed in Korean by default:

| Key | Korean | English (reference) |
|-----|--------|---------------------|
| header | 컨텍스트 복원 안내 | Context Restore Guide |
| checkpoint | 마지막 체크포인트 | Last checkpoint |
| goal | 이전 목표 | Previous goal |
| command | 명령으로 | with command |

## References

- Registry: [hooks.yaml](hooks.yaml)
- Script: [../../hooks/session-start-restore-hint.sh](../../hooks/session-start-restore-hint.sh)
- Precompact Hook: [HSC-006-precompact-save-state-spec.md](HSC-006-precompact-save-state-spec.md)
- Restore Command: [../../skills/wm/rules/commands/restore-context.md](../../skills/wm/rules/commands/restore-context.md)
