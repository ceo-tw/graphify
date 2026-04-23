#!/bin/bash
set -e
ROOT=.claude/skills/wm-setup/rules

# ── File existence checks ────────────────────────────────────────────────────

for v in binaries graph-data playwright env-vars; do
  test -f "$ROOT/validators/${v}-validator.md" || { echo "MISSING validator: $v"; exit 1; }
  test -f "$ROOT/remediators/${v}-remediation.md" || { echo "MISSING remediator: $v"; exit 1; }
done

# ── Validator interface compliance ───────────────────────────────────────────

for v in binaries graph-data playwright env-vars; do
  f="$ROOT/validators/${v}-validator.md"
  grep -q "Input" "$f"
  grep -q "Output" "$f"
  grep -q "\"counts\"" "$f"
  grep -q "PASS\|FAIL\|WARN\|SKIP" "$f"
done

# ── Remediator 3-mode contract ───────────────────────────────────────────────

for r in binaries graph-data playwright env-vars; do
  f="$ROOT/remediators/${r}-remediation.md"
  grep -q "NEW_SETUP" "$f"
  grep -q "UPDATE" "$f"
  grep -q "VERIFY" "$f"
done

# ── graphify safety guards ───────────────────────────────────────────────────

# binaries-remediation must contain the PyPI prohibition pattern
grep -q "must NOT install from PyPI\|never.*pip install graphifyy\|절대.*graphifyy\|pypi_forbidden\|graphifyy.*forbid\|GRAPHIFY_PYPI_FORBIDDEN" \
  "$ROOT/remediators/binaries-remediation.md" || {
  echo "MISSING: graphify PyPI prohibition guard in binaries-remediation.md"
  exit 1
}

# binaries-remediation must reference the correct fork URL
grep -q "git+https://github.com/ceo-tw/graphify.git" \
  "$ROOT/remediators/binaries-remediation.md" || {
  echo "MISSING: fork git URL in binaries-remediation.md"
  exit 1
}

# binaries-validator must reference pypi_forbidden
grep -q "pypi_forbidden" "$ROOT/validators/binaries-validator.md" || {
  echo "MISSING: pypi_forbidden check in binaries-validator.md"
  exit 1
}

# ── graph-data prereq guard ──────────────────────────────────────────────────

grep -q "jq not installed\|jq.*not.*installed\|binaries-validator\|jq must be installed" \
  "$ROOT/validators/graph-data-validator.md" || {
  echo "MISSING: jq dependency guard in graph-data-validator.md"
  exit 1
}

grep -q "graphify.*not found\|_check_graphify_available\|binaries-remediation" \
  "$ROOT/remediators/graph-data-remediation.md" || {
  echo "MISSING: graphify prereq check in graph-data-remediation.md"
  exit 1
}

# ── env-vars settings.local.json pattern ─────────────────────────────────────

grep -q "settings.local.json" "$ROOT/remediators/env-vars-remediation.md" || {
  echo "MISSING: settings.local.json write in env-vars-remediation.md"
  exit 1
}

grep -q "CLAUDE_PROJECT_DIR" "$ROOT/validators/env-vars-validator.md" || {
  echo "MISSING: CLAUDE_PROJECT_DIR check in env-vars-validator.md"
  exit 1
}

# ── playwright dry-run detection ─────────────────────────────────────────────

grep -q "dry-run\|--dry-run\|would install" "$ROOT/validators/playwright-validator.md" || {
  echo "MISSING: dry-run detection in playwright-validator.md"
  exit 1
}

grep -q "npm install" "$ROOT/remediators/playwright-remediation.md" || {
  echo "MISSING: npm install guidance in playwright-remediation.md"
  exit 1
}

# ── Count validators and remediators (quickstart 7 + new 4 = 11 each) ────────

validator_count=$(ls "$ROOT/validators/" | grep -c "\-validator\.md$")
remediator_count=$(ls "$ROOT/remediators/" | grep -c "\-remediation\.md$")

test "$validator_count" -ge 11 || {
  echo "FAIL: expected >= 11 validators, found $validator_count"
  exit 1
}

test "$remediator_count" -ge 11 || {
  echo "FAIL: expected >= 11 remediators, found $remediator_count"
  exit 1
}

echo ""
echo "Validator count : $validator_count"
echo "Remediator count: $remediator_count"
echo ""
echo "PHASE 3 PASS"
