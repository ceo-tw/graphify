---
title: UPDATE Mode Process
impact: HIGH
impactDescription: Existing project update workflow
tags: [process]
used_by: [wm-setup]
---

# UPDATE Mode Process

**Impact: HIGH** - Workflow for updating existing Claude Code projects

## Overview

UPDATE mode is activated when `.claude/` directory exists but completeness is 30%-99%.
This mode adds missing components without overwriting existing configuration.

## Detection Criteria

```python
def isUpdateMode(project_state: dict) -> bool:
    """Check if project needs update."""
    completeness = project_state.get("completeness_percentage", 0)
    return (
        project_state.get("has_claude_dir", False) and
        30 <= completeness < 100
    )
```

## Workflow Steps

```
UPDATE Mode
    |
    v
Step 0: Context Gate Check (MANDATORY)
    |
    v
Step 1: Unified Analysis
    - Detect existing components
    - Identify missing components
    - Analyze tech stack
    |
    v
Step 1.5: Shell Environment Check
    |
    v
Step 2: MCP Management (selective)
    - Only configure missing MCPs
    - Preserve existing configuration
    |
    v
Step 3: Checklist Generation (partial)
    - Generate checklist for missing items only
    - Skip already-configured items
    |
    v
Step 4: Validation - Full 12-module pipeline (UPDATE behavior)
    Module  1: folder          (blocking)
    Module  2: skills
    Module  3: agents
    Module  4: hooks-config
    Module  5: hooks-scripts
    Module  6: settings
    Module  7: binaries        (BIN-001=graphify is blocking for graph-data)
    Module  8: env-vars
    Module  9: graph-data      (skipped if BIN-001 fails)
    Module 10: playwright
    Module 11: runtime-checks  (SKIPPED in UPDATE - VERIFY only)
    Module 12: domains
    - Collect ALL FAIL items from all modules
    - Present single AskUserQuestion with 4 options
    |
    v
Step 4.5: Mismatch Resolution (if needed)
    |
    v
Step 5: Report Generation
```

## 4-Option User Interaction Pattern

After collecting all FAIL items across all 12 modules, present a single
AskUserQuestion with 4 options:

```python
def askUpdateAction(fail_items: list) -> str:
    """
    Present all FAIL items to user and ask for single batch decision.

    Args:
        fail_items: List of all FAIL items collected from 12-module validation

    Returns:
        str: selected option value
    """
    hard_count = sum(1 for item in fail_items if item.get("hard") in [True, "hard"])
    soft_count = len(fail_items) - hard_count

    summary = f"FAIL 항목: {len(fail_items)}개 (hard={hard_count}, soft={soft_count})"

    return AskUserQuestion(
        question=f"누락된 항목이 발견되었습니다.\n\n{summary}\n\n설치 방식을 선택해주세요.",
        header="업데이트",
        options=[
            {
                "value": "auto_all",
                "label": "Auto install all",
                "description": f"모든 {len(fail_items)}개 항목 자동 설치"
            },
            {
                "value": "hard_only",
                "label": "Install hard only",
                "description": f"필수(hard) {hard_count}개 항목만 설치"
            },
            {
                "value": "show_commands",
                "label": "Show commands",
                "description": "설치 명령어만 출력 (직접 실행)"
            },
            {
                "value": "cancel",
                "label": "Cancel",
                "description": "변경 없이 종료"
            }
        ]
    )
```

## Key Differences from NEW_SETUP

| Aspect | NEW_SETUP | UPDATE |
|--------|-----------|--------|
| Trigger | no .claude/ OR < 30% | 30%-99% completeness |
| .claude/ creation | Creates new | Preserves existing |
| MCP config | Full setup | Selective add |
| Checklist | All items | Missing items only |
| Settings | New file | Merge changes |
| User interaction | graphify option only | Single batch 4-option ask |
| Module 11 (runtime) | SKIPPED | SKIPPED |
| Module 9 (graph-data) | auto-build | user-approved build |
| Binaries 7 (graphify) | auto-install | user-approved install |
| Playwright 10 | auto-install | user-approved install |

## Selective Update Logic

```python
def getUpdateActions(project_state: dict) -> dict:
    """Determine what needs to be updated."""
    missing = project_state.get("missing_components", [])

    actions = {
        "mcp": "mcp_json" in missing,
        "skills": "skills" in missing,
        "agents": "agents" in missing,
        "hooks": "hooks" in missing,
        "settings": "settings" in missing,
        "binaries": "binaries" in missing,        # NEW: graphify, jq, etc.
        "env_vars": "env_vars" in missing,         # NEW: CLAUDE_PROJECT_DIR etc.
        "graph_data": "graph_data" in missing,     # NEW: 18 domain graphs
        "playwright": "playwright" in missing      # NEW: browser binaries
    }

    return actions
```

## Merge Strategy

```python
def mergeSettings(existing: dict, new: dict) -> dict:
    """Merge new settings into existing without overwriting."""
    result = existing.copy()

    for key, value in new.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = mergeSettings(result[key], value)
        elif isinstance(value, list) and isinstance(result[key], list):
            result[key] = list(set(result[key] + value))

    return result
```

## Expected Outputs

- Updated configuration files
- New skills/agents installed
- Missing binaries installed (graphify, jq, etc.)
- Missing environment variables set
- Missing graph data built
- Playwright browsers installed (if selected)
- Checklist for added items
- Compatibility report

## When to Apply

- When `has_claude_dir` is True
- When `completeness_percentage` is between 30 and 99 (inclusive)

## Module 7-10 Notes (wm-specific)

| Module | ID | UPDATE behavior |
|--------|----|-----------------|
| 7 | binaries | Listed in FAIL items; installed only if user selects auto_all or hard_only |
| 8 | env-vars | Listed in FAIL items; set if user approves |
| 9 | graph-data | Listed in FAIL items; built if user approves AND binaries passed |
| 10 | playwright | Listed in FAIL items; installed if user approves |

## References

- [new-setup.md](./new-setup.md) - NEW_SETUP mode
- [verify.md](./verify.md) - VERIFY mode
- [../orchestration/validation-orchestrator.md](../orchestration/validation-orchestrator.md) - 12-module pipeline definition
