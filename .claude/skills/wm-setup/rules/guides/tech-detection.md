---
title: Tech Stack Detection
impact: HIGH
impactDescription: 38 detection rules across 5 categories
tags: [workflow]
used_by: [wm-setup]
migrated_from: analysis-rules-tech.md
---

# Tech Stack Detection

**Impact: HIGH** - Technology stack detection for project onboarding

## Overview

This file contains functions for detecting:
1. **Primary Language**: TypeScript, Python, Go, Rust, Java, etc.
2. **Frameworks**: Next.js, React, Express, Django, FastAPI, etc.
3. **Databases**: PostgreSQL, MySQL, MongoDB, ClickHouse, etc.
4. **Testing Frameworks**: Jest, Vitest, Pytest, BATS, etc.
5. **Build Tools**: npm, yarn, pnpm, cargo, go build, etc.

**Detection Rules**: 38 total rules across 5 categories

## Detection Matrix (38 Rules)

| # | Category | Technology | Detection Files | Detection Pattern |
|---|----------|------------|----------------|-------------------|
| 1-6 | Language | Node.js, TypeScript, Python, Go, Rust | Config files | File exists |
| 7-12 | Framework | React, Next.js, Vue, Angular, Express, NestJS | package.json | Dependency check |
| 13-15 | Framework | Django, FastAPI, Flask | requirements.txt | Pattern match |
| 16-17 | Framework | Gin, Actix Web | go.mod, Cargo.toml | Pattern match |
| 18-21 | Database | Prisma, Drizzle, Sequelize, SQLAlchemy | Config files | File exists |
| 22-26 | Testing | Vitest, Jest, Pytest, Go test, Rust test | Config files | File/pattern exists |
| 27-31 | Build | Vite, Webpack, Rollup, Turborepo, Nx | Config files | File exists |
| 32-38 | Package Manager | npm, yarn, pnpm, cargo, go, pip, poetry | Lock files | File exists |

## Key Detection Functions

### detectPrimaryLanguage()

```python
def detectPrimaryLanguage():
    """Detect primary programming language from config files."""
    detected = []

    if Glob(pattern="package.json").exists():
        detected.append("Node.js")
    if Glob(pattern="tsconfig.json").exists():
        detected.append("TypeScript")
    if Glob(pattern="requirements.txt").exists() or Glob(pattern="pyproject.toml").exists():
        detected.append("Python")
    if Glob(pattern="go.mod").exists():
        detected.append("Go")
    if Glob(pattern="Cargo.toml").exists():
        detected.append("Rust")

    return detected
```

### detectNodeFrameworks()

```python
def detectNodeFrameworks():
    """Analyze package.json dependencies for frameworks."""
    if not Glob(pattern="package.json").exists():
        return []

    detected = []
    package_json = Read(file_path="package.json").parse_json()
    deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}

    if "react" in deps: detected.append("React")
    if "next" in deps: detected.append("Next.js")
    if "vue" in deps: detected.append("Vue.js")
    if "@angular/core" in deps: detected.append("Angular")
    if "express" in deps: detected.append("Express")
    if "@nestjs/core" in deps: detected.append("NestJS")

    return detected
```

### detectTechStack()

```python
def detectTechStack():
    """Master function to detect complete technology stack."""
    tech_stack = []

    # Phase 1: Primary Language Detection
    tech_stack.extend(detectPrimaryLanguage())

    # Phase 2: Framework Detection (based on language)
    if "Node.js" in tech_stack:
        tech_stack.extend(detectNodeFrameworks())
    if "Python" in tech_stack:
        tech_stack.extend(detectPythonFrameworks())
    if "Go" in tech_stack:
        tech_stack.extend(detectGoFrameworks())
    if "Rust" in tech_stack:
        tech_stack.extend(detectRustFrameworks())

    # Phase 3-5: Database, Testing, Build tools
    tech_stack.extend(detectDatabaseTools())
    tech_stack.extend(detectTestingFrameworks())
    tech_stack.extend(detectBuildTools())

    # Deduplicate
    return list(dict.fromkeys(tech_stack))
```

## Integration Patterns

### Pattern 1: Language-First Detection

```python
languages = detectPrimaryLanguage()
if "TypeScript" in languages:
    Read(file_path=".claude/skills/best-practices/rules/typescript.md")
```

### Pattern 2: Best Practices Loading

```python
tech_stack = detectTechStack()
if "TypeScript" in tech_stack:
    Read(file_path=".claude/skills/best-practices/rules/typescript.md")
if "React" in tech_stack:
    Read(file_path=".claude/skills/best-practices/rules/react.md")
```

## When to Apply

- During initial project analysis in wm-setup workflow
- When mapping tech stack to best practices references
- When determining required agents (e.g., Playwright for frontend)

## References

- [../orchestration/workflow-orchestration.md](../orchestration/workflow-orchestration.md) - Main orchestrator
- [tech-mapping.md](./tech-mapping.md) - Tech to resource mapping
