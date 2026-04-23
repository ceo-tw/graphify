---
title: Settings Remediation
impact: HIGH
impactDescription: Guides configuration of environment, plugins, and settings
tags: [remediation, settings, env, plugins]
used_by: [validation-orchestrator]
validator: validators/settings-validator.md
order: 6
canAutoFix: false
---

# Settings Remediation

**Impact: HIGH** - Guides configuration of environment, plugins, and settings

## Overview

This remediator handles missing settings, plugins, and environment issues.
**Report only**: System settings require user confirmation.

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "report-only"  # Always report-only for system settings
) -> RemediationResult:
    """
    Generate settings configuration guidance.

    Report only: System settings require user action
    """
    actions_required = []

    for item in validation_result["details"]:
        if item["status"] not in ["FAIL", "WARN"]:
            continue

        item_type = item.get("type", "unknown")

        if item_type == "environment":
            actions_required.append({
                "id": f"env-{item['id']}",
                "priority": "HIGH" if item.get("required") else "MEDIUM",
                "description": f"Set environment variable: {item['name']}",
                "command": getEnvCommand(item),
                "category": "environment"
            })

        elif item_type == "plugin":
            actions_required.append({
                "id": f"plugin-{item['id']}",
                "priority": "HIGH" if item.get("required") else "MEDIUM",
                "description": f"Enable plugin: {item['name']}",
                "command": getPluginCommand(item),
                "category": "plugin"
            })

        elif item_type == "config":
            actions_required.append({
                "id": f"config-{item['id']}",
                "priority": "HIGH" if item.get("required") else "MEDIUM",
                "description": f"Configure setting: {item['name']}",
                "command": getConfigCommand(item),
                "category": "config"
            })

        elif item_type == "mcp":
            actions_required.append({
                "id": f"mcp-{item['id']}",
                "priority": "MEDIUM",
                "description": f"Configure MCP server: {item['name']}",
                "command": getMcpCommand(item),
                "category": "mcp"
            })

    return {
        "moduleId": "settings",
        "moduleName": "Settings & Environment",
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

## Environment Variable Commands

```python
def generateQualityCheckPathsValue(item: dict) -> str:
    """
    Generate QUALITY_CHECK_PATHS remediation command.

    Uses auto-detected TypeScript domains if available.
    """
    auto_detect_info = item.get("autoDetectInfo", {})

    if auto_detect_info and auto_detect_info.get("detected"):
        recommended = auto_detect_info.get("recommendedValue", "")
        domains = auto_detect_info.get("domains", [])

        domain_list = "\n".join([
            f"#   - {d['name']} ({d['directory']})" for d in domains
        ])

        return f'''
# QUALITY_CHECK_PATHS - Auto-detected TypeScript domains:
{domain_list}
#
# Add to .claude/settings.json:
{{
  "env": {{
    "QUALITY_CHECK_PATHS": "{recommended}"
  }}
}}

# This enables quality checks (ESLint, TypeScript) for these directories
# when files are modified via quality-check.sh hook.
'''
    else:
        return '''
# QUALITY_CHECK_PATHS - Manual configuration required
#
# Add to .claude/settings.json:
{
  "env": {
    "QUALITY_CHECK_PATHS": "your-typescript-directory/"
  }
}

# Set to comma-separated list of directories containing TypeScript files.
# Example: "dashboard/,collector/" for multiple directories.
'''


def getEnvCommand(item: dict) -> str:
    """Generate environment variable setup command."""

    # Special handling for auto-detect env vars
    if item.get("name") == "QUALITY_CHECK_PATHS":
        return generateQualityCheckPathsValue(item)

    env_commands = {
        "ENABLE_TOOL_SEARCH": '''
# Add to .claude/settings.json:
{
  "env": {
    "ENABLE_TOOL_SEARCH": "auto:0"
  }
}''',
        "MAX_THINKING_TOKENS": '''
# Add to .claude/settings.json:
{
  "env": {
    "MAX_THINKING_TOKENS": "31999"
  }
}'''
    }

    return env_commands.get(item["name"], f"# Set {item['name']} in settings.json env section")
```

## Plugin Configuration

```python
def getPluginCommand(item: dict) -> str:
    """Generate plugin enable command."""

    return f'''
# Add to .claude/settings.json:
{{
  "enabledPlugins": {{
    "{item.get('packageName', item['name'])}": true
  }}
}}

# Or use Claude Code UI to enable the plugin
'''
```

## MCP Server Configuration

```python
def getMcpCommand(item: dict) -> str:
    """Generate MCP server configuration with .mcp.json templates."""

    mcp_configs = {
        "playwright": '''
# Playwright MCP - Browser automation tools
# Usually bundled with Claude Code, but can be explicitly configured

# Add to .mcp.json (project or ~/.claude/.mcp.json):
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-playwright"]
    }
  }
}

# Troubleshooting:
# 1. Verify tools available: Check for mcp__playwright__* tools in /context
# 2. If 0 tools: Restart Claude Code after adding config
# 3. Minimum required tools: navigate, click, screenshot
# 4. Common issue: npx not in PATH - ensure Node.js is installed
''',
        "memory": '''
# Memory MCP - Knowledge graph storage for persistent memory

# Add to .mcp.json:
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-memory"]
    }
  }
}

# Troubleshooting:
# 1. Verify tools: create_entities, search_nodes should appear
# 2. Storage location: ~/.claude/memory/ by default
# 3. If tools missing: Check npx permissions
# 4. Required minimum: 2 tools (create_entities, search_nodes)
''',
        "tavily": '''
# Tavily MCP - Web search and research tools

# Requires TAVILY_API_KEY environment variable
# Get API key at: https://tavily.com

# Add to .mcp.json:
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-tavily"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}

# Troubleshooting:
# 1. Set env: export TAVILY_API_KEY=your_key
# 2. Or add to .claude/settings.json env section
# 3. Verify: tavily_search tool should appear in /context
# 4. API errors: Check key validity at tavily.com dashboard
''',
        "serena": '''
# Serena Plugin - Semantic code analysis tools
# CRITICAL: This is a Claude Code plugin, NOT a standalone MCP server

# Enable via Claude Code:
# 1. Settings > Plugins > Enable "serena@claude-plugins-official"
# 2. Or add to .claude/settings.json:
{
  "enabledPlugins": {
    "serena@claude-plugins-official": true
  }
}

# Troubleshooting:
# 1. Tools appear as: mcp__plugin_serena_serena__*
# 2. Minimum required: 5 tools (find_symbol, get_symbols_overview, etc.)
# 3. If 0 tools: Restart Claude Code after enabling
# 4. BLOCKING: Less than 5 serena tools indicates partial activation
#    Run /context and verify serena tools are loading

# Required serena tools:
# - find_symbol, get_symbols_overview
# - replace_symbol_body, insert_after_symbol
# - search_for_pattern, read_memory, write_memory
''',
        "atlassian": '''
# Atlassian MCP - Jira, Confluence integration

# Requires OAuth setup - follow official guide:
# https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/

# Add to .mcp.json after OAuth setup:
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-atlassian"],
      "env": {
        "ATLASSIAN_SITE": "your-site.atlassian.net",
        "ATLASSIAN_EMAIL": "your@email.com",
        "ATLASSIAN_API_TOKEN": "${ATLASSIAN_API_TOKEN}"
      }
    }
  }
}

# Troubleshooting:
# 1. Get API token: https://id.atlassian.com/manage-profile/security/api-tokens
# 2. Set ATLASSIAN_API_TOKEN env variable
# 3. Verify site URL format (no https://, no trailing /)
'''
    }

    return mcp_configs.get(item["name"], f"# Configure {item['name']} MCP server\n# Check official documentation for setup instructions")
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Settings & Environment      │
├─────────────────────────────────────────────┤
│ User Actions Required                       │
├─────────────────────────────────────────────┤
│ ── Environment ──────────────────────────── │
│ ⚠️ [HIGH] Set: MAX_THINKING_TOKENS         │
│    Add to settings.json env section:        │
│    "MAX_THINKING_TOKENS": "31999"           │
│                                             │
│ ⚠️ [MEDIUM] Set: QUALITY_CHECK_PATHS       │
│    Auto-detected TypeScript domains:        │
│    - frontend (dashboard/)                  │
│    - backend (collector/)                   │
│    "QUALITY_CHECK_PATHS": "dashboard/,collector/" │
│                                             │
│ ── Plugins ──────────────────────────────── │
│ ⚠️ [HIGH] Enable: typescript-lsp           │
│    Package: typescript-lsp@claude-plugins   │
│    Required for TypeScript support          │
│                                             │
│ ⚠️ [HIGH] Enable: serena                   │
│    Package: serena@claude-plugins-official  │
│    Required for semantic code analysis      │
│                                             │
│ ── MCP Servers ──────────────────────────── │
│ ℹ️ [MEDIUM] Configure: playwright           │
│    Used by: e2e-test skill                  │
│    Usually bundled with Claude Code         │
└─────────────────────────────────────────────┘
```

## Complete settings.json Template

```json
{
  "env": {
    "ENABLE_TOOL_SEARCH": "auto:0",
    "MAX_THINKING_TOKENS": "31999",
    "QUALITY_CHECK_PATHS": "dashboard/,collector/"
  },
  "enabledPlugins": {
    "typescript-lsp@claude-plugins-official": true,
    "serena@claude-plugins-official": true,
    "commit-commands@claude-plugins-official": true,
    "security-guidance@claude-plugins-official": true,
    "vercel@claude-plugins-official": true,
    "vscode-html-css@claude-code-lsps": true
  },
  "plansDirectory": ".claude/plans"
}
```

> **Note**: `QUALITY_CHECK_PATHS` value should be adjusted based on your project's
> TypeScript directories. The wm-setup validator auto-detects these from `domains.yaml`.

## Priority Guidance

| Category | Priority | Rationale |
|----------|----------|-----------|
| Required plugins | HIGH | Core functionality |
| Required env vars | HIGH | Workflow support |
| Optional plugins | MEDIUM | Enhanced features |
| MCP servers | MEDIUM | Feature-specific |

## .mcp.json Configuration Guide

### File Locations

MCP servers can be configured at two levels:

| Level | Path | Priority | Scope |
|-------|------|----------|-------|
| Project | `./.mcp.json` | Higher | Current project only |
| Global | `~/.claude/.mcp.json` | Lower | All projects |

Project-level configuration overrides global for matching server names.

### Complete .mcp.json Template

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-playwright"]
    },
    "memory": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-memory"]
    },
    "tavily": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-tavily"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}
```

### Validation Checklist

After configuring .mcp.json:

1. **Restart Claude Code** - Required for changes to take effect
2. **Run `/context`** - Verify tools appear in output
3. **Check tool count** - Each MCP should show multiple tools:
   - playwright: 10+ tools (mcp__playwright__*)
   - memory: 5+ tools (mcp__memory__*)
   - tavily: 3+ tools (mcp__tavily__*)
   - serena: 15+ tools (mcp__plugin_serena_serena__*)

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| MCP not loading | 0 tools in /context | Check JSON syntax, restart Claude |
| Partial tools | Fewer tools than expected | Check npx permissions, Node.js version |
| Environment vars | API tools failing | Set env vars in shell or settings.json |
| Plugin vs MCP | serena not showing | Enable via Plugins, not .mcp.json |

### Quick Diagnostics

```bash
# Check if .mcp.json is valid JSON
cat .mcp.json | python -m json.tool

# Check global config
cat ~/.claude/.mcp.json | python -m json.tool

# Verify Node.js/npx available
which npx && npx --version
```

## References

- Validator: [../validators/settings-validator.md](../validators/settings-validator.md)
- Registry: [../registries/settings.yaml](../registries/settings.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
