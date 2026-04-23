---
title: VERIFY Mode Process
impact: MEDIUM
impactDescription: Verification-only workflow
tags: [process]
used_by: [wm-setup]
---

# VERIFY Mode Process

**Impact: MEDIUM** - Workflow for verifying existing Claude Code setup

## Overview

VERIFY mode is activated when `.claude/` directory exists and completeness == 100%,
or when the user explicitly requests a read-only health check.

This mode runs all 12 modules (including Module 11 runtime-checks) with **validators
only**. Remediators are never invoked. The final report states "wm is ready" or lists
specific FAIL items.

## Detection Criteria

```python
def isVerifyMode(project_state: dict) -> bool:
    """Check if project only needs verification."""
    return (
        project_state.get("has_claude_dir", False) and
        project_state.get("completeness_percentage", 0) >= 100
    ) or project_state.get("user_explicit_verify", False)
```

## Workflow Steps

```
VERIFY Mode
    |
    v
Step 0: Context Gate Check (MANDATORY)
    |
    v
Step 1: Unified Analysis (read-only)
    - Detect all components
    - No changes made
    |
    v
Step 1.5: Shell Environment Check
    |
    v
Step 4: Validation - Full 12-module pipeline (VERIFY behavior)
    Module  1: folder          (blocking - validator only)
    Module  2: skills          (validator only)
    Module  3: agents          (validator only)
    Module  4: hooks-config    (validator only)
    Module  5: hooks-scripts   (validator only)
    Module  6: settings        (validator only)
    Module  7: binaries        (validator only; BIN-001 graphify check)
    Module  8: env-vars        (validator only)
    Module  9: graph-data      (validator only; skipped if BIN-001 FAIL)
    Module 10: playwright      (validator only)
    Module 11: runtime-checks  (validator only; VERIFY mode only)
    Module 12: domains         (validator only)
    - NO remediation in any module
    - remediator = None for all modules
    |
    v
Step 4.5: Post-VERIFY Checklist (NEW)
    - Load runtime-validator.md
    - Execute 6 runtime check categories
    - Generate user checklist
    - See: post-verify-workflow.md
    |
    v
Step 4.6: Mismatch Resolution reporting (read-only)
    |
    v
Step 5: Report Generation
    - Detailed verification report
    - Health score
    - Post-VERIFY checklist guide
    - Final message: "wm is ready" OR list of FAIL items
```

## Skipped Steps

- **Step 2** (MCP Management): No configuration changes
- **Step 3** (Checklist Generation): Already complete, only verify
- **All remediators**: Never invoked in VERIFY mode

## Module 11 (runtime-checks) - VERIFY Only

Module 11 is the only module that runs **exclusively in VERIFY mode**. It does not
run in NEW_SETUP or UPDATE. It provides advisory health information about runtime
state (process liveness, connection checks, etc.).

```python
# Module 11 mode_scope
"modeScope": ["VERIFY"]    # VERIFY mode only
```

## Verification Checks

```python
def runVerification(context_data: dict, project_state: dict) -> dict:
    """
    Run comprehensive 12-module verification (read-only).
    Remediators not invoked.
    """
    results = runValidationPipeline(context_data, mode="VERIFY")

    # Calculate overall health score
    total = results["modules"]["total"]
    passed = results["modules"]["passed"]
    health_score = (passed / total * 100) if total > 0 else 0

    wm_ready = (
        results["modules"]["failed"] == 0
        and results["modules"]["warned"] == 0
    )

    return {
        "results": results,
        "health_score": round(health_score, 1),
        "status": "wm is ready" if wm_ready else "ISSUES_FOUND",
        "wm_ready": wm_ready
    }
```

## Final Report Format

```python
def generateVerifyReport(results: dict) -> str:
    """
    Generate final VERIFY report.

    If all 12 modules pass:
        "wm is ready"

    If any module fails, list specific FAIL items:
        "Issues found in: binaries (BIN-001 graphify), graph-data (3 domains missing)"
    """
    if results["wm_ready"]:
        return "wm is ready"

    fail_details = []
    for module_result in results["results"]["results"]:
        if module_result["status"] in ["FAIL", "WARN"]:
            module_id = module_result.get("moduleId", "unknown")
            issues = module_result.get("issues", [])
            if issues:
                fail_details.append(f"{module_id} ({', '.join(str(i) for i in issues[:3])})")
            else:
                fail_details.append(module_id)

    return f"Issues found in: {', '.join(fail_details)}"
```

## Report Template

```markdown
## Verification Report

**Project**: {project_name}
**Date**: {date}
**Health Score**: {score}%
**Mode**: VERIFY (read-only, no changes made)

### Module Status (12 modules)

| # | Module | Status | Notes |
|---|--------|--------|-------|
| 1 | Folder Structure | PASS | |
| 2 | Skills | PASS | |
| 3 | Agents | PASS | |
| 4 | Hooks Configuration | PASS | |
| 5 | Hook Scripts | PASS | |
| 6 | Settings & Environment | PASS | |
| 7 | Binary Dependencies | PASS | graphify v0.5.x |
| 8 | Environment Variables | PASS | |
| 9 | Graph Data | PASS | 18 domains + _global |
| 10 | Playwright Browsers | PASS | chromium/firefox/webkit |
| 11 | Runtime Health | PASS | (VERIFY only) |
| 12 | Domain Structure | PASS | |

### Final Status

wm is ready
```

## MCP Connectivity Test

```python
def verifyMCPConnectivity(context_data: dict) -> dict:
    """Test MCP server connectivity (read-only)."""
    servers = context_data.get("mcp_servers", [])

    connectivity = {
        "serena": "serena" in servers,
        "memory": "memory" in servers,
        "playwright": "playwright" in servers
    }

    required_ok = connectivity["serena"]
    score = (sum(connectivity.values()) / len(connectivity)) * 100

    return {
        "connectivity": connectivity,
        "required_ok": required_ok,
        "score": score
    }
```

## Expected Outputs

- Verification report (no changes made)
- Health score (0-100%)
- "wm is ready" OR specific FAIL items listed
- Post-VERIFY checklist (runtime-validator output)

## When to Apply

- When `has_claude_dir` is True AND `completeness_percentage` >= 100
- When user explicitly requests read-only health check
- For periodic health checks without modification

## Module 7-10 Notes (wm-specific, read-only)

| Module | ID | VERIFY check |
|--------|----|--------------|
| 7 | binaries | `command -v graphify`, version check `graphify --version \| grep -E '^0\.5\.'` |
| 8 | env-vars | `printenv CLAUDE_PROJECT_DIR CLAUDE_SKILL_DIR` |
| 9 | graph-data | `jq -e '.nodes\|length>0'` on each of 19 graph JSON files |
| 10 | playwright | `npx playwright install --dry-run` output parsing |
| 11 | runtime-checks | runtime-validator.md 6-category health check (VERIFY only) |

## References

- [new-setup.md](./new-setup.md) - NEW_SETUP mode
- [update.md](./update.md) - UPDATE mode
- [../orchestration/validation-orchestrator.md](../orchestration/validation-orchestrator.md) - 12-module pipeline definition
- [../onboarding/runtime-validator.md](../onboarding/runtime-validator.md) - Module 11 runtime checks
- [../onboarding/post-verify-workflow.md](../onboarding/post-verify-workflow.md) - Post-VERIFY checklist
