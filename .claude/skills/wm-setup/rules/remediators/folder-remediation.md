---
title: Folder Remediation
impact: CRITICAL
impactDescription: Creates missing required directories
tags: [remediation, folders]
used_by: [validation-orchestrator]
validator: validators/folder-validator.md
order: 1
canAutoFix: true
---

# Folder Remediation

**Impact: CRITICAL** - Creates missing required directories

## Overview

This remediator handles missing folder issues from folder-validator.
Can auto-create directories safely.

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "auto"
) -> RemediationResult:
    """
    Create missing folders.

    Auto-safe: mkdir is always safe
    """
    from pathlib import Path

    actions_executed = []
    actions_required = []

    for item in validation_result["details"]:
        if item["status"] not in ["FAIL", "WARN"]:
            continue

        folder_path = Path(context.projectRoot) / item["path"]

        if mode == "auto" or mode == "interactive":
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                actions_executed.append({
                    "id": f"create-{item['id']}",
                    "type": "create",
                    "target": item["path"],
                    "description": f"Created directory: {item['path']}",
                    "status": "DONE"
                })
            except Exception as e:
                actions_executed.append({
                    "id": f"create-{item['id']}",
                    "type": "create",
                    "target": item["path"],
                    "description": f"Failed to create: {item['path']}",
                    "status": "FAILED",
                    "error": str(e)
                })
                actions_required.append({
                    "id": f"manual-{item['id']}",
                    "priority": "HIGH",
                    "description": f"Manually create directory: {item['path']}",
                    "command": f"mkdir -p {item['path']}"
                })
        else:  # report-only
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": item["priority"],
                "description": f"Create directory: {item['path']}",
                "command": f"mkdir -p {item['path']}"
            })

    return {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "status": _determineStatus(actions_executed, actions_required),
        "actionsExecuted": actions_executed,
        "actionsRequired": actions_required,
        "summary": {
            "totalActions": len(actions_executed) + len(actions_required),
            "automaticActions": len(actions_executed),
            "manualActions": len(actions_required)
        },
        "timestamp": datetime.now().isoformat()
    }
```

## Commands Reference

| Folder | Command |
|--------|---------|
| .claude | `mkdir -p .claude` |
| .claude/skills | `mkdir -p .claude/skills` |
| .claude/agents | `mkdir -p .claude/agents` |
| .claude/hooks | `mkdir -p .claude/hooks` |
| .claude/plans | `mkdir -p .claude/plans` |
| .claude/docs | `mkdir -p .claude/docs` |

## Batch Creation

```bash
# Create all required directories at once
mkdir -p .claude/{skills,agents,hooks,plans,docs,projects}
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Folder Structure            │
├──────────────────────┬──────────────────────┤
│ Action               │ Status               │
├──────────────────────┼──────────────────────┤
│ Create .claude       │ ✅ DONE              │
│ Create .claude/skills│ ✅ DONE              │
│ Create .claude/agents│ ✅ DONE              │
│ Create .claude/hooks │ ✅ DONE              │
├──────────────────────┴──────────────────────┤
│ Summary: 4/4 directories created            │
│ Status: ✅ SUCCESS                          │
└─────────────────────────────────────────────┘
```

## Post-Remediation Verification

```python
def verify(validation_result: ValidationResult, context: ValidationContext) -> bool:
    """
    Verify that remediation was successful.
    Re-run folder validation and check all items pass.
    """
    from pathlib import Path

    for item in validation_result["details"]:
        if item["status"] in ["FAIL", "WARN"]:
            folder_path = Path(context.projectRoot) / item["path"]
            if not folder_path.exists():
                return False
    return True
```

## References

- Validator: [../validators/folder-validator.md](../validators/folder-validator.md)
- Registry: [../registries/folders.yaml](../registries/folders.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
