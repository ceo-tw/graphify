---
title: Binaries Remediation
impact: CRITICAL
impactDescription: Installs missing CLI binaries and runtimes
tags: [remediation, binaries, graphify]
used_by: [validation-orchestrator]
validator: validators/binaries-validator.md
order: 7
canAutoFix: partial
---

# Binaries Remediation

**Impact: CRITICAL** - Installs or guides installation of missing CLI binaries

## Overview

This remediator handles missing binary issues from binaries-validator.
Supports 3 modes:
- NEW_SETUP: installs all FAIL items automatically without asking
- UPDATE: asks per FAIL item via AskUserQuestion before installing
- VERIFY: reports only, no installation performed

## Safety Guard: graphify PyPI Prohibition

**CRITICAL**: This remediator must NEVER install graphify from PyPI.
The PyPI package (`pip install graphifyy`) is the upstream fork and lacks
URL-centric features (`resolve`, `callers`, `callees`, `blast`) required by wm.
The correct source is: `git+https://github.com/ceo-tw/graphify.git@v4`

```python
GRAPHIFY_PYPI_FORBIDDEN_PATTERNS = [
    "pip install graphifyy",
    "pip install graphify ",   # space after (not the venv install)
    "pypi.org/project/graphify",
]

def _abort_if_pypi_command(cmd: str) -> None:
    """Raise RuntimeError if install_command contains a PyPI graphify pattern."""
    for pattern in GRAPHIFY_PYPI_FORBIDDEN_PATTERNS:
        if pattern in cmd:
            raise RuntimeError(
                f"ABORT: install_command contains forbidden PyPI graphify pattern: '{pattern}'. "
                "graphify must NOT install from PyPI. "
                "Use: git+https://github.com/ceo-tw/graphify.git@v4"
            )
```

## Input

```
validation_result: output from binaries-validator
context: ValidationContext
mode: "NEW_SETUP" | "UPDATE" | "VERIFY"
```

## Output

```json
{
  "module": "binaries",
  "mode": "NEW_SETUP|UPDATE|VERIFY",
  "status": "SUCCESS|PARTIAL|FAILURE",
  "actionsExecuted": [
    {
      "id": "install-BIN-002",
      "type": "install",
      "target": "jq",
      "description": "Installed jq via brew install jq",
      "status": "DONE"
    }
  ],
  "actionsRequired": [
    {
      "id": "manual-BIN-005",
      "priority": "HIGH",
      "description": "Install Docker daemon (requires user action)",
      "command": "brew install --cask docker",
      "detail": ""
    }
  ],
  "summary": {"automaticActions": 1, "manualActions": 1, "skipped": 0}
}
```

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "NEW_SETUP"
) -> RemediationResult:
    """
    Install missing binaries.

    NEW_SETUP: auto-install all FAIL items
    UPDATE: ask per item
    VERIFY: report only (no install)
    """
    import subprocess
    import os
    from pathlib import Path

    actions_executed = []
    actions_required = []
    skipped_count = 0

    failed_items = [
        d for d in validation_result["details"]
        if d["status"] == "FAIL"
    ]

    if mode == "VERIFY":
        # Report only — no installation
        for item in failed_items:
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item.get("priority") in ("CRITICAL", "HIGH") else "MEDIUM",
                "description": f"Install {item['name']}: {item.get('detail', '')}",
                "command": item.get("install_hint", ""),
                "detail": ""
            })
        return _build_result(mode, actions_executed, actions_required, skipped_count)

    for item in failed_items:
        bin_name = item["name"]

        if mode == "UPDATE":
            # Ask user before installing
            user_approved = AskUserQuestion(
                question=f"Install missing binary: {bin_name}?\n{item.get('detail', '')}",
                options=["yes", "no", "skip"]
            )
            if user_approved != "yes":
                skipped_count += 1
                continue

        # Determine install command
        install_cmd = _get_install_command(bin_name, item, context)

        # Safety gate: abort if PyPI graphify command detected
        _abort_if_pypi_command(install_cmd)

        # Execute installation
        result = subprocess.run(
            install_cmd, shell=True, capture_output=True, text=True,
            cwd=context.projectRoot
        )

        if result.returncode == 0:
            # Verify after install
            verify_passed = _verify_after_install(bin_name, item, context)
            if verify_passed:
                actions_executed.append({
                    "id": f"install-{item['id']}",
                    "type": "install",
                    "target": bin_name,
                    "description": f"Installed {bin_name}",
                    "status": "DONE"
                })
            else:
                # Installed but verify failed (e.g., version_regex mismatch)
                actions_executed.append({
                    "id": f"install-{item['id']}",
                    "type": "install",
                    "target": bin_name,
                    "description": f"Installed {bin_name} but verification failed",
                    "status": "FAILED",
                    "error": f"verify_command failed after installation"
                })
                actions_required.append({
                    "id": f"verify-{item['id']}",
                    "priority": "HIGH",
                    "description": f"{bin_name} installed but version check failed. Manual investigation needed.",
                    "command": item.get("install_hint", ""),
                    "detail": ""
                })
        else:
            # Installation failed — capture last 20 lines of stderr
            stderr_tail = "\n".join(result.stderr.splitlines()[-20:])
            actions_executed.append({
                "id": f"install-{item['id']}",
                "type": "install",
                "target": bin_name,
                "description": f"Failed to install {bin_name}",
                "status": "FAILED",
                "error": result.stderr[:500]
            })
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item.get("priority") in ("CRITICAL", "HIGH") else "MEDIUM",
                "description": f"Manual installation required for {bin_name}",
                "command": item.get("install_hint", ""),
                "detail": stderr_tail
            })

    return _build_result(mode, actions_executed, actions_required, skipped_count)
```

## BIN-009: bash 4+ Remediation

**Symptom:** `check.sh` or any wm-setup script exits with `declare -A: command not found` or
`ERROR: check.sh requires bash 4+` (exit code 2).

**macOS (most common case):**
```bash
brew install bash
# Installs to /opt/homebrew/bin/bash (Apple Silicon)
# or /usr/local/bin/bash (Intel)
```

Apple does NOT update `/bin/bash` (remains at 3.2.57 for GPL v2 reasons).
After `brew install bash`, users MUST ensure the homebrew path comes BEFORE `/bin` in `$PATH`:
```bash
# Add to ~/.zprofile or ~/.bash_profile:
export PATH="/opt/homebrew/bin:$PATH"   # Apple Silicon
# export PATH="/usr/local/bin:$PATH"   # Intel
```

For scripts using `#!/bin/bash` shebang: the new bash is NOT picked up automatically.
Change shebangs to `#!/usr/bin/env bash` so `$PATH` resolution applies.

**Verify after install:**
```bash
bash --version | head -1 | grep -E 'version ([4-9]|[1-9][0-9])\.'
# Expected: GNU bash, version 5.x.x (or 4.x.x)
```

**Linux:** Usually pre-installed at version >= 4. If missing:
```bash
sudo apt-get install -y bash
```

**Windows (WSL / Git Bash):** WSL ships bash 5+. Git Bash ships bash 4+. No action needed.

**Auto-fix eligibility:** macOS only — `brew install bash` is safe to auto-execute in NEW_SETUP
mode. PATH update requires manual action (shell profile modification).

## graphify Special Handling

graphify has special handling due to its venv-based install and editable fallback:

```python
def _get_install_command(bin_name: str, item: dict, context: ValidationContext) -> str:
    """
    Return OS-appropriate install command.
    graphify: uses fork git+https install by default.
    UPDATE mode: if local clone exists, offer editable install.
    """
    import os
    ostype = os.environ.get("OSTYPE", "")
    project_root = context.projectRoot

    if bin_name == "graphify":
        # Check if a local clone exists (user-specified or ~/graphify default)
        local_clone_paths = [
            os.path.expanduser("~/graphify"),
            os.path.join(project_root, ".graphify-dev"),
        ]
        local_clone = next((p for p in local_clone_paths if os.path.isdir(p)), None)

        if local_clone and context.mode == "UPDATE":
            # In UPDATE mode, offer editable fallback — remediator's AskUserQuestion
            # handles this; here we return the editable form when a clone exists
            editable_cmd = item.get("install_command_editable_fallback", "")
            if editable_cmd:
                return editable_cmd.replace("<LOCAL_CLONE_PATH>", local_clone)

        # Default: fork git+https
        return item.get("install_command", "")

    # Non-graphify binaries: OS-aware command
    if "darwin" in ostype or sys.platform == "darwin":
        cmd = item.get("install_command_macos", "")
        if not cmd:
            # brew not available? Guide user
            brew_check = subprocess.run(["command", "-v", "brew"], shell=True, capture_output=True)
            if brew_check.returncode != 0:
                return (
                    f"# brew is not installed. Install Homebrew first:\n"
                    f"# /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                    f"# Then run: brew install {bin_name}"
                )
        return cmd
    elif "linux" in ostype or sys.platform.startswith("linux"):
        return item.get("install_command_linux", f"sudo apt-get install -y {bin_name}")
    else:
        return item.get("install_command", f"# Manual installation required for {bin_name}")
```

### graphify Editable Install (UPDATE mode)

In UPDATE mode, if a local clone of the graphify fork is detected at `~/graphify`
or `.graphify-dev/`, the user is asked whether to use editable install instead of
the standard git+https install. This allows in-place development of graphify itself.

The `install_command_editable_fallback` from the registry is used:
```
python3.12 -m venv .claude/graphify/.venv && .claude/graphify/.venv/bin/pip install -e <LOCAL_CLONE_PATH>
```

### Post-install Verification

After installing graphify, `version_regex` matching is performed:

```python
def _verify_after_install(bin_name: str, item: dict, context: ValidationContext) -> bool:
    """Run verify_command after install and check version_regex."""
    import subprocess, re
    from pathlib import Path

    verify_cmd = item.get("verify_command", "")
    if not verify_cmd:
        return True

    # Absolute path substitution for venv binaries
    if "path" in item:
        abs_path = str(Path(context.projectRoot) / item["path"])
        verify_cmd = verify_cmd.replace(item["path"], abs_path)

    result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()

    if "version_regex" in item:
        return bool(re.search(item["version_regex"], output, re.MULTILINE))

    return result.returncode == 0
```

## brew Not Installed (macOS)

If macOS is detected but `brew` is not installed, the remediator does not attempt
to auto-install. Instead, it adds a manual action:

```python
actions_required.append({
    "id": f"install-brew-for-{bin_name}",
    "priority": "HIGH",
    "description": "Homebrew is not installed. Install brew first, then retry.",
    "command": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
    "detail": f"After installing brew, run: brew install {bin_name}"
})
```

## Helper Functions

```python
def _build_result(mode: str, actions_executed: list, actions_required: list, skipped: int) -> dict:
    done = sum(1 for a in actions_executed if a["status"] == "DONE")
    failed = sum(1 for a in actions_executed if a["status"] == "FAILED")
    manual = len(actions_required)

    if failed == 0 and manual == 0:
        status = "SUCCESS"
    elif done > 0 and (failed > 0 or manual > 0):
        status = "PARTIAL"
    else:
        status = "FAILURE"

    return {
        "module": "binaries",
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

## Mode Behavior Summary

| Mode | auto-install | ask per item | report only |
|------|-------------|--------------|-------------|
| NEW_SETUP | yes | no | no |
| UPDATE | no | yes (AskUserQuestion) | no |
| VERIFY | no | no | yes |

## Output Format

```
┌──────────────────────────────────────────────────┐
│ Remediation: Binaries                             │
├──────────────────────┬────────────────────────────┤
│ Automatic Actions    │ Status                     │
├──────────────────────┼────────────────────────────┤
│ Install graphify     │ DONE                       │
│ Install jq           │ DONE                       │
│ Install python3.12   │ DONE                       │
├──────────────────────┴────────────────────────────┤
│ Manual Actions Required                           │
├───────────────────────────────────────────────────┤
│ [HIGH] Install Docker daemon                      │
│   Run: brew install --cask docker                 │
│   Note: Requires Docker Desktop GUI launch        │
└───────────────────────────────────────────────────┘
```

## References

- Validator: [../validators/binaries-validator.md](../validators/binaries-validator.md)
- Registry: [../registries/binaries.yaml](../registries/binaries.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
