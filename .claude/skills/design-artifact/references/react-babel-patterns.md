# React + Babel Patterns (Inline JSX)

React 프로토타입을 인라인 JSX로 작성할 때는 반드시 다음 규칙을 지킨다.

---

## Pinned Versions with Integrity Hashes (REQUIRED)

아래 **정확한** 스크립트 태그를 사용한다. unpinned 버전(예: `react@18`)이나 integrity 속성 누락은 금지.

```html
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y" crossorigin="anonymous"></script>
```

이후 작성한 헬퍼·컴포넌트 스크립트를 `<script>` 태그로 import 한다. `type="module"`은 사용하지 말 것 — 깨질 수 있다.

---

## CRITICAL: `const styles = { ... }` 금지

전역 스코프 style 객체를 정의할 때는 **구체적인 이름을 부여한다**. 2개 이상의 컴포넌트가 `styles` 객체를 쓰면 서로 덮어쓰며 깨진다.

**Bad:**
```jsx
// Terminal.jsx
const styles = { line: { color: 'gray' } };

// Header.jsx
const styles = { title: { fontSize: 24 } };
// -> 마지막 로드된 styles가 이전 것을 덮어씀
```

**Good:**
```jsx
// Terminal.jsx
const terminalStyles = { line: { color: 'gray' } };

// Header.jsx
const headerStyles = { title: { fontSize: 24 } };
```

또는 inline styles를 사용한다.

> 이 규칙은 **협상 불가**. 이름 충돌 style 객체는 깨짐을 유발한다.

---

## CRITICAL: Babel 스크립트 간 스코프 공유

각 `<script type="text/babel">` 은 트랜스파일 시 자체 스코프를 가진다. 여러 파일 간 컴포넌트를 공유하려면 컴포넌트 파일 끝에서 `window`에 export 한다.

```jsx
// components.jsx 의 맨 아래
Object.assign(window, {
  Terminal, Line, Spacer,
  Gray, Blue, Green, Bold,
  // ... 공유가 필요한 모든 컴포넌트
});
```

이렇게 하면 다른 스크립트에서 전역으로 사용 가능하다.

---

## CRITICAL: `file://` origin CORS 제약 — 외부 `.jsx` 로딩 금지

로컬 파일을 `file://` 프로토콜로 열 때 (Claude Code 환경의 기본 미리보기 방식), Chromium 계열 브라우저는 **`<script type="text/babel" src="components/*.jsx">` 같은 외부 파일 로딩을 CORS 로 차단한다**. Babel Standalone 이 내부적으로 XMLHttpRequest 로 파일을 가져오기 때문이다.

### 증상
- 콘솔에 `CORS-blocked XHR for components/*.jsx` 또는 `Cross origin requests are only supported for protocol schemes: chrome, ...` 에러
- `#root` 가 비어있음, 페이지 공백
- design-verifier 가 `body_rendered: false` 보고

### 해결책 — **모든 JSX 를 단일 HTML 에 인라인**

외부 `.jsx` 파일로 분할하지 말고, 모든 컴포넌트를 하나의 HTML 안에 `<script type="text/babel">` 블록으로 인라인한다.

```html
<!-- GOOD: inline, single file, works on file:// -->
<script type="text/babel">
  function Button({ children }) { ... }
  function Card({ title, children }) { ... }
  function App() {
    return <Card title="Demo"><Button>OK</Button></Card>;
  }
  ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
```

```html
<!-- BAD: external .jsx src — breaks under file:// -->
<script type="text/babel" src="components/button.jsx"></script>
<script type="text/babel" src="components/app.jsx"></script>
```

### 예외: 같은 origin 에서 서빙할 때

`http://localhost:3000`, `file://` 외의 HTTP 서버(예: `python -m http.server`), Artifact 호스트 환경에서는 외부 `.jsx` 로딩이 동작한다. 하지만 Claude Code 사용자는 대부분 `open file://...` 로 확인하므로 **기본은 항상 인라인**.

### 결과적으로 파일 크기 규칙 완화

원본 "1000 lines 미만" 가이드는 외부 파일 분할이 가능할 때의 기준이다. `file://` 환경에서는 **단일 파일 크기 제한보다 CORS 회피가 우선**. 1500-2000 lines 까지 허용. 그 이상이면 디자인 범위가 과도한지 재검토.

### 스코프 공유가 필요 없어짐

단일 `<script type="text/babel">` 블록 안이면 모든 컴포넌트가 같은 스코프에 있다. `Object.assign(window, {...})` 도 불필요. (여러 `<script>` 블록을 쓸 때만 window export 가 필요.)

---

## 파일 분할 (HTTP origin 전용)

HTTP 서버에서 서빙되는 환경에서만 유효:
- 큰 파일(>1000 lines)은 피한다
- 여러 작은 JSX 파일로 나누고 메인 파일에서 `<script type="text/babel" src="...">` 로 import
- 각 파일 끝에서 `Object.assign(window, {...})` 로 컴포넌트 공유

**기본 가이드**: `file://` 에서 동작하도록 항상 인라인 우선. 외부 서빙 환경이 확정된 경우에만 분할.

---

## 간단한 인터랙티브 프로토타입

- CSS transitions 또는 간단한 React state 로 충분하면 그것을 사용.
- 실제 앱 수준 인터랙션이 필요하면 React 상태 + 이벤트 핸들러.
- 타이틀 화면을 추가하려는 유혹을 참는다. 프로토타입은 뷰포트 중심에 두거나 반응형 크기(뷰포트 + 합리적 마진)로.

---

## 금지 사항

- `scrollIntoView` 금지 — 웹앱을 엉망으로 만들 수 있다. 필요하면 다른 DOM scroll 메서드 사용.
- 코드 대비 스크린샷 우선 금지 — Claude는 스크린샷보다 코드 기반 인터페이스 재현·편집에 더 강하다. 소스 데이터가 주어지면 코드·디자인 컨텍스트 탐색에 집중.
- 이모지 사용 금지 (디자인 시스템이 이모지를 사용하는 경우만 예외).
