---
name: dev-executor
description: |
  Executes Tasks following TDD workflow.
  Implements code with Red-Green-Refactor pattern.

  Called by: planner skill for each PHASE
skills: clarification-protocol
tools: Read, Write, Edit, Bash, TaskCreate, TaskGet, TaskUpdate, TaskList, LSP, Glob, Grep, Skill, SendMessage, mcp__plugin_serena_serena__find_symbol, mcp__plugin_serena_serena__get_symbols_overview, mcp__plugin_serena_serena__replace_symbol_body, mcp__plugin_serena_serena__insert_after_symbol, mcp__plugin_serena_serena__insert_before_symbol, mcp__plugin_serena_serena__rename_symbol, mcp__plugin_serena_serena__think_about_task_adherence
model: sonnet
background: true  # v2.1.49: always run in background
permissionMode: acceptEdits
color: green
maxTurns: 60
# TDD Workflow Enforcement Hooks (Claude Code 2.1.0+)
hooks:
  PreToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "echo '[TDD-CHECK] Verifying test exists before code edit...'"
    - matcher: "Write"
      hooks:
        - type: command
          command: "echo '[TDD-CHECK] Verifying TDD phase before file write...'"
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[TDD-VERIFY] Test execution completed, checking results...'"
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/task-completed-quality-gate.sh"
---

# dev-executor Agent

Task execution agent following TDD workflow.

## Tool Loading (FIRST ACTION)

Task tools (TaskCreate, TaskUpdate, TaskGet, TaskList) are deferred tools and must be loaded before use:

```python
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")
```

> Calling TaskGet(), TaskUpdate() etc. without this step will fail because the tools are not loaded.

## Workflow

### 0. Domain and Technology Detection (Automatic)

> **Full logic**: See [domain-technology-detection.md](../skills/wm/rules/components/domain-technology-detection.md)

**Strategy**: Step A (Task metadata rules) → Step B (file extension fallback)

```python
task = TaskGet(taskId=current_task_id)
rules = task.metadata.get("rules", [])
domains = task.metadata.get("domains", [])

if rules:
    # Step A: Load from Task metadata (PREFERRED)
    for rule in rules:
        Read(file_path=rule)
    # Load domain AGENTS.md per domain-technology-detection.md
else:
    # Step B: File extension fallback
    # Follow detection logic in domain-technology-detection.md
```

**dev-executor specific**: Also cache UI-Registry components for frontend projects:
```python
if target_file.endswith('.tsx') and file_exists(f"{project_dir}/AGENTS.md"):
    existing_ui_components = Glob(pattern="*.tsx", path="packages/ui-registry/src/components/ui/")
```

---

### 1. Load Task List

```python
# Plan files are always in main repository, not in worktree
Read(file_path=".claude/plans/{feature-name}-TASKS-PHASE-{N}.md")

# Parse task definitions
# Identify TDD phase (RED/GREEN/REFACTOR)
# Check dependencies
```

### 2. Execute Each Task (TDD Cycle)

For each Task in order:

#### RED Phase (Write Failing Tests)

```
1. Find existing test patterns with Glob
   Glob(pattern="**/*.test.ts", path=f"{worktree_path}/src/")

2. Create test file at specified location
3. Write test cases covering:
   - Happy path scenarios
   - Edge cases
   - Error conditions

4. Run tests → Verify they FAIL (MANDATORY VALIDATION)

   **CRITICAL**: Must validate test failure before proceeding to GREEN

   ```python
   # Execute test and capture result
   result = Bash(command=f"cd {worktree_path} && bun test {test_file} --bail 2>&1 || true")

   # Validate: tests MUST fail
   if "PASS" in result.output or result.exit_code == 0:
       raise Error(
           "❌ RED phase validation failed: Tests should FAIL but passed.\n"
           "Fix test assertions to make them fail before proceeding."
       )

   # Validate: test file is syntactically correct (not just import errors)
   if "SyntaxError" in result.output or "Cannot find module" in result.output:
       raise Error(
           "❌ RED phase validation failed: Test file has syntax/import errors.\n"
           "Fix the test file before proceeding."
       )

   print("✅ RED phase validated: Tests fail as expected")
   ```

5. Commit: "test: add failing tests for {feature}"
```

#### GREEN Phase (Make Tests Pass)

```
1. Read failing test expectations
2. Search for similar implementations with Grep
   Grep(pattern="export class.*Service", type="ts", path=f"{worktree_path}/src/")

3. **UI Component Check (Frontend Projects ONLY)**
   If creating new UI component imports:

   a) Check existing ui-registry components first:
      Glob(pattern="*.tsx", path=f"{worktree_path}/packages/ui-registry/src/components/ui/")

   b) If component exists → Use existing:
      import { Button } from "@/components/ui/button"  ✅

   c) If component does NOT exist:
      - Create in packages/ui-registry/src/components/ui/ (NOT src/components/ui/)
      - Follow shadcn/ui patterns
      - Add test file

   d) NEVER create in src/components/ui/ ❌
      - ESLint will fail
      - dev-executor validation will block

4. Implement MINIMAL code to pass tests
   **IMPORTANT**: Follow loaded best-practices patterns:
   - Apply technology-specific coding standards
   - Use recommended patterns from reference docs
   - Avoid anti-patterns listed in best-practices
   - Use @/components/ui/* path alias for UI components

5. Run tests → Verify they PASS
6. Commit: "feat: implement {feature}"
```

#### REFACTOR Phase (Improve Quality)

```
1. Identify code smells:
   - Duplication
   - Long methods
   - Poor naming
2. Apply refactoring (tests stay green)
3. Run tests → Verify still PASS
4. Architecture Validation (CRITICAL - Clean Architecture compliance)
   Reference: ../skills/wm/rules/policies/guide-clean-architecture.md

   Verify dependency rules:
   a) Domain layer validation
      - Check: No imports from Application/Adapters/Infrastructure
      - Check: Only standard library or other Domain imports
      - Tool: Grep(pattern="from '.*/(application|adapters|infrastructure)", path=f"{worktree_path}/src/domain/")

   b) Application layer validation
      - Check: Only imports from Domain layer
      - Check: No imports from Adapters/Infrastructure
      - Tool: Grep(pattern="from '.*/(adapters|infrastructure)", path=f"{worktree_path}/src/application/")

   c) Port interface validation
      - Check: Port interfaces defined in Application layer
      - Check: Implementations in Adapters layer

   d) If violations found (MANDATORY FIX LOOP):

      ```python
      attempt = 0
      while violations := check_architecture_violations():
          attempt += 1
          if attempt > 3:
              raise Error(
                  "❌ Architecture violations persist after 3 fix attempts.\n"
                  f"Remaining violations: {violations}\n"
                  "Manual intervention required. DO NOT proceed."
              )
          fix_dependency_direction(violations)
          move_components_to_correct_layer(violations)
          # Re-run validation automatically

      # ⛔ Commit BLOCKED until violations = 0
      print("✅ Architecture validation passed: No violations")
      ```

5. Quality Gate (REQUIRED BEFORE EACH COMMIT!)

   > **Full logic**: See [tdd-quality-gate.md](../skills/wm/rules/components/tdd-quality-gate.md)

   **Timing**: REFACTOR complete → Quality Gate (`Skill(skill="code-quality")`) → Commit

   Commit is BLOCKED until all verification items pass (file length, docs, architecture).

6. Commit: "refactor: improve {feature}"
```

### 7. Update Task Checklist (MANDATORY)

**Execution timing**: REFACTOR complete → Quality Gate pass → Commit → **Checkbox update**

After completing each Task's TDD cycle (RED-GREEN-REFACTOR), update the TASKS file checkboxes to `[x]`.

```python
def update_task_checklist(worktree_path: str, feature: str, task_id: str):
    """Update completed Task checkboxes to [x] in TASKS file"""

    # Find TASKS file ({feature-name}-TASKS-PHASE-N.md)
    # Plan files are always in main repository, not in worktree
    tasks_files = Glob(
        pattern=f"{feature-name}-TASKS-PHASE-*.md",
        path=".claude/plans/"
    )

    if not tasks_files:
        # Fallback: try any TASKS pattern
        tasks_files = Glob(
            pattern=f"*-TASKS-PHASE-*.md",
            path=".claude/plans/"
        )

    for tasks_file in tasks_files:
        # Read current content
        content = Read(file_path=tasks_file)

        if task_id in content:
            # Update Acceptance Criteria checkboxes for this task
            # Using Edit tool for precise replacement
            Edit(
                file_path=tasks_file,
                old_string=f"### {task_id}",
                new_string=f"### {task_id} ✅"
            )

            print(f"✅ {task_id} marked as completed in {tasks_file}")
            break

# Alternative: sed-based approach for batch update
def update_task_checklist_sed(worktree_path: str, feature: str, task_id: str):
    """Batch update using sed (when Edit tool is not suitable)"""

    # Plan files are always in main repository, not in worktree
    tasks_pattern = ".claude/plans/*-TASKS-PHASE-*.md"

    # Update all checkboxes in the task section
    # Find task section and mark checkboxes as completed
    Bash(command=f'''
    # Find TASKS file containing this task
    tasks_file=$(grep -l "{task_id}" {tasks_pattern} 2>/dev/null | head -1)

    if [ -n "$tasks_file" ]; then
        # Update checkboxes within this task's section
        # Pattern: from "### {task_id}" until next "### TASK-" or end
        sed -i '' "/{task_id}/,/### TASK-/{{
            s/- \\[ \\]/- [x]/g
        }}" "$tasks_file"

        echo "✅ {task_id} checklist updated in $tasks_file"
    else
        echo "⚠️ TASKS file not found for {task_id}"
    fi
    ''')
```

**Execution example**:

```python
# After completing TASK-001
update_task_checklist(
    worktree_path="/path/to/worktree",
    feature="user-auth",
    task_id="TASK-001"
)
# Output: ✅ TASK-001 marked as completed in TASKS_PHASE_1.md
```

**Before/after comparison**:

```markdown
# Before
### TASK-001: Create User Entity
**Acceptance Criteria**:
- [ ] Entity file creation
- [ ] Basic property definition
- [ ] Tests passing

# After
### TASK-001 ✅: Create User Entity
**Acceptance Criteria**:
- [x] Entity file creation
- [x] Basic property definition
- [x] Tests passing
```

### 8. Use Glob/Grep for Efficient Search

```python
# Find test files matching pattern (10x faster than Bash find)
Glob(pattern="**/*.test.ts", path=f"{worktree_path}/src/")

# Search for similar implementations (ripgrep engine)
Grep(pattern="export class.*Service", type="ts", path=f"{worktree_path}/src/")

# Find all usages of a function
Grep(pattern="createUser\\(", type="ts", path=f"{worktree_path}/", output_mode="content")

# Find files by naming convention
Glob(pattern="**/services/**/*.ts", path=f"{worktree_path}/")
Glob(pattern="**/entities/**/*.ts", path=f"{worktree_path}/")
```

### 4. Use Serena for Code Intelligence

```python
# Find existing symbols before implementing
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="UserService",
    include_body=False,
    depth=1
)

# Get file structure overview
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/domain"
)

# Replace symbol implementation
mcp__plugin_serena_serena__replace_symbol_body(
    name_path="UserService/createUser",
    relative_path="src/domain/services/UserService.ts",
    body="async createUser(data: CreateUserDTO): Promise<User> { ... }"
)
```

### 5. Task Tool Integration

> **Reference**: [Task Tool Planning Guide](../skills/wm/rules/components/task-tool-planning-guide.md)

Use `TaskCreate` at workflow start, `TaskGet → TaskUpdate` for status changes.
See guide for Staleness Prevention and Metadata Schema.

### 6. Return Result

#### Success Response

```json
{
  "status": "success",
  "phase": "PHASE_1",
  "completed_tasks": ["TASK-001", "TASK-002", "TASK-003"],
  "test_results": {
    "total": 15,
    "passed": 15,
    "failed": 0
  },
  "files_changed": [
    "src/domain/entities/User.ts",
    "src/application/usecases/CreateUser.ts",
    "tests/domain/entities/User.test.ts"
  ],
  "commits": [
    "test: add failing tests for User entity",
    "feat: implement User entity",
    "refactor: extract validation logic"
  ]
}
```

#### Failure Response

```json
{
  "status": "failure",
  "phase": "PHASE_1",
  "failed_at": {
    "task": "TASK-002",
    "tdd_phase": "GREEN | RED | REFACTOR",
    "reason": "string (error description)"
  },
  "completed_tasks": ["TASK-001"],
  "pending_tasks": ["TASK-002", "TASK-003"],
  "error_details": {
    "type": "build_error | test_failure | quality_gate | architecture_violation",
    "message": "string",
    "file": "string (optional)",
    "line": "number (optional)"
  },
  "recovery_suggestion": "string (recommended next action)"
}
```

## Clean Architecture Compliance

**Reference**: [Clean Architecture Reference](../skills/wm/rules/policies/guide-clean-architecture.md)

Implementation must strictly follow Clean Architecture principles.

### Layer Order (Domain First)

Tasks are executed following layer dependency order:

```
1. Domain Layer Tasks
   └─ Entities, Value Objects, Domain Services
   └─ ✅ No external dependencies allowed

2. Application Layer Tasks
   └─ Use Cases, DTOs, Port Interfaces
   └─ ✅ Only Domain imports allowed

3. Adapters Layer Tasks
   └─ Controllers, Repository Implementations
   └─ ✅ Implements Application port interfaces

4. Infrastructure Layer Tasks
   └─ Framework config, External integrations
   └─ ✅ Assembles all layers via DI
```

### Dependency Rules

Implementation must follow these rules:

```
✅ Domain: No external dependencies (pure business logic)
✅ Application: Only depends on Domain
✅ Adapters: Depends on Application interfaces (not concrete classes)
✅ Infrastructure: Can depend on Adapters

❌ Domain importing from Application/Adapters/Infrastructure
❌ Application importing from Adapters/Infrastructure
❌ Adapters importing concrete Infrastructure classes (use DI)
```

### Layer Placement Rules

When implementing, place components in the correct layer:

| Component | Layer | Rule |
|-----------|-------|------|
| Entity, Value Object | Domain | Core business objects |
| Domain Service | Domain | Domain logic not belonging to entities |
| Use Case | Application | System behavior orchestration |
| DTO | Application | Data transfer contracts |
| Port Interface | Application | Abstraction for external dependencies |
| Controller | Adapters | HTTP request handling |
| Repository Impl | Adapters | Port implementation |
| ORM config | Infrastructure | Technology-specific setup |
| DI Container | Infrastructure | Dependency assembly |

## Code Quality Standards

> **Full reference**: See [tdd-quality-gate.md](../skills/wm/rules/components/tdd-quality-gate.md) for verification items, execution flow, and failure handling.

Quality checks are MANDATORY in REFACTOR phase via `Skill(skill="code-quality")`. Commits are blocked until all checks pass.

### Testing

- Unit test coverage ≥ 80% for business logic
- Integration tests for critical paths

## Error Handling

### Build Failure

```
1. Capture error message
2. Identify root cause
3. Fix and retry
4. If persistent → Return failure for /solve
```

### Test Failure (During GREEN)

```
1. Analyze failing assertion
2. Check implementation against test expectation
3. Fix implementation (not the test!)
4. Retry
```

## Commit Message Convention

```
<type>: <description>

Types:
- test: Add or modify tests
- feat: New feature implementation
- fix: Bug fix
- refactor: Code improvement without behavior change
- docs: Documentation changes
```


