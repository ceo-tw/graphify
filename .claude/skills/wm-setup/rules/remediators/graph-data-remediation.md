---
title: Graph Data Remediation
impact: CRITICAL
impactDescription: Rebuilds missing or stale graphify build artifacts
tags: [remediation, graph-data, graphify]
used_by: [validation-orchestrator]
validator: validators/graph-data-validator.md
order: 8
canAutoFix: partial
depends_on: [binaries-remediation]
---

# Graph Data Remediation

**Impact: CRITICAL** - Rebuilds graphify build artifacts

## Overview

This remediator rebuilds missing or stale graph.json files and build-summary.json.
Graphify binary must be installed before this runs — if absent, abort with a message
directing to binaries-remediation first.

Build time estimates:
- `_global` directed graph: ~1 minute
- Full 18-domain rebuild: ~2–5 minutes (Node 22 AST-based analysis)
- Single domain rebuild: ~10–30 seconds

3 modes:
- NEW_SETUP: rebuild all FAIL items automatically
- UPDATE: ask per FAIL item via AskUserQuestion
- VERIFY: report only, no rebuild

## Input

```
validation_result: output from graph-data-validator
context: ValidationContext
mode: "NEW_SETUP" | "UPDATE" | "VERIFY"
```

## Output

```json
{
  "module": "graph-data",
  "mode": "NEW_SETUP|UPDATE|VERIFY",
  "status": "SUCCESS|PARTIAL|FAILURE",
  "actionsExecuted": [
    {
      "id": "rebuild-GRAPH-001",
      "type": "build",
      "target": ".claude/architecture/graph/build-summary.json",
      "description": "Rebuilt build-summary.json (18 domains)",
      "status": "DONE"
    }
  ],
  "actionsRequired": [],
  "summary": {"automaticActions": 1, "manualActions": 0, "skipped": 0}
}
```

## Prerequisite Check

```python
def _check_graphify_available(context: ValidationContext) -> bool:
    """graphify binary must exist before attempting graph rebuilds."""
    import os
    from pathlib import Path
    graphify_bin = Path(context.projectRoot) / ".claude/graphify/.venv/bin/graphify"
    return graphify_bin.exists() and os.access(graphify_bin, os.X_OK)
```

If `_check_graphify_available()` returns False, remediation aborts:
```
ABORT: graphify binary not found at .claude/graphify/.venv/bin/graphify
Run binaries-remediation first to install graphify from fork.
```

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "NEW_SETUP"
) -> RemediationResult:
    """
    Rebuild missing or stale graph data files.

    NEW_SETUP: rebuild all FAIL items automatically
    UPDATE: ask per item
    VERIFY: report only
    """
    import subprocess
    from pathlib import Path

    project_root = context.projectRoot

    # Prerequisite: graphify must be installed
    if not _check_graphify_available(context):
        return {
            "module": "graph-data",
            "mode": mode,
            "status": "FAILURE",
            "actionsExecuted": [],
            "actionsRequired": [{
                "id": "prereq-graphify",
                "priority": "HIGH",
                "description": "graphify binary not found. Run binaries-remediation first.",
                "command": "# Run /wm-setup to install graphify from fork",
                "detail": "graphify must be installed at .claude/graphify/.venv/bin/graphify"
            }],
            "summary": {"automaticActions": 0, "manualActions": 1, "skipped": 0}
        }

    actions_executed = []
    actions_required = []
    skipped_count = 0

    failed_items = [
        d for d in validation_result["details"]
        if d["status"] == "FAIL"
    ]

    if mode == "VERIFY":
        for item in failed_items:
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item.get("priority") == "CRITICAL" else "MEDIUM",
                "description": f"Rebuild graph: {item['name']}",
                "command": item.get("install_hint", ""),
                "detail": item.get("detail", "")
            })
        return _build_result(mode, actions_executed, actions_required, skipped_count)

    for item in failed_items:
        graph_name = item["name"]
        build_cmd = item.get("install_hint", "")

        if not build_cmd:
            # No install_hint — skip with manual action
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "MEDIUM",
                "description": f"No build command available for {graph_name}",
                "command": "# Check registries/graph-data.yaml for install_command",
                "detail": ""
            })
            continue

        if mode == "UPDATE":
            estimate = _get_build_time_estimate(item)
            user_approved = AskUserQuestion(
                question=(
                    f"Rebuild graph: {graph_name}?\n"
                    f"Estimated time: {estimate}\n"
                    f"Reason: {item.get('detail', 'graph missing or stale')}"
                ),
                options=["yes", "no", "skip"]
            )
            if user_approved != "yes":
                skipped_count += 1
                continue

        # Log progress before running (builds can be slow)
        print(f"[graph-data] Rebuilding {graph_name} ... (this may take a while)")

        result = subprocess.run(
            build_cmd, shell=True, capture_output=True, text=True,
            cwd=project_root
        )

        if result.returncode == 0:
            actions_executed.append({
                "id": f"rebuild-{item['id']}",
                "type": "build",
                "target": item.get("name", graph_name),
                "description": f"Rebuilt {graph_name}",
                "status": "DONE"
            })
        else:
            stderr_tail = "\n".join(result.stderr.splitlines()[-20:])
            actions_executed.append({
                "id": f"rebuild-{item['id']}",
                "type": "build",
                "target": graph_name,
                "description": f"Failed to rebuild {graph_name}",
                "status": "FAILED",
                "error": result.stderr[:500]
            })
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item.get("priority") == "CRITICAL" else "MEDIUM",
                "description": f"Manual rebuild required: {graph_name}",
                "command": build_cmd,
                "detail": stderr_tail
            })

    return _build_result(mode, actions_executed, actions_required, skipped_count)
```

## Build Strategy

### Item Type Routing

| Item ID | Name | Build Command Used |
|---------|------|--------------------|
| GRAPH-001 | build-summary | `node ... build-all-graphs.ts` (full rebuild) |
| GRAPH-002 | _global | `graphify build ./src --directed --out-dir ...` |
| GRAPH-003..020 | domain:* | `node ... build-all-graphs.ts --only <domain>` |

The `install_hint` from the registry already contains the correct per-item command.
This remediator passes it through directly without transformation.

### Build Time Estimates

```python
def _get_build_time_estimate(item: dict) -> str:
    """Return human-readable time estimate for a build."""
    item_id = item.get("id", "")
    if item_id == "GRAPH-001":
        return "~2-5 minutes (all 18 domains)"
    elif item_id == "GRAPH-002":
        return "~1 minute (_global directed graph)"
    else:
        return "~10-30 seconds (single domain)"
```

### Batch Rebuild Optimization (NEW_SETUP)

In NEW_SETUP mode, if multiple domain graphs (GRAPH-003 through GRAPH-020) are FAIL,
the remediator consolidates them into a single `build-all-graphs.ts` run instead of
rebuilding each domain individually:

```python
def _maybe_consolidate_domain_rebuilds(failed_items: list) -> list:
    """
    If 3+ domain graphs are FAIL, consolidate into a single full rebuild.
    Returns a possibly reduced list where domain items are replaced with
    a single GRAPH-001-equivalent full rebuild item.
    """
    domain_items = [i for i in failed_items if i.get("id", "").startswith("GRAPH-0") and int(i["id"].split("-")[1]) >= 3]
    other_items = [i for i in failed_items if i not in domain_items]

    if len(domain_items) >= 3:
        # Consolidate: use build-all-graphs.ts for all domains
        consolidated = {
            "id": "GRAPH-ALL",
            "name": "all-domains (consolidated)",
            "priority": "HIGH",
            "install_hint": "node --experimental-strip-types --no-warnings scripts/graphify/build-all-graphs.ts",
            "detail": f"Consolidated rebuild of {len(domain_items)} domain graphs"
        }
        return other_items + [consolidated]
    else:
        return failed_items
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
        "module": "graph-data",
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

| Mode | auto-rebuild | ask per item | report only |
|------|-------------|--------------|-------------|
| NEW_SETUP | yes (with consolidation) | no | no |
| UPDATE | no | yes (AskUserQuestion + time estimate) | no |
| VERIFY | no | no | yes |

## Output Format

```
┌──────────────────────────────────────────────────────┐
│ Remediation: Graph Data                               │
├──────────────────────────┬────────────────────────────┤
│ Automatic Actions        │ Status                     │
├──────────────────────────┼────────────────────────────┤
│ Rebuild build-summary    │ DONE (~3m)                 │
│ Rebuild _global          │ DONE (~1m)                 │
│ Rebuild domain:ai-chat   │ DONE (~15s)                │
├──────────────────────────┴────────────────────────────┤
│ Manual Actions Required                               │
├───────────────────────────────────────────────────────┤
│ (none)                                                │
└───────────────────────────────────────────────────────┘
```

## References

- Validator: [../validators/graph-data-validator.md](../validators/graph-data-validator.md)
- Registry: [../registries/graph-data.yaml](../registries/graph-data.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
- Depends on: [binaries-remediation.md](./binaries-remediation.md)
