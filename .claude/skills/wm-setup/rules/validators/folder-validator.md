---
title: Folder Validator
impact: CRITICAL
impactDescription: Validates required directory structure (blocking)
tags: [validator, folders]
used_by: [validation-orchestrator]
registry: registries/folders.yaml
order: 1
blocking: true
---

# Folder Validator

**Impact: CRITICAL** - Validates required directory structure; blocks pipeline on failure

## Overview

This validator checks for required directories defined in `folders.yaml`.
**BLOCKING**: If any CRITICAL folder is missing, the validation pipeline stops.

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate folder structure from registry.

    Order: 1 (first validator - blocking)
    """
    import yaml
    from pathlib import Path

    # Load registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []
    blocking_failed = False

    for item in registry["items"]:
        folder_path = Path(context.projectRoot) / item["path"]
        exists = folder_path.exists() and folder_path.is_dir()

        if exists:
            status = "PASS"
            message = None
        else:
            if item["blocking"]:
                status = "FAIL"
                blocking_failed = True
                message = f"CRITICAL: Required folder missing: {item['path']}"
            elif item["priority"] == "CRITICAL":
                status = "FAIL"
                message = f"Critical folder missing: {item['path']}"
            elif item["priority"] == "HIGH":
                status = "WARN"
                message = f"Recommended folder missing: {item['path']}"
            else:
                status = "SKIP"
                message = f"Optional folder missing: {item['path']}"

        results.append({
            "id": item["id"],
            "name": item["name"],
            "path": item["path"],
            "status": status,
            "priority": item["priority"],
            "blocking": item.get("blocking", False),
            "message": message,
            "remediation": "folder-remediation" if status == "FAIL" else None
        })

    # Calculate stats
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARN")

    # Determine overall status
    if blocking_failed:
        overall_status = "FAIL"
    elif failed > 0:
        overall_status = "FAIL"
    elif warnings > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    return {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "status": overall_status,
        "passRate": (passed / len(results)) * 100 if results else 0,
        "items": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings
        },
        "details": results,
        "blocking": blocking_failed,  # Stop pipeline if blocking folder missing
        "timestamp": datetime.now().isoformat()
    }
```

## Blocking Logic

```python
def shouldStopPipeline(result: ValidationResult) -> bool:
    """
    Check if pipeline should stop.

    Returns True if:
    - Any item with blocking=true has status=FAIL
    - .claude directory is missing (FLD-001)
    """
    return result["blocking"] or any(
        d["id"] == "FLD-001" and d["status"] == "FAIL"
        for d in result["details"]
    )
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ [1/6] Folder Structure                      │
├──────────────────────┬─────────┬────────────┤
│ Folder               │ Status  │ Blocking   │
├──────────────────────┼─────────┼────────────┤
│ .claude              │ ✅ PASS │ Yes        │
│ .claude/skills       │ ✅ PASS │ Yes        │
│ .claude/agents       │ ✅ PASS │ Yes        │
│ .claude/hooks        │ ✅ PASS │ Yes        │
│ .claude/plans        │ ✅ PASS │ No         │
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 100%              Status: ✅ PASS│
└─────────────────────────────────────────────┘
```

## Error Handling

If blocking folder is missing:

```
┌─────────────────────────────────────────────┐
│ ❌ BLOCKING ERROR: Required folder missing  │
├─────────────────────────────────────────────┤
│ Missing: .claude                            │
│                                             │
│ This is the root Claude Code directory.    │
│ Pipeline cannot continue without it.        │
│                                             │
│ Run: mkdir -p .claude                       │
│                                             │
│ See: folder-remediation.md                  │
└─────────────────────────────────────────────┘
```

## References

- Registry: [../registries/folders.yaml](../registries/folders.yaml)
- Remediation: [../remediators/folder-remediation.md](../remediators/folder-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
