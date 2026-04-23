# Tool Mapping: Artifact → Claude Code

원본 Artifact 환경의 전용 툴을 Claude Code 환경에서 어떻게 대체하는지 정리.

---

## 직접 대응 가능

| Artifact 툴 | Claude Code 대체 | 비고 |
|-------------|-----------------|------|
| `read_file` | `Read` | 동일 |
| `write_file` | `Write` | `asset` 파라미터는 제거 (Artifact 전용) |
| `list_files` | `Glob` 또는 `Bash("ls")` | |
| `grep` | `Grep` | |
| `delete_file` | `Bash("rm")` | 주의: 삭제 전 확인 |
| `copy_files` | `Bash("cp")` 또는 `Write` | |
| `str_replace_edit` | `Edit` | 거의 동일 |
| `view_image` | `Read` (이미지 자동 인식) | |
| `questions_v2` | `AskUserQuestion` | UI 포맷 다름, 10+ 질문 원칙 유지 |
| `update_todos` | `TodoWrite` | 동일 컨셉 |
| `invoke_skill` | `Skill` | 직접 매핑 |
| `set_project_title` | 해당 없음 | Claude Code 에 프로젝트 제목 개념 없음 |
| `connect_github` | 해당 없음 | `gh` CLI 가 있다고 가정 |
| `web_search` | `WebSearch` | 동일 |
| `web_fetch` | `WebFetch` | 동일 |

---

## Sub-agent 로 대체

| Artifact 툴 | Claude Code 대체 |
|-------------|-----------------|
| `fork_verifier_agent` | `Agent(subagent_type="design-verifier")` |
| `fork_verifier_agent({task: "..."})` | `Agent(subagent_type="design-verifier", prompt="Mode: directed-check\nFocus: ...")` |
| `gen_pptx` | `Agent(subagent_type="design-exporter")` | Playwright + pptxgenjs, screenshots mode. editable은 exit 2 stub. |

---

## Playwright MCP 로 대체 (design-verifier 내부 전용)

| Artifact 툴 | Claude Code 대체 |
|-------------|-----------------|
| `show_html` | `mcp__playwright__playwright_navigate(file://...)` |
| `get_webview_logs` | `mcp__playwright__playwright_console_logs` |
| `save_screenshot` / `multi_screenshot` | `mcp__playwright__playwright_screenshot` |
| `eval_js_user_view` | `mcp__playwright__playwright_evaluate` |
| `screenshot_user_view` | `mcp__playwright__playwright_screenshot` |

> 이 툴들은 **design-verifier 서브에이전트 내부에서만** 사용. 메인 스킬에서는 Playwright 를 직접 호출하지 않는다.

---

## 사용자 안내 텍스트로 대체

| Artifact 툴 | Claude Code 대체 |
|-------------|-----------------|
| `show_to_user(path)` | 사용자에게 `Bash("open '{path}'")` 또는 `file://...` 경로 텍스트 전달 |
| `done(path)` | 동일 — 사용자에게 열 방법 안내, 그 후 `design-verifier` 호출 |
| `open_for_print` | `Bash("open '{path}'")` + 사용자에게 Cmd+P 안내 |
| `present_fs_item_for_download` | 파일: 경로 안내 / 폴더: `Bash("zip -r ... ...")` 후 경로 |
| `get_public_file_url` | 해당 없음 — 공용 URL 생성 메커니즘 없음 |

---

## 별도 구현 필요 (현재 미지원)

<!-- 향후 확장: 아래 기능들은 Claude Code 에서 네이티브 대응이 없다. 주석으로 남겨두어 확장 시 참조 가능.

| Artifact 툴 | 필요한 외부 도구 |
|-------------|----------------|
| `super_inline_html` | Node 기반 HTML 인라이너 (data URI 변환, font base64 embed) |
| `copy_starter_component` | 스킬 `assets/` 디렉토리 (현재 범위 외 결정) |
| `register_assets` / `unregister_assets` | Claude.ai UI 자산 리뷰 팬 전용 — Claude Code 대응 없음 |
| `save_as_template` | Claude.ai 템플릿 시스템 전용 |
| `snip` | Claude Code 는 컨텍스트 압축을 자동 처리 |

이들은 SKILL.md 의 "Future Extensions" 섹션에 주석으로 남겨 확장 계획을 보존한다.
-->

---

## GitHub 통합

원본의 `github_*` 툴 대신 `gh` CLI 를 사용한다.

| Artifact 툴 | Claude Code 대체 |
|-------------|-----------------|
| `github_list_repos` | `Bash("gh repo list")` 또는 `Bash("gh api users/USERNAME/repos")` |
| `github_get_tree` | `Bash("gh api repos/OWNER/REPO/git/trees/REF?recursive=1")` |
| `github_read_file` | `Bash("gh api repos/OWNER/REPO/contents/PATH?ref=REF --jq .content | base64 -d")` |
| `github_import_files` | `gh api` 로 파일 내용 가져온 후 `Write` 로 저장 |

### 사용 플로우

1. 사용자가 `github.com/OWNER/REPO/tree/REF/PATH` URL 을 제공
2. URL 파싱: OWNER / REPO / REF / PATH
3. `gh api` 로 트리 조회해 파일 목록 확인
4. 필요한 파일만 선택적으로 가져와 프로젝트 루트에 저장
5. `Read` 로 읽어 디자인 토큰·컴포넌트·스타일시트 추출

### 중요

`gh api` 는 트리 구조(파일 이름)만 보여준다. **반드시 전체 체인을 완료**: tree 조회 → 파일 가져오기 → Read. 훈련 데이터 기억으로 UI 를 재구성하지 말 것 — 실제 소스가 있으면 읽어서 정확한 값(hex, spacing scale, font stack, border radius) 을 추출한다.

타겟 파일 우선순위:
- Theme/color tokens (`theme.ts`, `colors.ts`, `tokens.css`, `_variables.scss`)
- 사용자가 언급한 특정 컴포넌트
- 글로벌 스타일시트·레이아웃 스캐폴드

---

## Starter Components (현재 범위 외)

원본 Artifact 의 `copy_starter_component` 는 Claude Code 에서 **포함하지 않기로** 결정되었다 (사용자 결정).

`design-executor` 는 각 산출물마다 필요한 구조(`<deck-stage>` 웹 컴포넌트, 디바이스 베젤, 애니메이션 엔진 등) 를 **references/*.md 의 패턴을 읽고 스크래치에서 작성**한다.

관련 references:
- `deck-authoring.md` — `<deck-stage>` 웹 컴포넌트 사양
- `react-babel-patterns.md` — React + Babel 기반 구조
- `tweaks-protocol.md` — Tweaks UI 프로토콜

<!-- 향후 확장: 반복 패턴이 많아지면 starter 파일을 `.claude/skills/design-artifact/assets/` 에 두고 `Bash("cp")` 로 복사하는 방식으로 전환 가능. -->

---

## PPTX 내보내기

`design-exporter` 에이전트가 담당한다. `design-artifact` SKILL의 Step 6 (Delivery)에서
`export_pptx === true` + `artifact_format === "deck"` 조건일 때만 호출된다.

| 항목 | 값 |
|------|-----|
| 모드 | `screenshots` (기본). `editable`은 향후 PHASE 7 구현 예정 — 현재 `exit 2` stub |
| 스크립트 | `.claude/skills/design-artifact/scripts/export-pptx.mjs` |
| 의존성 | Playwright + pptxgenjs (skill-local `node_modules/`) |
| 입력 | `<deck-stage>` HTML deck (권장) / fallback: 일반 HTML (single-page 모드) |
| 출력 | `.pptx` (screenshots 모드: 슬라이드당 풀블리드 PNG) |
| 상세 가이드 | [`references/pptx-export.md`](pptx-export.md) |
| Deck 요건 | [`references/deck-authoring.md`](deck-authoring.md) 의 "PPTX Export Contract" 섹션 |

주석으로 남겨둔 Future Extensions 중 PPTX 항목은 구현 완료되어 제거됨.
