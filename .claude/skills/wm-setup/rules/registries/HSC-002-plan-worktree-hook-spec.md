---
id: HSC-002
name: Plan Worktree Hook
script: plan-worktree-hook.sh
event: PostToolUse
impact: HIGH
blocking: false
dependencies:
  - hook-utils.sh
usedBy:
  - planner skill
  - wm skill
---

# Plan Worktree Hook Specification

## Purpose

Automatically creates a git worktree when a new plan file is created. This isolates
feature development in separate worktrees, enabling parallel work streams and clean
rollback capabilities.

## Event Binding

| Field | Value |
|-------|-------|
| Event | PostToolUse |
| Matcher | Write |
| Timeout | 30000ms |

## Input Parameters

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| TOOL_NAME | string | env | Tool that was executed |
| TOOL_INPUT | json | env | Tool input parameters |
| file_path | string | TOOL_INPUT | File that was written |

## Trigger Conditions

```bash
# Only triggers when:
# 1. Tool is Write
# 2. file_path matches .claude/plans/*.md
# 3. file_path is a new file (not existing)

is_plan_file() {
    [[ "$file_path" == *".claude/plans/"*".md" ]]
}
```

## Output Format

```
# Worktree created
[WORKTREE] Created: feature/{plan-name}
[WORKTREE] Base: main
[WORKTREE] Path: ../worktrees/{plan-name}

# Skipped (existing file)
[WORKTREE] Skipped: Not a new plan file

# Error
[WORKTREE] Error: {error message}
```

## Validation Checklist

- [x] Script exists at `.claude/hooks/plan-worktree-hook.sh`
- [x] Script is executable (chmod +x)
- [x] hook-utils.sh dependency present
- [x] Hook registered in settings.json PostToolUse
- [x] Timeout appropriate for git operations (30s)
- [x] Git repository check implemented
- [x] Branch naming follows convention

## Test Cases

### TC-001: Create worktree for new plan
- Input: Write tool creates `.claude/plans/new-feature.md`
- Expected: Worktree created at `../worktrees/new-feature`
- Status: [x] PASS [ ] FAIL

### TC-002: Skip existing plan modification
- Input: Write tool modifies existing `.claude/plans/existing.md`
- Expected: No worktree created, "Skipped" message
- Status: [x] PASS [ ] FAIL

### TC-003: Handle non-git directory
- Input: Write tool in non-git directory
- Expected: Skip gracefully, no error
- Status: [x] PASS [ ] FAIL

## Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | Success or skipped | Continue |
| 1 | Git error | Log warning, continue |
| 2 | N/A (non-blocking) | N/A |

## Worktree Naming Convention

```
Plan file: .claude/plans/quirky-dancing-claude.md
Branch: feature/quirky-dancing-claude
Worktree: ../worktrees/quirky-dancing-claude
```

## Dependencies

| Dependency | Type | Required |
|------------|------|----------|
| hook-utils.sh | Library | Yes |
| git | Binary | Yes |

## Integration with wm Skill

This hook is typically triggered by the wm (workflow manager) skill during:
1. Plan creation (`/plan` command)
2. Feature kickoff
3. Automated planning workflows

## References

- Registry: [hooks.yaml](hooks.yaml)
- Script: [../../hooks/plan-worktree-hook.sh](../../hooks/plan-worktree-hook.sh)
- wm Skill: [../../wm/SKILL.md](../../wm/SKILL.md)
