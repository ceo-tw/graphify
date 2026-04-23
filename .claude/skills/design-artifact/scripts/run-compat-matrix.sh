#!/bin/bash
# run-compat-matrix.sh — PHASE 4 병렬 호환성 매트릭스 export
#
# 7개 덱(실제 6 + synthetic 2)을 editable 모드로 병렬 export 하고
# 각 결과를 out/compat/{name}.json 에 저장.
#
# 사용법:
#   chmod +x scripts/run-compat-matrix.sh
#   cd .claude/skills/design-artifact
#   ./scripts/run-compat-matrix.sh
#
# 출력:
#   out/compat/{name}.pptx  — PPTX 파일 (editable 모드)
#   out/compat/{name}.json  — export-pptx.mjs JSON 결과 + stderr 로그
#   out/compat/summary.json — 전체 덱 결과 요약
#
# 타임아웃: 덱당 5분 (300초). 초과 시 'TIMEOUT' 으로 기록.
# Exit codes: 0 = 전체 성공, 1 = 일부 실패 (개별 결과 확인 필요)

set -uo pipefail

# ---------------------------------------------------------------------------
# 경로 설정 (이 스크립트는 design-artifact 루트에서 실행 가정)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SKILL_ROOT}/../../../.." && pwd)"

EXPORT_SCRIPT="${SCRIPT_DIR}/export-pptx.mjs"
OUT_DIR="${SKILL_ROOT}/out/compat"

mkdir -p "${OUT_DIR}"

echo "PHASE 4 Compat Matrix — 시작: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Project root: ${PROJECT_ROOT}"
echo "Output dir: ${OUT_DIR}"
echo ""

# ---------------------------------------------------------------------------
# 덱 목록 (7개: 실제 6 + synthetic 2)
# 형식: "relative-path-from-project-root|deck-name"
# ---------------------------------------------------------------------------
declare -a DECKS=(
  "designs/onboarding-first-week-deck/index.html|onboarding-first-week-deck"
  "designs/clawpod-customer-intro.html|clawpod-customer-intro"
  ".claude/skills/design-artifact/fixtures/minimal-tier1/index.html|minimal-tier1"
  ".claude/skills/design-artifact/fixtures/cjk-stress/index.html|cjk-stress"
  "designs/agent-create-wizard/index.html|agent-create-wizard"
  "designs/onboarding-intro-animation/index.html|onboarding-intro-animation"
  "designs/marketing-landing/index.html|marketing-landing"
)

TIMEOUT_SECONDS=300  # 5분

# ---------------------------------------------------------------------------
# 병렬 export 실행
# ---------------------------------------------------------------------------
declare -a PIDS=()
declare -a DECK_NAMES=()
declare -a DECK_PATHS=()

for deck_entry in "${DECKS[@]}"; do
  IFS='|' read -r deck_path deck_name <<< "${deck_entry}"
  abs_deck_path="${PROJECT_ROOT}/${deck_path}"
  out_pptx="${OUT_DIR}/${deck_name}.pptx"
  out_json="${OUT_DIR}/${deck_name}.json"

  DECK_NAMES+=("${deck_name}")
  DECK_PATHS+=("${abs_deck_path}")

  echo "Starting: ${deck_name} (${abs_deck_path})"

  # 각 덱을 백그라운드에서 export
  (
    if [[ ! -f "${abs_deck_path}" ]]; then
      echo "{\"status\":\"error\",\"deck\":\"${deck_name}\",\"error\":\"Input file not found: ${abs_deck_path}\",\"timeout\":false}" > "${out_json}"
      exit 1
    fi

    # timeout 으로 최대 실행 시간 제한
    timeout "${TIMEOUT_SECONDS}" \
      node "${EXPORT_SCRIPT}" \
        --input "${abs_deck_path}" \
        --output "${out_pptx}" \
        --mode editable \
        --verbose \
        2>&1 | head -c 102400 > "${out_json}.raw"  # stderr+stdout 혼합, 최대 100KB

    EXIT_CODE=${PIPESTATUS[0]}

    if [[ ${EXIT_CODE} -eq 124 ]]; then
      # timeout 종료
      echo "{\"status\":\"error\",\"deck\":\"${deck_name}\",\"error\":\"Export timeout (>${TIMEOUT_SECONDS}s)\",\"timeout\":true}" > "${out_json}"
    else
      # 마지막 JSON 라인 추출 (stdout JSON 결과)
      LAST_JSON=$(grep -E '^\{' "${out_json}.raw" | tail -1)
      if [[ -n "${LAST_JSON}" ]]; then
        echo "${LAST_JSON}" > "${out_json}"
      else
        echo "{\"status\":\"error\",\"deck\":\"${deck_name}\",\"error\":\"No JSON output from export-pptx.mjs\",\"raw_preview\":$(head -c 500 "${out_json}.raw" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '\"\"')}" > "${out_json}"
      fi
    fi

    # raw 로그는 보존 (디버깅용)
    mv "${out_json}.raw" "${out_json%.json}.log" 2>/dev/null || true

  ) &
  PIDS+=($!)
done

echo ""
echo "모든 export 백그라운드 시작 완료 (${#PIDS[@]}개 프로세스). 완료 대기 중..."
echo ""

# ---------------------------------------------------------------------------
# 모든 프로세스 완료 대기
# ---------------------------------------------------------------------------
OVERALL_SUCCESS=true
for i in "${!PIDS[@]}"; do
  pid="${PIDS[$i]}"
  name="${DECK_NAMES[$i]}"
  wait "${pid}"
  exit_code=$?
  if [[ ${exit_code} -ne 0 ]]; then
    echo "  [FAIL] ${name} (background process exit ${exit_code})"
    OVERALL_SUCCESS=false
  else
    echo "  [DONE] ${name}"
  fi
done

echo ""
echo "All exports completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ---------------------------------------------------------------------------
# 결과 요약 JSON 생성
# ---------------------------------------------------------------------------
echo "Generating summary..."

python3 - <<'PYEOF'
import json, os, sys

out_dir = os.environ.get('OUT_DIR', '')
if not out_dir:
    import subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(script_dir, '..', 'out', 'compat')

deck_names = [
    'onboarding-first-week-deck',
    'clawpod-customer-intro',
    'minimal-tier1',
    'cjk-stress',
    'agent-create-wizard',
    'onboarding-intro-animation',
    'marketing-landing',
]

summary = {
    'generated_at': __import__('datetime').datetime.now().isoformat(),
    'phase': 'PHASE_4',
    'mode': 'editable',
    'decks': []
}

for name in deck_names:
    json_path = os.path.join(out_dir, f'{name}.json')
    pptx_path = os.path.join(out_dir, f'{name}.pptx')

    entry = {'deck': name, 'pptx_exists': os.path.exists(pptx_path)}

    if os.path.exists(pptx_path):
        entry['pptx_size_bytes'] = os.path.getsize(pptx_path)

    if os.path.exists(json_path):
        try:
            with open(json_path) as f:
                result = json.load(f)
            entry['status'] = result.get('status', 'unknown')
            entry['slide_count'] = result.get('slide_count')
            entry['detection_method'] = result.get('detection_method')
            entry['mode_used'] = result.get('mode_used')
            entry['fallback_used'] = result.get('fallback_used')
            entry['fallback_reason'] = result.get('fallback_reason')
            entry['no_speaker_notes'] = result.get('no_speaker_notes', False)
            entry['warnings_count'] = len(result.get('warnings', []))
            entry['per_slide_modes_count'] = len(result.get('per_slide_modes', []))
            if result.get('status') == 'error':
                entry['error'] = result.get('error', '')
            entry['timeout'] = result.get('timeout', False)
        except Exception as e:
            entry['status'] = 'parse_error'
            entry['error'] = str(e)
    else:
        entry['status'] = 'missing_json'

    summary['decks'].append(entry)

summary_path = os.path.join(out_dir, 'summary.json')
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

# Print summary table
print('\n=== PHASE 4 Export Summary ===')
print(f'{"Deck":<40} {"Status":<12} {"Slides":<8} {"Mode":<12} {"Fallback":<10} {"PPTX KB":<10}')
print('-' * 100)
for d in summary['decks']:
    status = d.get('status', '?')
    slides = d.get('slide_count', '?')
    mode = d.get('mode_used', '?')
    fallback = 'YES' if d.get('fallback_used') else ('NO' if d.get('fallback_used') is False else '?')
    size_kb = f"{d.get('pptx_size_bytes', 0) / 1024:.1f}" if d.get('pptx_size_bytes') else '-'
    timeout = ' [TIMEOUT]' if d.get('timeout') else ''
    print(f'{d["deck"]:<40} {status:<12} {str(slides):<8} {str(mode):<12} {fallback:<10} {size_kb:<10}{timeout}')

print(f'\nSummary written to: {summary_path}')
PYEOF

# ---------------------------------------------------------------------------
# 최종 상태 반환
# ---------------------------------------------------------------------------
if [[ "${OVERALL_SUCCESS}" == "true" ]]; then
  echo ""
  echo "SUCCESS: 모든 덱 export 완료"
  exit 0
else
  echo ""
  echo "PARTIAL FAILURE: 일부 덱 export 실패 (개별 .json 파일 확인)"
  exit 1
fi
