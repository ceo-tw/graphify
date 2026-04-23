---
title: Hooks Scripts Validator
impact: HIGH
impactDescription: Validates hook script files existence and permissions
tags: [validator, hooks, scripts]
used_by: [validation-orchestrator]
registry: registries/hooks.yaml
order: 5
blocking: false
---

# Hooks Scripts Validator

**Impact: HIGH** - Validates hook script files existence and permissions

## Overview

This validator checks for hook script files defined in `hooks.yaml` (scripts section).
Verifies that script files exist and have proper permissions.

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate hook scripts from registry, including specification verification.

    Order: 5 (after hooks config validation)
    """
    import yaml
    import os
    from pathlib import Path

    # Load registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []
    spec_results = []
    registries_dir = Path(registry_path).parent

    for script in registry.get("scripts", []):
        script_path = Path(context.projectRoot) / script["path"]

        # Check existence
        exists = script_path.exists() and script_path.is_file()

        # Check executable permission (if required)
        executable_required = script["validation"].get("executable", False)
        is_executable = os.access(script_path, os.X_OK) if exists else False

        # Validate specification file
        spec_result = validateHookSpecification(script["id"], str(registries_dir))
        spec_results.append(spec_result)

        if exists:
            if executable_required and not is_executable:
                status = "WARN"
                message = f"Script not executable: {script['name']}"
            else:
                status = "PASS"
                message = None
        else:
            if script["priority"] == "CRITICAL":
                status = "FAIL"
                message = f"Critical script missing: {script['name']}"
            elif script["priority"] == "HIGH":
                status = "WARN"
                message = f"Recommended script missing: {script['name']}"
            else:
                status = "SKIP"
                message = f"Optional script missing: {script['name']}"

        results.append({
            "id": script["id"],
            "name": script["name"],
            "path": script["path"],
            "status": status,
            "priority": script["priority"],
            "exists": exists,
            "executable": is_executable if exists else None,
            "usedBy": script.get("usedBy", []),
            "message": message,
            "specification": spec_result,  # Include spec validation result
            "remediation": "hooks-scripts-remediation" if status in ["FAIL", "WARN"] else None
        })

    # Calculate stats
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARN")

    # Calculate specification stats
    spec_summary = calculateOverallSpecificationRate(spec_results)

    # Determine overall status
    if failed > len(results) * 0.3:
        overall_status = "FAIL"
    elif failed > 0 or warnings > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    return {
        "moduleId": "hooks-scripts",
        "moduleName": "Hook Scripts",
        "status": overall_status,
        "passRate": (passed / len(results)) * 100 if results else 0,
        "items": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings
        },
        "specifications": {
            "total": spec_summary["totalSpecs"],
            "existing": spec_summary["existingSpecs"],
            "averageChecklistRate": spec_summary["averageChecklistRate"],
            "averageTestRate": spec_summary["averageTestRate"],
            "status": spec_summary["overallStatus"]
        },
        "details": results,
        "blocking": False,
        "timestamp": datetime.now().isoformat()
    }
```

## Script Categories

| Category | Scripts | Priority |
|----------|---------|----------|
| Security | sensitive-file-guard.sh | CRITICAL |
| Workflow | plan-worktree-hook.sh, precompact-save-state.sh | HIGH |
| Quality | quality-check.sh | HIGH |
| Context | decision-context.sh, session-start-restore-hint.sh | MEDIUM |
| Utility | hook-utils.sh (shared library) | CRITICAL |

## Output Format

```
┌─────────────────────────────────────────────────────────────┐
│ [5/6] Hook 스크립트                                          │
├──────────────────────┬─────────┬────────────┬───────────────┤
│ 스크립트              │ 상태    │ 실행 가능   │ 사양서        │
├──────────────────────┼─────────┼────────────┼───────────────┤
│ sensitive-file-guard │ ✅ 통과 │ 예         │ ✅ 100%       │
│ plan-worktree-hook   │ ✅ 통과 │ 예         │ ✅ 100%       │
│ quality-check        │ ✅ 통과 │ 예         │ ✅ 100%       │
│ decision-context     │ ✅ 통과 │ 예         │ ✅ 100%       │
│ subagent-monitor     │ ✅ 통과 │ 예         │ ✅ 100%       │
│ precompact-save-state│ ✅ 통과 │ 예         │ ✅ 100%       │
│ session-start-*      │ ✅ 통과 │ 예         │ ✅ 100%       │
│ hook-utils           │ ✅ 통과 │ N/A        │ ⚠️ 미지정     │
├──────────────────────┴─────────┴────────────┴───────────────┤
│ 스크립트 통과율: 100% (8/8)                                   │
│ 사양서 커버리지: 87.5% (7/8)                                  │
│ 평균 체크리스트 완료율: 100%                                  │
│ 상태: ✅ 통과                                                │
└─────────────────────────────────────────────────────────────┘
```

### Specification Column Legend

| Icon | Meaning |
|------|---------|
| ✅ 100% | Fully verified (checklist & tests 100%) |
| ✅ 80%+ | Verified (checklist & tests ≥80%) |
| ⚠️ 60-79% | Partial verification |
| ❌ <60% | Insufficient verification |
| ⚠️ 미지정 | No specification file found |

## Permission Check

```python
def checkPermissions(script_path: Path) -> dict:
    """
    Check script file permissions.

    Returns:
    {
        "readable": True/False,
        "executable": True/False,
        "mode": "755" or similar
    }
    """
    import stat

    if not script_path.exists():
        return {"readable": False, "executable": False, "mode": None}

    mode = script_path.stat().st_mode
    return {
        "readable": bool(mode & stat.S_IRUSR),
        "executable": bool(mode & stat.S_IXUSR),
        "mode": oct(mode)[-3:]
    }
```

## Fix Permissions

```bash
# Make script executable
chmod +x .claude/hooks/script-name.sh

# Fix all hook scripts
chmod +x .claude/hooks/*.sh
```

## Hook Specification Validation

```python
def validateHookSpecification(script_id: str, registries_path: str) -> dict:
    """
    Validate hook specification file for a given script.

    Checks for HSC-XXX-*-spec.md file and parses its validation checklist.

    Args:
        script_id: Script ID (e.g., "HSC-001")
        registries_path: Path to registries directory

    Returns:
        {
            "specExists": bool,
            "specPath": str,
            "checklist": {
                "total": int,
                "completed": int,
                "rate": float
            },
            "testCases": {
                "total": int,
                "passed": int,
                "rate": float
            },
            "status": "PASS" | "WARN" | "FAIL",
            "message": str
        }
    """
    import os
    import re
    from pathlib import Path

    result = {
        "specExists": False,
        "specPath": "",
        "checklist": {"total": 0, "completed": 0, "rate": 0.0},
        "testCases": {"total": 0, "passed": 0, "rate": 0.0},
        "status": "FAIL",
        "message": ""
    }

    # Find specification file matching the script ID
    spec_pattern = f"{script_id}-*-spec.md"
    registries_dir = Path(registries_path)

    spec_files = list(registries_dir.glob(spec_pattern))
    if not spec_files:
        result["status"] = "WARN"
        result["message"] = f"No specification file found for {script_id}"
        return result

    spec_file = spec_files[0]
    result["specExists"] = True
    result["specPath"] = str(spec_file)

    # Read and parse specification
    try:
        with open(spec_file) as f:
            content = f.read()

        # Parse checklist items (- [x] or - [ ])
        checklist_items = re.findall(r'- \[([ xX])\]', content)
        result["checklist"]["total"] = len(checklist_items)
        result["checklist"]["completed"] = sum(1 for item in checklist_items if item.lower() == 'x')
        if result["checklist"]["total"] > 0:
            result["checklist"]["rate"] = (result["checklist"]["completed"] / result["checklist"]["total"]) * 100

        # Parse test cases (### TC-XXX: ... Status: [x])
        tc_pattern = r'### (TC-\d+):.*?Status: \[([ xX])\]'
        tc_matches = re.findall(tc_pattern, content, re.DOTALL)
        result["testCases"]["total"] = len(tc_matches)
        result["testCases"]["passed"] = sum(1 for _, status in tc_matches if status.lower() == 'x')
        if result["testCases"]["total"] > 0:
            result["testCases"]["rate"] = (result["testCases"]["passed"] / result["testCases"]["total"]) * 100

        # Determine status based on rates
        checklist_rate = result["checklist"]["rate"]
        test_rate = result["testCases"]["rate"]

        if checklist_rate >= 100 and test_rate >= 100:
            result["status"] = "PASS"
            result["message"] = f"Fully verified (checklist: 100%, tests: 100%)"
        elif checklist_rate >= 80 and test_rate >= 80:
            result["status"] = "PASS"
            result["message"] = f"Verified (checklist: {checklist_rate:.0f}%, tests: {test_rate:.0f}%)"
        elif checklist_rate >= 60:
            result["status"] = "WARN"
            result["message"] = f"Partial verification (checklist: {checklist_rate:.0f}%, tests: {test_rate:.0f}%)"
        else:
            result["status"] = "FAIL"
            result["message"] = f"Insufficient verification (checklist: {checklist_rate:.0f}%)"

    except Exception as e:
        result["status"] = "WARN"
        result["message"] = f"Error parsing specification: {str(e)}"

    return result


def calculateOverallSpecificationRate(spec_results: list) -> dict:
    """
    Calculate overall specification completion rate across all hooks.

    Args:
        spec_results: List of validateHookSpecification() results

    Returns:
        {
            "totalSpecs": int,
            "existingSpecs": int,
            "averageChecklistRate": float,
            "averageTestRate": float,
            "overallStatus": "PASS" | "WARN" | "FAIL"
        }
    """
    result = {
        "totalSpecs": len(spec_results),
        "existingSpecs": sum(1 for r in spec_results if r["specExists"]),
        "averageChecklistRate": 0.0,
        "averageTestRate": 0.0,
        "overallStatus": "FAIL"
    }

    if result["existingSpecs"] == 0:
        result["overallStatus"] = "WARN"
        return result

    # Calculate averages only from existing specs
    existing = [r for r in spec_results if r["specExists"]]
    result["averageChecklistRate"] = sum(r["checklist"]["rate"] for r in existing) / len(existing)
    result["averageTestRate"] = sum(r["testCases"]["rate"] for r in existing) / len(existing)

    # Determine overall status
    spec_coverage = (result["existingSpecs"] / result["totalSpecs"]) * 100
    if spec_coverage >= 80 and result["averageChecklistRate"] >= 80:
        result["overallStatus"] = "PASS"
    elif spec_coverage >= 50 and result["averageChecklistRate"] >= 60:
        result["overallStatus"] = "WARN"
    else:
        result["overallStatus"] = "FAIL"

    return result
```

## Orphan Detection

```python
def detectOrphanScripts(registry_scripts: list, config_results: list) -> list:
    """
    Find scripts that exist but are not configured.
    """
    orphans = []
    configured_scripts = set()

    for config in config_results:
        if config["status"] == "PASS":
            configured_scripts.add(config["scriptPath"])

    for script in registry_scripts:
        if script["path"] not in configured_scripts and len(script.get("usedBy", [])) == 0:
            orphans.append(script)

    return orphans
```

## Config Files Validation

Hook config files (.cjs) are validated separately from executable scripts.

```python
def validateConfigFiles(registry_path: str, context: ValidationContext) -> list:
    """
    Validate hook config files (.cjs) from registry.

    These are Node.js configuration files used by quality-check.sh.
    They are NOT executable - just need to exist.
    connectionType: "indirect" - settings.json에서 직접 참조되지 않고 스크립트를 통해 간접 연결
    """
    import yaml
    from pathlib import Path

    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []

    for config_file in registry.get("config_files", []):
        file_path = Path(context.projectRoot) / config_file["path"]
        exists = file_path.exists() and file_path.is_file()

        if exists:
            status = "PASS"
            message = None
        else:
            if config_file["priority"] == "CRITICAL":
                status = "FAIL"
                message = f"필수 설정 파일 누락: {config_file['name']}"
            elif config_file["priority"] == "HIGH":
                status = "WARN"
                message = f"권장 설정 파일 누락: {config_file['name']}"
            else:
                status = "SKIP"
                message = f"선택적 설정 파일 누락: {config_file['name']}"

        results.append({
            "id": config_file["id"],
            "name": config_file["name"],
            "path": config_file["path"],
            "status": status,
            "priority": config_file["priority"],
            "exists": exists,
            "usedBy": config_file.get("usedBy", []),
            "connectionType": config_file.get("connectionType", "direct"),
            "dependencyChain": config_file.get("dependencyChain", ""),
            "message": message
        })

    return results
```

### Config Files Output

```
┌─────────────────────────────────────────────────────────────────┐
│ [5b/6] Hook 설정 파일 (간접 연결)                                  │
├──────────────────┬─────────┬────────────┬──────────────────────┤
│ 설정 파일         │ 상태    │ 연결 유형   │ 의존성 체인           │
├──────────────────┼─────────┼────────────┼──────────────────────┤
│ eslint.cjs       │ ✅ 통과 │ 간접       │ HCF-003 → HSC-003    │
│ prettier.cjs     │ ✅ 통과 │ 간접       │ HCF-003 → HSC-003    │
│ typecheck.cjs    │ ✅ 통과 │ 간접       │ HCF-003 → HSC-003    │
│ parallel-check.cjs│ ✅ 통과│ 간접       │ HCF-003 → HSC-003    │
├──────────────────┴─────────┴────────────┴──────────────────────┤
│ 통과율: 100% (4/4)                         상태: ✅ 통과        │
└─────────────────────────────────────────────────────────────────┘

📌 간접 연결 설명:
   settings.json (PostToolUse) → quality-check.sh → 위 설정 파일들
   이 파일들은 settings.json에서 직접 참조되지 않지만,
   quality-check.sh (HSC-003)를 통해 Hook 시스템에 포함됩니다.
```

## References

- Registry: [../registries/hooks.yaml](../registries/hooks.yaml)
- Remediation: [../remediators/hooks-scripts-remediation.md](../remediators/hooks-scripts-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
