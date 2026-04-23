---
title: Hooks Scripts Remediation
impact: HIGH
impactDescription: Creates or fixes missing hook scripts
tags: [remediation, hooks, scripts]
used_by: [validation-orchestrator]
validator: validators/hooks-scripts-validator.md
order: 5
canAutoFix: partial
---

# Hooks Scripts Remediation

**Impact: HIGH** - Creates or fixes missing hook scripts

## Overview

This remediator handles missing or broken hook script issues.
**Partial auto-fix**: Can create scripts from templates and fix permissions.

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "auto"
) -> RemediationResult:
    """
    Create missing scripts or fix permissions.

    Partial auto-fix:
    - Can copy from templates
    - Can fix permissions (chmod +x)
    """
    import shutil
    import os
    from pathlib import Path

    actions_executed = []
    actions_required = []

    template_base = Path(context.projectRoot) / ".claude/templates/hooks"

    for item in validation_result["details"]:
        if item["status"] not in ["FAIL", "WARN"]:
            continue

        script_path = Path(context.projectRoot) / item["path"]
        template_path = template_base / item["name"]

        # Case 1: Script exists but not executable
        if item.get("exists") and not item.get("executable"):
            if mode in ["auto", "interactive"]:
                try:
                    os.chmod(script_path, 0o755)
                    actions_executed.append({
                        "id": f"chmod-{item['id']}",
                        "type": "modify",
                        "target": item["path"],
                        "description": f"Made script executable: {item['name']}",
                        "status": "DONE"
                    })
                except Exception as e:
                    actions_required.append({
                        "id": f"chmod-{item['id']}",
                        "priority": "MEDIUM",
                        "description": f"Fix permissions: {item['name']}",
                        "command": f"chmod +x {item['path']}"
                    })

        # Case 2: Script missing
        elif not item.get("exists"):
            if template_path.exists() and mode in ["auto", "interactive"]:
                try:
                    script_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(template_path, script_path)
                    os.chmod(script_path, 0o755)
                    actions_executed.append({
                        "id": f"create-{item['id']}",
                        "type": "create",
                        "target": item["path"],
                        "description": f"Created script from template: {item['name']}",
                        "status": "DONE"
                    })
                except Exception as e:
                    actions_required.append({
                        "id": f"create-{item['id']}",
                        "priority": item["priority"],
                        "description": f"Create script: {item['name']}",
                        "command": f"# Create {item['path']} with proper content"
                    })
            else:
                actions_required.append({
                    "id": f"create-{item['id']}",
                    "priority": item["priority"],
                    "description": f"Create script: {item['name']}",
                    "command": getScriptTemplate(item["name"]),
                    "link": f"Template: {template_path}"
                })

    return {
        "moduleId": "hooks-scripts",
        "moduleName": "Hook Scripts",
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

## Script Templates

### hook-utils.sh (Shared Library)

```bash
#!/bin/bash
# Hook utilities - shared functions for all hooks

# Output formatting
output_json() {
    local key="$1"
    local value="$2"
    echo "{\"$key\": \"$value\"}"
}

# Check if running in worktree
is_worktree() {
    [ -f "$(git rev-parse --git-dir)/worktrees" ]
}

# Get project root
get_project_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}
```

### Basic Hook Template

```bash
#!/bin/bash
# Hook: {hook-name}
# Event: {event-type}
# Description: {description}

set -e

# Source utilities
source "$(dirname "$0")/hook-utils.sh"

# Main logic
main() {
    # Your hook logic here
    echo "Hook executed successfully"
}

main "$@"
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Hook Scripts                │
├──────────────────────┬──────────────────────┤
│ Automatic Actions    │ Status               │
├──────────────────────┼──────────────────────┤
│ chmod +x quality-chk │ ✅ DONE              │
│ Create hook-utils.sh │ ✅ DONE              │
├──────────────────────┴──────────────────────┤
│ User Actions Required                       │
├─────────────────────────────────────────────┤
│ ⚠️ [HIGH] Create script: decision-context  │
│    Template:                                │
│    ┌─────────────────────────────────────┐  │
│    │ #!/bin/bash                         │  │
│    │ # Hook: decision-context            │  │
│    │ source "$(dirname "$0")/hook-utils" │  │
│    │ # Add logic here                    │  │
│    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Permission Fix Commands

```bash
# Fix single script
chmod +x .claude/hooks/script-name.sh

# Fix all hook scripts
chmod +x .claude/hooks/*.sh

# Verify permissions
ls -la .claude/hooks/
```

## Script Validation

```python
def validateScript(script_path: Path) -> dict:
    """
    Basic validation of hook script.
    """
    issues = []

    if not script_path.exists():
        return {"valid": False, "issues": ["File does not exist"]}

    content = script_path.read_text()

    # Check shebang
    if not content.startswith("#!/bin/bash") and not content.startswith("#!/usr/bin/env bash"):
        issues.append("Missing or invalid shebang")

    # Check for common issues
    if "set -e" not in content:
        issues.append("Consider adding 'set -e' for error handling")

    return {
        "valid": len(issues) == 0,
        "issues": issues
    }
```

## References

- Validator: [../validators/hooks-scripts-validator.md](../validators/hooks-scripts-validator.md)
- Registry: [../registries/hooks.yaml](../registries/hooks.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
