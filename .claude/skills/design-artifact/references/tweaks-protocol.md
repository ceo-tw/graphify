# Tweaks Protocol

사용자는 디자인에서 툴바를 통해 **Tweaks** 를 on/off 할 수 있다 (Artifact 환경 한정). on 일 때는 페이지 내부에 컨트롤을 보여 사용자가 디자인 측면(색상, 폰트, 스페이싱, 카피, 레이아웃 변형, 피처 플래그 등)을 조정할 수 있게 한다.

**Tweaks UI 는 당신이 디자인한다**; 프로토타입 내부에 살며, 창·패널 제목은 **"Tweaks"** 로 툴바 토글명과 일치시킨다.

> **Claude Code 환경에서의 주의**: Artifact 호스트가 없으므로 `__edit_mode_set_keys` postMessage 가 디스크에 다시 쓰는 메커니즘은 동작하지 않는다. 그러나 프로토콜을 구현해 두면 Artifact 환경으로 이식하거나, 향후 대응 호스트가 생겼을 때 바로 동작한다. 현재는 사용자가 값 변경 시 페이지 내에서만 적용된다 (새로고침 시 기본값으로 복귀).

---

## Protocol

### 순서가 중요: listener 먼저, announce 나중

`__edit_mode_available` 를 먼저 post 하면 호스트의 activate 메시지가 핸들러 존재 전에 도착해 토글이 조용히 실패할 수 있다.

**1. 먼저** `window` 에 `message` listener 등록:

```js
window.addEventListener('message', (e) => {
  if (e.data?.type === '__activate_edit_mode') {
    showTweaksPanel();
  } else if (e.data?.type === '__deactivate_edit_mode') {
    hideTweaksPanel();
  }
});
```

**2. 그 후 — listener 가 살아있을 때만** 호출:

```js
window.parent.postMessage({ type: '__edit_mode_available' }, '*');
```

이 호출이 툴바 토글을 표시시킨다.

### 값 변경 시

사용자가 값을 바꾸면 페이지에 라이브 반영하고 영속화를 위해 호출:

```js
window.parent.postMessage({
  type: '__edit_mode_set_keys',
  edits: { fontSize: 18 }
}, '*');
```

부분 업데이트 가능 — 포함한 키만 머지된다.

---

## State 영속화

tweak 가능 기본값을 comment marker 로 감싼다. 호스트가 디스크에 다시 쓸 수 있도록.

```html
<script>
const TWEAK_DEFAULS = /*EDITMODE-BEGIN*/{
  "primaryColor": "#D97757",
  "fontSize": 16,
  "dark": false
}/*EDITMODE-END*/;
</script>
```

### 규칙

- marker 사이 블록은 **유효한 JSON** 이어야 한다 (키·문자열 모두 쌍따옴표)
- 루트 HTML 파일의 inline `<script>` 안에 **정확히 하나**만 존재
- `__edit_mode_set_keys` 가 도착하면 호스트가 JSON을 파싱해 edits 를 머지하고 파일에 다시 쓴다 — 변경이 새로고침 후에도 유지

---

## Tips

- Tweaks 표면은 작게 유지 — 화면 오른쪽 아래 floating panel 또는 inline handle. 과도하게 만들지 말 것.
- Tweaks off 일 때는 컨트롤을 완전히 숨긴다; 디자인은 최종본처럼 보여야 한다.
- 사용자가 큰 디자인 안의 단일 요소에 대한 여러 변형을 요청하면, Tweaks 로 옵션들을 순환할 수 있게 한다.
- 사용자가 tweak 를 요청하지 않아도 기본으로 몇 개 노출해 흥미로운 가능성을 보여준다.
