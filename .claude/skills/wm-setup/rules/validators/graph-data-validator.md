---
title: Graph Data Validator
impact: CRITICAL
impactDescription: Validates graphify build artifacts (graph.json files)
tags: [validator, graph-data, graphify]
used_by: [validation-orchestrator]
registry: registries/graph-data.yaml
order: 8
blocking: true
depends_on: [binaries-validator]
---

# Graph Data Validator

**Impact: CRITICAL** - Validates graphify build artifacts required by review-orchestrator
and knowledge-graph-navigator

## Overview

This validator checks existence and content validity of all graph.json files and
build-summary.json defined in `graph-data.yaml`. jq must be installed (from
binaries-validator) — if absent, all items are SKIP.

## Input

```
registry_path: path to registries/graph-data.yaml
context: ValidationContext (projectRoot, mode, verbose)
```

## Output

```json
{
  "module": "graph-data",
  "items": [
    {
      "id": "GRAPH-001",
      "name": "build-summary",
      "status": "PASS|FAIL|WARN|SKIP",
      "detail": "build-summary.json exists, 18 domains found",
      "install_hint": "node --experimental-strip-types --no-warnings scripts/graphify/build-all-graphs.ts"
    }
  ],
  "counts": {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
}
```

## Dependency Check (jq)

```python
def _check_jq_available() -> bool:
    """jq must be installed for JSON validation commands."""
    import subprocess
    result = subprocess.run(
        ["command", "-v", "jq"],
        shell=True, capture_output=True
    )
    return result.returncode == 0
```

If `_check_jq_available()` returns False, ALL items are returned with status=SKIP
and detail="jq not installed — run binaries-validator first".

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate graph data files from registry.

    Order: 8
    Blocking: True for CRITICAL items (build-summary, _global)
    Depends on: binaries-validator (jq must pass)
    """
    import subprocess
    import json
    from pathlib import Path

    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    project_root = Path(context.projectRoot)

    # Prerequisite: jq must be installed
    if not _check_jq_available():
        results = []
        for item in registry["items"]:
            results.append({
                "id": item["id"],
                "name": item["name"],
                "status": "SKIP",
                "detail": "jq not installed — run binaries-validator first",
                "install_hint": "",
                "priority": item.get("priority", "HIGH")
            })
        counts = _count_statuses(results)
        return _build_result(results, counts, "SKIP")

    results = []

    for item in registry["items"]:
        file_path = project_root / item["path"]

        # Step 1: file existence check
        if not file_path.exists():
            status = "FAIL"
            detail = f"File not found: {item['path']}"
            install_hint = item.get("install_command", "")
            results.append(_make_item(item, status, detail, install_hint))
            continue

        # Step 2: run verify_command (jq-based empty graph detection)
        verify_cmd = item.get("verify_command", "")
        if verify_cmd:
            # Substitute relative path with absolute
            abs_verify_cmd = verify_cmd.replace(item["path"], str(file_path))
            verify_result = subprocess.run(
                abs_verify_cmd, shell=True, capture_output=True, text=True
            )

            if verify_result.returncode != 0:
                # Determine whether it's empty or corrupt
                jq_output = verify_result.stdout.strip()
                if jq_output in ("false", "null", "0"):
                    status = "FAIL"
                    detail = f"{item['name']} graph is empty or stale (nodes/edges == 0)"
                else:
                    status = "FAIL"
                    detail = f"{item['name']} verify_command failed: {verify_result.stderr.strip()}"
                install_hint = item.get("install_command", "")
                results.append(_make_item(item, status, detail, install_hint))
                continue

        # Step 3: build-summary specific — check domains array length == 18
        if item["id"] == "GRAPH-001":
            try:
                with open(file_path) as f:
                    summary = json.load(f)
                domains = summary.get("domains", [])
                domain_count = len(domains)
                if domain_count != 18:
                    status = "FAIL"
                    detail = (
                        f"build-summary.json has {domain_count} domains, expected 18. "
                        "Graph data may be incomplete."
                    )
                    install_hint = item.get("install_command", "")
                    results.append(_make_item(item, status, detail, install_hint))
                    continue
                else:
                    detail = f"build-summary.json present, {domain_count} domains confirmed"
            except (json.JSONDecodeError, KeyError) as e:
                status = "FAIL"
                detail = f"build-summary.json is corrupt or invalid JSON: {e}"
                install_hint = item.get("install_command", "")
                results.append(_make_item(item, status, detail, install_hint))
                continue
        else:
            detail = f"{item['name']} graph.json present and non-empty"

        results.append(_make_item(item, "PASS", detail, None))

    counts = _count_statuses(results)

    # Determine overall status — CRITICAL items (build-summary, _global) failures block
    critical_failed = any(
        r["status"] == "FAIL" and r.get("priority") == "CRITICAL"
        for r in results
    )
    high_failed_count = sum(
        1 for r in results
        if r["status"] == "FAIL" and r.get("priority") == "HIGH"
    )

    if critical_failed:
        overall = "FAIL"
    elif high_failed_count > 0:
        overall = "WARN"
    else:
        overall = "PASS"

    return _build_result(results, counts, overall)
```

## Helper Functions

```python
def _make_item(item: dict, status: str, detail: str, install_hint) -> dict:
    return {
        "id": item["id"],
        "name": item["name"],
        "status": status,
        "detail": detail,
        "install_hint": install_hint or "",
        "priority": item.get("priority", "HIGH")
    }


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
        "moduleId": "graph-data",
        "moduleName": "Graph Data",
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

## Status Mapping

| Condition | Status |
|-----------|--------|
| jq not installed | SKIP (all items) |
| File does not exist | FAIL |
| nodes/edges == 0 in graph.json | FAIL (stale/corrupt) |
| build-summary domains != 18 | FAIL |
| build-summary corrupt/invalid JSON | FAIL |
| verify_command non-zero exit | FAIL |
| All checks pass | PASS |

## Output Format

```
┌─────────────────────────────────────────────────────┐
│ [8/10] Graph Data                                    │
├──────────────────────────┬─────────┬─────────────────┤
│ Graph                    │ Status  │ Priority        │
├──────────────────────────┼─────────┼─────────────────┤
│ build-summary            │ ✅ PASS │ CRITICAL        │
│ _global                  │ ✅ PASS │ CRITICAL        │
│ domain:agents-orch       │ ✅ PASS │ HIGH            │
│ domain:ai-chat           │ ❌ FAIL │ HIGH            │
│ domain:billing           │ ✅ PASS │ HIGH            │
│ ...                      │ ...     │ HIGH            │
├──────────────────────────┴─────────┴─────────────────┤
│ Pass Rate: 90% (18/20)           Status: ⚠️ WARN    │
└─────────────────────────────────────────────────────┘
```

## References

- Registry: [../registries/graph-data.yaml](../registries/graph-data.yaml)
- Remediation: [../remediators/graph-data-remediation.md](../remediators/graph-data-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
- Depends on: [binaries-validator.md](./binaries-validator.md) (jq)
