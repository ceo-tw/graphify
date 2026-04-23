---
name: commit2
type: workflow
description: "Jira 티켓 번호를 포함한 git commit을 생성합니다. 변경된 소스 코드를 분석하여 관련 Jira 티켓을 자동으로 판단하고, Conventional Commits 형식으로 커밋합니다. 사용 시점: (1) 코드 변경 후 커밋할 때, (2) Jira 티켓 번호가 포함된 커밋이 필요할 때, (3) 'commit', '커밋', '커밋해줘' 등. /commit2 커맨드로 호출."
argument-hint: "[추가 커밋 메시지 힌트]"
allowed-tools:
  - Bash(git add:*)
  - Bash(git status:*)
  - Bash(git commit:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git branch:*)
  - AskUserQuestion
  - mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql
  - mcp__plugin_atlassian_atlassian__getJiraIssue
  - mcp__plugin_atlassian_atlassian__getTransitionsForJiraIssue
  - mcp__plugin_atlassian_atlassian__transitionJiraIssue
user-invocable: true
---

# commit2 -- Jira 티켓 연동 커밋

변경된 소스 코드를 분석하여 관련 Jira 티켓을 자동 판단하고, 티켓 번호를 포함한 Conventional Commits 형식으로 커밋한다.

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Workflow

### Step 1: 변경 분석

위 Context의 diff 내용을 분석하여 다음을 파악한다:
- 어떤 모듈/기능이 변경되었는지 (billing, admin-portal, agent 등)
- 변경의 성격 (새 기능, 버그 수정, 리팩토링 등)
- 핵심 키워드 추출 (변경과 관련된 도메인 용어)

### Step 2: Jira 티켓 검색

`mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql`을 사용하여 관련 티켓을 검색한다.

**검색 전략** (순서대로 시도, 결과가 나오면 중단):

1. **키워드 기반 검색**: 변경 내용에서 추출한 핵심 키워드로 검색
   - JQL: `project = PAW AND status != Done AND text ~ "{keyword}" ORDER BY created ASC`
   - 여러 키워드를 조합하여 정밀도를 높인다

2. **모듈 기반 검색**: 변경된 파일 경로에서 모듈명 추출
   - 예: `src/billing-api/` 변경 → `text ~ "billing"`
   - 예: `src/admin-portal/components/agents/` 변경 → `text ~ "agent"`

3. **최근 활성 티켓**: 넓은 범위로 최근 생성된 미완료 티켓 조회
   - JQL: `project = PAW AND status != Done ORDER BY created DESC`

**Jira 설정**:
- cloudId: `wondermove-official.atlassian.net`
- 기본 프로젝트: `PAW`

### Step 3: 티켓 결정

- **후보가 1개**: 해당 티켓 사용
- **후보가 2개 이상**: `created` 기준 가장 먼저 생성된 티켓 사용 (JQL에서 `ORDER BY created ASC`로 첫 번째 결과)
- **후보가 0개**: `AskUserQuestion`으로 사용자에게 티켓 번호 입력 요청
  - 질문 예: "관련 Jira 티켓 번호를 입력해주세요 (예: PAW-123). 변경 내용: {변경 요약}"

### Step 4: 커밋 생성

**커밋 메시지 형식** (프로젝트 기존 패턴 준수):

```
{type}({TICKET}): {description}
```

**Example:**
```
fix(PAW-60): Paddle 가격 동기화 + 취소 알림 메시지 개선
feat(PAW-51): TossPayments provider abstraction 추가
```

**type 결정 기준**:
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `refactor`: 동작 변경 없는 코드 구조 개선
- `test`: 테스트 추가/수정
- `docs`: 문서 변경
- `chore`: 빌드, 설정 등 기타 변경

**실행**: 관련 파일을 stage하고 커밋을 생성한다. 단일 메시지에서 tool call만 사용하고, 추가 텍스트는 출력하지 않는다.

### Step 5: Jira 티켓 완료 처리

커밋 성공 후, 커밋에 사용된 Jira 티켓을 "완료" 상태로 전환한다.

1. `getTransitionsForJiraIssue`로 해당 티켓의 가능한 전환 목록 조회
2. "완료" (또는 "Done") 전환 ID 확인
3. `transitionJiraIssue`로 티켓 상태를 "완료"로 전환
4. 전환 실패 시 경고만 출력하고 중단하지 않는다 (커밋은 이미 완료됨)

**Jira 설정**:
- cloudId: `wondermove-official.atlassian.net`
- 완료 전환 ID: `31` (PAW 프로젝트 기본값, 조회 결과와 다를 경우 조회된 값 사용)

## Rules

- 티켓 번호 없이는 절대 커밋하지 않는다
- 커밋 메시지는 한국어 또는 영어로 작성 (변경 내용에 맞춰 자연스럽게)
- HEREDOC을 사용하여 커밋 메시지를 전달한다
- 커밋할 변경 사항이 없으면 사용자에게 알리고 중단한다
