---
title: NEW_SETUP Mode Process
impact: HIGH
impactDescription: Fresh project setup workflow
tags: [process]
used_by: [wm-setup]
---

# NEW_SETUP Mode Process

**Impact: HIGH** - Workflow for fresh Claude Code project setup

## Overview

NEW_SETUP mode is activated when no `.claude/` directory exists OR completeness < 30%.
This is the full setup workflow for new projects or severely incomplete setups.

Estimated duration: **3-8 minutes** (includes graphify venv build for BIN-001).

## Detection Criteria

```python
def isNewSetup(project_state: dict) -> bool:
    """Check if project needs fresh setup."""
    return (
        not project_state.get("has_claude_dir", False)
        or project_state.get("completeness_percentage", 0) < 30
    )
```

## Workflow Steps

```
NEW_SETUP Mode (3-8 minutes)
    |
    v
Step 0: Context Gate Check (MANDATORY)
    |
    v
Step 1: Unified Analysis
    - Detect tech stack
    - Analyze MCP status
    |
    v
Step 1.5: Shell Environment Check
    - Verify ENABLE_LSP_TOOL
    - Verify MAX_THINKING_TOKENS
    |
    v
Step 2: MCP Management
    - Configure serena (required)
    - Optional: memory, playwright
    |
    v
Step 3: Checklist Generation
    - Generate checklist
    - Create .claude/ structure
    - Install skills/agents
    |
    v
Step 4: Validation - Full 12-module pipeline
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
    Module 11: runtime-checks  (SKIPPED in NEW_SETUP - VERIFY only)
    Module 12: domains
    - Auto-remediate all issues (no user prompts)
    - Exception: AskUserQuestion for graphify editable option only
    |
    v
Step 4.5: Mismatch Resolution (if needed)
    |
    v
Step 5: Report Generation
    - Generate summary report
    - Save configuration
```

## Key Actions by Step

### Step 2: MCP Management

```python
def configureMCPForNewSetup(user_selection: dict) -> dict:
    """Configure MCP servers for new project."""
    mcp_config = {
        "mcpServers": {}
    }

    # Serena is always required
    mcp_config["mcpServers"]["serena"] = {
        "command": "npx",
        "args": ["-y", "@anthropic/serena"]
    }

    # Optional servers based on user selection
    if user_selection.get("memory"):
        mcp_config["mcpServers"]["memory"] = {...}

    if user_selection.get("playwright"):
        mcp_config["mcpServers"]["playwright"] = {...}

    # Write .mcp.json
    Write(file_path=".mcp.json", content=json.dumps(mcp_config, indent=2))

    return {"status": "SUCCESS", "servers": list(mcp_config["mcpServers"].keys())}
```

### Step 3: Structure Creation

```python
def createClaudeStructure() -> dict:
    """Create .claude/ directory structure."""
    directories = [
        ".claude/",
        ".claude/skills/",
        ".claude/agents/",
        ".claude/hooks/",
        ".claude/plans/",
        ".claude/graphify/"
    ]

    for dir_path in directories:
        Bash(f"mkdir -p {dir_path}")

    settings = {
        "permissions": {
            "allow": [],
            "deny": []
        }
    }
    Write(file_path=".claude/settings.json", content=json.dumps(settings, indent=2))

    return {"status": "SUCCESS", "created": directories}
```

### Step 4: 12-Module Validation Pipeline (NEW_SETUP behavior)

```python
def runNewSetupPipeline(context: ValidationContext) -> dict:
    """
    Run full 12-module pipeline in NEW_SETUP mode.

    - All modules auto-remediated (no user prompts)
    - Module 11 (runtime-checks) skipped (VERIFY only)
    - Graphify editable install: single AskUserQuestion allowed

    Modules 7-9 (binaries, env-vars, graph-data) are wm-specific.
    Module 7 (binaries) BIN-001 failure causes Module 9 (graph-data) SKIP.
    """
    # Ask only about graphify editable option (minimized AskUserQuestion)
    graphify_editable = AskUserQuestion(
        question="graphify 설치 방식을 선택해주세요.",
        header="graphify",
        options=[
            {"value": "fork_git", "label": "Fork git+https (권장)", "description": "git+https://github.com/ceo-tw/graphify.git@v4"},
            {"value": "editable", "label": "로컬 editable (개발자용)", "description": "git clone 후 pip install -e ~/graphify"}
        ]
    )

    return runValidationPipeline(context, mode="NEW_SETUP")
```

## Expected Outputs

- `.claude/` directory with full structure
- `.mcp.json` with configured servers
- `.claude/settings.json`
- Installed skills and agents
- Hook scripts configured
- graphify venv at `.claude/graphify/.venv/` (if Python 3.12 available)
- 18 domain graph JSON files built (if graphify installed)
- Playwright browsers installed (if requested)
- Checklist evaluated across all 12 modules

## When to Apply

- When `has_claude_dir` is False
- When `completeness_percentage` < 30
- Fresh project onboarding

## Module 7-10 Notes (wm-specific)

| Module | ID | Key Action |
|--------|----|------------|
| 7 | binaries | Install graphify from `ceo-tw/graphify@v4` fork (NOT PyPI); also jq, kubectl, docker, gh, python3.12 |
| 8 | env-vars | Set CLAUDE_PROJECT_DIR, CLAUDE_SKILL_DIR in shell profile |
| 9 | graph-data | Build 18 domain graphs + _global overlay; requires BIN-001 pass |
| 10 | playwright | Run `npx playwright install chromium firefox webkit` |

## References

- [update.md](./update.md) - UPDATE mode
- [verify.md](./verify.md) - VERIFY mode
- [../orchestration/validation-orchestrator.md](../orchestration/validation-orchestrator.md) - 12-module pipeline definition
