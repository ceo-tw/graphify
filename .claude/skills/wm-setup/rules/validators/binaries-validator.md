---
title: Binaries Validator
impact: CRITICAL
impactDescription: Validates required CLI binaries and runtimes
tags: [validator, binaries, graphify, runtime]
used_by: [validation-orchestrator]
registry: registries/binaries.yaml
order: 7
blocking: true
---

# Binaries Validator

**Impact: CRITICAL** - Validates required CLI binaries and runtimes against registry

## Overview

This validator checks all CLI binaries and runtimes defined in `binaries.yaml`.
Blocking: CRITICAL binary failures halt the pipeline because wm workflow is non-functional
without graphify, jq, python3.12, node, and npm.

## Input

```
registry_path: path to registries/binaries.yaml
context: ValidationContext (projectRoot, mode, verbose)
```

## Output

```json
{
  "module": "binaries",
  "items": [
    {
      "id": "BIN-001",
      "name": "graphify",
      "status": "PASS|FAIL|WARN|SKIP",
      "detail": "graphify 0.5.4 installed, all required features present",
      "install_hint": "python3.12 -m venv .claude/graphify/.venv && .claude/graphify/.venv/bin/pip install 'git+https://github.com/ceo-tw/graphify.git@v4'"
    }
  ],
  "counts": {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
}
```

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate binaries from registry.

    Order: 7 (after existing validators)
    Blocking: True — CRITICAL binary failures stop pipeline
    """
    import subprocess
    import re
    import os
    from pathlib import Path

    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []
    project_root = Path(context.projectRoot)

    for item in registry["items"]:
        bin_name = item["name"]
        has_path = "path" in item  # explicit install path (e.g., graphify venv)

        # Step 1: existence check
        if has_path:
            # kind: binary with path — check test -x <path>
            bin_path = project_root / item["path"]
            exists = bin_path.exists() and os.access(bin_path, os.X_OK)
        else:
            # kind: binary without path — check command -v <name>
            result = subprocess.run(
                ["command", "-v", bin_name],
                shell=True,
                capture_output=True, text=True
            )
            exists = result.returncode == 0

        if not exists:
            status = "FAIL"
            detail = f"{bin_name} not found"
            install_hint = _get_install_hint(item)
            results.append(_make_item(item, status, detail, install_hint))
            continue

        # Step 2: version_regex check (if present)
        if "verify_command" in item:
            verify_cmd = item["verify_command"]
            if has_path:
                # Replace relative path prefix with absolute
                verify_cmd = verify_cmd.replace(
                    item["path"],
                    str(project_root / item["path"])
                )
            verify_result = subprocess.run(
                verify_cmd, shell=True, capture_output=True, text=True
            )
            verify_output = (verify_result.stdout + verify_result.stderr).strip()

            if "version_regex" in item:
                pattern = item["version_regex"]
                if not re.search(pattern, verify_output, re.MULTILINE):
                    status = "FAIL"
                    detail = f"{bin_name} version mismatch. Got: '{verify_output}'. Expected regex: '{pattern}'"
                    install_hint = _get_install_hint(item)
                    results.append(_make_item(item, status, detail, install_hint))
                    continue
            elif verify_result.returncode != 0:
                status = "FAIL"
                detail = f"{bin_name} verify_command failed: {verify_output}"
                install_hint = _get_install_hint(item)
                results.append(_make_item(item, status, detail, install_hint))
                continue

        # Step 3: required_features check (graphify --help)
        # HARD tier (required_features): missing → FAIL
        # SOFT tier (required_features_soft, R4.2 v0.5.6+): missing → WARN (1-release compat window)
        # See "Special Cases: graphify query / path / explain feature check (R4.2, soft-warn)" below.
        if "required_features" in item or "required_features_soft" in item:
            if has_path:
                bin_exec = str(project_root / item["path"])
            else:
                bin_exec = bin_name
            help_result = subprocess.run(
                [bin_exec, "--help"],
                capture_output=True, text=True
            )
            help_output = help_result.stdout + help_result.stderr

            missing_features = [
                f for f in item.get("required_features", [])
                if f not in help_output
            ]
            if missing_features:
                status = "FAIL"
                detail = f"{bin_name} missing required features: {missing_features}"
                install_hint = _get_install_hint(item)
                results.append(_make_item(item, status, detail, install_hint))
                continue

            # Soft tier (R4.2, 1-release compatibility window): WARN instead of FAIL.
            # Does not `continue` — rest of validation still runs for this item.
            missing_soft = [
                f for f in item.get("required_features_soft", [])
                if f not in help_output
            ]
            if missing_soft:
                soft_status = "WARN"
                soft_detail = (
                    f"{bin_name} missing soft features: {missing_soft} — "
                    f"wm A-1 Tier 2/3 (NL query / two-node path) unavailable; "
                    f"falls back to Explore. Upgrade ceo-tw/graphify to ≥ v0.5.6."
                )
                results.append(_make_item(item, soft_status, soft_detail, _get_install_hint(item)))
                # NOTE: do NOT `continue` — pypi_forbidden and other checks should still run.

        # Step 4: pypi_forbidden check
        if item.get("pypi_forbidden"):
            pip_check = subprocess.run(
                ["pip", "show", bin_name],
                capture_output=True, text=True
            )
            if pip_check.returncode == 0:
                # Installed via pip — check if it came from PyPI (no Location pointing to git)
                pip_output = pip_check.stdout
                if "git+" not in pip_output and "editable" not in pip_output.lower():
                    # Likely PyPI origin — FAIL
                    status = "FAIL"
                    detail = (
                        f"{bin_name} appears to be installed from PyPI (pip show returned results). "
                        "Must be installed from fork: git+https://github.com/ceo-tw/graphify.git@v4"
                    )
                    install_hint = _get_install_hint(item)
                    results.append(_make_item(item, status, detail, install_hint))
                    continue

        # All checks passed
        status = "PASS"
        detail = f"{bin_name} installed and verified"
        results.append(_make_item(item, "PASS", detail, None))

    # Aggregate counts
    counts = _count_statuses(results)

    # Determine overall status
    critical_failed = any(
        r["status"] == "FAIL" and r.get("priority") == "CRITICAL"
        for r in results
    )
    high_failed = any(
        r["status"] == "FAIL" and r.get("priority") == "HIGH"
        for r in results
    )

    if critical_failed:
        overall = "FAIL"
    elif high_failed:
        overall = "WARN"
    else:
        overall = "PASS"

    passed = counts["pass"]
    total = len(results)

    return {
        "moduleId": "binaries",
        "moduleName": "Binaries",
        "status": overall,
        "passRate": (passed / total) * 100 if total else 0,
        "items": {
            "total": total,
            "passed": counts["pass"],
            "failed": counts["fail"],
            "warnings": counts["warn"]
        },
        "details": results,
        "blocking": True,
        "timestamp": datetime.now().isoformat(),
        "counts": counts
    }
```

## Helper Functions

```python
def _get_install_hint(item: dict) -> str:
    """Return OS-appropriate install hint based on $OSTYPE."""
    import os
    ostype = os.environ.get("OSTYPE", "")

    if "darwin" in ostype or "macos" in ostype.lower():
        # macOS
        hint = item.get("install_command_macos") or item.get("install_command", "")
    elif "linux" in ostype:
        hint = item.get("install_command_linux") or item.get("install_command", "")
    else:
        hint = item.get("install_command", "# See documentation for installation")

    return hint


def _make_item(item: dict, status: str, detail: str, install_hint: str) -> dict:
    return {
        "id": item["id"],
        "name": item["name"],
        "status": status,
        "detail": detail,
        "install_hint": install_hint or "",
        "priority": item.get("priority", "MEDIUM"),
        "hard": item.get("hard", False)
    }


def _count_statuses(results: list) -> dict:
    return {
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "warn": sum(1 for r in results if r["status"] == "WARN"),
        "skip": sum(1 for r in results if r["status"] == "SKIP")
    }
```

## Status Mapping

| Condition | Status | Effect |
|-----------|--------|--------|
| CRITICAL binary missing | FAIL | Pipeline blocked |
| HIGH binary missing | FAIL + WARN aggregate | Reported; pipeline warns |
| MEDIUM binary missing | FAIL | Reported in separate summary |
| version_regex mismatch | FAIL | Detail includes actual vs expected |
| required_features missing | FAIL | Detail lists missing features |
| pypi_forbidden origin | FAIL | Must reinstall from fork |
| All checks pass | PASS | |

Note: `hard: false` items (MEDIUM priority, e.g., `gh`) still report FAIL when missing,
but are tallied separately in the summary so they do not trigger the CRITICAL block path.

## Output Format

```
┌─────────────────────────────────────────────────┐
│ [7/10] Binaries                                  │
├──────────────────────┬─────────┬─────────────────┤
│ Binary               │ Status  │ Priority        │
├──────────────────────┼─────────┼─────────────────┤
│ graphify             │ ✅ PASS │ CRITICAL        │
│ jq                   │ ✅ PASS │ CRITICAL        │
│ python3.12           │ ✅ PASS │ CRITICAL        │
│ node                 │ ✅ PASS │ CRITICAL        │
│ npm                  │ ✅ PASS │ CRITICAL        │
│ kubectl              │ ✅ PASS │ HIGH            │
│ docker               │ ❌ FAIL │ HIGH            │
│ gh                   │ ⚠️ WARN │ MEDIUM          │
├──────────────────────┴─────────┴─────────────────┤
│ Pass Rate: 75% (6/8)          Status: ❌ FAIL    │
└─────────────────────────────────────────────────┘
```

## Special Cases

### BIN-009: bash 4+ Version Check

BIN-009 carries `validation_order: 0` in the registry, meaning it must be validated BEFORE
all other BIN-* entries (including BIN-001 graphify) despite its numeric ID being 009.
Rationale: validator scripts themselves may invoke bash; a bash 3.2 environment would silently
corrupt any `declare -A` usage in downstream validation logic.

**Validation procedure:**

1. Check `/bin/bash --version` to get the macOS system bash version.
2. Check `bash -c 'echo ${BASH_VERSINFO[0]}'` to get the PATH bash major version.
3. Decision matrix:
   - PATH bash major >= 4: PASS
   - PATH bash < 4 AND /bin/bash < 4: FAIL — use `install_hint` from remediation
   - PATH bash >= 4 BUT /bin/bash is 3.x: WARN with message:
     "PATH bash is new enough but /bin/bash is still 3.2 — scripts using `#!/bin/bash` shebang may fail. Ensure homebrew bash path precedes /bin in $PATH."

**Implementation note:** `version_regex: "^([4-9]|[1-9][0-9])$"` matches the single-line
output of `bash -c 'echo ${BASH_VERSINFO[0]}'` (major version integer only).

### graphify PyPI Safety

The `pypi_forbidden: true` flag on BIN-001 ensures we detect and reject installations
sourced from PyPI (`pip install graphifyy`). The PyPI package is the upstream fork and
lacks URL-centric features (`resolve`, `callers`, `callees`, `blast`) required by wm.

Detection strategy: after `test -x <path>` passes, check `pip show graphify` output;
if it lacks `Location:` pointing to a git-based install, flag as FAIL.

### OS-specific install hints

`install_command_macos` / `install_command_linux` fields in the registry are used to
provide accurate install hints per platform. Detection uses `$OSTYPE` environment variable:
- `darwin*` → macOS (brew)
- `linux*` → Linux (apt-get)
- Other → generic `install_command` fallback

### graphify query / path / explain feature check (R4.2, soft-warn)

Introduced in v0.5.5/v0.5.6. These three subcommands back the `knowledge-graph-navigator`
Tier 2 and Tier 3 paths of the wm A-1 fallback (wm/SKILL.md §1).

Detection is the existing `required_features` substring match on `graphify --help` output,
but gated under a new **`required_features_soft`** field in the registry:

```bash
# Contract (existing logic, extended to soft tier):
.claude/graphify/.venv/bin/graphify --help | grep -qE '^\s*(query|path|explain)\s'
```

If any of `{query, path, explain}` is missing:

- Status: **WARN** (not FAIL) — wm navigator Tier 2/3 degrades to Tier 4 (Explore agent)
  for NL/concept questions, but core structural lookups (`resolve`/`callers`/`callees`/
  `blast`) continue working via Tier 1.
- Log: `"graphify <name> subcommand missing — A-1 Tier 2/3 unavailable; wm falls
  back to Explore for NL/concept questions. Upgrade ceo-tw/graphify to ≥ v0.5.6."`
- install_hint: same as BIN-001 (reinstall from ceo-tw fork v4 branch).

**Rollout window**: 1-release compatibility period. In a follow-up release, promote
these three from `required_features_soft` → `required_features` (WARN → HARD FAIL).
This prevents `/wm-setup VERIFY` from tripping HARD FAIL on every v0.5.4/v0.5.5
install on the day v0.5.6 ships.

Validator pseudocode addition:

```python
for feature in item.get("required_features", []):
    if feature not in help_output:
        emit_fail(item.id, f"missing required feature: {feature}")
for feature in item.get("required_features_soft", []):
    if feature not in help_output:
        emit_warn(item.id, f"missing soft feature: {feature} — Tier 2/3 unavailable")
```

## References

- Registry: [../registries/binaries.yaml](../registries/binaries.yaml)
- Remediation: [../remediators/binaries-remediation.md](../remediators/binaries-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
