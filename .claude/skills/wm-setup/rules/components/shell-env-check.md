---
title: Shell Environment Check
impact: HIGH
impactDescription: Verify required shell environment variables
tags: [component]
used_by: [wm-setup]
---

# Shell Environment Check

**Impact: HIGH** - Verify required shell environment variables for Claude Code features

## Overview

This component checks that required shell environment variables are properly set
for Claude Code features to function correctly.

## Required Environment Variables

| Variable | Expected Value | Purpose |
|----------|----------------|---------|
| `ENABLE_LSP_TOOL` | `1` | LSP tool activation (serena MCP required) |
| `MAX_THINKING_TOKENS` | `4000` | Extended Thinking token budget |

## Detection Logic

```python
def checkShellEnvVars() -> dict:
    """
    Check required shell environment variables.

    Returns:
        {
            "all_set": True/False,
            "missing": ["VAR_NAME", ...],
            "incorrect": [{"name": "VAR", "expected": "1", "actual": "0"}, ...],
            "correct": ["VAR_NAME", ...]
        }
    """
    required_vars = [
        ("ENABLE_LSP_TOOL", "1"),
        ("MAX_THINKING_TOKENS", "4000")
    ]

    results = {
        "all_set": True,
        "missing": [],
        "incorrect": [],
        "correct": []
    }

    for var_name, expected in required_vars:
        # Use Bash tool to get current value
        current = Bash(f"echo ${var_name}").strip()

        if not current:
            results["missing"].append(var_name)
            results["all_set"] = False
        elif current != expected:
            results["incorrect"].append({
                "name": var_name,
                "expected": expected,
                "actual": current
            })
            results["all_set"] = False
        else:
            results["correct"].append(var_name)

    return results
```

## Report Format

```python
def formatEnvCheckReport(results: dict) -> str:
    """Format environment check results for display."""
    lines = ["### Shell Environment Variables"]

    if results["all_set"]:
        lines.append("All required variables are correctly set.")
    else:
        if results["missing"]:
            lines.append("\n**Missing Variables:**")
            for var in results["missing"]:
                lines.append(f"- `{var}` (not set)")

        if results["incorrect"]:
            lines.append("\n**Incorrect Values:**")
            for item in results["incorrect"]:
                lines.append(
                    f"- `{item['name']}`: expected `{item['expected']}`, "
                    f"got `{item['actual']}`"
                )

    return "\n".join(lines)
```

## Setup Instructions

### For Missing Variables

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Claude Code Environment Variables
export ENABLE_LSP_TOOL=1
export MAX_THINKING_TOKENS=4000
```

Then reload:
```bash
source ~/.zshrc  # or ~/.bashrc
```

## Note

This step reports status only; it does NOT modify shell files automatically.
User action is required to fix any issues.

## When to Apply

- During Step 1.5 of wm-setup workflow
- After initial analysis, before MCP management

## References

- [context-gate.md](./context-gate.md) - Step 0 context check
