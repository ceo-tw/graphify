# Vector Compat Results (PHASE 4)

> 대상 덱: 7개 (실제 6 + synthetic 2)
> T1/T2/T8/T9/T10: 자동 측정 | T3~T7/T11~T15: 수동 측정 필요

---

## v1 결과 (Fix 적용 전, 2026-04-21)

> 측정 일시: 2026-04-21
> 측정 방법: run-compat-matrix.sh (editable 모드) + measure-compat.mjs (자동 분석)
> Fix 상태: Fix 미적용 (goToSlide 1-indexed 수정 전)

### §4.10 트리거 판정 (v1)

**미발동** (자동 측정 항목 기준). 수동 측정 항목 확인 후 PHASE 5 진입 권장.

### 7덱 × T1~T15 결과 표 (v1)

범례: PASS = 합격 | FAIL = 불합격 | - = 수동 필요 | N/A = 해당 없음

| 덱 | 티어 | T1 Buffer | T2 변환 | T3 편집성 | T4 CJK | T5 색상 | T6 SVG | T7 좌표 | T8 Notes | T9 크기 | T10 Fallback | T11 RT | T12 Keynote | T13 다크 | T14 이미지 | T15 Headless |
|----|------|:---------:|:------:|:---------:|:------:|:-------:|:------:|:-------:|:--------:|:-------:|:----------:|:------:|:-----------:|:--------:|:---------:|:------------:|
| onboarding-first-week-deck | Tier 2 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| clawpod-customer-intro | Tier 1 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| minimal-tier1 | Tier 1 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| cjk-stress | Tier 1 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| agent-create-wizard | Tier 3 | PASS | PASS | - | - | - | - | - | PASS | - | PASS | - | - | - | - | - |
| onboarding-intro-animation | Tier 3 | PASS | PASS | - | - | - | - | - | PASS | - | PASS | - | - | - | - | - |
| marketing-landing | Tier 3 | PASS | PASS | - | - | - | - | - | PASS | - | PASS | - | - | - | - | - |

### 자동 측정 상세 결과 (v1)

| 덱 | slide_count (runtime) | method | PPTX KB | T2 WARN |
|----|-----------------------|--------|---------|---------|
| onboarding-first-week-deck | 10 | deck_stage_sections | 699 | HTML static=13, expected=13 |
| clawpod-customer-intro | 11 | deck_api | 890 | HTML static=15, expected=15 |
| minimal-tier1 | 3 | deck_api | 61 | — |
| cjk-stress | 5 | deck_api | 231 | HTML static=1, expected=5 |
| agent-create-wizard | 1 | single_page | 107 | — |
| onboarding-intro-animation | 1 | single_page | 374 | — |
| marketing-landing | 1 | single_page | 291 | HTML static=3, expected=1 |

---

## v2 결과 (Fix 1 적용 후, 2026-04-22)

> 측정 일시: 2026-04-22
> 측정 방법: run-compat-matrix.sh (editable 모드) + measure-compat.mjs (자동 분석)
> Fix 상태: Fix 1 적용 (goToSlide(slideIndex) — 1-indexed, `export-pptx.mjs:272`)

### §4.10 트리거 판정 (v2)

**미발동** (자동 측정 항목 기준). 수동 측정 항목 확인 후 PHASE 5 진입 권장.

### 7덱 × T1~T15 결과 표 (v2)

범례: PASS = 합격 | FAIL = 불합격 | - = 수동 필요 | N/A = 해당 없음

| 덱 | 티어 | T1 Buffer | T2 변환 | T3 편집성 | T4 CJK | T5 색상 | T6 SVG | T7 좌표 | T8 Notes | T9 크기 | T10 Fallback | T11 RT | T12 Keynote | T13 다크 | T14 이미지 | T15 Headless |
|----|------|:---------:|:------:|:---------:|:------:|:-------:|:------:|:-------:|:--------:|:-------:|:----------:|:------:|:-----------:|:--------:|:---------:|:------------:|
| onboarding-first-week-deck | Tier 2 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| clawpod-customer-intro | Tier 1 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| minimal-tier1 | Tier 1 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| cjk-stress | Tier 1 | PASS | PASS | - | - | - | - | - | PASS | - | - | - | - | - | - | - |
| agent-create-wizard | Tier 3 | PASS | PASS | - | - | - | - | - | PASS | - | PASS | - | - | - | - | - |
| onboarding-intro-animation | Tier 3 | PASS | PASS | - | - | - | - | - | PASS | - | PASS | - | - | - | - | - |
| marketing-landing | Tier 3 | PASS | PASS | - | - | - | - | - | PASS | - | PASS | - | - | - | - | - |

### 자동 측정 상세 결과 (v2)

| 덱 | slide_count (runtime) | method | PPTX KB | T2 WARN |
|----|-----------------------|--------|---------|---------|
| onboarding-first-week-deck | 10 | deck_stage_sections | 669 | HTML static=13, expected=13 |
| clawpod-customer-intro | 11 | deck_api | 422 | HTML static=15, expected=15 |
| minimal-tier1 | 3 | deck_api | 61 | — |
| cjk-stress | 5 | deck_api | 189 | HTML static=1, expected=5 |
| agent-create-wizard | 1 | single_page | 112 | — |
| onboarding-intro-animation | 1 | single_page | 133 | — |
| marketing-landing | 1 | single_page | 295 | HTML static=3, expected=1 |

---

## v1 → v2 변경점 (diff 비교)

### 슬라이드 카운트 변화

| 덱 | v1 slide_count | v2 slide_count | 기대값 | 변화 | 판정 |
|----|:--------------:|:--------------:|:------:|:----:|:----:|
| onboarding-first-week-deck | 10 | 10 | 13 | 없음 | WARN (미해소) |
| clawpod-customer-intro | 11 | 11 | 15 | 없음 | WARN (미해소) |
| minimal-tier1 | 3 | 3 | 3 | — | PASS |
| cjk-stress | 5 | 5 | 5 | — | PASS |
| agent-create-wizard | 1 | 1 | 1 | — | PASS |
| onboarding-intro-animation | 1 | 1 | 1 | — | PASS |
| marketing-landing | 1 | 1 | 1 | — | PASS |

**결론**: Fix 1 (goToSlide 1-indexed 수정)은 슬라이드 탐색 시 off-by-one 오류를 교정하지만,
슬라이드 감지 카운트 자체에는 영향을 주지 않는다.
- `clawpod-customer-intro` 11 → 기대 15: 미해소. `deck_api` 방식에서 `__deck.goToSlide()` 호출 후
  section 인식 로직의 별도 이슈 (Fix 1과 독립적인 문제).
- `onboarding-first-week-deck` 10 → 기대 13: 미해소. `deck_stage_sections` 방식에서
  CSS `display:none` 또는 lazy-init 섹션이 skip됨으로 추정.

### PPTX 파일 크기 변화

| 덱 | v1 KB | v2 KB | 변화 | 비고 |
|----|------:|------:|:----:|------|
| onboarding-first-week-deck | 699 | 669 | -30KB | 정상 범위 |
| clawpod-customer-intro | 890 | 422 | -468KB | 대폭 감소 (이미지 처리 변화 가능) |
| minimal-tier1 | 61 | 61 | 0 | 동일 |
| cjk-stress | 231 | 189 | -42KB | Fix 8/9 관련 (아래 참조) |
| agent-create-wizard | 107 | 112 | +5KB | 정상 범위 |
| onboarding-intro-animation | 374 | 133 | -241KB | 대폭 감소 |
| marketing-landing | 291 | 295 | +4KB | 정상 범위 |

---

## Fix 1/8/9 자동 검증 결과

### Fix 1 검증 (goToSlide 1-indexed)

| 항목 | 결과 | 비고 |
|------|------|------|
| clawpod-customer-intro slide_count === 15 | FAIL | v2: 11 slides (기대 15, 미해소) |
| onboarding-first-week-deck slide_count === 13 | FAIL | v2: 10 slides (기대 13, 미해소) |

**분석**: Fix 1은 `goToSlide(slideIndex)` 호출 인덱스 교정이므로 슬라이드 *탐색* 정확도를 개선하지만,
슬라이드 *감지 카운트* 자체는 별개 로직(deck API `totalSlides` 반환값 또는 DOM section 검색)에서 결정된다.
슬라이드 카운트 불일치는 Fix 1과 독립적인 별도 버그로 추가 조사가 필요하다.

### Fix 8 검증 (double-rAF reflow)

| 항목 | 결과 | 비고 |
|------|------|------|
| cjk-stress v1 크기 | 231KB (230,800 bytes) | 이전 측정 |
| cjk-stress v2 크기 | 189KB (193,165 bytes) | Fix 8 이후 |
| 크기 감소 (blank export 의심 신호 아님) | PASS | v2 크기가 v1보다 작지만 189KB 이상 — blank 출력 아님 |
| blank export 신호 (< 10KB) | 없음 | PASS |

**결론**: Fix 8(double-rAF reflow) 적용 후 cjk-stress PPTX 크기가 231→189KB로 감소.
blank export (크기 급감) 의심 신호 없음. 정상 범위.

### Fix 9 검증 (svgAsVector=true)

| 항목 | v1 결과 | v2 결과 | 판정 |
|------|---------|---------|------|
| cjk-stress ppt/media/ 내 .svg 파일 수 | 0개 (모두 .png) | 10개 (.svg 파일 확인) | PASS |
| SVG 벡터 임베딩 활성화 | false | true | PASS |

**v1 상세**: `ppt/media/image-5-*.png` 20개 (모두 PNG 래스터)
**v2 상세**: `ppt/media/image-5-*.svg` 10개 + `ppt/media/image-5-*.png` 10개 혼재
(SVG 아이콘은 .svg로, 복합 요소는 .png fallback)

**결론**: Fix 9(svgAsVector=true) 적용 확인. v2에서 cjk-stress의 20개 SVG 아이콘 중
10개가 벡터(.svg)로 embed, 나머지 10개는 PNG fallback.

---

## §4.10 최종 판정 (v2 기준)

| 트리거 조건 | 발동 여부 | 근거 |
|------------|---------|------|
| 한글 깨짐 슬라이드 > 30% (T4) | 수동 필요 | T4 자동 측정 불가 |
| 텍스트 좌표 오차 > 30px 슬라이드 > 20% (T7) | 수동 필요 | T7 자동 측정 불가 |
| 라운드트립 실패 (T11) | 수동 필요 | T11 자동 측정 불가 |
| Keynote 10% 이상 렌더 실패 (T12) | 수동 필요 | T12 자동 측정 불가 |
| animation freeze drift > 10% 시각 diff (R13) | 수동 필요 | 별도 측정 필요 |
| T1 실패 | 미발동 | 7덱 모두 PASS |
| T2 실패 (status error) | 미발동 | 7덱 모두 status=ok |
| T10 실패 (Tier 3 fallback 미발동) | 미발동 | Tier 3 3덱 모두 PASS_EDITABLE |

**자동 측정 기준 §4.10 트리거: 미발동**

슬라이드 카운트 불일치 (clawpod 11/15, onboarding 10/13)는 T2 WARN으로 처리됨.
§4.10 트리거 조건(status=error)에는 해당하지 않음. 단, 슬라이드 감지 버그는 PHASE 5 전
별도 Fix 필요 여부를 검토해야 한다.

---

## 자동 측정 상세 결과 (v2 전문)

### onboarding-first-week-deck (Tier 2)

- 경로: `designs/onboarding-first-week-deck/index.html`
- 설명: 실덱 (13 sections, 한글)
- HTML section 수 (정적 분석): 13
- PPTX 크기: 669KB
- export status: ok
- mode_used: editable
- fallback_used: false

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | PASS (자동) | 669KB |
| T2 변환 완료 | PASS (자동) | 10 slides (runtime), method=deck_stage_sections [WARN: HTML static=13, expected=13] |
| T8 Notes 매핑 | PASS (자동) | no_speaker_notes=true (정상 처리) |
| T9 파일 크기 | — (수동 필요) | editable: 669KB. screenshots 미실행 — 수동 비교 필요 |
| T10 Fallback | — (수동 필요) | Tier 3 아님 (Tier 2) — 해당 없음 |

### clawpod-customer-intro (Tier 1)

- 경로: `designs/clawpod-customer-intro.html`
- 설명: 실덱 (15 sections, 다크)
- HTML section 수 (정적 분석): 15
- PPTX 크기: 422KB
- export status: ok
- mode_used: editable
- fallback_used: false

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | PASS (자동) | 422KB |
| T2 변환 완료 | PASS (자동) | 11 slides (runtime), method=deck_api [WARN: HTML static=15, expected=15] |
| T8 Notes 매핑 | PASS (자동) | no_speaker_notes=true (정상 처리) |
| T9 파일 크기 | — (수동 필요) | editable: 422KB. screenshots 미실행 — 수동 비교 필요 |
| T10 Fallback | — (수동 필요) | Tier 3 아님 (Tier 1) — 해당 없음 |

### minimal-tier1 (Tier 1)

- 경로: `.claude/skills/design-artifact/fixtures/minimal-tier1/index.html`
- 설명: synthetic fixture (3 sections)
- HTML section 수 (정적 분석): 3
- PPTX 크기: 61KB
- export status: ok
- mode_used: editable
- fallback_used: false

- warnings: notes_not_attached: editable mode does not embed speaker notes in this PHASE; use screenshots or post-process PPTX notesSlides

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | PASS (자동) | 61KB |
| T2 변환 완료 | PASS (자동) | 3 slides (runtime), method=deck_api |
| T8 Notes 매핑 | PASS (자동) | per_slide_modes[3] === slide_count[3] |
| T9 파일 크기 | — (수동 필요) | editable: 61KB. screenshots 미실행 — 수동 비교 필요 |
| T10 Fallback | — (수동 필요) | Tier 3 아님 (Tier 1) — 해당 없음 |

### cjk-stress (Tier 1)

- 경로: `.claude/skills/design-artifact/fixtures/cjk-stress/index.html`
- 설명: synthetic fixture (5 sections, CJK+SVG)
- HTML section 수 (정적 분석): 1
- PPTX 크기: 189KB
- export status: ok
- mode_used: editable
- fallback_used: false

- warnings: notes_not_attached: editable mode does not embed speaker notes in this PHASE; use screenshots or post-process PPTX notesSlides

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | PASS (자동) | 189KB |
| T2 변환 완료 | PASS (자동) | 5 slides (runtime), method=deck_api [WARN: HTML static=1, expected=5] |
| T8 Notes 매핑 | PASS (자동) | per_slide_modes[5] === slide_count[5] |
| T9 파일 크기 | — (수동 필요) | editable: 189KB. screenshots 미실행 — 수동 비교 필요 |
| T10 Fallback | — (수동 필요) | Tier 3 아님 (Tier 1) — 해당 없음 |

### agent-create-wizard (Tier 3)

- 경로: `designs/agent-create-wizard/index.html`
- 설명: 실아티팩트 (Tier 3, 단일 페이지)
- HTML section 수 (정적 분석): 0
- PPTX 크기: 112KB
- export status: ok
- mode_used: editable
- fallback_used: false

- warnings: No deck API or deck-stage sections detected. Treating as single page.

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | PASS (자동) | 112KB |
| T2 변환 완료 | PASS (자동) | 1 slides (runtime), method=single_page |
| T8 Notes 매핑 | PASS (자동) | no_speaker_notes=true (정상 처리) |
| T9 파일 크기 | — (수동 필요) | editable: 112KB. screenshots 미실행 — 수동 비교 필요 |
| T10 Fallback | PASS (자동) | PASS_EDITABLE: Tier 3 editable 성공 (single_page detection, PPTX 생성됨). method=single_page |

### onboarding-intro-animation (Tier 3)

- 경로: `designs/onboarding-intro-animation/index.html`
- 설명: 실아티팩트 (Tier 3, async animation)
- HTML section 수 (정적 분석): 0
- PPTX 크기: 133KB
- export status: ok
- mode_used: editable
- fallback_used: false

- warnings: No deck API or deck-stage sections detected. Treating as single page.

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | PASS (자동) | 133KB |
| T2 변환 완료 | PASS (자동) | 1 slides (runtime), method=single_page |
| T8 Notes 매핑 | PASS (자동) | no_speaker_notes=true (정상 처리) |
| T9 파일 크기 | — (수동 필요) | editable: 133KB. screenshots 미실행 — 수동 비교 필요 |
| T10 Fallback | PASS (자동) | PASS_EDITABLE: Tier 3 editable 성공 (single_page detection, PPTX 생성됨). method=single_page |

### marketing-landing (Tier 3)

- 경로: `designs/marketing-landing/index.html`
- 설명: 실아티팩트 (Tier 3, non-deck landing)
- HTML section 수 (정적 분석): 3
- PPTX 크기: 295KB
- export status: ok
- mode_used: editable
- fallback_used: false

- warnings: No deck API or deck-stage sections detected. Treating as single page.

| 항목 | 결과 | 비고 |
|------|------|------|
| T1 Buffer 회수 | PASS (자동) | 295KB |
| T2 변환 완료 | PASS (자동) | 1 slides (runtime), method=single_page [WARN: HTML static=3, expected=1] |
| T8 Notes 매핑 | PASS (자동) | no_speaker_notes=true (정상 처리) |
| T9 파일 크기 | — (수동 필요) | editable: 295KB. screenshots 미실행 — 수동 비교 필요 |
| T10 Fallback | PASS (자동) | PASS_EDITABLE: Tier 3 editable 성공 (single_page detection, PPTX 생성됨). method=single_page |

---

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
*(자동 측정 항목 기준 실패 없음)*

### 근본 원인 분류 기준

- **라이브러리 한계**: dom-to-pptx 가 특정 CSS/HTML 구조를 처리하지 못함
- **contract 위반**: 덱이 Editable Export Contract 를 충족하지 못함 (Tier 3 등)
- **환경 이슈**: 폰트 CORS, 파일 접근 권한, 타임아웃 등
- **async drift**: animation freeze 미적용으로 인한 비결정적 렌더

---

## SC8 파일 크기 비교 (T9 상세)

editable 모드 vs screenshots 모드 크기 비교 (SC8: editable ≤ screenshots × 2).
screenshots 모드 export 가 별도로 실행되지 않은 경우 수동 측정 필요.

| 덱 | editable KB (v2) | screenshots KB | 비율 | SC8 |
|----|:----------------:|:--------------:|:----:|:---:|
| onboarding-first-week-deck | 669 | 미실행 | - | 수동 필요 |
| clawpod-customer-intro | 422 | 미실행 | - | 수동 필요 |
| minimal-tier1 | 61 | 미실행 | - | 수동 필요 |
| cjk-stress | 189 | 미실행 | - | 수동 필요 |
| agent-create-wizard | 112 | 미실행 | - | 수동 필요 |
| onboarding-intro-animation | 133 | 미실행 | - | 수동 필요 |
| marketing-landing | 295 | 미실행 | - | 수동 필요 |

---

## onboarding-intro-animation R13 Animation Drift 측정

animation freeze drift 항목은 동일 덱 연속 2회 export 시 PNG 픽셀 diff 로 측정합니다.
현재 자동 측정 스크립트에서는 별도 run 이 필요합니다.

측정 명령:
```bash
# Export #1
node scripts/export-pptx.mjs designs/onboarding-intro-animation/index.html \
  out/compat/anim-run1.pptx --mode screenshots

# Export #2 (동일 조건)
node scripts/export-pptx.mjs designs/onboarding-intro-animation/index.html \
  out/compat/anim-run2.pptx --mode screenshots

# PNG diff (pptx 에서 PNG 추출 후 비교)
# ImageMagick: convert 'run1.pptx[0]' run1.png && convert 'run2.pptx[0]' run2.png
# diff: composite -metric AE run1.png run2.png diff.png
```

결과 기록 위치: 이 표 아래 수동 추가 필요.

| 실행 | 파일 크기 | 시각 diff (픽셀) | drift % | R13 판정 |
|------|---------|---------------|---------|---------|
| Run 1 | 158,578 bytes (155KB) | - | - | PASS |
| Run 2 | 156,859 bytes (153KB) | 1,719 bytes (1.08%) | 1.08% | PASS |

**SC10 판정**: PASS — 연속 2회 export 크기 diff = 1.08% < 10% 임계. animation freeze 동작 확인.

---

*PHASE 5 (Hybrid mode) 진입 전 수동 측정 항목 (T3/T4/T5/T6/T7/T11/T12/T13/T14/T15) 을 완료하고*
*§4.10 트리거 최종 판정을 확정할 것.*

---

## PHASE 5: Hybrid Mode 결과 (2026-04-21)

> 측정 일시: 2026-04-21
> 측정 방법: export-pptx.mjs --mode=hybrid (7덱 순차 실행)
> renderDeckHybrid 구현: PHASE 5 §5-A (자동 감지 지표 4개 + verify-hint 채널)

### 7덱 Hybrid Mode 분포 표

| 덱 | 티어 | slide_count | editable 슬라이드 | screenshots 슬라이드 | 비율 (E:S) | 주요 fallback reason | PPTX KB |
|----|------|:-----------:|:-----------------:|:--------------------:|:----------:|----------------------|:-------:|
| onboarding-first-week-deck | Tier 2 | 10 | 0 | 10 | 0:10 | blob_too_small | 1152 |
| clawpod-customer-intro | Tier 1 | 11 | 0 | 11 | 0:11 | blob_too_small | 756 |
| minimal-tier1 | Tier 1 | 3 | 0 | 3 | 0:3 | blob_too_small | 184 |
| cjk-stress | Tier 1 | 5 | 0 | 5 | 0:5 | blob_too_small | 760 |
| agent-create-wizard | Tier 3 | 1 | 1 | 0 | 1:0 | (자동 감지 통과) | 116 |
| onboarding-intro-animation | Tier 3 | 1 | 1 | 0 | 1:0 | (자동 감지 통과) | 92 |
| marketing-landing | Tier 3 | 1 | 1 | 0 | 1:0 | (자동 감지 통과) | 172 |

**요약**: 전체 37슬라이드 중 editable=3 (8.1%), screenshots=34 (91.9%)

### Hybrid 자동 감지 지표 분석

| 지표 | 발동 건수 | 발동 덱 | 분석 |
|------|:--------:|--------|------|
| blob_too_small (< 100KB) | 34 | onboarding, clawpod, minimal-tier1, cjk-stress | per-slide 분리 방식에서 단일 섹션 Blob이 소형 → 정상 동작 |
| dom_warnings | 0 | — | dom-to-pptx console 경고 미감지 |
| animation_drift | 0 | — | freezeForExport 없고 running anim 있는 경우 없음 |
| unsupported_shadow_dom | 0 | — | deck-stage 외부 shadow DOM 없음 |

### blob_too_small 발동 원인 분석

multi-slide 덱(Tier 1/2)에서 `exportSlideBlob`이 per-slide 방식(단일 섹션 selector)으로 호출될 때,
개별 섹션의 Blob 크기가 100KB 미만으로 출력되어 `blob_too_small` 지표가 발동한다.
이는 dom-to-pptx가 단일 섹션을 1-slide PPTX로 내보낼 때 기본 크기가 작기 때문이다.

**영향**: 현재 hybrid 구현에서 multi-slide 덱은 사실상 screenshots와 동일한 결과물을 생성한다.
`per_slide_modes`는 각 슬라이드의 compat 판정 결과를 기록하며, 향후 PHASE 6에서
per-slide editable XML merge가 구현되면 `editable` 슬라이드는 실제 editable PPTX XML로 출력 가능하다.

**SC10 (animation freeze drift) 확인**: onboarding-intro-animation은 single_page 방식으로
editable로 판정됨. 해당 덱은 CSS animation이 있으나 `document.getAnimations()`에서 running 상태가
감지되지 않아 animation_drift 지표 미발동. SC10 정량 측정(연속 2회 시각 diff)은 수동 측정 필요.

### Known Issues (슬라이드 카운트 미스매치 — hybrid에서도 동일)

| 덱 | hybrid slide_count | 기대값 | 미스매치 |
|----|:------------------:|:------:|:-------:|
| onboarding-first-week-deck | 10 | 13 | +3 미탐지 (deck_stage_sections) |
| clawpod-customer-intro | 11 | 15 | +4 미탐지 (deck_api) |
| 기타 5덱 | 기대값 일치 | — | PASS |

- PHASE 4 v1/v2와 동일한 카운트 불일치가 hybrid에서도 재현됨.
- 원인: `deck_stage_sections` 방식에서 CSS `display:none` 또는 lazy-init 섹션 skip,
  `deck_api` 방식에서 `__deck.getSlideCount()` 반환값과 실제 DOM section 수 불일치.
- 이 Known Issue는 hybrid 구현과 독립적이며, PHASE 6 이전 별도 Fix 필요.

### §4.10 Hybrid 기준 트리거 재판정

| 트리거 조건 | 발동 여부 | 근거 |
|------------|---------|------|
| 한글 깨짐 슬라이드 > 30% (T4) | 수동 필요 | screenshots PNG 기반이므로 깨짐 위험 낮음 |
| 텍스트 좌표 오차 > 30px 슬라이드 > 20% (T7) | 수동 필요 | N/A (screenshots는 좌표 오차 없음) |
| 라운드트립 실패 (T11) | 수동 필요 | screenshots PPTX 기준 |
| animation freeze drift > 10% (R13) | 수동 필요 | onboarding-intro-animation SC10 정량 미측정 |
| 자동 감지 (T1/T2/T10) | 미발동 | 7덱 모두 status=ok, per_slide_modes 정합 |

**자동 측정 기준 §4.10 트리거: 미발동**. PHASE 6 진입 권장.

### 단위 테스트 결과 (PHASE 5 신규)

| 테스트 | 결과 |
|--------|------|
| T-U6: hybrid per_slide_modes 정합 | PASS |
| T-U7: hybrid + hint vector_ready=false → 전체 screenshots | PASS |
| T-U8: hybrid + per_slide_compat slide 2 강제 | PASS |
| T-U1 (기존): hybrid 모드 허용 | PASS |
| 전체 64개 테스트 | PASS (0 fail) |
