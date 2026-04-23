# Pattern: Standardized Error Messages

## Purpose

Centralized error messages for consistent user experience.

## Error Message Catalog

### 1. no_checkpoint
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

### 2. file_read_failed
```
❌ 체크포인트 파일을 읽을 수 없습니다.

에러: {error_details}

**조치 방법**:
1. 파일 권한 확인: ls -la .claude/workflow-checkpoint.json
2. 파일이 손상되었다면 삭제: rm .claude/workflow-checkpoint.json
```

### 3. corrupted_json
```
❌ 체크포인트 파일이 손상되었습니다.

JSON 파싱 에러가 발생했습니다: {error_details}

**조치 방법**:
1. 체크포인트 파일 확인: cat .claude/workflow-checkpoint.json
2. JSON 유효성 검사: jq . .claude/workflow-checkpoint.json
3. 수동 수정 가능 여부 확인
4. 수정 불가능하면 삭제 후 재시작: rm .claude/workflow-checkpoint.json
```

### 4. empty_checkpoints
```
❌ 체크포인트 배열이 비어있습니다.

**조치 방법**:
체크포인트 파일을 삭제하고 새로 시작하세요:

rm .claude/workflow-checkpoint.json
/wm "새 작업"
```

### 5. invalid_schema
```
❌ 체크포인트 스키마가 유효하지 않습니다.

누락된 필드: {missing_fields}

**조치 방법**:
체크포인트 파일을 삭제하고 새로 시작하세요:

rm .claude/workflow-checkpoint.json
/wm "재시작"
```

### 6. worktree_expired
```
❌ Worktree가 만료되었습니다.

| 항목 | 값 |
|------|-----|
| 계획 이름 | {plan_name} |
| 만료된 경로 | {worktree_path} |

**복구 방법**:

1. Worktree 재생성:
   git worktree add tree/{plan_name} plan/{plan_name}

2. 마지막 커밋에서 파일 복원:
   cd tree/{plan_name}
   git checkout plan/{plan_name}

3. 복원 재시도:
   /restore-context

**또는** 체크포인트를 삭제하고 처음부터 시작:
rm .claude/workflow-checkpoint.json
/wm "{plan_name} 재시작"
```

### 7. invalid_slot
```
❌ 유효하지 않은 슬롯: {slot_number}

유효 범위: 1-{checkpoint_count}
```

### 8. invalid_other_input
```
❌ 'Other' 입력은 숫자(슬롯 번호)만 지원합니다.
```

### 9. selection_not_found
```
❌ 선택된 옵션을 찾을 수 없습니다.
```

### 10. cancelled
```
❌ 복원이 취소되었습니다.
```

### 11. planner_invocation_failed
```
❌ Planner 복원 중 오류가 발생했습니다.

오류: {error_details}

체크포인트는 보존됩니다. 다시 시도하거나 수동 복구하세요.
```

## Message Format Guidelines

1. **Emoji Prefix**: Use ❌ for errors, ⚠️ for warnings, ✅ for success
2. **Clear Title**: First line describes the error
3. **Context**: Provide relevant variable values in tables
4. **Actions**: Always include "조치 방법" with specific commands
5. **Language**: Korean for descriptions, English for code/paths
