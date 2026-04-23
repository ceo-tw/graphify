---
title: Context Data Gate
impact: CRITICAL
impactDescription: Ensures /context data before any analysis
tags: [component]
used_by: [wm-setup]
---

# Context Data Gate

**Impact: CRITICAL** - Verify /context data is provided before any analysis

## Overview

This component ensures that `/context` output is available before proceeding
with any project analysis. This is MANDATORY for Step 0.

## Why /context is Required

- Provides accurate MCP server status (enabled/disabled)
- Shows installed skills and agents with token counts
- Displays model and context window usage
- Cannot reliably detect Claude Code configuration without it

## Detection Logic

```python
def hasContextData(user_input: str) -> bool:
    """
    Check if user input contains /context output data.

    Args:
        user_input: Raw user input string

    Returns:
        True if /context data detected, False otherwise
    """
    indicators = [
        "Context Usage",
        "MCP tools",
        "Skills",
        "Custom agents",
        "mcp__"
    ]
    return any(indicator in user_input for indicator in indicators)
```

## Workflow

```
User invokes /wm-setup
    |
    v
Check hasContextData(user_input)
    |
    +--> TRUE: Parse context, proceed to Step 1
    |
    +--> FALSE: Show AskUserQuestion with guide, EXIT skill
```

## AskUserQuestion Format

```python
def generateContextGuide() -> dict:
    """Generate AskUserQuestion for missing /context data."""
    return {
        "questions": [{
            "header": "Context 필요",
            "question": "/context를 실행해서 출력되는 전체 text와 함께 아래와 같이 실행해 주세요.\n\n/wm-setup ⎿   Context Usage\n     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   claude-opus-4-5-20251101 · 71k/200k tokens (35%)\n     ⛁ ⛁ ⛁ ⛀ ⛀ ⛀ ⛁ ⛁ ⛁ ⛁\n     ...",
            "options": [
                {
                    "label": "알겠습니다 (권장)",
                    "description": "/context 실행 후 출력을 복사해서 /wm-setup와 함께 붙여넣기"
                },
                {
                    "label": "없이 진행",
                    "description": "일부 검증 기능이 제한됩니다 (MCP 서버 상태 확인 불가)"
                }
            ],
            "multiSelect": False
        }]
    }
```

## Context Parsing

```python
def parseContextOutput(context_output: str) -> dict:
    """
    Parse /context output into structured data.

    Returns:
        {
            "mcp_servers": ["serena", "playwright", "memory", ...],
            "skills": {"project": [...], "plugin": [...]},
            "agents": {"project": [...], "user": [...], "plugin": [...]},
            "memory_files": ["CLAUDE.md", ...],
            "model": "claude-opus-4-5-20251101",
            "tokens": {"used": 46000, "total": 200000},
            "serena": {
                "active": bool,
                "toolCount": int,
                "tools": list,
                "status": "PASS" | "WARN" | "FAIL"
            },
            "availableTools": list  # All tool names for MCP validation
        }
    """
    import re

    result = {
        "mcp_servers": [],
        "skills": {"project": [], "plugin": []},
        "agents": {"project": [], "user": [], "plugin": []},
        "memory_files": [],
        "model": "",
        "tokens": {"used": 0, "total": 0},
        "serena": {
            "active": False,
            "toolCount": 0,
            "tools": [],
            "status": "FAIL"
        },
        "availableTools": []
    }

    # Extract model and tokens from header
    model_match = re.search(r'(claude-[a-z0-9\-]+)\s*·\s*(\d+)k/(\d+)k', context_output)
    if model_match:
        result["model"] = model_match.group(1)
        result["tokens"]["used"] = int(model_match.group(2)) * 1000
        result["tokens"]["total"] = int(model_match.group(3)) * 1000

    # Extract all tool names (for MCP validation)
    tool_matches = re.findall(r'(mcp__[a-zA-Z_]+__[a-zA-Z_]+)', context_output)
    result["availableTools"] = list(set(tool_matches))

    # Extract MCP servers from tool names
    mcp_matches = re.findall(r'mcp__([a-zA-Z_]+)__', context_output)
    for raw_server in mcp_matches:
        server = raw_server.replace("plugin_serena_", "").replace("_", "-")
        if server and server not in result["mcp_servers"]:
            result["mcp_servers"].append(server)

    # Check Serena activation explicitly
    serena_result = checkSerenaActivation(context_output)
    result["serena"] = serena_result

    return result
```

## Serena Plugin Verification

```python
def checkSerenaActivation(context_output: str) -> dict:
    """
    Explicitly verify Serena plugin activation status.

    Serena is CRITICAL for semantic code analysis. This function
    checks for minimum required tools to ensure proper activation.

    Args:
        context_output: Raw /context output string

    Returns:
        {
            "active": bool,
            "toolCount": int,
            "tools": list of tool names,
            "status": "PASS" | "WARN" | "FAIL",
            "message": str,
            "blocking": bool  # True if serena is required but inactive
        }
    """
    import re

    # Required minimum tools for serena to be considered active
    SERENA_MIN_TOOLS = 5

    # Core serena tools that should be present
    SERENA_CORE_TOOLS = [
        "find_symbol",
        "get_symbols_overview",
        "replace_symbol_body",
        "search_for_pattern",
        "read_memory"
    ]

    result = {
        "active": False,
        "toolCount": 0,
        "tools": [],
        "status": "FAIL",
        "message": "",
        "blocking": False
    }

    # Extract serena tools (they have the pattern: mcp__plugin_serena_serena__*)
    serena_pattern = r'mcp__plugin_serena_serena__([a-zA-Z_]+)'
    tool_matches = re.findall(serena_pattern, context_output)

    # Deduplicate
    serena_tools = list(set(tool_matches))
    result["tools"] = serena_tools
    result["toolCount"] = len(serena_tools)

    # Check for core tools
    core_present = sum(1 for tool in SERENA_CORE_TOOLS if tool in serena_tools)

    if len(serena_tools) >= SERENA_MIN_TOOLS and core_present >= 3:
        result["active"] = True
        result["status"] = "PASS"
        result["message"] = f"Serena active: {len(serena_tools)} tools available"
    elif len(serena_tools) > 0:
        # Partial activation - tools present but below threshold
        result["active"] = True
        result["status"] = "WARN"
        result["message"] = f"Serena partially active: {len(serena_tools)}/{SERENA_MIN_TOOLS} tools"
        result["blocking"] = False  # Warn but don't block
    else:
        # No serena tools detected
        result["active"] = False
        result["status"] = "FAIL"
        result["message"] = "Serena not active: 0 tools detected"
        result["blocking"] = True  # CRITICAL - blocks workflow

    return result


def generateSerenaRemediationGuide() -> str:
    """
    Generate remediation guide for Serena activation issues.
    """
    return '''
## Serena Plugin Activation Required

Serena provides semantic code analysis tools that are CRITICAL for:
- Symbol navigation (find_symbol, get_symbols_overview)
- Code modification (replace_symbol_body, insert_after_symbol)
- Pattern search (search_for_pattern)
- Memory persistence (read_memory, write_memory)

### How to Enable Serena

**Option 1: Via Claude Code UI**
1. Open Claude Code Settings
2. Navigate to Plugins
3. Enable "serena@claude-plugins-official"
4. Restart Claude Code

**Option 2: Via settings.json**
Add to `.claude/settings.json`:
```json
{
  "enabledPlugins": {
    "serena@claude-plugins-official": true
  }
}
```

### Verification

After enabling, run `/context` and check for:
```
mcp__plugin_serena_serena__find_symbol
mcp__plugin_serena_serena__get_symbols_overview
mcp__plugin_serena_serena__replace_symbol_body
...
```

Minimum 5 serena tools should be visible.

### Troubleshooting

| Issue | Solution |
|-------|----------|
| 0 tools after enable | Restart Claude Code |
| Partial tools (<5) | Check for errors in Claude Code logs |
| Plugin not in list | Update Claude Code to latest version |
'''
```

## When to Apply

- ALWAYS at the start of wm-setup workflow (Step 0)
- Before any project analysis

## References

- [../orchestration/workflow-orchestration.md](../orchestration/workflow-orchestration.md)
