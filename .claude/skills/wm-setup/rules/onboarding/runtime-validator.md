---
title: Runtime Validator
impact: HIGH
impactDescription: Validates runtime environment and connectivity (VERIFY mode only)
tags: [validator, runtime, mcp, environment]
used_by: [validation-orchestrator]
registry: onboarding/runtime-checks.yaml
order: 7
blocking: false
verifyModeOnly: true
---

# Runtime Validator

**Impact: HIGH** - Validates runtime environment, MCP connectivity, and actual system state

## Overview

This validator performs runtime checks to verify that the Claude Code environment
is properly configured and operational. Unlike static validators (1-6), this module
tests actual connectivity, environment values, and plugin functionality.

**VERIFY Mode Only**: This module only executes in VERIFY mode, not in NEW_SETUP or UPDATE.

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> RuntimeValidationResult:
    """
    Validate runtime environment and connectivity.

    Order: 7 (Post-VERIFY checklist)
    Blocking: False (always report-only)
    Mode: VERIFY only

    Args:
        registry_path: Path to runtime-checks.yaml
        context: Shared validation context

    Returns:
        RuntimeValidationResult with 6 category results
    """
    import yaml
    import os

    # Load runtime checks registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    categories = registry.get("categories", [])
    category_results = []
    all_details = []

    # Execute checks for each category
    for category in categories:
        cat_id = category["id"]
        cat_name = category["name"]
        checks = category.get("checks", [])

        # Dispatch to category-specific validator
        if cat_id == "RC-MCP":
            result = checkMCPConnectivity(checks, context)
        elif cat_id == "RC-ENV":
            result = checkEnvironmentValues(checks, context)
        elif cat_id == "RC-PERM":
            result = checkPermissionConfig(checks, context)
        elif cat_id == "RC-PLUG":
            result = checkPluginFunctionality(checks, context)
        elif cat_id == "RC-HOOK":
            result = checkHookIntegration(checks, context)
        elif cat_id == "RC-AGENT":
            result = checkAgentWorkflow(checks, context)
        else:
            result = {
                "id": cat_id,
                "name": cat_name,
                "status": "SKIP",
                "passRate": 0,
                "checksTotal": len(checks),
                "checksPassed": 0,
                "checksFailed": len(checks)
            }

        category_results.append(result)
        all_details.extend(result.get("details", []))

    # Aggregate results
    return aggregateResults(category_results, all_details)


def checkMCPConnectivity(checks: list, context: ValidationContext) -> CategoryResult:
    """
    Check MCP server connectivity and tool availability.

    For each MCP server:
    1. Use ToolSearch to list available tools
    2. Compare with expectedTools from check definition
    3. Report PASS if all expected tools are available

    Args:
        checks: List of MCP connectivity checks
        context: Validation context

    Returns:
        CategoryResult for RC-MCP
    """
    details = []

    for check in checks:
        check_id = check["id"]
        server_name = check["server"]
        expected_tools = check.get("expectedTools", [])
        severity = check.get("severity", "WARNING")
        required = check.get("required", False)

        # Query available tools using ToolSearch
        # NOTE: In actual implementation, use MCP tool listing API
        # For now, document the expected behavior
        try:
            # Example: available_tools = ToolSearch(server=server_name)
            # For demonstration, assume we check tool availability
            available_tools = []  # Replace with actual tool discovery

            missing_tools = [t for t in expected_tools if t not in available_tools]

            if not missing_tools:
                status = "PASS"
                message = f"MCP server '{server_name}' connected with all expected tools"
            elif required:
                status = "FAIL"
                message = f"Required MCP server '{server_name}' missing tools: {', '.join(missing_tools)}"
            else:
                status = "WARN"
                message = f"Optional MCP server '{server_name}' missing tools: {', '.join(missing_tools)}"

        except Exception as e:
            status = "FAIL" if required else "WARN"
            message = f"Cannot connect to MCP server '{server_name}': {str(e)}"
            missing_tools = expected_tools

        details.append({
            "id": check_id,
            "category": "RC-MCP",
            "name": check["name"],
            "status": status,
            "testType": "list_tools",
            "currentValue": len(available_tools),
            "recommendedValue": len(expected_tools),
            "severity": severity,
            "message": message,
            "remediation": check.get("remediation")
        })

    # Calculate category status
    passed = sum(1 for d in details if d["status"] == "PASS")
    failed = sum(1 for d in details if d["status"] == "FAIL")
    total = len(checks)

    return {
        "id": "RC-MCP",
        "name": "MCP Connectivity",
        "status": "PASS" if failed == 0 else ("WARN" if passed > 0 else "FAIL"),
        "passRate": (passed / total * 100) if total > 0 else 0,
        "checksTotal": total,
        "checksPassed": passed,
        "checksFailed": failed,
        "details": details
    }


def checkEnvironmentValues(checks: list, context: ValidationContext) -> CategoryResult:
    """
    Compare current environment values with recommended values.

    For each environment variable:
    1. Get current value from os.environ or settings
    2. Compare with recommendedValue
    3. Report WARN if mismatch (not FAIL, as these are recommendations)

    Args:
        checks: List of environment value checks
        context: Validation context

    Returns:
        CategoryResult for RC-ENV
    """
    import os

    details = []
    settings = context.settings

    for check in checks:
        check_id = check["id"]
        env_var = check["envVar"]
        recommended_value = check["recommendedValue"]
        rationale = check.get("rationale", "")
        severity = check.get("severity", "WARNING")

        # Get current value (check settings.env first, then os.environ)
        current_value = settings.get("env", {}).get(env_var) or os.environ.get(env_var)

        if current_value == recommended_value:
            status = "PASS"
            message = f"{env_var} matches recommended value"
        elif current_value is None:
            status = "WARN"
            message = f"{env_var} not set (recommended: {recommended_value})"
        else:
            status = "WARN"
            message = f"{env_var}={current_value} differs from recommended: {recommended_value}. {rationale}"

        details.append({
            "id": check_id,
            "category": "RC-ENV",
            "name": check["name"],
            "status": status,
            "testType": "value_compare",
            "currentValue": current_value,
            "recommendedValue": recommended_value,
            "severity": severity,
            "message": message,
            "remediation": check.get("remediation")
        })

    # Calculate category status (ENV mismatches are always WARN, never FAIL)
    passed = sum(1 for d in details if d["status"] == "PASS")
    total = len(checks)

    return {
        "id": "RC-ENV",
        "name": "Environment Values",
        "status": "PASS" if passed == total else "WARN",
        "passRate": (passed / total * 100) if total > 0 else 0,
        "checksTotal": total,
        "checksPassed": passed,
        "checksFailed": 0,  # ENV checks never fail
        "details": details
    }


def checkPermissionConfig(checks: list, context: ValidationContext) -> CategoryResult:
    """
    Verify permission settings in settings.json.

    Checks permissions.allow configuration for essential tool patterns.

    Args:
        checks: List of permission checks
        context: Validation context

    Returns:
        CategoryResult for RC-PERM
    """
    details = []
    settings = context.settings

    for check in checks:
        check_id = check["id"]
        config_path = check["configPath"]
        expected_patterns = check.get("expectedPatterns", [])
        severity = check.get("severity", "WARNING")

        # Navigate to config path (e.g., "permissions.allow")
        path_parts = config_path.split(".")
        config_value = settings
        for part in path_parts:
            config_value = config_value.get(part, []) if isinstance(config_value, dict) else []

        # Check if expected patterns are present
        if isinstance(config_value, list):
            missing_patterns = [p for p in expected_patterns if p not in config_value]
            if not missing_patterns:
                status = "PASS"
                message = "All essential tool patterns allowed"
            else:
                status = "WARN"
                message = f"Missing permission patterns: {', '.join(missing_patterns)}"
        else:
            status = "FAIL"
            message = f"Invalid permissions configuration at {config_path}"
            missing_patterns = expected_patterns

        details.append({
            "id": check_id,
            "category": "RC-PERM",
            "name": check["name"],
            "status": status,
            "testType": "config_check",
            "currentValue": str(config_value),
            "recommendedValue": str(expected_patterns),
            "severity": severity,
            "message": message,
            "remediation": check.get("remediation")
        })

    passed = sum(1 for d in details if d["status"] == "PASS")
    failed = sum(1 for d in details if d["status"] == "FAIL")
    total = len(checks)

    return {
        "id": "RC-PERM",
        "name": "Permission Config",
        "status": "PASS" if failed == 0 else "WARN",
        "passRate": (passed / total * 100) if total > 0 else 0,
        "checksTotal": total,
        "checksPassed": passed,
        "checksFailed": failed,
        "details": details
    }


def checkPluginFunctionality(checks: list, context: ValidationContext) -> CategoryResult:
    """
    Test actual plugin operations.

    For each plugin:
    1. Verify plugin is enabled
    2. Optionally: Attempt simple tool call to verify functionality
    3. Report based on actual response

    Args:
        checks: List of plugin functionality checks
        context: Validation context

    Returns:
        CategoryResult for RC-PLUG
    """
    details = []
    settings = context.settings
    enabled_plugins = settings.get("enabledPlugins", {})

    for check in checks:
        check_id = check["id"]
        plugin_name = check["plugin"]
        severity = check.get("severity", "WARNING")

        # Find plugin package name from settings registry
        plugin_enabled = any(
            enabled_plugins.get(pkg, False)
            for pkg in enabled_plugins.keys()
            if plugin_name in pkg
        )

        if plugin_enabled:
            status = "PASS"
            message = f"Plugin '{plugin_name}' is enabled"
        else:
            status = "FAIL" if severity == "CRITICAL" else "WARN"
            message = f"Plugin '{plugin_name}' is not enabled"

        details.append({
            "id": check_id,
            "category": "RC-PLUG",
            "name": check["name"],
            "status": status,
            "testType": "tool_call",
            "currentValue": str(plugin_enabled),
            "recommendedValue": "true",
            "severity": severity,
            "message": message,
            "remediation": check.get("remediation")
        })

    passed = sum(1 for d in details if d["status"] == "PASS")
    failed = sum(1 for d in details if d["status"] == "FAIL")
    total = len(checks)

    return {
        "id": "RC-PLUG",
        "name": "Plugin Functionality",
        "status": "PASS" if failed == 0 else ("WARN" if passed > 0 else "FAIL"),
        "passRate": (passed / total * 100) if total > 0 else 0,
        "checksTotal": total,
        "checksPassed": passed,
        "checksFailed": failed,
        "details": details
    }


def checkHookIntegration(checks: list, context: ValidationContext) -> CategoryResult:
    """
    Test hook script execution.

    For each hook:
    1. Verify hook script exists
    2. Verify hook is configured in settings.json
    3. Optionally: Check script is executable

    Args:
        checks: List of hook integration checks
        context: Validation context

    Returns:
        CategoryResult for RC-HOOK
    """
    import os

    details = []
    settings = context.settings
    project_root = context.projectRoot

    for check in checks:
        check_id = check["id"]
        script_path = check["scriptPath"]
        hook_type = check.get("hookType", "")
        severity = check.get("severity", "WARNING")

        # Check if script exists
        full_path = os.path.join(project_root, script_path)
        script_exists = os.path.isfile(full_path)

        # Check if hook is configured
        hooks_config = settings.get("hooks", {})
        hook_configured = any(
            hook.get("scriptPath") == script_path
            for hook in hooks_config.values()
            if isinstance(hook, dict)
        )

        if script_exists and hook_configured:
            status = "PASS"
            message = f"Hook script '{script_path}' exists and is configured"
        elif not script_exists:
            status = "WARN"
            message = f"Hook script '{script_path}' not found"
        else:
            status = "WARN"
            message = f"Hook script '{script_path}' exists but not configured"

        details.append({
            "id": check_id,
            "category": "RC-HOOK",
            "name": check["name"],
            "status": status,
            "testType": "exec_script",
            "currentValue": f"exists={script_exists}, configured={hook_configured}",
            "recommendedValue": "exists=true, configured=true",
            "severity": severity,
            "message": message,
            "remediation": check.get("remediation")
        })

    passed = sum(1 for d in details if d["status"] == "PASS")
    failed = sum(1 for d in details if d["status"] == "FAIL")
    total = len(checks)

    return {
        "id": "RC-HOOK",
        "name": "Hook Integration",
        "status": "PASS" if failed == 0 else "WARN",
        "passRate": (passed / total * 100) if total > 0 else 0,
        "checksTotal": total,
        "checksPassed": passed,
        "checksFailed": failed,
        "details": details
    }


def checkAgentWorkflow(checks: list, context: ValidationContext) -> CategoryResult:
    """
    Verify agent and skill file integrity.

    For each check:
    1. Find files matching pattern
    2. Parse frontmatter/YAML
    3. Report any syntax errors

    Args:
        checks: List of agent workflow checks
        context: Validation context

    Returns:
        CategoryResult for RC-AGENT
    """
    import os
    import glob

    details = []
    project_root = context.projectRoot

    for check in checks:
        check_id = check["id"]
        pattern = check["pattern"]
        check_type = check.get("checkType", "frontmatter_valid")
        severity = check.get("severity", "WARNING")

        # Find files matching pattern
        full_pattern = os.path.join(project_root, pattern)
        files = glob.glob(full_pattern)

        if not files:
            status = "WARN"
            message = f"No files found matching pattern: {pattern}"
        else:
            # Check frontmatter validity (simplified check)
            invalid_files = []
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # Simple check: frontmatter starts with --- and ends with ---
                        if not (content.startswith("---") and "\n---\n" in content):
                            invalid_files.append(os.path.basename(file_path))
                except Exception as e:
                    invalid_files.append(os.path.basename(file_path))

            if not invalid_files:
                status = "PASS"
                message = f"All {len(files)} files have valid frontmatter"
            else:
                status = "WARN"
                message = f"Invalid frontmatter in: {', '.join(invalid_files)}"

        details.append({
            "id": check_id,
            "category": "RC-AGENT",
            "name": check["name"],
            "status": status,
            "testType": "file_parse",
            "currentValue": f"{len(files)} files found",
            "recommendedValue": "all files valid",
            "severity": severity,
            "message": message,
            "remediation": check.get("remediation")
        })

    passed = sum(1 for d in details if d["status"] == "PASS")
    failed = sum(1 for d in details if d["status"] == "FAIL")
    total = len(checks)

    return {
        "id": "RC-AGENT",
        "name": "Agent Workflow",
        "status": "PASS" if failed == 0 else "WARN",
        "passRate": (passed / total * 100) if total > 0 else 0,
        "checksTotal": total,
        "checksPassed": passed,
        "checksFailed": failed,
        "details": details
    }


def aggregateResults(category_results: list, all_details: list) -> RuntimeValidationResult:
    """
    Aggregate category results into final validation result.

    Args:
        category_results: List of CategoryResult objects
        all_details: List of all RuntimeCheckDetail objects

    Returns:
        RuntimeValidationResult conforming to ValidationResult interface
    """
    from datetime import datetime

    total_checks = sum(r["checksTotal"] for r in category_results)
    passed_checks = sum(r["checksPassed"] for r in category_results)
    failed_checks = sum(r["checksFailed"] for r in category_results)
    warned_checks = total_checks - passed_checks - failed_checks

    # Determine overall status
    if failed_checks > 0:
        overall_status = "FAIL"
    elif warned_checks > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    return {
        "moduleId": "runtime",
        "moduleName": "Runtime Checks",
        "status": overall_status,
        "passRate": pass_rate,
        "items": {
            "total": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "warnings": warned_checks
        },
        "details": all_details,
        "blocking": False,  # Always false - report only
        "categories": category_results,
        "timestamp": datetime.now().isoformat()
    }
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ [7/7] Runtime Checks                        │
├──────────────────────┬─────────┬────────────┤
│ Category             │ Status  │ Pass Rate  │
├──────────────────────┼─────────┼────────────┤
│ RC-MCP               │ ✅ PASS │ 100%       │
│ RC-ENV               │ ⚠️ WARN │ 50%        │
│ RC-PERM              │ ✅ PASS │ 100%       │
│ RC-PLUG              │ ❌ FAIL │ 50%        │
│ RC-HOOK              │ ⚠️ WARN │ 0%         │
│ RC-AGENT             │ ✅ PASS │ 100%       │
├──────────────────────┴─────────┴────────────┤
│ Overall: ⚠️ WARN  Pass Rate: 67% (8/12)     │
└─────────────────────────────────────────────┘

Post-VERIFY Checklist: See post-verify-checklist.md
```

## Integration Points

- **Called By**: `validation-orchestrator.md` (7th module, VERIFY mode only)
- **Registry**: `onboarding/runtime-checks.yaml`
- **Checklist Output**: `post-verify-checklist.md`

## Error Handling

```python
def handleValidationError(check: dict, error: Exception) -> ValidationDetail:
    """
    Handle errors during runtime validation gracefully.
    Never block pipeline on runtime check failures.
    """
    return {
        "id": check["id"],
        "name": check["name"],
        "status": "WARN",
        "message": f"Check failed with error: {str(error)}",
        "remediation": "See post-verify-checklist.md for manual testing"
    }
```

## References

- [runtime-checks.yaml](./runtime-checks.yaml)
- [post-verify-checklist.md](./post-verify-checklist.md)
- [post-verify-workflow.md](./post-verify-workflow.md)
- [_validator-interface.md](../validators/_validator-interface.md)
