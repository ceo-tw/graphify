---
title: Domains Remediation
impact: HIGH
impactDescription: Creates missing AGENTS.md files and domain directories
tags: [remediation, domains]
used_by: [validation-orchestrator]
validator: validators/domains-validator.md
order: 7
canAutoFix: partial
---

# Domains Remediation

**Impact: HIGH** - Creates missing domain directories and AGENTS.md template files

## Overview

This remediator handles domain validation failures:
- Creates missing domain directories (auto-safe)
- Creates AGENTS.md template files (auto-safe)
- Reports missing guide files (manual action required)

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "auto"
) -> RemediationResult:
    """
    Remediate missing domain files and directories.

    Auto-safe: mkdir and template creation
    """
    from pathlib import Path

    actions_executed = []
    actions_required = []

    for item in validation_result["details"]:
        if item["status"] not in ["FAIL", "WARN"]:
            continue

        domain_path = Path(context.projectRoot) / item["directory"]
        agents_file_path = Path(context.projectRoot) / item.get("agentsFile", f"{item['directory']}/AGENTS.md")

        # Remediate missing directory
        if not domain_path.exists():
            if mode in ["auto", "interactive"]:
                try:
                    domain_path.mkdir(parents=True, exist_ok=True)
                    actions_executed.append({
                        "id": f"create-dir-{item['id']}",
                        "type": "create",
                        "target": item["directory"],
                        "description": f"Created domain directory: {item['directory']}",
                        "status": "DONE"
                    })
                except Exception as e:
                    actions_executed.append({
                        "id": f"create-dir-{item['id']}",
                        "type": "create",
                        "target": item["directory"],
                        "description": f"Failed to create directory: {item['directory']}",
                        "status": "FAILED",
                        "error": str(e)
                    })
                    actions_required.append({
                        "id": f"manual-dir-{item['id']}",
                        "priority": "HIGH",
                        "description": f"Manually create domain directory: {item['directory']}",
                        "command": f"mkdir -p {item['directory']}"
                    })
            else:  # report-only
                actions_required.append({
                    "id": f"manual-dir-{item['id']}",
                    "priority": item.get("priority", "MEDIUM"),
                    "description": f"Create domain directory: {item['directory']}",
                    "command": f"mkdir -p {item['directory']}"
                })

        # Remediate missing AGENTS.md
        if not agents_file_path.exists():
            if mode in ["auto", "interactive"]:
                try:
                    agents_template = _generateAgentsTemplate(item)
                    agents_file_path.parent.mkdir(parents=True, exist_ok=True)
                    agents_file_path.write_text(agents_template)
                    actions_executed.append({
                        "id": f"create-agents-{item['id']}",
                        "type": "create",
                        "target": str(agents_file_path),
                        "description": f"Created AGENTS.md template: {item['directory']}/AGENTS.md",
                        "status": "DONE"
                    })
                except Exception as e:
                    actions_executed.append({
                        "id": f"create-agents-{item['id']}",
                        "type": "create",
                        "target": str(agents_file_path),
                        "description": f"Failed to create AGENTS.md: {item['directory']}/AGENTS.md",
                        "status": "FAILED",
                        "error": str(e)
                    })
                    actions_required.append({
                        "id": f"manual-agents-{item['id']}",
                        "priority": "HIGH",
                        "description": f"Manually create AGENTS.md in {item['directory']}",
                        "link": "https://github.com/your-org/templates/AGENTS.md"
                    })
            else:  # report-only
                actions_required.append({
                    "id": f"manual-agents-{item['id']}",
                    "priority": item.get("priority", "MEDIUM"),
                    "description": f"Create AGENTS.md file in {item['directory']}",
                    "link": "https://github.com/your-org/templates/AGENTS.md"
                })

        # Report missing guide files (cannot auto-create)
        if item.get("guideFile") and item["status"] == "WARN":
            actions_required.append({
                "id": f"manual-guide-{item['id']}",
                "priority": "MEDIUM",
                "description": f"Guide file missing for {item['name']}: {item['guideFile']}",
                "link": ".claude/skills/wm/rules/policies/"
            })

    return {
        "moduleId": "domains",
        "moduleName": "Domain Definitions",
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

## AGENTS.md Template Generator

```python
def _generateAgentsTemplate(domain_item: dict) -> str:
    """
    Generate AGENTS.md template for domain.
    """
    template = f"""# {domain_item['name'].title()} Domain Guidelines

> Domain-specific rules and guidelines for {domain_item['name']} development.

---

## 1. Overview

**Domain**: {domain_item['name']}
**Type**: {domain_item['type']}
**Tech Stack**: {', '.join(domain_item.get('techStack', []))}

## 2. Directory Structure

```
{domain_item['directory']}/
├── src/                    # Source code
├── tests/                  # Tests
├── AGENTS.md              # This file
└── README.md              # Documentation
```

## 3. Golden Rules

### Do's
- Follow {domain_item['type']} best practices
- Write tests for new features
- Document public APIs

### Don'ts
- Avoid hardcoded values
- No secrets in code
- Keep files under 300 lines

## 4. Technology-Specific Guidelines

{_getTechStackGuidelines(domain_item.get('techStack', []))}

## 5. Testing Requirements

- Unit test coverage ≥ 80%
- Integration tests for critical paths
- E2E tests for user workflows

## 6. Common Patterns

[Document common patterns used in this domain]

## 7. References

- [Project Root AGENTS.md](../AGENTS.md)
- Tech Stack Documentation: [Add links]

---

Generated on: {datetime.now().strftime('%Y-%m-%d')}
"""
    return template


def _getTechStackGuidelines(tech_stack: list) -> str:
    """Generate tech-specific guidelines."""
    guidelines = []
    for tech in tech_stack:
        if "Next.js" in tech or "React" in tech:
            guidelines.append("- Use functional components with hooks")
            guidelines.append("- Implement proper error boundaries")
        elif "TypeScript" in tech:
            guidelines.append("- Enable strict mode")
            guidelines.append("- Avoid `any` type")
        elif "Shell" in tech:
            guidelines.append("- Use ShellCheck for linting")
            guidelines.append("- Follow Google Shell Style Guide")
    return "\\n".join(guidelines) if guidelines else "- Follow general best practices"
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Domain Definitions          │
├──────────────────────┬──────────────────────┤
│ Automatic Actions    │ Status               │
├──────────────────────┼──────────────────────┤
│ Create dashboard/    │ ✅ DONE              │
│ Create AGENTS.md     │ ✅ DONE              │
├──────────────────────┴──────────────────────┤
│ User Actions Required                       │
├─────────────────────────────────────────────┤
│ ℹ️ [MEDIUM] Guide file missing for frontend│
│    Path: .claude/skills/wm/rules/policies/ │
│          guide-frontend.md                  │
└─────────────────────────────────────────────┘
```

## Commands Reference

| Action | Command |
|--------|---------|
| Create domain dir | `mkdir -p {domain}` |
| Create AGENTS.md | See template generator in Remediation Logic |
| Batch create all | `for d in dash coll dock cli depl tray; do mkdir -p $d; done` |

## Post-Remediation Verification

```python
def verify(validation_result: ValidationResult, context: ValidationContext) -> bool:
    """
    Verify that remediation was successful.
    Re-run domains validation and check all items pass.
    """
    from pathlib import Path

    for item in validation_result["details"]:
        if item["status"] in ["FAIL", "WARN"]:
            domain_path = Path(context.projectRoot) / item["directory"]
            agents_file = Path(context.projectRoot) / item.get("agentsFile", f"{item['directory']}/AGENTS.md")

            if not domain_path.exists() or not agents_file.exists():
                return False
    return True
```

## Safety Checks

All remediation actions are safe:
- ✅ Creating directories (mkdir)
- ✅ Creating template files (from template)
- ❌ Modifying existing AGENTS.md (manual action required)
- ❌ Creating guide files (manual action required)

## References

- Validator: [../validators/domains-validator.md](../validators/domains-validator.md)
- Registry: [../registries/domains.yaml](../registries/domains.yaml)
- Schema: [../registries/domains-schema.md](../registries/domains-schema.md)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
- AGENTS.md Template: [../../templates/AGENTS.md](../../templates/AGENTS.md)
