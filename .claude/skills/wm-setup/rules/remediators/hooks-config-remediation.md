---
title: Hooks Config Remediation
impact: HIGH
impactDescription: Guides configuration of missing hooks in settings.json
tags: [remediation, hooks, config]
used_by: [validation-orchestrator]
validator: validators/hooks-config-validator.md
order: 4
canAutoFix: false
---

# Hooks Config Remediation

**Impact: HIGH** - Guides configuration of missing hooks in settings.json

## Overview

This remediator handles missing hook configuration issues.
**Report only**: Modifying settings.json requires user confirmation.

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "report-only"  # Always report-only for settings.json
) -> RemediationResult:
    """
    Generate hook configuration guidance.

    Report only: settings.json modification requires user action
    """
    actions_required = []

    for item in validation_result["details"]:
        if item["status"] not in ["FAIL", "WARN"]:
            continue

        config_snippet = generateConfigSnippet(item)

        actions_required.append({
            "id": f"config-{item['id']}",
            "priority": "HIGH" if item["priority"] in ["CRITICAL", "HIGH"] else "MEDIUM",
            "description": f"Add hook config: {item['name']}",
            "config": config_snippet,
            "event": item["event"],
            "link": "See hooks configuration documentation"
        })

    return {
        "moduleId": "hooks-config",
        "moduleName": "Hooks Configuration",
        "status": "NEEDS_USER_ACTION" if actions_required else "SUCCESS",
        "actionsExecuted": [],
        "actionsRequired": actions_required,
        "summary": {
            "totalActions": len(actions_required),
            "automaticActions": 0,
            "manualActions": len(actions_required)
        },
        "timestamp": datetime.now().isoformat()
    }
```

## Configuration Snippets

```python
def generateConfigSnippet(item: dict) -> str:
    """Generate settings.json snippet for hook configuration."""

    snippets = {
        "sensitive-file-guard": '''
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/sensitive-file-guard.sh"
          }
        ]
      }
    ]
  }
}''',
        "quality-check": '''
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/quality-check.sh"
          }
        ]
      }
    ]
  }
}''',
        "decision-context": '''
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/decision-context.sh"
          }
        ]
      }
    ]
  }
}''',
        "precompact-save-state": '''
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/precompact-save-state.sh"
          }
        ]
      }
    ]
  }
}''',
        "session-start-restore-hint": '''
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/session-start-restore-hint.sh"
          }
        ]
      }
    ]
  }
}'''
    }

    return snippets.get(item["name"], "# See documentation for configuration")
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Hooks Configuration         │
├─────────────────────────────────────────────┤
│ ⚠️ settings.json 수정 필요                 │
│                                             │
│ User Actions Required                       │
├─────────────────────────────────────────────┤
│ ⚠️ [HIGH] Add hook: sensitive-file-guard   │
│    Event: PreToolUse                        │
│    Matcher: Edit|Write|MultiEdit            │
│                                             │
│    Add to .claude/settings.json:            │
│    ┌─────────────────────────────────────┐  │
│    │ "PreToolUse": [                     │  │
│    │   {                                 │  │
│    │     "matcher": "Edit|Write|Multi..",│  │
│    │     "hooks": [{                     │  │
│    │       "type": "command",            │  │
│    │       "command": "bash ..."         │  │
│    │     }]                              │  │
│    │   }                                 │  │
│    │ ]                                   │  │
│    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Complete settings.json Template

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/sensitive-file-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/plan-worktree-hook.sh"
          }
        ]
      },
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/quality-check.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/decision-context.sh"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/subagent-monitor.sh"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/precompact-save-state.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-start-restore-hint.sh"
          }
        ]
      }
    ]
  }
}
```

## References

- Validator: [../validators/hooks-config-validator.md](../validators/hooks-config-validator.md)
- Registry: [../registries/hooks.yaml](../registries/hooks.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
