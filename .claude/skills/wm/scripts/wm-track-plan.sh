#!/bin/bash
#
# wm-track-plan.sh - PostToolUse(Write) skill-scoped hook
#
# Write로 .claude/plans/*.md 파일이 작성되면 session_id -> plan_path 매핑을 기록한다.
# 다중 세션에서도 각 세션의 plan 파일을 정확히 식별하기 위한 추적 메커니즘.
#

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')

# .claude/plans/ 내 .md 파일인지 확인
if [[ "$FILE_PATH" == *".claude/plans/"* && "$FILE_PATH" == *.md ]]; then
  # .wm-sessions 하위 파일은 제외
  if [[ "$FILE_PATH" == *".wm-sessions"* ]]; then
    exit 0
  fi

  SESSIONS_DIR="$(dirname "$FILE_PATH")/.wm-sessions"
  mkdir -p "$SESSIONS_DIR"
  echo "$FILE_PATH" > "$SESSIONS_DIR/$SESSION_ID"
fi

exit 0
