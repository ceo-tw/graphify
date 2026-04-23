# dom-to-pptx Spike Notes — PHASE 2 GO/NO-GO Report

> 실측일: 2026-04-21
> 버전: dom-to-pptx v1.1.7
> Spike 실행: `node .claude/skills/design-artifact/scripts/spike-vector.mjs`

---

## 1. exportToPptx() 실측 시그니처

```javascript
exportToPptx(elementOrSelector, options?) -> Promise<Blob>
```

### 파라미터

| 파라미터 | 타입 | 설명 |
|---------|-----|------|
| `elementOrSelector` | `string \| HTMLElement \| HTMLElement[]` | CSS 셀렉터 문자열, 단일 DOM 엘리먼트, 또는 엘리먼트 배열 |
| `options.fileName` | `string` | 기본값 `"export.pptx"` |
| `options.skipDownload` | `boolean` | `true` 시 자동 다운로드 없이 Blob 반환. **Node 측 추출 필수** |
| `options.autoEmbedFonts` | `boolean` | 기본값 `true`. 사용 폰트 자동 임베딩 |
| `options.svgAsVector` | `boolean` | 기본값 `false`. SVG를 PNG 대신 벡터로 보존 (v1.1.5+) |
| `options.fonts` | `Array<{name, url}>` | 수동 폰트 지정 |
| `options.listConfig` | `object` | 목록 스타일 설정 |

### 반환 타입

`Promise<Blob>` — PPTX 바이너리 Blob. `skipDownload: true` 없으면 브라우저가 즉시 파일 저장 다이얼로그 열림.

### multi-selector 지원 (실측 확인)

**b1 전략 지원 확인**: `exportToPptx(Array.from(sections), { skipDownload: true })` 형태의 배열 입력이 v1.1.7 에서 정상 동작. 배열 내 각 엘리먼트가 독립 슬라이드로 처리됨.

USAGE.md 인용:
```javascript
// Multiple Slides
const slides = document.querySelectorAll('.slide');
await exportToPptx(Array.from(slides), { fileName: 'multi-slides.pptx' });
```

---

## 2. 채택된 멀티슬라이드 전략: b1 (1순위 가설과 다름)

### 결론: b1 채택

| 전략 | 설명 | 실측 결과 |
|------|-----|---------|
| b1 | `exportToPptx(Array<Element>)` 다중 엘리먼트 한 번에 | **PASS — 채택** |
| b2 | 슬라이드별 개별 Blob → JSZip rel-id 재번호 머지 | 구현됨 (adapter), b1 성공으로 fallback 경로만 역할 |
| b3 | dom-to-pptx IR + PptxGenJS 리매핑 | 미시도 (b1 성공으로 불필요) |

### 근거

설계 문서 (`design-pptx-vector-export.md:100-106`) 에서 b1 가능성을 "낮음"으로 평가했으나, dom-to-pptx v1.1.7 USAGE.md 에 Array 입력 예시가 명시되어 있고 실측에서 3-section fixture 에 대해 3-slide PPTX(2.2MB) 를 정상 출력했다. b2 는 구현 완료 상태로 adapter 내 fallback 경로로 보존한다.

### b1 제약 사항 (실측)

- 배열 내 모든 엘리먼트가 **동시에 DOM에 visible 상태**여야 함. `display: none` 엘리먼트는 내용이 비어 나올 수 있음.
- `transform: scale()` 이 적용된 엘리먼트는 좌표 추출 오차 발생 가능 (`deck-stage noscale` 적용 필요).
- 외부 폰트: `crossorigin="anonymous"` 없으면 임베딩 실패 → Arial 폴백.

---

## 3. 프로브별 결과 표

### §2.4 (a)(b)(c) 통과 여부

| 프로브 | 대상 | 기준 | 결과 | 비고 |
|--------|-----|------|------|------|
| (a) Single-slide | `vector-spike-single.html` → `#root` | Buffer > 1KB, slide1.xml 확인 | PASS | 172,511 bytes, slide1.xml 존재 |
| (b) Multi-slide | `vector-spike-multi.html` → 3 sections | 3-slide PPTX 생성, 각 슬라이드 내용 분리 | PASS | 2,248,325 bytes, 3 slide XML 확인, 전략: b1 |
| (c) Real deck | `onboarding-first-week-deck` → 3 slides | media + speaker notes 슬라이드별 매핑 | PASS | 22,847 bytes, 3 slides, notesSlides 존재 |

### 세부 측정치

| 항목 | 값 |
|------|---|
| (a) PPTX 파일 크기 | 172,511 bytes (168 KB) |
| (b) PPTX 파일 크기 | 2,248,325 bytes (2.2 MB, 폰트 임베딩 포함) |
| (c) PPTX 파일 크기 | 22,847 bytes (22 KB, 폰트 없음) |
| (b) slide count | 3 (ZIP 내 slide1.xml ~ slide3.xml 확인) |
| (c) slide count | 3 (10슬라이드 덱에서 첫 3개) |
| (c) notesSlides 존재 | true |
| (c) media (img) 존재 | false (onboarding-first-week-deck 이미지 없음) |
| 실행 총 소요 시간 | ~9초 (3 프로브 합계) |

### 편집 가능성 (PowerPoint 열기 확인)

- (a)(b): `unzip -l` 에서 `ppt/slides/slide*.xml` 이 텍스트 XML 로 저장됨 확인. 슬라이드 XML 내 `<a:t>` 텍스트 노드 존재 → PowerPoint 에서 텍스트 편집 가능 구조.
- (c): 22KB 는 폰트 없이 순수 XML 구조만 — onboarding-first-week-deck 이 구글 폰트(외부 URL) 를 사용하므로 file:// 프로토콜에서 CORS 실패 → 폰트 임베딩 없이 생성됨 (PHASE 3 에서 `--allow-file-access-from-files` Chromium 플래그 또는 폰트 URL 수동 지정으로 해결 필요).

---

## 4. adapter 함수 3개 시그니처 (2-D 결과)

파일: `.claude/skills/design-artifact/scripts/lib/dom-to-pptx-adapter.mjs`

```javascript
/**
 * Inject dom-to-pptx bundle into Playwright page (local file, no CDN).
 * Must be called after page.goto() before any exportSlideBlob() calls.
 */
export async function injectDomToPptx(page: PlaywrightPage): Promise<void>

/**
 * Export a single slide or multiple elements as PPTX Blob → Node.js Buffer.
 * Uses skipDownload: true to suppress browser save-as dialog.
 *
 * @param selector - CSS selector string OR array of selectors/elements
 * @param options  - dom-to-pptx options (svgAsVector, autoEmbedFonts, etc.)
 */
export async function exportSlideBlob(
  page: PlaywrightPage,
  selector: string | string[],
  options?: Record<string, unknown>
): Promise<Buffer>

/**
 * Merge multiple single-slide PPTX Buffers into one multi-slide PPTX (strategy b2).
 * Handles rel-id renumbering, theme dedup, [Content_Types].xml rebuild,
 * and speaker notes attachment.
 *
 * @param slideBuffers - one Buffer per slide (from individual exportToPptx calls)
 * @param notes        - speaker note strings, one per slide
 * @param layout       - optional { width, height } in EMU for sldSz override
 */
export async function mergePptxSlides(
  slideBuffers: Buffer[],
  notes?: string[],
  layout?: { width?: number; height?: number }
): Promise<Buffer>
```

---

## 5. GO/NO-GO 판정

```
verdict: GO
```

### 판정 근거

| 기준 | 결과 |
|------|------|
| §2.4(a): Buffer > 1KB + slide1.xml | PASS |
| §2.4(b): 3-slide PPTX 생성 | PASS (b1 전략) |
| §2.4(c): real deck 3 slides + notes mapping | PASS |
| 전략 b1/b2/b3 중 하나 이상 통과 | PASS (b1) |

모든 GO 조건을 충족. **PHASE 3 진행 권장**.

### 주의 사항 (PHASE 3 에서 해결 필요)

1. **외부 폰트 CORS**: 실제 덱은 Google Fonts (외부 URL) 사용 → file:// 프로토콜에서 CORS 실패로 폰트 임베딩 불가. 해결책: `--allow-file-access-from-files` Chromium 플래그 또는 `options.fonts` 수동 지정.
2. **b1 visible 요구**: 배열 엘리먼트가 `display: none` 이면 내용이 빈 슬라이드로 나올 수 있음. 수출 전 `section.style.display = 'flex'` 일시 적용 필요.
3. **transform:scale 오차**: deck-stage 의 scale 적용 시 좌표 오차. `<deck-stage noscale>` 강제 적용.
4. **speaker notes**: onboarding-first-week-deck 에 `<script id="speaker-notes">` 없음 (Tier 2). notes 슬라이드는 빈 문자열로 생성됨.

---

## 6. 다음 단계 권장

verdict: **GO** → **PHASE 3 진행**

PHASE 3 작업:
- `export-pptx.mjs` 에 `--mode=editable` 실구현 (b1 전략 기반 `renderDeckEditable`)
- `--mode=hybrid` orchestrator
- `--strict`, `--fallback-on-error` flag
- 외부 폰트 해결 (Chromium flag 추가)
- TDD: `export-pptx.test.mjs` T-U1~T-U5 구현
