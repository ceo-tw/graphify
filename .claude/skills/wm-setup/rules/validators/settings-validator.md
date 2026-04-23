---
title: Settings Validator
impact: HIGH
impactDescription: Validates environment variables, plugins, and configuration
tags: [validator, settings, env, plugins]
used_by: [validation-orchestrator]
registry: registries/settings.yaml
order: 6
blocking: false
---

# Settings Validator

**Impact: HIGH** - Validates environment variables, plugins, and configuration settings

## Overview

This validator checks environment variables, enabled plugins, and configuration
settings defined in `settings.yaml`. Final validation step in the pipeline.

## Validation Logic

### MCP Configuration File Validation

```python
def checkMcpConfigFile(project_root: str) -> dict:
    """
    Check for .mcp.json file existence and validate its structure.

    Checks both project-level and global (~/.claude/) .mcp.json files.

    Args:
        project_root: Path to project root directory

    Returns:
        {
            "projectLevel": {
                "exists": bool,
                "path": str,
                "valid": bool,
                "servers": list of server names,
                "error": str or None
            },
            "globalLevel": {
                "exists": bool,
                "path": str,
                "valid": bool,
                "servers": list of server names,
                "error": str or None
            },
            "merged": list of all unique server names,
            "status": "PASS" | "WARN" | "FAIL",
            "message": str
        }
    """
    import json
    import os
    from pathlib import Path

    result = {
        "projectLevel": {
            "exists": False,
            "path": "",
            "valid": False,
            "servers": [],
            "error": None
        },
        "globalLevel": {
            "exists": False,
            "path": "",
            "valid": False,
            "servers": [],
            "error": None
        },
        "merged": [],
        "status": "FAIL",
        "message": ""
    }

    # Check project-level .mcp.json
    project_mcp_path = Path(project_root) / ".mcp.json"
    result["projectLevel"]["path"] = str(project_mcp_path)

    if project_mcp_path.exists():
        result["projectLevel"]["exists"] = True
        try:
            with open(project_mcp_path) as f:
                config = json.load(f)
            if "mcpServers" in config:
                result["projectLevel"]["valid"] = True
                result["projectLevel"]["servers"] = list(config["mcpServers"].keys())
            else:
                result["projectLevel"]["error"] = "Missing 'mcpServers' key"
        except json.JSONDecodeError as e:
            result["projectLevel"]["error"] = f"Invalid JSON: {str(e)}"

    # Check global-level .mcp.json
    global_mcp_path = Path.home() / ".claude" / ".mcp.json"
    result["globalLevel"]["path"] = str(global_mcp_path)

    if global_mcp_path.exists():
        result["globalLevel"]["exists"] = True
        try:
            with open(global_mcp_path) as f:
                config = json.load(f)
            if "mcpServers" in config:
                result["globalLevel"]["valid"] = True
                result["globalLevel"]["servers"] = list(config["mcpServers"].keys())
            else:
                result["globalLevel"]["error"] = "Missing 'mcpServers' key"
        except json.JSONDecodeError as e:
            result["globalLevel"]["error"] = f"Invalid JSON: {str(e)}"

    # Merge servers (project takes precedence)
    all_servers = set(result["projectLevel"]["servers"])
    all_servers.update(result["globalLevel"]["servers"])
    result["merged"] = list(all_servers)

    # Determine status
    if result["projectLevel"]["valid"] or result["globalLevel"]["valid"]:
        if result["projectLevel"]["exists"] and result["globalLevel"]["exists"]:
            result["status"] = "PASS"
            result["message"] = f"MCP configured at both levels ({len(result['merged'])} servers)"
        elif result["globalLevel"]["valid"]:
            result["status"] = "WARN"
            result["message"] = "Using global .mcp.json only (project-level recommended)"
        else:
            result["status"] = "PASS"
            result["message"] = f"Project .mcp.json valid ({len(result['projectLevel']['servers'])} servers)"
    else:
        result["status"] = "FAIL"
        result["message"] = "No valid .mcp.json found"

    return result


def executeMcpTestCommand(mcp_name: str, context: dict) -> dict:
    """
    Execute MCP server test command to verify actual tool availability.

    Uses the testCommand from registry to validate MCP is operational,
    not just configured.

    Args:
        mcp_name: Name of MCP server (e.g., "playwright", "memory")
        context: Validation context containing available tools

    Returns:
        {
            "name": str,
            "available": bool,
            "toolCount": int,
            "testResult": "PASS" | "FAIL" | "SKIP",
            "message": str,
            "tools": list of available tool names
        }
    """
    # Tool prefix patterns for each MCP server
    MCP_TOOL_PREFIXES = {
        "playwright": "mcp__playwright__",
        "memory": "mcp__memory__",
        "tavily": "mcp__tavily__",
        "serena": "mcp__plugin_serena_serena__"
    }

    # Minimum required tools for each MCP
    MCP_MIN_TOOLS = {
        "playwright": 3,  # navigate, click, screenshot at minimum
        "memory": 2,      # create_entities, search_nodes at minimum
        "tavily": 1,      # tavily_search at minimum
        "serena": 5       # find_symbol, get_symbols_overview, etc.
    }

    result = {
        "name": mcp_name,
        "available": False,
        "toolCount": 0,
        "testResult": "SKIP",
        "message": "",
        "tools": []
    }

    prefix = MCP_TOOL_PREFIXES.get(mcp_name)
    if not prefix:
        result["testResult"] = "SKIP"
        result["message"] = f"No test pattern defined for {mcp_name}"
        return result

    # Get available tools from context
    available_tools = context.get("availableTools", [])

    # Find matching tools
    matching_tools = [t for t in available_tools if t.startswith(prefix)]
    result["tools"] = matching_tools
    result["toolCount"] = len(matching_tools)

    min_required = MCP_MIN_TOOLS.get(mcp_name, 1)

    if len(matching_tools) >= min_required:
        result["available"] = True
        result["testResult"] = "PASS"
        result["message"] = f"{len(matching_tools)} tools available"
    elif len(matching_tools) > 0:
        result["available"] = True
        result["testResult"] = "WARN"
        result["message"] = f"Only {len(matching_tools)}/{min_required} tools (partial)"
    else:
        result["available"] = False
        result["testResult"] = "FAIL"
        result["message"] = f"No {mcp_name} tools detected"

    return result
```

### TypeScript Domain Detection

```python
def detectTypeScriptDomainsFromRegistry(domains_registry_path: str) -> dict:
    """
    Detect TypeScript domains from domains.yaml registry.

    Returns:
        {
            "found": bool,
            "domains": list of domain dicts,
            "recommendedPaths": str (comma-separated paths),
            "error": str or None
        }
    """
    import yaml
    import os

    result = {
        "found": False,
        "domains": [],
        "recommendedPaths": "",
        "error": None
    }

    try:
        if not os.path.exists(domains_registry_path):
            result["error"] = "domains.yaml not found"
            return result

        with open(domains_registry_path) as f:
            registry = yaml.safe_load(f)

        items = registry.get("items", [])
        ts_domains = []

        for item in items:
            tech_stack = item.get("techStack", [])
            directory = item.get("directory")

            # Check if TypeScript is in techStack
            if any("TypeScript" in tech for tech in tech_stack) and directory:
                ts_domains.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "directory": directory,
                    "techStack": tech_stack
                })

        if ts_domains:
            result["found"] = True
            result["domains"] = ts_domains
            # Generate comma-separated paths with trailing slashes
            paths = [f"{d['directory']}/" for d in ts_domains]
            result["recommendedPaths"] = ",".join(paths)

        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate settings from registry.

    Order: 6 (final validation step)
    """
    import yaml
    import os

    # Load registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    settings = context.settings
    results = []

    # Detect TypeScript domains for auto-detect validation
    domains_registry_path = registry_path.replace("settings.yaml", "domains.yaml")
    ts_detection = detectTypeScriptDomainsFromRegistry(domains_registry_path)

    # Validate environment variables
    for env_item in registry.get("environment", []):
        value = settings.get("env", {}).get(env_item["name"]) or os.environ.get(env_item["name"])
        validation_type = env_item.get("validation", {}).get("type", "env_defined")

        # Special handling for auto-detect validation type
        if validation_type == "env_defined_or_auto_detect":
            auto_detect_info = None

            if value is not None:
                # User has explicitly set the value - respect it
                status = "PASS"
                message = None
            elif ts_detection["found"]:
                # TypeScript domains found but value not set - WARN with recommendation
                status = "WARN"
                auto_detect_info = {
                    "detected": True,
                    "domains": ts_detection["domains"],
                    "recommendedValue": ts_detection["recommendedPaths"]
                }
                message = f"TypeScript domains detected. Recommended: {ts_detection['recommendedPaths']}"
            else:
                # No TypeScript domains found - SKIP (graceful degradation)
                status = "SKIP"
                message = "No TypeScript domains detected - quality check not applicable"

            results.append({
                "id": env_item["id"],
                "name": env_item["name"],
                "type": "environment",
                "status": status,
                "required": env_item["required"],
                "message": message,
                "currentValue": value,
                "defaultValue": env_item.get("defaultValue"),
                "autoDetectInfo": auto_detect_info,
                "remediation": "settings-remediation" if status == "WARN" else None
            })
            continue

        # Standard environment variable validation
        if value is not None:
            status = "PASS"
            message = None
        elif env_item["required"]:
            status = "FAIL"
            message = f"Required env var missing: {env_item['name']}"
        else:
            status = "SKIP"
            message = f"Optional env var not set: {env_item['name']}"

        results.append({
            "id": env_item["id"],
            "name": env_item["name"],
            "type": "environment",
            "status": status,
            "required": env_item["required"],
            "message": message,
            "currentValue": value,
            "defaultValue": env_item.get("defaultValue"),
            "remediation": "settings-remediation" if status == "FAIL" else None
        })

    # Validate plugins
    enabled_plugins = settings.get("enabledPlugins", {})
    for plugin in registry.get("plugins", []):
        used_by = plugin.get("usedBy", [])

        # SKIP if not used AND not required
        if not plugin["required"] and len(used_by) == 0:
            results.append({
                "id": plugin["id"],
                "name": plugin["name"],
                "type": "plugin",
                "packageName": plugin["packageName"],
                "status": "SKIP",
                "required": plugin["required"],
                "usedBy": used_by,
                "message": "Not used by any skill/agent",
                "skipReason": "unused",
                "enabled": None,
                "remediation": None
            })
            continue

        is_enabled = enabled_plugins.get(plugin["packageName"], False)

        if is_enabled:
            status = "PASS"
            message = None
        elif plugin["required"]:
            status = "FAIL"
            message = f"Required plugin not enabled: {plugin['name']}"
        else:
            status = "SKIP"
            message = f"Optional plugin not enabled: {plugin['name']}"

        results.append({
            "id": plugin["id"],
            "name": plugin["name"],
            "type": "plugin",
            "packageName": plugin["packageName"],
            "status": status,
            "required": plugin["required"],
            "usedBy": used_by,
            "message": message,
            "enabled": is_enabled,
            "remediation": "settings-remediation" if status == "FAIL" else None
        })

    # Validate config settings
    for config in registry.get("config", []):
        path_parts = config["path"].split(".")
        value = settings
        for part in path_parts:
            value = value.get(part) if isinstance(value, dict) else None

        if value is not None:
            if config.get("expectedValue") and value != config["expectedValue"]:
                status = "WARN"
                message = f"Config value mismatch: {config['name']}"
            else:
                status = "PASS"
                message = None
        elif config["required"]:
            status = "FAIL"
            message = f"Required config missing: {config['name']}"
        else:
            status = "SKIP"
            message = f"Optional config not set: {config['name']}"

        results.append({
            "id": config["id"],
            "name": config["name"],
            "type": "config",
            "path": config["path"],
            "status": status,
            "required": config["required"],
            "message": message,
            "currentValue": value,
            "expectedValue": config.get("expectedValue"),
            "remediation": "settings-remediation" if status == "FAIL" else None
        })

    # ===== MCP Configuration File Validation =====
    # First, check .mcp.json files at project and global levels
    mcp_config = checkMcpConfigFile(context.projectRoot)

    results.append({
        "id": "MCP-CONFIG",
        "name": ".mcp.json Configuration",
        "type": "mcp-config",
        "status": mcp_config["status"],
        "required": False,
        "message": mcp_config["message"],
        "projectLevel": mcp_config["projectLevel"],
        "globalLevel": mcp_config["globalLevel"],
        "configuredServers": mcp_config["merged"],
        "remediation": "settings-remediation" if mcp_config["status"] != "PASS" else None
    })

    # ===== MCP Server Validation (with testCommand) =====
    for mcp in registry.get("mcpServers", []):
        used_by = mcp.get("usedBy", [])

        # SKIP if not used AND not required
        if not mcp["required"] and len(used_by) == 0:
            results.append({
                "id": mcp["id"],
                "name": mcp["name"],
                "type": "mcp",
                "status": "SKIP",
                "required": mcp["required"],
                "usedBy": used_by,
                "message": "Not used by any skill/agent",
                "skipReason": "unused",
                "remediation": None
            })
            continue

        # Check if MCP is configured in .mcp.json
        is_configured = mcp["name"] in mcp_config["merged"]

        # Execute testCommand to verify actual tool availability
        test_result = executeMcpTestCommand(mcp["name"], context)

        # Determine status based on both configuration and availability
        if test_result["testResult"] == "PASS":
            status = "PASS"
            message = f"Operational: {test_result['toolCount']} tools available"
        elif test_result["testResult"] == "WARN":
            status = "WARN"
            message = test_result["message"]
        elif is_configured and not test_result["available"]:
            # Configured but tools not loading - indicates a problem
            status = "WARN"
            message = f"Configured but not operational: {test_result['message']}"
        elif mcp["required"]:
            status = "FAIL"
            message = f"Required MCP server not available: {mcp['name']}"
        else:
            status = "SKIP"
            message = f"Optional MCP server not available: {mcp['name']}"

        results.append({
            "id": mcp["id"],
            "name": mcp["name"],
            "type": "mcp",
            "status": status,
            "required": mcp["required"],
            "usedBy": used_by,
            "message": message,
            "configured": is_configured,
            "testResult": test_result,
            "remediation": "settings-remediation" if status in ["FAIL", "WARN"] else None
        })

    # Calculate stats (excluding unused items from pass rate)
    unused_items = [r for r in results if r.get("skipReason") == "unused"]
    used_items = [r for r in results if r.get("skipReason") != "unused"]

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARN")
    skipped_unused = len(unused_items)

    # Determine overall status
    required_failed = any(r["status"] == "FAIL" and r.get("required") for r in results)

    if required_failed:
        overall_status = "FAIL"
    elif failed > 0 or warnings > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    # Pass rate calculated only for used items
    used_total = len(used_items)
    used_passed = sum(1 for r in used_items if r["status"] == "PASS")

    return {
        "moduleId": "settings",
        "moduleName": "Settings & Environment",
        "status": overall_status,
        "passRate": (used_passed / used_total) * 100 if used_total else 0,
        "items": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "skippedUnused": skipped_unused,
            "usedTotal": used_total
        },
        "details": results,
        "blocking": False,
        "timestamp": datetime.now().isoformat()
    }
```

## Output Format

```
┌────────────────────────────────────────────────────┐
│ [6/6] Settings & Environment                        │
├──────────────────────┬──────────┬──────────────────┤
│ Setting              │ Status   │ Type             │
├──────────────────────┼──────────┼──────────────────┤
│ ── Environment ──────┼──────────┼──────────────────│
│ ENABLE_TOOL_SEARCH   │ ✅ PASS  │ env              │
│ MAX_THINKING_TOKENS  │ ✅ PASS  │ env              │
│ CLAUDE_PROJECT_DIR   │ ✅ PASS  │ env              │
│ QUALITY_CHECK_PATHS  │ ⚠️ WARN  │ env (auto-detect)│
│   └─ Recommended: dashboard/,collector/            │
├──────────────────────┼──────────┼──────────────────┤
│ ── Plugins (Used) ───┼──────────┼──────────────────│
│ typescript-lsp       │ ✅ PASS  │ plugin           │
│ serena               │ ✅ PASS  │ plugin           │
├──────────────────────┼──────────┼──────────────────┤
│ ── Plugins (Unused) ─┼──────────┼──────────────────│
│ commit-commands      │ ⏭️ SKIP  │ unused           │
│ security-guidance    │ ⏭️ SKIP  │ unused           │
│ vercel               │ ⏭️ SKIP  │ unused           │
│ vscode-html-css      │ ⏭️ SKIP  │ unused           │
├──────────────────────┼──────────┼──────────────────┤
│ ── Configuration ────┼──────────┼──────────────────│
│ plansDirectory       │ ✅ PASS  │ config           │
│ hooks                │ ✅ PASS  │ config           │
│ enabledPlugins       │ ✅ PASS  │ config           │
├──────────────────────┼──────────┼──────────────────┤
│ ── MCP Config ───────┼──────────┼──────────────────│
│ .mcp.json            │ ✅ PASS  │ mcp-config       │
│   └─ Project: ✓  Global: ✓  (4 servers)           │
├──────────────────────┼──────────┼──────────────────┤
│ ── MCP Servers ──────┼──────────┼──────────────────│
│ playwright           │ ✅ PASS  │ 12 tools         │
│ memory               │ ✅ PASS  │ 8 tools          │
│ tavily               │ ✅ PASS  │ 5 tools          │
│ serena               │ ✅ PASS  │ 22 tools         │
│ atlassian            │ ⏭️ SKIP  │ unused           │
├──────────────────────┴──────────┴──────────────────┤
│ Pass Rate: 100% (12/12 used items) Status: ✅ PASS │
└────────────────────────────────────────────────────┘
```

## Plugin Check Helper

```python
def getPluginStatus(settings: dict, package_name: str) -> dict:
    """
    Get detailed plugin status.
    """
    enabled_plugins = settings.get("enabledPlugins", {})
    is_enabled = enabled_plugins.get(package_name, False)

    return {
        "enabled": is_enabled,
        "packageName": package_name,
        "scope": package_name.split("@")[-1] if "@" in package_name else "unknown"
    }
```

## References

- Registry: [../registries/settings.yaml](../registries/settings.yaml)
- Remediation: [../remediators/settings-remediation.md](../remediators/settings-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
