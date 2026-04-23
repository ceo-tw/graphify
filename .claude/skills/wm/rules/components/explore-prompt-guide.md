# Explore Prompt Guide Component

This guide provides structured templates for effective Explore agent invocation, ensuring consistent and efficient codebase exploration.

---

## Explore Type System

The Explore agent uses 4 distinct types based on exploration purpose:

| Type | Purpose | Thoroughness | Primary Use |
|------|---------|--------------|-------------|
| **LOCATE** | File/structure location | Quick | Find specific files |
| **ANALYZE** | Pattern/implementation analysis | Medium | Understand code patterns |
| **COLLECT** | Data/statistics collection | Quick | Gather files for reports |
| **ASSESS** | Impact range assessment | Medium | Evaluate change impact |

### Type Selection Guide

```
What is your exploration goal?
├─ Find specific files/structures → LOCATE
├─ Understand patterns/implementation → ANALYZE
├─ Collect files/data for report → COLLECT
└─ Assess change impact/dependencies → ASSESS
```

### Type Reference

> **Full details**: See [explore-types-reference.md](explore-types/explore-types-reference.md) for templates, examples, and configuration per type.

---

## Process-to-Type Mapping

| Process | Primary Type | Secondary Type |
|---------|--------------|----------------|
| NEW_DEVELOPMENT | LOCATE | ANALYZE |
| MODIFICATION | LOCATE | ASSESS |
| BUG_FIX (Complex) | LOCATE | ANALYZE |
| INQUIRY | ANALYZE | - |
| REPORT | COLLECT | - |
| CLEANUP | LOCATE | - |

---

## Structured Prompt Template

When invoking the Explore agent, use this structured format:

```python
Task(
    subagent_type="Explore",
    description="<Brief 3-5 word description>",
    prompt="""
## Exploration Goal
<Clear exploration purpose statement>

## Search Targets
- Path: <search paths, e.g., src/, tests/>
- Pattern: <file patterns, e.g., auth, login, *.test.ts>
- Keywords: <code keywords, e.g., authentication, JWT>

## Expected Output
- <expected result 1>
- <expected result 2>
- <expected result 3>

## Thoroughness Level: <Quick|Medium>

## Essential Files Output
Include 5-10 most important files.
Format: path:line - brief description
""",
    model="haiku"
)
```

### Template Sections Explained

| Section | Purpose | Example |
|---------|---------|---------|
| **Exploration Goal** | Clear exploration purpose | "Locate auth-related files" |
| **Search Targets** | Define search scope | Path: src/auth/, Pattern: login, session |
| **Expected Output** | Define output format | "File locations", "Pattern summary" |
| **Thoroughness Level** | Set exploration depth | Quick, Medium |
| **Essential Files** | Request key files | 5-10 files with descriptions |

---

## Model Selection: haiku Fixed

**All Explore types use `model="haiku"` by default.**

### Rationale

| Factor | haiku | sonnet |
|--------|-------|--------|
| **Cost** | ~10x cheaper | Expensive |
| **Speed** | Fast | Slower |
| **Sufficiency** | Sufficient for exploration | Overkill for most cases |
| **Predictability** | Fixed model = predictable cost | Variable cost |

### Exception (Very Thorough)

Only consider `model="sonnet"` for architecture deep-dive with Very thorough level:

```python
# EXCEPTION: Architecture deep-dive only
Task(
    subagent_type="Explore",
    description="Analyze system architecture",
    prompt="""
## Exploration Goal
Understand overall system architecture and verify layer separation
...
## Thoroughness Level: Very thorough
""",
    model="sonnet",  # Exception for deep architecture analysis
    run_in_background=True
)
```

---

## Thoroughness Level Details

| Level | Files Analyzed | Duration | Use For |
|-------|----------------|----------|---------|
| **Quick** | 15-30 | < 30s | LOCATE, COLLECT |
| **Medium** | 30-50 | 30s-1m | ANALYZE, ASSESS |
| **Very thorough** | 50+ | 1-3m | Architecture deep-dive (exception) |

### Quick
- Fast file enumeration
- Basic pattern matching
- Shallow directory traversal
- Best for: File location, data collection

### Medium
- Moderate depth analysis
- Code structure examination
- Dependency mapping
- Best for: Pattern analysis, impact assessment

### Very thorough (Exception)
- Deep architectural analysis
- Cross-file relationship tracing
- Use `model="sonnet"` only when necessary

---

## Background Execution

Use `run_in_background=True` based on type:

| Type | Background | Rationale |
|------|------------|-----------|
| LOCATE | Optional | Usually completes quickly |
| ANALYZE | **Yes** | May take 30s-1m |
| COLLECT | Optional | Usually completes quickly |
| ASSESS | **Yes** | May take 30s-1m |

---

## Essential Files Output Format

> **Reference**: This format aligns with [codebase-explorer](../../codebase-explorer/SKILL.md#essential-files-output-adopted-from-feature-dev) for consistency.

### Markdown Format (Preferred)

```markdown
## Essential Files (5-10)

1. **src/domain/entities/User.ts:45** - Core entity definition
2. **src/application/usecases/CreateUser.ts:12** - Main use case
3. **src/adapters/controllers/UserController.ts:30** - API endpoint
4. **src/domain/ports/UserRepository.ts:8** - Repository interface
5. **src/infrastructure/db/UserRepositoryImpl.ts:15** - DB implementation

## Related Files (8)
- src/application/dto/CreateUserDTO.ts
- src/domain/value-objects/Email.ts
- tests/domain/entities/User.test.ts

Total analyzed: 42 files
```

### Selection Criteria

| Criteria | Include? |
|----------|----------|
| Contains core business logic | Yes (priority 1) |
| Defines key interfaces/types | Yes (priority 2) |
| Entry point for feature | Yes (priority 1-2) |
| Configuration affecting feature | Yes (priority 3) |
| Test file for core component | Yes (priority 3) |
| Utility/helper (general) | No (unless specifically used) |
| External library code | No |

### Guidelines

- **Essential files**: 5-10 files (most important)
- **Related files**: Up to 20 files (contextually relevant)
- **Include line numbers**: Helps with quick navigation
- **Brief descriptions**: One line explaining the file's role

---

## Quick Reference Examples

### LOCATE Example

```python
Task(
    subagent_type="Explore",
    description="Locate user domain files",
    prompt="""
## Exploration Goal
Locate user domain related files

## Search Targets
- Path: src/domain/, src/application/
- Pattern: user, User, account
- Keywords: entity, repository, usecase

## Expected Output
- User entity location
- User repository interface
- User-related use cases

## Thoroughness Level: Quick

## Essential Files Output
5-10 core files for User domain
Format: path:line - purpose
""",
    model="haiku"
)
```

### ANALYZE Example

```python
Task(
    subagent_type="Explore",
    description="Analyze auth patterns",
    prompt="""
## Exploration Goal
Analyze authentication patterns and implementation approach

## Search Targets
- Path: src/
- Pattern: auth, login, session
- Keywords: authentication, JWT, OAuth

## Expected Output
- Authentication methods in use
- Key file locations
- Implementation pattern summary

## Thoroughness Level: Medium

## Essential Files Output
5-10 most important files
Format: path:line - role
""",
    model="haiku",
    run_in_background=True
)
```

### COLLECT Example

```python
Task(
    subagent_type="Explore",
    description="Collect test files",
    prompt="""
## Exploration Goal
Collect test files for test coverage analysis

## Search Targets
- Path: tests/, **/*.test.ts, **/*.spec.ts
- Pattern: test, spec, coverage
- Keywords: describe, it, expect

## Expected Output
- Complete test file list
- Classification by test type (unit, integration, e2e)
- Identify coverage gap areas

## Thoroughness Level: Quick

## Essential Files Output
5-10 test files representing coverage patterns
Format: path:line - test type and scope
""",
    model="haiku"
)
```

### ASSESS Example

```python
Task(
    subagent_type="Explore",
    description="Assess User change impact",
    prompt="""
## Exploration Goal
Assess impact scope when modifying User entity

## Search Targets
- Path: src/, tests/
- Pattern: user, User, account
- Keywords: import User, UserService, UserRepository

## Expected Output
- Files directly referencing User
- Services depending on User
- Related test files

## Thoroughness Level: Medium

## Essential Files Output
5-10 affected files
Format: path:line - direct/indirect dependency
""",
    model="haiku",
    run_in_background=True
)
```

---

## Integration with WM Processes

This guide is referenced by:
- [INQUIRY Process](../processes/inquiry.md) - Uses ANALYZE type
- [REPORT Process](../processes/report.md) - Uses COLLECT type
- [Development Process](../processes/development-process.md) - Uses LOCATE, ANALYZE types
- [BUG_FIX Complex](../processes/bug-fix-complex.md) - Uses LOCATE, ANALYZE types
- [WM SKILL.md](../../SKILL.md) - Main file exploration rules
