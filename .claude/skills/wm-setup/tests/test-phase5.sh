#!/bin/bash
# test-phase5.sh — Phase 5 TDD validation
# Tests: SKILL.md, scripts/check.sh, scripts/install.sh

set -e

ROOT=".claude/skills/wm-setup"
PASS=0
FAIL=0

check() {
  local desc="$1"
  shift
  if "$@" 2>/dev/null; then
    PASS=$((PASS+1))
    echo "  [PASS] ${desc}"
  else
    FAIL=$((FAIL+1))
    echo "  [FAIL] ${desc}"
  fi
}

echo "=== PHASE 5 Tests ==="
echo ""

# ── SKILL.md checks ───────────────────────────────────────────────────────────
echo "[SKILL.md]"

check "frontmatter: name: wm-setup" \
  grep -q '^name: wm-setup' "${ROOT}/SKILL.md"

check "frontmatter: user-invocable: true" \
  grep -q 'user-invocable: true' "${ROOT}/SKILL.md"

check "invocation: /wm-setup present" \
  grep -q '/wm-setup' "${ROOT}/SKILL.md"

check "modes: NEW_SETUP present" \
  grep -q 'NEW_SETUP' "${ROOT}/SKILL.md"

check "modes: UPDATE present" \
  grep -q 'UPDATE' "${ROOT}/SKILL.md"

check "modes: VERIFY present" \
  grep -q 'VERIFY' "${ROOT}/SKILL.md"

check "Step 0: Mode Detection present" \
  grep -qE 'Step 0.*Mode Detection|Mode Detection' "${ROOT}/SKILL.md"

check "Step 4: AskUserQuestion present" \
  grep -q 'AskUserQuestion' "${ROOT}/SKILL.md"

check "consent: Auto install all" \
  grep -q 'Auto install all' "${ROOT}/SKILL.md"

check "consent: Install hard only" \
  grep -q 'Install hard only' "${ROOT}/SKILL.md"

check "consent: Show install commands" \
  grep -q 'Show install commands' "${ROOT}/SKILL.md"

check "consent: Cancel" \
  grep -q 'Cancel' "${ROOT}/SKILL.md"

check "graphify: ceo-tw fork mentioned" \
  grep -q 'ceo-tw fork' "${ROOT}/SKILL.md"

check "graphify: PyPI forbidden mentioned" \
  grep -qE 'NEVER install from PyPI|pip install graphifyy' "${ROOT}/SKILL.md"

check "graphify: v0.5.x version requirement" \
  grep -q '0\.5\.' "${ROOT}/SKILL.md"

check "final verdicts: SOFT FAIL only" \
  grep -q 'degraded mode' "${ROOT}/SKILL.md"

check "final verdicts: HARD FAIL" \
  grep -q 'cannot proceed' "${ROOT}/SKILL.md"

check "status table: HARD column" \
  grep -q 'HARD' "${ROOT}/SKILL.md"

check "status table: SOFT column" \
  grep -q 'SOFT' "${ROOT}/SKILL.md"

check "status table: install_command in table" \
  grep -q 'Install Command' "${ROOT}/SKILL.md"

check "status table: referenced_by in table" \
  grep -q 'Referenced By' "${ROOT}/SKILL.md"

echo ""

# ── scripts/ existence and permissions ───────────────────────────────────────
echo "[scripts/ structure]"

check "check.sh exists" \
  test -f "${ROOT}/scripts/check.sh"

check "install.sh exists" \
  test -f "${ROOT}/scripts/install.sh"

check "_lib.sh exists" \
  test -f "${ROOT}/scripts/_lib.sh"

check "check.sh is executable" \
  test -x "${ROOT}/scripts/check.sh"

check "install.sh is executable" \
  test -x "${ROOT}/scripts/install.sh"

echo ""

# ── bash syntax validation ────────────────────────────────────────────────────
echo "[bash syntax]"

check "check.sh syntax valid" \
  bash -n "${ROOT}/scripts/check.sh"

check "install.sh syntax valid" \
  bash -n "${ROOT}/scripts/install.sh"

check "_lib.sh syntax valid" \
  bash -n "${ROOT}/scripts/_lib.sh"

echo ""

# ── graphifyy PyPI guard ──────────────────────────────────────────────────────
echo "[PyPI guard]"

check "install.sh: graphifyy guard (pypi_forbidden or must not install from PyPI or graphifyy)" \
  grep -qE 'graphifyy|pypi_forbidden|must not install from PyPI|PyPI.*blocked|pip install graphifyy.*blocked' "${ROOT}/scripts/install.sh"

check "_lib.sh: pypi_guard function exists" \
  grep -q 'pypi_guard' "${ROOT}/scripts/_lib.sh"

check "install.sh: calls pypi_guard" \
  grep -q 'pypi_guard' "${ROOT}/scripts/install.sh"

echo ""

# ── check.sh options ─────────────────────────────────────────────────────────
echo "[check.sh options]"

check "check.sh: --json option" \
  grep -q '\-\-json' "${ROOT}/scripts/check.sh"

check "check.sh: --category option" \
  grep -q '\-\-category' "${ROOT}/scripts/check.sh"

check "check.sh: --module option" \
  grep -q '\-\-module' "${ROOT}/scripts/check.sh"

check "check.sh: exit code logic (EXIT_HARD_FAIL)" \
  grep -q 'EXIT_HARD_FAIL\|exit.*1\|exit.*2' "${ROOT}/scripts/check.sh"

echo ""

# ── install.sh options ───────────────────────────────────────────────────────
echo "[install.sh options]"

check "install.sh: --mode option" \
  grep -q '\-\-mode' "${ROOT}/scripts/install.sh"

check "install.sh: --ids option" \
  grep -q '\-\-ids' "${ROOT}/scripts/install.sh"

check "install.sh: --dry-run option" \
  grep -q '\-\-dry-run' "${ROOT}/scripts/install.sh"

check "install.sh: dependency order (python3.12 before graphify)" \
  grep -q 'BIN-003.*python3.12\|python3.12.*before\|dependency order' "${ROOT}/scripts/install.sh"

check "install.sh: log to logs/ directory" \
  grep -q 'logs/' "${ROOT}/scripts/install.sh"

echo ""

# ── install.sh dry-run sanity ─────────────────────────────────────────────────
echo "[install.sh dry-run]"

if "${ROOT}/scripts/install.sh" --dry-run --ids BIN-002 2>&1 | head -20 | grep -qiE 'jq|brew|dry.run|install|BIN-002|bash 4'; then
  PASS=$((PASS+1))
  echo "  [PASS] install.sh --dry-run --ids BIN-002 outputs something useful"
else
  FAIL=$((FAIL+1))
  echo "  [FAIL] install.sh --dry-run --ids BIN-002 outputs something useful"
fi

echo ""

# ── logs .gitignore ───────────────────────────────────────────────────────────
echo "[logs .gitignore]"

check "logs/.gitignore exists" \
  test -f "${ROOT}/logs/.gitignore"

check "logs/.gitignore: *.log excluded" \
  grep -q '\*.log' "${ROOT}/logs/.gitignore"

check "logs/.gitignore: itself preserved (!.gitignore)" \
  grep -q '!.gitignore' "${ROOT}/logs/.gitignore"

echo ""

# ── Summary ──────────────────────────────────────────────────────────────────
echo "════════════════════════════════"
echo "Results: PASS=${PASS}  FAIL=${FAIL}"
echo ""

if [ "${FAIL}" -eq 0 ]; then
  echo "PHASE 5 PASS"
  exit 0
else
  echo "PHASE 5 FAIL (${FAIL} checks failed)"
  exit 1
fi
