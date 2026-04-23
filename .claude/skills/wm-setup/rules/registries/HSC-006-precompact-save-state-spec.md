---
id: HSC-006
name: Precompact Save State
script: precompact-save-state.sh
event: PreCompact
impact: HIGH
blocking: false
dependencies:
  - hook-utils.sh
usedBy:
  - all-skills
  - wm skill
---

# Precompact Save State Specification

## Purpose

Saves conversation state before context compaction occurs. This enables recovery
of important context that might be lost during compaction, including task progress,
decision history, and working state.

## Event Binding

| Field | Value |
|-------|-------|
| Event | PreCompact |
| Matcher | (empty - all compactions) |
| Timeout | 10000ms |

## Input Parameters

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| CLAUDE_PROJECT_DIR | string | env | Project root directory |
| CONVERSATION_ID | string | env | Current conversation ID |
| TOKEN_COUNT | string | env | Current token usage |

## Saved State Components

```bash
STATE_COMPONENTS=(
    "task_list"       # Current TaskList state
    "active_plan"     # Active plan file path
    "working_files"   # Recently modified files
    "decisions"       # Recent decisions made
    "checkpoint"      # Execution checkpoint
)
```

## Output Format

```
# State saved
[PRECOMPACT] Saving state for conversation: {conversation_id}
[PRECOMPACT] Token count: {token_count}
[PRECOMPACT] Saved to: .claude/checkpoints/{timestamp}.json

# Nothing to save
[PRECOMPACT] No significant state to save
```

## State File Format

```json
{
  "conversationId": "abc-123",
  "timestamp": "2024-01-15T10:30:00Z",
  "tokenCount": 180000,
  "tasks": [
    {"id": "1", "subject": "...", "status": "in_progress"},
    {"id": "2", "subject": "...", "status": "pending"}
  ],
  "activePlan": ".claude/plans/current-feature.md",
  "workingFiles": [
    "src/index.ts",
    "src/components/Auth.tsx"
  ],
  "recentDecisions": [
    "Using JWT for authentication",
    "PostgreSQL over MySQL"
  ],
  "checkpoint": {
    "phase": "implementation",
    "step": 3,
    "description": "Implementing login component"
  }
}
```

## Validation Checklist

- [x] Script exists at `.claude/hooks/precompact-save-state.sh`
- [x] Script is executable (chmod +x)
- [x] hook-utils.sh dependency present
- [x] Hook registered in settings.json PreCompact
- [x] .claude/checkpoints/ directory created
- [x] JSON state format validated
- [x] Timeout appropriate (10s)

## Test Cases

### TC-001: Save state with active tasks
- Input: PreCompact event with tasks in TaskList
- Expected: State file created with task list
- Status: [x] PASS [ ] FAIL

### TC-002: Save state with active plan
- Input: PreCompact event with plan file active
- Expected: State file includes plan path
- Status: [x] PASS [ ] FAIL

### TC-003: Handle empty state
- Input: PreCompact event with no tasks/plans
- Expected: Minimal state file or skip
- Status: [x] PASS [ ] FAIL

## Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | State saved | Continue compaction |
| 1 | Save error | Log warning, continue |
| 2 | N/A (non-blocking) | N/A |

## Dependencies

| Dependency | Type | Required |
|------------|------|----------|
| hook-utils.sh | Library | Yes |
| jq | Binary | Yes |

## Storage Location

```
.claude/
└── checkpoints/
    ├── 2024-01-15T10-30-00.json
    ├── 2024-01-15T14-45-00.json
    └── latest.json (symlink)
```

## Restoration

State can be restored using the `/restore-context` command which:
1. Reads latest checkpoint
2. Recreates TaskList entries
3. Restores working context
4. Provides summary of restored state

## References

- Registry: [hooks.yaml](hooks.yaml)
- Script: [../../hooks/precompact-save-state.sh](../../hooks/precompact-save-state.sh)
- Restore Command: [../../skills/wm/rules/commands/restore-context.md](../../skills/wm/rules/commands/restore-context.md)
