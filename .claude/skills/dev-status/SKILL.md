---
name: dev-status
type: workflow
description: "개발 워크플로우 진행 상황을 확인합니다. 현재 단계, 완료된 문서, 태스크 상태를 보여줍니다. 사용 시점: (1) 현재 개발 진행 상황을 파악할 때, (2) 워크플로우의 어느 단계에 있는지 확인할 때. /dev-status 커맨드로 호출."
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
user-invocable: true
---

# dev-status

개발 워크플로우 진행 상황을 한눈에 확인하는 스킬입니다.

## Usage

```
/dev-status
/dev-status [plan-name]
```

**Examples:**
```
/dev-status                    # 모든 활성 계획 상태
/dev-status payment-system     # 특정 계획 상세 상태
```

---

## Workflow

```
/dev-status
    │
    ├─► 활성 계획 문서 검색 (.claude/plans/)
    │
    ├─► 각 계획별 상태 분석
    │   ├─ PRD 존재 여부
    │   ├─ Architecture 완료 여부
    │   ├─ Tasks 정의 여부
    │   └─ 현재 Phase/Task 진행률
    │
    └─► 요약 리포트 출력
```

---

## Output Format

### 전체 상태 보기

```
============================================
📊 개발 워크플로우 상태
============================================

🔄 활성 계획: 2개

┌─────────────────────────────────────────┐
│ 1. payment-system                       │
├─────────────────────────────────────────┤
│ 단계: Design (2/5)                      │
│ 진행률: ████████░░░░░░░░ 40%           │
│ 현재: Architecture 설계 중              │
│ 마지막 업데이트: 2025-01-11 09:30       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 2. user-auth                            │
├─────────────────────────────────────────┤
│ 단계: Implementation (4/5)              │
│ 진행률: █████████████░░░ 80%           │
│ 현재: TASK-005 구현 중                  │
│ 마지막 업데이트: 2025-01-11 10:15       │
└─────────────────────────────────────────┘

============================================
```

### 특정 계획 상세 보기

```
============================================
📋 payment-system 상세 상태
============================================

📄 문서 상태:
  ✅ PRD:          .claude/plans/PLAN_payment-system.md
  ✅ Architecture: 포함됨
  ✅ ERD:          포함됨
  🔄 Tasks:        8개 정의됨

📊 Phase 진행률:

  PHASE 1: 결제 모듈 기초 설계 ✅
  ├─ TASK-001: Domain 엔티티 정의 ✅
  ├─ TASK-002: Repository 인터페이스 ✅
  └─ TASK-003: UseCase 정의 ✅

  PHASE 2: 결제 처리 구현 🔄 (현재)
  ├─ TASK-004: PG 연동 어댑터 ✅
  ├─ TASK-005: 결제 요청 처리 🔄 ← 현재
  ├─ TASK-006: 결제 확인 처리 ⏳
  └─ TASK-007: 에러 핸들링 ⏳

  PHASE 3: 테스트 및 QA ⏳
  └─ TASK-008: E2E 테스트 ⏳

📈 전체 진행률: 50% (4/8 Tasks)

============================================
```

---

## Implementation

### Step 1: 활성 계획 검색

```python
# .claude/plans/ 에서 PLAN_*.md 파일 검색
plans = Glob(pattern=".claude/plans/PLAN_*.md")

if not plans:
    print("📭 활성 계획이 없습니다.")
    print("   /planner <요청> 으로 새 개발을 시작하세요.")
    return
```

### Step 2: 계획별 상태 분석

```python
for plan_path in plans:
    content = Read(file_path=plan_path)

    status = {
        "name": extract_plan_name(plan_path),
        "has_prd": "## PRD" in content or "## 요구사항" in content,
        "has_arch": "## Architecture" in content or "## 아키텍처" in content,
        "has_erd": "## ERD" in content,
        "phases": extract_phases(content),
        "tasks": extract_tasks(content),
        "current_phase": detect_current_phase(content),
        "current_task": detect_current_task(content),
        "progress": calculate_progress(content),
        "last_updated": get_file_mtime(plan_path)
    }
```

### Step 3: 진행률 계산

```python
def calculate_progress(content):
    """
    진행률 계산 로직
    - ✅ 완료된 태스크 카운트
    - 🔄 진행 중 태스크 카운트
    - ⏳ 대기 중 태스크 카운트
    """
    completed = content.count("✅") or content.count("[x]")
    in_progress = content.count("🔄") or content.count("[ ]")
    pending = content.count("⏳")

    total = completed + in_progress + pending
    if total == 0:
        return 0

    # 진행 중은 50% 가중치
    return int((completed + in_progress * 0.5) / total * 100)
```

### Step 4: 결과 출력

```python
def print_status(plans_status):
    print("=" * 44)
    print("📊 개발 워크플로우 상태")
    print("=" * 44)
    print()
    print(f"🔄 활성 계획: {len(plans_status)}개")
    print()

    for idx, status in enumerate(plans_status, 1):
        print_plan_card(idx, status)
```

---

## Related Skills

```
  Skill        Purpose           When to Use
  ───────────  ────────────────  ──────────────────────────────
  /planner     새 개발 시작      상태 확인 후 새 기능 개발 시
  /dev-status  진행 상황 확인    현재 작업 상태 파악 시
  /research    기술 조사         개발 전 기술 검토 시
  ───────────  ────────────────  ──────────────────────────────
```

---

## Error Handling

```
  상황              대응
  ────────────────  ─────────────────────────────
  활성 계획 없음    /planner 안내 메시지 출력
  파일 읽기 실패    해당 계획 스킵, 경고 메시지
  진행률 계산 불가  0%로 표시, 수동 확인 권장
  ────────────────  ─────────────────────────────
```

---

## Notes

- 계획 문서 형식이 표준을 따르지 않으면 정확한 분석이 어려울 수 있습니다
- `.claude/plans/complete/`로 이동된 계획은 표시되지 않습니다
- 실시간 상태가 아닌 문서 기반 분석입니다
