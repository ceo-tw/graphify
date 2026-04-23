#!/bin/bash
#
# wm-plan-gate.sh - PreToolUse(ExitPlanMode) skill-scoped hook
#
# wm skill이 활성화된 동안에만 실행된다.
# 현재 session_id에 매핑된 plan 파일을 찾아 필수 섹션을 검증한다.
#
# 검증 조건:
#   1. session marker 존재 (이 세션에서 plan을 작성했는지)
#   2. plan 파일 존재
#   3. Simple 타입 예외: "execution skip" 키워드 있으면 통과
#   4. Section 1 (문제 정의) 존재
#   5. Section 2 (상세 요구사항) 존재
#   6. 최소 2개 체크박스
#

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
PROJECT_ROOT=$(echo "$INPUT" | jq -r '.cwd // empty')
SESSIONS_DIR="${PROJECT_ROOT}/.claude/plans/.wm-sessions"
MARKER="${SESSIONS_DIR}/${SESSION_ID}"

# 1. session marker 확인
if [[ ! -f "$MARKER" ]]; then
  echo "BLOCKED: wm 세션에서 plan 문서를 먼저 작성하세요. (.claude/plans/ 에 .md 파일을 Write)" >&2
  exit 2
fi

PLAN_FILE=$(cat "$MARKER")

# 2. plan 파일 존재 확인
if [[ ! -f "$PLAN_FILE" ]]; then
  echo "BLOCKED: 기록된 plan 파일이 존재하지 않습니다: $PLAN_FILE" >&2
  exit 2
fi

# 3. Simple 타입 예외: "execution skip" 키워드 있으면 통과
if grep -q 'execution skip' "$PLAN_FILE"; then
  exit 0
fi

# 4. Section 1 검증
if ! grep -qE '^##\s+(1\.|1\s|Problem|문제)' "$PLAN_FILE"; then
  echo "BLOCKED: plan에 Section 1 (문제 정의)이 없습니다." >&2
  exit 2
fi

# 5. Section 2 검증
if ! grep -qE '^##\s+(2\.|2\s)' "$PLAN_FILE"; then
  echo "BLOCKED: plan에 Section 2 (상세 요구사항)가 없습니다." >&2
  exit 2
fi

# 6. 체크박스 최소 2개
CHECKBOX_COUNT=$(grep -c '^\s*- \[ \]' "$PLAN_FILE" || echo "0")
if [[ "$CHECKBOX_COUNT" -lt 2 ]]; then
  echo "BLOCKED: 체크박스가 ${CHECKBOX_COUNT}개뿐입니다 (최소 2개 필요)." >&2
  exit 2
fi

exit 0
