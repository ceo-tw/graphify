---
title: Remediation Interface
impact: HIGH
impactDescription: Common interface for all remediators
tags: [interface, remediation]
used_by: [wm-setup, validation-orchestrator]
---

# Remediation Interface

**Impact: HIGH** - Common interface definition for all remediators

## Overview

All remediators MUST implement this interface to ensure consistent behavior
and enable automated remediation actions.

## Interface Definition

```typescript
interface RemediationResult {
  moduleId: string;           // e.g., "skills", "agents"
  moduleName: string;         // Human-readable name
  status: "SUCCESS" | "PARTIAL" | "NEEDS_USER_ACTION" | "SKIPPED";
  actionsExecuted: RemediationAction[];
  actionsRequired: UserAction[];
  summary: {
    totalActions: number;
    automaticActions: number;
    manualActions: number;
  };
  timestamp: string;
}

interface RemediationAction {
  id: string;                 // Action ID
  type: "create" | "delete" | "modify" | "configure";
  target: string;             // Path or identifier
  description: string;        // What was done
  status: "DONE" | "FAILED";
  error?: string;             // Error message if failed
}

interface UserAction {
  id: string;                 // Action ID
  priority: "HIGH" | "MEDIUM" | "LOW";
  description: string;        // What user needs to do
  command?: string;           // Suggested command
  link?: string;              // Link to documentation
}
```

## Remediator Signature

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: RemediationMode
) -> RemediationResult:
    """
    Execute remediation for validation failures.

    Args:
        validation_result: Result from corresponding validator
        context: Shared validation context
        mode: "auto" | "interactive" | "report-only"

    Returns:
        RemediationResult with actions taken and user actions required
    """
```

## Remediation Modes

| Mode | Description | Behavior |
|------|-------------|----------|
| `auto` | Automatic remediation | Execute all safe actions without prompting |
| `interactive` | User-guided | Ask before each action |
| `report-only` | Generate report | List actions without executing |

## Status Determination

```python
def determineStatus(actions_executed: list, actions_required: list) -> str:
    """
    Determine remediation status.

    - SUCCESS: All actions executed successfully, no user actions required
    - PARTIAL: Some actions executed, some require user intervention
    - NEEDS_USER_ACTION: No automatic actions possible, user must act
    - SKIPPED: Remediation was skipped (e.g., user chose to skip)
    """
    if not actions_executed and not actions_required:
        return "SUCCESS"  # Nothing to remediate

    all_executed = all(a["status"] == "DONE" for a in actions_executed)
    no_user_actions = len(actions_required) == 0

    if all_executed and no_user_actions:
        return "SUCCESS"
    elif actions_executed and actions_required:
        return "PARTIAL"
    elif actions_required:
        return "NEEDS_USER_ACTION"
    else:
        return "SKIPPED"
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Skills                      │
├──────────────────────┬──────────────────────┤
│ Automatic Actions    │ Status               │
├──────────────────────┼──────────────────────┤
│ Create restore-ctx   │ ✅ DONE              │
│ Create skill-creator │ ✅ DONE              │
├──────────────────────┴──────────────────────┤
│ User Actions Required                       │
├─────────────────────────────────────────────┤
│ ⚠️ [HIGH] Install e2e-test skill           │
│    Run: cp -r template/e2e-test .claude/   │
│                                             │
│ ℹ️ [MEDIUM] Configure playwright MCP       │
│    See: docs/mcp-setup.md                   │
└─────────────────────────────────────────────┘
```

## Remediator Registry

| Remediator | Handles | Can Auto-Fix |
|------------|---------|--------------|
| folder-remediation | Missing folders | Yes (mkdir) |
| skills-remediation | Missing skills | Partial |
| agents-remediation | Missing agents | Partial |
| hooks-config-remediation | Missing hook configs | Report only |
| hooks-scripts-remediation | Missing/broken scripts | Partial |
| settings-remediation | Missing settings | Report only |

## Safety Checks

```python
def isSafeAction(action: dict) -> bool:
    """
    Check if action can be safely auto-executed.

    Safe actions:
    - Create empty directory
    - Create from template
    - Set permissions

    Unsafe actions (require user confirmation):
    - Delete files/folders
    - Modify existing files
    - Change system settings
    """
    safe_types = ["create", "configure"]
    unsafe_targets = ["settings.json", ".env", "credentials"]

    if action["type"] not in safe_types:
        return False

    if any(t in action["target"] for t in unsafe_targets):
        return False

    return True
```

## References

- [folder-remediation.md](./folder-remediation.md)
- [skills-remediation.md](./skills-remediation.md)
- [agents-remediation.md](./agents-remediation.md)
- [hooks-config-remediation.md](./hooks-config-remediation.md)
- [hooks-scripts-remediation.md](./hooks-scripts-remediation.md)
- [settings-remediation.md](./settings-remediation.md)
