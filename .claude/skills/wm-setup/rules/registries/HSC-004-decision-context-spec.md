---
id: HSC-004
name: Decision Context
script: decision-context.sh
event: Notification
impact: MEDIUM
blocking: false
dependencies:
  - hook-utils.sh
usedBy:
  - wm skill
  - planner skill
---

# Decision Context Specification

## Purpose

Captures and logs important decision points during workflow execution. Records
context about why certain approaches were chosen, enabling future reference
and audit trails for architectural decisions.

## Event Binding

| Field | Value |
|-------|-------|
| Event | Notification |
| Matcher | (empty - all notifications) |
| Timeout | 5000ms |

## Input Parameters

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| NOTIFICATION_TYPE | string | env | Type of notification |
| NOTIFICATION_MESSAGE | string | env | Notification content |
| CLAUDE_PROJECT_DIR | string | env | Project root directory |

## Notification Types Captured

```bash
CAPTURED_TYPES=(
    "decision"
    "architecture"
    "tradeoff"
    "assumption"
    "risk"
)
```

## Output Format

```
# Decision captured
[DECISION] Captured: {decision_type}
[DECISION] Context: {brief context}
[DECISION] Logged to: .claude/decisions/{date}-{id}.md

# Skipped (non-decision notification)
[DECISION] Skipped: Not a decision notification
```

## Log File Format

```markdown
# Decision: {title}

**Date**: {ISO timestamp}
**Type**: {decision_type}
**Context**: {workflow context}

## Decision

{decision content}

## Rationale

{extracted rationale if present}

## Alternatives Considered

{extracted alternatives if present}
```

## Validation Checklist

- [x] Script exists at `.claude/hooks/decision-context.sh`
- [x] Script is executable (chmod +x)
- [x] hook-utils.sh dependency present
- [x] Hook registered in settings.json Notification
- [x] .claude/decisions/ directory created on first use
- [x] Decision log format validated
- [x] Timeout appropriate (5s)

## Test Cases

### TC-001: Capture architecture decision
- Input: Notification with type="architecture"
- Expected: Decision logged to .claude/decisions/
- Status: [x] PASS [ ] FAIL

### TC-002: Skip non-decision notification
- Input: Notification with type="info"
- Expected: Skipped, no log created
- Status: [x] PASS [ ] FAIL

### TC-003: Handle missing project directory
- Input: CLAUDE_PROJECT_DIR not set
- Expected: Graceful skip with warning
- Status: [x] PASS [ ] FAIL

## Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | Success or skipped | Continue |
| 1 | Write error | Log warning, continue |
| 2 | N/A (non-blocking) | N/A |

## Dependencies

| Dependency | Type | Required |
|------------|------|----------|
| hook-utils.sh | Library | Yes |

## Integration Points

- Works with wm skill for architectural decisions
- Complements the planner skill decision tracking
- Decisions can be reviewed via `/decisions` command

## Storage Location

```
.claude/
└── decisions/
    ├── 2024-01-15-001.md
    ├── 2024-01-15-002.md
    └── 2024-01-16-001.md
```

## References

- Registry: [hooks.yaml](hooks.yaml)
- Script: [../../hooks/decision-context.sh](../../hooks/decision-context.sh)
- wm Skill: [../../wm/SKILL.md](../../wm/SKILL.md)
