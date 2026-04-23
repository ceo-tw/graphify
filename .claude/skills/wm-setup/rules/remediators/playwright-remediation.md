---
title: Playwright Remediation
impact: HIGH
impactDescription: Installs missing Playwright browsers for E2E tests
tags: [remediation, playwright, e2e]
used_by: [validation-orchestrator]
validator: validators/playwright-validator.md
order: 9
canAutoFix: partial
---

# Playwright Remediation

**Impact: HIGH** - Installs missing Playwright browsers

## Overview

This remediator installs Playwright browsers detected as missing by playwright-validator.
Installation runs inside `src/admin-portal` where the playwright package lives.

3 modes:
- NEW_SETUP: installs all FAIL browsers automatically
- UPDATE: asks per browser via AskUserQuestion
- VERIFY: reports only, no installation

## Input

```
validation_result: output from playwright-validator
context: ValidationContext
mode: "NEW_SETUP" | "UPDATE" | "VERIFY"
```

## Output

```json
{
  "module": "playwright",
  "mode": "NEW_SETUP|UPDATE|VERIFY",
  "status": "SUCCESS|PARTIAL|FAILURE",
  "actionsExecuted": [
    {
      "id": "install-PW-001",
      "type": "install",
      "target": "chromium",
      "description": "Installed Playwright browser: chromium",
      "status": "DONE"
    }
  ],
  "actionsRequired": [],
  "summary": {"automaticActions": 1, "manualActions": 0, "skipped": 0}
}
```

## Prerequisite Check

```python
def _check_portal_and_playwright(context: ValidationContext) -> tuple[bool, bool, str]:
    """
    Returns (portal_exists, playwright_installed, detail).
    playwright_installed is checked via `npx playwright --version`.
    """
    import subprocess
    from pathlib import Path

    portal_dir = Path(context.projectRoot) / "src" / "admin-portal"
    if not portal_dir.exists():
        return False, False, "src/admin-portal not found"

    pw_check = subprocess.run(
        ["npx", "playwright", "--version"],
        capture_output=True, text=True,
        cwd=str(portal_dir)
    )
    return True, pw_check.returncode == 0, str(portal_dir)
```

If `src/admin-portal` does not exist → all items SKIP.
If playwright package not installed → manual action: run `npm install` first.

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "NEW_SETUP"
) -> RemediationResult:
    """
    Install missing Playwright browsers.

    NEW_SETUP: auto-install all FAIL browsers
    UPDATE: ask per browser
    VERIFY: report only
    """
    import subprocess
    from pathlib import Path

    portal_exists, playwright_installed, portal_path = _check_portal_and_playwright(context)
    actions_executed = []
    actions_required = []
    skipped_count = 0

    if not portal_exists:
        return {
            "module": "playwright",
            "mode": mode,
            "status": "FAILURE",
            "actionsExecuted": [],
            "actionsRequired": [{
                "id": "prereq-portal",
                "priority": "MEDIUM",
                "description": "src/admin-portal not found — Playwright installation skipped",
                "command": "",
                "detail": "Playwright is only required when E2E tests are run"
            }],
            "summary": {"automaticActions": 0, "manualActions": 1, "skipped": 0}
        }

    if not playwright_installed:
        # Playwright package itself is missing — npm install is needed
        # Direct npm install without user approval would be intrusive; require user action
        actions_required.append({
            "id": "prereq-npm-install",
            "priority": "HIGH",
            "description": "Playwright package is not installed. Run npm install in src/admin-portal first.",
            "command": "cd src/admin-portal && npm install",
            "detail": (
                "After npm install completes, re-run /wm-setup to install browsers. "
                "Or run: cd src/admin-portal && npx playwright install"
            )
        })
        return _build_result(mode, actions_executed, actions_required, skipped_count)

    failed_items = [
        d for d in validation_result["details"]
        if d["status"] == "FAIL"
    ]

    if mode == "VERIFY":
        for item in failed_items:
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "MEDIUM",
                "description": f"Install Playwright browser: {item['name']}",
                "command": item.get("install_hint", f"cd src/admin-portal && npx playwright install {item['name']}"),
                "detail": ""
            })
        return _build_result(mode, actions_executed, actions_required, skipped_count)

    for item in failed_items:
        browser = item["name"]
        install_cmd = item.get("install_hint", f"cd src/admin-portal && npx playwright install {browser}")

        if mode == "UPDATE":
            user_approved = AskUserQuestion(
                question=f"Install Playwright browser: {browser}?",
                options=["yes", "no", "skip"]
            )
            if user_approved != "yes":
                skipped_count += 1
                continue

        result = subprocess.run(
            install_cmd, shell=True, capture_output=True, text=True,
            cwd=context.projectRoot
        )

        if result.returncode == 0:
            actions_executed.append({
                "id": f"install-{item['id']}",
                "type": "install",
                "target": browser,
                "description": f"Installed Playwright browser: {browser}",
                "status": "DONE"
            })
        else:
            stderr_tail = "\n".join(result.stderr.splitlines()[-20:])
            actions_executed.append({
                "id": f"install-{item['id']}",
                "type": "install",
                "target": browser,
                "description": f"Failed to install browser: {browser}",
                "status": "FAILED",
                "error": result.stderr[:500]
            })
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "MEDIUM",
                "description": f"Manual Playwright browser installation required: {browser}",
                "command": install_cmd,
                "detail": stderr_tail
            })

    return _build_result(mode, actions_executed, actions_required, skipped_count)
```

## Helper Functions

```python
def _build_result(mode: str, actions_executed: list, actions_required: list, skipped: int) -> dict:
    done = sum(1 for a in actions_executed if a.get("status") == "DONE")
    failed = sum(1 for a in actions_executed if a.get("status") == "FAILED")
    manual = len(actions_required)

    if failed == 0 and manual == 0:
        status = "SUCCESS"
    elif done > 0 and (failed > 0 or manual > 0):
        status = "PARTIAL"
    else:
        status = "FAILURE"

    return {
        "module": "playwright",
        "mode": mode,
        "status": status,
        "actionsExecuted": actions_executed,
        "actionsRequired": actions_required,
        "summary": {
            "automaticActions": done,
            "manualActions": manual,
            "skipped": skipped
        }
    }
```

## npm install Note

When the playwright package itself is absent, the remediator does NOT auto-run
`npm install` without user consent. This is because `npm install` modifies
`node_modules` and `package-lock.json` and may be disruptive in some contexts.
Instead, the remediator reports a manual action with the exact command, and the
user can approve and run it. In UPDATE mode the same behavior applies.

## Mode Behavior Summary

| Mode | auto-install | ask per browser | report only |
|------|-------------|-----------------|-------------|
| NEW_SETUP | yes | no | no |
| UPDATE | no | yes (AskUserQuestion per browser) | no |
| VERIFY | no | no | yes |

## Output Format

```
┌──────────────────────────────────────────────────┐
│ Remediation: Playwright                           │
├──────────────────────┬────────────────────────────┤
│ Automatic Actions    │ Status                     │
├──────────────────────┼────────────────────────────┤
│ Install firefox      │ DONE                       │
│ Install webkit       │ DONE                       │
├──────────────────────┴────────────────────────────┤
│ Manual Actions Required                           │
├───────────────────────────────────────────────────┤
│ (none)                                            │
└───────────────────────────────────────────────────┘
```

## References

- Validator: [../validators/playwright-validator.md](../validators/playwright-validator.md)
- Registry: [../registries/playwright.yaml](../registries/playwright.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
