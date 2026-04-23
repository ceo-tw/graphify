---
title: Hooks Config Validator
impact: HIGH
impactDescription: Validates hooks configuration in settings.json
tags: [validator, hooks, config]
used_by: [validation-orchestrator]
registry: registries/hooks.yaml
order: 4
blocking: false
---

# Hooks Config Validator

**Impact: HIGH** - Validates hooks configuration entries in settings.json

## Overview

This validator checks for hook configuration entries defined in `hooks.yaml` (configs section).
Verifies that settings.json contains the expected hook definitions.

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate hook configurations from registry.

    Order: 4 (after agents validation)
    """
    import yaml
    import json

    # Load registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    # Load settings.json
    settings = context.settings
    hooks_config = settings.get("hooks", {})

    results = []

    for config in registry.get("configs", []):
        event = config["event"]
        script_path = config["scriptPath"]

        # Check if hook is configured
        event_hooks = hooks_config.get(event, [])
        found = False

        for hook_entry in event_hooks:
            if isinstance(hook_entry, dict):
                # Check hooks array
                for h in hook_entry.get("hooks", []):
                    if script_path in h.get("command", ""):
                        found = True
                        break

        if found:
            status = "PASS"
            message = None
        else:
            if config["priority"] == "CRITICAL":
                status = "FAIL"
                message = f"Critical hook config missing: {config['name']}"
            elif config["priority"] == "HIGH":
                status = "WARN"
                message = f"Recommended hook config missing: {config['name']}"
            else:
                status = "SKIP"
                message = f"Optional hook config missing: {config['name']}"

        results.append({
            "id": config["id"],
            "name": config["name"],
            "event": event,
            "scriptPath": script_path,
            "status": status,
            "priority": config["priority"],
            "message": message,
            "remediation": "hooks-config-remediation" if status in ["FAIL", "WARN"] else None
        })

    # Calculate stats
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARN")

    # Determine overall status
    if failed > len(results) * 0.3:
        overall_status = "FAIL"
    elif failed > 0 or warnings > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    return {
        "moduleId": "hooks-config",
        "moduleName": "Hooks Configuration",
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

## Event Types

| Event | Description | Common Hooks |
|-------|-------------|--------------|
| PreToolUse | Before tool execution | sensitive-file-guard |
| PostToolUse | After tool execution | quality-check, plan-worktree-hook |
| UserPromptSubmit | When user submits prompt | decision-context |
| SubagentStop | When subagent completes | subagent-monitor |
| PreCompact | Before context compression | precompact-save-state |
| SessionStart | On session initialization | session-start-restore-hint |

## Output Format

```
┌─────────────────────────────────────────────┐
│ [4/6] Hooks Configuration                   │
├──────────────────────┬─────────┬────────────┤
│ Hook Config          │ Status  │ Event      │
├──────────────────────┼─────────┼────────────┤
│ sensitive-file-guard │ ✅ PASS │ PreToolUse │
│ plan-worktree-hook   │ ✅ PASS │ PostToolUse│
│ quality-check        │ ✅ PASS │ PostToolUse│
│ decision-context     │ ✅ PASS │ UserPrompt │
│ subagent-monitor     │ ✅ PASS │ SubagentStp│
│ precompact-save-state│ ✅ PASS │ PreCompact │
│ session-start-*      │ ✅ PASS │ SessionStrt│
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 100% (7/7)        Status: ✅ PASS│
└─────────────────────────────────────────────┘
```

## Config Structure Validation

```python
def validateConfigStructure(hooks_config: dict) -> list:
    """
    Validate hooks config structure in settings.json.

    Expected structure:
    {
        "EventName": [
            {
                "matcher": "pattern",
                "hooks": [
                    {"type": "command", "command": "..."}
                ]
            }
        ]
    }
    """
    issues = []

    valid_events = [
        "PreToolUse", "PostToolUse", "UserPromptSubmit",
        "SubagentStop", "PreCompact", "SessionStart", "Stop"
    ]

    for event, entries in hooks_config.items():
        if event not in valid_events:
            issues.append(f"Unknown event type: {event}")

        if not isinstance(entries, list):
            issues.append(f"Event {event} should have array value")

    return issues
```

## References

- Registry: [../registries/hooks.yaml](../registries/hooks.yaml)
- Remediation: [../remediators/hooks-config-remediation.md](../remediators/hooks-config-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
