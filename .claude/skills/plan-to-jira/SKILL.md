---
name: plan-to-jira
type: capability
description: "계획서를 Jira 이슈로 변환합니다. .claude/plans/*.md 파일에서 제목, 문제 정의, 요구사항을 추출하여 Jira 이슈를 생성하고 상세 계획을 댓글로 첨부합니다. 사용 시점: (1) 계획 완료 후 Jira 티켓이 필요할 때, (2) 'plan을 jira로', 'jira 티켓 생성', 'plan to jira' 등. /plan-to-jira 커맨드로 호출."
argument-hint: "[plan-file-path] [--project KEY] [--type 작업|스토리|버그]"
allowed-tools:
  - Read
  - Glob
  - AskUserQuestion
  - mcp__plugin_atlassian_atlassian__createJiraIssue
  - mcp__plugin_atlassian_atlassian__editJiraIssue
  - mcp__plugin_atlassian_atlassian__addCommentToJiraIssue
  - mcp__plugin_atlassian_atlassian__getVisibleJiraProjects
  - mcp__plugin_atlassian_atlassian__getJiraProjectIssueTypesMetadata
user-invocable: true
---

# plan-to-jira

`.claude/plans/` 계획서 파일을 Jira 이슈로 변환하는 스킬.

## Issue Type Rule (MUST)

**이슈 타입은 반드시 한글로 입력한다. 영문 이슈 타입명(Story, Bug, Task, Epic)을 절대 사용하지 않는다.**

- 이슈 생성 전 `getJiraProjectIssueTypesMetadata`로 프로젝트의 실제 이슈 타입 목록을 반드시 조회한다.
- 조회된 목록에서 한글 타입명을 사용한다 (예: 스토리, 버그, 작업, 에픽).
- 영문명으로 시행착오를 시도하는 것을 금지한다. 반드시 MCP 조회 결과 기반으로 정확한 타입명을 사용한다.

## Configuration

| 항목 | 값 |
|------|-----|
| cloudId | `wondermove-official.atlassian.net` |
| assignee | `622581bab7e7c7007158d1c3` (superman) |
| defaultProject | `PAW` |

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `[plan-file-path]` | 계획서 파일 경로 (생략시 자동 탐지) | 최근 plan 파일 |
| `--project KEY` | Jira 프로젝트 키 | 사용자에게 질문 |
| `--type TYPE` | 이슈 타입 (작업, 스토리, 버그) -- 반드시 한글 | 자동 감지 |

## Ticket Sizing Principle

**모든 티켓은 담당자 1명이 1-2일 내 완료 가능한 크기로 작성한다.**

- PHASE 단위가 아닌 개별 요구사항(체크박스) 단위로 티켓을 분해
- 하나의 체크박스가 너무 크면 (3일 이상 예상) 추가 분해
- 하나의 체크박스가 너무 작으면 (1시간 미만) 관련 항목과 병합

## Business Decision Gate (CRITICAL)

**티켓 생성 과정에서 비즈니스 의사결정이 필요한 사항을 발견하면 즉시 작업을 중단하고 `AskUserQuestion`으로 사용자에게 질문한다.**

중단이 필요한 상황:
- 요구사항 간 충돌이 발견된 경우
- PHASE 간 의존성이 불명확한 경우
- 티켓 분해 기준이 모호한 경우 (하나의 요구사항이 여러 도메인에 걸치는 등)
- 우선순위 판단이 필요한 경우
- 계획서에 "별도 판단", "TBD", "미정" 등 미결정 사항이 포함된 경우

**자동으로 추측하거나 임의로 결정하지 않는다.** 사용자의 명시적 답변을 받은 후에만 작업을 재개한다.

## Workflow

### Step 0: Plan 파일 결정

인자로 경로가 전달되면 해당 파일을 사용한다.

인자가 없으면 자동 탐지:
1. `Glob(".claude/plans/*.md")`로 파일 목록 조회
2. 제외 대상: `complete/` 하위, `-DESIGN.md`, `-TASKS-*.md`, `-REPORT.md` 접미사
3. 가장 최근 수정된 파일을 선택
4. `AskUserQuestion`으로 사용자 확인: "이 계획서로 Jira 이슈를 생성할까요? {파일명}"

### Step 1: Plan 파싱

`Read`로 파일을 읽고 다음을 추출한다:

- **제목**: 첫 번째 `# ` 헤더. codename 패턴(영문-영문-영문)이면 Section 1의 **목표** 첫 문장을 대신 사용.
- **Section 1** (Problem Definition): `## 1. Problem Definition` ~ `## 2.` 사이 내용
- **Section 2** (Requirements): `## 2. Clarified Requirements` ~ `## 3.` 사이 내용
- **Section 3** (Verification): `## 3. Verification Method` 이후 내용
- **Plan 타입**: Section 0에서 `NEW_DEVELOPMENT`, `MODIFICATION`, `BUG_FIX` 등 감지
- **PHASE 목록**: Section 2에서 `### PHASE N: {title}` 헤더와 하위 체크박스 항목

번호 없는 섹션(`## Context` 등)이면 첫 번째 `##` ~ 두 번째 `##` 사이를 description으로 사용.

### Step 2: Jira 프로젝트 결정 (MUST)

프로젝트 결정 우선순위:

1. **`--project` 인자가 있으면** 해당 값을 그대로 사용한다.
2. **Configuration의 `defaultProject`가 설정되어 있으면** 해당 값을 `AskUserQuestion`에서 "(Recommended)"로 제시한다.
3. **둘 다 없으면** `mcp__plugin_atlassian_atlassian__getVisibleJiraProjects`로 프로젝트 목록을 조회하고, `AskUserQuestion`으로 선택하도록 질문한다.

`AskUserQuestion` 사용 시:
- `defaultProject`가 있으면 해당 프로젝트를 첫 번째 옵션 + "(Recommended)"로 배치
- 나머지 옵션은 조회된 프로젝트 중 관련성 높은 것 (최대 3개)
- 사용자가 직접 입력할 수 있도록 "Other" 옵션 자동 제공

### Step 2.5: 이슈 타입 조회 (MUST -- 이슈 생성 전 반드시 실행)

**영문 이슈 타입명으로 시행착오를 하지 않기 위해, 이슈 생성 전 반드시 프로젝트의 실제 이슈 타입 목록을 MCP로 조회한다.**

1. `mcp__plugin_atlassian_atlassian__getJiraProjectIssueTypesMetadata` 호출:
   - `cloudId`: `wondermove-official.atlassian.net`
   - `projectKey`: Step 2에서 결정된 값
2. 응답에서 이슈 타입 목록을 추출하고, 한글 타입명을 확인한다.
3. 확인된 한글 타입명을 이후 Step 3, 4, 6에서 사용한다.
4. **만약 한글 타입명이 없는 프로젝트라면** (영문만 존재), 조회된 영문 타입명을 그대로 사용한다 (이 경우에만 영문 허용).

> **MUST**: 이 단계를 건너뛰고 영문 타입명을 추측하여 입력하는 것을 절대 금지한다.

### Step 3: Jira 파라미터 결정

1. `--type` 인자가 있으면 사용 (반드시 한글), 없으면 Plan 타입에서 자동 감지하되 **Step 2.5에서 조회한 실제 타입명**을 사용:
   - `NEW_DEVELOPMENT` / `MODIFICATION` -> `스토리` (조회 결과에서 매칭)
   - `BUG_FIX` -> `버그` (조회 결과에서 매칭)
   - 기타 (`INQUIRY`, `REPORT`, `CLEANUP`, `DOCUMENTATION`) -> `작업` (조회 결과에서 매칭)
2. `AskUserQuestion`으로 최종 확인:

```
Jira 이슈 생성 정보:
- 제목: {extracted_title}
- 프로젝트: {project_key}
- 이슈 타입: {issue_type}
- 담당자: superman
- 하위 티켓: {ticket_count}개 (PHASE/요구사항 기반)

진행할까요? (프로젝트/타입 변경이 필요하면 알려주세요)
```

### Step 3.5: 서비스 레이블 감지

계획서 내용(파일 경로, 서비스 언급)에서 관련 서비스를 자동 감지하여 레이블을 결정한다.

**레이블 목록**: `admin-portal`, `billing-api`, `admin-api`, `orbstack`, `env`

**감지 규칙:**

| 레이블 | 감지 조건 |
|--------|-----------|
| `admin-portal` | `src/admin-portal/` 경로 언급, 또는 "portal", "프론트엔드", "UI", "컴포넌트", "i18n" 등 키워드 |
| `admin-api` | `src/admin-api/` 경로 언급, 또는 "admin-api", "백엔드 API" 등 키워드 |
| `billing-api` | `src/billing-api/` 경로 언급, 또는 "billing", "Paddle", "결제" 등 키워드 |
| `orbstack` | `orbstack/` 경로 언급, 또는 "OrbStack", "로컬 K8s", "E2E 검증" 등 키워드 |
| `env` | `.env` 파일 변경 언급, 또는 "환경변수", "시크릿", "configmap" 등 키워드 |

**적용 규칙:**
1. 계획서 전체(Section 1~3)에서 감지. 하나의 계획서가 여러 서비스에 걸칠 수 있음.
2. 감지된 레이블을 `AskUserQuestion`으로 사용자에게 확인: "다음 레이블이 감지되었습니다: [admin-portal, admin-api]. 맞습니까?"
3. 사용자가 수정하면 수정된 레이블 사용.
4. 하위 티켓(Step 6)에는 해당 PHASE의 파일 경로를 기준으로 개별 레이블을 설정. PHASE별로 레이블이 다를 수 있음.

### Step 4: Jira Epic 이슈 생성

`mcp__plugin_atlassian_atlassian__createJiraIssue` 호출:

- `cloudId`: `wondermove-official.atlassian.net`
- `projectKey`: Step 2에서 결정된 값
- `issueTypeName`: Step 2.5에서 조회한 에픽 타입명 (예: `에픽`)
- `summary`: 추출된 제목 (max 255자, 초과시 truncate + "...")
- `description`: Section 1 + "\n\n---\n\n" + Section 3 (30,000자 초과시 truncate하고 "상세 내용은 첫 번째 댓글 참조" 추가)
- `contentFormat`: `"markdown"`
- `assignee_account_id`: `622581bab7e7c7007158d1c3`
- `duedate`: 오늘 날짜 기준 YYYY-MM-DD 형식 (예: `2026-03-31`). 계획서에 기한이 명시되어 있으면 해당 날짜 사용, 없으면 오늘 날짜 사용.
- `additional_fields`: `{ "labels": ["admin-portal", "admin-api", ...] }` (Step 3.5에서 감지/확인된 레이블)

생성된 이슈 키를 변수에 저장 (예: `CP-123`).

### Step 5: 상세 계획 댓글 첨부

`mcp__plugin_atlassian_atlassian__addCommentToJiraIssue` 호출:

- `cloudId`: `wondermove-official.atlassian.net`
- `issueIdOrKey`: Step 4에서 생성된 이슈 키
- `commentBody`: 전체 plan 파일 내용 (Section 0 포함, 원본 그대로)
- `contentFormat`: `"markdown"`

### Step 6: 하위 티켓 생성 (항상 실행)

**Ticket Sizing Principle에 따라 담당자 1명 기준으로 티켓을 분해한다.**

Section 2에서 추출한 PHASE 목록을 순회하며, 각 PHASE 내 체크박스 항목을 기준으로 티켓을 생성한다:

**분해 규칙:**
1. 각 체크박스 항목(`- [ ]`)을 하나의 티켓 후보로 간주
2. 관련성이 높고 작은 항목(1시간 미만)은 병합하여 하나의 티켓으로 생성
3. 큰 항목(3일 이상 예상)은 하위 단위로 추가 분해
4. 각 티켓 summary에 PHASE 번호를 접두사로 포함: `"[P{N}] {task_description}"`

각 티켓에 대해 `createJiraIssue` 호출:

- `projectKey`: Epic과 동일
- `issueTypeName`: Step 3에서 결정된 한글 타입명 (스토리, 작업, 버그 등 -- Step 2.5 조회 결과 기반)
- `summary`: `"[P{N}] {task_description}"` (1명이 처리 가능한 단위)
- `description`: **해당 PHASE 원본 섹션의 전체 원문을 verbatim으로 포함** (아래 규칙 참조)
- `contentFormat`: `"markdown"`
- `assignee_account_id`: `622581bab7e7c7007158d1c3`
- `duedate`: Epic과 동일한 기한 (YYYY-MM-DD 형식)
- `additional_fields`: `{ "labels": ["admin-portal", ...] }` (해당 PHASE의 파일 경로 기반으로 개별 레이블 설정. Epic의 전체 레이블이 아닌 PHASE별 관련 서비스만 포함)

**Description 작성 규칙 (MUST):**

1. **원문 그대로 복사한다.** 계획서에서 해당 PHASE 섹션(`### PHASE N:` ~ 다음 `### PHASE` 또는 `## 3.` 전까지)의 전체 내용을 description에 그대로 포함한다.
2. **요약, 압축, 재작성을 금지한다.** 테이블, 코드 블록, 유의 사항, 금지 사항 등 모든 하위 내용을 원본 그대로 유지한다.
3. **CRITICAL 항목 인라인 포함:** 해당 PHASE에서 참조하는 CRITICAL 항목(CRITICAL-1~4 등)의 원문도 함께 포함한다.
4. **공통 규칙 첨부:** "안전 중단 기준"과 "허용되는 변경 범위" 섹션이 계획서에 존재하면, 모든 하위 티켓의 description 하단에 해당 원문을 반복 첨부한다.
5. **30,000자 초과 시:** description을 truncate하고 나머지는 댓글로 첨부한다. truncate 지점에 "--- 이하 내용은 첫 번째 댓글 참조 ---" 표시.

PHASE가 없는 plan이면 전체 요구사항을 하나의 티켓으로 생성한다.

### Step 7: 결과 보고

사용자에게 결과를 출력한다:

```
Jira 이슈 생성 완료:
- Epic: {KEY}-{NUM}
- URL: https://wondermove-official.atlassian.net/browse/{KEY}-{NUM}
- 하위 티켓: {count}개
- 상세 계획이 댓글로 첨부되었습니다.
```
