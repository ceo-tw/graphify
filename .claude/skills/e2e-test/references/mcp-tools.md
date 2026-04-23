# Playwright MCP Tools Reference

`playwright@claude-plugins-official` 플러그인에서 제공하는 도구 목록.

> **Note**: 모든 도구의 full name은 `mcp__playwright__<tool_name>` 형식입니다.
> (예: `mcp__playwright__playwright_navigate`)

---

## Browser Navigation

| Tool | Description |
|------|-------------|
| `playwright_navigate` | URL로 이동 |
| `playwright_go_back` | 이전 페이지로 이동 |
| `playwright_go_forward` | 다음 페이지로 이동 |
| `playwright_close` | 브라우저 종료 |

---

## Browser Interaction

| Tool | Description |
|------|-------------|
| `playwright_click` | 요소 클릭 |
| `playwright_fill` | 입력 필드에 텍스트 입력 |
| `playwright_hover` | 요소에 호버 |
| `playwright_drag` | 드래그 앤 드롭 |
| `playwright_press_key` | 키보드 키 누르기 |
| `playwright_select` | select 요소에서 옵션 선택 |
| `playwright_upload_file` | 파일 업로드 |
| `playwright_iframe_click` | iframe 내 요소 클릭 |
| `playwright_iframe_fill` | iframe 내 입력 필드에 텍스트 입력 |
| `playwright_resize` | 브라우저 뷰포트 크기 조정 |

---

## Page Inspection

| Tool | Description |
|------|-------------|
| `playwright_get_visible_text` | 페이지의 가시 텍스트 가져오기 |
| `playwright_get_visible_html` | 페이지의 HTML 가져오기 |
| `playwright_screenshot` | 스크린샷 캡처 (저장 위치: `.playwright-mcp/`) |
| `playwright_console_logs` | 콘솔 로그 조회 |
| `playwright_evaluate` | JavaScript 실행 |
| `playwright_save_as_pdf` | 페이지를 PDF로 저장 |

### Screenshot Path Standard

**MANDATORY**: All E2E test screenshots MUST be saved to `.playwright-mcp/` with session-based naming.

**File Naming Convention**:
```
{session-id}-{timestamp}-{name}.png
```

**Example Usage**:
```python
# Use downloadsDir parameter to specify standard path
playwright_screenshot(
    name="login-page",
    downloadsDir=".playwright-mcp/"
)

# Session-based filename: abc123-20260119-143020-login-page.png
```

**Why Session-Based Naming:**
- Tracks which screenshots belong to which test session
- Enables targeted cleanup after workflow completion
- Prevents file conflicts across concurrent sessions
- Facilitates debugging by linking screenshots to session context

> **Screenshot Storage**: All E2E test screenshots are saved to `.playwright-mcp/` and auto-cleaned after workflow completion.

---

## Session Management

| Tool | Description |
|------|-------------|
| `start_codegen_session` | 코드 생성 세션 시작 |
| `end_codegen_session` | 코드 생성 세션 종료 및 테스트 파일 생성 |
| `get_codegen_session` | 세션 정보 조회 |
| `clear_codegen_session` | 세션 정리 (테스트 미생성) |

---

## HTTP Requests

| Tool | Description |
|------|-------------|
| `playwright_get` | HTTP GET 요청 |
| `playwright_post` | HTTP POST 요청 |
| `playwright_put` | HTTP PUT 요청 |
| `playwright_patch` | HTTP PATCH 요청 |
| `playwright_delete` | HTTP DELETE 요청 |

---

## Response Handling

| Tool | Description |
|------|-------------|
| `playwright_expect_response` | HTTP 응답 대기 시작 |
| `playwright_assert_response` | HTTP 응답 검증 |

---

## Tab Management

| Tool | Description |
|------|-------------|
| `playwright_click_and_switch_tab` | 링크 클릭 후 새 탭으로 전환 |

---

## Custom Settings

| Tool | Description |
|------|-------------|
| `playwright_custom_user_agent` | 사용자 에이전트 설정 |

---

## Cleanup Protocol

**모든 작업 전 필수:**

```python
# 1. 브라우저 종료
mcp__playwright__playwright_close()

# 2. 세션 정리 (ID가 있는 경우)
mcp__playwright__clear_codegen_session(sessionId="...")
```

---

## 도구 사용 예시

### 페이지 탐색
```python
# URL로 이동
playwright_navigate(url="https://example.com")

# 페이지 구조 확인
html = playwright_get_visible_html()
```

### 폼 입력
```python
# 입력 필드에 텍스트 입력
playwright_fill(selector="input[name='email']", value="test@example.com")

# 버튼 클릭
playwright_click(selector="button[type='submit']")
```

### 세션 기반 테스트 생성
```python
# 1. 세션 시작
start_codegen_session(options={"outputPath": "/path/to/tests"})

# 2. 페이지 탐색 및 상호작용
playwright_navigate(url="https://example.com")
playwright_click(selector="button")

# 3. 세션 종료 및 테스트 파일 생성
end_codegen_session(sessionId="session-id")
```
