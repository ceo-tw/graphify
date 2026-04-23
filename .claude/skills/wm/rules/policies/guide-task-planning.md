# Task Planning Guide

> **Source**: Migrated from `planning-guide-for-task/SKILL.md`
> **Purpose**: Guidelines for breaking PHASEs into executable Tasks with TDD workflow.
> **Used by**: planner-task agent (includes self-validation)

---

## Task Definition

A Task is a tactical unit of work with these characteristics:

| Attribute | Requirement |
|-----------|-------------|
| Duration | 15-60 minutes |
| Responsibility | Single, focused purpose |
| Executable | Can be completed independently |
| Testable | Has clear verification criteria |

## Task Decomposition Guidelines

### Task Sizing

| Size | Duration | Use Case |
|------|----------|----------|
| Small | 15-30 min | Single function, simple test |
| Medium | 30-45 min | Component, integration |
| Large | 45-60 min | Complex logic, multiple files |

### Decomposition Strategy

1. **Start from Test**
   - What needs to be tested?
   - Each test case → potential Task

2. **Follow Clean Architecture**
   - Domain → Application → Adapters → Infrastructure
   - Tasks follow layer order

3. **TDD Phases**
   - RED Tasks: Write failing tests
   - GREEN Tasks: Implement to pass
   - REFACTOR Tasks: Improve quality

## TDD Workflow

### RED Phase (Write Failing Test)

```
1. Identify test case
2. Write test file
3. Write test code
4. Run test → confirm FAIL
5. Commit test file
```

**Task Output**:
- Test file created
- Test fails for expected reason
- No implementation yet

### GREEN Phase (Make Test Pass)

```
1. Write minimal implementation
2. Run test → confirm PASS
3. No refactoring yet
4. Commit implementation
```

**Task Output**:
- Implementation exists
- Test passes
- Code may be rough

### REFACTOR Phase (Improve Quality)

```
1. Identify improvements
2. Refactor code
3. Run tests → confirm still PASS
4. Commit refactored code
```

**Task Output**:
- Clean code
- All tests still pass
- Ready for review

## Clean Architecture Task Patterns

### Domain Layer Tasks

| Task Type | Example |
|-----------|---------|
| Entity | Create User entity with validation |
| Value Object | Create Email value object |
| Domain Service | Create PasswordHasher service |
| Repository Interface | Define UserRepository port |

### Application Layer Tasks

| Task Type | Example |
|-----------|---------|
| Use Case | Implement CreateUser use case |
| DTO | Create CreateUserRequest DTO |
| Port | Define NotificationPort interface |
| Application Service | Create UserApplicationService |

### Adapter Layer Tasks

| Task Type | Example |
|-----------|---------|
| Controller | Create UserController |
| Repository Impl | Implement PostgresUserRepository |
| Presenter | Create UserJsonPresenter |
| Mapper | Create UserEntityMapper |

### Infrastructure Layer Tasks

| Task Type | Example |
|-----------|---------|
| Configuration | Setup database connection |
| Framework Integration | Configure dependency injection |
| External API | Implement EmailApiAdapter |

## Templates

Load the template below using Read tool when generating TASKS document:

- [TASKS Template](template-tasks.md) - Use when generating TASKS document

## References (MUST)

> **These references are REQUIRED for Task decomposition.**

- [PRD to TASK Mapping](guide-prd-to-task-mapping.md) - **MUST** use for field conversion rules
- [Time Allocation Rules](guide-time-allocation.md) - **MUST** use for PHASE time distribution
- [Clean Architecture Reference](guide-clean-architecture.md) - Layer definitions and inference patterns

## Task Tool Integration

Use Task tools (TaskCreate, TaskGet, TaskUpdate, TaskList) for progress tracking:

### Task Creation

```python
TaskCreate(
    subject="TASK-0101: Write User entity test",
    description="Create test file for User entity with validation cases.",
    activeForm="Writing User entity test...",
    metadata={
        "feature": feature_name,
        "phase": "PHASE-1",
        "tdd_stage": "RED",
        "layer": "domain"
    }
)
```

### Task Status Updates (CRITICAL: Staleness Prevention)

**RULE**: Always call `TaskGet` before `TaskUpdate` to read latest state.

```python
# ✅ CORRECT Pattern
current = TaskGet(taskId=task_id)
if current.status == "pending":
    TaskUpdate(taskId=task_id, status="in_progress")

# ... do task work ...

current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="completed")

# ❌ WRONG Pattern (Never do this)
TaskUpdate(taskId=task_id, status="completed")  # Stale!
```

### Task Metadata Schema

```python
metadata = {
    "feature": "user-auth",      # Feature name for scoped cleanup
    "phase": "PHASE-1",          # PHASE identifier
    "tdd_stage": "RED|GREEN|REFACTOR",  # TDD stage
    "layer": "domain|application|adapter|infrastructure",
    "planning": True             # For planning-only tasks
}
```

> **Full Guide**: [Task Tool Planning Guide](../components/task-tool-planning-guide.md)

## Task Dependencies

### Dependency Rules

1. **Same Layer**: RED → GREEN → REFACTOR
2. **Cross Layer**: Inner layer first (Domain before Application)
3. **Same Feature**: Foundation before extension

### Dependency Notation

```
TASK-001 (independent)
    └── TASK-002 (depends on 001)
        └── TASK-003 (depends on 002)

TASK-004 (independent, parallel OK)
```

## Definition of Done

Each Task must satisfy:

### Mandatory Criteria
- [ ] All acceptance criteria met
- [ ] Test exists and passes (for GREEN/REFACTOR)
- [ ] Test fails correctly (for RED)
- [ ] Code follows project conventions
- [ ] No linting errors

### Quality Criteria
- [ ] Function/class documented (JSDoc/docstring)
- [ ] Edge cases handled
- [ ] Error handling present

### Verification
```bash
# Run specific test
bun run test -- --grep "TASK-001"

# Check lint
bun run lint

# Type check
bun run type-check
```

## Common Anti-patterns

| Anti-pattern | Better Approach |
|--------------|-----------------|
| Task too large (>1h) | Split into smaller tasks |
| Skipping RED phase | Always write test first |
| GREEN with extras | Minimal code only |
| REFACTOR without tests | Tests must pass throughout |
| Hidden dependencies | Document all prerequisites |
| No acceptance criteria | Define clear completion |

---

## MCP Tool Usage Guide

### Serena MCP - Code Structure Analysis

Use symbol-level analysis instead of Grep for accurate dependency identification during Task decomposition:

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `get_symbols_overview` | List classes/functions in file | When loading context |
| `find_symbol` | Search specific symbol definition | When identifying modification targets |
| `find_referencing_symbols` | Analyze reference relationships | When determining impact scope |

```python
# Example: Understand file structure
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/domain/entities/user.ts",
    depth=1
)
```

### Memory MCP - Task Dependency Graph

Automatically register Tasks to knowledge graph for dependency management:

```python
# Register Task entity
mcp__memory__create_entities(entities=[
    {
        "name": "TASK-001",
        "entityType": "Task",
        "observations": ["phase: PHASE_1", "tdd_stage: RED", "layer: domain"]
    }
])

# Register dependency relationship
mcp__memory__create_relations(relations=[
    {"from": "TASK-002", "to": "TASK-001", "relationType": "depends_on"}
])

# Query independent Tasks (can run in parallel)
mcp__memory__search_nodes(query="Task independent")
```

### Pattern Memory Usage

Store project structure analysis results in memory for reuse:

```python
# Save pattern
mcp__plugin_serena_serena__write_memory(
    memory_file_name="task-patterns",
    content="..."
)

# Load pattern
mcp__plugin_serena_serena__read_memory(
    memory_file_name="task-patterns"
)
```

### Tool Usage Checklist

- [ ] Use `get_symbols_overview` to understand code structure when loading context
- [ ] Use `create_entities` to register Tasks to graph when creating
- [ ] Use `create_relations` to register relationships when setting dependencies
- [ ] Use `write_memory` to save patterns after first decomposition
- [ ] Use `read_memory` to load patterns for subsequent decompositions
