---
title: Workflow Orchestration
impact: CRITICAL
impactDescription: Main entry point for project analysis
tags: [workflow]
used_by: [wm-setup]
migrated_from: analysis-rules-orchestrator.md
---

# Workflow Orchestration

**Impact: CRITICAL** - Main orchestrator for project analysis (context-based)

## Overview

This file serves as the **main entry point** for project analysis.
Orchestrates the 3-step workflow based on `/context` output.

**Key Functions**:
1. **parseContextOutput()**: Parse /context data for MCP, Skills, Agents
2. **runAnalysis()**: Main orchestrator for complete project analysis
3. **mapRelatedSkills()**: Map detected tech stack to skill references

**New Workflow (3 Steps)**:
```
Step 1: Parse /context output (MCP, Skills, Agents)
   ↓
Step 2: Detect tech stack (workflow-tech-detection.md)
   ↓
Step 3: Generate report (checklist + report)
```

**Dependencies**:
1. `../guides/project-detection.md` - Project state detection
2. `../guides/tech-detection.md` - Tech stack detection
3. `../guides/checklist-template.md` - Checklist items
4. `../guides/report-template.md` - Report format

## 1. Context Parsing Functions

### hasContextData()

**Purpose**: Check if user provided /context output.

```python
def hasContextData(user_input: str) -> bool:
    """
    Check if user input contains /context output data.

    Args:
        user_input: Raw user input string

    Returns:
        True if /context data detected, False otherwise
    """
    indicators = [
        "Context Usage",
        "MCP tools · /mcp",
        "Skills · /skills",
        "Custom agents · /agents",
        "mcp__"
    ]
    return any(indicator in user_input for indicator in indicators)
```

### parseContextOutput()

**Purpose**: Parse /context output into structured data.

```python
def parseContextOutput(context_output: str) -> dict:
    """
    Parse /context output into structured data.

    Args:
        context_output: Raw /context output string

    Returns:
        {
            "mcp_servers": ["serena", "playwright", "memory", ...],
            "skills": {
                "project": ["planner", "solve", ...],
                "plugin": ["frontend-design", ...]
            },
            "agents": {
                "project": ["0-user-question", ...],
                "user": ["project-guardian", ...],
                "plugin": ["feature-dev:code-architect", ...]
            },
            "memory_files": ["CLAUDE.md", ...],
            "model": "claude-opus-4-5-20251101",
            "tokens": {"used": 46000, "total": 200000}
        }
    """
    import re

    result = {
        "mcp_servers": [],
        "skills": {"project": [], "plugin": []},
        "agents": {"project": [], "user": [], "plugin": []},
        "memory_files": [],
        "model": "",
        "tokens": {"used": 0, "total": 0}
    }

    # 1. Extract model and tokens from header
    model_match = re.search(r'(claude-[a-z0-9\-]+)\s*·\s*(\d+)k/(\d+)k', context_output)
    if model_match:
        result["model"] = model_match.group(1)
        result["tokens"]["used"] = int(model_match.group(2)) * 1000
        result["tokens"]["total"] = int(model_match.group(3)) * 1000

    # 2. Extract MCP servers from tool names
    mcp_matches = re.findall(r'mcp__([a-zA-Z_]+)__', context_output)
    for raw_server in mcp_matches:
        server = normalizeServerName(raw_server)
        if server and server not in result["mcp_servers"]:
            result["mcp_servers"].append(server)

    # 3-5. Parse sections (Skills, Agents, Memory)
    # See full implementation in source

    return result
```

## 2. Skills Mapping Function

### mapRelatedSkills()

**Purpose**: Map detected tech stack to best-practices references.

```python
def mapRelatedSkills(tech_stack: list) -> dict:
    """Map detected tech stack to best-practices references."""
    skill_map = {
        "TypeScript": ".claude/skills/best-practices/rules/typescript.md",
        "React": ".claude/skills/best-practices/rules/react.md",
        "Next.js": ".claude/skills/best-practices/rules/frontend.md",
        "Python": ".claude/skills/best-practices/rules/python.md",
        "Go": ".claude/skills/best-practices/rules/go.md",
        "Rust": ".claude/skills/best-practices/rules/rust.md"
    }

    related_skills = {}
    missing_references = []

    for tech in tech_stack:
        if tech in skill_map:
            related_skills[tech] = skill_map[tech]
        else:
            missing_references.append(tech)

    return {
        "related_skills": related_skills,
        "missing_references": missing_references
    }
```

## 3. Main Orchestrator Function

### runAnalysis()

**Purpose**: Complete project analysis using /context data and tech detection.

```python
def runAnalysis(user_input: str) -> dict:
    """
    Orchestrates the 3-step analysis workflow.

    Returns:
        {
            "status": "SUCCESS|NEEDS_CONTEXT|ERROR",
            "context_data": {...},
            "project_state": {...},
            "tech_stack": [...],
            "related_skills": {...},
            "needs_user_input": bool
        }
    """
    # Step 1: Check for /context data
    if not hasContextData(user_input):
        return {
            "status": "NEEDS_CONTEXT",
            "guide_message": generateContextGuide()
        }

    # Parse /context data
    context_data = parseContextOutput(user_input)

    # Step 2: Detect project state and tech stack
    project_state = detectProjectState()
    tech_stack = detectTechStack()

    # Step 3: Map related skills
    skills_mapping = mapRelatedSkills(tech_stack)

    return {
        "status": "SUCCESS",
        "context_data": context_data,
        "project_state": project_state,
        "tech_stack": tech_stack,
        "related_skills": skills_mapping['related_skills'],
        "needs_user_input": False
    }
```

## When to Apply

- Initial project setup with wm-setup skill
- When user invokes /wm-setup command
- When /context output is provided for analysis

## References

- [../guides/project-detection.md](../guides/project-detection.md) - Project state detection
- [../guides/tech-detection.md](../guides/tech-detection.md) - Tech stack detection
- [../guides/checklist-template.md](../guides/checklist-template.md) - Checklist generation
- [../guides/report-template.md](../guides/report-template.md) - Report generation
