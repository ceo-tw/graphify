---
title: Playwright Validator
impact: HIGH
impactDescription: Validates Playwright browser installations for E2E tests
tags: [validator, playwright, e2e]
used_by: [validation-orchestrator]
registry: registries/playwright.yaml
order: 9
blocking: false
---

# Playwright Validator

**Impact: HIGH** - Validates Playwright browser installations against registry

## Overview

This validator checks whether Playwright browsers (chromium, firefox, webkit) are
installed in `src/admin-portal`. Uses `npx playwright install --dry-run <browser>`
to detect installation status without side effects.

Non-blocking: Missing browsers are reported but the main pipeline continues.
E2E tests will fail if browsers are absent, but the project can still be developed.

## Input

```
registry_path: path to registries/playwright.yaml
context: ValidationContext (projectRoot, mode, verbose)
```

## Output

```json
{
  "module": "playwright",
  "items": [
    {
      "id": "PW-001",
      "name": "chromium",
      "status": "PASS|FAIL|WARN|SKIP",
      "detail": "chromium installed",
      "install_hint": "cd src/admin-portal && npx playwright install chromium"
    }
  ],
  "counts": {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
}
```

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate Playwright browser installations.

    Order: 9
    Blocking: False — missing browsers degrade E2E capability but don't block pipeline
    """
    import subprocess
    from pathlib import Path

    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    project_root = Path(context.projectRoot)
    portal_dir = project_root / "src" / "admin-portal"

    # Step 1: admin-portal directory must exist
    if not portal_dir.exists():
        results = []
        for item in registry["items"]:
            results.append({
                "id": item["id"],
                "name": item["name"],
                "status": "SKIP",
                "detail": "src/admin-portal not found — skipping Playwright validation",
                "install_hint": "",
                "priority": item.get("priority", "HIGH")
            })
        counts = _count_statuses(results)
        return _build_result(results, counts, "SKIP")

    # Step 2: check if playwright package is installed
    pw_check = subprocess.run(
        ["npx", "playwright", "--version"],
        capture_output=True, text=True,
        cwd=str(portal_dir)
    )
    if pw_check.returncode != 0:
        results = []
        for item in registry["items"]:
            results.append({
                "id": item["id"],
                "name": item["name"],
                "status": "SKIP",
                "detail": "playwright package not installed, run npm install first",
                "install_hint": f"cd src/admin-portal && npm install && npx playwright install {item['name']}",
                "priority": item.get("priority", "HIGH")
            })
        counts = _count_statuses(results)
        return _build_result(results, counts, "SKIP")

    results = []

    for item in registry["items"]:
        browser = item["name"]

        # Step 3: dry-run to detect install status
        dry_run = subprocess.run(
            ["npx", "playwright", "install", "--dry-run", browser],
            capture_output=True, text=True,
            cwd=str(portal_dir)
        )
        dry_run_output = (dry_run.stdout + dry_run.stderr).lower()

        if "would install" in dry_run_output or "needs to be installed" in dry_run_output:
            # Browser not installed
            status = "FAIL"
            detail = f"{browser} is not installed (dry-run reported would-install)"
            install_hint = item.get("install_command", f"cd src/admin-portal && npx playwright install {browser}")
        elif dry_run.returncode != 0:
            # Unexpected error
            status = "FAIL"
            detail = f"{browser} check failed: {dry_run_output[:200]}"
            install_hint = item.get("install_command", f"cd src/admin-portal && npx playwright install {browser}")
        else:
            # No "would install" in output → browser already installed
            status = "PASS"
            detail = f"{browser} installed"
            install_hint = None

        results.append({
            "id": item["id"],
            "name": item["name"],
            "status": status,
            "detail": detail,
            "install_hint": install_hint or "",
            "priority": item.get("priority", "HIGH")
        })

    counts = _count_statuses(results)

    # Non-blocking: FAIL items produce WARN at module level (soft dependency)
    any_failed = counts["fail"] > 0
    overall = "WARN" if any_failed else "PASS"

    return _build_result(results, counts, overall)
```

## Helper Functions

```python
def _count_statuses(results: list) -> dict:
    return {
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "warn": sum(1 for r in results if r["status"] == "WARN"),
        "skip": sum(1 for r in results if r["status"] == "SKIP")
    }


def _build_result(results: list, counts: dict, overall: str) -> dict:
    passed = counts["pass"]
    total = len(results)
    return {
        "moduleId": "playwright",
        "moduleName": "Playwright",
        "status": overall,
        "passRate": (passed / total) * 100 if total else 0,
        "items": {
            "total": total,
            "passed": counts["pass"],
            "failed": counts["fail"],
            "warnings": counts["warn"]
        },
        "details": results,
        "blocking": False,
        "timestamp": datetime.now().isoformat(),
        "counts": counts
    }
```

## Status Mapping

| Condition | Item Status | Module Status |
|-----------|-------------|---------------|
| src/admin-portal not found | SKIP (all) | SKIP |
| playwright package missing | SKIP (all) | SKIP |
| dry-run: "would install" | FAIL | WARN |
| dry-run: unexpected error | FAIL | WARN |
| dry-run: no "would install" | PASS | PASS |

Module is non-blocking — FAIL items produce WARN at module level, not FAIL.
This prevents pipeline halt for E2E-only tooling.

## dry-run Detection Detail

`npx playwright install --dry-run <browser>` outputs something like:

```
# Installed:
# Browser: chromium version 127.0.0.0 - PASS (already installed)
# OR
# Would install browser: chromium version 127.0.0.0
```

The validator searches for `"would install"` or `"needs to be installed"` (case-insensitive)
in the combined stdout+stderr. Absence of these strings with exit code 0 indicates
the browser is already installed.

## Output Format

```
┌─────────────────────────────────────────────┐
│ [9/10] Playwright                           │
├──────────────────────┬─────────┬────────────┤
│ Browser              │ Status  │ Priority   │
├──────────────────────┼─────────┼────────────┤
│ chromium             │ ✅ PASS │ HIGH       │
│ firefox              │ ❌ FAIL │ HIGH       │
│ webkit               │ ❌ FAIL │ HIGH       │
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 33% (1/3)         Status: ⚠️ WARN│
└─────────────────────────────────────────────┘
```

## References

- Registry: [../registries/playwright.yaml](../registries/playwright.yaml)
- Remediation: [../remediators/playwright-remediation.md](../remediators/playwright-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
