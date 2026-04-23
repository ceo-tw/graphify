# Worktree Verifier Component

## Purpose

Verify that a Git worktree directory still exists before restoration.

## When to Verify

Check worktree only when:
- `checkpoint.worktree_path` is not null/empty
- Worktree was used for the saved session

## Implementation

```python
import os

def verify_worktree(worktree_path):
    """Verify worktree directory exists."""
    if not worktree_path:
        # No worktree used - working on main branch
        return {"valid": True, "worktree_path": None, "using_main": True}

    if os.path.isdir(worktree_path):
        return {"valid": True, "worktree_path": worktree_path, "using_main": False}

    return {
        "valid": False,
        "error": "worktree_expired",
        "worktree_path": worktree_path
    }
```

## Recovery Steps (When Worktree Expired)

```bash
# Get plan name from checkpoint
PLAN_NAME=$(jq -r '.plan_name // .current_work.plan_path | split("/")[-1] | rtrimstr(".md")' \
    .claude/workflow-checkpoint.json)

# Option 1: Recreate worktree
git worktree add tree/$PLAN_NAME plan/$PLAN_NAME
cd tree/$PLAN_NAME
git checkout plan/$PLAN_NAME
cd ../..
/restore-context

# Option 2: Delete checkpoint and restart
rm .claude/workflow-checkpoint.json
/wm "restart workflow"
```

## Error Display

When worktree is expired, display:

```
❌ Worktree가 만료되었습니다.

| 항목 | 값 |
|------|-----|
| 계획 이름 | {plan_name} |
| 만료된 경로 | {worktree_path} |

**복구 방법**:
1. Worktree 재생성:
   git worktree add tree/{plan_name} plan/{plan_name}

2. 마지막 커밋에서 파일 복원:
   cd tree/{plan_name}
   git checkout plan/{plan_name}

3. 복원 재시도:
   /restore-context
```
