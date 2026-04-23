---
title: Validation Logic
impact: HIGH
impactDescription: Tech-resource mismatch detection and validation
tags: [workflow]
used_by: [wm-setup]
migrated_from: analysis-rules-validation.md
---

# Validation Logic

**Impact: HIGH** - Validation logic for Claude Code resources and tech-resource mismatch detection

## Overview

This file defines validation functions to check Claude Code environment setup and detect mismatches between detected tech stack and installed resources.

**Key Functions**:
- `runAllValidations()`: Execute all validation checks
- `detectTechResourceMismatch()`: Compare detected tech with installed resources
- `buildRemediationItems()`: Create prioritized remediation action list

**Dependencies**:
- tech-mapping.md (for TECH_SKILLS_MAP, TECH_AGENTS_MAP, CORE_SKILLS)

## Functions

### runAllValidations()

```python
def runAllValidations(context_data: dict, tech_stack: list) -> dict:
    """
    Run all validation checks.

    Args:
        context_data: Parsed /context output
        tech_stack: List of detected technologies

    Returns:
        {
            "mcp_status": {...},
            "skills_status": {...},
            "agents_status": {...},
            "tech_mismatch": {...},
            "overall_status": "PASS" | "FAIL",
            "remediation_needed": True/False
        }
    """
    results = {}

    installed_resources = {
        "skills": extractInstalledSkills(),
        "agents": extractInstalledAgents()
    }

    results["mcp_status"] = validateMcpServers(context_data)
    results["skills_status"] = validateSkills(context_data, installed_resources["skills"])
    results["agents_status"] = validateAgents(context_data, installed_resources["agents"])
    results["tech_mismatch"] = detectTechResourceMismatch(tech_stack, installed_resources)

    results["overall_status"] = _determineOverallStatus(results)
    results["remediation_needed"] = results["overall_status"] == "FAIL"

    return results
```

### detectTechResourceMismatch()

```python
def detectTechResourceMismatch(tech_stack: list, installed_resources: dict) -> dict:
    """
    Compare detected tech stack with installed resources.

    Returns:
        {
            "skills_mismatch": {
                "missing": ["react.md"],
                "extra": ["python.md"]
            },
            "agents_mismatch": {
                "missing": [],
                "extra": []
            },
            "has_mismatch": True,
            "mismatch_type": "NONE" | "MISSING" | "EXTRA" | "BOTH"
        }
    """
    # Get expected resources
    expected_skills = set(getTechSkillsMapping(tech_stack))
    expected_agents_map = getTechAgentsMapping(tech_stack)
    expected_agents = set(expected_agents_map["core"] + expected_agents_map["frontend"])

    # Get installed resources
    installed_skills = set(installed_resources.get("skills", []))
    installed_agents = set(installed_resources.get("agents", []))

    # Core resources (NOT flagged as extra)
    core_skills = set(CORE_SKILLS)
    core_agents = set(TECH_AGENTS_MAP["core"])

    # Detect mismatch
    skills_missing = expected_skills - installed_skills
    skills_extra = (installed_skills - expected_skills) - core_skills
    agents_missing = expected_agents - installed_agents
    agents_extra = (installed_agents - expected_agents) - core_agents

    # Classify type
    has_missing = len(skills_missing) > 0 or len(agents_missing) > 0
    has_extra = len(skills_extra) > 0 or len(agents_extra) > 0

    if has_missing and has_extra:
        mismatch_type = "BOTH"
    elif has_missing:
        mismatch_type = "MISSING"
    elif has_extra:
        mismatch_type = "EXTRA"
    else:
        mismatch_type = "NONE"

    return {
        "skills_mismatch": {"missing": sorted(list(skills_missing)), "extra": sorted(list(skills_extra))},
        "agents_mismatch": {"missing": sorted(list(agents_missing)), "extra": sorted(list(agents_extra))},
        "has_mismatch": has_missing or has_extra,
        "mismatch_type": mismatch_type
    }
```

### buildRemediationItems()

```python
def buildRemediationItems(validation_results: dict) -> list:
    """
    Build remediation items sorted by priority.

    Priority Order:
    1. MCP_MISSING (critical)
    2. SKILL_MISSING (code quality)
    3. TECH_MISMATCH (requires user decision)
    4. AGENT_MISSING (optional)
    """
    items = []

    if validation_results["mcp_status"].get("has_failures"):
        items.append({"type": "MCP_MISSING", "priority": 1, "requires_user_decision": False})

    if validation_results["skills_status"].get("has_failures"):
        items.append({"type": "SKILL_MISSING", "priority": 2, "requires_user_decision": False})

    if validation_results["tech_mismatch"]["has_mismatch"]:
        items.append({"type": "TECH_MISMATCH", "priority": 3, "requires_user_decision": True})

    if validation_results["agents_status"].get("has_failures"):
        items.append({"type": "AGENT_MISSING", "priority": 4, "requires_user_decision": False})

    return sorted(items, key=lambda x: x["priority"])
```

## Helper Functions

### extractInstalledSkills()

```python
def extractInstalledSkills() -> list:
    """Extract installed best-practices skills from filesystem."""
    skill_files = Glob(pattern="*.md", path=".claude/skills/best-practices/rules/")
    return [os.path.basename(f) for f in skill_files]
```

### extractInstalledAgents()

```python
def extractInstalledAgents() -> list:
    """Extract installed agents from filesystem."""
    agent_files = Glob(pattern="*.md", path=".claude/agents/")
    return [os.path.basename(os.path.dirname(f)) for f in agent_files]
```

## When to Apply

- After tech stack detection in wm-setup workflow
- Before presenting remediation options to user
- When generating validation report

## References

- [tech-mapping.md](./tech-mapping.md) - Tech to resource mapping
- [remediation.md](./remediation.md) - Remediation execution
