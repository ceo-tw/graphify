---
title: Env Vars Remediation
impact: CRITICAL
impactDescription: Configures missing wm workflow environment variables
tags: [remediation, env-vars, configuration]
used_by: [validation-orchestrator]
validator: validators/env-vars-validator.md
order: 10
canAutoFix: partial
---

# Env Vars Remediation

**Impact: CRITICAL** - Configures missing environment variables for wm workflow

## Overview

Environment variables cannot be set in the current shell session from a subprocess —
they would vanish when the subprocess exits. This remediator therefore writes missing
variables to `.claude/settings.local.json` under the `env:` block, which Claude Code
reads on startup and injects into all hook and skill executions.

Shell rc file modification (`.zshrc`/`.bashrc`) is NOT performed automatically because:
1. It modifies the user's persistent shell environment without explicit consent
2. Changes only take effect in new shell sessions, not the current one
3. Different users may use different shells (zsh, bash, fish)

Instead: rc file instructions are provided as manual action hints.

3 modes:
- NEW_SETUP: writes to settings.local.json after user confirmation per variable
- UPDATE: asks per variable via AskUserQuestion
- VERIFY: reports only, no writes

## Input

```
validation_result: output from env-vars-validator
context: ValidationContext
mode: "NEW_SETUP" | "UPDATE" | "VERIFY"
```

## Output

```json
{
  "module": "env-vars",
  "mode": "NEW_SETUP|UPDATE|VERIFY",
  "status": "SUCCESS|PARTIAL|FAILURE",
  "actionsExecuted": [
    {
      "id": "configure-ENV-001",
      "type": "configure",
      "target": ".claude/settings.local.json",
      "description": "Added CLAUDE_PROJECT_DIR to .claude/settings.local.json env block",
      "status": "DONE"
    }
  ],
  "actionsRequired": [
    {
      "id": "shell-ENV-001",
      "priority": "MEDIUM",
      "description": "Add CLAUDE_PROJECT_DIR to ~/.zshrc for persistence across all shells",
      "command": "echo 'export CLAUDE_PROJECT_DIR=/path/to/project' >> ~/.zshrc",
      "detail": "Settings.local.json covers Claude Code sessions only"
    }
  ],
  "summary": {"automaticActions": 1, "manualActions": 1, "skipped": 0}
}
```

## Auto-Detect Default Values

```python
def _get_default_value(var_name: str, context: ValidationContext) -> str:
    """
    Auto-detect sensible defaults for known env vars.

    CLAUDE_PROJECT_DIR: current projectRoot (confirmed existing directory)
    CLAUDE_SKILL_DIR: projectRoot + /.claude/skills
    """
    import os

    if var_name == "CLAUDE_PROJECT_DIR":
        return context.projectRoot
    elif var_name == "CLAUDE_SKILL_DIR":
        return os.path.join(context.projectRoot, ".claude", "skills")
    else:
        return ""
```

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "NEW_SETUP"
) -> RemediationResult:
    """
    Configure missing environment variables.

    Writes to .claude/settings.local.json env block.
    Shell rc modification is always manual — provided as hint.

    NEW_SETUP: confirm once, then write all vars
    UPDATE: ask per variable
    VERIFY: report only
    """
    import json
    import os
    from pathlib import Path

    failed_items = [
        d for d in validation_result["details"]
        if d["status"] == "FAIL"
    ]

    actions_executed = []
    actions_required = []
    skipped_count = 0

    if not failed_items:
        return _build_result(mode, actions_executed, actions_required, skipped_count)

    if mode == "VERIFY":
        for item in failed_items:
            default_val = _get_default_value(item["name"], context)
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item.get("priority") == "CRITICAL" else "MEDIUM",
                "description": f"Configure {item['name']} (suggested: {default_val or 'see registry'})",
                "command": _get_zshrc_hint(item["name"], default_val),
                "detail": (
                    f"Option 1: Add to ~/.zshrc\n"
                    f"Option 2: Add to .claude/settings.local.json env block"
                )
            })
        return _build_result(mode, actions_executed, actions_required, skipped_count)

    settings_local_path = Path(context.projectRoot) / ".claude" / "settings.local.json"

    # Load existing settings.local.json (or start fresh)
    existing_settings = {}
    if settings_local_path.exists():
        try:
            with open(settings_local_path) as f:
                existing_settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_settings = {}

    env_block = existing_settings.get("env", {})

    for item in failed_items:
        var_name = item["name"]
        default_val = _get_default_value(var_name, context)

        if mode == "NEW_SETUP":
            # In NEW_SETUP, confirm once before writing
            user_approved = AskUserQuestion(
                question=(
                    f"Configure {var_name} in .claude/settings.local.json?\n"
                    f"Suggested value: {default_val or '(enter manually)'}\n"
                    f"This is required for wm skill path resolution."
                ),
                options=["yes (use suggested)", "no (skip)", "enter manually"]
            )
            if user_approved == "no (skip)":
                skipped_count += 1
                continue
            elif user_approved == "enter manually":
                # Cannot prompt for free text in AskUserQuestion — add manual action
                actions_required.append({
                    "id": f"manual-{item['id']}",
                    "priority": "HIGH" if item.get("priority") == "CRITICAL" else "MEDIUM",
                    "description": f"Manually configure {var_name} in .claude/settings.local.json",
                    "command": _get_settings_json_hint(var_name, default_val),
                    "detail": "Add to the \"env\" block in .claude/settings.local.json"
                })
                skipped_count += 1
                continue
            value_to_write = default_val
        elif mode == "UPDATE":
            user_approved = AskUserQuestion(
                question=(
                    f"Add {var_name} to .claude/settings.local.json?\n"
                    f"Suggested value: {default_val or '(none — will need manual entry)'}"
                ),
                options=["yes", "no"]
            )
            if user_approved != "yes":
                skipped_count += 1
                continue
            value_to_write = default_val

        if not value_to_write:
            # No auto-detect value available → manual only
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item.get("priority") == "CRITICAL" else "MEDIUM",
                "description": f"No default value detected for {var_name}. Set manually.",
                "command": _get_settings_json_hint(var_name, f"<your-value>"),
                "detail": ""
            })
            continue

        # Write to env block
        env_block[var_name] = value_to_write
        existing_settings["env"] = env_block

        try:
            settings_local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_local_path, "w") as f:
                json.dump(existing_settings, f, indent=2)
            f.write("\n")  # trailing newline

            actions_executed.append({
                "id": f"configure-{item['id']}",
                "type": "configure",
                "target": str(settings_local_path.relative_to(context.projectRoot)),
                "description": f"Added {var_name}={value_to_write} to .claude/settings.local.json env block",
                "status": "DONE"
            })

            # Also provide shell rc hint as informational manual action
            actions_required.append({
                "id": f"shell-{item['id']}",
                "priority": "LOW",
                "description": (
                    f"For persistence across all shells (not just Claude Code), "
                    f"also add {var_name} to ~/.zshrc"
                ),
                "command": _get_zshrc_hint(var_name, value_to_write),
                "detail": "settings.local.json covers Claude Code sessions only"
            })

        except IOError as e:
            actions_executed.append({
                "id": f"configure-{item['id']}",
                "type": "configure",
                "target": str(settings_local_path),
                "description": f"Failed to write {var_name} to settings.local.json",
                "status": "FAILED",
                "error": str(e)
            })
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH",
                "description": f"Manual configuration required: {var_name}",
                "command": _get_settings_json_hint(var_name, value_to_write),
                "detail": str(e)
            })

    return _build_result(mode, actions_executed, actions_required, skipped_count)
```

## Helper Functions

```python
def _get_zshrc_hint(var_name: str, value: str) -> str:
    return f"echo 'export {var_name}={value}' >> ~/.zshrc && source ~/.zshrc"


def _get_settings_json_hint(var_name: str, value: str) -> str:
    return (
        f"# In .claude/settings.local.json, add/update:\n"
        f"# {{\n"
        f"#   \"env\": {{\n"
        f"#     \"{var_name}\": \"{value}\"\n"
        f"#   }}\n"
        f"# }}"
    )


def _build_result(mode: str, actions_executed: list, actions_required: list, skipped: int) -> dict:
    done = sum(1 for a in actions_executed if a.get("status") == "DONE")
    failed_exec = sum(1 for a in actions_executed if a.get("status") == "FAILED")
    # Filter out LOW-priority shell hints from "manual action" count for status
    non_low_required = [a for a in actions_required if a.get("priority") != "LOW"]

    if failed_exec == 0 and len(non_low_required) == 0:
        status = "SUCCESS"
    elif done > 0 and (failed_exec > 0 or len(non_low_required) > 0):
        status = "PARTIAL"
    else:
        status = "FAILURE"

    return {
        "module": "env-vars",
        "mode": mode,
        "status": status,
        "actionsExecuted": actions_executed,
        "actionsRequired": actions_required,
        "summary": {
            "automaticActions": done,
            "manualActions": len([a for a in actions_required if a.get("priority") != "LOW"]),
            "skipped": skipped
        }
    }
```

## Why settings.local.json Instead of Shell RC

| Approach | Pros | Cons |
|----------|------|------|
| `.claude/settings.local.json` env block | Takes effect immediately in Claude Code; project-scoped | Only applies to Claude Code sessions |
| `~/.zshrc` / `~/.bashrc` | Persistent across all tools | Requires new shell session; modifies global config |

This remediator uses `settings.local.json` for the automatic action because:
1. It takes effect in the current Claude Code session without requiring a shell restart
2. It is project-scoped and does not pollute the global shell environment
3. It is safe to write automatically with user confirmation

The shell rc approach is always provided as a supplementary LOW-priority manual action.

## Mode Behavior Summary

| Mode | auto-configure | ask per var | report only |
|------|---------------|-------------|-------------|
| NEW_SETUP | yes (with confirmation) | yes (AskUserQuestion) | no |
| UPDATE | no | yes (AskUserQuestion) | no |
| VERIFY | no | no | yes |

## Output Format

```
┌──────────────────────────────────────────────────────────┐
│ Remediation: Environment Variables                        │
├───────────────────────────────────┬──────────────────────┤
│ Automatic Actions                 │ Status               │
├───────────────────────────────────┼──────────────────────┤
│ Configure CLAUDE_PROJECT_DIR      │ DONE                 │
├───────────────────────────────────┴──────────────────────┤
│ Manual Actions Required                                   │
├───────────────────────────────────────────────────────────┤
│ [MEDIUM] Configure CLAUDE_SKILL_DIR                       │
│   No auto-detect value. Add to settings.local.json:      │
│   { "env": { "CLAUDE_SKILL_DIR": "/path/.claude/skills"  │
│                                                          │
│ [LOW] Add CLAUDE_PROJECT_DIR to ~/.zshrc for persistence │
│   echo 'export CLAUDE_PROJECT_DIR=...' >> ~/.zshrc       │
└───────────────────────────────────────────────────────────┘
```

## References

- Validator: [../validators/env-vars-validator.md](../validators/env-vars-validator.md)
- Registry: [../registries/env-vars.yaml](../registries/env-vars.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
