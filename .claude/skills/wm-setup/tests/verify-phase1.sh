#!/usr/bin/env bash
set -e

# PHASE 1 verification script for wm-setup skill scaffold
# Run from project root: bash scripts/verify-phase1.sh

ROOT=.claude/skills/wm-setup

echo "Checking wm-setup scaffold..."

# SKILL.md exists
test -f $ROOT/SKILL.md && echo "  [OK] SKILL.md"

# Directory structure
test -d $ROOT/rules/registries && echo "  [OK] rules/registries/"
test -d $ROOT/rules/validators && echo "  [OK] rules/validators/"
test -d $ROOT/rules/remediators && echo "  [OK] rules/remediators/"
test -d $ROOT/rules/orchestration && echo "  [OK] rules/orchestration/"
test -d $ROOT/rules/components && echo "  [OK] rules/components/"
test -d $ROOT/rules/onboarding && echo "  [OK] rules/onboarding/"
test -d $ROOT/rules/processes && echo "  [OK] rules/processes/"

# Key files
test -f $ROOT/rules/registries/_registry-schema.md && echo "  [OK] registries/_registry-schema.md"
test -f $ROOT/rules/validators/_validator-interface.md && echo "  [OK] validators/_validator-interface.md"
test -f $ROOT/rules/remediators/_remediation-interface.md && echo "  [OK] remediators/_remediation-interface.md"

# No quickstart references remain (excluding allowed comment/deprecation patterns)
REMAINING=$(grep -rE '(skills/quickstart|name: quickstart)' $ROOT --include='*.md' --include='*.yaml' \
  | grep -v '# 이관\|# from quickstart\|이전.*quickstart\|deprecated\|Replaces' || true)
# Also check for /quickstart as a skill invocation (not in deprecation/description context)
REMAINING2=$(grep -rE '/quickstart' $ROOT --include='*.md' --include='*.yaml' \
  | grep -v '# 이관\|# from quickstart\|이전.*quickstart\|deprecated\|Replaces\|/quickstart\.' || true)
REMAINING_ALL="${REMAINING}${REMAINING2}"
if [ -n "$REMAINING_ALL" ]; then
  echo "  [FAIL] quickstart references remain:"
  echo "$REMAINING_ALL"
  exit 1
else
  echo "  [OK] No forbidden quickstart references"
fi

# SKILL.md frontmatter checks
grep -q '^name: wm-setup' $ROOT/SKILL.md && echo "  [OK] SKILL.md name: wm-setup"
grep -q 'ceo-tw fork' $ROOT/SKILL.md && echo "  [OK] SKILL.md mentions ceo-tw fork"

echo ""
echo "PHASE 1 PASS"
