#!/usr/bin/env bash
set -e
SCRIPT=.claude/skills/wm-setup/scripts/check.sh

# Regression: sh invocation must NOT fail with "declare: -A: invalid option"
OUT=$(sh "$SCRIPT" --json 2>&1 || true)
if echo "$OUT" | grep -q "declare: -A: invalid option"; then
  echo "FAIL: declare -A error still present under sh invocation"
  exit 1
fi

# Sanity: bash invocation continues to work
bash "$SCRIPT" --category env-vars --json >/dev/null 2>&1 && echo "OK: bash invocation works"

echo "PASS: check.sh bash-compat regression test"
