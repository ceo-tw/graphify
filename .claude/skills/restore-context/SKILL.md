---
name: restore-context
type: workflow
description: "저장된 체크포인트에서 플래너 워크플로우 상태를 복원합니다. 사용 시점: (1) Context compression 후 중단된 작업을 이어갈 때, (2) 새 세션에서 이전 작업을 복원할 때. /restore-context 커맨드로 호출."
allowed-tools:
  - Read
  - Agent
  - Bash
  - AskUserQuestion
user-invocable: true
---

# Restore Context Skill

## Purpose

Restore planner workflow state after context compression.

When Claude Code performs context compression, the planner orchestration state is lost. This skill reads the saved checkpoint and re-invokes the planner with restoration context.

## Quick Reference

| Command | Description |
|---------|-------------|
| `/restore-context` | 대화형 체크포인트 선택 |
| `/restore-context --slot N` | 특정 슬롯 복원 (1=최근) |

## Module Structure

This skill is modularized. See [rules/_sections.md](rules/_sections.md) for the full index.

| Category | Modules |
|----------|---------|
| Components | checkpoint-reader, checkpoint-validator, relative-time, worktree-verifier |
| Processes | restore-v1, restore-v3, restore-v4 |
| Rules | feature-interactive-selection, feature-cleanup-after-restore, pattern-error-messages, pattern-planner-invocation |
| Orchestration | restoration-flow |

## Workflow

```mermaid
graph TD
    A[/restore-context 호출] --> B{체크포인트 존재?}
    B -->|없음| C[에러: no_checkpoint]
    B -->|있음| D[JSON 읽기 및 검증]
    D -->|실패| E[에러: corrupted_json]
    D -->|성공| F[대화형 선택 UI]
    F -->|취소| G[취소됨]
    F -->|선택| H{Worktree 검증}
    H -->|실패| I[에러: worktree_expired]
    H -->|성공| J[Planner 복원 모드 실행]
    J --> K[체크포인트 정리]
    K --> L[완료]
```

## Execution Instructions (CRITICAL)

When `/restore-context` is invoked, execute these steps in order:

### Step 1: Read Checkpoint File

```python
checkpoint_content = Read(".claude/workflow-checkpoint.json")
```

**If file doesn't exist**, show this error message and EXIT immediately:

```
❌ 체크포인트 파일이 존재하지 않습니다.

복원할 워크플로우가 없습니다.

**가능한 원인**:
- Context compression이 발생하지 않음
- 이미 복원되어 checkpoint 삭제됨
- PreCompact hook이 실행되지 않음

**조치 방법**:
- 새로운 워크플로우를 시작하려면: /wm
- PreCompact hook 설정 확인: cat .claude/settings.json
```

If file exists → Continue to Step 2

### Step 2: Parse and Validate

- Parse JSON content
- Detect version (v1.0 / v3.0 / v4.0) from `version` field
- Validate schema per version

If parse error → Show `corrupted_json` error and exit

### Step 3: Build Options and Show Selection UI (MUST)

**You MUST call `AskUserQuestion`** with options built from checkpoints:

```python
# Build options (newest first, max 4)
options = []
checkpoints = checkpoint_content.get("checkpoints", [checkpoint_content])  # v4 has array, v1/v3 is single

for cp in reversed(checkpoints[-4:]):  # Max 4 options
    summary = cp.get("summary") or cp.get("plan_name") or "Unknown"
    current_work = cp.get("current_work", {})
    status = current_work.get("status", "unknown")
    plan_path = current_work.get("plan_path", "")
    last_agent = current_work.get("last_agent", "")
    completed_phases = cp.get("completed_phases", [])
    timestamp = cp.get("timestamp", "")

    # Label: [status] summary (N phases) - relative_time
    status_badge = f"[{status}]" if status else ""
    phase_count = f"({len(completed_phases)} phases)" if completed_phases else ""

    label = f"{status_badge} {summary} {phase_count}".strip()
    label += f" - {relative_time(timestamp)}"

    # Description: 풍부한 컨텍스트 정보
    plan_name = plan_path.split("/")[-1] if plan_path else "N/A"
    desc_parts = [f"📄 계획: {plan_name}"]
    if completed_phases:
        desc_parts.append(f"✅ 완료: {len(completed_phases)} phases")
    if last_agent:
        desc_parts.append(f"🤖 마지막: {last_agent}")
    desc_parts.append(f"⏰ {timestamp}")

    options.append({
        "label": label,
        "description": " | ".join(desc_parts)
    })

# For single checkpoint: add cancel option
if len(options) == 1:
    options.append({
        "label": "복원 취소",
        "description": "체크포인트를 유지하고 취소합니다"
    })

# ========================================
# MUST CALL AskUserQuestion - THIS IS CRITICAL
# ========================================
answer = AskUserQuestion(questions=[{
    "question": "어떤 체크포인트로 복원할까요?",
    "header": "체크포인트",
    "options": options,
    "multiSelect": False
}])
```

### Step 4: Process User Selection

- If "복원 취소" selected → Exit with message "복원이 취소되었습니다."
- Otherwise → Extract the selected checkpoint data
- Display selected checkpoint info in a table format

### Step 5: Verify Worktree (if applicable)

If checkpoint has `worktree_path`:
```python
# Check if worktree directory still exists
worktree_exists = Bash(f"test -d '{worktree_path}' && echo 'exists'")
if not worktree_exists:
    # Show worktree_expired error
    exit()
```

### Step 6: Invoke Planner in Restoration Mode

If checkpoint has `current_work.plan_path`:
```python
# Re-invoke wm skill with restoration context
Skill("wm", args=f"--restore {plan_path}")
```

Otherwise → Just display the checkpoint info and exit

### Step 7: Cleanup (After Successful Restoration)

After planner confirms restoration:
- Remove the used checkpoint from the FIFO array
- Write updated checkpoint file (or delete if empty)

## Checkpoint Versions

| Version | Format | Description |
|---------|--------|-------------|
| v4.0 | FIFO Array | 최대 5개 체크포인트, 슬롯 선택 |
| v3.0 | Single Object | 단일 체크포인트, current_work 포함 |
| v1.0 | Legacy | plan_name, current_phase 기반 |

## Error Handling

All error messages are in Korean. See [rules/pattern-error-messages.md](rules/rules/pattern-error-messages.md).

| Error | Description |
|-------|-------------|
| `no_checkpoint` | 체크포인트 파일 없음 |
| `corrupted_json` | JSON 파싱 실패 |
| `invalid_schema` | 스키마 검증 실패 |
| `worktree_expired` | Worktree 디렉토리 없음 |
| `planner_invocation_failed` | Planner 실행 실패 |

## Prerequisites

- Checkpoint file: `.claude/workflow-checkpoint.json`
- Valid checkpoint schema (v1/v3/v4)
- Worktree directory (if worktree was used)

## Example Usage

### Interactive Selection (v4)

```
User: /restore-context

┌─ 어떤 체크포인트로 복원할까요? ─────────────────────┐
│ ○ [in_progress] e2e-test (2 phases) - 방금 전      │
│   📄 계획: e2e-test.md | ✅ 완료: 2 phases | ⏰ 14:30│
│                                                     │
│ ○ [completed] code-quality (5 phases) - 2시간 전   │
│   📄 계획: code-quality.md | ✅ 완료: 5 phases      │
│                                                     │
│ ○ Other...                                         │
└────────────────────────────────────────────────────┘

[User selects: "[in_progress] e2e-test (2 phases) - 방금 전"]

📋 선택된 체크포인트 정보
| 항목 | 값 |
|------|-----|
| 계획 이름 | e2e-test-enhancement |
| 상태 | in_progress |
| 저장 시각 | 2026-01-25T14:30:00Z |

🚀 Planner를 복원 모드로 실행합니다...

✅ 워크플로우가 성공적으로 복원되었습니다.
```

## Integration Points

| Hook/Skill | Role |
|------------|------|
| PreCompact Hook | 체크포인트 생성 |
| SessionStart Hook | 복원 안내 메시지 |
| Planner Skill | 복원 모드 처리 |

## Troubleshooting

See [rules/pattern-error-messages.md](rules/rules/pattern-error-messages.md) for detailed error messages and recovery steps.

### Quick Fixes

```bash
# 체크포인트 확인
cat .claude/workflow-checkpoint.json | jq .

# JSON 검증
jq . .claude/workflow-checkpoint.json

# 체크포인트 삭제 후 재시작
rm .claude/workflow-checkpoint.json
/wm "새 작업"
```

## Related Documentation

- Module Index: `rules/_sections.md`
- PreCompact Hook: `.claude/hooks/precompact-save-state.sh`
- SessionStart Hook: `.claude/hooks/session-start-restore-hint.sh`
- Hook Utilities: `.claude/hooks/hook-utils.sh`
