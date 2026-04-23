---
title: Project State Detection
impact: HIGH
impactDescription: Detects existing Claude Code project setup state
tags: [workflow]
used_by: [wm-setup]
migrated_from: analysis-rules-project.md
---

# Project State Detection

**Impact: HIGH** - Project state detection and user intent selection for onboarding

## Overview

This file contains functions for:
1. **Project State Detection**: Analyze codebase structure and components
2. **User Intent Selection**: Determine user's current work intent

**Functions Included**:
- `detectProjectState()`: Detect existing Claude Code project setup state
- `getUserIntent(project_state)`: Ask user to select setup mode
- `_suggestMode(project_state)`: Helper to suggest mode based on completeness
- `_formatStateSummary(project_state)`: Helper to format state for display

## 1. Project State Detection

### detectProjectState()

**Purpose**: Detect existing Claude Code project setup state.

**Detected Components** (7 total):
1. claude_dir - .claude/ directory exists
2. agents_md - AGENTS.md file(s) exist (any location)
3. skills - .claude/skills/ directory with files
4. agents - .claude/agents/ directory with files
5. hooks - .claude/hooks/ directory with files OR .claude/hooks.json
6. mcp_json - .mcp.json file exists
7. settings - .claude/settings.json exists

**Returns**:
```python
{
    has_claude_dir: bool,
    existing_components: dict,
    completeness_percentage: int (0-100),
    missing_components: list[str]
}
```

**Implementation**:
```python
def detectProjectState():
    """Detect existing Claude Code project setup state."""
    # Detect each component
    has_claude_dir = Glob(pattern=".claude").exists()
    has_agents_md = Glob(pattern="**/AGENTS.md").count() > 0
    has_skills = Glob(pattern=".claude/skills/*/SKILL.md").count() > 0
    has_agents = Glob(pattern=".claude/agents/*").count() > 0
    has_hooks = (
        Glob(pattern=".claude/hooks/*").count() > 0 or
        Glob(pattern=".claude/hooks.json").exists()
    )
    has_mcp_json = Glob(pattern=".mcp.json").exists()
    has_settings = Glob(pattern=".claude/settings.json").exists()

    # Build components dictionary
    existing_components = {
        "claude_dir": has_claude_dir,
        "agents_md": has_agents_md,
        "skills": has_skills,
        "agents": has_agents,
        "hooks": has_hooks,
        "mcp_json": has_mcp_json,
        "settings": has_settings
    }

    # Calculate completeness
    present_count = sum(1 for v in existing_components.values() if v)
    completeness_percentage = round((present_count / 7) * 100)
    missing_components = [k for k, v in existing_components.items() if not v]

    return {
        "has_claude_dir": has_claude_dir,
        "existing_components": existing_components,
        "completeness_percentage": completeness_percentage,
        "missing_components": missing_components
    }
```

## 2. User Intent Selection

### getUserIntent()

**Purpose**: Ask user to select setup mode via AskUserQuestion.

**Args**:
- `project_state`: Result from detectProjectState()

**Returns**:
```python
{
    selected_mode: "NEW_SETUP" | "UPDATE" | "VERIFY",
    user_selected: bool,
    recommendation: str,
    reason: str
}
```

**Behavior**:
1. If no .claude/ directory exists: Auto-select NEW_SETUP
2. If .claude/ directory exists: Show AskUserQuestion with 3 options

**Recommendation Logic**:
- completeness == 100%: Recommend VERIFY
- completeness < 100%: Recommend UPDATE

## 3. Helper Functions

### _suggestMode()

```python
def _suggestMode(project_state):
    """Suggest mode based on completeness percentage."""
    completeness = project_state["completeness_percentage"]
    if completeness >= 100:
        return "VERIFY"
    else:
        return "UPDATE"
```

### _formatStateSummary()

```python
def _formatStateSummary(project_state):
    """Format project state for user display."""
    components = project_state["existing_components"]
    present_count = sum(1 for v in components.values() if v)

    return {
        "completeness": f"{project_state['completeness_percentage']}%",
        "components_present": present_count,
        "components_total": len(components),
        "has_claude_dir": project_state["has_claude_dir"],
        "component_details": {
            "present": [k for k, v in components.items() if v],
            "missing": project_state["missing_components"]
        }
    }
```

## When to Apply

- At the start of wm-setup workflow
- When determining setup mode (NEW_SETUP, UPDATE, VERIFY)
- When displaying project state to user

## References

- [../orchestration/workflow-orchestration.md](../orchestration/workflow-orchestration.md) - Main orchestrator
- [tech-detection.md](./tech-detection.md) - Tech stack detection
