#!/bin/bash
set -e
ROOT=.claude/skills/wm-setup/rules

echo "=== PHASE 4 Tests: Orchestrator 12-module expansion + 3-mode pipeline ==="

# orchestrator 12모듈 확장 확인
echo "[1/8] Checking new module IDs exist in validation-orchestrator.md..."
grep -q 'binaries' "$ROOT/orchestration/validation-orchestrator.md"
grep -q 'graph-data' "$ROOT/orchestration/validation-orchestrator.md"
grep -q 'playwright' "$ROOT/orchestration/validation-orchestrator.md"
grep -q 'env-vars' "$ROOT/orchestration/validation-orchestrator.md"
grep -q 'runtime-checks' "$ROOT/orchestration/validation-orchestrator.md"
echo "  PASS: all new module IDs found"

# blocking_items: [BIN-001] 존재
echo "[2/8] Checking BIN-001 blocking item declaration..."
grep -q 'BIN-001' "$ROOT/orchestration/validation-orchestrator.md"
echo "  PASS: BIN-001 found"

# depends_on: [binaries] 존재 (graph-data 의존성)
echo "[3/8] Checking graph-data depends_on binaries..."
grep -q 'depends_on.*\[.*binaries.*\]\|dependsOn.*binaries\|\"binaries\"\]' "$ROOT/orchestration/validation-orchestrator.md"
echo "  PASS: graph-data depends_on binaries found"

# 모듈 12개 선언 확인 (YAML definitions 섹션)
echo "[4/8] Checking 12 module declarations in YAML block..."
count=$(grep -cE '^\s+- order: [0-9]+' "$ROOT/orchestration/validation-orchestrator.md" || true)
if [ "$count" -lt 12 ]; then
  echo "  FAIL: expected >= 12 module declarations, got $count"
  exit 1
fi
echo "  PASS: found $count module declarations (>= 12)"

# VERIFY 모드 전용 runtime-checks 명시
echo "[5/8] Checking runtime-checks is VERIFY mode only..."
grep -q 'mode_scope.*VERIFY\]\|modeScope.*VERIFY\|VERIFY.*only\|VERIFY mode only' "$ROOT/orchestration/validation-orchestrator.md"
echo "  PASS: runtime-checks VERIFY-only flag found"

# 3-mode process 문서 업데이트 확인
echo "[6/8] Checking process files reference new modules..."
for p in new-setup update verify; do
  f="$ROOT/processes/${p}.md"
  if ! grep -q 'binaries\|graph-data\|playwright' "$f"; then
    echo "  FAIL: $f does not mention new modules (binaries/graph-data/playwright)"
    exit 1
  fi
  echo "  PASS: $f references new wm-specific modules"
done

# 12모듈 참조 (숫자 또는 텍스트)
echo "[7/8] Checking process files reference 12 modules..."
for p in new-setup update verify; do
  f="$ROOT/processes/${p}.md"
  if ! grep -qE '12.module|12-module|12 모듈|Module.*11|Module.*12|order: 12' "$f"; then
    echo "  FAIL: $f does not reference 12-module pipeline"
    exit 1
  fi
  echo "  PASS: $f references 12-module pipeline"
done

# UPDATE mode 4-option interaction pattern 확인
echo "[8/8] Checking UPDATE mode has 4-option interaction pattern..."
f="$ROOT/processes/update.md"
if ! grep -q 'Auto install all\|Install hard only\|Show commands\|Cancel' "$f"; then
  echo "  FAIL: $f missing 4-option interaction pattern"
  exit 1
fi
echo "  PASS: UPDATE mode 4-option pattern found"

echo ""
echo "=== PHASE 4 PASS ==="
