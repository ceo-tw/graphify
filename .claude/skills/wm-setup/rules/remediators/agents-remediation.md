---
title: Agents Remediation
impact: HIGH
impactDescription: Guides installation of missing agents
tags: [remediation, agents]
used_by: [validation-orchestrator]
validator: validators/agents-validator.md
order: 3
canAutoFix: partial
---

# Agents Remediation

**Impact: HIGH** - Guides installation of missing agents

## Overview

This remediator handles missing agent issues from agents-validator.
Provides installation guidance; agents can be copied from templates.

## Remediation Logic

```python
def remediate(
    validation_result: ValidationResult,
    context: ValidationContext,
    mode: str = "auto"
) -> RemediationResult:
    """
    Provide agent installation guidance.

    Partial auto-fix: Can copy from templates if available
    """
    import shutil
    from pathlib import Path

    actions_executed = []
    actions_required = []

    template_base = Path(context.projectRoot) / ".claude/templates/agents"

    for item in validation_result["details"]:
        if item["status"] not in ["FAIL", "WARN"]:
            continue

        agent_name = item["name"]
        agent_path = Path(context.projectRoot) / item["path"]
        template_path = template_base / f"{agent_name}.md"

        # Check if template exists
        if template_path.exists() and mode in ["auto", "interactive"]:
            try:
                agent_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(template_path, agent_path)
                actions_executed.append({
                    "id": f"install-{item['id']}",
                    "type": "create",
                    "target": item["path"],
                    "description": f"Installed agent from template: {agent_name}",
                    "status": "DONE"
                })
            except Exception as e:
                actions_executed.append({
                    "id": f"install-{item['id']}",
                    "type": "create",
                    "target": item["path"],
                    "description": f"Failed to install agent: {agent_name}",
                    "status": "FAILED",
                    "error": str(e)
                })
        else:
            actions_required.append({
                "id": f"manual-{item['id']}",
                "priority": "HIGH" if item["priority"] in ["CRITICAL", "HIGH"] else "MEDIUM",
                "description": f"Install agent: {agent_name}",
                "command": f"# Copy {agent_name}.md to .claude/agents/",
                "link": f"See category: {item.get('category', 'unknown')}"
            })

    return {
        "moduleId": "agents",
        "moduleName": "Agents",
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

## Agent File Template

```markdown
# {agent-name}

## Description
{Brief description of what this agent does}

## Capabilities
- Capability 1
- Capability 2

## Tools Available
- Tool 1
- Tool 2

## Usage
This agent is invoked by: {invokedBy}
This agent invokes: {invokes}
```

## Category-Based Guidance

### Core Development Agents

| Agent | Purpose | Template |
|-------|---------|----------|
| design | Architecture design | Required |
| planner-task | Task breakdown | Required |
| dev-executor | TDD implementation | Required |
| qa | Quality assurance | Required |

### Bug Resolution Agents

| Agent | Purpose | Template |
|-------|---------|----------|
| root-cause-finder | 5 Whys analysis | Required |
| bug-fixer | TDD bug fix | Required |
| knowledge-keeper | Document resolution | Optional |

### E2E Testing Agents

| Agent | Purpose | Dependency |
|-------|---------|------------|
| playwright-test-planner | Test planning | playwright MCP |
| playwright-test-generator | Test generation | playwright MCP |
| playwright-test-healer | Test debugging | playwright MCP |

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔧 Remediation: Agents                      │
├──────────────────────┬──────────────────────┤
│ Automatic Actions    │ Status               │
├──────────────────────┼──────────────────────┤
│ Install dev-executor │ ✅ DONE              │
│ Install qa           │ ✅ DONE              │
├──────────────────────┴──────────────────────┤
│ User Actions Required                       │
├─────────────────────────────────────────────┤
│ ⚠️ [HIGH] Install agent: design              │
│    Category: core-development               │
│    Required for: Architecture design        │
│                                             │
│ ℹ️ [MEDIUM] Install agent: playwright-*    │
│    Requires: playwright MCP server          │
└─────────────────────────────────────────────┘
```

## Dependency Hierarchy

```python
def getAgentHierarchy(agent_name: str) -> dict:
    """
    Get agent invocation hierarchy.

    Helps users understand which agents need to be installed together.
    """
    hierarchy = {
        "design": {
            "invokes": [],
            "invokedBy": ["wm skill"]
        },
        "planner-task": {
            "invokes": [],
            "invokedBy": ["wm skill"]
        },
        # ... more agents
    }
    return hierarchy.get(agent_name, {})
```

## Batch Installation

```bash
# Install all core-development agents
cp templates/agents/{design,planner-task,dev-executor,qa}.md .claude/agents/

# Install all bug-resolution agents
cp templates/agents/{root-cause-finder,bug-fixer,knowledge-keeper}.md .claude/agents/

# Install all e2e-testing agents
cp templates/agents/playwright-test-{planner,generator,healer}.md .claude/agents/
```

## References

- Validator: [../validators/agents-validator.md](../validators/agents-validator.md)
- Registry: [../registries/agents.yaml](../registries/agents.yaml)
- Interface: [_remediation-interface.md](./_remediation-interface.md)
