#!/bin/bash
set -euo pipefail

# TaskCompleted Hook (graphify): run a fast Python quality gate on changed files.
# stdin:  { task_id, task_name, task_status, agent_id, team_name }
# exit 0: complete allowed / exit 2: completion blocked + stderr feedback
#
# graphify is a pure-Python project. The gate performs:
#   1. Python AST syntax check via `python -m py_compile` (catches syntax errors)
#   2. `ruff check` on changed files if `ruff` is on PATH (fast lint)
# TypeScript / ESLint checks that existed here previously were tailored to a
# different project and have been removed.

input=$(cat)

# Collect changed files (staged + unstaged vs HEAD)
changed_files=$(git -C "$CLAUDE_PROJECT_DIR" diff --name-only HEAD 2>/dev/null || true)
if [[ -z "$changed_files" ]]; then
  exit 0
fi

# Filter to Python files under the graphify package and tests
py_files=$(echo "$changed_files" | grep -E '\.py$' | grep -E '^(graphify/|tests/|scripts/)' || true)
if [[ -z "$py_files" ]]; then
  exit 0
fi

errors=""

# 1. Syntax check (py_compile) — fastest failure signal
python_bin="${PYTHON:-python3}"
if command -v "$python_bin" >/dev/null 2>&1; then
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    [[ ! -f "$CLAUDE_PROJECT_DIR/$file" ]] && continue
    if ! "$python_bin" -m py_compile "$CLAUDE_PROJECT_DIR/$file" 2> /tmp/graphify-pycompile.err; then
      errors+="[SYNTAX FAIL] $file:\n$(cat /tmp/graphify-pycompile.err)\n\n"
    fi
  done <<< "$py_files"
fi

# 2. ruff lint (optional — pass silently if ruff is not installed)
if command -v ruff >/dev/null 2>&1; then
  ruff_target_list=$(echo "$py_files" | sed "s|^|$CLAUDE_PROJECT_DIR/|")
  if ! ruff_output=$(echo "$ruff_target_list" | xargs ruff check --quiet 2>&1); then
    errors+="[RUFF FAIL]\n$ruff_output\n\n"
  fi
fi

if [[ -n "$errors" ]]; then
  echo -e "graphify quality gate failed - fix these errors before marking task complete:\n\n$errors" >&2
  exit 2
fi

exit 0
