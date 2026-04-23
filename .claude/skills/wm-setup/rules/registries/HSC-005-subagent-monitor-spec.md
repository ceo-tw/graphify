---
id: HSC-005
name: Subagent Monitor
script: subagent-monitor.sh
event: PostToolUse
impact: MEDIUM
blocking: false
dependencies:
  - hook-utils.sh
usedBy:
  - all-skills
  - all-agents
---

# Subagent Monitor Specification

## Purpose

Tracks and monitors subagent (Task tool) executions, providing visibility into
agent spawning patterns, execution times, and resource usage. Helps identify
runaway agents and optimize multi-agent workflows.

## Event Binding

| Field | Value |
|-------|-------|
| Event | PostToolUse |
| Matcher | Task |
| Timeout | 5000ms |

## Input Parameters

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| TOOL_NAME | string | env | Should be "Task" |
| TOOL_INPUT | json | env | Task parameters |
| TOOL_RESULT | json | env | Task execution result |
| subagent_type | string | TOOL_INPUT | Type of subagent |
| description | string | TOOL_INPUT | Task description |

## Monitored Metrics

```bash
METRICS=(
    "agent_type"      # Type of subagent spawned
    "execution_time"  # Time taken for task
    "status"          # Success/failure
    "parent_context"  # Calling context
    "token_usage"     # Approximate token usage
)
```

## Output Format

```
# Task completed
[SUBAGENT] Type: Explore
[SUBAGENT] Description: Find authentication files
[SUBAGENT] Duration: 12.5s
[SUBAGENT] Status: completed

# Task running in background
[SUBAGENT] Type: Bash (background)
[SUBAGENT] Task ID: task-abc123
[SUBAGENT] Status: running
```

## Log File Format

```jsonl
{"timestamp":"2024-01-15T10:30:00Z","type":"Explore","description":"Find auth files","duration_ms":12500,"status":"completed"}
{"timestamp":"2024-01-15T10:31:00Z","type":"Bash","description":"Run tests","duration_ms":null,"status":"running","task_id":"task-abc123"}
```

## Validation Checklist

- [x] Script exists at `.claude/hooks/subagent-monitor.sh`
- [x] Script is executable (chmod +x)
- [x] hook-utils.sh dependency present
- [x] Hook registered in settings.json PostToolUse
- [x] JSONL log format validated
- [x] Background task tracking works
- [x] Timeout appropriate (5s)

## Test Cases

### TC-001: Log completed Explore agent
- Input: Task tool with subagent_type="Explore", completed
- Expected: Log entry with duration and status
- Status: [x] PASS [ ] FAIL

### TC-002: Log background Bash agent
- Input: Task tool with run_in_background=true
- Expected: Log entry with task_id, status="running"
- Status: [x] PASS [ ] FAIL

### TC-003: Handle missing TOOL_RESULT
- Input: Task tool without result (error case)
- Expected: Log entry with status="error"
- Status: [x] PASS [ ] FAIL

## Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | Logged successfully | Continue |
| 1 | Logging error | Continue without log |
| 2 | N/A (non-blocking) | N/A |

## Dependencies

| Dependency | Type | Required |
|------------|------|----------|
| hook-utils.sh | Library | Yes |
| jq | Binary | Yes |

## Storage Location

```
.claude/
└── logs/
    └── subagent-monitor.jsonl
```

## Analysis Queries

```bash
# Count agents by type
jq -s 'group_by(.type) | map({type: .[0].type, count: length})' .claude/logs/subagent-monitor.jsonl

# Find slow agents (>30s)
jq 'select(.duration_ms > 30000)' .claude/logs/subagent-monitor.jsonl

# Running background tasks
jq 'select(.status == "running")' .claude/logs/subagent-monitor.jsonl
```

## References

- Registry: [hooks.yaml](hooks.yaml)
- Script: [../../hooks/subagent-monitor.sh](../../hooks/subagent-monitor.sh)
- Task Tool Documentation: [../../agents/README.md](../../agents/README.md)
