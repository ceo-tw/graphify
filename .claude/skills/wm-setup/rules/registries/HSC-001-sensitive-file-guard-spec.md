---
id: HSC-001
name: Sensitive File Guard
script: sensitive-file-guard.sh
event: PreToolUse
impact: CRITICAL
blocking: true
dependencies:
  - hook-utils.sh
usedBy:
  - all-skills
  - all-agents
---

# Sensitive File Guard Specification

## Purpose

Prevents accidental modification of sensitive files (credentials, environment files,
security configurations) by blocking Edit/Write tool calls that target protected paths.
This is a CRITICAL security hook that should never be disabled.

## Event Binding

| Field | Value |
|-------|-------|
| Event | PreToolUse |
| Matcher | Edit, Write, MultiEdit |
| Timeout | 1000ms |

## Input Parameters

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| TOOL_NAME | string | env | Name of tool being called |
| TOOL_INPUT | json | env | Tool input parameters |
| file_path | string | TOOL_INPUT | Target file path |

## Protected Patterns

```bash
PROTECTED_PATTERNS=(
    "*.env"
    "*.env.*"
    ".env"
    ".env.*"
    "*credentials*"
    "*secret*"
    "*.pem"
    "*.key"
    "*password*"
    ".aws/*"
    ".ssh/*"
    "*.p12"
    "*.pfx"
)
```

## Output Format

```
# Success (allowed)
ALLOWED: {file_path}

# Blocked
BLOCKED: Sensitive file detected: {file_path}
Pattern matched: {pattern}
```

## Validation Checklist

- [x] Script exists at `.claude/hooks/sensitive-file-guard.sh`
- [x] Script is executable (chmod +x)
- [x] hook-utils.sh dependency present
- [x] Hook registered in settings.json PreToolUse
- [x] Timeout set to 1000ms (fast check required)
- [x] Exit code 2 used for blocking
- [x] All protected patterns tested

## Test Cases

### TC-001: Block .env modification
- Input: Write tool with file_path=".env"
- Expected: Exit code 2, "BLOCKED" message
- Status: [x] PASS [ ] FAIL

### TC-002: Allow normal file modification
- Input: Write tool with file_path="src/index.ts"
- Expected: Exit code 0, "ALLOWED" message
- Status: [x] PASS [ ] FAIL

### TC-003: Block credentials file
- Input: Edit tool with file_path="config/credentials.json"
- Expected: Exit code 2, "BLOCKED" message
- Status: [x] PASS [ ] FAIL

### TC-004: Block nested env file
- Input: Write tool with file_path="deploy/.env.production"
- Expected: Exit code 2, "BLOCKED" message
- Status: [x] PASS [ ] FAIL

## Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | File allowed | Continue tool execution |
| 1 | Script error | Log warning, allow (fail-open) |
| 2 | File blocked | Halt tool execution |

## Dependencies

| Dependency | Type | Required |
|------------|------|----------|
| hook-utils.sh | Library | Yes |
| jq | Binary | Yes (for JSON parsing) |

## Security Considerations

- This hook uses fail-open on script errors (exit 1)
- Pattern matching is case-insensitive
- Paths are normalized before matching
- No bypass mechanism should exist

## References

- Registry: [hooks.yaml](hooks.yaml)
- Script: [../../hooks/sensitive-file-guard.sh](../../hooks/sensitive-file-guard.sh)
- Validator: [../validators/hooks-scripts-validator.md](../validators/hooks-scripts-validator.md)
