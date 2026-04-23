---
name: plan-cleanup
type: workflow
description: "계획 완료 후 문서 정리를 수행합니다. 계획 파일을 complete 폴더로 이동하고 체크포인트를 삭제합니다. 사용 시점: (1) 개발 완료 후 계획 문서를 정리할 때, (2) 불필요한 체크포인트를 정리할 때. /plan-cleanup 커맨드로 호출."
argument-hint: [plan-name]
context: fork
allowed-tools:
  - Bash
  - Read
  - Glob
user-invocable: true
---

# Plan Cleanup

계획 완료 후 문서 정리를 위한 skill입니다.

## Usage

```bash
# 특정 계획 정리
/plan-cleanup <plan-name>

# 모든 활성 계획 정리
/plan-cleanup --all

# dry-run (실제 이동 없이 확인)
/plan-cleanup --dry-run
```

## Arguments

| Argument | Description |
|----------|-------------|
| `<plan-name>` | 정리할 계획 이름 (확장자 제외) |
| `--all` | 모든 활성 계획 파일 정리 |
| `--dry-run` | 실제 이동 없이 대상 파일 확인 |

## Logic

**Reference**: `rules/cleanup-logic.md`

### 1. 대상 파일 식별

```
# 이동 대상 - TO-BE 플랫 구조
.claude/plans/{feature-name}.md              # PRD (메인 계획 파일)
.claude/plans/{feature-name}-DESIGN.md       # 설계 문서 (통합)
.claude/plans/{feature-name}-TASKS-PHASE-*.md # PHASE별 태스크 문서

# 체크포인트 처리 (v4.0 multi-checkpoint)
.claude/workflow-checkpoint.json             # 해당 plan의 엔트리만 제거 (파일 전체 삭제 금지!)

# 제외 (이미 완료)
.claude/plans/complete/**/*
```

### 2. 처리 로직

```python
PROJECT_ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
today = datetime.now().strftime("%Y-%m-%d")
target_dir = f"{PROJECT_ROOT}/.claude/plans/complete/{today}"

# 1. 대상 디렉토리 생성
Bash(command=f"mkdir -p {target_dir}")

# 2. 계획 파일 이동 (TO-BE 플랫 구조)
if plan_name:
    # 특정 계획 - TO-BE 패턴
    base_patterns = [
        f"{plan_name}.md",           # PRD (메인 계획 파일)
        f"{plan_name}-DESIGN.md",    # 설계 문서 (통합)
    ]
    for pattern in base_patterns:
        Bash(command=f"mv {PROJECT_ROOT}/.claude/plans/{pattern} {target_dir}/ 2>/dev/null || true")

    # TASKS-PHASE-*.md 파일 (glob 패턴)
    Bash(command=f"mv {PROJECT_ROOT}/.claude/plans/{plan_name}-TASKS-PHASE-*.md {target_dir}/ 2>/dev/null || true")
else:
    # --all: 모든 활성 파일
    Bash(command=f"mv {PROJECT_ROOT}/.claude/plans/*.md {target_dir}/ 2>/dev/null || true")

# 3. 체크포인트 엔트리 제거 (v4.0 multi-checkpoint 대응)
# 주의: 파일 전체 삭제 금지! 해당 plan의 엔트리만 제거
checkpoint_file = f"{PROJECT_ROOT}/.claude/workflow-checkpoint.json"

# plan_name과 매칭되는 checkpoint 엔트리 제거 후 slot 재인덱싱
# 체크포인트가 0개가 되면 파일 삭제
Bash(command=f"""
if [ -f "{checkpoint_file}" ]; then
    # v4.0 형식 확인
    version=$(jq -r '.version // "1.0"' "{checkpoint_file}" 2>/dev/null)
    if [ "$version" = "4.0" ]; then
        # plan_name이 포함된 엔트리 제거 후 reindex
        jq --arg plan "{plan_name}" '
            .checkpoints = [.checkpoints[] | select(
                (.current_work.plan_path // "" | contains($plan) | not) and
                (.summary // "" | contains($plan) | not)
            )] |
            .checkpoints = [.checkpoints | to_entries[] | .value + {{"slot": .key}}]
        ' "{checkpoint_file}" > "{checkpoint_file}.tmp" && mv "{checkpoint_file}.tmp" "{checkpoint_file}"

        # 체크포인트가 0개면 파일 삭제
        count=$(jq '.checkpoints | length' "{checkpoint_file}" 2>/dev/null)
        if [ "$count" = "0" ]; then
            rm -f "{checkpoint_file}"
        fi
    else
        # v3.0 이하: 해당 plan의 체크포인트인 경우에만 삭제
        current_plan=$(jq -r '.current_work.plan_path // ""' "{checkpoint_file}" 2>/dev/null)
        if echo "$current_plan" | grep -q "{plan_name}"; then
            rm -f "{checkpoint_file}"
        fi
    fi
fi
""")

# 4. 결과 보고
Bash(command=f"ls -la {target_dir}/")
```

### 3. 결과 보고

```markdown
## Cleanup Report

### Moved Files
- [file list]

### Checkpoint Handling (v4.0 multi-checkpoint)
- 해당 plan의 체크포인트 엔트리 제거됨
- (체크포인트가 0개가 되면 파일 삭제됨)

### Target Directory
.claude/plans/complete/YYYY-MM-DD/
```

## Examples

### 특정 계획 정리

```bash
/plan-cleanup zazzy-herding-biscuit
```

**결과:**
```
.claude/plans/
└── complete/
    └── 2026-01-24/
        └── zazzy-herding-biscuit.md
```

### PRD 계획 정리 (관련 파일 포함)

```bash
/plan-cleanup snazzy-enchanting-brook
```

**결과 (TO-BE 플랫 구조):**
```
.claude/plans/
└── complete/
    └── 2026-01-24/
        ├── snazzy-enchanting-brook.md
        ├── snazzy-enchanting-brook-DESIGN.md
        ├── snazzy-enchanting-brook-TASKS-PHASE-1.md
        └── snazzy-enchanting-brook-TASKS-PHASE-2.md
```

### 모든 활성 계획 정리

```bash
/plan-cleanup --all
```

### Dry-run

```bash
/plan-cleanup --dry-run
```

**출력 (TO-BE 플랫 구조):**
```
[DRY-RUN] Would move:
  - .claude/plans/snazzy-enchanting-brook.md
  - .claude/plans/snazzy-enchanting-brook-DESIGN.md
  - .claude/plans/snazzy-enchanting-brook-TASKS-PHASE-1.md
  - .claude/plans/snazzy-enchanting-brook-TASKS-PHASE-2.md

[DRY-RUN] Would remove checkpoint entry for: snazzy-enchanting-brook
  (Note: 다른 workflow의 체크포인트는 유지됨)

Target: .claude/plans/complete/2026-01-24/
```

## Integration with Planner

Planner Step 7에서 자동 호출:

```python
# planner SKILL.md Step 7
Skill(skill="plan-cleanup", args=plan_name)
```
