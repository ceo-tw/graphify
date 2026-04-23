---
title: Remediation Logic
impact: HIGH
impactDescription: User decision workflow and remediation execution
tags: [feature]
used_by: [wm-setup]
migrated_from: analysis-rules-remediation.md
---

# Remediation Logic

**Impact: HIGH** - User decision workflow and remediation logic for tech-resource mismatch

## Overview

This file contains functions for handling user decisions on tech-resource mismatches and planning remediation actions.

**Key Functions**:
- `buildMismatchDecisionOptions()`: Generate AskUserQuestion options
- `processUserDecision()`: Parse user selection and determine actions
- `remediateSkillMismatch()`: Execute skill remediation
- `remediateAgentMismatch()`: Execute agent remediation
- `consolidateRemediationResults()`: Merge results for reporting

## User Decision Functions

### buildMismatchDecisionOptions()

```python
def buildMismatchDecisionOptions(mismatch_result: dict) -> dict | None:
    """
    Build AskUserQuestion options for tech-resource mismatch.

    Returns None if no mismatch (skip Step 4.5).

    Options by mismatch_type:
    - MISSING: add_all, skip
    - EXTRA: remove_all, skip
    - BOTH: add_all, remove_all, apply_all, skip
    """
    if not mismatch_result.get("has_mismatch"):
        return None

    mismatch_type = mismatch_result.get("mismatch_type")
    options = []

    if mismatch_type in ["MISSING", "BOTH"]:
        options.append({
            "value": "add_all",
            "label": "누락 리소스 추가" + (" (권장)" if mismatch_type == "MISSING" else "")
        })

    if mismatch_type in ["EXTRA", "BOTH"]:
        options.append({"value": "remove_all", "label": "불필요 리소스 제거 안내"})

    if mismatch_type == "BOTH":
        options.append({"value": "apply_all", "label": "전체 적용 (권장)"})

    options.append({"value": "skip", "label": "건너뛰기"})

    return {"header": "[Step 4.5] 기술 스택 불일치 발견", "options": options}
```

### processUserDecision()

```python
def processUserDecision(user_selection: str, mismatch_result: dict) -> dict:
    """
    Parse user selection and determine actions.

    Returns:
        {
            "actions": ["add_skills", "remove_agents", ...],
            "skip": False,
            "details": {
                "skills_to_add": [...],
                "skills_to_remove": [...],
                "agents_to_add": [...],
                "agents_to_remove": [...]
            }
        }
    """
    if user_selection == "skip":
        return {"actions": [], "skip": True, "details": {}}

    actions = []
    details = {"skills_to_add": [], "skills_to_remove": [], "agents_to_add": [], "agents_to_remove": []}

    skills_missing = mismatch_result.get("skills_mismatch", {}).get("missing", [])
    agents_missing = mismatch_result.get("agents_mismatch", {}).get("missing", [])
    skills_extra = mismatch_result.get("skills_mismatch", {}).get("extra", [])
    agents_extra = mismatch_result.get("agents_mismatch", {}).get("extra", [])

    if user_selection in ["add_all", "apply_all"]:
        if skills_missing:
            actions.append("add_skills")
            details["skills_to_add"] = skills_missing
        if agents_missing:
            actions.append("add_agents")
            details["agents_to_add"] = agents_missing

    if user_selection in ["remove_all", "apply_all"]:
        if skills_extra:
            actions.append("remove_skills")
            details["skills_to_remove"] = skills_extra
        if agents_extra:
            actions.append("remove_agents")
            details["agents_to_remove"] = agents_extra

    return {"actions": actions, "skip": False, "details": details}
```

## Remediation Execution Functions

### remediateSkillMismatch()

```python
def remediateSkillMismatch(mismatch: dict, action: str) -> dict:
    """
    Execute remediation for skill mismatch.

    Returns:
        {
            "actions_taken": [],
            "user_actions_required": [...],
            "status": "SUCCESS" | "NEEDS_USER_ACTION" | "SKIPPED"
        }
    """
    if action == "skip":
        return {"actions_taken": [], "user_actions_required": [], "status": "SKIPPED"}

    user_actions = []
    skills_missing = mismatch.get("skills_mismatch", {}).get("missing", [])
    skills_extra = mismatch.get("skills_mismatch", {}).get("extra", [])

    if action in ["add_all", "apply_all"] and skills_missing:
        user_actions.append(f"📋 누락된 Best-Practice Skills: {', '.join(skills_missing)}")
        user_actions.append("복사 경로: .claude/skills/best-practices/rules/")

    if action in ["remove_all", "apply_all"] and skills_extra:
        user_actions.append(f"🗑️ 불필요한 Skills: {', '.join(skills_extra)}")
        user_actions.append("⚠️ 삭제 전 백업 권장")

    status = "NEEDS_USER_ACTION" if user_actions else "SUCCESS"
    return {"actions_taken": [], "user_actions_required": user_actions, "status": status}
```

### consolidateRemediationResults()

```python
def consolidateRemediationResults(results: list[dict]) -> dict:
    """
    Consolidate multiple remediation results.

    Returns:
        {
            "actions_taken": [...],
            "user_actions_required": [...],
            "overall_status": "SUCCESS" | "NEEDS_USER_ACTION" | "PARTIAL" | "SKIPPED",
            "summary": {"total_actions": N, "automatic_actions": N, "manual_actions": N}
        }
    """
    all_actions = []
    all_user_actions = []

    for result in results:
        all_actions.extend(result.get("actions_taken", []))
        all_user_actions.extend(result.get("user_actions_required", []))

    # Deduplicate
    actions_taken = list(dict.fromkeys(all_actions))
    user_actions = list(dict.fromkeys(all_user_actions))

    # Determine status
    statuses = [r.get("status") for r in results]
    if all(s == "SKIPPED" for s in statuses):
        overall_status = "SKIPPED"
    elif any(s == "NEEDS_USER_ACTION" for s in statuses):
        overall_status = "NEEDS_USER_ACTION"
    else:
        overall_status = "SUCCESS"

    return {
        "actions_taken": actions_taken,
        "user_actions_required": user_actions,
        "overall_status": overall_status,
        "summary": {
            "total_actions": len(actions_taken) + len(user_actions),
            "automatic_actions": len(actions_taken),
            "manual_actions": len(user_actions)
        }
    }
```

## Message Style Guide

### Emoji Usage

| Action | Emoji | Example |
|--------|-------|---------|
| Addition | 📋 | "📋 누락된 Best-Practice Skill: react.md" |
| Removal | 🗑️ | "🗑️ 불필요한 Skill: python.md" |
| Information | ℹ️ | "ℹ️ Core Skill이므로 제거하지 않습니다" |
| Warning | ⚠️ | "⚠️ 삭제 전 백업 권장" |
| Agent | 🤖 | "🤖 누락된 Agent: playwright-test-planner" |

## When to Apply

- After validation detects tech-resource mismatch
- During user decision workflow (Step 4.5)
- When executing remediation actions

## References

- [validation.md](./validation.md) - Validation logic
- [tech-mapping.md](./tech-mapping.md) - Tech mapping
