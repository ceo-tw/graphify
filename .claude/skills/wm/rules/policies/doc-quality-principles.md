# Document Quality Principles

> 프로젝트 문서 품질 3원칙. skill/agent 산출물 작성 시 참조. 프로젝트-중립 규칙 — 코드 인용 예시 경로는 현재 저장소 기준으로 해석한다.

## 1. 3원칙 정의

### 원칙 1: 인라인 인용 `[n]`

주장이나 데이터를 제시한 직후 `[n]` 마커로 출처를 명시한다. 문서 하단에 reference table을 배치하여 번호와 실제 출처를 매핑한다. 코드 인용은 `path:line` 또는 `path:line-line` 형식을 사용하며, 외부 링크는 full URL, 내부 파일은 repo 루트 기준 상대경로로 표기한다.

- 문서 하단 reference table 형식: `[n] URL / 파일경로:라인 / 커밋 SHA`
- 코드 인용 예시: `graphify/build.py:42-58`
- 외부 링크 예시: `https://networkx.org/documentation/stable/reference/classes/digraph.html`

### 원칙 2: Narrative prose (서술형 산문)

단락당 4-5 문장으로 완결된 서술을 작성한다. 섹션당 300-800 단어를 목표로 하며, 독자가 맥락 없이 읽어도 이해할 수 있는 자기완결적 서술을 지향한다. 불릿 목록 남용은 금지이며, Background/Rationale/Postmortem 컨텍스트에 한정하여 사용한다.

### 원칙 3: Table-first (테이블 우선)

2개 이상의 대안을 비교할 때는 테이블을 필수로 사용한다. trade-off 분석, 매트릭스 형태의 데이터는 모두 테이블로 표현하며, 각 행은 원자적으로 구성한다(한 가지 축만 비교). 복합 개념은 별도 테이블로 분리하여 가독성을 높인다.

---

## 2. 적용 매트릭스

| 문서 타입 | 인라인 인용 [n] | Narrative prose | Table-first |
|---|:-:|:-:|:-:|
| ADR | O | O | O (대안 비교) |
| 포스트모템 | O | O (재발 방지 200+ 단어) | O (원인 비교) |
| Research 리포트 (`/research --report`) | O | O | O |
| Confluence 운영 문서 | O | O | O |
| Security 리뷰 리포트 | O (`path:line`) | O (Executive Summary 200-400 단어) | O (카테고리×심각도×영향) |
| Plan 체크리스트 (이 plan 포함) | - | - | O (선택) |
| Jira 이슈 설명 | - | - | O (선택) |
| PR 설명 | - | - | - |
| Commit message | - | - | - |

---

## 3. Anti-patterns

다음 패턴은 문서 품질 원칙 위반으로 간주한다.

- "모든 출력에 인용 강제" — plan 체크리스트/PR/commit은 인용 불필요. 적용 매트릭스를 먼저 확인할 것.
- "Plan 문서에 narrative 강제" — 체크리스트 기반 실행 문서는 prose가 오히려 실행 흐름을 저해한다.
- "Bullet list로 dump" — 비교 데이터는 테이블, 설명은 prose로 분리. 불릿은 열거가 아닌 나열이 필요할 때만 사용.
- "Reference table 누락" — `[n]` 마커만 있고 하단 테이블이 없으면 인용 원칙 위반이다.

---

## 4. 비적용 범위

이 원칙은 아래 산출물에는 적용하지 않는다.

- Jira ticket 설명 (PM/개발자 혼합 독자, 체크리스트 선호)
- PR 설명 템플릿 (GitHub UI 렌더링 제약, 짧은 요약 선호)
- Commit message (Conventional Commits 규약 — narrative 배제)
- Plan 체크리스트 (실행 중심, 체크박스 필수)
- dev-executor / bug-fixer / planner-task agent 프롬프트 (실행 에이전트 — prose 추가 시 token 낭비)

---

## 5. 참조

이 정책의 소비자는 다음과 같다.

- `.claude/skills/research/SKILL.md` — `--report` 모드에서 인용 및 narrative prose 규칙 적용
- `.claude/agents/design.md` — Background block 작성 시 narrative prose 규칙 적용
- `.claude/agents/security-reviewer.md` — 리포트 형식 (Executive Summary, path:line 인용, 카테고리×심각도 테이블)
- `.claude/skills/solve/` — 포스트모템 템플릿 (재발 방지 200+ 단어, 원인 비교 테이블)
- 상위 skill: `.claude/skills/wm/SKILL.md` Reference Materials 섹션
