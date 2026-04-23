---
title: Env Vars Validator
impact: CRITICAL
impactDescription: Validates required environment variables for wm workflow
tags: [validator, env-vars, configuration]
used_by: [validation-orchestrator]
registry: registries/env-vars.yaml
order: 10
blocking: true
---

# Env Vars Validator

**Impact: CRITICAL** - Validates required wm workflow environment variables

## Overview

This validator checks whether required environment variables are set, using `printenv`.
Only processes `kind: env-var` items from the registry.

Blocking: CLAUDE_PROJECT_DIR is CRITICAL — wm skill path resolution and all hook
scripts depend on it. A missing CLAUDE_PROJECT_DIR will cause silent failures in the
wm workflow.

## Input

```
registry_path: path to registries/env-vars.yaml
context: ValidationContext (projectRoot, mode, verbose)
```

## Output

```json
{
  "module": "env-vars",
  "items": [
    {
      "id": "ENV-001",
      "name": "CLAUDE_PROJECT_DIR",
      "status": "PASS|FAIL|WARN|SKIP",
      "detail": "CLAUDE_PROJECT_DIR=/Users/user/projects/myproject (directory exists)",
      "install_hint": "# Add to ~/.zshrc:\nexport CLAUDE_PROJECT_DIR=/Users/user/projects/myproject\n# Or configure in .claude/settings.local.json env block"
    }
  ],
  "counts": {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
}
```

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate environment variables from registry.

    Order: 10
    Blocking: True — CLAUDE_PROJECT_DIR is CRITICAL
    """
    import subprocess
    import os
    from pathlib import Path

    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []

    for item in registry["items"]:
        # Only process env-var kind items
        if item.get("kind") != "env-var":
            continue

        var_name = item["name"]

        # Step 1: printenv check — empty output means unset
        printenv_result = subprocess.run(
            ["printenv", var_name],
            capture_output=True, text=True
        )
        var_value = printenv_result.stdout.strip()

        if not var_value:
            status = "FAIL"
            detail = f"{var_name} is not set"
            install_hint = _get_install_hint(item, context)
            results.append(_make_item(item, status, detail, install_hint))
            continue

        # Step 2: CLAUDE_PROJECT_DIR — verify the value is an existing directory
        if var_name == "CLAUDE_PROJECT_DIR":
            if not Path(var_value).is_dir():
                status = "FAIL"
                detail = (
                    f"{var_name}={var_value} is set but the path does not exist "
                    "or is not a directory"
                )
                install_hint = _get_install_hint(item, context)
                results.append(_make_item(item, status, detail, install_hint))
                continue
            else:
                detail = f"{var_name}={var_value} (directory exists)"
        else:
            detail = f"{var_name} is set"

        results.append(_make_item(item, "PASS", detail, None))

    counts = _count_statuses(results)

    # Determine overall status
    critical_failed = any(
        r["status"] == "FAIL" and r.get("priority") == "CRITICAL"
        for r in results
    )

    if critical_failed:
        overall = "FAIL"
    elif counts["fail"] > 0:
        overall = "WARN"
    else:
        overall = "PASS"

    passed = counts["pass"]
    total = len(results)

    return {
        "moduleId": "env-vars",
        "moduleName": "Environment Variables",
        "status": overall,
        "passRate": (passed / total) * 100 if total else 0,
        "items": {
            "total": total,
            "passed": counts["pass"],
            "failed": counts["fail"],
            "warnings": counts["warn"]
        },
        "details": results,
        "blocking": True,
        "timestamp": datetime.now().isoformat(),
        "counts": counts
    }
```

## Helper Functions

```python
def _get_install_hint(item: dict, context: ValidationContext) -> str:
    """
    Generate install hint for an env var.
    CLAUDE_PROJECT_DIR: suggest current projectRoot as default value.
    CLAUDE_SKILL_DIR: suggest projectRoot + /.claude/skills.
    """
    var_name = item["name"]

    if var_name == "CLAUDE_PROJECT_DIR":
        suggested = context.projectRoot
        return (
            f"# Option 1 — Add to ~/.zshrc (persistent across all shells):\n"
            f"export {var_name}={suggested}\n\n"
            f"# Option 2 — Add to .claude/settings.local.json env block (Claude Code only):\n"
            f"# \"env\": {{ \"{var_name}\": \"{suggested}\" }}"
        )
    elif var_name == "CLAUDE_SKILL_DIR":
        suggested = context.projectRoot + "/.claude/skills"
        return (
            f"# Option 1 — Add to ~/.zshrc (persistent):\n"
            f"export {var_name}={suggested}\n\n"
            f"# Option 2 — .claude/settings.local.json env block:\n"
            f"# \"env\": {{ \"{var_name}\": \"{suggested}\" }}\n\n"
            f"# Note: CLAUDE_SKILL_DIR is optional when CLAUDE_PROJECT_DIR is set."
        )
    else:
        return item.get("install_command", f"# Set {var_name} in ~/.zshrc or .claude/settings.local.json")


def _make_item(item: dict, status: str, detail: str, install_hint) -> dict:
    return {
        "id": item["id"],
        "name": item["name"],
        "status": status,
        "detail": detail,
        "install_hint": install_hint or "",
        "priority": item.get("priority", "MEDIUM")
    }


def _count_statuses(results: list) -> dict:
    return {
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "warn": sum(1 for r in results if r["status"] == "WARN"),
        "skip": sum(1 for r in results if r["status"] == "SKIP")
    }
```

## Status Mapping

| Condition | Status | Notes |
|-----------|--------|-------|
| printenv returns empty | FAIL | Variable not set |
| CLAUDE_PROJECT_DIR path not a directory | FAIL | Value set but path invalid |
| Variable set and valid | PASS | |
| item.kind != env-var | skipped | Non-env-var items are not processed |

## Auto-Detect Capability

`CLAUDE_PROJECT_DIR` and `CLAUDE_SKILL_DIR` can be auto-detected:

- `CLAUDE_PROJECT_DIR`: defaults to `context.projectRoot` (current working directory)
- `CLAUDE_SKILL_DIR`: defaults to `context.projectRoot + "/.claude/skills"`

These defaults are surfaced in `install_hint` so the remediator can pre-fill them
when writing to `.claude/settings.local.json`.

## Output Format

```
┌──────────────────────────────────────────────────┐
│ [10/10] Environment Variables                     │
├──────────────────────┬─────────┬─────────────────┤
│ Variable             │ Status  │ Priority        │
├──────────────────────┼─────────┼─────────────────┤
│ CLAUDE_PROJECT_DIR   │ ✅ PASS │ CRITICAL        │
│ CLAUDE_SKILL_DIR     │ ❌ FAIL │ MEDIUM          │
├──────────────────────┴─────────┴─────────────────┤
│ Pass Rate: 50% (1/2)          Status: ⚠️ WARN    │
└──────────────────────────────────────────────────┘
```

## References

- Registry: [../registries/env-vars.yaml](../registries/env-vars.yaml)
- Remediation: [../remediators/env-vars-remediation.md](../remediators/env-vars-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
