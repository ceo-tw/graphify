# Explore Types Reference

Unified reference for all Explore agent invocation types.

---

## Type Overview

| Type | Purpose | Thoroughness | Background | Files Analyzed |
|------|---------|--------------|------------|----------------|
| **LOCATE** | File/structure location | Quick | Optional | 15-20 |
| **ANALYZE** | Pattern/implementation analysis | Medium | Yes | 30-50 |
| **COLLECT** | Data/statistics collection | Quick | Optional | 15-30 |
| **ASSESS** | Impact range assessment | Medium | Yes | 30-50 |

**Model**: Always `haiku` (exception: `sonnet` for architecture deep-dive only)

---

## When to Use

| Scenario | Type |
|----------|------|
| Find specific file by name | LOCATE |
| Find class/function location | LOCATE |
| Directory structure overview | LOCATE |
| Understand implementation pattern | ANALYZE |
| Analyze code flow/structure | ANALYZE |
| Module relationship analysis | ANALYZE |
| Gather test/config files | COLLECT |
| Count/categorize files | COLLECT |
| Collect metrics data | COLLECT |
| Evaluate change impact | ASSESS |
| Identify dependencies | ASSESS |
| Find affected tests | ASSESS |

---

## Process Mapping

| Process | Primary Type | Secondary Type |
|---------|--------------|----------------|
| NEW_DEVELOPMENT | LOCATE | ANALYZE |
| MODIFICATION | LOCATE | ASSESS |
| BUG_FIX (Complex) | LOCATE | ANALYZE |
| INQUIRY | ANALYZE | - |
| REPORT | COLLECT | - |

---

## Common Template Structure

All types use this prompt structure:

```python
Task(
    subagent_type="Explore",
    description="{brief_description}",
    prompt="""
## Exploration Goal
{goal_line}

## Search Targets
- Path: {search_paths}
- Pattern: {file_patterns}
- Keywords: {keywords}

## Expected Output
- {output_item_1}
- {output_item_2}
- {output_item_3}

## Thoroughness Level: {thoroughness}

## Essential Files Output
5-10 core files
Format: path:line - role/purpose
""",
    model="haiku",
    run_in_background={use_background}  # True for ANALYZE/ASSESS
)
```

### Placeholder Guide

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{brief_description}` | 3-5 word task description | "Locate auth domain files" |
| `{goal_line}` | Type-specific goal (see per-type below) | "Locate files related to {target}" |
| `{search_paths}` | Directory paths to search | "src/domain/, src/adapters/" |
| `{file_patterns}` | File name patterns | "auth, login, User, *.service.ts" |
| `{keywords}` | Code keywords to search | "authenticate, session, JWT" |

---

## Per-Type Details

### LOCATE

- **Goal line**: `Locate files and structure related to {target}`
- **Expected Output**: Key file locations, related directory structure, entry point files
- **Thoroughness**: Quick
- **Background**: Optional (usually completes quickly)
- **Notes**: Use ANALYZE if you need to understand patterns or implementation

<details>
<summary>Example: Locate User Domain Files</summary>

```python
Task(
    subagent_type="Explore",
    description="Locate user domain files",
    prompt="""
## Exploration Goal
Locate files related to the user domain

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
</details>

### ANALYZE

- **Goal line**: `Analyze implementation patterns and structure of {target}`
- **Expected Output**: Patterns/methods in use, code flow, key component relationships
- **Thoroughness**: Medium
- **Background**: Yes (`run_in_background=True`, may take 30s-1m)
- **Notes**: For architecture deep-dive (Very thorough), consider `sonnet` as exception

<details>
<summary>Example: Analyze Authentication Patterns</summary>

```python
Task(
    subagent_type="Explore",
    description="Analyze auth patterns",
    prompt="""
## Exploration Goal
Analyze authentication patterns and implementation methods

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
</details>

### COLLECT

- **Goal line**: `Collect data related to {target}`
- **Expected Output**: File list, categorization by type, counts/statistics
- **Thoroughness**: Quick
- **Background**: Optional (usually completes quickly)
- **Notes**: Focus on gathering data, not analyzing patterns. Combine with Bash for metrics.

<details>
<summary>Example: Collect Test Coverage Data</summary>

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
- Identify areas with missing coverage

## Thoroughness Level: Quick

## Essential Files Output
5-10 test files representing coverage patterns
Format: path:line - test type and scope
""",
    model="haiku"
)
```
</details>

### ASSESS

- **Goal line**: `Assess impact scope when changing {target}`
- **Expected Output**: Directly affected files, indirect dependencies, test file associations
- **Thoroughness**: Medium
- **Background**: Yes (`run_in_background=True`, may take 30s-1m)
- **Notes**: Always include "import", "require", "dependency" in keywords

<details>
<summary>Example: Assess User Entity Change Impact</summary>

```python
Task(
    subagent_type="Explore",
    description="Assess User change impact",
    prompt="""
## Exploration Goal
Assess impact scope when changing User entity

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
</details>
