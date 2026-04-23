---
title: Validator Interface
impact: HIGH
impactDescription: Common interface for all validators
tags: [interface, validation]
used_by: [wm-setup, validation-orchestrator]
---

# Validator Interface

**Impact: HIGH** - Common interface definition for all validators

## Overview

All validators MUST implement this interface to ensure consistent behavior
and enable orchestrated sequential execution.

## Interface Definition

```typescript
interface ValidationResult {
  moduleId: string;           // e.g., "skills", "agents", "hooks-config"
  moduleName: string;         // Human-readable name
  status: "PASS" | "WARN" | "FAIL";
  passRate: number;           // 0-100
  items: {
    total: number;
    passed: number;
    failed: number;
    warnings: number;
  };
  details: ValidationDetail[];
  blocking: boolean;          // If FAIL, should pipeline stop?
  timestamp: string;          // ISO timestamp
}

interface ValidationDetail {
  id: string;                 // Registry item ID
  name: string;               // Item name
  status: "PASS" | "WARN" | "FAIL" | "SKIP";
  message?: string;           // Error or warning message
  remediation?: string;       // Link to remediation
}
```

## Validator Signature

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate items from registry.

    Args:
        registry_path: Path to YAML registry file
        context: Shared validation context (settings, paths, etc.)

    Returns:
        ValidationResult with status and details
    """
```

## Validation Context

```typescript
interface ValidationContext {
  projectRoot: string;        // Project root path
  settingsPath: string;       // Path to settings.json
  settings: object;           // Parsed settings.json
  mode: "NEW_SETUP" | "UPDATE" | "VERIFY";
  verbose: boolean;           // Show detailed output
}
```

## Status Determination Rules

```python
def determineStatus(items: list) -> str:
    """
    Determine overall module status from item results.

    Rules:
    - FAIL: Any CRITICAL item failed OR > 50% items failed
    - WARN: Any HIGH item failed OR > 20% items failed
    - PASS: All items pass or only LOW priority failures
    """
    critical_failed = any(i.priority == "CRITICAL" and i.status == "FAIL" for i in items)
    high_failed = any(i.priority == "HIGH" and i.status == "FAIL" for i in items)

    fail_rate = sum(1 for i in items if i.status == "FAIL") / len(items)

    if critical_failed or fail_rate > 0.5:
        return "FAIL"
    elif high_failed or fail_rate > 0.2:
        return "WARN"
    else:
        return "PASS"
```

## Output Format

Each validator outputs results in this format:

```
┌─────────────────────────────────────────────┐
│ [2/6] Skills Validation                     │
├──────────────────────┬─────────┬────────────┤
│ Item                 │ Status  │ Priority   │
├──────────────────────┼─────────┼────────────┤
│ wm                   │ ✅ PASS │ CRITICAL   │
│ solve                │ ✅ PASS │ CRITICAL   │
│ research             │ ⚠️ WARN │ HIGH       │
│ e2e-test             │ ❌ FAIL │ HIGH       │
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 75% (3/4 core)  Status: ⚠️ WARN  │
└─────────────────────────────────────────────┘
```

## Validator Registry

| Validator | Registry | Blocking | Order |
|-----------|----------|----------|-------|
| folder-validator | folders.yaml | Yes | 1 |
| skills-validator | skills.yaml | No | 2 |
| agents-validator | agents.yaml | No | 3 |
| hooks-config-validator | hooks.yaml (configs) | No | 4 |
| hooks-scripts-validator | hooks.yaml (scripts) | No | 5 |
| settings-validator | settings.yaml | No | 6 |

## References

- [folder-validator.md](./folder-validator.md)
- [skills-validator.md](./skills-validator.md)
- [agents-validator.md](./agents-validator.md)
- [hooks-config-validator.md](./hooks-config-validator.md)
- [hooks-scripts-validator.md](./hooks-scripts-validator.md)
- [settings-validator.md](./settings-validator.md)
