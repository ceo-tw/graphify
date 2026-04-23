---
title: Hook Specification Template
impact: HIGH
impactDescription: Standard template for hook script specifications
tags: [template, hooks, specification]
used_by: [hooks-scripts-validator]
---

# Hook Specification Template

**Impact: HIGH** - Standardizes hook script documentation and validation

## Overview

This template defines the standard structure for hook script specifications (HSC-*).
All hook specifications MUST follow this format for consistency and validation.

## Template Structure

```yaml
# HSC-XXX-{script-name}-spec.md

---
id: HSC-XXX
name: {Human Readable Name}
script: {script-filename}.sh
event: PreToolUse | PostToolUse | PreCompact | Stop | Notification
impact: CRITICAL | HIGH | MEDIUM | LOW
blocking: true | false
dependencies:
  - hook-utils.sh
  - {other dependencies}
usedBy:
  - {skill or agent that uses this hook}
---

# {Hook Name} Specification

## Purpose
{One paragraph describing what this hook does and why it exists}

## Event Binding
| Field | Value |
|-------|-------|
| Event | {Event type} |
| Matcher | {Tool matcher pattern or empty} |
| Timeout | {Timeout in ms} |

## Input Parameters
| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| {param} | string | {env/arg} | {description} |

## Output Format
```
{Expected output format}
```

## Validation Checklist
- [ ] Script exists at `.claude/hooks/{script}.sh`
- [ ] Script is executable (chmod +x)
- [ ] Required dependencies are present
- [ ] Hook is registered in settings.json
- [ ] Timeout is appropriate for operation
- [ ] Error handling is implemented
- [ ] Exit codes are correct (0=success, 1=fail, 2=blocked)

## Test Cases
### TC-001: {Test case name}
- Input: {input description}
- Expected: {expected output}
- Status: [ ] PASS [ ] FAIL

### TC-002: {Test case name}
- Input: {input description}
- Expected: {expected output}
- Status: [ ] PASS [ ] FAIL

## Error Handling
| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | Success | Continue |
| 1 | Non-blocking error | Log and continue |
| 2 | Blocking error | Halt execution |

## Dependencies
| Dependency | Type | Required |
|------------|------|----------|
| hook-utils.sh | Library | Yes |
| {other} | {type} | {Yes/No} |

## References
- Registry: [../registries/hooks.yaml](../registries/hooks.yaml)
- Script: [../../hooks/{script}.sh](../../hooks/{script}.sh)
- Validator: [../validators/hooks-scripts-validator.md](../validators/hooks-scripts-validator.md)
```

## Validation Rules

### Required Sections

Every HSC specification MUST contain:

1. **YAML Frontmatter** - Metadata with id, name, script, event, impact
2. **Purpose** - Clear description of hook functionality
3. **Event Binding** - Table with event, matcher, timeout
4. **Input Parameters** - All parameters with types and sources
5. **Output Format** - Expected output structure
6. **Validation Checklist** - Testable requirements
7. **Test Cases** - At least 2 test cases
8. **Error Handling** - Exit codes and recovery

### Naming Convention

```
HSC-{NNN}-{script-name-kebab-case}-spec.md

Examples:
- HSC-001-sensitive-file-guard-spec.md
- HSC-002-plan-worktree-hook-spec.md
- HSC-003-quality-check-spec.md
```

### Checklist Completion Rate

Specifications are validated by checklist completion:

| Rate | Status | Action |
|------|--------|--------|
| 100% | PASS | Fully verified |
| 80-99% | WARN | Minor issues |
| <80% | FAIL | Major gaps |

## Parsing Logic

```python
def parseHookSpecification(spec_content: str) -> dict:
    """
    Parse hook specification markdown into structured data.

    Returns:
        {
            "id": "HSC-XXX",
            "name": str,
            "script": str,
            "event": str,
            "impact": str,
            "blocking": bool,
            "checklist": {
                "total": int,
                "completed": int,
                "rate": float
            },
            "testCases": [
                {"id": "TC-001", "name": str, "passed": bool}
            ],
            "valid": bool
        }
    """
    import re
    import yaml

    result = {
        "id": "",
        "name": "",
        "script": "",
        "event": "",
        "impact": "",
        "blocking": False,
        "checklist": {"total": 0, "completed": 0, "rate": 0.0},
        "testCases": [],
        "valid": False
    }

    # Parse YAML frontmatter
    frontmatter_match = re.search(r'^---\n(.*?)\n---', spec_content, re.DOTALL)
    if frontmatter_match:
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            result["id"] = frontmatter.get("id", "")
            result["name"] = frontmatter.get("name", "")
            result["script"] = frontmatter.get("script", "")
            result["event"] = frontmatter.get("event", "")
            result["impact"] = frontmatter.get("impact", "")
            result["blocking"] = frontmatter.get("blocking", False)
        except yaml.YAMLError:
            pass

    # Parse checklist items
    checklist_items = re.findall(r'- \[([ xX])\]', spec_content)
    result["checklist"]["total"] = len(checklist_items)
    result["checklist"]["completed"] = sum(1 for item in checklist_items if item.lower() == 'x')
    if result["checklist"]["total"] > 0:
        result["checklist"]["rate"] = (result["checklist"]["completed"] / result["checklist"]["total"]) * 100

    # Parse test cases
    tc_pattern = r'### (TC-\d+): (.+)\n.*?Status: \[([ xX])\]'
    for match in re.finditer(tc_pattern, spec_content, re.DOTALL):
        result["testCases"].append({
            "id": match.group(1),
            "name": match.group(2),
            "passed": match.group(3).lower() == 'x'
        })

    # Validate completeness
    result["valid"] = (
        result["id"] != "" and
        result["script"] != "" and
        result["checklist"]["rate"] >= 80
    )

    return result
```

## References

- Hooks Registry: [hooks.yaml](hooks.yaml)
- Validator: [../validators/hooks-scripts-validator.md](../validators/hooks-scripts-validator.md)
- Remediation: [../remediators/hooks-scripts-remediation.md](../remediators/hooks-scripts-remediation.md)
