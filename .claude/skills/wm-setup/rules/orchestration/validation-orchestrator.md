---
title: Validation Orchestrator
impact: CRITICAL
impactDescription: Orchestrates sequential validation and remediation pipeline
tags: [orchestration, validation, pipeline]
used_by: [wm-setup]
---

# Validation Orchestrator

**Impact: CRITICAL** - Orchestrates sequential validation and remediation pipeline

## Overview

The Validation Orchestrator manages the sequential execution of all validators
and remediators, providing progress tracking and unified reporting.

## Enhanced Validations (v3.0)

The pipeline includes enhanced validations for critical components:

### MCP Validation Enhancements
- **`.mcp.json` File Validation**: Checks both project and global level configs
- **testCommand Execution**: Verifies actual tool availability via tool prefix matching
- **Tool Count Thresholds**: Ensures minimum required tools per MCP server

### Serena Plugin Verification
- **Explicit Activation Check**: Validates serena plugin via `context-gate.md`
- **Minimum Tool Requirement**: 5 serena tools required for full activation
- **Blocking on Inactive**: Less than 5 tools triggers blocking remediation

### Hook Specification Framework
- **HSC Spec Files**: Each hook has a standardized specification (HSC-001 to HSC-007)
- **Checklist Validation**: Parses and calculates completion rates
- **Test Case Tracking**: Monitors test pass/fail status
- **Coverage Reporting**: Reports specification coverage across all hooks

### wm Dependency Validation (NEW in v3.0)
- **Binary Dependencies**: graphify venv, jq, kubectl, docker, gh, python3.12
- **Graph Data**: 18 domain graphs + _global overlay + build-summary.json
- **Playwright Browsers**: chromium/firefox/webkit installation status
- **Environment Variables**: CLAUDE_PROJECT_DIR, CLAUDE_SKILL_DIR

See `rules/registries/hooks-spec-template.md` for specification format.

## Module YAML Definitions

```yaml
modules:
  - order: 1
    id: folder
    name: "Folder Structure"
    validator: "validators/folder-validator.md"
    remediator: "remediators/folder-remediation.md"
    registry: "registries/folders.yaml"
    blocking: true
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: true
    depends_on: []

  - order: 2
    id: skills
    name: "Skills"
    validator: "validators/skills-validator.md"
    remediator: "remediators/skills-remediation.md"
    registry: "registries/skills.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: true
    depends_on: []

  - order: 3
    id: agents
    name: "Agents"
    validator: "validators/agents-validator.md"
    remediator: "remediators/agents-remediation.md"
    registry: "registries/agents.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: true
    depends_on: []

  - order: 4
    id: hooks-config
    name: "Hooks Configuration"
    validator: "validators/hooks-config-validator.md"
    remediator: "remediators/hooks-config-remediation.md"
    registry: "registries/hooks.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: true
    depends_on: []

  - order: 5
    id: hooks-scripts
    name: "Hook Scripts"
    validator: "validators/hooks-scripts-validator.md"
    remediator: "remediators/hooks-scripts-remediation.md"
    registry: "registries/hooks.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: true
    depends_on: []

  - order: 6
    id: settings
    name: "Settings & Environment"
    validator: "validators/settings-validator.md"
    remediator: "remediators/settings-remediation.md"
    registry: "registries/settings.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: mixed    # some settings items are hard, others soft
    depends_on: []

  - order: 7
    id: binaries
    name: "Binary Dependencies"
    validator: "validators/binaries-validator.md"
    remediator: "remediators/binaries-remediation.md"
    registry: "registries/binaries.yaml"
    blocking: false
    blocking_items: [BIN-001]    # BIN-001 = graphify; blocking because graph-data depends on it
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: mixed    # graphify (BIN-001) is hard; others are mixed
    depends_on: []

  - order: 8
    id: env-vars
    name: "Environment Variables"
    validator: "validators/env-vars-validator.md"
    remediator: "remediators/env-vars-remediation.md"
    registry: "registries/env-vars.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: mixed
    depends_on: []

  - order: 9
    id: graph-data
    name: "Graph Data"
    validator: "validators/graph-data-validator.md"
    remediator: "remediators/graph-data-remediation.md"
    registry: "registries/graph-data.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: mixed    # build-summary + _global = hard; 18 domain graphs = soft
    depends_on: [binaries]    # requires graphify binary (BIN-001) to be present

  - order: 10
    id: playwright
    name: "Playwright Browsers"
    validator: "validators/playwright-validator.md"
    remediator: "remediators/playwright-remediation.md"
    registry: "registries/playwright.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: soft
    depends_on: []

  - order: 11
    id: runtime-checks
    name: "Runtime Health"
    validator: "onboarding/runtime-validator.md"
    remediator: null              # No auto-remediation
    registry: "onboarding/runtime-checks.yaml"
    blocking: false
    mode_scope: [VERIFY]          # VERIFY mode only
    hard: advisory
    depends_on: []

  - order: 12
    id: domains
    name: "Domain Structure"
    validator: "validators/domains-validator.md"
    remediator: "remediators/domains-remediation.md"
    registry: "registries/domains.yaml"
    blocking: false
    mode_scope: [NEW_SETUP, UPDATE, VERIFY]
    hard: soft
    depends_on: []
```

## Blocking Rules

| Module | Blocking Condition | Effect |
|--------|--------------------|--------|
| folder (order 1) | any FAIL | entire pipeline aborted |
| binaries (order 7) | BIN-001 (graphify) FAIL | graph-data module (order 9) SKIPped |
| all others | FAIL | non-blocking; pipeline continues |

Key points:
- `folder` module failure immediately stops the pipeline. All subsequent modules are SKIPped.
- `binaries` module is NOT globally blocking, but item BIN-001 (graphify) failing causes
  graph-data (order 9) to be SKIPped because graph-data depends on graphify.
- VERIFY mode: all modules run validators only; remediator is never invoked.
- Modules with `mode_scope` not containing the current mode are skipped automatically.

## Pipeline Definition

```python
VALIDATION_PIPELINE = [
    {
        "order": 1,
        "moduleId": "folder",
        "moduleName": "Folder Structure",
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "blocking": True,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": True,
        "dependsOn": []
    },
    {
        "order": 2,
        "moduleId": "skills",
        "moduleName": "Skills",
        "validator": "validators/skills-validator.md",
        "remediator": "remediators/skills-remediation.md",
        "registry": "registries/skills.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": True,
        "dependsOn": []
    },
    {
        "order": 3,
        "moduleId": "agents",
        "moduleName": "Agents",
        "validator": "validators/agents-validator.md",
        "remediator": "remediators/agents-remediation.md",
        "registry": "registries/agents.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": True,
        "dependsOn": []
    },
    {
        "order": 4,
        "moduleId": "hooks-config",
        "moduleName": "Hooks Configuration",
        "validator": "validators/hooks-config-validator.md",
        "remediator": "remediators/hooks-config-remediation.md",
        "registry": "registries/hooks.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": True,
        "dependsOn": []
    },
    {
        "order": 5,
        "moduleId": "hooks-scripts",
        "moduleName": "Hook Scripts",
        "validator": "validators/hooks-scripts-validator.md",
        "remediator": "remediators/hooks-scripts-remediation.md",
        "registry": "registries/hooks.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": True,
        "dependsOn": []
    },
    {
        "order": 6,
        "moduleId": "settings",
        "moduleName": "Settings & Environment",
        "validator": "validators/settings-validator.md",
        "remediator": "remediators/settings-remediation.md",
        "registry": "registries/settings.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": "mixed",
        "dependsOn": []
    },
    {
        "order": 7,
        "moduleId": "binaries",
        "moduleName": "Binary Dependencies",
        "validator": "validators/binaries-validator.md",
        "remediator": "remediators/binaries-remediation.md",
        "registry": "registries/binaries.yaml",
        "blocking": False,
        "blockingItems": ["BIN-001"],   # graphify; its failure causes graph-data SKIP
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": "mixed",
        "dependsOn": []
    },
    {
        "order": 8,
        "moduleId": "env-vars",
        "moduleName": "Environment Variables",
        "validator": "validators/env-vars-validator.md",
        "remediator": "remediators/env-vars-remediation.md",
        "registry": "registries/env-vars.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": "mixed",
        "dependsOn": []
    },
    {
        "order": 9,
        "moduleId": "graph-data",
        "moduleName": "Graph Data",
        "validator": "validators/graph-data-validator.md",
        "remediator": "remediators/graph-data-remediation.md",
        "registry": "registries/graph-data.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": "mixed",
        "dependsOn": ["binaries"]    # requires graphify (BIN-001) to be present
    },
    {
        "order": 10,
        "moduleId": "playwright",
        "moduleName": "Playwright Browsers",
        "validator": "validators/playwright-validator.md",
        "remediator": "remediators/playwright-remediation.md",
        "registry": "registries/playwright.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": "soft",
        "dependsOn": []
    },
    {
        "order": 11,
        "moduleId": "runtime-checks",
        "moduleName": "Runtime Health",
        "validator": "onboarding/runtime-validator.md",
        "remediator": None,                          # No auto-remediation
        "registry": "onboarding/runtime-checks.yaml",
        "blocking": False,
        "modeScope": ["VERIFY"],                     # VERIFY mode only
        "hard": "advisory",
        "dependsOn": []
    },
    {
        "order": 12,
        "moduleId": "domains",
        "moduleName": "Domain Structure",
        "validator": "validators/domains-validator.md",
        "remediator": "remediators/domains-remediation.md",
        "registry": "registries/domains.yaml",
        "blocking": False,
        "modeScope": ["NEW_SETUP", "UPDATE", "VERIFY"],
        "hard": "soft",
        "dependsOn": []
    }
]
```

## Type Definitions

### ValidationTaskMetadata

TypeScript interface defining the metadata structure for validation Task objects.

```typescript
interface ValidationTaskMetadata {
  /**
   * Unique module identifier (e.g., "folder", "skills", "binaries")
   */
  moduleId: string;

  /**
   * Human-readable module name (e.g., "Folder Structure", "Binary Dependencies")
   */
  moduleName: string;

  /**
   * Whether this module is globally blocking (stops pipeline on failure)
   * STRICT: Must be boolean type - no string/integer coercion
   */
  blocking: boolean;

  /**
   * Item IDs within this module whose failure triggers a downstream SKIP.
   * e.g., ["BIN-001"] for the binaries module means graphify failure causes
   * graph-data to be skipped.
   */
  blockingItems?: string[];

  /**
   * Execution order in the validation pipeline
   * STRICT: Must be integer in range [1,12]
   */
  order: number;

  /**
   * Path to validator agent file (relative to .claude/skills/wm-setup/)
   */
  validator: string;

  /**
   * Path to remediator agent file (relative to .claude/skills/wm-setup/)
   * Can be null for modules without auto-remediation (e.g., Module 11 Runtime Checks)
   */
  remediator: string | null;

  /**
   * Path to registry YAML file (relative to .claude/skills/wm-setup/)
   */
  registry: string;

  /**
   * Modes in which this module executes.
   * Module 11 (runtime-checks) only runs in VERIFY.
   */
  modeScope: Array<"NEW_SETUP" | "UPDATE" | "VERIFY">;

  /**
   * Module IDs this module depends on. If any dependency has a blocking item
   * failure, this module is skipped.
   * e.g., ["binaries"] for graph-data.
   */
  dependsOn: string[];

  /**
   * Required marker for TaskList filtering
   * MUST be literal boolean true to identify wm-setup validation tasks
   */
  "wm-setup": true;
}
```

**Validation Rules:**

1. **Required Fields**: All fields except `blockingItems`, `modeScope`, `dependsOn` are required
2. **Type Safety**:
   - `blocking`: Strict boolean (no "true"/1 coercion)
   - `order`: Strict integer (no float/string coercion)
   - `wm-setup`: Must be literal `true` (not just truthy)
3. **Range Constraints**:
   - `order`: Must be in range [1, 12]
4. **Null Handling**:
   - `remediator`: Can be `null` for modules without remediation

**Usage Example:**

```typescript
const folderValidationMetadata: ValidationTaskMetadata = {
  moduleId: "folder",
  moduleName: "Folder Structure",
  blocking: true,
  order: 1,
  validator: "validators/folder-validator.md",
  remediator: "remediators/folder-remediation.md",
  registry: "registries/folders.yaml",
  modeScope: ["NEW_SETUP", "UPDATE", "VERIFY"],
  dependsOn: [],
  "wm-setup": true
};

const binariesValidationMetadata: ValidationTaskMetadata = {
  moduleId: "binaries",
  moduleName: "Binary Dependencies",
  blocking: false,
  blockingItems: ["BIN-001"],
  order: 7,
  validator: "validators/binaries-validator.md",
  remediator: "remediators/binaries-remediation.md",
  registry: "registries/binaries.yaml",
  modeScope: ["NEW_SETUP", "UPDATE", "VERIFY"],
  dependsOn: [],
  "wm-setup": true
};

const graphDataValidationMetadata: ValidationTaskMetadata = {
  moduleId: "graph-data",
  moduleName: "Graph Data",
  blocking: false,
  order: 9,
  validator: "validators/graph-data-validator.md",
  remediator: "remediators/graph-data-remediation.md",
  registry: "registries/graph-data.yaml",
  modeScope: ["NEW_SETUP", "UPDATE", "VERIFY"],
  dependsOn: ["binaries"],    // skipped if BIN-001 fails
  "wm-setup": true
};

const runtimeValidationMetadata: ValidationTaskMetadata = {
  moduleId: "runtime-checks",
  moduleName: "Runtime Health",
  blocking: false,
  order: 11,
  validator: "onboarding/runtime-validator.md",
  remediator: null,  // No auto-remediation for runtime checks
  registry: "onboarding/runtime-checks.yaml",
  modeScope: ["VERIFY"],  // Only runs in VERIFY mode
  dependsOn: [],
  "wm-setup": true
};
```

## Pipeline Execution Flow

```python
def run_pipeline(mode: str) -> dict:
    """
    Execute the 12-module validation pipeline.

    Pseudo-code for the full pipeline execution.
    Actual implementation delegates to validator/remediator agents.

    Args:
        mode: "NEW_SETUP" | "UPDATE" | "VERIFY"

    Returns:
        dict: global_results keyed by module id
    """
    global_results = {}

    # Track which modules had blocking item failures (affects dependents)
    blocking_item_failures = set()  # module IDs with blocking item failures

    # Track global pipeline halt (folder module failure only)
    pipeline_halted = False
    halted_at = None

    for module in sorted(VALIDATION_PIPELINE, key=lambda m: m["order"]):
        module_id = module["moduleId"]

        # Skip if mode not in module scope
        if mode not in module["modeScope"]:
            global_results[module_id] = {
                "status": "SKIPPED",
                "reason": f"mode {mode} not in module scope {module['modeScope']}"
            }
            continue

        # Skip remaining modules if pipeline halted (folder failure)
        if pipeline_halted:
            global_results[module_id] = {
                "status": "SKIPPED",
                "reason": f"pipeline halted at {halted_at}"
            }
            continue

        # Skip if any dependency had a blocking item failure
        failed_deps = [dep for dep in module["dependsOn"] if dep in blocking_item_failures]
        if failed_deps:
            global_results[module_id] = {
                "status": "SKIPPED",
                "reason": f"dependency blocking item failed: {failed_deps}"
            }
            continue

        # Run validator
        validator_result = run_validator(module)

        # Check for blocking module failure (folder only)
        if module["blocking"] and validator_result["counts"]["fail"] > 0:
            global_results[module_id] = {
                "status": "FAIL",
                "validator": validator_result,
                "remediator": None
            }
            pipeline_halted = True
            halted_at = module_id
            continue

        # Check for blocking item failures within non-globally-blocking modules
        if "blockingItems" in module:
            failed_blocking_items = [
                item for item in validator_result.get("items", [])
                if item["id"] in module["blockingItems"] and item["status"] == "FAIL"
            ]
            if failed_blocking_items:
                blocking_item_failures.add(module_id)

        # VERIFY mode: validators only, no remediator
        if mode == "VERIFY":
            remediator_result = None
        else:
            # Run remediator only for FAIL items
            failed_items = [
                item for item in validator_result.get("items", [])
                if item["status"] == "FAIL"
            ]
            if failed_items and module["remediator"] is not None:
                remediator_result = run_remediator(module, failed_items, mode)
            else:
                remediator_result = None

        global_results[module_id] = {
            "status": validator_result["overall"],
            "validator": validator_result,
            "remediator": remediator_result
        }

    if pipeline_halted:
        return {
            "status": "ABORTED",
            "halted_at": halted_at,
            "reason": f"{halted_at} blocking failure",
            "results": global_results
        }

    return {
        "status": "COMPLETED",
        "halted_at": None,
        "results": global_results
    }
```

## Orchestration Logic

```python
def shouldSkipModule(step: dict, mode: str, blocking_item_failures: set) -> tuple:
    """
    Determine if a validation module should be skipped.

    Args:
        step: Module configuration dictionary from VALIDATION_PIPELINE
        mode: Current validation mode ("NEW_SETUP" | "UPDATE" | "VERIFY")
        blocking_item_failures: Set of module IDs that had blocking item failures

    Returns:
        tuple: (should_skip: bool, reason: str | None)

    Logic:
        1. If mode not in modeScope -> skip
        2. If any dependsOn module is in blocking_item_failures -> skip
        3. Otherwise -> do not skip

    Example:
        >>> step = {"moduleId": "runtime-checks", "modeScope": ["VERIFY"], "dependsOn": []}
        >>> shouldSkipModule(step, "NEW_SETUP", set())
        (True, "mode NEW_SETUP not in module scope ['VERIFY']")

        >>> step = {"moduleId": "graph-data", "modeScope": ["NEW_SETUP","UPDATE","VERIFY"], "dependsOn": ["binaries"]}
        >>> shouldSkipModule(step, "NEW_SETUP", {"binaries"})
        (True, "dependency blocking item failed: ['binaries']")

        >>> shouldSkipModule(step, "NEW_SETUP", set())
        (False, None)
    """
    # Check mode scope
    if mode not in step.get("modeScope", ["NEW_SETUP", "UPDATE", "VERIFY"]):
        return True, f"mode {mode} not in module scope {step.get('modeScope')}"

    # Check dependency blocking items
    failed_deps = [dep for dep in step.get("dependsOn", []) if dep in blocking_item_failures]
    if failed_deps:
        return True, f"dependency blocking item failed: {failed_deps}"

    return False, None


def runValidationPipeline(
    context: ValidationContext,
    mode: str = "VERIFY"  # NEW_SETUP, UPDATE, VERIFY
) -> dict:
    """
    Execute validation pipeline using two-phase pattern.

    Phase 1: Create all validation tasks upfront
    Phase 2: Execute tasks sequentially with blocking check

    Args:
        context: Shared validation context
        mode: wm-setup mode determining remediation behavior
            - "NEW_SETUP": Automatic remediation of all issues (3-8 minutes)
            - "UPDATE": Interactive remediation with user confirmation
            - "VERIFY": Report-only, no remediation

    Returns:
        dict: Pipeline result containing:
            - mode (str): The execution mode used
            - pipeline (dict): Aggregated counts (passed, warned, failed, skipped)
            - results (list): Individual module results
            - halted (bool): Whether pipeline was halted by blocking failure
            - halted_at (str|None): Module id where pipeline halted

    Example:
        >>> context = ValidationContext(project_root="/test/project")
        >>> result = runValidationPipeline(context, "VERIFY")
        >>> print(result)
        {
            "mode": "VERIFY",
            "pipeline": {"passed": 9, "warned": 1, "failed": 0, "skipped": 2},
            "results": [...],
            "halted": False,
            "halted_at": None
        }
    """

    # Track blocking item failures (not global halt, but affects dependents)
    blocking_item_failures = set()  # module IDs that had blockingItems fail

    # ===== PHASE 1: Create All Tasks Upfront =====
    task_ids = []
    for step in VALIDATION_PIPELINE:
        should_skip, skip_reason = shouldSkipModule(step, mode, set())
        # At creation time, we don't know blocking_item_failures yet
        # so we only skip based on modeScope here
        if mode not in step.get("modeScope", ["NEW_SETUP", "UPDATE", "VERIFY"]):
            continue

        task_id = createValidationTask(step, mode)
        task_ids.append(task_id)

    # ===== PHASE 2: Execute Sequentially =====
    results = []
    pipeline_halted = False
    halted_module_id = None

    for task_id in task_ids:
        task = TaskGet(taskId=task_id)
        step_module_id = task.metadata.get("moduleId", "unknown")
        step_depends_on = task.metadata.get("dependsOn", [])

        # Check if dependency had blocking item failure
        failed_deps = [dep for dep in step_depends_on if dep in blocking_item_failures]
        if failed_deps or pipeline_halted:
            reason = (
                f"Pipeline blocked at {halted_module_id}"
                if pipeline_halted
                else f"dependency blocking item failed: {failed_deps}"
            )
            results.append({
                "taskId": task_id,
                "moduleId": step_module_id,
                "moduleName": task.metadata.get("moduleName", "Unknown Module"),
                "order": task.metadata.get("order", 0),
                "status": "SKIPPED",
                "reason": reason,
                "blocking": task.metadata.get("blocking", False)
            })
            TaskUpdate(taskId=task_id, status="completed", metadata={"result": "SKIPPED", "reason": reason})
            continue

        # Execute with staleness prevention
        result = executeValidationTask(task_id, mode)
        results.append(result)

        # Check global blocking failure (folder module)
        if result["status"] == "FAIL" and result.get("blocking", False):
            pipeline_halted = True
            halted_module_id = step_module_id

        # Check blocking item failures (affects downstream dependents)
        blocking_items = task.metadata.get("blockingItems", [])
        if blocking_items:
            failed_blocking = [
                item for item in result.get("items", [])
                if item.get("id") in blocking_items and item.get("status") == "FAIL"
            ]
            if failed_blocking:
                blocking_item_failures.add(step_module_id)

    # ===== Aggregate Results =====
    count_passed = sum(1 for r in results if r["status"] == "PASS")
    count_warned = sum(1 for r in results if r["status"] == "WARN")
    count_failed = sum(1 for r in results if r["status"] == "FAIL")
    count_skipped = sum(1 for r in results if r["status"] == "SKIPPED")

    # Determine overall status
    if count_failed > 0:
        overall_status = "FAIL"
    elif count_warned > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    # Count total modules (12 total)
    total_modules = len(VALIDATION_PIPELINE)

    return {
        "mode": mode,
        "modules": {
            "total": total_modules,
            "passed": count_passed,
            "warned": count_warned,
            "failed": count_failed,
            "skipped": count_skipped
        },
        "results": results,
        "blocked": pipeline_halted,
        "halted_at": halted_module_id,
        "overall": overall_status,
        "actions": {
            "executed": sum(len(r.get("actionsExecuted", [])) for r in results if "actionsExecuted" in r),
            "required": sum(len(r.get("issues", [])) for r in results if r["status"] in ["FAIL", "WARN"])
        }
    }
```

## Helper Functions and Constants

### getValidationTasks

```python
def getValidationTasks() -> list:
    """
    Get all wm-setup validation tasks from TaskList.

    This helper filters the TaskList to return only tasks marked with
    metadata.wm-setup == True, which represent validation pipeline modules.

    Returns:
        list: Tasks filtered by metadata.wm-setup == True, unsorted

    Example:
        >>> tasks = getValidationTasks()
        >>> len(tasks)
        12  # All 12 validation modules
        >>> all(t.metadata.get("wm-setup") == True for t in tasks)
        True
    """
    all_tasks = TaskList()
    return [t for t in all_tasks if t.metadata.get("wm-setup") == True]
```

### Status Icons

```python
# Status icon mappings for display functions
# Used by: printPipelineProgress(), generatePipelineSummary()
STATUS_ICONS = {
    "pending": "⏸️",      # Task not yet started
    "in_progress": "⏳",  # Task currently executing
    "completed": "✅",    # Task completed (default, may be refined based on result)
    "blocked": "🔒",      # Task blocked by dependency
    "pass": "✅",         # Completed with PASS result
    "warn": "⚠️",         # Completed with WARN result
    "fail": "❌"          # Completed with FAIL result
}

# Korean status labels for user-facing output
STATUS_LABELS_KO = {
    "PASS": "통과",
    "WARN": "경고",
    "FAIL": "실패",
    "SKIPPED": "건너뜀",
    "ERROR": "오류",
    "PENDING": "대기"
}

# Korean module names for user-facing output
MODULE_NAMES_KO = {
    "folder": "폴더 구조",
    "skills": "스킬",
    "agents": "에이전트",
    "hooks-config": "훅 설정",
    "hooks-scripts": "훅 스크립트",
    "settings": "설정 & 환경",
    "binaries": "바이너리 의존성",
    "env-vars": "환경 변수",
    "graph-data": "그래프 데이터",
    "playwright": "Playwright 브라우저",
    "runtime-checks": "런타임 검사",
    "domains": "도메인 구조"
}

# Priority classification for issues
PRIORITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

PRIORITY_LABELS_KO = {
    "CRITICAL": "긴급",
    "HIGH": "높음",
    "MEDIUM": "보통",
    "LOW": "낮음"
}

# Module priority mapping
MODULE_PRIORITY = {
    "folder": "CRITICAL",        # Blocking module - must be fixed first
    "skills": "HIGH",            # Core functionality
    "agents": "HIGH",            # Core functionality
    "hooks-config": "MEDIUM",    # Enhancement
    "hooks-scripts": "MEDIUM",   # Enhancement
    "settings": "LOW",           # Optional optimization
    "binaries": "HIGH",          # wm workflow dependency
    "env-vars": "MEDIUM",        # Environment configuration
    "graph-data": "HIGH",        # Graphify Fast Pass requires this
    "playwright": "LOW",         # E2E testing dependency
    "runtime-checks": "MEDIUM",  # Runtime health (VERIFY only)
    "domains": "LOW"             # Optional structure
}
```

### 우선순위 분류 함수

```python
def classifyResultsByPriority(results: list) -> dict:
    """
    검증 결과를 우선순위별로 분류합니다.

    Args:
        results: 검증 파이프라인 결과 목록

    Returns:
        우선순위별로 그룹화된 결과 딕셔너리

    Example:
        >>> results = [
        ...     {"moduleId": "folder", "status": "FAIL"},
        ...     {"moduleId": "settings", "status": "WARN"}
        ... ]
        >>> classified = classifyResultsByPriority(results)
        >>> classified["CRITICAL"]
        [{"moduleId": "folder", "status": "FAIL"}]
    """
    classified = {p: [] for p in PRIORITY_ORDER}

    for result in results:
        if result.get("status") not in ["WARN", "FAIL"]:
            continue

        module_id = result.get("moduleId", "unknown")
        priority = MODULE_PRIORITY.get(module_id, "LOW")
        classified[priority].append(result)

    return classified
```

## Progress Display

```python
def printPipelineProgress() -> None:
    """
    Displays real-time validation pipeline progress by reading from TaskList.
    No parameters - reads directly from TaskList API.
    Outputs Korean labels for user-facing display.

    Display Format (한국어):
    ┌──────────────────────────────────────────────────────┐
    │ wm-setup 검증 파이프라인 (12 모듈)                   │
    ├──────────────────────────────┬──────────┬────────────┤
    │ 모듈                         │ 상태     │ 블로킹     │
    ├──────────────────────────────┼──────────┼────────────┤
    │ [ 1/12] 폴더 구조            │ ✅ 통과  │ 예         │
    │ [ 2/12] 스킬                 │ ⚠️ 경고  │ 아니오     │
    │ [ 3/12] 에이전트             │ ✅ 통과  │ 아니오     │
    │ [ 4/12] 훅 설정              │ ⏳ ...   │ 아니오     │
    │ [ 5/12] 훅 스크립트          │ ⏸️ 대기  │ 아니오     │
    │ [ 6/12] 설정 & 환경          │ ⏸️ 대기  │ 아니오     │
    │ [ 7/12] 바이너리 의존성      │ ⏸️ 대기  │ 아니오*    │
    │ [ 8/12] 환경 변수            │ ⏸️ 대기  │ 아니오     │
    │ [ 9/12] 그래프 데이터        │ ⏸️ 대기  │ 아니오     │
    │ [10/12] Playwright 브라우저  │ ⏸️ 대기  │ 아니오     │
    │ [11/12] 런타임 검사          │ ⏸️ 대기  │ 아니오     │
    │ [12/12] 도메인 구조          │ ⏸️ 대기  │ 아니오     │
    └──────────────────────────────┴──────────┴────────────┘
    * 바이너리 BIN-001(graphify) 실패 시 그래프 데이터 모듈 SKIP
    """
    validation_tasks = getValidationTasks()
    validation_tasks.sort(key=lambda t: t.metadata.get("order", 999))
    task_map = {task.metadata.get("moduleId"): task for task in validation_tasks}

    output = []
    output.append("┌──────────────────────────────────────────────────────┐")
    output.append("│ wm-setup 검증 파이프라인 (12 모듈)                   │")
    output.append("├──────────────────────────────┬──────────┬────────────┤")
    output.append("│ 모듈                         │ 상태     │ 블로킹     │")
    output.append("├──────────────────────────────┼──────────┼────────────┤")

    total_modules = len(VALIDATION_PIPELINE)
    for i, module in enumerate(VALIDATION_PIPELINE):
        step_num = i + 1
        module_id = module["moduleId"]
        module_name_ko = MODULE_NAMES_KO.get(module_id, module["moduleName"])
        is_blocking = module.get("blocking", False)
        has_blocking_items = bool(module.get("blockingItems", []))
        if is_blocking:
            blocking_ko = "예"
        elif has_blocking_items:
            blocking_ko = "아니오*"
        else:
            blocking_ko = "아니오"

        task = task_map.get(module_id)

        if task:
            task_status = task.status
            if task_status == "completed":
                result = task.metadata.get("result", "PASS")
                if result == "PASS":
                    icon, status_label = "✅", "통과"
                elif result == "WARN":
                    icon, status_label = "⚠️", "경고"
                elif result == "FAIL":
                    icon, status_label = "❌", "실패"
                elif result == "SKIPPED":
                    icon, status_label = "⏭️", "건너뜀"
                else:
                    icon, status_label = "✅", "통과"
            elif task_status == "in_progress":
                icon, status_label = "⏳", "..."
            elif task_status == "blocked":
                icon, status_label = "🔒", "차단"
            else:
                icon, status_label = "⏸️", "대기"
        else:
            icon, status_label = "⏸️", "대기"

        module_col = f"[{step_num:2}/{total_modules}] {module_name_ko:<16}"
        status_col = f"{icon} {status_label:<4}"
        blocking_col = f"{blocking_ko:<8}"

        output.append(f"│ {module_col} │ {status_col} │ {blocking_col} │")

    output.append("└──────────────────────────────┴──────────┴────────────┘")
    output.append("* 바이너리 BIN-001(graphify) 실패 시 그래프 데이터 모듈 SKIP")

    print("\n".join(output))
```

## Mode-Specific Behavior

### NEW_SETUP Mode

```python
def newSetupBehavior():
    """
    NEW_SETUP mode: Full 12-module validation with automatic remediation.
    Estimated duration: 3-8 minutes (includes graphify venv build).

    - Run all 12 modules sequentially (runtime-checks skipped - VERIFY only)
    - Auto-remediate all safe issues without user prompts
    - AskUserQuestion only for graphify editable install option
    - Create missing folders, copy templates, install binaries
    - Report remaining manual actions
    """
    return {
        "validation": "full_12_modules",
        "remediation": "auto",
        "blocking_behavior": "remediate_and_retry",
        "user_interaction": "graphify_editable_only",
        "estimated_duration_minutes": "3-8",
        "report": "detailed"
    }
```

### UPDATE Mode

```python
def updateBehavior():
    """
    UPDATE mode: 12-module validation with interactive remediation.

    - Run all 12 modules sequentially (runtime-checks skipped - VERIFY only)
    - Collect all FAIL items across all modules first
    - Present single AskUserQuestion with 4 options:
        1. Auto install all  - remediate everything automatically
        2. Install hard only  - only hard-classified items
        3. Show commands     - print install commands, user runs manually
        4. Cancel            - no changes
    - Focus on detecting changes from previous state
    """
    return {
        "validation": "full_12_modules",
        "remediation": "interactive_batch",
        "interaction_pattern": "single_ask_4_options",
        "options": [
            "Auto install all",
            "Install hard only",
            "Show commands",
            "Cancel"
        ],
        "blocking_behavior": "remediate_and_retry",
        "report": "changes_only"
    }
```

### VERIFY Mode

```python
def verifyBehavior():
    """
    VERIFY mode: Report-only validation (all 12 modules including runtime-checks).

    - Run all 12 modules (including module 11 runtime-checks)
    - No automatic remediation
    - validators only, remediator = None for all modules
    - Generate detailed report with "wm is ready" or specific FAIL items
    """
    return {
        "validation": "full_12_modules_plus_runtime",
        "remediation": "report_only",
        "runtime_checks_included": True,   # module 11 runs in VERIFY
        "blocking_behavior": "report_and_stop",
        "final_message": "wm is ready OR list specific FAIL items",
        "report": "detailed"
    }
```

## Pipeline Summary

```python
def generatePipelineSummary(mode: str = None) -> dict:
    """
    Generate final pipeline summary by reading from TaskList.
    Outputs Korean messages for user-facing display.

    Args:
        mode: Optional mode for backwards compatibility (not used internally)

    Returns:
        Summary dict with overall status, module counts, and action tallies

    Example Display Format (한국어):
    ┌─────────────────────────────────────────────────┐
    │ 파이프라인 요약 (VERIFY 모드)                     │
    ├──────────────────────────────────────────────────┤
    │ 전체 모듈: 12개 (런타임 검사 포함)                 │
    │ 통과: 9   경고: 1   실패: 1   건너뜀: 0          │
    │ 전체 상태: ⚠️ 경고                              │
    ├──────────────────────────────────────────────────┤
    │ 실행된 조치: 0건 (VERIFY 모드 - 보고만)           │
    │ 필요한 조치: 3건                                 │
    │ VERIFY 후 체크리스트: runtime-validator 참조      │
    └─────────────────────────────────────────────────┘
    """
    validation_tasks = getValidationTasks()

    completed = [t for t in validation_tasks if t.status == "completed"]
    pending = [t for t in validation_tasks if t.status == "pending"]

    passed = sum(1 for t in completed if t.metadata.get("result") == "PASS")
    warned = sum(1 for t in completed if t.metadata.get("result") == "WARN")
    failed = sum(1 for t in completed if t.metadata.get("result") == "FAIL")
    skipped = sum(1 for t in pending if t.metadata.get("skipped") == True)
    skipped += sum(1 for t in completed if t.metadata.get("result") == "SKIPPED")

    actions_executed = 0
    actions_required = 0
    for t in completed:
        remediation = t.metadata.get("remediation", {})
        actions_executed += len(remediation.get("actionsExecuted", []))
        actions_required += len(remediation.get("actionsRequired", []))

    blocked = any(
        t.metadata.get("blocking") == True and t.metadata.get("result") == "FAIL"
        for t in completed
    )

    if blocked:
        overall = "FAIL"
    elif failed > 0:
        has_nonblocking_failure = any(
            t.metadata.get("result") == "FAIL" and t.metadata.get("blocking") == False
            for t in completed
        )
        overall = "PARTIAL" if (has_nonblocking_failure and not blocked) else "FAIL"
    elif warned > 0:
        overall = "WARN"
    else:
        overall = "PASS"

    # Final user-facing message
    if overall == "PASS":
        final_message = "wm is ready"
    else:
        fail_modules = [
            t.metadata.get("moduleName", t.metadata.get("moduleId"))
            for t in completed
            if t.metadata.get("result") in ["FAIL", "WARN"]
        ]
        final_message = f"Issues found in: {', '.join(fail_modules)}"

    return {
        "overall": overall,
        "blocked": blocked,
        "finalMessage": final_message,
        "modules": {
            "total": len(validation_tasks),
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "skipped": skipped
        },
        "actions": {
            "executed": actions_executed,
            "required": actions_required
        },
        "timestamp": datetime.now().isoformat()
    }
```

## Error Handling

```python
def handlePipelineError(step: dict, error: Exception) -> dict:
    """
    Handle errors during pipeline execution.
    """
    return {
        "order": step["order"],
        "moduleId": step["moduleId"],
        "moduleName": step["moduleName"],
        "status": "ERROR",
        "error": str(error),
        "blocking": step["blocking"]
    }
```

## Task Creation Utility

### Constants

```python
# Total number of validation modules in the pipeline
TOTAL_VALIDATION_MODULES = 12

# Task formatting templates
TASK_SUBJECT_TEMPLATE = "[{order}/{total}] Validate {moduleName}"
TASK_ACTIVE_FORM_TEMPLATE = "Validating {moduleName}..."
TASK_DESCRIPTION_TEMPLATE = """Execute validation for {moduleName} module
Validator: {validator}
Mode: {mode}
Blocking: {blocking}"""

# Required metadata fields for task creation
REQUIRED_METADATA_FIELDS = [
    "moduleId",
    "moduleName",
    "validator",
    "order",
    "blocking",
    "registry"
]

# Task status constants
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Mode behavior configuration
MODE_BEHAVIOR = {
    "NEW_SETUP": {
        "remediation": "auto",
        "trackMetadata": True,
        "askUser": False,
        "askUserException": "graphify_editable_option"
    },
    "UPDATE": {
        "remediation": "interactive_batch",
        "trackMetadata": True,
        "askUser": True,
        "interactionPattern": "single_ask_4_options"
    },
    "VERIFY": {
        "remediation": None,
        "trackMetadata": True,
        "askUser": False
    }
}
```

### createValidationTask

```python
def createValidationTask(
    step: dict,
    mode: str,
    total_steps: int = TOTAL_VALIDATION_MODULES
) -> str:
    """
    Create a Task for tracking validation module execution.

    Args:
        step: Pipeline step definition from VALIDATION_PIPELINE containing:
            - moduleId (str): Unique module identifier (e.g., "folder")
            - moduleName (str): Human-readable name (e.g., "Folder Structure")
            - validator (str): Path to validator agent file
            - order (int): Execution order (1-12)
            - blocking (bool): Whether module blocks pipeline on failure
            - registry (str): Path to registry YAML file
            - remediator (str|None, optional): Path to remediator agent file
            - modeScope (list, optional): Modes in which this module runs
            - dependsOn (list, optional): Module IDs this module depends on
            - blockingItems (list, optional): Item IDs whose failure blocks dependents

        mode: wm-setup mode determining remediation behavior

        total_steps: Total number of validation modules in pipeline
            (default: TOTAL_VALIDATION_MODULES = 12)

    Returns:
        str: Unique taskId of the created Task (e.g., "task-abc123")

    Raises:
        ValueError: If required metadata fields are missing or invalid
        TypeError: If field types are incorrect (e.g., blocking is not bool)
    """
    _validate_task_metadata(step)

    subject = TASK_SUBJECT_TEMPLATE.format(
        order=step['order'],
        total=total_steps,
        moduleName=step['moduleName']
    )

    blocking_text = "Yes" if step.get('blocking', False) else "No"
    description = TASK_DESCRIPTION_TEMPLATE.format(
        moduleName=step['moduleName'],
        validator=step['validator'],
        mode=mode,
        blocking=blocking_text
    )

    active_form = TASK_ACTIVE_FORM_TEMPLATE.format(
        moduleName=step['moduleName']
    )

    metadata = {
        "moduleId": step['moduleId'],
        "moduleName": step['moduleName'],
        "validator": step['validator'],
        "order": step['order'],
        "blocking": step.get('blocking', False),
        "registry": step['registry'],
        "mode": mode,
        "pipeline": "validation",
        "wm-setup": True
    }

    if 'remediator' in step:
        metadata['remediator'] = step['remediator']
    if 'modeScope' in step:
        metadata['modeScope'] = step['modeScope']
    if 'dependsOn' in step:
        metadata['dependsOn'] = step['dependsOn']
    if 'blockingItems' in step:
        metadata['blockingItems'] = step['blockingItems']

    task_result = TaskCreate(
        subject=subject,
        description=description,
        activeForm=active_form,
        metadata=metadata
    )

    return task_result.taskId


def _validate_task_metadata(step: dict) -> None:
    """
    Validate required metadata fields for task creation.

    Raises:
        ValueError: If required fields are missing or values are invalid
        TypeError: If field types are incorrect
    """
    for field in REQUIRED_METADATA_FIELDS:
        if field not in step:
            raise ValueError(
                f"Missing required field: '{field}'. "
                f"Required fields: {', '.join(REQUIRED_METADATA_FIELDS)}"
            )

    if not isinstance(step['blocking'], bool):
        raise TypeError(
            f"Field 'blocking' must be boolean, got {type(step['blocking']).__name__}. "
            f"Use True or False, not 'true'/1."
        )

    if not isinstance(step['order'], int) or isinstance(step['order'], bool):
        raise TypeError(
            f"Field 'order' must be integer, got {type(step['order']).__name__}. "
            f"Use 1, not 1.0 or '1'."
        )

    if not (1 <= step['order'] <= TOTAL_VALIDATION_MODULES):
        raise ValueError(
            f"Field 'order' must be in range [1,{TOTAL_VALIDATION_MODULES}], "
            f"got {step['order']}"
        )
```

## Task Execution

### executeValidationTask

```python
def executeValidationTask(taskId: str, mode: str) -> dict:
    """
    Execute a single validation task with staleness prevention.

    Staleness Prevention:
        TaskGet is called THREE times during execution:
        1. Before marking task as "in_progress"
        2. Before running remediator (if needed)
        3. Before final status update (completed/failed)
    """
    current = TaskGet(taskId=taskId)

    if current.status != STATUS_PENDING:
        return {
            "taskId": taskId,
            "moduleId": current.metadata.get("moduleId", "unknown"),
            "moduleName": current.metadata.get("moduleName", "Unknown Module"),
            "status": "SKIPPED",
            "reason": f"Task already processed (status: {current.status})",
            "blocking": current.metadata.get("blocking", False)
        }

    TaskUpdate(taskId=taskId, status=STATUS_IN_PROGRESS)

    metadata = current.metadata
    module_id = metadata.get("moduleId")
    module_name = metadata.get("moduleName")
    validator_path = metadata.get("validator")
    remediator_path = metadata.get("remediator")
    blocking = metadata.get("blocking", False)
    registry_path = metadata.get("registry")

    try:
        validator_result = runValidator(
            validator_path=validator_path,
            registry_path=registry_path,
            context=ValidationContext()
        )

        mode_config = MODE_BEHAVIOR.get(mode, MODE_BEHAVIOR["VERIFY"])
        remediation_metadata = {}

        should_remediate = (
            validator_result["status"] in ["FAIL", "WARN"]
            and remediator_path is not None
            and mode_config["remediation"] is not None
        )

        if should_remediate:
            if mode == "NEW_SETUP":
                current = TaskGet(taskId=taskId)
                remediation_result = runRemediator(
                    remediator_path=remediator_path,
                    validation_result=validator_result,
                    context=ValidationContext(),
                    mode=mode_config["remediation"]
                )
                remediation_metadata = {
                    "autoExecuted": True,
                    "userApproved": None,
                    "actionsExecuted": remediation_result.get("actionsExecuted", []),
                    "actionsRequired": remediation_result.get("actionsRequired", []),
                    "timestamp": datetime.now().isoformat(),
                    "revalidated": True
                }
                validator_result = runValidator(
                    validator_path=validator_path,
                    registry_path=registry_path,
                    context=ValidationContext()
                )

            elif mode == "UPDATE":
                # UPDATE mode collects all FAIL items and presents single batch question
                # See updateBehavior() for 4-option interaction pattern
                current = TaskGet(taskId=taskId)
                remediation_result = runRemediator(
                    remediator_path=remediator_path,
                    validation_result=validator_result,
                    context=ValidationContext(),
                    mode=mode_config["remediation"]
                )
                remediation_metadata = {
                    "userApproved": True,
                    "actionsExecuted": remediation_result.get("actionsExecuted", []),
                    "actionsRequired": remediation_result.get("actionsRequired", []),
                    "timestamp": datetime.now().isoformat(),
                    "revalidated": True
                }
                validator_result = runValidator(
                    validator_path=validator_path,
                    registry_path=registry_path,
                    context=ValidationContext()
                )

        elif validator_result["status"] in ["FAIL", "WARN"] and remediator_path is not None:
            remediation_metadata = {
                "skipped": True,
                "skipReason": f"{mode} mode - report only",
                "actionsRequired": validator_result.get("actionsRequired", [])
            }

        if remediation_metadata:
            TaskUpdate(taskId=taskId, metadata={"remediation": remediation_metadata})

        current = TaskGet(taskId=taskId)
        validation_passed = validator_result["status"] == "PASS"
        final_status = STATUS_COMPLETED if validation_passed else STATUS_FAILED
        TaskUpdate(taskId=taskId, status=final_status)

        return {
            "taskId": taskId,
            "moduleId": module_id,
            "moduleName": module_name,
            "status": "PASS" if validation_passed else "FAIL",
            "blocking": blocking,
            "passRate": validator_result.get("passRate", 0),
            "issues": validator_result.get("issues", []),
            "items": validator_result.get("items", [])
        }

    except Exception as e:
        print(f"Error executing validation task {taskId}: {str(e)}")
        return {
            "taskId": taskId,
            "moduleId": module_id,
            "moduleName": module_name,
            "status": "ERROR",
            "blocking": blocking,
            "error": str(e),
            "requiresManualRecovery": True
        }
```


## References

- **Test Documentation**: [validation-orchestrator-tests.md](./validation-orchestrator-tests.md) - TDD test scenarios
- **Validators**: [../validators/](../validators/)
- **Remediators**: [../remediators/](../remediators/)
- **Registries**: [../registries/](../registries/)
- **Progress Tracking**: [progress-tracking.md](./progress-tracking.md)
- **Task Tools Guide**: [../../wm/rules/components/task-tool-planning-guide.md](../../wm/rules/components/task-tool-planning-guide.md)
