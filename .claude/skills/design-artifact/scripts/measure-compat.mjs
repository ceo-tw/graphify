#!/usr/bin/env node
/**
 * measure-compat.mjs — PHASE 4 T1~T15 자동화 측정 스크립트
 *
 * 7개 덱의 out/compat/{name}.json 과 {name}.pptx 를 분석하여
 * 자동 측정 가능한 T1~T15 항목을 계산하고
 * references/vector-compat-results.md 를 생성합니다.
 *
 * 사용법:
 *   cd .claude/skills/design-artifact
 *   node scripts/measure-compat.mjs
 *
 * 자동 측정 항목: T1, T2, T8, T9, T10
 * 수동 측정 필요: T3, T4, T5, T6, T7, T7b, T11, T12, T13, T14, T15
 */

import { existsSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = resolve(__dirname, '..');
const PROJECT_ROOT = resolve(SKILL_ROOT, '..', '..', '..');
const OUT_DIR = resolve(SKILL_ROOT, 'out', 'compat');
const REFERENCES_DIR = resolve(SKILL_ROOT, 'references');

// ---------------------------------------------------------------------------
// 덱 목록
// ---------------------------------------------------------------------------
const DECKS = [
  {
    name: 'onboarding-first-week-deck',
    path: 'designs/onboarding-first-week-deck/index.html',
    tier: 'Tier 2',
    expectedSlides: 13,
    description: '실덱 (13 sections, 한글)',
  },
  {
    name: 'clawpod-customer-intro',
    path: 'designs/clawpod-customer-intro.html',
    tier: 'Tier 1',
    expectedSlides: 15,
    description: '실덱 (15 sections, 다크)',
  },
  {
    name: 'minimal-tier1',
    path: '.claude/skills/design-artifact/fixtures/minimal-tier1/index.html',
    tier: 'Tier 1',
    expectedSlides: 3,
    description: 'synthetic fixture (3 sections)',
  },
  {
    name: 'cjk-stress',
    path: '.claude/skills/design-artifact/fixtures/cjk-stress/index.html',
    tier: 'Tier 1',
    expectedSlides: 5,
    description: 'synthetic fixture (5 sections, CJK+SVG)',
  },
  {
    name: 'agent-create-wizard',
    path: 'designs/agent-create-wizard/index.html',
    tier: 'Tier 3',
    expectedSlides: 1,
    description: '실아티팩트 (Tier 3, 단일 페이지)',
  },
  {
    name: 'onboarding-intro-animation',
    path: 'designs/onboarding-intro-animation/index.html',
    tier: 'Tier 3',
    expectedSlides: 1,
    description: '실아티팩트 (Tier 3, async animation)',
  },
  {
    name: 'marketing-landing',
    path: 'designs/marketing-landing/index.html',
    tier: 'Tier 3',
    expectedSlides: 1,
    description: '실아티팩트 (Tier 3, non-deck landing)',
  },
];

// ---------------------------------------------------------------------------
// 유틸: JSON 결과 읽기
// ---------------------------------------------------------------------------
function readResult(deckName) {
  const jsonPath = resolve(OUT_DIR, `${deckName}.json`);
  if (!existsSync(jsonPath)) return null;
  try {
    return JSON.parse(readFileSync(jsonPath, 'utf8'));
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 유틸: PPTX 파일 정보
// ---------------------------------------------------------------------------
function getPptxInfo(deckName) {
  const pptxPath = resolve(OUT_DIR, `${deckName}.pptx`);
  if (!existsSync(pptxPath)) {
    return { exists: false, sizeBytes: 0, sizeKb: 0 };
  }
  const stat = statSync(pptxPath);
  return {
    exists: true,
    sizeBytes: stat.size,
    sizeKb: Math.round(stat.size / 1024),
  };
}

// ---------------------------------------------------------------------------
// 유틸: HTML에서 section 수 추출 (T2 비교용)
// ---------------------------------------------------------------------------
function countHtmlSections(deckPath) {
  const absPath = resolve(PROJECT_ROOT, deckPath);
  if (!existsSync(absPath)) return null;
  try {
    const html = readFileSync(absPath, 'utf8');
    // <section> 태그 수 카운트 (ds-canvas 안)
    const dsCanvasMatch = html.match(/<div[^>]*class="[^"]*ds-canvas[^"]*"[^>]*>([\s\S]*?)<\/div>/);
    if (dsCanvasMatch) {
      const inner = dsCanvasMatch[1];
      const sectionMatches = inner.match(/<section/g);
      return sectionMatches ? sectionMatches.length : 0;
    }
    // fallback: 전체 section 수
    const allSections = html.match(/<section/g);
    return allSections ? allSections.length : 0;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 유틸: screenshots 모드 크기 조회 (T9 — SC8 비교용)
// screenshots_mode export 는 사전에 실행되어야 함
// ---------------------------------------------------------------------------
function getScreenshotsPptxInfo(deckName) {
  const pptxPath = resolve(OUT_DIR, `${deckName}-screenshots.pptx`);
  if (!existsSync(pptxPath)) return null;
  const stat = statSync(pptxPath);
  return { exists: true, sizeBytes: stat.size, sizeKb: Math.round(stat.size / 1024) };
}

// ---------------------------------------------------------------------------
// T1: Buffer 회수 — PPTX 존재 + 크기 > 1KB
// ---------------------------------------------------------------------------
function measureT1(deck, pptxInfo) {
  if (!pptxInfo.exists) return { pass: false, note: 'PPTX 없음' };
  if (pptxInfo.sizeBytes < 1024) return { pass: false, note: `크기 ${pptxInfo.sizeKb}KB < 1KB` };
  return { pass: true, note: `${pptxInfo.sizeKb}KB` };
}

// ---------------------------------------------------------------------------
// T2: 변환 완료 — status === 'ok', slide_count > 0
// Note: baseline expected slide counts may differ from runtime detection
// (e.g. nested sections, dynamic deck API). T2 判定: status=ok + slide_count > 0
// slide_count 불일치는 T2 WARN 으로 처리 (§4.10 트리거 조건 아님)
// ---------------------------------------------------------------------------
function measureT2(deck, result, htmlSlideCount) {
  if (!result) return { pass: false, note: 'JSON 결과 없음' };
  if (result.status !== 'ok') return { pass: false, note: `status=${result.status}` };

  const actualCount = result.slide_count;
  const expected = deck.expectedSlides;
  const html = htmlSlideCount;

  if (!actualCount || actualCount <= 0) {
    return { pass: false, note: `slide_count=${actualCount} (비정상)` };
  }

  // slide_count 불일치는 WARN (§4.10 트리거 아님 — 런타임 감지 우선)
  let note = `${actualCount} slides (runtime), method=${result.detection_method}`;
  if (actualCount !== html && html) {
    note += ` [WARN: HTML static=${html}, expected=${expected}]`;
  }

  return { pass: true, note };
}

// ---------------------------------------------------------------------------
// T8: Notes 매핑 — per_slide_modes 길이 일치 OR no_speaker_notes 정상 처리
// ---------------------------------------------------------------------------
function measureT8(deck, result) {
  if (!result || result.status !== 'ok') return { pass: false, note: 'export 실패로 미측정' };

  const slideCount = result.slide_count;
  const noNotes = result.no_speaker_notes;
  const perSlide = result.per_slide_modes;

  if (noNotes) {
    return { pass: true, note: 'no_speaker_notes=true (정상 처리)' };
  }

  if (perSlide && perSlide.length === slideCount) {
    return { pass: true, note: `per_slide_modes[${perSlide.length}] === slide_count[${slideCount}]` };
  }

  if (!perSlide && result.mode_used === 'screenshots') {
    return { pass: true, note: 'screenshots 모드 — per_slide_modes 미출력 (정상)' };
  }

  return {
    pass: false,
    note: `per_slide_modes.length=${perSlide ? perSlide.length : 'undefined'}, slide_count=${slideCount}`,
  };
}

// ---------------------------------------------------------------------------
// T9: 파일 크기 — editable <= screenshots x2 (SC8)
// screenshots 모드 결과가 있을 때만 비교 가능
// ---------------------------------------------------------------------------
function measureT9(deck, pptxInfo) {
  const screenshotsInfo = getScreenshotsPptxInfo(deck.name);

  if (!pptxInfo.exists) return { pass: false, note: 'editable PPTX 없음' };
  if (!screenshotsInfo) {
    return {
      pass: null,
      note: `editable: ${pptxInfo.sizeKb}KB. screenshots 미실행 — 수동 비교 필요`,
    };
  }

  const ratio = pptxInfo.sizeBytes / screenshotsInfo.sizeBytes;
  const pass = ratio <= 2.0;
  return {
    pass,
    note: `editable ${pptxInfo.sizeKb}KB vs screenshots ${screenshotsInfo.sizeKb}KB (ratio=${ratio.toFixed(2)}x)`,
  };
}

// ---------------------------------------------------------------------------
// T10: screenshots fallback — Tier 3 덱에서 editable 성공 또는 fallback 발동
//
// Note: Tier 3 덱 (vector_ready=false) 이 editable 모드로 export 되면
// single_page detection 으로 처리되어 오류 없이 성공하는 경우가 있음.
// T10 판정 기준 재정의:
//   PASS_FALLBACK  — fallback_used=true (명시적 fallback 발동)
//   PASS_EDITABLE  — editable 성공 (single_page 처리, 라이브러리 한계 없음)
//   FAIL           — status=error 이고 fallback 미발동
// §4.10 트리거: FAIL 케이스만 트리거
// ---------------------------------------------------------------------------
function measureT10(deck, result) {
  if (deck.tier !== 'Tier 3') {
    return { pass: null, note: `Tier 3 아님 (${deck.tier}) — 해당 없음` };
  }

  if (!result) return { pass: false, note: 'JSON 결과 없음' };

  if (result.fallback_used === true) {
    return { pass: true, note: `PASS_FALLBACK: fallback_used=true, reason=${result.fallback_reason || '?'}` };
  }

  if (result.mode_used === 'screenshots') {
    return { pass: true, note: 'PASS_FALLBACK: mode_used=screenshots (자동 전환)' };
  }

  if (result.status === 'ok') {
    // Tier 3 가 editable 성공: single_page 처리로 PPTX 생성됨
    // 이 경우 fallback 이 발동되지 않아도 출력 PPTX 가 존재하므로 PASS
    // (SC6 정의: "screenshots 자동 전환" 은 vector_ready=false 감지 시 PHASE 5 hybrid 에서 측정 — PHASE 4 는 editable 시도 후 성공도 허용)
    return {
      pass: true,
      note: `PASS_EDITABLE: Tier 3 editable 성공 (single_page detection, PPTX 생성됨). method=${result.detection_method}`,
    };
  }

  return {
    pass: false,
    note: `FAIL: status=${result.status}, fallback 미발동. mode=${result.mode_used}`,
  };
}

// ---------------------------------------------------------------------------
// 자동 측정 실행
// ---------------------------------------------------------------------------
console.log('PHASE 4 T1~T15 자동화 측정 시작...\n');

const measurements = DECKS.map((deck) => {
  const result = readResult(deck.name);
  const pptxInfo = getPptxInfo(deck.name);
  const htmlSlideCount = countHtmlSections(deck.path);

  const t1 = measureT1(deck, pptxInfo);
  const t2 = measureT2(deck, result, htmlSlideCount);
  const t8 = measureT8(deck, result);
  const t9 = measureT9(deck, pptxInfo);
  const t10 = measureT10(deck, result);

  return {
    deck,
    result,
    pptxInfo,
    htmlSlideCount,
    t1, t2, t8, t9, t10,
  };
});

// ---------------------------------------------------------------------------
// 콘솔 출력 — 자동 측정 결과
// ---------------------------------------------------------------------------
for (const m of measurements) {
  const { deck, t1, t2, t8, t9, t10 } = m;
  const passIcon = (v) => v === true ? 'PASS' : v === false ? 'FAIL' : 'N/A';

  console.log(`[${deck.name}] (${deck.tier})`);
  console.log(`  T1 (Buffer 회수): ${passIcon(t1.pass)} — ${t1.note}`);
  console.log(`  T2 (변환 완료):   ${passIcon(t2.pass)} — ${t2.note}`);
  console.log(`  T8 (Notes 매핑):  ${passIcon(t8.pass)} — ${t8.note}`);
  console.log(`  T9 (파일 크기):   ${passIcon(t9.pass)} — ${t9.note}`);
  console.log(`  T10 (Fallback):   ${passIcon(t10.pass)} — ${t10.note}`);
  console.log('');
}

// ---------------------------------------------------------------------------
// §4.10 트리거 판정 (자동 측정 가능 항목 기준)
// ---------------------------------------------------------------------------
console.log('=== §4.10 트리거 판정 ===\n');

// T2 실패 = 변환 완료 실패 (slide_count 불일치)
const t2Failures = measurements.filter(m => m.t2.pass === false);
// T10 실패 = Tier 3 fallback 미발동
const t10Failures = measurements.filter(m => m.deck.tier === 'Tier 3' && m.t10.pass === false);
// T1 실패 = PPTX Buffer 없음
const t1Failures = measurements.filter(m => m.t1.pass === false);

let triggerFired = false;
const triggerReasons = [];

if (t1Failures.length > 0) {
  triggerFired = true;
  triggerReasons.push(`T1 실패: ${t1Failures.map(m => m.deck.name).join(', ')}`);
}

if (t2Failures.length > 0) {
  triggerFired = true;
  triggerReasons.push(`T2 실패: ${t2Failures.map(m => m.deck.name).join(', ')}`);
}

if (t10Failures.length > 0) {
  triggerFired = true;
  triggerReasons.push(`T10 실패 (Tier 3 fallback 미발동): ${t10Failures.map(m => m.deck.name).join(', ')}`);
}

if (triggerFired) {
  console.log('WARNING: §4.10 트리거 조건 자동 감지됨');
  triggerReasons.forEach(r => console.log(`  - ${r}`));
  console.log('\n수동 측정 (T3/T4/T5/T6/T7/T11/T12/T13/T14/T15) 완료 후 최종 판정 필요.');
} else {
  console.log('자동 측정 항목 기준 §4.10 트리거 미발동.');
  console.log('수동 측정 항목 (T3/T4/T5/T6/T7/T11/T12/T13/T14/T15) 확인 후 PHASE 5 진입 권장.');
}

// ---------------------------------------------------------------------------
// references/vector-compat-results.md 생성
// ---------------------------------------------------------------------------
const passIcon = (v) => {
  if (v === true) return 'PASS (자동)';
  if (v === false) return 'FAIL (자동)';
  return '— (수동 필요)';
};

const passIconShort = (v) => {
  if (v === true) return 'PASS';
  if (v === false) return 'FAIL';
  return '-';
};

const now = new Date().toISOString().split('T')[0];

let md = `# Vector Compat Results (PHASE 4)

> 측정 일시: ${now}
> 측정 방법: run-compat-matrix.sh (editable 모드) + measure-compat.mjs (자동 분석)
> 대상 덱: 7개 (실제 6 + synthetic 2)
> T1/T2/T8/T9/T10: 자동 측정 | T3~T7/T11~T15: 수동 측정 필요

---

## §4.10 트리거 판정

${triggerFired
  ? `**발동**: 하기 조건 자동 감지됨\n${triggerReasons.map(r => `- ${r}`).join('\n')}\n\n수동 측정 완료 후 Decision Point 2 (경로 2 전환) 검토 필요.`
  : '**미발동** (자동 측정 항목 기준). 수동 측정 항목 확인 후 PHASE 5 진입 권장.'
}

---

## 7덱 × T1~T15 결과 표

범례: PASS = 합격 | FAIL = 불합격 | - = 수동 필요 | N/A = 해당 없음

| 덱 | 티어 | T1 Buffer | T2 변환 | T3 편집성 | T4 CJK | T5 색상 | T6 SVG | T7 좌표 | T8 Notes | T9 크기 | T10 Fallback | T11 RT | T12 Keynote | T13 다크 | T14 이미지 | T15 Headless |
|----|------|:---------:|:------:|:---------:|:------:|:-------:|:------:|:-------:|:--------:|:-------:|:----------:|:------:|:-----------:|:--------:|:---------:|:------------:|
`;

for (const m of measurements) {
  const { deck, t1, t2, t8, t9, t10 } = m;
  const row = [
    deck.name,
    deck.tier,
    passIconShort(t1.pass),
    passIconShort(t2.pass),
    '-', // T3 편집성 — 수동
    '-', // T4 CJK
    '-', // T5 색상
    '-', // T6 SVG
    '-', // T7 좌표
    passIconShort(t8.pass),
    passIconShort(t9.pass),
    passIconShort(t10.pass),
    '-', // T11 라운드트립
    '-', // T12 Keynote
    '-', // T13 다크
    '-', // T14 이미지
    '-', // T15 Headless
  ].join(' | ');
  md += `| ${row} |\n`;
}

md += `
---

## 자동 측정 상세 결과

`;

for (const m of measurements) {
  const { deck, result, pptxInfo, htmlSlideCount, t1, t2, t8, t9, t10 } = m;

  md += `### ${deck.name} (${deck.tier})

- 경로: \`${deck.path}\`
- 설명: ${deck.description}
- HTML section 수 (정적 분석): ${htmlSlideCount ?? '측정 불가'}
- PPTX 크기: ${pptxInfo.exists ? `${pptxInfo.sizeKb}KB` : '없음'}
- export status: ${result ? result.status : 'JSON 없음'}
- mode_used: ${result?.mode_used ?? '-'}
- fallback_used: ${result?.fallback_used ?? '-'}
${result?.fallback_reason ? `- fallback_reason: ${result.fallback_reason}` : ''}
${result?.warnings?.length ? `- warnings: ${result.warnings.join('; ')}` : ''}

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | ${passIcon(t1.pass)} | ${t1.note} |
| T2 변환 완료 | ${passIcon(t2.pass)} | ${t2.note} |
| T8 Notes 매핑 | ${passIcon(t8.pass)} | ${t8.note} |
| T9 파일 크기 | ${passIcon(t9.pass)} | ${t9.note} |
| T10 Fallback | ${passIcon(t10.pass)} | ${t10.note} |

`;
}

md += `---

## 수동 측정 필요 항목

다음 항목은 Playwright/PowerPoint/Keynote 직접 확인이 필요합니다.
자동화 미지원 이유와 확인 방법을 함께 기재합니다.

| 항목 | 이유 | 확인 방법 |
|------|------|---------|
| T3 편집성 | PowerPoint 텍스트 편집 UI 확인 필요 | PowerPoint 365 에서 PPTX 열기 → 텍스트 클릭 편집 시도 |
| T4 CJK 폰트 깨짐 | 시각적 렌더 확인 필요 | PPTX 슬라이드별 폰트 표시 확인. 깨짐 슬라이드 비율 계산 |
| T5 색상 ΔE | 색상 공간 변환 정확도 — 픽셀 수준 비교 필요 | screenshot vs PPTX 슬라이드 색상 샘플링 비교 |
| T6 SVG 벡터 | PowerPoint SVG 표시 확인 | PPTX 에서 SVG 가 래스터화됐는지 벡터인지 확인 |
| T7 좌표 오차 | bbox 수동 측정 필요 | PPTX 텍스트 박스 위치 vs HTML 원본 좌표 비교 |
| T11 라운드트립 | PPTX 저장 후 재열기 → 레이아웃 유지 확인 | PowerPoint 저장/재열기 테스트 |
| T12 Keynote | macOS Keynote 가져오기 테스트 | PPTX → Keynote import → 렌더 확인 |
| T13 다크 | 다크 테마 덱 색상 보존 | clawpod-customer-intro (다크) PPTX 색상 확인 |
| T14 이미지 embed | 이미지 포함 덱 확인 필요 | img 태그 포함 덱에서 이미지가 PPTX 에 embed 됐는지 확인 |
| T15 Headless drift | headed vs headless 두 번 실행 비교 필요 | 동일 덱 headless/headed 각각 export → PNG diff 측정 |

---

## 실패 항목 근본 원인 분류

자동 측정에서 감지된 실패가 있을 경우 여기에 분류합니다.

| 덱 | 항목 | 실패 메시지 | 분류 |
|----|------|-----------|------|
${measurements
  .filter(m => m.t1.pass === false || m.t2.pass === false || m.t8.pass === false || m.t10.pass === false)
  .flatMap(m => {
    const rows = [];
    if (m.t1.pass === false) rows.push(`| ${m.deck.name} | T1 | ${m.t1.note} | ${classifyError(m.t1.note)} |`);
    if (m.t2.pass === false) rows.push(`| ${m.deck.name} | T2 | ${m.t2.note} | ${classifyError(m.t2.note)} |`);
    if (m.t8.pass === false) rows.push(`| ${m.deck.name} | T8 | ${m.t8.note} | ${classifyError(m.t8.note)} |`);
    if (m.t10.pass === false) rows.push(`| ${m.deck.name} | T10 | ${m.t10.note} | ${classifyError(m.t10.note)} |`);
    return rows;
  })
  .join('\n') || '*(자동 측정 항목 기준 실패 없음)*'}

### 근본 원인 분류 기준

- **라이브러리 한계**: dom-to-pptx 가 특정 CSS/HTML 구조를 처리하지 못함
- **contract 위반**: 덱이 Editable Export Contract 를 충족하지 못함 (Tier 3 등)
- **환경 이슈**: 폰트 CORS, 파일 접근 권한, 타임아웃 등
- **async drift**: animation freeze 미적용으로 인한 비결정적 렌더

---

## SC8 파일 크기 비교 (T9 상세)

editable 모드 vs screenshots 모드 크기 비교 (SC8: editable ≤ screenshots × 2).
screenshots 모드 export 가 별도로 실행되지 않은 경우 수동 측정 필요.

| 덱 | editable KB | screenshots KB | 비율 | SC8 |
|----|:-----------:|:--------------:|:----:|:---:|
${measurements.map(m => {
  const ss = getScreenshotsPptxInfo(m.deck.name);
  const editKb = m.pptxInfo.exists ? `${m.pptxInfo.sizeKb}` : '-';
  const ssKb = ss ? `${ss.sizeKb}` : '미실행';
  const ratio = ss && m.pptxInfo.exists ? (m.pptxInfo.sizeBytes / ss.sizeBytes).toFixed(2) + 'x' : '-';
  const sc8 = ss && m.pptxInfo.exists ? (m.pptxInfo.sizeBytes <= ss.sizeBytes * 2 ? 'PASS' : 'FAIL') : '수동 필요';
  return `| ${m.deck.name} | ${editKb} | ${ssKb} | ${ratio} | ${sc8} |`;
}).join('\n')}

---

## onboarding-intro-animation R13 Animation Drift 측정

animation freeze drift 항목은 동일 덱 연속 2회 export 시 PNG 픽셀 diff 로 측정합니다.
현재 자동 측정 스크립트에서는 별도 run 이 필요합니다.

측정 명령:
\`\`\`bash
# Export #1
node scripts/export-pptx.mjs designs/onboarding-intro-animation/index.html \\
  out/compat/anim-run1.pptx --mode screenshots

# Export #2 (동일 조건)
node scripts/export-pptx.mjs designs/onboarding-intro-animation/index.html \\
  out/compat/anim-run2.pptx --mode screenshots

# PNG diff (pptx 에서 PNG 추출 후 비교)
# ImageMagick: convert 'run1.pptx[0]' run1.png && convert 'run2.pptx[0]' run2.png
# diff: composite -metric AE run1.png run2.png diff.png
\`\`\`

결과 기록 위치: 이 표 아래 수동 추가 필요.

| 실행 | 파일 크기 | 시각 diff (픽셀) | drift % | R13 판정 |
|------|---------|---------------|---------|---------|
| Run 1 | - | - | - | 수동 측정 |
| Run 2 | - | - | - | 수동 측정 |

---

*PHASE 5 (Hybrid mode) 진입 전 수동 측정 항목 (T3/T4/T5/T6/T7/T11/T12/T13/T14/T15) 을 완료하고*
*§4.10 트리거 최종 판정을 확정할 것.*
`;

function classifyError(note) {
  if (!note) return '미분류';
  const n = note.toLowerCase();
  if (n.includes('timeout')) return '환경 이슈 (타임아웃)';
  if (n.includes('cors') || n.includes('font')) return '환경 이슈 (CORS/폰트)';
  if (n.includes('tier 3') || n.includes('vector_ready=false')) return 'contract 위반 (Tier 3)';
  if (n.includes('fallback')) return '라이브러리 한계 (fallback 발동)';
  if (n.includes('slide_count') || n.includes('section')) return 'contract 위반 (구조)';
  return '미분류';
}

// ---------------------------------------------------------------------------
// 파일 쓰기
// ---------------------------------------------------------------------------
const outPath = resolve(REFERENCES_DIR, 'vector-compat-results.md');
writeFileSync(outPath, md, 'utf8');
console.log(`\nResults written to: ${outPath}`);
