# Merge Scenarios & Recovery Procedures

> This document is referenced from the main [SKILL.md](../SKILL.md).

---

## Merge Scenarios

### Scenario 1: Normal Complete (No Conflicts)

Standard case when no changes conflict with main.

```python
# 1. QA passes in worktree
# 2. Agent triggers complete with --yes for automation
Skill(skill="worktree-manager", args="complete {plan-name} --yes")
# 3. Squash merge succeeds
# 4. Plan moves to complete/
```

### Scenario 2: Main Has New Changes

When main has been updated while working in worktree.

**Handling:**
```bash
# The complete script handles this:
# 1. Pulls latest main
# 2. Attempts squash merge
# 3. If conflict -> reports to user (exit code 3)
```

**Agent Response to Conflict:**
```python
# If complete fails with exit code 3
AskUserQuestion(
    questions=[{
        "header": "Merge Conflict",
        "question": "Merge conflict detected. How would you like to proceed?",
        "options": [
            {"label": "Resolve manually", "description": "I will resolve conflicts in the worktree"},
            {"label": "Rebase on main", "description": "Rebase worktree branch on latest main"},
            {"label": "Abort merge", "description": "Cancel and keep worktree as-is"}
        ],
        "multiSelect": False
    }]
)
```

### Scenario 3: Merging Another Worktree First

When multiple worktrees exist and one needs to merge first.

**Check for conflicts:**
```bash
# List all active worktrees
.claude/scripts/worktree-manager.sh list

# Check if branches will conflict
git log --oneline main..plan/{plan-1}
git log --oneline main..plan/{plan-2}
```

**Recommended Order:**
1. Complete the worktree with fewer/simpler changes first
2. After merge to main, other worktrees should rebase

### Scenario 4: Partial Merge (Cherry-pick)

When only some changes should go to main.

**Manual Process:**
```bash
# On main branch
git checkout main

# Cherry-pick specific commits from worktree branch
git cherry-pick <commit-hash-1>
git cherry-pick <commit-hash-2>

# Keep worktree for remaining work
```

---

## Recovery and Rollback Procedures

### Recovery from Failed Complete

If `complete` fails mid-way, follow this recovery procedure:

```python
# 1. Check current state
result = Bash(command=".claude/scripts/worktree-manager.sh status {plan-name}")

# 2. If merge was in progress (exit code 3)
if "MERGING" in result.output:
    # Abort the merge on main
    Bash(command="git merge --abort")

    # Worktree is still intact, can retry later
    log_info("Merge aborted. Worktree preserved for retry.")

# 3. If worktree was partially removed (exit code 4)
if result.exit_code == 2:  # Worktree doesn't exist
    # Check if branch still exists
    branch_exists = Bash(command="git branch --list plan/{plan-name}")

    if branch_exists:
        # Recreate worktree from existing branch
        Bash(command="git worktree add tree/{plan-name} plan/{plan-name}")
```

### Manual Rollback Procedure

When automation fails completely, use manual recovery:

```bash
# 1. List current worktree state
git worktree list

# 2. If merge conflict on main, abort
git merge --abort

# 3. Return to main branch
git checkout main
git reset --hard origin/main  # Use with caution

# 4. Recreate worktree if needed
git worktree add tree/{plan-name} plan/{plan-name}

# 5. Or completely remove failed worktree
git worktree remove --force tree/{plan-name}
git branch -D plan/{plan-name}
```

### Fallback: Environment Variable Not Set

```python
# Safe PROJECT_ROOT acquisition with multiple fallbacks
def get_project_root():
    # Priority 1: Claude Code environment variable
    if os.environ.get('CLAUDE_PROJECT_DIR'):
        return os.environ['CLAUDE_PROJECT_DIR']

    # Priority 2: Git root
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()

    # Priority 3: Current working directory (last resort)
    return os.getcwd()

PROJECT_ROOT = get_project_root()
```

### Agent Retry Logic

```python
MAX_RETRIES = 3

def complete_worktree_with_retry(plan_name: str) -> dict:
    for attempt in range(MAX_RETRIES):
        result = Bash(
            command=f".claude/scripts/worktree-manager.sh complete {plan_name} --yes"
        )

        if result.exit_code == 0:
            return {"status": "success"}

        if result.exit_code == 3:  # Merge conflict - don't retry
            return {
                "status": "conflict",
                "requires_manual_resolution": True
            }

        # For other errors, wait and retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)  # Exponential backoff

    return {"status": "failed", "exit_code": result.exit_code}
```
