# Slide Deck Authoring

슬라이드 덱, 프레젠테이션, 비디오 등 **고정 크기** 콘텐츠는 자체 JS 스케일링을 구현해 어떤 뷰포트에서도 맞게 만든다. 고정 크기 캔버스(기본 1920×1080, 16:9)를 풀뷰포트 스테이지로 감싸고 `transform: scale()` 로 레터박스 처리. **prev/next 컨트롤은 스케일된 요소 밖에 두어** 작은 화면에서도 사용 가능하게 한다.

---

## `<deck-stage>` Web Component

슬라이드 덱은 직접 스케일링을 손으로 짜지 말고 `<deck-stage>` 패턴을 사용한다. 다음 기능을 제공한다:

- 자동 스케일 (viewport fit)
- 키보드·터치 네비게이션 (좌/우 화살표, Space)
- 슬라이드 카운터 오버레이
- Speaker notes postMessage 연동
- localStorage 현재 슬라이드 영속화
- Print-to-PDF (슬라이드 당 1 페이지)
- 외부 컨트랙트: 모든 슬라이드에 `data-screen-label`, `data-om-validate` 자동 부착
- 부모에게 `{slideIndexChanged: N}` postMessage 전송

### 구조

```html
<deck-stage>
  <section>Slide 1 content</section>
  <section>Slide 2 content</section>
  <section>Slide 3 content</section>
</deck-stage>
```

각 슬라이드는 `<deck-stage>` 의 **직접 자식** `<section>` 이어야 한다.

### 최소 구현 (design-executor가 작성할 템플릿)

`<deck-stage>` 웹 컴포넌트는 다음 요건을 만족해야 한다:

1. `ResizeObserver`로 뷰포트 추적
2. 내부 캔버스를 `transform: scale(min(vw/1920, vh/1080))` 으로 피팅, letterbox는 검정
3. 키보드 이벤트: ArrowLeft/ArrowRight/Space
4. 각 `<section>` 에 `data-screen-label="01 Title"` (01-indexed, zero-padded) 자동 부착
5. 슬라이드 인덱스가 바뀔 때마다 `localStorage.setItem('deck-index', N)` 과 `window.parent.postMessage({slideIndexChanged: N}, '*')`
6. 로드 시 `localStorage.getItem('deck-index')` 읽어 복원
7. 속성 `noscale` 이 붙으면 스케일 해제 (PPTX 캡처 대응)
8. `@media print` 에 각 슬라이드를 개별 페이지로 표시

---

## 구현 함정 (Custom Element Pitfalls)

실제 덱 구현 시 반복적으로 발생하는 2가지 버그. **처음부터 피하도록** 한다.

### Pitfall 1: `connectedCallback` 타이밍 문제

**증상**: `this.sections = []` 영구 빈 배열. 라벨링·렌더링이 아무것도 안 됨. 모든 section 이 `display: none` 으로 남음.

**원인**: HTML parser 는 opening tag `<deck-stage>` 만난 즉시 `connectedCallback` 을 fire 한다. 이 시점에 자식 `<section>` 들은 아직 파싱 전이라 `this.children` 이 비어있다.

**해결책 (3가지, A 선호)**:

**A. 동기식 init-after-parse (권장)** — `<deck-stage>` 닫는 태그 이후, `<script type="text/babel">` 전에 인라인 `<script>` 하나를 배치해 동기 실행:

```html
<deck-stage>
  <section>...</section>
  ...
</deck-stage>

<script>
  // 이 시점엔 parser 가 이미 <section> 10개를 DOM 에 넣은 상태
  document.querySelectorAll('deck-stage').forEach(stage => stage._initWithChildren());
</script>

<script type="text/babel">
  // React mount — 이미 라벨링 끝난 section 들에 마운트됨
  ReactDOM.createRoot(document.getElementById('slide-01')).render(<Slide01 />);
  ...
</script>
```

**왜 `DOMContentLoaded` 대신 동기식?** `@babel/standalone` 이 자체 `DOMContentLoaded` 리스너를 등록해 `<script type="text/babel">` 을 트랜스파일한다. 만약 init 을 `DOMContentLoaded` 에 넣으면 Babel 이 먼저 실행돼 라벨링되지 않은 section 에 React 가 마운트된다.

**B. MutationObserver**: `connectedCallback` 에서 `MutationObserver` 를 붙여 childList 변경까지 대기. teardown 복잡.

**C. `customElements.define` 호출을 `</deck-stage>` 뒤로 이동**: 등록 전에는 upgrade 가 일어나지 않아 `connectedCallback` 도 호출되지 않는다. 등록 시점에 children 이 이미 존재하므로 `connectedCallback` 이 정상 동작. 다만 실수로 define 을 앞쪽에 두면 버그 재발.

### Pitfall 2: CSS selector vs 래퍼 구조 불일치

**증상**: init 은 성공해 section 에 `data-active` 토글이 반영되는데, 시각적으로는 모든 슬라이드가 동시에 스택. 마지막 section 이 항상 위에 페인팅됨. 스크린샷이 모든 슬라이드에서 동일.

**원인**: `_initWithChildren` 이 section 들을 `<div class="ds-canvas">` 래퍼 안으로 옮기는 경우가 많다(스케일·letterbox 배경 처리용). 그런데 CSS 는 여전히 `deck-stage > section` 으로 **직접 자식**만 선택 → 래퍼 이후엔 selector 가 매칭되지 않는다.

**해결책**: 래퍼를 도입하면 **모든 관련 CSS selector 를 함께 업데이트**한다. 최소한 6곳 정도 되는 경향:

```css
/* BAD (래퍼 도입 후 깨짐) */
deck-stage > section { display: none; }
deck-stage > section[data-active="true"] { display: block; ... }
[data-density="compact"] deck-stage > section { ... }
@media print { deck-stage > section { page-break-after: always; } }

/* GOOD */
deck-stage .ds-canvas > section { display: none; }
deck-stage .ds-canvas > section[data-active="true"] { display: block; ... }
[data-density="compact"] deck-stage .ds-canvas > section { ... }
@media print { deck-stage .ds-canvas > section { page-break-after: always; } }
```

**대안**: 래퍼를 도입하지 않고 `deck-stage` 자체에 `transform: scale()` 과 배경을 적용. 래퍼 없이도 letterbox 가능.

### design-verifier 가 체크하는 항목

이 두 함정 모두 runtime 단계에서 감지된다:
- `document.querySelectorAll('deck-stage .ds-canvas > section').length === 10` (또는 래퍼 없을 때 `deck-stage > section`)
- `data-screen-label`, `data-om-validate` 부착
- 정확히 1개 section 이 `data-active="true"`
- 슬라이드 1/5/10 스크린샷이 서로 md5 가 **distinct** 해야 함 (동일하면 CSS 미스매치 의심)
- 키보드 네비게이션 후 counter text 가 반영되는지

---

## Speaker Notes

덱의 스피커 노트는 사용자가 명시적으로 요청한 경우에만 추가한다. **요청하지 않으면 절대 추가 금지.**

스피커 노트가 있을 때는 슬라이드의 텍스트를 줄이고 임팩트 있는 비주얼에 집중한다. 스피커 노트는 발표자가 실제로 말할 전체 스크립트 (대화체) 로 작성한다.

`<head>` 에 추가:

```html
<script type="application/json" id="speaker-notes">
[
    "Slide 0 notes",
    "Slide 1 notes"
]
</script>
```

페이지는 init 시·슬라이드 변경마다 `window.postMessage({slideIndexChanged: N})` 를 호출해야 한다. `<deck-stage>` 를 사용하면 이 postMessage 를 자동으로 처리한다.

---

## 슬라이드·스크린 라벨링

사용자 댓글 컨텍스트를 위해 슬라이드·스크린 요소에 `[data-screen-label]` 속성을 붙인다. **슬라이드 번호는 1-indexed**. `"01 Title"`, `"02 Agenda"` 같은 라벨을 사용해 슬라이드 카운터(`{idx + 1}/{total}`) 와 일치시킨다.

사용자가 "슬라이드 5" 또는 "index 5" 라고 말하면 **5번째 슬라이드**(라벨 "05") 를 의미하지 배열 위치 [4] 가 아니다. 사람은 0-indexed 로 말하지 않는다. 0-indexed 라벨을 쓰면 모든 슬라이드 참조가 1 밀린다.

`<deck-stage>` 는 이 규칙에 따라 자동 라벨링한다.

---

## 시스템 우선 (덱 레이아웃 규칙)

- 섹션 헤더·타이틀·이미지 레이아웃을 위한 일관된 체계 선택
- 의도적 시각 다양성·리듬 도입: 섹션 스타터에 다른 배경색, 이미지 중심일 때 풀블리드 레이아웃
- 덱 당 배경색은 최대 1-2개
- 텍스트 헤비 슬라이드에는 디자인 시스템 이미지 또는 placeholder 추가
- 기존 타이포 시스템이 있으면 사용, 없으면 `<style>` 태그에 폰트 변수 + Tweaks 로 전환

---

## 텍스트 스케일

1920×1080 슬라이드에서 텍스트는 **절대 24px 미만 금지**, 이상적으로 훨씬 크게.

---

## 애니메이션 슬라이드 (비디오 스타일)

타임라인 기반 애니메이션이 필요하면 Stage + Sprite 패턴을 사용한다 (자체 구현). 핵심 요소:

- `<Stage>`: 자동 스케일 + 스크러버 + 재생/일시정지
- `<Sprite start end>`: 시간 범위 내에만 렌더
- `useTime()` / `useSprite()` hooks
- `Easing`: 이징 함수 모음
- `interpolate()`: 값 보간
- Entry/exit primitives

인터랙티브 프로토타입은 CSS transitions 또는 간단한 React state 로 충분할 때가 많다. 타이틀 화면을 추가하려는 유혹을 참고, 뷰포트 중심 또는 반응형 크기로 만든다.

대안: [Popmotion](https://unpkg.com/popmotion@11.0.5/dist/popmotion.min.js) 이 자체 구현보다 적합한 경우에만 사용.

---

## PPTX Export Contract (deck-stage ↔ export-pptx.mjs)

`export-pptx.mjs` 는 headless Playwright 로 덱을 캡처해 PPTX 를 생성한다. 이 스크립트가 `<deck-stage>` 와 통신하는 계약을 정의한다. 덱 구현 시 이 계약을 준수해야 export 가 정상 동작한다.

### 1. Required API Surface

`export-pptx.mjs` 는 `window.__deck` 객체를 통해 덱을 제어한다. `<deck-stage>` 는 반드시 다음 API 를 노출해야 한다:

| 메서드 | 시그니처 | 설명 |
|--------|----------|------|
| `getSlideCount` | `() => number` | 전체 슬라이드 수 반환 |
| `goToSlide` | `(index: number) => void` | 지정 슬라이드로 이동 (1-indexed) |
| `getCurrentSlide` | `() => number` | 현재 슬라이드 번호 반환 (optional) |

```js
// deck-stage 구현 예시
window.__deck = {
  getSlideCount: () => this._sections.length,
  goToSlide: (index) => { /* 1-indexed */ this._goTo(index); },
  getCurrentSlide: () => this._currentIndex, // optional
};
```

**경계 값 처리**: `goToSlide(0)`, `goToSlide(n+1)` 등 범위 밖 인덱스는 **no-op** 으로 처리한다 (예외 throw 금지). export 스크립트가 루프 경계에서 안전하게 호출할 수 있어야 한다.

**동기 paint**: `goToSlide` 호출 후 DOM 변경은 동기적으로 완료되어야 한다. Playwright 는 `goToSlide` 반환 직후 스크린샷을 찍는다. `requestAnimationFrame` 또는 `setTimeout` 으로 슬라이드 전환을 지연하지 않는다.

### 2. `noscale` Attribute 동작

`export-pptx.mjs` 는 캡처 전 `<deck-stage noscale>` 을 설정한다. `noscale` 이 붙으면:

- `transform: scale()` 을 **제거**한다 (Playwright 뷰포트가 이미 1920×1080 으로 설정됨)
- 캔버스는 **natural size 1920×1080** 으로 렌더된다
- `ResizeObserver` 기반 자동 rescale 을 **비활성화**한다 (뷰포트 리사이즈 이벤트에 반응하지 않음)
- 슬라이드 인덱스 상태, 키보드 네비게이션, `window.__deck` API 는 **영향 없음**

```js
// noscale 속성 감지 예시
_updateScale() {
  if (this.hasAttribute('noscale')) {
    this._canvas.style.transform = '';
    return;
  }
  const scale = Math.min(
    window.innerWidth / 1920,
    window.innerHeight / 1080
  );
  this._canvas.style.transform = `scale(${scale})`;
}
```

`noscale` 제거 시 자동 rescale 이 재개되어야 한다 (`attributeChangedCallback` 또는 `observedAttributes` 를 통해 감지).

### 3. Speaker Notes

`export-pptx.mjs` 는 슬라이드별 스피커 노트를 PPTX 에 삽입하기 위해 다음 방식으로 노트를 읽는다:

```html
<!-- <head> 또는 <body> 상단에 배치 -->
<script type="application/json" id="speaker-notes">
[
  "Slide 1 notes — 발표자가 실제로 말할 내용",
  "Slide 2 notes",
  "Slide 3 notes"
]
</script>
```

**규칙**:

- 배열 길이는 반드시 `getSlideCount()` 반환값과 **동일**해야 한다
- 길이 불일치 시 export 스크립트는 `no_speaker_notes=true` 플래그로 처리하고 PPTX 에 노트를 포함하지 않는다 (오류로 중단하지 않음)
- 노트가 없는 슬라이드는 빈 문자열 `""` 로 자리를 채운다

```json
// 10개 슬라이드, 일부 노트 없음 — 배열 길이는 여전히 10
["인트로 스크립트", "", "핵심 메시지", "", "", "", "", "", "", "마무리 멘트"]
```

### 4. 1-Indexed Numbering

덱의 모든 공개 인터페이스에서 슬라이드 번호는 **1-indexed** 를 사용한다. 내부 배열 인덱스(0-indexed)와 혼동하지 않는다.

| 인터페이스 | 값 | 예시 |
|-----------|-----|------|
| `data-screen-label` 속성 | 1-indexed, zero-padded | `"01 Title"`, `"10 Summary"` |
| `localStorage['deck-index']` | 1-indexed | `1`, `5`, `10` |
| `window.__deck.goToSlide(index)` | 1-indexed | `goToSlide(1)` = 첫 슬라이드 |
| `postMessage({ slideIndexChanged: N })` | 1-indexed | `{ slideIndexChanged: 1 }` |

export 스크립트는 이 규칙을 전제로 `for (let i = 1; i <= count; i++)` 루프로 순회한다. 0-indexed API 를 노출하면 첫 슬라이드 또는 마지막 슬라이드가 누락된다.

### 5. Graceful Degradation

`window.__deck` 를 노출하지 않는 기존 덱(레거시)은 **tier-2 fallback** 으로 처리한다:

- export 스크립트는 `window.__deck` 존재 여부를 확인 후 없으면 fallback 경로 진입
- Fallback: 키보드 `ArrowRight` 이벤트를 직접 dispatch 해 슬라이드를 순회
- Fallback 은 timing-dependent 이므로 각 이동 후 `waitForTimeout` 을 추가로 삽입
- **기존 덱에 회귀 없음** — `__deck` API 추가 없이도 export 는 동작하나, 정확도와 속도가 낮을 수 있음

신규 덱은 반드시 tier-1 (`window.__deck`) 을 구현한다.

---

## Editable Export Contract

`--mode=editable` 또는 `--mode=hybrid` 로 편집 가능 PPTX 를 생성하려면 아래 계약을 준수해야 한다. 미준수 항목이 있는 덱은 `vector_ready=false` 로 판정되어 자동으로 screenshots fallback 경로로 처리된다.

### MUST (필수)

| 항목 | 요구사항 | 비고 |
|------|---------|------|
| Tier 1 API | `window.__deck.getSlideCount()`, `window.__deck.goToSlide()` 구현 | tier-2 (ArrowRight fallback) 덱은 editable 미지원 |
| Canvas 크기 | 1920×1080 고정 (`.ds-canvas` 또는 `<deck-stage>` 직계 자식) | `getComputedStyle` 으로 확인 |
| 슬라이드 구조 | `<deck-stage> [.ds-canvas >] section` 패턴 — `<section>` 이 슬라이드 단위 | 다른 컨테이너 사용 시 dom-to-pptx 슬라이드 분할 실패 |
| 이미지 | `<img>` 는 same-origin 또는 CORS-allowed | `crossorigin="anonymous"` + 서버 CORS 헤더 필수 |
| 색상 추출 | 모든 색상값이 `getComputedStyle` 으로 추출 가능해야 함 | oklch, rgb, hex 모두 허용. 단, CSS custom property 최종값이 색상이어야 함 |
| Shadow DOM 범위 | shadow DOM 을 사용하는 web component 가 있다면 반드시 `<deck-stage>` 후손 내에만 위치 | `<deck-stage>` 외부의 shadow DOM 은 dom-to-pptx 파싱 대상 외 |
| 외부 리소스 | 외부 웹폰트·CDN 이미지는 `crossorigin="anonymous"` 명시 | CORS 미설정 시 base64 추출 실패 → 이미지 누락 |
| Async animation freeze hook | `window.__deck.freezeForExport?()` 구현 권장. 미구현 시 500ms 정지 후 캡처 (fallback) | CSS animation / JS setInterval / rAF 사용 덱은 freeze hook 없이는 캡처 결과가 프레임마다 달라질 수 있음 |

```js
// freeze hook 구현 예시
window.__deck = {
  getSlideCount: () => sections.length,
  goToSlide: (i) => { /* 1-indexed */ },
  freezeForExport: () => {
    // CSS animation 정지
    document.querySelectorAll('*').forEach(el => {
      el.style.animationPlayState = 'paused';
    });
    // rAF/setInterval 기반 애니메이션도 여기서 취소
  },
};
```

### SHOULD (권장)

| 항목 | 권장사항 |
|------|---------|
| 폰트 | Geist (본문) + Noto Sans CJK 또는 Pretendard (한글) fallback chain. PPTX 에서 CJK 폰트 미임베딩 시 깨짐 발생 가능 |
| Speaker notes 길이 | `speaker-notes` 배열 길이 === `getSlideCount()` 반환값. 불일치 시 노트 전체 누락 |

### MAY (선택)

| 항목 | 설명 |
|------|------|
| Tweaks / dark mode | editable export 는 현재 렌더 상태를 그대로 캡처. 다크모드 전환 후 export 가능 |
| 정지 가능한 애니메이션 | freeze hook 을 통해 정지 가능하면 editable 경로 유지. 정지 불가 시 해당 슬라이드 screenshots fallback |

### 변동성 허용 매트릭스 (editable export 관점)

덱 작성 시 아래 차원별 허용 범위와 editable 모드에서의 제약을 참고한다.

| 차원 | 변동 범위 | editable MUST 강제 |
|------|---------|--------------------|
| 슬라이드 단위 | `<section>` only | MUST 유지 |
| Canvas | 1920×1080 | MUST 유지 |
| 폰트 | Geist / Pretendard / Inter / CJK | SHOULD (fallback chain) |
| 색상 | oklch / rgb / hex | MUST: `getComputedStyle` 추출 가능 |
| 레이아웃 | flex / grid / absolute | 자유 |
| 미디어 | `<img>` / SVG / Canvas / video | MUST: `<img>` same-origin or CORS. SVG vector 유지. Canvas/video 는 raster fallback 필수 |
| Shadow DOM | web component 내부 | MUST: `<deck-stage>` 이외 shadow DOM 사용 시 raster fallback |
| 외부 리소스 | webfont, CDN 이미지 | MUST: `crossorigin="anonymous"` 또는 same-origin |
| 비동기 애니메이션 | CSS anim / JS setInterval / rAF | MUST: freeze hook 권장. 미구현 시 500ms 정지 fallback |
| 렌더링 컨텍스트 | headless vs headed | MUST: headless Chromium 에서 실제 렌더와 오차 < 5% |
| Tweaks / dark mode | 선택 | 자유 (export 시 현재 상태 캡처) |
| 인터랙션 | Tier 1 API | MUST (신규 덱): Tier 1 API |

### vector_ready 판정 기준

design-verifier 의 집계 필드 `vector_ready` 는 다음 조건이 모두 충족될 때 `true`:

```
vector_ready = vector_tier1
             && vector_structure_ok
             && vector_images_ok
             && vector_notes_ok
             && vector_colors_ok
             && vector_shadow_dom_ok
             && vector_cors_ok
             && (vector_animation_freezable || hasFreezeFallback)
```

`vector_headless_drift_ok` 는 SC9 측정용으로만 사용하며 `vector_ready` 판정에는 포함되지 않는다 (`false` 시 WARN 기록).

`vector_ready=false` 인 덱은 editable 경로를 건너뛰고 screenshots fallback 으로 처리된다.
