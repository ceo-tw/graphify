---
title: Agents Validator
impact: CRITICAL
impactDescription: Validates core agents installation - CRITICAL agents block pipeline
tags: [validator, agents]
used_by: [validation-orchestrator]
registry: registries/agents.yaml
order: 3
blocking: true  # CRITICAL agents block pipeline
---

# Agents Validator

**Impact: CRITICAL** - Validates core agents installation against registry.
CRITICAL agents (dev-executor) will **block** the pipeline if missing.

## Overview

This validator checks for installed agents defined in `agents.yaml`.
**Blocking**: CRITICAL agents (dev-executor) will stop the pipeline if missing.

## Validation Logic

```python
def validate(registry_path: str, context: ValidationContext) -> ValidationResult:
    """
    Validate agents from registry.

    Order: 3 (after skills validation)
    """
    import yaml
    from pathlib import Path

    # Load registry
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    results = []

    for item in registry["items"]:
        agent_path = Path(context.projectRoot) / item["path"]
        exists = agent_path.exists() and agent_path.is_file()

        if exists:
            status = "PASS"
            message = None
        else:
            if item["priority"] == "CRITICAL":
                status = "FAIL"
                message = f"Critical agent missing: {item['name']}"
            elif item["priority"] == "HIGH":
                status = "WARN"
                message = f"Recommended agent missing: {item['name']}"
            else:
                status = "SKIP"
                message = f"Optional agent missing: {item['name']}"

        results.append({
            "id": item["id"],
            "name": item["name"],
            "path": item["path"],
            "status": status,
            "priority": item["priority"],
            "category": item.get("category", "unknown"),
            "invokes": item.get("invokes", []),
            "invokedBy": item.get("invokedBy", []),
            "message": message,
            "remediation": "agents-remediation" if status in ["FAIL", "WARN"] else None
        })

    # Calculate stats
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warnings = sum(1 for r in results if r["status"] == "WARN")

    # Determine overall status
    critical_failed = any(
        r["status"] == "FAIL" and r["priority"] == "CRITICAL"
        for r in results
    )

    if critical_failed:
        overall_status = "FAIL"
    elif failed > 0 or warnings > len(results) * 0.2:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    # Check if any CRITICAL agent is missing
    critical_missing = any(
        r["status"] == "FAIL" and r["priority"] == "CRITICAL"
        for r in results
    )

    return {
        "moduleId": "agents",
        "moduleName": "Agents",
        "status": overall_status,
        "passRate": (passed / len(results)) * 100 if results else 0,
        "items": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings
        },
        "details": results,
        "blocking": critical_missing,  # Block if CRITICAL agents missing
        "timestamp": datetime.now().isoformat()
    }
```

## Category Grouping

```python
def groupByCategory(results: list) -> dict:
    """Group validation results by category."""
    categories = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    return categories

# Categories:
# - core-development: design, planner-task, dev-executor, qa
# - bug-resolution: root-cause-finder, bug-fixer, knowledge-keeper
# - e2e-testing: playwright-test-planner, playwright-test-generator, playwright-test-healer
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ [3/6] Agents                                │
├──────────────────────┬─────────┬────────────┤
│ Agent                │ Status  │ Category   │
├──────────────────────┼─────────┼────────────┤
│ ── Core Development ─┼─────────┼────────────│
│ design               │ ✅ PASS │ core       │
│ planner-task         │ ✅ PASS │ core       │
│ dev-executor         │ ✅ PASS │ core       │
│ qa                   │ ✅ PASS │ core       │
├──────────────────────┼─────────┼────────────│
│ ── Bug Resolution ───┼─────────┼────────────│
│ root-cause-finder    │ ✅ PASS │ bug-fix    │
│ bug-fixer            │ ✅ PASS │ bug-fix    │
│ knowledge-keeper     │ ✅ PASS │ bug-fix    │
├──────────────────────┼─────────┼────────────│
│ ── E2E Testing ──────┼─────────┼────────────│
│ playwright-*-planner │ ✅ PASS │ e2e        │
│ playwright-*-generator│ ✅ PASS │ e2e        │
│ playwright-*-healer  │ ✅ PASS │ e2e        │
├──────────────────────┴─────────┴────────────┤
│ Pass Rate: 100% (10/10)      Status: ✅ PASS│
└─────────────────────────────────────────────┘
```

## Dependency Check

```python
def checkAgentDependencies(results: list) -> list:
    """
    Check if agent dependencies are satisfied.

    If agent A invokes agent B, but B is missing, add warning.
    """
    warnings = []
    installed = {r["name"] for r in results if r["status"] == "PASS"}

    for r in results:
        if r["status"] == "PASS":
            for dep in r.get("invokes", []):
                if dep not in installed:
                    warnings.append({
                        "agent": r["name"],
                        "missing_dep": dep,
                        "message": f"{r['name']} invokes {dep}, but {dep} is not installed"
                    })

    return warnings
```

## Call Graph Consistency Validation

Validates that the invokes/invokedBy relationships are consistent.

```python
def validateCallGraph(results: list) -> dict:
    """
    Validate agent call graph for consistency.

    Checks:
    1. If A invokes B, then B.invokedBy should contain A
    2. If A.invokedBy contains B, then B.invokes should contain A
    3. Detect orphan agents (no invokedBy and not invoked by skills)
    4. Detect broken chains (agent invokes non-existent agent)
    """
    installed = {r["name"]: r for r in results if r["status"] == "PASS"}
    inconsistencies = []
    orphans = []
    broken_chains = []

    for name, agent in installed.items():
        # Check forward consistency (invokes -> invokedBy)
        for target in agent.get("invokes", []):
            if target in installed:
                target_agent = installed[target]
                if name not in target_agent.get("invokedBy", []):
                    inconsistencies.append({
                        "type": "missing_invokedBy",
                        "agent": name,
                        "target": target,
                        "message": f"{name} invokes {target}, but {target}.invokedBy doesn't list {name}"
                    })
            else:
                # Target agent not installed
                broken_chains.append({
                    "agent": name,
                    "missing_target": target,
                    "message": f"{name} invokes {target}, but {target} is not installed"
                })

        # Check backward consistency (invokedBy -> invokes)
        for caller in agent.get("invokedBy", []):
            # Skip skill invocations (e.g., "wm skill", "solve skill")
            if "skill" in caller.lower():
                continue
            if caller in installed:
                caller_agent = installed[caller]
                if name not in caller_agent.get("invokes", []):
                    inconsistencies.append({
                        "type": "missing_invokes",
                        "agent": caller,
                        "target": name,
                        "message": f"{name}.invokedBy lists {caller}, but {caller}.invokes doesn't list {name}"
                    })

        # Check for orphan agents (no parent)
        invokedBy = agent.get("invokedBy", [])
        if not invokedBy or (len(invokedBy) == 0):
            orphans.append({
                "agent": name,
                "message": f"{name} has no invokedBy - may be orphan"
            })

    return {
        "inconsistencies": inconsistencies,
        "orphans": orphans,
        "broken_chains": broken_chains,
        "is_valid": len(inconsistencies) == 0 and len(broken_chains) == 0
    }
```

### Call Graph Output

```
┌─────────────────────────────────────────────┐
│ Call Graph Validation                       │
├─────────────────────────────────────────────┤
│ Consistency Check:                          │
│   ✅ Forward references (invokes → invokedBy)│
│   ✅ Backward references (invokedBy → invokes)│
│   ⚠️ Orphan agents: 0                       │
│   ✅ Broken chains: 0                       │
├─────────────────────────────────────────────┤
│ Status: ✅ VALID                            │
└─────────────────────────────────────────────┘
```

## References

- Registry: [../registries/agents.yaml](../registries/agents.yaml)
- Remediation: [../remediators/agents-remediation.md](../remediators/agents-remediation.md)
- Interface: [_validator-interface.md](./_validator-interface.md)
