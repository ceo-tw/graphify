---
name: quick
type: workflow
description: "단순 작업을 위한 빠른 경로. 단일 파일 수정, 타이포 수정, 설정 변경 등 간단한 작업을 즉시 처리합니다. 사용 시점: (1) 단일 파일의 간단한 수정이 필요할 때, (2) 타이포나 설정값 변경 등 즉시 처리 가능한 작업일 때. /quick 커맨드로 호출."
argument-hint: [작업 설명]
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Skill
user-invocable: true
---

# Quick Mode Skill

단순하고 명확한 작업을 빠르게 처리하는 스킬입니다. 완전한 planning 워크플로우 없이 간소화된 절차로 실행합니다.

---

## 1. Quick Mode 조건 (Auto-Detection)

다음 조건을 **모두** 만족할 때만 Quick Mode 진입:

| 조건 | 설명 |
|------|------|
| **단일 파일** | 수정 대상이 1개 파일만 |
| **명확한 의도** | 무엇을 어떻게 할지 분명함 |
| **낮은 복잡도** | 타이포, 설정 변경, 단순 버그 |
| **테스트 불필요** | 로직 변경 없음 또는 기존 테스트로 충분 |

### Quick Mode 적합 예시

```
✅ "AGENTS.md에서 오타 수정해줘"
✅ "package.json에서 버전을 1.2.0으로 변경"
✅ ".env.example에 새 환경변수 추가"
✅ "README의 설치 명령어 업데이트"
✅ "tsconfig.json에서 strict 옵션 켜기"
```

### Quick Mode 부적합 예시 (→ /wm 사용)

```
❌ "로그인 기능 추가" (새 기능 개발)
❌ "API 에러 수정하고 테스트도 추가" (복잡한 버그 + 테스트)
❌ "2개 파일 수정: auth.ts와 user.ts" (다중 파일)
❌ "리팩토링: 중복 코드 제거" (영향 범위 불명확)
```

---

## 2. Workflow

```
/quick <요청>
    │
    ├─► 작업 설명 수집 (AskUserQuestion if needed)
    │
    ├─► 번호 계산 (.claude/quick/ 디렉토리)
    │   ├─ Glob: .claude/quick/*/
    │   └─ Next number: max + 1
    │
    ├─► 작업 디렉토리 생성
    │   └─ .claude/quick/{number}-{short-name}/
    │
    ├─► 간소화된 계획 작성
    │   ├─ plan.md (1-3 tasks)
    │   └─ 검증 방법 (선택)
    │
    ├─► 직접 실행
    │   ├─ 파일 수정 (Edit/Write)
    │   ├─ 린트 실행 (해당 시)
    │   └─ 간단한 검증
    │
    └─► 상태 업데이트
        └─ plan.md에 완료 체크
```

---

## 3. 작업 번호 계산

기존 작업 번호를 조회하여 다음 번호 결정:

```python
# 기존 작업 조회
existing_dirs = Glob(pattern=".claude/quick/*/")

# 번호 추출 및 정렬
numbers = [int(d.split('/')[-2].split('-')[0]) for d in existing_dirs if d.split('/')[-2][0].isdigit()]

# 다음 번호
next_number = max(numbers) + 1 if numbers else 1
```

---

## 4. 작업 디렉토리 생성

```python
# 작업명에서 short-name 추출
short_name = sanitize_name(user_request[:30])  # 예: "fix-typo-agents-md"

# 디렉토리 생성
work_dir = f".claude/quick/{next_number:03d}-{short_name}"
Bash(command=f"mkdir -p {work_dir}")
```

---

## 5. 간소화된 계획 작성

**파일**: `.claude/quick/{number}-{short-name}/plan.md`

```markdown
# Quick Task: {요청 요약}

## 요청 내용
{사용자 요청}

## 작업 계획 (1-3 tasks)

- [ ] TASK-001: {구체적 작업}
- [ ] TASK-002: {추가 작업 - 선택}
- [ ] TASK-003: {검증 - 선택}

## 변경 대상

- **파일**: {file_path}
- **변경 사항**: {무엇을 어떻게}

## 검증 방법 (선택)

- [ ] 린트 통과 (해당 시)
- [ ] 수동 확인 항목 (해당 시)

## 실행 시간

시작: {timestamp}
완료: {timestamp}
```

---

## 6. 직접 실행

Worktree 없이 main 브랜치에서 직접 실행:

### Step 1: 파일 수정

```python
# 파일 읽기
content = Read(file_path=target_file)

# 수정 (Edit 또는 Write)
if simple_replacement:
    Edit(
        file_path=target_file,
        old_string="...",
        new_string="..."
    )
else:
    Write(file_path=target_file, content=new_content)
```

### Step 2: 검증 (선택)

```python
# 린트 실행 (해당 파일 유형에 따라)
if target_file.endswith('.ts'):
    Bash(command=f"cd dashboard && bun run lint {target_file}")
elif target_file.endswith('.sh'):
    Bash(command=f"shellcheck {target_file}")
elif target_file.endswith('.py'):
    Bash(command=f"ruff check {target_file}")
```

### Step 3: 커밋 (선택 - 사용자 확인 필요)

```python
# 변경 사항 확인
git_status = Bash(command="git status --short")

# 사용자 확인
response = AskUserQuestion(questions=[{
    "question": f"다음 변경을 커밋하시겠습니까?\n{git_status.output}",
    "options": [
        {"label": "예", "description": "변경 사항 커밋"},
        {"label": "아니오", "description": "커밋하지 않음"}
    ]
}])

if response.get("답변") == "예":
    Bash(command=f"""
        git add {target_file} && \
        git commit -m "quick: {commit_message}"
    """)
```

---

## 7. 상태 업데이트

실행 완료 후 plan.md 업데이트:

```python
# 완료 체크박스 업데이트
Edit(
    file_path=f"{work_dir}/plan.md",
    old_string="- [ ] TASK-001:",
    new_string="- [x] TASK-001:"
)

# 완료 시간 기록
Edit(
    file_path=f"{work_dir}/plan.md",
    old_string="완료: {timestamp}",
    new_string=f"완료: {datetime.now().isoformat()}"
)
```

---

## 8. 완료 보고

```markdown
## ✅ Quick Task 완료

### 변경 내용
- **파일**: {file_path}
- **변경**: {summary}

### 검증 결과
- [x] 린트 통과 (해당 시)
- [x] 수동 확인 완료

### 작업 로그
- **위치**: {work_dir}/plan.md
- **실행 시간**: {duration}초

---

추가 작업이 필요하면 `/wm` 또는 `/quick`을 다시 실행하세요.
```

---

## 9. 에러 처리

| 상황 | 대응 |
|------|------|
| 파일 없음 | 경로 확인 후 재시도 또는 /wm으로 전환 |
| 다중 파일 감지 | Quick Mode 종료, /wm 권장 |
| 복잡도 높음 | Quick Mode 종료, /wm 권장 |
| 린트 실패 | 에러 메시지 표시, 수동 수정 안내 |

---

## 10. Quick Mode vs /wm 비교

| 항목 | Quick Mode | /wm (Full) |
|------|-----------|-----------|
| **대상** | 단일 파일, 단순 작업 | 다중 파일, 복잡한 작업 |
| **계획** | 간소 (1-3 tasks) | 완전 (PRD, Design, TASKS) |
| **Worktree** | ❌ 불필요 | ✅ 필수 (코드 변경 시) |
| **에이전트** | 없음 (직접 실행) | design, planner-task, dev-executor 등 |
| **검증** | 간단 (린트만) | 완전 (qa 에이전트) |
| **실행 시간** | < 1분 | 수 분 ~ 수십 분 |

---

## 11. 관련 Skill

| Skill | 용도 | 전환 조건 |
|-------|------|----------|
| `/wm` | 완전한 워크플로우 | Quick Mode 조건 불만족 시 |
| `/solve` | 복잡한 버그 수정 | 5 Whys 분석 필요 시 |
| `/dev-status` | 진행 상황 확인 | 전체 계획 상태 파악 시 |

---

## Summary

1. **조건 체크** - 단일 파일, 명확한 의도, 낮은 복잡도
2. **번호 계산** - 기존 작업 조회 후 다음 번호
3. **디렉토리 생성** - `.claude/quick/{number}-{short-name}/`
4. **간소 계획** - 1-3 tasks만 작성
5. **직접 실행** - Worktree 없이 main에서 수정
6. **상태 업데이트** - plan.md 체크박스 업데이트
7. **완료 보고** - 변경 요약 및 검증 결과

---

## Notes

- Quick Mode는 **명확하고 단순한** 작업만 처리합니다
- 조건이 맞지 않으면 즉시 `/wm`으로 전환하세요
- 코드 로직 변경은 Quick Mode 부적합 (테스트 필요)
- 설정 파일, 문서, 타이포는 Quick Mode 적합
