---
name: worktree-manager
type: workflow
description: "Git Worktree 기반 계획 관리 자동화. create/complete/abort/status 명령으로 worktree를 관리합니다. 사용 시점: (1) 새 계획을 위한 격리된 worktree를 생성할 때, (2) 완료된 계획을 main에 머지할 때, (3) worktree 상태를 확인할 때. /worktree-manager 커맨드로 호출."
argument-hint: create|complete|abort|status [plan-name]
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - TaskCreate
  - TaskGet
  - TaskUpdate
  - TaskList
  - AskUserQuestion
user-invocable: true
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[WORKTREE] Executing git operation...'"
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: "echo '[WORKTREE] Worktree operation completed.'"
---

# Worktree Manager Skill

Git Worktree-based plan management automation skill.

---

## CRITICAL: Environment Variables and Path Handling

### Getting PROJECT_ROOT

Claude Code sessions are fixed to their starting directory. When working with worktrees, you must use **absolute paths**.

**Method 1: Use $CLAUDE_PROJECT_DIR (Recommended)**
```bash
# Claude Code sets this environment variable
PROJECT_ROOT="${CLAUDE_PROJECT_DIR}"
worktree_path="${PROJECT_ROOT}/tree/{plan-name}"
```

**Method 2: Use pwd as fallback**
```bash
# If CLAUDE_PROJECT_DIR is not set
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
```

### Using Absolute Paths in Agents

When working in a worktree context, ALL file operations must use absolute paths:

```python
# Get PROJECT_ROOT from environment or pwd
import os
PROJECT_ROOT = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

# Construct absolute paths
worktree_path = f"{PROJECT_ROOT}/tree/{plan_name}"
file_to_read = f"{worktree_path}/src/file.ts"

# Use in tool calls
Read(file_path=file_to_read)
Edit(file_path=file_to_read, ...)
```

**IMPORTANT**: Relative paths like `src/file.ts` will read from the main project, NOT the worktree!

---

## Agent Trigger Methods

**Agents MUST use this skill via the Skill tool for worktree operations.**

### Direct Skill Invocation

```python
# Create worktree after PRD approval
Skill(
    skill="worktree-manager",
    args="create {plan-name}"
)

# Complete worktree after QA passes (with --yes for automation)
Skill(
    skill="worktree-manager",
    args="complete {plan-name} --yes"
)

# Check worktree status
Skill(
    skill="worktree-manager",
    args="status {plan-name}"
)
```

### When to Trigger

```
  Event                   Action            Trigger
  ──────────────────────  ────────────────  ──────────────────────────────────────────────────────────────
  PRD created & approved  Create worktree   Skill(skill="worktree-manager", args="create {plan}")
  QA passed               Complete & merge  Skill(skill="worktree-manager", args="complete {plan} --yes")
  User requests abort     Remove worktree   Skill(skill="worktree-manager", args="abort {plan}")
  ──────────────────────  ────────────────  ──────────────────────────────────────────────────────────────
```

---

## Commands

### /worktree-manager create

Creates a new worktree for a plan.

**Execution:**
```bash
# Default: create from main
.claude/scripts/worktree-manager.sh create "{plan-name}"

# With --base: create from specified branch
.claude/scripts/worktree-manager.sh create "{plan-name}" --base "{branch-name}"
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `{plan-name}` | Yes | Name of the plan (used for worktree directory and branch) |
| `--base {branch}` | No | Base branch to create worktree from. Default: creates `plan/{plan-name}` from `main` |

**What it does:**
1. Without `--base`: Creates branch `plan/{plan-name}` from main
2. With `--base {branch}`: Creates worktree at `tree/{plan-name}/` from the specified branch (e.g., a feature branch)
3. Returns the absolute path for file operations

**Agent Usage:**
```python
# Default: create from main
result = Skill(skill="worktree-manager", args="create evaluation-metrics")

# With --base: create from feature branch (used in development pipeline)
result = Skill(skill="worktree-manager", args="create evaluation-metrics --base feature/evaluation-metrics")

# Then use absolute paths for all file operations
PROJECT_ROOT = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
worktree_path = f"{PROJECT_ROOT}/tree/evaluation-metrics"
Read(file_path=f"{worktree_path}/src/target-file.ts")
```

### /worktree-manager complete

Completes a plan with squash merge to main.

**Execution:**
```bash
# Interactive mode (asks for confirmation)
.claude/scripts/worktree-manager.sh complete "{plan-name}"

# Non-interactive mode (auto-commits uncommitted changes)
.claude/scripts/worktree-manager.sh complete "{plan-name}" --yes
```

**What it does:**
1. Commits any uncommitted changes in worktree (auto with `--yes`)
2. Pushes branch to remote (if available)
3. Switches to main and pulls latest
4. Performs squash merge
5. Removes worktree and branch
6. Moves plan file to `.claude/plans/complete/YYYY-MM-DD/`

**Agent Usage:**
```python
# After QA passes - USE --yes FLAG FOR AUTOMATION
Skill(skill="worktree-manager", args="complete evaluation-metrics --yes")
```

### /worktree-manager abort

Aborts a plan and removes the worktree.

**Execution:**
```bash
.claude/scripts/worktree-manager.sh abort "{plan-name}"
```

**What it does:**
1. Force removes worktree
2. Deletes local branch
3. Keeps plan file in `active/` for retry

### /worktree-manager status

Shows status of a specific worktree.

**Execution:**
```bash
.claude/scripts/worktree-manager.sh status "{plan-name}"
```

**Returns JSON for automation:**
```json
{
  "plan_name": "feature-auth",
  "worktree_path": "/path/to/project/tree/feature-auth",
  "branch": "plan/feature-auth",
  "uncommitted_changes": 3,
  "commits_ahead_of_main": 5
}
```

### /worktree-manager list

Lists all active worktrees.

**Execution:**
```bash
.claude/scripts/worktree-manager.sh list
```

---

## Exit Codes

```
  Code  Meaning
  ────  ────────────────────────────────────────────────────
  0     Success
  1     General error (missing arguments, usage error)
  2     Worktree/branch does not exist
  3     Git operation failed (merge conflict, etc.)
  4     Filesystem error
  ────  ────────────────────────────────────────────────────
```

### Error Handling in Agents

```python
# Example error handling
result = Bash(command=".claude/scripts/worktree-manager.sh complete my-plan --yes")

if result.exit_code == 0:
    # Success - proceed with next steps
    pass
elif result.exit_code == 2:
    # Worktree doesn't exist
    log_error("Worktree not found")
elif result.exit_code == 3:
    # Merge conflict
    AskUserQuestion(
        questions=[{
            "header": "Merge Conflict",
            "question": "Merge conflict detected. How to proceed?",
            "options": [
                {"label": "Resolve manually", "description": "I'll resolve conflicts"},
                {"label": "Abort merge", "description": "Cancel and keep worktree"}
            ],
            "multiSelect": False
        }]
    )
elif result.exit_code == 4:
    # Filesystem error
    log_error("Filesystem error - check permissions")
```

---

> **Reference**: See [Merge Scenarios & Recovery](references/merge-recovery.md) for detailed merge scenarios (normal, conflict, cherry-pick) and recovery/rollback procedures.

---

## Workflow Integration

### Plan Approval → Worktree Creation

In `planner` skill, after user approves the PHASE plan:

```python
# Step 4-4: After approval
if user_selection == "승인 (Recommended)":
    # Create worktree
    plan_name = extract_plan_name(planning.prd_path)
    Skill(skill="worktree-manager", args=f"create {plan_name}")

    # Get absolute path
    PROJECT_ROOT = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    worktree_path = f"{PROJECT_ROOT}/tree/{plan_name}"

    # All subsequent file operations use this path
```

### QA Pass → Worktree Complete

In `qa` agent, after all validations pass:

```python
# Step 7: Git Operations
if qa_result == "PASS":
    # Use AskUserQuestion for confirmation
    AskUserQuestion(
        questions=[{
            "header": "Worktree Complete",
            "question": "QA passed. Complete worktree and merge to main?",
            "options": [
                {"label": "Complete & Merge (Recommended)", "description": "Squash merge to main, remove worktree"},
                {"label": "Commit only", "description": "Commit changes but keep worktree"},
                {"label": "Skip", "description": "No git operations"}
            ],
            "multiSelect": False
        }]
    )

    if selection == "Complete & Merge":
        # USE --yes FLAG FOR AUTOMATION
        Skill(skill="worktree-manager", args=f"complete {plan_name} --yes")
```

---

## Tips

1. **Always use --yes for automation** - Prevents blocking on interactive prompts
2. **Always use absolute paths** - Worktree paths need full paths, not relative
3. **Check exit codes** - Handle errors gracefully using exit code values
4. **Commit frequently** - More commits = better squash merge message
5. **One plan per worktree** - Don't mix multiple plans in same worktree

---

## Related Skills

```
  Skill              Relationship
  ─────────────────  ─────────────────────────────────────────────
  planner            Triggers create after PRD approval
  qa           Triggers complete --yes after QA pass
  worktree-complete  Alternative invocation for completion
  ─────────────────  ─────────────────────────────────────────────
```
