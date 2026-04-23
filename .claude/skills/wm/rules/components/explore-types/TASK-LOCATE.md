# TASK-LOCATE Type - Task Decomposition File Search

Exploration template dedicated to the planner-task agent. Locates implementation target files for PHASE decomposition.

---

## Purpose

Quickly identifies the locations of files needed to decompose a PHASE into Task units.

---

## When to Use

| Scenario | Use TASK-LOCATE? |
|----------|------------------|
| Locate PHASE-related files | Yes |
| Identify TDD target files | Yes |
| Search implementation files by layer | Yes |
| Search dependency files | Yes |
| Pattern analysis (implementation methods) | Use ANALYZE |
| Code quality evaluation | Use ASSESS |

---

## Process Mapping

| Process | Phase | Usage |
|---------|-------|-------|
| NEW_DEVELOPMENT | Task Planning | Determine new file locations per PHASE |
| MODIFICATION | Task Planning | Identify files to modify |
| BUG_FIX | Task Planning | Locate related test files |

---

## Template

```python
Task(
    subagent_type="Explore",
    description="LOCATE {phase_name} implementation targets",
    prompt="""
## Exploration Goal
Locate implementation target files for {phase_name} PHASE

## Search Targets
- Path: {layer_paths}
- Pattern: {entity_patterns}
- Keywords: {tdd_keywords}

## Expected Output
- List of files to implement (new/modify)
- Test file locations
- Dependency file list

## Layer Priority (Clean Architecture)
1. Domain Layer: src/domain/, src/entities/
2. Application Layer: src/application/, src/usecases/
3. Adapters Layer: src/adapters/, src/repositories/
4. Infrastructure Layer: src/infrastructure/, src/api/
5. Presentation Layer: src/components/, src/pages/

## TDD Mapping
- Test files: *.test.ts, *.spec.ts, __tests__/
- Mock files: __mocks__/, *.mock.ts
- Fixture files: __fixtures__/, *.fixture.ts

## Thoroughness Level: Quick

## Essential Files Output
5-10 files per layer
Format: path:line - layer/tdd_phase
""",
    model="haiku"
)
```

---

## Placeholder Guide

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{phase_name}` | PHASE name | "User Authentication" |
| `{layer_paths}` | Clean Architecture layer paths | "src/domain/, src/application/" |
| `{entity_patterns}` | Entity/component patterns | "User, Auth, Session" |
| `{tdd_keywords}` | TDD-related keywords | "test, spec, mock, repository" |

---

## Example: Locate User Management PHASE Files

```python
Task(
    subagent_type="Explore",
    description="LOCATE User Management implementation targets",
    prompt="""
## Exploration Goal
Locate implementation target files for User Management PHASE

## Search Targets
- Path: src/domain/, src/application/, src/components/
- Pattern: User, user, Account, Profile
- Keywords: entity, repository, service, usecase

## Expected Output
- List of files to implement (new/modify)
- Test file locations
- Dependency file list

## Layer Priority (Clean Architecture)
1. Domain Layer: src/domain/, src/entities/
2. Application Layer: src/application/, src/usecases/
3. Adapters Layer: src/adapters/, src/repositories/
4. Infrastructure Layer: src/infrastructure/, src/api/
5. Presentation Layer: src/components/, src/pages/

## TDD Mapping
- Test files: *.test.ts, *.spec.ts, __tests__/
- Mock files: __mocks__/, *.mock.ts
- Fixture files: __fixtures__/, *.fixture.ts

## Thoroughness Level: Quick

## Essential Files Output
5-10 files per layer
Format: path:line - layer/tdd_phase
""",
    model="haiku"
)
```

---

## Parallel Usage Pattern

When exploring multiple PHASEs simultaneously:

```python
# Parallel exploration per PHASE
phases = [
    {"name": "User Authentication", "paths": "src/domain/auth, src/services/auth"},
    {"name": "User Profile", "paths": "src/domain/profile, src/components/profile"},
    {"name": "Session Management", "paths": "src/domain/session, src/middleware"}
]

# Parallel execution (run_in_background=True)
explore_tasks = []
for phase in phases:
    task = Task(
        subagent_type="Explore",
        description=f"LOCATE {phase['name']} files",
        prompt=template.replace("{phase_name}", phase["name"])
                       .replace("{layer_paths}", phase["paths"]),
        model="haiku",
        run_in_background=True
    )
    explore_tasks.append(task)

# Wait for all explorations to complete
for task in explore_tasks:
    TaskOutput(task_id=task.agent_id, block=True)
```

---

## Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Thoroughness** | Quick | Fast file location |
| **Model** | haiku | Cost-efficient exploration |
| **Background** | Yes (for parallel) | Process multiple PHASEs simultaneously |
| **Files Analyzed** | 20-30 | 5-10 per layer |

---

## Differences from LOCATE.md

| Aspect | LOCATE | TASK-LOCATE |
|--------|--------|-------------|
| **Purpose** | General file location | For PHASE -> Task decomposition |
| **Layer Info** | No | Yes (Clean Architecture) |
| **TDD Mapping** | No | Yes (test, mock, fixture) |
| **Output Format** | path:line - role | path:line - layer/tdd_phase |
| **Parallel Pattern** | No | Yes (parallel per PHASE) |

---

## Notes

- `model="haiku"` required (cost efficiency)
- Use `run_in_background=True` for parallel execution
- Results are grouped by Layer order (Domain -> Infrastructure)
- Includes TDD Phase tagging (RED/GREEN/REFACTOR targets)
