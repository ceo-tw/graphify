---
id: HSC-003
name: Quality Check
script: quality-check.sh
event: PostToolUse
impact: HIGH
blocking: false
dependencies:
  - hook-utils.sh
  - eslint.cjs
  - prettier.cjs
  - typecheck.cjs
  - parallel-check.cjs
usedBy:
  - all-skills
  - all-agents
---

# Quality Check Specification

## Purpose

Runs automated code quality checks (ESLint, Prettier, TypeScript) after file
modifications. Provides immediate feedback on code quality issues without blocking
the workflow.

## Event Binding

| Field | Value |
|-------|-------|
| Event | PostToolUse |
| Matcher | Edit, Write, MultiEdit |
| Timeout | 60000ms |

## Input Parameters

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| TOOL_NAME | string | env | Tool that was executed |
| TOOL_INPUT | json | env | Tool input parameters |
| file_path | string | TOOL_INPUT | Modified file path |
| QUALITY_CHECK_PATHS | string | env | Comma-separated paths to check |

## Environment Configuration

```bash
# Required in .claude/settings.json
{
  "env": {
    "QUALITY_CHECK_PATHS": "dashboard/,collector/"
  }
}
```

## Output Format

```
# All checks pass
[QUALITY] ✅ ESLint: 0 errors, 0 warnings
[QUALITY] ✅ Prettier: formatted
[QUALITY] ✅ TypeScript: no errors

# With issues
[QUALITY] ⚠️ ESLint: 2 errors, 5 warnings
  src/index.ts:10 - no-unused-vars
  src/index.ts:25 - prefer-const
[QUALITY] ❌ TypeScript: 1 error
  src/types.ts:5 - Type 'string' is not assignable to type 'number'
```

## Validation Checklist

- [x] Script exists at `.claude/hooks/quality-check.sh`
- [x] Script is executable (chmod +x)
- [x] hook-utils.sh dependency present
- [x] eslint.cjs config file present
- [x] prettier.cjs config file present
- [x] typecheck.cjs config file present
- [x] QUALITY_CHECK_PATHS configured
- [x] Timeout appropriate for checks (60s)

## Test Cases

### TC-001: Check TypeScript file
- Input: Edit tool modifies `dashboard/src/index.ts`
- Expected: ESLint, Prettier, TypeScript checks run
- Status: [x] PASS [ ] FAIL

### TC-002: Skip non-TypeScript file
- Input: Edit tool modifies `README.md`
- Expected: Checks skipped, no output
- Status: [x] PASS [ ] FAIL

### TC-003: Handle missing QUALITY_CHECK_PATHS
- Input: QUALITY_CHECK_PATHS not set
- Expected: Checks skipped with warning
- Status: [x] PASS [ ] FAIL

### TC-004: Parallel check execution
- Input: Multiple files modified
- Expected: Checks run in parallel, all results reported
- Status: [x] PASS [ ] FAIL

## Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | All checks pass | Continue |
| 1 | Quality issues found | Log issues, continue |
| 2 | N/A (non-blocking) | N/A |

## Config File Dependencies

| File | Purpose | Required |
|------|---------|----------|
| eslint.cjs | ESLint configuration | Yes |
| prettier.cjs | Prettier configuration | Yes |
| typecheck.cjs | TypeScript check config | Yes |
| parallel-check.cjs | Parallel execution | Yes |

## Path Matching

```bash
# Check if file is in QUALITY_CHECK_PATHS
should_check_file() {
    local file="$1"
    IFS=',' read -ra PATHS <<< "$QUALITY_CHECK_PATHS"
    for path in "${PATHS[@]}"; do
        if [[ "$file" == "$path"* ]]; then
            return 0
        fi
    done
    return 1
}
```

## References

- Registry: [hooks.yaml](hooks.yaml)
- Script: [../../hooks/quality-check.sh](../../hooks/quality-check.sh)
- ESLint Config: [../../hooks/eslint.cjs](../../hooks/eslint.cjs)
- Prettier Config: [../../hooks/prettier.cjs](../../hooks/prettier.cjs)
