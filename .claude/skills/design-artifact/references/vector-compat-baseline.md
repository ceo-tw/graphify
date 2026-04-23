# Vector Compat Baseline (PHASE 1)

> 측정 일시: 2026-04-21
> 측정 방법: 정적 HTML 소스 분석 (`measure-baseline.mjs --static`)
> PHASE 4에서 Playwright 런타임 측정으로 교체 예정

## 요약

| 지표 | 값 |
|------|----|
| 전체 덱 수 | 7개 (6개 HTML + 1개 디렉토리 잔재) |
| vector_ready=true | 0/7 (0%) |
| vector_tier1=true | 1/7 (clawpod-customer-intro.html만) |
| animation_freezable=false | 4/6 측정 가능 덱 (R13 위험 높음) |
| cors_ok=false | 5/6 측정 가능 덱 (crossorigin 미설정) |

## 덱별 체크 항목 매트릭스

측정 방법 범례: S = 정적 분석, P = Playwright 런타임 (PHASE 4), - = 해당 없음/제외

| 덱 | 티어 | vector_tier1 | vector_structure_ok | vector_shadow_dom_ok | vector_cors_ok | vector_animation_freezable | vector_ready | 마이그레이션 필요 |
|----|------|:---:|:---:|:---:|:---:|:---:|:---:|------|
| onboarding-first-week-deck | Tier 2 | false (S) | true (S) | true (S) | false (S) | false (S) | false | 필수 |
| clawpod-customer-intro.html | Tier 1 | true (S) | true (S) | true (S) | false (S) | true (S) | false | 권장 |
| agent-create-wizard | Tier 3 | false (S) | false (S) | true (S) | false (S) | false (S) | false | 불필요 (screenshots fallback) |
| marketing-landing | Tier 3 | false (S) | false (S) | true (S) | false (S) | true (S) | false | 불필요 (screenshots fallback) |
| onboarding-intro-animation | Tier 3 | false (S) | false (S) | true (S) | true (S) | false (S) | false | 불필요 (screenshots fallback) |
| payment-flow-wireframe | Tier 3 | false (S) | false (S) | true (S) | true (S) | false (S) | false | 불필요 (screenshots fallback) |
| clawpod-customer-intro/ (디렉토리) | N/A | — | — | — | — | — | — | 제외 (index.html 없음, R15 확인 완료) |

## 덱별 상세

### onboarding-first-week-deck (Tier 2)

- 경로: `designs/onboarding-first-week-deck/index.html`
- 슬라이드 수: 13개 section
- **vector_tier1=false**: `window.__deck` 객체가 선언되어 있으나 `getSlideCount` / `goToSlide` 함수가 미노출. Tier 1 API 추가 필요.
- **vector_structure_ok=true**: `<deck-stage>` + `<section>` + 1920 캔버스 확인
- **vector_shadow_dom_ok=true**: `attachShadow` 사용 없음
- **vector_cors_ok=false**: 외부 리소스 1개에 `crossorigin="anonymous"` 미설정 (웹폰트 추정)
- **vector_animation_freezable=false (R13 WARN)**: CSS animation 사용. `freezeForExport` hook 없음. 500ms fallback 적용 예정.
- **마이그레이션 분류: 필수** — Tier 1 API 추가 + freeze hook + crossorigin 권장
- PHASE 6 마이그레이션 가이드 대상 (`tier2-to-tier1-migration.md`)

### clawpod-customer-intro.html (Tier 1)

- 경로: `designs/clawpod-customer-intro.html` (단일 파일 75KB, canonical)
- 슬라이드 수: 15개 section
- **vector_tier1=true**: `window.__deck.getSlideCount`, `goToSlide` 구현 완료 (line 475~)
- **vector_structure_ok=true**: `<deck-stage>` + `<section>` + 1920 확인
- **vector_shadow_dom_ok=true**: `attachShadow` 사용 없음
- **vector_cors_ok=false**: 외부 리소스 1개에 `crossorigin` 미설정 (웹폰트 추정)
- **vector_animation_freezable=true**: rAF/setInterval/CSS animation 미감지
- **마이그레이션 분류: 권장** — `crossorigin="anonymous"` 추가로 `vector_ready=true` 달성 가능
- PHASE 2의 PoC 대상 덱 (클로폴 인트로, 이미 Tier 1)

### agent-create-wizard (Tier 3)

- 경로: `designs/agent-create-wizard/index.html`
- **vector_tier1=false**: `window.__deck` 없음
- **vector_structure_ok=false**: `<deck-stage>` 없음, 1920 캔버스 없음 (와이어프레임)
- **vector_cors_ok=false**: 외부 리소스 2개에 `crossorigin` 미설정
- **vector_animation_freezable=false (R13 WARN)**: rAF 또는 CSS animation 사용
- **마이그레이션 분류: 불필요** — Tier 3 비덱 페이지. editable 시도 없이 screenshots fallback 강제 (PHASE 5)
- plan §4.5: `vector_ready=false` 감지 → screenshots 자동 fallback 검증 대상

### marketing-landing (Tier 3)

- 경로: `designs/marketing-landing/index.html`
- **vector_tier1=false**: `window.__deck` 없음
- **vector_structure_ok=false**: `<deck-stage>` 없음 (랜딩 페이지, section 3개)
- **vector_cors_ok=false**: 외부 리소스 2개에 `crossorigin` 미설정
- **vector_animation_freezable=true**: 활성 animation 미감지
- **마이그레이션 분류: 불필요** — 비덱 랜딩 페이지. screenshots fallback 전용.
- plan §4.7: non-deck fallback 자연스러움 검증 대상

### onboarding-intro-animation (Tier 3)

- 경로: `designs/onboarding-intro-animation/index.html`
- **vector_tier1=false**: `window.__deck` 없음
- **vector_structure_ok=false**: `<deck-stage>` 없음 (애니메이션 전용 페이지)
- **vector_cors_ok=true**: 외부 리소스 전체에 CORS 설정 확인
- **vector_animation_freezable=false (R13 WARN)**: `requestAnimationFrame` 루프 사용 (line 169, 171). `freezeForExport` 없음. 연속 2회 캡처 시 프레임이 달라질 수 있음.
- **마이그레이션 분류: 불필요** — R13 실측 대상. PHASE 4 (§4.6) 에서 500ms 정지 fallback 효과 정량화.
- SC10: `onboarding-intro-animation` freeze 적용 후 연속 2회 export 시각 diff = 0 검증 필요

### payment-flow-wireframe (Tier 3)

- 경로: `designs/payment-flow-wireframe/index.html`
- **vector_tier1=false**: `window.__deck` 없음
- **vector_structure_ok=false**: `<deck-stage>` 없음 (와이어프레임)
- **vector_cors_ok=true**: 외부 리소스 CORS 설정 확인
- **vector_animation_freezable=false (R13 WARN)**: animation 관련 코드 감지
- **마이그레이션 분류: 불필요** — 비덱 와이어프레임. screenshots fallback 전용.

### clawpod-customer-intro/ (디렉토리) — R15 확인 완료

- 경로: `designs/clawpod-customer-intro/` (디렉토리)
- `index.html` 없음 — 이전 버전 애셋 잔재(빈 디렉토리) 확인
- canonical 경로는 `designs/clawpod-customer-intro.html` (단일 파일)
- **조치**: 이 디렉토리는 PHASE 6에서 삭제 또는 명시적 주석 처리 권장

## 마이그레이션 분류 요약

| 분류 | 덱 | 마이그레이션 내용 |
|------|----|----------------|
| 필수 마이그레이션 | onboarding-first-week-deck | Tier 1 API 추가 + freeze hook + crossorigin (PHASE 6 가이드) |
| 권장 마이그레이션 | clawpod-customer-intro.html | crossorigin="anonymous" 1개 추가 → vector_ready=true 달성 |
| 불필요 (screenshots 전용) | agent-create-wizard, marketing-landing, onboarding-intro-animation, payment-flow-wireframe | Tier 3 비덱. editable 경로 skip. |
| 제외 | clawpod-customer-intro/ (디렉토리) | R15 확인 완료. 삭제 권장. |

## R13 위험 시각화

`vector_animation_freezable=false` 덱: **4/6** (67%)

| 덱 | animation 유형 | R13 위험도 |
|----|--------------|-----------|
| onboarding-first-week-deck | CSS animation (선언 확인) | 중간 (500ms fallback 적용) |
| onboarding-intro-animation | rAF 루프 (line 169, 171) | 높음 (프레임 연속 변화) |
| agent-create-wizard | rAF 또는 CSS animation | 중간 |
| payment-flow-wireframe | animation 관련 코드 | 낮음~중간 |

clawpod-customer-intro.html 은 animation 미감지 (`vector_animation_freezable=true`) — PHASE 2 PoC 덱으로 적합.

## 런타임 측정 필요 항목 (PHASE 4)

| 항목 | 이유 |
|------|------|
| vector_shadow_dom_ok (런타임) | 정적 분석에서 `attachShadow` 미감지 → 모두 `true` 로 표시됨. 실제 web component 가 런타임에 shadow DOM 생성할 수 있음. |
| vector_headless_drift_ok (T15) | 정적 분석 불가. Playwright headless/headed 텍스트 bbox + 색상 ΔE 실측 필요. |
| speaker_notes_ok | `<script id="speaker-notes">` 유무 및 배열 길이 === slideCount 런타임 확인. |
| vector_cors_ok (정밀) | 현재 정규식 기반. 런타임에서 network 요청 실제 실패 여부 확인 필요. |

## PHASE 2 → PHASE 4 인터페이스

1-B에서 정의한 `vector_shadow_dom_ok`, `vector_cors_ok`, `vector_animation_freezable`, `vector_headless_drift_ok` 4개 체크 항목은 PHASE 4 통합 테스트에서 Playwright `page.evaluate` 로 동일 키명으로 측정된다.
PHASE 4 결과는 본 베이스라인 표의 `(S)` 항목을 `(P)` 로 업데이트하여 `references/vector-compat-results.md` 에 기록된다.
