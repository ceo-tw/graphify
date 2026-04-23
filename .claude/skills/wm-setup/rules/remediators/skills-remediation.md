---
title: Skills Remediation
impact: HIGH
impactDescription: Guides installation of missing skills
tags: [remediation, skills]
used_by: [validation-orchestrator]
validator: validators/skills-validator.md
order: 2
canAutoFix: partial
---

# Skills Remediation

**Impact: HIGH** - Guides installation of missing skills

## Overview

This remediator handles missing skill issues from skills-validator.
Provides installation guidance; some skills can be copied from templates.

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "auto"
) -> RemediationResult:
    """
    Provide skill installation guidance.

    Partial auto-fix: Can copy from templates if available
    """
    import shutil
    from pathlib import Path

    actions_executed = []
    actions_required = []

    template_base = Path(context.projectRoot) / ".claude/templates/skills"

    for item in validation_result["details"]:
        if item["status"] not in ["FAIL", "WARN"]:
            continue

        skill_name = item["name"]
        skill_path = Path(context.projectRoot) / item["path"]
        template_path = template_base / skill_name

        # Check if template exists
        if template_path.exists() and mode in ["auto", "interactive"]:
            try:
                skill_dir = skill_path.parent
                skill_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(template_path, skill_dir, dirs_exist_ok=True)
                actions_executed.append({
                    "id": f"install-{item['id']}",
                    "type": "create",
                    "target": item["path"],
                    "description": f"Installed skill from template: {skill_name}",
                    "status": "DONE"
                })
            except Exception as e:
                actions_executed.append({
                    "id": f"install-{item['id']}",
                    "type": "create",
                    "target": item["path"],
                    "description": f"Failed to install skill: {skill_name}",
                    "status": "FAILED",
                    "error": str(e)
                })
        else:
            # No template, user action required
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item["priority"] == "CRITICAL" else "MEDIUM",
                "description": f"Install skill: {skill_name}",
                "command": getInstallCommand(skill_name),
                "link": getDocumentationLink(skill_name)
            })

    return {
        "moduleId": "skills",
        "moduleName": "Skills",
        "status": _determineStatus(actions_executed, actions_required),
        "actionsExecuted": actions_executed,
        "actionsRequired": actions_required,
        "summary": {
            "totalActions": len(actions_executed) + len(actions_required),
            "automaticActions": len(actions_executed),
            "manualActions": len(actions_required)
        },
        "timestamp": datetime.now().isoformat()
    }
```

## Installation Commands

```python
def getInstallCommand(skill_name: str) -> str:
    """Get installation command for a skill."""
    commands = {
        "wm": "# Copy from reference project or create from template",
        "solve": "# Copy from reference project or create from template",
        "research": "# Copy from reference project",
        "codebase-explorer": "# Requires serena MCP setup first",
        "code-quality": "# Copy from reference project",
        "e2e-test": "# Requires playwright MCP setup first",
        "worktree-manager": "# Copy from reference project",
        "restore-context": "# Copy from reference project",
        "skill-creator": "# Copy from reference project",
        "dev-status": "# Copy from reference project"
    }
    return commands.get(skill_name, "# See documentation for installation")
```

## Skill Directory Structure

```
.claude/skills/{skill-name}/
├── SKILL.md              # Main skill definition
├── README.md             # Optional documentation
└── rules/                # Rule files (optional)
    ├── _sections.md
    └── {category}/
        └── {rule}.md
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Skills                      │
├──────────────────────┬──────────────────────┤
│ Automatic Actions    │ Status               │
├──────────────────────┼──────────────────────┤
│ (none available)     │                      │
├──────────────────────┴──────────────────────┤
│ User Actions Required                       │
├─────────────────────────────────────────────┤
│ ⚠️ [HIGH] Install skill: wm                │
│    The wm skill is CRITICAL for planning    │
│    workflows.                               │
│                                             │
│ ⚠️ [HIGH] Install skill: solve             │
│    The solve skill is CRITICAL for problem  │
│    solving workflows.                       │
│                                             │
│ ℹ️ [MEDIUM] Install skill: e2e-test        │
│    Requires: playwright MCP server          │
└─────────────────────────────────────────────┘
```

## Priority Guidance

| Priority | Action | Rationale |
|----------|--------|-----------|
| CRITICAL | Install immediately | Core workflow blocked |
| HIGH | Install soon | Key functionality limited |
| MEDIUM | Install when needed | Enhanced features |

## Dependency Check

```python
def checkSkillDependencies(skill_name: str, context: ValidationContext) -> list:
    """
    Check if skill dependencies are met.
    """
    dependencies = {
        "codebase-explorer": ["serena MCP"],
        "e2e-test": ["playwright MCP"],
        "research": ["WebSearch tool"]
    }

    missing = []
    for dep in dependencies.get(skill_name, []):
        if not isDependencyMet(dep, context):
            missing.append(dep)

    return missing
```

## References

- Validator: [../validators/skills-validator.md](../validators/skills-validator.md)
- Registry: [../registries/skills.yaml](../registries/skills.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
