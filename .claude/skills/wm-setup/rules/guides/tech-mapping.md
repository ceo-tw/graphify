---
title: Tech-Resource Mapping
impact: HIGH
impactDescription: Maps technologies to required Skills/Agents
tags: [guide]
used_by: [wm-setup]
migrated_from: analysis-rules-tech-mapping.md
---

# Tech-Resource Mapping

**Impact: HIGH** - Define mapping between detected technologies and required Skills/Agents

## Overview

This file defines data structures and functions to map detected technology stacks to required Claude Code resources (Skills and Agents).

**Key Functions**:
- `getTechSkillsMapping(tech_stack)`: Returns required best-practices Skills
- `getTechAgentsMapping(tech_stack)`: Returns required Agents (core + frontend)
- `isFrontendProject(tech_stack)`: Helper to detect frontend projects

## Data Structures

### TECH_SKILLS_MAP

```python
TECH_SKILLS_MAP = {
    # Primary Languages
    "Go": ["go.md"],
    "JavaScript": ["typescript.md"],
    "Python": ["python.md"],
    "Rust": ["rust.md"],
    "TypeScript": ["typescript.md"],

    # Frontend Frameworks
    "Next.js": ["react.md"],
    "React": ["react.md"],
    "Angular": [],  # Not yet supported
    "Vue.js": [],   # Not yet supported

    # Backend Frameworks
    "Django": ["python.md"],
    "FastAPI": ["python.md"],
    "Flask": ["python.md"],
    "Gin": ["go.md"],
    "Actix Web": ["rust.md"]
}
```

### TECH_AGENTS_MAP

```python
TECH_AGENTS_MAP = {
    "core": [
        "design",
        "planner-task",
        "dev-executor",
        "qa",
        "root-cause-finder",
        "bug-fixer",
        "knowledge-keeper"
    ],
    "frontend": [
        "playwright-test-planner",
        "playwright-test-generator",
        "playwright-test-healer"
    ]
}
```

### CORE_SKILLS

```python
CORE_SKILLS = [
    "code-quality",
    "codebase-explorer",
    "dev-status",
    "e2e-test",
    "research",
    "restore-context",
    "skill-creator",
    "solve",
    "wm",
    "worktree-manager"
]
```

### FRONTEND_FRAMEWORKS

```python
FRONTEND_FRAMEWORKS = [
    "Angular",
    "Next.js",
    "Nuxt",
    "React",
    "Svelte",
    "Vue.js"
]
```

## Functions

### getTechSkillsMapping()

```python
def getTechSkillsMapping(tech_stack: list) -> list:
    """
    Get required best-practices skills for detected tech stack.

    Example:
        >>> getTechSkillsMapping(["TypeScript", "React", "Next.js"])
        ["react.md", "typescript.md"]
    """
    skills = set()
    for tech in tech_stack:
        if tech in TECH_SKILLS_MAP:
            skills.update(TECH_SKILLS_MAP[tech])
    return sorted(list(skills))
```

### isFrontendProject()

```python
def isFrontendProject(tech_stack: list) -> bool:
    """
    Check if project uses frontend frameworks.

    Example:
        >>> isFrontendProject(["TypeScript", "React"])
        True
        >>> isFrontendProject(["Python", "FastAPI"])
        False
    """
    return any(fw in tech_stack for fw in FRONTEND_FRAMEWORKS)
```

### getTechAgentsMapping()

```python
def getTechAgentsMapping(tech_stack: list) -> dict:
    """
    Get required agents for detected tech stack.

    Example:
        >>> getTechAgentsMapping(["TypeScript", "React"])
        {
            "core": ["0-user-question", ..., "knowledge-keeper"],
            "frontend": ["playwright-test-planner", "playwright-test-generator", "playwright-test-healer"]
        }
    """
    result = {"core": TECH_AGENTS_MAP["core"], "frontend": []}

    if isFrontendProject(tech_stack):
        result["frontend"] = TECH_AGENTS_MAP["frontend"]

    return result
```

## Usage Examples

### TypeScript + React Project

```python
tech_stack = ["TypeScript", "React"]

skills = getTechSkillsMapping(tech_stack)
# Returns: ["react.md", "typescript.md"]

agents = getTechAgentsMapping(tech_stack)
# Returns: {"core": [...7 agents...], "frontend": [...3 playwright agents...]}
```

### Python Backend Project

```python
tech_stack = ["Python", "FastAPI"]

skills = getTechSkillsMapping(tech_stack)
# Returns: ["python.md"]

agents = getTechAgentsMapping(tech_stack)
# Returns: {"core": [...7 agents...], "frontend": []}
```

## Maintenance

### Adding New Technology

1. Add to `TECH_SKILLS_MAP` with skill files
2. Create best-practices reference (if applicable)
3. Update `FRONTEND_FRAMEWORKS` (if frontend)
4. Update tests

### Removing Deprecated Technology

1. Remove from `TECH_SKILLS_MAP`
2. Remove from `FRONTEND_FRAMEWORKS` (if applicable)
3. Archive best-practices reference
4. Update tests

## When to Apply

- During tech-resource mismatch detection
- When determining required skills for detected tech stack
- When deciding if Playwright agents are needed

## References

- [validation.md](./validation.md) - Uses mapping for validation
- [remediation.md](./remediation.md) - Uses mapping for remediation
