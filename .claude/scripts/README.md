# Claude Code Scripts

이 디렉토리는 Claude Code 자동화를 위한 스크립트를 포함합니다.

---

## Git Worktree 자동화 시스템

### 개요

계획 기반 개발을 지원하는 Git Worktree 자동화 시스템입니다.
`.claude/plans/`에 계획 파일이 생성되면 자동으로 독립된 worktree를 생성하여,
각 계획을 별도 브랜치에서 격리된 환경으로 작업할 수 있습니다.

### 핵심 원리

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  기존 방식                           │  Worktree 방식                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  한 디렉토리 = 한 브랜치              │  한 디렉토리 = 한 브랜치              │
│  브랜치 전환 시 파일 변경             │  각 계획마다 별도 디렉토리            │
│  동시 작업 불가                      │  여러 계획 동시 작업 가능             │
│  stash/commit 필요                  │  독립적 작업 환경                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 시스템 구성

### 파일 구조

```
.claude/
├── scripts/
│   ├── README.md                    # 이 문서
│   ├── worktree-manager.sh          # 메인 관리 스크립트
│   └── statusline-command.sh        # Status Line 커스텀 스크립트
├── hooks/
│   └── plan-worktree-hook.sh        # PostToolUse 자동 트리거 Hook
└── skills/
    └── worktree-manager/
        └── SKILL.md                 # Claude Code Skill 정의

docs/
├── plans/
│   ├── active/                      # 진행 중인 계획 (PLAN_*.md)
│   └── complete/                    # 완료된 계획
└── guides/
    └── worktree-automation.md       # 상세 사용 가이드

tree/                                # Worktree 디렉토리 (.gitignore됨)
└── {plan-name}/                     # 각 계획별 작업 공간
```

---

## 워크플로우

### 전체 흐름

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           [1. 계획 생성 단계]                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 사용자: "새 기능을 계획해줘"                                                   │
│         ↓                                                                   │
│ Claude: .claude/plans/PLAN_feature-x.md 생성                            │
│         ↓                                                                   │
│ Hook: 파일 생성 감지 → worktree-manager.sh create 호출                        │
│         ↓                                                                   │
│ 결과:                                                                       │
│   - ./tree/feature-x 디렉토리 생성                                           │
│   - plan/feature-x 브랜치 생성                                               │
│   - 해당 브랜치로 자동 전환                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                           [2. 작업 수행 단계]                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 작업: ./tree/feature-x 디렉토리에서 코드 작성/수정                             │
│   - 모든 변경사항은 plan/feature-x 브랜치에 기록                               │
│   - main 브랜치는 영향 없음                                                   │
│   - 다른 worktree와 독립적으로 작업 가능                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                           [3. 완료/중단 단계]                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ /worktree-complete feature-x 실행 시:                                        │
│   1. 미커밋 변경사항 커밋                                                     │
│   2. plan/feature-x → origin push                                           │
│   3. main 브랜치로 squash merge                                              │
│   4. worktree 및 브랜치 삭제                                                  │
│   5. 계획 파일 → .claude/plans/complete/YYYY-MM-DD/로 이동                    │
│                                                                             │
│ /worktree-abort feature-x 실행 시:                                           │
│   1. worktree 강제 삭제                                                      │
│   2. 로컬 브랜치 삭제                                                         │
│   3. 계획 파일은 active/에 유지 (재시도 가능)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 스크립트 사용법

### worktree-manager.sh

메인 관리 스크립트입니다.

```bash
# 사용법
.claude/scripts/worktree-manager.sh <command> [plan-name]

# 명령어
create   <name>   # 새 worktree 및 브랜치 생성
complete <name>   # 완료 처리 (push + squash merge + 정리)
abort    <name>   # 중단 처리 (worktree 삭제, 변경사항 버림)
list              # 활성 worktree 목록 표시
status   <name>   # 특정 worktree 상태 확인
```

### 예시

```bash
# 새 worktree 생성
.claude/scripts/worktree-manager.sh create user-auth
# 결과:
#   Path:   ./tree/user-auth
#   Branch: plan/user-auth

# 활성 worktree 확인
.claude/scripts/worktree-manager.sh list
# ┌──────────────────────┬────────────────────┬──────────────────┐
# │ Plan Name            │ Path               │ Branch           │
# ├──────────────────────┼────────────────────┼──────────────────┤
# │ user-auth            │ ./tree/user-auth   │ plan/user-auth   │
# └──────────────────────┴────────────────────┴──────────────────┘

# 상태 확인
.claude/scripts/worktree-manager.sh status user-auth

# 완료 처리
.claude/scripts/worktree-manager.sh complete user-auth

# 중단 처리
.claude/scripts/worktree-manager.sh abort user-auth
```

---

## Status Line 커스텀 스크립트

### 개요

`statusline-command.sh`는 Claude Code의 Status Line을 커스터마이즈하는 스크립트입니다.
현재 세션의 모델, 컨텍스트 사용량, 작업 디렉토리, Git 상태를 한눈에 볼 수 있도록 표시합니다.

### 표시 정보

```
[Opus] ████░░░░░░ 40.5% | ➜ project-name git:(main) ✗
 ^^^^^  ^^^^^^^^^^        ^   ^^^^^^^^^^^^  ^^^^    ^
 모델명  컨텍스트 사용량      디렉토리명       브랜치   변경사항
```

| 항목 | 설명 |
|------|------|
| 모델명 | 현재 사용 중인 Claude 모델의 첫 단어 (예: Opus, Sonnet) |
| 컨텍스트 사용량 | 10칸 프로그레스 바 + 퍼센트 |
| 디렉토리명 | 현재 작업 디렉토리의 basename |
| Git 브랜치 | 현재 체크아웃된 브랜치명 |
| 변경사항 표시 | `✗` - 커밋되지 않은 변경사항 있음 |

### 컨텍스트 사용량 색상

| 사용량 | 색상 | 의미 |
|--------|------|------|
| 0-49% | 초록 | 여유 있음 |
| 50-74% | 노랑 | 주의 필요 |
| 75-100% | 빨강 | 컨텍스트 압축 고려 |

### 설정 방법

Claude Code 설정에서 Status Line Command를 다음과 같이 설정합니다:

```bash
# Claude Code 설정 열기
claude config edit

# 또는 직접 설정 파일 수정
# ~/.claude/settings.json
```

```json
{
  "statusLineCommand": ".claude/scripts/statusline-command.sh"
}
```

### 요구사항

| 도구 | 용도 |
|------|------|
| jq | JSON 입력 파싱 |

---

## Claude Code Skill 명령어

Claude Code 대화에서 사용할 수 있는 slash 명령어입니다.

| 명령어 | 설명 |
|--------|------|
| `/worktree-list` | 활성 worktree 목록 표시 |
| `/worktree-status {name}` | 특정 worktree 상태 확인 |
| `/worktree-create {name}` | 수동으로 worktree 생성 |
| `/worktree-complete {name}` | 완료 처리 (squash merge) |
| `/worktree-abort {name}` | 중단 처리 |

---

## 자동 생성 조건

PostToolUse hook이 다음 조건에서 worktree를 자동 생성합니다:

1. **도구 조건**: `Write` 또는 `Edit` 도구 호출
2. **경로 조건**: `.claude/plans/PLAN_*.md` 패턴 일치
3. **중복 방지**: 해당 이름의 worktree가 존재하지 않음

### Hook 설정 위치

`.claude/settings.json`:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": ".claude/hooks/plan-worktree-hook.sh"
        }]
      }
    ]
  }
}
```

---

## 브랜치 전략

### 명명 규칙

| 유형 | 패턴 | 예시 |
|------|------|------|
| 계획 브랜치 | `plan/{plan-name}` | `plan/user-auth` |
| Worktree 경로 | `./tree/{plan-name}` | `./tree/user-auth` |
| 계획 파일 | `PLAN_{plan-name}.md` | `PLAN_user-auth.md` |

### Merge 전략

**Squash Merge**를 사용합니다:
- 계획의 모든 커밋을 하나로 합침
- main 브랜치 히스토리가 깔끔하게 유지됨
- 각 계획이 하나의 커밋으로 표현됨

```
# 예시 커밋 메시지
feat(plan): complete user-auth

Plan completed and merged via worktree-manager.
```

---

## 문제 해결

### Merge Conflict 발생 시

```bash
# 1. worktree에서 최신 main 가져오기
cd ./tree/{plan-name}
git fetch origin main
git rebase origin/main

# 2. conflict 해결
# ... 파일 수정 ...

git add .
git rebase --continue

# 3. 다시 complete 시도
.claude/scripts/worktree-manager.sh complete {plan-name}
```

### Worktree가 자동 생성되지 않을 때

```bash
# 1. Hook 로그 확인
cat .claude/hooks/hook.log

# 2. 수동으로 생성
.claude/scripts/worktree-manager.sh create {plan-name}
```

### 잘못된 Worktree 정리

```bash
# 모든 worktree 확인
git worktree list

# 강제 삭제
git worktree remove --force ./tree/{name}

# 잘못된 참조 정리
git worktree prune
```

---

## 요구사항

| 도구 | 최소 버전 | 용도 |
|------|----------|------|
| Git | 2.17+ | worktree 지원 |
| jq | 1.6+ | JSON 파싱 (hook용) |
| Bash | 4.0+ | 스크립트 실행 |

### 설치 확인

```bash
git --version      # git version 2.17 이상
jq --version       # jq-1.6 이상
bash --version     # GNU bash 4.0 이상
```

---

## 관련 문서

- [사용 가이드](../../docs/guides/worktree-automation.md) - 상세 사용 방법
- [Skill 정의](../skills/worktree-manager/SKILL.md) - Claude Code Skill
- [Planner Skill](../skills/planner/SKILL.md) - 계획 생성 통합

---

## 설계 결정

### 왜 Worktree인가?

| 대안 | 문제점 |
|------|--------|
| 브랜치 전환 | 작업 중 stash 필요, 동시 작업 불가 |
| 저장소 복제 | 디스크 공간 낭비, 동기화 복잡 |
| **Worktree** | 가볍고, 독립적, 한 저장소에서 관리 |

### 왜 Squash Merge인가?

| 대안 | 문제점 |
|------|--------|
| 일반 Merge | 히스토리가 복잡해짐 |
| Rebase | 충돌 해결이 복잡할 수 있음 |
| **Squash** | 깔끔한 히스토리, 계획 단위 커밋 |

### 왜 자동 생성인가?

- 개발자가 worktree 생성을 잊지 않음
- 일관된 명명 규칙 적용
- 계획 파일과 작업 환경 자동 연결
