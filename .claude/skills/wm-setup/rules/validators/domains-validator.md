---
title: Domains Validator
impact: HIGH
impactDescription: Validates project domain definitions and AGENTS.md files
tags: [validator, domains]
used_by: [validation-orchestrator]
registry: registries/domains.yaml
order: 7
blocking: false
---

# Domains Validator

**Impact: HIGH** - Validates project domain structure and AGENTS.md files

## Overview

This validator checks domain definitions from `domains.yaml` and verifies:
1. Domain directory exists
2. AGENTS.md file exists in domain directory
3. Guide file exists (if specified)

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate domains from registry.

    Order: 7 (after settings-validator)
    """
    import yaml
    from pathlib import Path

    # Load registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []

    for item in registry["items"]:
        # Check domain directory
        domain_path = Path(context.projectRoot) / item["directory"]
        dir_exists = domain_path.exists() and domain_path.is_dir()

        # Check AGENTS.md file
        agents_file_path = Path(context.projectRoot) / item["agentsFile"]
        agents_file_exists = agents_file_path.exists() and agents_file_path.is_file()

        # Check guide file (if specified)
        guide_file_exists = True
        guide_message = None
        if item.get("guideFile"):
            guide_file_path = Path(context.projectRoot) / item["guideFile"]
            guide_file_exists = guide_file_path.exists() and guide_file_path.is_file()
            if not guide_file_exists:
                guide_message = f"Guide file missing: {item['guideFile']}"

        # Determine status
        if not dir_exists:
            status = "FAIL"
            message = f"Domain directory missing: {item['directory']}"
        elif not agents_file_exists:
            status = "FAIL"
            message = f"AGENTS.md missing: {item['agentsFile']}"
        elif not guide_file_exists:
            status = "WARN"
            message = guide_message
        else:
            status = "PASS"
            message = None

        results.append({
            "id": item["id"],
            "name": item["name"],
            "directory": item["directory"],
            "status": status,
            "priority": item["priority"],
            "type": item["type"],
            "message": message,
            "remediation": "domains-remediation" if status == "FAIL" else None
        })

    # Calculate stats
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARN")

    # Determine overall status
    critical_failed = any(
        r["priority"] == "CRITICAL" and r["status"] == "FAIL"
        for r in results
    )
    fail_rate = failed / len(results) if results else 0

    if critical_failed or fail_rate > 0.5:
        overall_status = "FAIL"
    elif failed > 0 or fail_rate > 0.2:
        overall_status = "WARN"
    elif warnings > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    return {
        "moduleId": "domains",
        "moduleName": "Domain Definitions",
        "status": overall_status,
        "passRate": (passed / len(results)) * 100 if results else 0,
        "items": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings
        },
        "details": results,
        "blocking": False,
        "timestamp": datetime.now().isoformat()
    }
```

## Validation Checks

| Check | Severity | Description |
|-------|----------|-------------|
| Directory exists | FAIL | Domain directory must exist |
| AGENTS.md exists | FAIL | AGENTS.md file must exist in domain |
| Guide file exists | WARN | Guide file should exist if specified |
| Valid type | FAIL | Domain type must be valid enum value |

## Output Format

```
┌─────────────────────────────────────────────┐
│ [8/8] Domain Definitions                    │
├──────────────────────┬─────────┬────────────┤
│ Domain               │ Status  │ Priority   │
├──────────────────────┼─────────┼────────────┤
│ frontend             │ ✅ PASS │ HIGH       │
│ backend              │ ✅ PASS │ HIGH       │
│ database             │ ✅ PASS │ CRITICAL   │
│ client               │ ✅ PASS │ MEDIUM     │
│ deploy               │ ✅ PASS │ HIGH       │
│ tray-app             │ ✅ PASS │ MEDIUM     │
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 100%              Status: ✅ PASS│
└─────────────────────────────────────────────┘
```

## Error Example

```
┌─────────────────────────────────────────────┐
│ [8/8] Domain Definitions                    │
├──────────────────────┬─────────┬────────────┤
│ Domain               │ Status  │ Issue      │
├──────────────────────┼─────────┼────────────┤
│ frontend             │ ❌ FAIL │ AGENTS.md  │
│                      │         │ missing    │
├──────────────────────┼─────────┼────────────┤
│ backend              │ ⚠️ WARN │ Guide file │
│                      │         │ missing    │
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 66%               Status: ❌ FAIL│
└─────────────────────────────────────────────┘
```

## Usage in Validation Pipeline

```python
# After runtime-validator (order: 8)
domains_result = validate(
    registry_path=".claude/skills/wm-setup/rules/registries/domains.yaml",
    context=validation_context
)

if domains_result["status"] in ["FAIL", "WARN"]:
    # Trigger remediation
    remediation_result = remediate(domains_result, context, mode="auto")
```

## Integration with Orchestrator

The domains validator is executed as part of the validation pipeline:

```python
# validation-orchestrator.py
validators = [
    ("folder-validator", 1, True),      # Blocking
    ("skills-validator", 2, False),
    ("agents-validator", 3, False),
    ("hooks-config-validator", 4, False),
    ("hooks-scripts-validator", 5, False),
    ("settings-validator", 6, False),
    ("runtime-validator", 7, False),    # VERIFY mode only
    ("domains-validator", 8, False),    # New validator
]
```

## References

- Registry: [../registries/domains.yaml](../registries/domains.yaml)
- Schema: [../registries/domains-schema.md](../registries/domains-schema.md)
- Remediation: [../remediators/domains-remediation.md](../remediators/domains-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
