#!/bin/bash
set -e
ROOT=.claude/skills/wm-setup/rules/registries

# 4개 신규 registry 존재 확인
for f in binaries.yaml graph-data.yaml playwright.yaml env-vars.yaml; do
  test -f "$ROOT/$f" || { echo "MISSING: $ROOT/$f"; exit 1; }
done

# graphify 엔트리 검증
grep -q 'id: BIN-001' "$ROOT/binaries.yaml"
grep -q 'pypi_forbidden: true' "$ROOT/binaries.yaml"
grep -q 'git+https://github.com/ceo-tw/graphify.git@v4' "$ROOT/binaries.yaml"
grep -q 'required_features:' "$ROOT/binaries.yaml"

# graph-data 에 _global + 18도메인 항목
test $(grep -c 'id: GRAPH-' "$ROOT/graph-data.yaml") -ge 20

# runtime-checks 확장
grep -q 'graphify-runtime' .claude/skills/wm-setup/rules/onboarding/runtime-checks.yaml
grep -q 'playwright-runtime' .claude/skills/wm-setup/rules/onboarding/runtime-checks.yaml

# _registry-schema.md 에 신규 필드 문서화
grep -q 'pypi_forbidden' .claude/skills/wm-setup/rules/registries/_registry-schema.md
grep -q 'required_features' .claude/skills/wm-setup/rules/registries/_registry-schema.md

echo "PHASE 2 PASS"
