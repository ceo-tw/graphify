---
title: Skills Validator
impact: HIGH
impactDescription: Validates core skills installation
tags: [validator, skills]
used_by: [validation-orchestrator]
registry: registries/skills.yaml
order: 2
blocking: false
---

# Skills Validator

**Impact: HIGH** - Validates core skills installation against registry

## Overview

This validator checks for installed skills defined in `skills.yaml`.
Non-blocking: Missing skills are reported but pipeline continues.

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate skills from registry.

    Order: 2 (after folder validation)
    """
    import yaml
    from pathlib import Path

    # Load registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []

    for item in registry["items"]:
        skill_path = Path(context.projectRoot) / item["path"]
        validation_type = item.get("validation", {}).get("type", "exists")

        # Support both file existence and directory existence
        if validation_type == "dir_exists":
            exists = skill_path.exists() and skill_path.is_dir()
        else:
            exists = skill_path.exists() and skill_path.is_file()

        if exists:
            status = "PASS"
            message = None
        else:
            if item["priority"] == "CRITICAL":
                status = "FAIL"
                message = f"Critical skill missing: {item['name']}"
            elif item["priority"] == "HIGH":
                status = "WARN"
                message = f"Recommended skill missing: {item['name']}"
            else:
                status = "SKIP"
                message = f"Optional skill missing: {item['name']}"

        results.append({
            "id": item["id"],
            "name": item["name"],
            "path": item["path"],
            "status": status,
            "priority": item["priority"],
            "tags": item.get("tags", []),
            "message": message,
            "remediation": "skills-remediation" if status in ["FAIL", "WARN"] else None
        })

    # Calculate stats
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARN")

    # Determine overall status
    critical_failed = any(
        r["status"] == "FAIL" and r["priority"] == "CRITICAL"
        for r in results
    )

    if critical_failed:
        overall_status = "FAIL"
    elif failed > 0 or warnings > len(results) * 0.2:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    return {
        "moduleId": "skills",
        "moduleName": "Skills",
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

## Validation Types

| Type | Description | Use Case |
|------|-------------|----------|
| `exists` | File must exist | Skills with SKILL.md |
| `dir_exists` | Directory must exist | Rules-only skills (no SKILL.md) |

## Priority-Based Status

| Priority | Missing Status | Effect |
|----------|---------------|--------|
| CRITICAL | FAIL | Overall status = FAIL |
| HIGH | WARN | Overall status = WARN |
| MEDIUM | SKIP | No effect on overall |
| LOW | SKIP | No effect on overall (rules-only) |

## Output Format

```
┌─────────────────────────────────────────────┐
│ [2/6] Skills                                │
├──────────────────────┬─────────┬────────────┤
│ Skill                │ Status  │ Priority   │
├──────────────────────┼─────────┼────────────┤
│ wm                   │ ✅ PASS │ CRITICAL   │
│ solve                │ ✅ PASS │ CRITICAL   │
│ research             │ ✅ PASS │ HIGH       │
│ codebase-explorer    │ ✅ PASS │ HIGH       │
│ code-quality         │ ⚠️ WARN │ HIGH       │
│ e2e-test             │ ✅ PASS │ HIGH       │
│ worktree-manager     │ ✅ PASS │ MEDIUM     │
│ restore-context      │ ✅ PASS │ MEDIUM     │
│ skill-creator        │ ⏭️ SKIP │ MEDIUM     │
│ dev-status           │ ✅ PASS │ MEDIUM     │
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 80% (8/10)        Status: ⚠️ WARN│
└─────────────────────────────────────────────┘
```

## Missing Skills Report

```python
def getMissingSkillsReport(result: ValidationResult) -> str:
    """Generate detailed report of missing skills."""
    missing = [d for d in result["details"] if d["status"] in ["FAIL", "WARN"]]

    if not missing:
        return "All skills installed"

    report = "Missing Skills:\n"
    for item in missing:
        report += f"  - {item['name']} ({item['priority']})\n"
        report += f"    Path: {item['path']}\n"

    return report
```

## References

- Registry: [../registries/skills.yaml](../registries/skills.yaml)
- Remediation: [../remediators/skills-remediation.md](../remediators/skills-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
