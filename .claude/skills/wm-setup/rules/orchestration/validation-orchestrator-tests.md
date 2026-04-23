---
title: Validation Orchestrator - TDD Tests
impact: HIGH
impactDescription: TDD test scenarios for validation pipeline
tags: [testing, tdd, validation, pipeline]
used_by: [validation-orchestrator]
parent_document: ./validation-orchestrator.md
---

# Validation Orchestrator - TDD Test Documentation

**Parent Document**: [validation-orchestrator.md](./validation-orchestrator.md)

This document contains TDD (Test-Driven Development) test scenarios for the Validation Orchestrator.
The test scenarios are separated from the core implementation to optimize loading performance.

---

## Test Documentation (RED Phase)

### Test Scenarios for createValidationTask

The following test scenarios define expected behavior for the `createValidationTask` function.

**Status: FAILING** - Function not yet implemented

#### Test 1: Subject Format

**Given**: A validation step with order=1, moduleName="Folder Structure", total_steps=8
**When**: createValidationTask is called
**Then**: Task subject should be exactly `[1/8] Validate Folder Structure`

```python
# Expected Task.subject format
assert task.subject == f"[{step['order']}/{total_steps}] Validate {step['moduleName']}"

# Test cases
test_cases = [
    {"order": 1, "moduleName": "Folder Structure", "expected": "[1/8] Validate Folder Structure"},
    {"order": 2, "moduleName": "Skills", "expected": "[2/8] Validate Skills"},
    {"order": 8, "moduleName": "Domain Structure", "expected": "[8/8] Validate Domain Structure"}
]
```

#### Test 2: Metadata Fields

**Given**: A validation step with all fields populated
**When**: createValidationTask is called
**Then**: Task metadata must include:

- `moduleId`: step["moduleId"]
- `moduleName`: step["moduleName"]
- `validator`: step["validator"]
- `order`: step["order"]
- `blocking`: step["blocking"]
- `mode`: current wm-setup mode
- `pipeline`: "validation"

```python
# Expected metadata structure
expected_metadata = {
    "moduleId": "folders",
    "moduleName": "Folder Structure",
    "validator": "validators/folder-validator.md",
    "order": 1,
    "blocking": True,
    "mode": "VERIFY",
    "pipeline": "validation"
}

assert task.metadata == expected_metadata
```

#### Test 3: ActiveForm Field

**Given**: A validation step with moduleName="Skills"
**When**: createValidationTask is called
**Then**: Task activeForm should use present continuous tense: `Validating {moduleName}...`

```python
# Expected activeForm format
assert task.activeForm == f"Validating {step['moduleName']}..."

# Test cases
test_cases = [
    {"moduleName": "Folder Structure", "expected": "Validating Folder Structure..."},
    {"moduleName": "Skills", "expected": "Validating Skills..."},
    {"moduleName": "Hooks Configuration", "expected": "Validating Hooks Configuration..."}
]
```

#### Test 4: Return Value

**Given**: A successful Task creation
**When**: createValidationTask is called
**Then**: Function must return the taskId as a string

```python
# Expected return type and format
task_id = createValidationTask(step, mode, total_steps)
assert isinstance(task_id, str), "taskId must be a string"
assert len(task_id) > 0, "taskId must not be empty"
assert task_id.startswith("task-"), "taskId should follow 'task-' prefix convention"
```

#### Test 5: Description Field

**Given**: A validation step with validator path
**When**: createValidationTask is called
**Then**: Task description should include validator path and mode

```python
# Expected description content
expected_description = (
    f"Execute validation for {step['moduleName']} module\n"
    f"Validator: {step['validator']}\n"
    f"Mode: {mode}\n"
    f"Blocking: {'Yes' if step['blocking'] else 'No'}"
)

assert task.description == expected_description
```

#### Test 6: Edge Cases

**Test 6.1**: Module with verifyModeOnly flag
```python
step = {
    "order": 7,
    "moduleId": "runtime",
    "moduleName": "Runtime Checks",
    "verifyModeOnly": True
}

task_id = createValidationTask(step, "VERIFY", 8)
assert task.metadata["verifyModeOnly"] == True
```

**Test 6.2**: Module without remediator
```python
step = {
    "order": 7,
    "moduleId": "runtime",
    "moduleName": "Runtime Checks",
    "remediator": None
}

task_id = createValidationTask(step, "VERIFY", 8)
assert task.metadata["remediator"] is None
```

**Test 6.3**: Different total_steps value
```python
task_id = createValidationTask(step, "VERIFY", total_steps=10)
assert task.subject == "[1/10] Validate Folder Structure"
```

### Expected Test Output (RED Phase)

When tests are run, they should FAIL with the following error:

```
FAIL: test_createValidationTask_subject_format
  NameError: name 'createValidationTask' is not defined

FAIL: test_createValidationTask_metadata_fields
  NameError: name 'createValidationTask' is not defined

FAIL: test_createValidationTask_activeForm
  NameError: name 'createValidationTask' is not defined

FAIL: test_createValidationTask_return_value
  NameError: name 'createValidationTask' is not defined

FAIL: test_createValidationTask_description
  NameError: name 'createValidationTask' is not defined

FAIL: test_createValidationTask_edge_cases
  NameError: name 'createValidationTask' is not defined

6 failed, 0 passed
```

### Test Scenarios for ValidationTaskMetadata Schema

The following test scenarios define expected validation behavior for the ValidationTaskMetadata interface.

**Status: FAILING** - Schema validation not yet implemented

#### Schema Test 1: Valid Metadata with All Required Fields

**Given**: A ValidationTaskMetadata object with all required fields populated correctly
**When**: Schema validation is performed
**Then**: Validation should pass

```python
def test_valid_metadata_complete():
    """
    Test that metadata with all required fields passes validation.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1,
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: validate_metadata(metadata) returns True
    # Actual: NameError - validate_metadata function doesn't exist
    assert validate_metadata(metadata) == True
```

#### Schema Test 2: Missing Required Field - moduleId

**Given**: ValidationTaskMetadata without moduleId field
**When**: Schema validation is performed
**Then**: Validation should reject with clear error

```python
def test_missing_module_id():
    """
    Test that missing moduleId field is rejected.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        # "moduleId": "folders",  # MISSING REQUIRED FIELD
        "moduleName": "Folder Structure",
        "order": 1,
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: ValidationError("Required field 'moduleId' is missing")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValidationError) as exc:
        validate_metadata(metadata)
    assert "moduleId" in str(exc.value)
```

#### Schema Test 3: Missing Required Field - blocking

**Given**: ValidationTaskMetadata without blocking field
**When**: Schema validation is performed
**Then**: Validation should reject with clear error

```python
def test_missing_blocking():
    """
    Test that missing blocking field is rejected.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1,
        # "blocking": True,  # MISSING REQUIRED FIELD
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: ValidationError("Required field 'blocking' is missing")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValidationError) as exc:
        validate_metadata(metadata)
    assert "blocking" in str(exc.value)
```

#### Schema Test 4: Missing Required Field - order

**Given**: ValidationTaskMetadata without order field
**When**: Schema validation is performed
**Then**: Validation should reject with clear error

```python
def test_missing_order():
    """
    Test that missing order field is rejected.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        # "order": 1,  # MISSING REQUIRED FIELD
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: ValidationError("Required field 'order' is missing")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValidationError) as exc:
        validate_metadata(metadata)
    assert "order" in str(exc.value)
```

#### Schema Test 5: Missing Required Field - validator

**Given**: ValidationTaskMetadata without validator field
**When**: Schema validation is performed
**Then**: Validation should reject with clear error

```python
def test_missing_validator():
    """
    Test that missing validator field is rejected.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1,
        "blocking": True,
        # "validator": "validators/folder-validator.md",  # MISSING REQUIRED FIELD
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: ValidationError("Required field 'validator' is missing")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValidationError) as exc:
        validate_metadata(metadata)
    assert "validator" in str(exc.value)
```

#### Schema Test 6: Missing Required Field - registry

**Given**: ValidationTaskMetadata without registry field
**When**: Schema validation is performed
**Then**: Validation should reject with clear error

```python
def test_missing_registry():
    """
    Test that missing registry field is rejected.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1,
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        # "registry": "registries/folders.yaml",  # MISSING REQUIRED FIELD
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: ValidationError("Required field 'registry' is missing")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValidationError) as exc:
        validate_metadata(metadata)
    assert "registry" in str(exc.value)
```

#### Schema Test 7: Missing Required Field - wm-setup

**Given**: ValidationTaskMetadata without wm-setup filter marker
**When**: Schema validation is performed
**Then**: Validation should reject (required for TaskList filtering)

```python
def test_missing_wm-setup_marker():
    """
    Test that missing wm-setup field is rejected.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1,
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        # "wm-setup": True  # MISSING - Required for TaskList filtering
    }

    # Expected: ValidationError("Required field 'wm-setup' is missing")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValidationError) as exc:
        validate_metadata(metadata)
    assert "wm-setup" in str(exc.value)
```

#### Schema Test 8: Type Validation - blocking Must Be Boolean

**Given**: ValidationTaskMetadata with blocking as string instead of boolean
**When**: Schema validation is performed
**Then**: Validation should reject with type error

```python
def test_blocking_type_string():
    """
    Test that blocking field rejects non-boolean values.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1,
        "blocking": "true",  # WRONG TYPE: string instead of boolean
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: TypeError("Field 'blocking' must be boolean, got str")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(TypeError) as exc:
        validate_metadata(metadata)
    assert "blocking" in str(exc.value)
    assert "boolean" in str(exc.value).lower()
```

**Test 8.2**: blocking as integer (no implicit coercion)
```python
def test_blocking_type_integer():
    """
    Test that blocking field rejects integer values (1/0).

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1,
        "blocking": 1,  # WRONG TYPE: integer instead of boolean
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: TypeError("Field 'blocking' must be boolean, got int")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(TypeError) as exc:
        validate_metadata(metadata)
    assert "blocking" in str(exc.value)
```

#### Schema Test 9: Type Validation - order Must Be Integer

**Given**: ValidationTaskMetadata with order as string instead of integer
**When**: Schema validation is performed
**Then**: Validation should reject with type error

```python
def test_order_type_string():
    """
    Test that order field rejects non-integer values.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": "1",  # WRONG TYPE: string instead of integer
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: TypeError("Field 'order' must be integer, got str")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(TypeError) as exc:
        validate_metadata(metadata)
    assert "order" in str(exc.value)
    assert "integer" in str(exc.value).lower()
```

**Test 9.2**: order as float (no implicit rounding)
```python
def test_order_type_float():
    """
    Test that order field rejects float values.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 1.0,  # WRONG TYPE: float instead of integer
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: TypeError("Field 'order' must be integer, got float")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(TypeError) as exc:
        validate_metadata(metadata)
    assert "order" in str(exc.value)
```

#### Schema Test 10: Range Validation - order Must Be 1-8

**Given**: ValidationTaskMetadata with order in valid range [1,8]
**When**: Schema validation is performed
**Then**: All values 1-8 should be accepted

```python
def test_order_valid_range():
    """
    Test that order field accepts all values from 1 to 8.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    for order_value in range(1, 9):  # 1-8 inclusive
        metadata = {
            "moduleId": f"module{order_value}",
            "moduleName": f"Module {order_value}",
            "order": order_value,  # Valid range
            "blocking": False,
            "validator": f"validators/module{order_value}-validator.md",
            "remediator": f"remediators/module{order_value}-remediation.md",
            "registry": f"registries/module{order_value}.yaml",
            "verifyModeOnly": False,
            "wm-setup": True
        }

        # Expected: validate_metadata(metadata) returns True
        # Actual: NameError - validate_metadata function doesn't exist
        assert validate_metadata(metadata) == True
```

**Test 10.2**: order below minimum (0)
```python
def test_order_below_minimum():
    """
    Test that order field rejects value below 1.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 0,  # INVALID: below minimum (1)
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: ValueError("Field 'order' must be in range [1,8], got 0")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValueError) as exc:
        validate_metadata(metadata)
    assert "order" in str(exc.value)
    assert "1" in str(exc.value) and "8" in str(exc.value)
```

**Test 10.3**: order above maximum (9)
```python
def test_order_above_maximum():
    """
    Test that order field rejects value above 8.

    Expected Result: FAIL - Schema validation not implemented yet
    """
    metadata = {
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "order": 9,  # INVALID: above maximum (8)
        "blocking": True,
        "validator": "validators/folder-validator.md",
        "remediator": "remediators/folder-remediation.md",
        "registry": "registries/folders.yaml",
        "verifyModeOnly": False,
        "wm-setup": True
    }

    # Expected: ValueError("Field 'order' must be in range [1,8], got 9")
    # Actual: NameError - validate_metadata function doesn't exist
    with pytest.raises(ValueError) as exc:
        validate_metadata(metadata)
    assert "order" in str(exc.value)
    assert "1" in str(exc.value) and "8" in str(exc.value)
```

### Expected Schema Test Output (RED Phase)

When schema validation tests are run, they should FAIL:

```
FAIL: test_valid_metadata_complete
  NameError: name 'validate_metadata' is not defined

FAIL: test_missing_module_id
  NameError: name 'validate_metadata' is not defined

FAIL: test_missing_blocking
  NameError: name 'validate_metadata' is not defined

FAIL: test_missing_order
  NameError: name 'validate_metadata' is not defined

FAIL: test_missing_validator
  NameError: name 'validate_metadata' is not defined

FAIL: test_missing_registry
  NameError: name 'validate_metadata' is not defined

FAIL: test_missing_wm-setup_marker
  NameError: name 'validate_metadata' is not defined

FAIL: test_blocking_type_string
  NameError: name 'validate_metadata' is not defined

FAIL: test_blocking_type_integer
  NameError: name 'validate_metadata' is not defined

FAIL: test_order_type_string
  NameError: name 'validate_metadata' is not defined

FAIL: test_order_type_float
  NameError: name 'validate_metadata' is not defined

FAIL: test_order_valid_range
  NameError: name 'validate_metadata' is not defined

FAIL: test_order_below_minimum
  NameError: name 'validate_metadata' is not defined

FAIL: test_order_above_maximum
  NameError: name 'validate_metadata' is not defined

14 schema validation tests failed, 0 passed
```

### TDD Status

#### createValidationTask Function
- [x] RED: Test documentation written
- [ ] GREEN: Implementation to make tests pass
- [ ] REFACTOR: Code quality improvements

#### ValidationTaskMetadata Schema
- [x] RED: Test documentation written
- [x] GREEN: TypeScript interface implemented (lines 99-192)
- [ ] REFACTOR: Code quality improvements

## Test Scenarios: executeValidationTask

The following test scenarios define expected behavior for the `executeValidationTask` function,
which executes a single validation module and updates task status with staleness prevention.

**Status: FAILING** - Function not yet implemented

### Staleness Prevention Tests

#### Test 1: TaskGet Called Before TaskUpdate

**Given**: A validation task with taskId "task-abc123" in status "pending"
**When**: executeValidationTask is called
**Then**: TaskGet must be called BEFORE TaskUpdate to prevent race conditions

```python
def test_taskget_before_taskupdate():
    """
    Test that TaskGet is called before TaskUpdate to prevent stale updates.

    Expected Result: FAIL - executeValidationTask not implemented yet

    Why: Multiple agents might update the same task simultaneously.
    TaskGet reads current state before updating to avoid overwriting
    concurrent changes.
    """
    task_id = "task-abc123"

    # Mock call tracker
    call_order = []

    def mock_task_get(taskId):
        call_order.append(("TaskGet", taskId))
        return {"taskId": task_id, "status": "pending"}

    def mock_task_update(taskId, **kwargs):
        call_order.append(("TaskUpdate", taskId))
        return {"taskId": task_id, "status": kwargs.get("status")}

    # Expected: executeValidationTask(task_id) calls TaskGet before TaskUpdate
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(task_id)

    # Verify call order
    assert len(call_order) >= 2, "Must have at least 2 calls"
    assert call_order[0][0] == "TaskGet", "First call must be TaskGet"
    assert call_order[1][0] == "TaskUpdate", "Second call must be TaskUpdate"
```

#### Test 2: Multiple TaskGet Calls Throughout Execution

**Given**: A validation task executing with multiple state changes
**When**: executeValidationTask updates status multiple times
**Then**: Each TaskUpdate must be preceded by TaskGet

```python
def test_multiple_taskget_calls():
    """
    Test that TaskGet is called before each TaskUpdate during execution.

    Expected Result: FAIL - executeValidationTask not implemented yet

    Execution flow:
    1. TaskGet → TaskUpdate (status: pending → in_progress)
    2. Run validator
    3. TaskGet → TaskUpdate (status: in_progress → completed/failed)
    """
    task_id = "task-abc123"
    call_order = []

    # Expected: Multiple TaskGet calls throughout execution
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(task_id)

    # Count TaskGet/TaskUpdate pairs
    taskget_count = sum(1 for call, _ in call_order if call == "TaskGet")
    taskupdate_count = sum(1 for call, _ in call_order if call == "TaskUpdate")

    assert taskget_count >= 2, "Must call TaskGet at least twice"
    assert taskget_count == taskupdate_count, "Each TaskUpdate must be preceded by TaskGet"
```

### Status Transition Tests

#### Test 3: Status Transition - Successful Validation

**Given**: A validation task in "pending" status
**When**: executeValidationTask runs and validator returns PASS
**Then**: Task status transitions: pending → in_progress → completed

```python
def test_status_transition_success():
    """
    Test status transitions for successful validation.

    Expected Result: FAIL - executeValidationTask not implemented yet
    """
    task_id = "task-abc123"
    status_history = []

    def mock_task_update(taskId, **kwargs):
        status = kwargs.get("status")
        if status:
            status_history.append(status)
        return {"taskId": taskId, "status": status}

    # Mock validator that returns PASS
    def mock_validator():
        return {"status": "PASS", "passRate": 100}

    # Expected: executeValidationTask(task_id) transitions statuses correctly
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(task_id, validator=mock_validator)

    # Verify status transitions
    assert status_history == ["in_progress", "completed"], \
        f"Expected [in_progress, completed], got {status_history}"
```

#### Test 4: Status Transition - Failed Validation

**Given**: A validation task in "pending" status
**When**: executeValidationTask runs and validator returns FAIL
**Then**: Task status transitions: pending → in_progress → failed

```python
def test_status_transition_failure():
    """
    Test status transitions for failed validation.

    Expected Result: FAIL - executeValidationTask not implemented yet
    """
    task_id = "task-abc123"
    status_history = []

    def mock_task_update(taskId, **kwargs):
        status = kwargs.get("status")
        if status:
            status_history.append(status)
        return {"taskId": taskId, "status": status}

    # Mock validator that returns FAIL
    def mock_validator():
        return {
            "status": "FAIL",
            "passRate": 0,
            "violations": ["Missing folder: .claude/skills"]
        }

    # Expected: executeValidationTask(task_id) transitions statuses correctly
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(task_id, validator=mock_validator)

    # Verify status transitions
    assert status_history == ["in_progress", "failed"], \
        f"Expected [in_progress, failed], got {status_history}"
```

#### Test 5: Status Transition - Exception During Execution

**Given**: A validation task in "pending" status
**When**: executeValidationTask encounters an exception
**Then**: Task status remains "in_progress" (requires manual recovery)

```python
def test_status_transition_exception():
    """
    Test that exceptions leave task in 'in_progress' state.

    Expected Result: FAIL - executeValidationTask not implemented yet

    Why: When an exception occurs, we don't automatically mark as
    'failed' because the failure might be transient (network issue,
    temporary file lock, etc.). Keeping it 'in_progress' allows
    manual investigation and potential retry.
    """
    task_id = "task-abc123"
    status_history = []

    def mock_task_update(taskId, **kwargs):
        status = kwargs.get("status")
        if status:
            status_history.append(status)
        return {"taskId": taskId, "status": status}

    # Mock validator that raises exception
    def mock_validator():
        raise Exception("Unexpected error during validation")

    # Expected: Exception is caught, status remains in_progress
    # Actual: NameError - executeValidationTask function doesn't exist
    try:
        executeValidationTask(task_id, validator=mock_validator)
    except Exception:
        pass  # Exception should be caught inside executeValidationTask

    # Verify status
    assert "in_progress" in status_history, \
        "Task must be set to in_progress before error"
    assert "completed" not in status_history, \
        "Task must NOT be marked completed on error"
    assert "failed" not in status_history, \
        "Task must NOT be auto-failed on exception (manual recovery required)"
```

### Blocking Failure Tests

#### Test 6: Blocking Module Failure Stops Pipeline

**Given**: Module 1 (Folder Structure) with blocking=True fails validation
**When**: executeValidationTask marks Module 1 as failed
**Then**: Subsequent tasks (Modules 2-8) should NOT be executed

```python
def test_blocking_failure_stops_pipeline():
    """
    Test that blocking module failure prevents subsequent task execution.

    Expected Result: FAIL - executeValidationTask not implemented yet

    Scenario:
    - Module 1 (blocking=True) fails
    - Pipeline should stop
    - Modules 2-8 should be marked as SKIPPED
    """
    # Module 1: Folder Structure (blocking)
    task1_id = "task-module1"
    task1_metadata = {
        "moduleId": "folders",
        "blocking": True,
        "order": 1
    }

    # Mock validator that fails
    def mock_validator_fail():
        return {"status": "FAIL", "passRate": 0, "blocking": True}

    # Expected: executeValidationTask returns blocking failure indicator
    # Actual: NameError - executeValidationTask function doesn't exist
    result = executeValidationTask(task1_id, validator=mock_validator_fail)

    # Verify blocking failure is returned
    assert result.get("blocking") == True, \
        "Blocking failure must be indicated in result"
    assert result.get("status") == "FAIL", \
        "Status must be FAIL"

    # Expected: Pipeline orchestrator checks this flag and skips remaining tasks
    # (This is tested in the orchestrator, not executeValidationTask itself)
```

#### Test 7: Non-Blocking Module Failure Continues Pipeline

**Given**: Module 2 (Skills) with blocking=False fails validation
**When**: executeValidationTask marks Module 2 as failed
**Then**: Subsequent tasks (Modules 3-8) should still execute

```python
def test_non_blocking_failure_continues():
    """
    Test that non-blocking module failure allows pipeline to continue.

    Expected Result: FAIL - executeValidationTask not implemented yet
    """
    task_id = "task-module2"
    task_metadata = {
        "moduleId": "skills",
        "blocking": False,
        "order": 2
    }

    # Mock validator that fails (non-blocking)
    def mock_validator_fail():
        return {"status": "FAIL", "passRate": 40, "blocking": False}

    # Expected: executeValidationTask returns non-blocking failure
    # Actual: NameError - executeValidationTask function doesn't exist
    result = executeValidationTask(task_id, validator=mock_validator_fail)

    # Verify non-blocking failure
    assert result.get("blocking") == False, \
        "Non-blocking failure must be indicated"
    assert result.get("status") == "FAIL", \
        "Status must be FAIL"

    # Pipeline continues to next module (tested in orchestrator)
```

### Validator/Remediator Invocation Tests

#### Test 8: Validator Always Called

**Given**: A validation task with validator path specified
**When**: executeValidationTask runs
**Then**: Validator must always be invoked

```python
def test_validator_always_called():
    """
    Test that validator is always invoked during execution.

    Expected Result: FAIL - executeValidationTask not implemented yet
    """
    task_id = "task-abc123"
    validator_called = False

    def mock_validator():
        nonlocal validator_called
        validator_called = True
        return {"status": "PASS", "passRate": 100}

    # Expected: Validator is invoked
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(task_id, validator=mock_validator)

    assert validator_called == True, \
        "Validator must be called during task execution"
```

#### Test 9: Remediator Called When Validation Fails

**Given**: A validation task that fails with remediator available
**When**: executeValidationTask runs in NEW_SETUP mode
**Then**: Remediator must be invoked after validator fails

```python
def test_remediator_called_on_failure():
    """
    Test that remediator is invoked when validation fails.

    Expected Result: FAIL - executeValidationTask not implemented yet
    """
    task_id = "task-abc123"
    validator_called = False
    remediator_called = False

    def mock_validator():
        nonlocal validator_called
        validator_called = True
        return {"status": "FAIL", "passRate": 0}

    def mock_remediator():
        nonlocal remediator_called
        remediator_called = True
        return {"actionsExecuted": ["Created .claude/skills folder"]}

    # Expected: Both validator and remediator are called
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(
        task_id,
        validator=mock_validator,
        remediator=mock_remediator,
        mode="NEW_SETUP"
    )

    assert validator_called == True, \
        "Validator must be called first"
    assert remediator_called == True, \
        "Remediator must be called when validation fails"
```

#### Test 10: Remediator NOT Called When Validation Passes

**Given**: A validation task that passes with remediator available
**When**: executeValidationTask runs
**Then**: Remediator must NOT be invoked

```python
def test_remediator_not_called_on_pass():
    """
    Test that remediator is NOT invoked when validation passes.

    Expected Result: FAIL - executeValidationTask not implemented yet
    """
    task_id = "task-abc123"
    validator_called = False
    remediator_called = False

    def mock_validator():
        nonlocal validator_called
        validator_called = True
        return {"status": "PASS", "passRate": 100}

    def mock_remediator():
        nonlocal remediator_called
        remediator_called = True
        return {"actionsExecuted": []}

    # Expected: Only validator is called, remediator is skipped
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(
        task_id,
        validator=mock_validator,
        remediator=mock_remediator,
        mode="NEW_SETUP"
    )

    assert validator_called == True, \
        "Validator must be called"
    assert remediator_called == False, \
        "Remediator must NOT be called when validation passes"
```

#### Test 11: Remediator NOT Called in VERIFY Mode

**Given**: A validation task that fails in VERIFY mode
**When**: executeValidationTask runs
**Then**: Remediator must NOT be invoked (report-only mode)

```python
def test_remediator_not_called_in_verify_mode():
    """
    Test that remediator is NOT invoked in VERIFY mode.

    Expected Result: FAIL - executeValidationTask not implemented yet

    Why: VERIFY mode is report-only. Even if validation fails,
    we only report the issues without auto-remediation.
    """
    task_id = "task-abc123"
    remediator_called = False

    def mock_validator():
        return {"status": "FAIL", "passRate": 0}

    def mock_remediator():
        nonlocal remediator_called
        remediator_called = True
        return {"actionsExecuted": []}

    # Expected: Remediator is NOT called in VERIFY mode
    # Actual: NameError - executeValidationTask function doesn't exist
    executeValidationTask(
        task_id,
        validator=mock_validator,
        remediator=mock_remediator,
        mode="VERIFY"
    )

    assert remediator_called == False, \
        "Remediator must NOT be called in VERIFY mode (report-only)"
```

#### Test 12: Remediator NOT Called When None

**Given**: A validation task with remediator=None (Runtime Checks module)
**When**: executeValidationTask runs and validation fails
**Then**: No remediator invocation should occur (no auto-remediation)

```python
def test_no_remediator_when_none():
    """
    Test that missing remediator is handled gracefully.

    Expected Result: FAIL - executeValidationTask not implemented yet

    Scenario: Module 7 (Runtime Checks) has no remediator because
    runtime issues cannot be auto-fixed (e.g., missing MCP servers,
    network issues, permission problems).
    """
    task_id = "task-runtime"
    task_metadata = {
        "moduleId": "runtime",
        "remediator": None  # No auto-remediation available
    }

    def mock_validator():
        return {"status": "FAIL", "passRate": 0}

    # Expected: executeValidationTask handles None remediator without error
    # Actual: NameError - executeValidationTask function doesn't exist
    result = executeValidationTask(
        task_id,
        validator=mock_validator,
        remediator=None,
        mode="NEW_SETUP"
    )

    # Verify task completed without error
    assert result.get("status") == "FAIL", \
        "Status must be FAIL (validation failed)"
    # No remediator invocation, no exception
```

### Expected Test Output (RED Phase)

When tests are run, they should FAIL with the following error:

```
FAIL: test_taskget_before_taskupdate
  NameError: name 'executeValidationTask' is not defined

FAIL: test_multiple_taskget_calls
  NameError: name 'executeValidationTask' is not defined

FAIL: test_status_transition_success
  NameError: name 'executeValidationTask' is not defined

FAIL: test_status_transition_failure
  NameError: name 'executeValidationTask' is not defined

FAIL: test_status_transition_exception
  NameError: name 'executeValidationTask' is not defined

FAIL: test_blocking_failure_stops_pipeline
  NameError: name 'executeValidationTask' is not defined

FAIL: test_non_blocking_failure_continues
  NameError: name 'executeValidationTask' is not defined

FAIL: test_validator_always_called
  NameError: name 'executeValidationTask' is not defined

FAIL: test_remediator_called_on_failure
  NameError: name 'executeValidationTask' is not defined

FAIL: test_remediator_not_called_on_pass
  NameError: name 'executeValidationTask' is not defined

FAIL: test_remediator_not_called_in_verify_mode
  NameError: name 'executeValidationTask' is not defined

FAIL: test_no_remediator_when_none
  NameError: name 'executeValidationTask' is not defined

12 tests failed, 0 passed
```

### TDD Status for executeValidationTask

#### executeValidationTask Function
- [x] RED: Test documentation written (12 test scenarios)
- [x] GREEN: Implementation completed with staleness prevention
- [ ] REFACTOR: Code quality improvements

## Test Scenarios: runValidationPipeline

The following test scenarios define expected behavior for the `runValidationPipeline` integration function.

**Status: FAILING** - Function not yet implemented (pseudocode exists but not functional)

### Integration Test 1: Task Creation Order

**Given**: VALIDATION_PIPELINE with 8 modules
**When**: runValidationPipeline is called
**Then**: All 8 validation Tasks created in correct order

```python
def test_pipeline_creates_all_tasks_in_order():
    """
    Test that runValidationPipeline creates all 8 Tasks sequentially.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Expected: Creates 8 Tasks in order 1-8
    # Actual: NameError - runValidationPipeline function doesn't exist
    result = runValidationPipeline(context, mode)

    # Verify all tasks were created
    tasks = TaskList(filter={"metadata.wm-setup": True})
    assert len(tasks) == 8, f"Expected 8 tasks, got {len(tasks)}"

    # Verify task order matches VALIDATION_PIPELINE
    for i, task in enumerate(tasks, start=1):
        expected_order = VALIDATION_PIPELINE[i-1]["order"]
        assert task.metadata["order"] == expected_order
        assert task.metadata["moduleId"] == VALIDATION_PIPELINE[i-1]["moduleId"]
```

### Integration Test 2: Task Subject Format

**Given**: VALIDATION_PIPELINE with defined moduleNames
**When**: runValidationPipeline creates Tasks
**Then**: Each Task subject follows format `[N/8] Validate {moduleName}`

```python
def test_pipeline_task_subject_format():
    """
    Test that all Tasks have correct subject format.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Expected: Tasks with formatted subjects
    # Actual: NameError - runValidationPipeline function doesn't exist
    result = runValidationPipeline(context, mode)

    # Verify subject format for each task
    expected_subjects = [
        "[1/8] Validate Folder Structure",
        "[2/8] Validate Skills",
        "[3/8] Validate Agents",
        "[4/8] Validate Hooks Configuration",
        "[5/8] Validate Hook Scripts",
        "[6/8] Validate Settings & Environment",
        "[7/8] Validate Runtime Checks",
        "[8/8] Validate Domain Structure"
    ]

    tasks = TaskList(filter={"metadata.wm-setup": True})
    for i, task in enumerate(tasks):
        assert task.subject == expected_subjects[i]
```

### Integration Test 3: Sequential Execution

**Given**: Pipeline with 8 validation modules
**When**: runValidationPipeline executes
**Then**: Tasks execute in order (Task N completes before Task N+1 starts)

```python
def test_pipeline_sequential_execution():
    """
    Test that Tasks execute sequentially, not in parallel.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Track execution order
    execution_log = []

    # Mock validator to log execution
    def mock_validator(validator_path, registry, context):
        execution_log.append({
            "validator": validator_path,
            "timestamp": datetime.now(),
            "status": "completed"
        })
        return {"status": "PASS", "passRate": 100}

    # Expected: Sequential execution (Task 1 → Task 2 → ... → Task 8)
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        result = runValidationPipeline(context, mode)

    # Verify execution order
    for i in range(len(execution_log) - 1):
        current = execution_log[i]
        next_item = execution_log[i + 1]

        # Next task should start AFTER current task completes
        assert next_item["timestamp"] >= current["timestamp"]

        # Validator paths should match pipeline order
        assert current["validator"] == VALIDATION_PIPELINE[i]["validator"]
```

### Integration Test 4: Blocking Behavior - Pipeline Stops on Blocking Failure

**Given**: Module 1 (Folder Structure) fails with blocking=True
**When**: runValidationPipeline executes
**Then**: Pipeline skips all remaining tasks (Modules 2-8)

```python
def test_blocking_failure_skips_remaining_tasks():
    """
    Test that blocking failure stops pipeline execution.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Mock validator - Module 1 fails with blocking
    def mock_validator(validator_path, registry, context):
        if "folder-validator" in validator_path:
            return {
                "status": "FAIL",
                "blocking": True,
                "passRate": 0,
                "issues": ["Critical: .claude folder missing"]
            }
        return {"status": "PASS", "passRate": 100}

    # Expected: Module 1 fails → Modules 2-8 skipped
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        result = runValidationPipeline(context, mode)

    # Verify pipeline results
    assert result["blocked"] == True
    assert result["modules"]["passed"] == 0
    assert result["modules"]["failed"] == 1
    assert result["modules"]["skipped"] == 7  # Modules 2-8 skipped

    # Verify skipped modules have correct reason
    skipped_results = [r for r in result["results"] if r["status"] == "SKIPPED"]
    assert len(skipped_results) == 7
    for skipped in skipped_results:
        assert "blocked by previous failure" in skipped["reason"].lower()
```

### Integration Test 5: Non-Blocking Failure - Pipeline Continues

**Given**: Module 2 (Skills) fails with blocking=False
**When**: runValidationPipeline executes
**Then**: Pipeline continues with Modules 3-8

```python
def test_nonblocking_failure_continues_pipeline():
    """
    Test that non-blocking failure allows pipeline to continue.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Mock validator - Module 2 fails without blocking
    def mock_validator(validator_path, registry, context):
        if "skills-validator" in validator_path:
            return {
                "status": "FAIL",
                "blocking": False,
                "passRate": 60,
                "issues": ["Warning: Missing skill documentation"]
            }
        return {"status": "PASS", "passRate": 100}

    # Expected: Module 2 fails → Modules 3-8 still execute
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        result = runValidationPipeline(context, mode)

    # Verify pipeline results
    assert result["blocked"] == False
    assert result["modules"]["failed"] == 1
    assert result["modules"]["passed"] == 7  # Modules 1, 3-8 pass
    assert result["modules"]["skipped"] == 0
    assert result["overall"] == "WARN"  # Overall status is WARN (not FAIL)
```

### Integration Test 6: Mode-Specific Behavior - NEW_SETUP Auto-Remediation

**Given**: Module with failures in NEW_SETUP mode
**When**: runValidationPipeline executes
**Then**: Auto-remediate all failures without prompting

```python
def test_new_setup_mode_auto_remediation():
    """
    Test that NEW_SETUP mode automatically remediates failures.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "NEW_SETUP"

    # Mock validator - Module 1 fails initially
    validator_call_count = 0
    def mock_validator(validator_path, registry, context):
        nonlocal validator_call_count
        validator_call_count += 1

        # First call fails, second call (after remediation) passes
        if "folder-validator" in validator_path:
            if validator_call_count == 1:
                return {
                    "status": "FAIL",
                    "blocking": True,
                    "issues": ["Missing .claude folder"]
                }
            else:
                return {"status": "PASS", "passRate": 100}
        return {"status": "PASS", "passRate": 100}

    # Mock remediator - auto-fix issues
    def mock_remediator(remediator_path, validation_result, context, mode):
        return {
            "actionsExecuted": ["Created .claude folder"],
            "actionsRequired": [],
            "status": "SUCCESS"
        }

    # Expected: Auto-remediation without user prompts
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        with patch('runRemediator', mock_remediator):
            result = runValidationPipeline(context, mode)

    # Verify remediation was executed
    assert result["actions"]["executed"] > 0
    assert result["blocked"] == False  # After remediation, pipeline continues
    assert validator_call_count >= 2  # Validator called twice (before and after remediation)
```

### Integration Test 7: Mode-Specific Behavior - UPDATE Interactive Remediation

**Given**: Module with failures in UPDATE mode
**When**: runValidationPipeline executes
**Then**: Prompt user before each remediation action

```python
def test_update_mode_interactive_remediation():
    """
    Test that UPDATE mode prompts for user confirmation before remediation.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "UPDATE"

    # Mock validator - Module 2 fails
    def mock_validator(validator_path, registry, context):
        if "skills-validator" in validator_path:
            return {
                "status": "FAIL",
                "blocking": False,
                "issues": ["Missing best-practices skill"]
            }
        return {"status": "PASS", "passRate": 100}

    # Mock remediator - interactive mode
    remediation_mode_used = None
    def mock_remediator(remediator_path, validation_result, context, mode):
        nonlocal remediation_mode_used
        remediation_mode_used = mode
        return {
            "actionsExecuted": ["Created best-practices skill"],
            "actionsRequired": [],
            "status": "SUCCESS"
        }

    # Expected: Remediator called with mode="interactive"
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        with patch('runRemediator', mock_remediator):
            result = runValidationPipeline(context, mode)

    # Verify interactive mode was used
    assert remediation_mode_used == "interactive"
```

### Integration Test 8: Mode-Specific Behavior - VERIFY Report Only

**Given**: Module with failures in VERIFY mode
**When**: runValidationPipeline executes
**Then**: No remediation attempted, report only

```python
def test_verify_mode_report_only():
    """
    Test that VERIFY mode does not attempt any remediation.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Mock validator - Module 2 fails
    def mock_validator(validator_path, registry, context):
        if "skills-validator" in validator_path:
            return {
                "status": "FAIL",
                "blocking": False,
                "issues": ["Missing best-practices skill"]
            }
        return {"status": "PASS", "passRate": 100}

    # Mock remediator - should NOT be called
    remediator_called = False
    def mock_remediator(remediator_path, validation_result, context, mode):
        nonlocal remediator_called
        remediator_called = True
        return {"actionsExecuted": [], "actionsRequired": [], "status": "SKIPPED"}

    # Expected: No remediation in VERIFY mode
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        with patch('runRemediator', mock_remediator):
            result = runValidationPipeline(context, mode)

    # Verify remediator was NOT called
    assert remediator_called == False
    assert result["actions"]["executed"] == 0
    assert result["actions"]["required"] > 0  # Issues reported but not fixed
```

### Integration Test 9: Module 7 Runtime Checks - verifyModeOnly

**Given**: Pipeline in NEW_SETUP mode
**When**: runValidationPipeline reaches Module 7 (Runtime Checks)
**Then**: Module 7 is skipped (verifyModeOnly=True)

```python
def test_runtime_checks_skipped_in_new_setup_mode():
    """
    Test that Module 7 (Runtime Checks) is skipped in NEW_SETUP mode.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "NEW_SETUP"

    # Mock validator - track which modules are called
    called_validators = []
    def mock_validator(validator_path, registry, context):
        called_validators.append(validator_path)
        return {"status": "PASS", "passRate": 100}

    # Expected: Module 7 skipped in NEW_SETUP mode
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        result = runValidationPipeline(context, mode)

    # Verify Module 7 was skipped
    assert "onboarding/runtime-validator.md" not in called_validators

    # Verify Module 7 appears in results as SKIPPED
    runtime_result = next(
        r for r in result["results"]
        if r["moduleId"] == "runtime"
    )
    assert runtime_result["status"] == "SKIPPED"
    assert "only runs in VERIFY mode" in runtime_result["reason"].lower()
```

### Integration Test 10: Module 7 Runtime Checks - Executes in VERIFY Mode

**Given**: Pipeline in VERIFY mode
**When**: runValidationPipeline reaches Module 7 (Runtime Checks)
**Then**: Module 7 executes normally

```python
def test_runtime_checks_execute_in_verify_mode():
    """
    Test that Module 7 (Runtime Checks) executes in VERIFY mode.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Mock validator - track which modules are called
    called_validators = []
    def mock_validator(validator_path, registry, context):
        called_validators.append(validator_path)
        return {"status": "PASS", "passRate": 100}

    # Expected: Module 7 executes in VERIFY mode
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        result = runValidationPipeline(context, mode)

    # Verify Module 7 was executed
    assert "onboarding/runtime-validator.md" in called_validators

    # Verify Module 7 appears in results with validation status (not SKIPPED)
    runtime_result = next(
        r for r in result["results"]
        if r["moduleId"] == "runtime"
    )
    assert runtime_result["status"] in ["PASS", "WARN", "FAIL"]  # Any validation status
    assert runtime_result["status"] != "SKIPPED"
```

### Integration Test 11: Pipeline Result Aggregation

**Given**: Pipeline completes with mixed results (PASS, WARN, FAIL)
**When**: runValidationPipeline finishes
**Then**: Return aggregated summary with correct counts

```python
def test_pipeline_result_aggregation():
    """
    Test that pipeline result includes correct aggregated counts.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Mock validator - mixed results
    def mock_validator(validator_path, registry, context):
        if "folder-validator" in validator_path:
            return {"status": "PASS", "passRate": 100}
        elif "skills-validator" in validator_path:
            return {"status": "WARN", "passRate": 85}
        elif "agents-validator" in validator_path:
            return {"status": "FAIL", "blocking": False, "passRate": 40}
        else:
            return {"status": "PASS", "passRate": 100}

    # Expected: Aggregated result summary
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        result = runValidationPipeline(context, mode)

    # Verify aggregated counts
    assert result["modules"]["total"] == 8
    assert result["modules"]["passed"] == 5  # Modules 1, 4, 5, 6, 8
    assert result["modules"]["warned"] == 1  # Module 2
    assert result["modules"]["failed"] == 1  # Module 3
    assert result["modules"]["skipped"] == 0  # All modules ran (Module 7 runs in VERIFY mode)

    # Verify overall status
    assert result["overall"] == "WARN"  # Has warnings and failures but non-blocking
    assert result["blocked"] == False
```

### Integration Test 12: Pipeline Result - Individual Module Details

**Given**: Pipeline completes successfully
**When**: runValidationPipeline finishes
**Then**: Return array of individual module results with all details

```python
def test_pipeline_result_module_details():
    """
    Test that pipeline result includes detailed results for each module.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    context = ValidationContext(project_root="/test/project")
    mode = "VERIFY"

    # Mock validator
    def mock_validator(validator_path, registry, context):
        return {
            "status": "PASS",
            "passRate": 100,
            "checksRun": 5,
            "checksPassed": 5,
            "issues": []
        }

    # Expected: Detailed results array
    # Actual: NameError - runValidationPipeline function doesn't exist
    with patch('runValidator', mock_validator):
        result = runValidationPipeline(context, mode)

    # Verify results array structure
    assert "results" in result
    assert len(result["results"]) == 8  # One result per module

    # Verify each result has required fields
    for module_result in result["results"]:
        assert "moduleId" in module_result
        assert "moduleName" in module_result
        assert "order" in module_result
        assert "status" in module_result
        assert module_result["status"] in ["PASS", "WARN", "FAIL", "SKIPPED"]
```

### Integration Test 13: Progress Display During Execution

**Given**: Pipeline is executing Module 3
**When**: printPipelineProgress is called
**Then**: Display shows completed (1-2), running (3), waiting (4-8)

```python
def test_pipeline_progress_display():
    """
    Test that pipeline shows real-time progress during execution.

    Expected Result: FAIL - runValidationPipeline not implemented yet
    """
    results = [
        {"status": "PASS", "passRate": 100},  # Module 1 completed
        {"status": "WARN", "passRate": 85}    # Module 2 completed
    ]
    current_step = 3  # Module 3 currently running
    total_steps = 8

    # Expected: Progress table showing status for each module
    # Actual: Function exists (defined in validation-orchestrator.md)
    progress_output = printPipelineProgress(results, current_step, total_steps)

    # Verify progress table format
    assert "[1/8] Folder Structure" in progress_output
    assert "✅ PASS" in progress_output  # Module 1 completed
    assert "[2/8] Skills" in progress_output
    assert "⚠️ WARN" in progress_output  # Module 2 completed
    assert "[3/8] Agents" in progress_output
    assert "⏳ RUNNING" in progress_output  # Module 3 in progress
    assert "[4/8] Hooks Configuration" in progress_output
    assert "⏸️ WAIT" in progress_output  # Module 4 waiting
```

### Expected Integration Test Output (RED Phase)

When integration tests are run, they should FAIL with the following errors:

```
FAIL: test_pipeline_creates_all_tasks_in_order
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_pipeline_task_subject_format
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_pipeline_sequential_execution
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_blocking_failure_skips_remaining_tasks
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_nonblocking_failure_continues_pipeline
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_new_setup_mode_auto_remediation
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_update_mode_interactive_remediation
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_verify_mode_report_only
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_runtime_checks_skipped_in_new_setup_mode
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_runtime_checks_execute_in_verify_mode
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_pipeline_result_aggregation
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_pipeline_result_module_details
  NameError: name 'runValidationPipeline' is not defined

FAIL: test_pipeline_progress_display
  NameError: name 'printPipelineProgress' is not defined

13 integration tests failed, 0 passed
```

## Test Scenarios: verifyModeOnly Handling

**Purpose**: Test the `verifyModeOnly` flag that allows modules to be skipped in certain modes (e.g., Module 7 Runtime Checks only runs in VERIFY mode).

**TDD Phase**: RED (Test Documentation Only - Implementation Not Started)

### Test Category 1: Module 7 Skip Logic

#### Test 1.1: Module 7 Skipped in NEW_SETUP Mode

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Pipeline configured with 8 modules
- Module 7 (Runtime Checks) has `verifyModeOnly: True`
- Mode is "NEW_SETUP"

**When**:
- `runValidationPipeline(context, "NEW_SETUP")` is called

**Then**:
- Module 7 is NOT included in task creation
- Only 7 tasks are created (Modules 1-6, 8)
- Module 7 does NOT appear in `task_ids` list

```python
def test_module_7_skipped_in_new_setup_mode():
    """
    Test that Module 7 (verifyModeOnly=True) is skipped in NEW_SETUP mode.

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    context = {"claude_dir": ".claude"}
    mode = "NEW_SETUP"

    # Expected: 7 tasks created (Module 7 skipped)
    # Actual: shouldSkipModule function doesn't exist
    result = runValidationPipeline(context, mode)

    # Verify Module 7 was NOT included in task creation
    task_subjects = [task.subject for task in result["tasks"]]
    assert not any("Runtime Checks" in subject for subject in task_subjects)

    # Verify only 7 tasks created
    assert len(result["tasks"]) == 7

    # Verify Module 7 appears in results as SKIPPED
    runtime_result = next(
        (r for r in result["results"] if r["moduleId"] == "runtime"),
        None
    )
    assert runtime_result is not None
    assert runtime_result["status"] == "SKIPPED"
    assert "verifyModeOnly" in runtime_result["reason"]
```

#### Test 1.2: Module 7 Skipped in UPDATE Mode

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Pipeline configured with 8 modules
- Module 7 (Runtime Checks) has `verifyModeOnly: True`
- Mode is "UPDATE"

**When**:
- `runValidationPipeline(context, "UPDATE")` is called

**Then**:
- Module 7 is NOT included in task creation
- Only 7 tasks are created (Modules 1-6, 8)
- Module 7 does NOT appear in `task_ids` list

```python
def test_module_7_skipped_in_update_mode():
    """
    Test that Module 7 (verifyModeOnly=True) is skipped in UPDATE mode.

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    context = {"claude_dir": ".claude"}
    mode = "UPDATE"

    # Expected: 7 tasks created (Module 7 skipped)
    # Actual: shouldSkipModule function doesn't exist
    result = runValidationPipeline(context, mode)

    # Verify Module 7 was NOT included in task creation
    task_subjects = [task.subject for task in result["tasks"]]
    assert not any("Runtime Checks" in subject for subject in task_subjects)

    # Verify only 7 tasks created
    assert len(result["tasks"]) == 7

    # Verify Module 7 appears in results as SKIPPED
    runtime_result = next(
        (r for r in result["results"] if r["moduleId"] == "runtime"),
        None
    )
    assert runtime_result is not None
    assert runtime_result["status"] == "SKIPPED"
    assert "verifyModeOnly" in runtime_result["reason"]
```

#### Test 1.3: Module 7 Included in VERIFY Mode

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Pipeline configured with 8 modules
- Module 7 (Runtime Checks) has `verifyModeOnly: True`
- Mode is "VERIFY"

**When**:
- `runValidationPipeline(context, "VERIFY")` is called

**Then**:
- Module 7 IS included in task creation
- All 8 tasks are created (Modules 1-8)
- Module 7 appears in `task_ids` list

```python
def test_module_7_included_in_verify_mode():
    """
    Test that Module 7 (verifyModeOnly=True) is included in VERIFY mode.

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    context = {"claude_dir": ".claude"}
    mode = "VERIFY"

    # Expected: 8 tasks created (Module 7 included)
    # Actual: shouldSkipModule function doesn't exist
    result = runValidationPipeline(context, mode)

    # Verify Module 7 WAS included in task creation
    task_subjects = [task.subject for task in result["tasks"]]
    assert any("Runtime Checks" in subject for subject in task_subjects)

    # Verify all 8 tasks created
    assert len(result["tasks"]) == 8

    # Verify Module 7 appears in results with validation status (not SKIPPED)
    runtime_result = next(
        (r for r in result["results"] if r["moduleId"] == "runtime"),
        None
    )
    assert runtime_result is not None
    assert runtime_result["status"] in ["PASS", "WARN", "FAIL"]
```

### Test Category 2: shouldSkipModule Function

#### Test 2.1: Skip When verifyModeOnly=True AND mode != VERIFY

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Module has `verifyModeOnly: True`
- Mode is "NEW_SETUP" (or "UPDATE")

**When**:
- `shouldSkipModule(step, mode)` is called

**Then**:
- Function returns `True` (module should be skipped)

```python
def test_should_skip_module_verify_only_in_new_setup():
    """
    Test that shouldSkipModule returns True when verifyModeOnly=True and mode != VERIFY.

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    step = {
        "order": 7,
        "moduleId": "runtime",
        "moduleName": "Runtime Checks",
        "verifyModeOnly": True
    }

    # Expected: Returns True (skip module)
    # Actual: NameError - shouldSkipModule doesn't exist
    result = shouldSkipModule(step, "NEW_SETUP")
    assert result is True

    # Also test UPDATE mode
    result = shouldSkipModule(step, "UPDATE")
    assert result is True
```

#### Test 2.2: Do NOT Skip When verifyModeOnly=False

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Module has `verifyModeOnly: False`
- Mode is "NEW_SETUP" (any mode)

**When**:
- `shouldSkipModule(step, mode)` is called

**Then**:
- Function returns `False` (module should NOT be skipped)

```python
def test_should_not_skip_module_verify_only_false():
    """
    Test that shouldSkipModule returns False when verifyModeOnly=False.

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    step = {
        "order": 1,
        "moduleId": "folders",
        "moduleName": "Folder Structure",
        "verifyModeOnly": False
    }

    # Expected: Returns False (don't skip module)
    # Actual: NameError - shouldSkipModule doesn't exist
    result = shouldSkipModule(step, "NEW_SETUP")
    assert result is False

    result = shouldSkipModule(step, "UPDATE")
    assert result is False

    result = shouldSkipModule(step, "VERIFY")
    assert result is False
```

#### Test 2.3: Do NOT Skip When verifyModeOnly=True AND mode=VERIFY

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Module has `verifyModeOnly: True`
- Mode is "VERIFY"

**When**:
- `shouldSkipModule(step, mode)` is called

**Then**:
- Function returns `False` (module should NOT be skipped)

```python
def test_should_not_skip_module_verify_mode():
    """
    Test that shouldSkipModule returns False when verifyModeOnly=True but mode=VERIFY.

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    step = {
        "order": 7,
        "moduleId": "runtime",
        "moduleName": "Runtime Checks",
        "verifyModeOnly": True
    }

    # Expected: Returns False (don't skip in VERIFY mode)
    # Actual: NameError - shouldSkipModule doesn't exist
    result = shouldSkipModule(step, "VERIFY")
    assert result is False
```

#### Test 2.4: Do NOT Skip When verifyModeOnly Not Set (Default Behavior)

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Module does NOT have `verifyModeOnly` field (field is omitted)
- Mode is any valid mode

**When**:
- `shouldSkipModule(step, mode)` is called

**Then**:
- Function returns `False` (module should NOT be skipped - default behavior)

```python
def test_should_not_skip_module_field_not_set():
    """
    Test that shouldSkipModule returns False when verifyModeOnly field is not set.

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    step = {
        "order": 2,
        "moduleId": "skills",
        "moduleName": "Skills"
        # verifyModeOnly field intentionally omitted
    }

    # Expected: Returns False (default behavior - don't skip)
    # Actual: NameError - shouldSkipModule doesn't exist
    result = shouldSkipModule(step, "NEW_SETUP")
    assert result is False

    result = shouldSkipModule(step, "UPDATE")
    assert result is False

    result = shouldSkipModule(step, "VERIFY")
    assert result is False
```

### Test Category 3: Task Count Validation

#### Test 3.1: Task Count in NEW_SETUP Mode

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Pipeline has 8 modules total
- Module 7 has `verifyModeOnly: True`
- Mode is "NEW_SETUP"

**When**:
- `runValidationPipeline(context, "NEW_SETUP")` is called

**Then**:
- Exactly 7 tasks are created (Module 7 skipped)
- Task order is: Modules 1, 2, 3, 4, 5, 6, 8

```python
def test_task_count_new_setup_mode():
    """
    Test that 7 tasks are created in NEW_SETUP mode (Module 7 skipped).

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    context = {"claude_dir": ".claude"}
    mode = "NEW_SETUP"

    # Expected: 7 tasks created
    # Actual: shouldSkipModule doesn't exist, so all 8 modules might be included
    result = runValidationPipeline(context, mode)

    # Verify exact count
    assert len(result["tasks"]) == 7

    # Verify module IDs in tasks (Module 7 'runtime' should NOT be present)
    created_module_ids = [
        task.metadata["moduleId"] for task in result["tasks"]
    ]
    expected_module_ids = [
        "folders", "skills", "agents", "hooks-config",
        "hooks-impl", "plugin-json", "marketplace-json"
    ]
    assert created_module_ids == expected_module_ids

    # Verify 'runtime' module is NOT in created tasks
    assert "runtime" not in created_module_ids
```

#### Test 3.2: Task Count in UPDATE Mode

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Pipeline has 8 modules total
- Module 7 has `verifyModeOnly: True`
- Mode is "UPDATE"

**When**:
- `runValidationPipeline(context, "UPDATE")` is called

**Then**:
- Exactly 7 tasks are created (Module 7 skipped)
- Task order is: Modules 1, 2, 3, 4, 5, 6, 8

```python
def test_task_count_update_mode():
    """
    Test that 7 tasks are created in UPDATE mode (Module 7 skipped).

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    context = {"claude_dir": ".claude"}
    mode = "UPDATE"

    # Expected: 7 tasks created
    # Actual: shouldSkipModule doesn't exist, so all 8 modules might be included
    result = runValidationPipeline(context, mode)

    # Verify exact count
    assert len(result["tasks"]) == 7

    # Verify module IDs in tasks (Module 7 'runtime' should NOT be present)
    created_module_ids = [
        task.metadata["moduleId"] for task in result["tasks"]
    ]
    expected_module_ids = [
        "folders", "skills", "agents", "hooks-config",
        "hooks-impl", "plugin-json", "marketplace-json"
    ]
    assert created_module_ids == expected_module_ids

    # Verify 'runtime' module is NOT in created tasks
    assert "runtime" not in created_module_ids
```

#### Test 3.3: Task Count in VERIFY Mode

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Pipeline has 8 modules total
- Module 7 has `verifyModeOnly: True`
- Mode is "VERIFY"

**When**:
- `runValidationPipeline(context, "VERIFY")` is called

**Then**:
- Exactly 8 tasks are created (all modules included)
- Task order is: Modules 1, 2, 3, 4, 5, 6, 7, 8

```python
def test_task_count_verify_mode():
    """
    Test that 8 tasks are created in VERIFY mode (all modules included).

    Expected Result: FAIL - shouldSkipModule function not implemented yet
    """
    context = {"claude_dir": ".claude"}
    mode = "VERIFY"

    # Expected: 8 tasks created (Module 7 included)
    # Actual: shouldSkipModule doesn't exist, behavior may be inconsistent
    result = runValidationPipeline(context, mode)

    # Verify exact count
    assert len(result["tasks"]) == 8

    # Verify module IDs in tasks (ALL modules including 'runtime' should be present)
    created_module_ids = [
        task.metadata["moduleId"] for task in result["tasks"]
    ]
    expected_module_ids = [
        "folders", "skills", "agents", "hooks-config",
        "hooks-impl", "plugin-json", "runtime", "marketplace-json"
    ]
    assert created_module_ids == expected_module_ids

    # Verify 'runtime' module IS in created tasks
    assert "runtime" in created_module_ids
```

### Test Category 4: Edge Cases

#### Test 4.1: Multiple Modules with verifyModeOnly

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Two modules have `verifyModeOnly: True` (e.g., Module 7 and a hypothetical Module 9)
- Mode is "NEW_SETUP"

**When**:
- `runValidationPipeline(context, "NEW_SETUP")` is called

**Then**:
- Both modules are skipped
- Task count reflects both skips

```python
def test_multiple_modules_with_verify_mode_only():
    """
    Test that multiple modules with verifyModeOnly=True are all skipped.

    Expected Result: FAIL - shouldSkipModule function not implemented yet

    Note: This tests scalability of the skip logic for future modules.
    """
    # Hypothetical pipeline with two verifyModeOnly modules
    # This test documents expected behavior if more modules are added

    context = {"claude_dir": ".claude"}
    mode = "NEW_SETUP"

    # Expected: Both verifyModeOnly modules skipped
    # Actual: shouldSkipModule doesn't exist
    result = runValidationPipeline(context, mode)

    # If Module 7 and Module 9 both have verifyModeOnly=True
    # Then only 6 tasks should be created (8 total - 2 skipped)
    # This assertion will need adjustment based on actual pipeline config

    verify_only_modules = [
        m for m in VALIDATION_PIPELINE
        if m.get("verifyModeOnly", False)
    ]
    expected_task_count = len(VALIDATION_PIPELINE) - len(verify_only_modules)

    assert len(result["tasks"]) == expected_task_count
```

#### Test 4.2: Invalid Mode Handling

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Module has `verifyModeOnly: True`
- Mode is invalid (e.g., "INVALID_MODE")

**When**:
- `shouldSkipModule(step, "INVALID_MODE")` is called

**Then**:
- Function should handle gracefully (skip by default for safety)
- OR raise ValueError for invalid mode

```python
def test_should_skip_module_invalid_mode():
    """
    Test shouldSkipModule behavior with invalid mode.

    Expected Result: FAIL - shouldSkipModule function not implemented yet

    Design Decision: Should invalid mode skip (safe default) or raise error?
    """
    step = {
        "order": 7,
        "moduleId": "runtime",
        "verifyModeOnly": True
    }

    # Option 1: Skip by default (safe behavior)
    result = shouldSkipModule(step, "INVALID_MODE")
    assert result is True  # Skip for unknown modes

    # Option 2: Raise error (strict validation)
    # with pytest.raises(ValueError, match="Invalid mode"):
    #     shouldSkipModule(step, "INVALID_MODE")
```

### Expected Test Output (RED Phase)

When these tests are run, they should ALL FAIL with the following error:

```
FAIL: test_module_7_skipped_in_new_setup_mode
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_module_7_skipped_in_update_mode
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_module_7_included_in_verify_mode
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_should_skip_module_verify_only_in_new_setup
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_should_not_skip_module_verify_only_false
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_should_not_skip_module_verify_mode
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_should_not_skip_module_field_not_set
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_task_count_new_setup_mode
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_task_count_update_mode
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_task_count_verify_mode
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_multiple_modules_with_verify_mode_only
  NameError: name 'shouldSkipModule' is not defined

FAIL: test_should_skip_module_invalid_mode
  NameError: name 'shouldSkipModule' is not defined

12 tests failed, 0 passed
```

### Implementation Notes (for GREEN Phase)

When implementing `shouldSkipModule`, consider:

1. **Function Signature**:
   ```python
   def shouldSkipModule(step: dict, mode: str) -> bool:
       """
       Determine if a module should be skipped based on verifyModeOnly flag.

       Args:
           step: Module configuration from VALIDATION_PIPELINE
           mode: wm-setup mode ("NEW_SETUP" | "UPDATE" | "VERIFY")

       Returns:
           True if module should be skipped, False otherwise
       """
   ```

2. **Logic**:
   - Check if `verifyModeOnly` exists in step
   - If `verifyModeOnly=True` AND `mode != "VERIFY"` → return True
   - Otherwise → return False

3. **Integration Point**:
   - Call in `runValidationPipeline` before creating each task:
     ```python
     for step in VALIDATION_PIPELINE:
         if shouldSkipModule(step, mode):
             continue  # Skip task creation
         task_id = createValidationTask(step, mode)
     ```

### TDD Status for verifyModeOnly Handling

#### shouldSkipModule Function (PHASE 3)
- [x] RED: Test scenarios documented (12 test cases)
- [ ] GREEN: Implementation not started
- [ ] REFACTOR: Not started

### TDD Status for runValidationPipeline

#### runValidationPipeline Function (PHASE 2)
- [x] RED: Integration test documentation written
- [x] GREEN: Implementation with two-phase execution pattern completed
- [ ] REFACTOR: Code quality improvements

## Test Scenarios: Mode-Specific Remediation

**Phase**: PHASE 3 - RED
**Status**: [ ] Test documentation written
**Purpose**: Define test scenarios for mode-specific remediation logic

The following test scenarios define expected behavior for mode-specific remediation handling across the orchestrator pipeline. These tests ensure that NEW_SETUP, UPDATE, and VERIFY modes behave correctly when failures are detected.

### Test Category 1: NEW_SETUP Mode - Auto-Remediation

#### Test 1.1: Auto-Remediate Without User Prompts

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is NEW_SETUP
- Validation fails with remediable issues
- Remediator is available for the module

**When**:
- executeValidationTask processes the failure
- Remediation is triggered

**Then**:
- Remediator is called automatically without user prompts
- Task metadata includes `remediation.autoExecuted: true`
- Task metadata includes `remediation.userApproved: null` (no user interaction)
- Re-validation occurs after remediation
- Task status updates to PASS if remediation succeeds

```python
def test_new_setup_auto_remediation():
    """
    Test that NEW_SETUP mode automatically remediates without prompting.

    Expected Result: FAIL - Mode-specific remediation logic not implemented
    """
    task = create_validation_task(
        module_id="folders",
        validator_path="validators/folder-validator.md",
        remediator_path="remediators/folder-remediation.md",
        registry_path="registries/folders.yaml"
    )

    # Mock validation failure
    validation_result = {
        "status": "FAIL",
        "passRate": 0,
        "issues": ["Missing .claude folder"],
        "blocking": True
    }

    # Mock successful remediation
    remediation_result = {
        "actionsExecuted": ["Created .claude folder"],
        "actionsRequired": [],
        "status": "SUCCESS"
    }

    mode = "NEW_SETUP"

    # Expected: Auto-remediation without AskUserQuestion
    # Actual: Mode-specific logic not implemented yet
    task_result = execute_validation_task(task, mode)

    # Assertions
    assert task_result.metadata["remediation"]["autoExecuted"] == True
    assert task_result.metadata["remediation"]["userApproved"] is None
    assert task_result.metadata["remediation"]["actionsExecuted"] > 0
    assert task_result.status == "PASS"  # After remediation
```

#### Test 1.2: Track Remediation Metadata

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is NEW_SETUP
- Validation fails
- Remediation executes automatically

**When**:
- Remediation completes

**Then**:
- Task metadata includes `remediation.timestamp`
- Task metadata includes `remediation.actionsExecuted` (list)
- Task metadata includes `remediation.actionsRequired` (list)
- Task metadata includes `remediation.revalidated: true`
- Task is updated via TaskUpdate tool

```python
def test_new_setup_remediation_metadata_tracking():
    """
    Test that remediation metadata is properly tracked in NEW_SETUP mode.

    Expected Result: FAIL - Metadata tracking not implemented
    """
    task = create_validation_task(module_id="skills")
    mode = "NEW_SETUP"

    validation_result = {"status": "FAIL", "issues": ["Missing skill X"]}
    remediation_result = {
        "actionsExecuted": ["Created skill X"],
        "actionsRequired": [],
        "status": "SUCCESS"
    }

    # Expected: Metadata tracked in Task
    # Actual: Not implemented yet
    task_result = execute_validation_task(task, mode)

    # Verify metadata structure
    remediation_metadata = task_result.metadata["remediation"]
    assert "timestamp" in remediation_metadata
    assert remediation_metadata["actionsExecuted"] == ["Created skill X"]
    assert remediation_metadata["actionsRequired"] == []
    assert remediation_metadata["revalidated"] == True
```

#### Test 1.3: Re-Validate After Remediation

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is NEW_SETUP
- Initial validation fails
- Remediation executes and completes

**When**:
- Remediation finishes

**Then**:
- Validator is called again with same parameters
- Second validation result is captured
- Task metadata includes `validation.revalidationResult`
- Task status reflects final validation state

```python
def test_new_setup_revalidation_after_remediation():
    """
    Test that re-validation occurs after remediation in NEW_SETUP mode.

    Expected Result: FAIL - Re-validation logic not implemented
    """
    task = create_validation_task(module_id="folders")
    mode = "NEW_SETUP"

    # Mock validator - first fails, second passes
    validator_call_count = 0
    def mock_validator(validator_path, registry, context):
        nonlocal validator_call_count
        validator_call_count += 1

        if validator_call_count == 1:
            return {"status": "FAIL", "passRate": 0, "issues": ["Missing folder"]}
        else:
            return {"status": "PASS", "passRate": 100, "issues": []}

    # Expected: Validator called twice
    # Actual: Re-validation not implemented
    with patch('run_validator', mock_validator):
        task_result = execute_validation_task(task, mode)

    # Assertions
    assert validator_call_count == 2, "Validator should be called twice"
    assert task_result.metadata["validation"]["revalidationResult"]["status"] == "PASS"
    assert task_result.status == "PASS"
```

### Test Category 2: UPDATE Mode - Interactive Remediation

#### Test 2.1: Require User Confirmation Before Remediation

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is UPDATE
- Validation fails with remediable issues
- User confirmation is required

**When**:
- executeValidationTask processes the failure
- Remediation is about to be triggered

**Then**:
- AskUserQuestion is called to confirm remediation
- Question includes failure details and proposed actions
- Remediation only executes if user approves
- Task metadata includes `remediation.userApproved: true/false`

```python
def test_update_mode_interactive_remediation():
    """
    Test that UPDATE mode requires user confirmation before remediation.

    Expected Result: FAIL - Interactive mode not implemented
    """
    task = create_validation_task(module_id="skills")
    mode = "UPDATE"

    validation_result = {
        "status": "FAIL",
        "issues": ["Missing best-practices skill"]
    }

    remediation_result = {
        "actionsExecuted": ["Created best-practices skill"],
        "actionsRequired": [],
        "status": "SUCCESS"
    }

    # Mock user approval
    user_response = "yes"

    # Expected: AskUserQuestion called before remediation
    # Actual: Interactive mode not implemented
    with patch('AskUserQuestion', return_value=user_response):
        task_result = execute_validation_task(task, mode)

    # Assertions
    assert AskUserQuestion.called == True
    assert "Missing best-practices skill" in AskUserQuestion.call_args[0][0]
    assert task_result.metadata["remediation"]["userApproved"] == True
    assert task_result.metadata["remediation"]["actionsExecuted"] > 0
```

#### Test 2.2: Skip Remediation When User Declines

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is UPDATE
- Validation fails
- User declines remediation

**When**:
- User responds "no" to remediation prompt

**Then**:
- Remediator is NOT called
- Task metadata includes `remediation.userApproved: false`
- Task metadata includes `remediation.userDeclined: true`
- Task status remains FAIL
- No re-validation occurs

```python
def test_update_mode_skip_remediation_on_decline():
    """
    Test that remediation is skipped when user declines in UPDATE mode.

    Expected Result: FAIL - User decline handling not implemented
    """
    task = create_validation_task(module_id="agents")
    mode = "UPDATE"

    validation_result = {"status": "FAIL", "issues": ["Invalid agent config"]}

    # Mock user decline
    user_response = "no"
    remediator_called = False

    def mock_remediator(*args):
        nonlocal remediator_called
        remediator_called = True
        return {"actionsExecuted": [], "status": "SKIPPED"}

    # Expected: Remediator NOT called
    # Actual: User decline not implemented
    with patch('AskUserQuestion', return_value=user_response):
        with patch('run_remediator', mock_remediator):
            task_result = execute_validation_task(task, mode)

    # Assertions
    assert remediator_called == False, "Remediator should not be called"
    assert task_result.metadata["remediation"]["userApproved"] == False
    assert task_result.metadata["remediation"]["userDeclined"] == True
    assert task_result.status == "FAIL"
```

#### Test 2.3: Proceed with Remediation on User Approval

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is UPDATE
- Validation fails
- User approves remediation

**When**:
- User responds "yes" to remediation prompt

**Then**:
- Remediator is called with validation result and context
- Remediation actions are executed
- Re-validation occurs
- Task metadata tracks approval and actions
- Task status updates based on re-validation

```python
def test_update_mode_proceed_on_user_approval():
    """
    Test that remediation proceeds when user approves in UPDATE mode.

    Expected Result: FAIL - User approval flow not implemented
    """
    task = create_validation_task(module_id="hooks-config")
    mode = "UPDATE"

    validation_result = {"status": "FAIL", "issues": ["Invalid hooks.yaml"]}
    remediation_result = {
        "actionsExecuted": ["Fixed hooks.yaml syntax"],
        "status": "SUCCESS"
    }

    # Mock user approval
    user_response = "yes"
    remediator_called = False

    def mock_remediator(*args):
        nonlocal remediator_called
        remediator_called = True
        return remediation_result

    # Expected: Remediator called after user approval
    # Actual: Not implemented
    with patch('AskUserQuestion', return_value=user_response):
        with patch('run_remediator', mock_remediator):
            task_result = execute_validation_task(task, mode)

    # Assertions
    assert remediator_called == True
    assert task_result.metadata["remediation"]["userApproved"] == True
    assert task_result.metadata["remediation"]["actionsExecuted"] == ["Fixed hooks.yaml syntax"]
```

#### Test 2.4: Track User Decision in Metadata

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is UPDATE
- Validation fails

**When**:
- User is prompted for remediation decision
- User provides response (yes/no)

**Then**:
- Task metadata includes `remediation.userPrompted: true`
- Task metadata includes `remediation.userResponse: "yes"|"no"`
- Task metadata includes `remediation.promptTimestamp`
- Metadata persists via TaskUpdate

```python
def test_update_mode_track_user_decision():
    """
    Test that user decision metadata is tracked in UPDATE mode.

    Expected Result: FAIL - Decision tracking not implemented
    """
    task = create_validation_task(module_id="settings")
    mode = "UPDATE"

    validation_result = {"status": "FAIL", "issues": ["Missing env var"]}
    user_response = "yes"

    # Expected: User decision tracked in metadata
    # Actual: Not implemented
    with patch('AskUserQuestion', return_value=user_response):
        task_result = execute_validation_task(task, mode)

    # Verify metadata
    remediation_metadata = task_result.metadata["remediation"]
    assert remediation_metadata["userPrompted"] == True
    assert remediation_metadata["userResponse"] == "yes"
    assert "promptTimestamp" in remediation_metadata
```

### Test Category 3: VERIFY Mode - Report Only

#### Test 3.1: Never Call Remediator in VERIFY Mode

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is VERIFY
- Validation fails with remediable issues
- Remediator is available

**When**:
- executeValidationTask processes the failure

**Then**:
- Remediator is NEVER called
- No AskUserQuestion prompts
- Task metadata includes `remediation.skipped: true`
- Task metadata includes `remediation.skipReason: "VERIFY mode"`
- Task status remains FAIL

```python
def test_verify_mode_never_remediate():
    """
    Test that VERIFY mode never attempts remediation.

    Expected Result: FAIL - VERIFY mode remediation skip not implemented
    """
    task = create_validation_task(module_id="domain")
    mode = "VERIFY"

    validation_result = {
        "status": "FAIL",
        "issues": ["Domain structure violation"]
    }

    remediator_called = False
    ask_user_called = False

    def mock_remediator(*args):
        nonlocal remediator_called
        remediator_called = True
        return {"status": "SKIPPED"}

    def mock_ask_user(*args):
        nonlocal ask_user_called
        ask_user_called = True
        return "yes"

    # Expected: Neither remediator nor AskUserQuestion called
    # Actual: VERIFY mode logic not implemented
    with patch('run_remediator', mock_remediator):
        with patch('AskUserQuestion', mock_ask_user):
            task_result = execute_validation_task(task, mode)

    # Assertions
    assert remediator_called == False, "Remediator should never be called in VERIFY mode"
    assert ask_user_called == False, "No user prompts in VERIFY mode"
    assert task_result.metadata["remediation"]["skipped"] == True
    assert task_result.metadata["remediation"]["skipReason"] == "VERIFY mode"
    assert task_result.status == "FAIL"
```

#### Test 3.2: Only Report Validation Results

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is VERIFY
- Validation fails

**When**:
- executeValidationTask completes

**Then**:
- Task metadata includes full validation results
- Task metadata includes `actionsRequired` (suggested fixes)
- No `actionsExecuted` field
- Task provides report for user review

```python
def test_verify_mode_report_only():
    """
    Test that VERIFY mode only reports results without taking action.

    Expected Result: FAIL - Report-only behavior not implemented
    """
    task = create_validation_task(module_id="runtime")
    mode = "VERIFY"

    validation_result = {
        "status": "FAIL",
        "passRate": 60,
        "issues": [
            "Runtime check A failed",
            "Runtime check B failed"
        ],
        "actionsRequired": [
            "Fix configuration X",
            "Update environment variable Y"
        ]
    }

    # Expected: Report only, no actions
    # Actual: Not implemented
    task_result = execute_validation_task(task, mode)

    # Assertions
    assert task_result.metadata["validation"]["passRate"] == 60
    assert len(task_result.metadata["validation"]["issues"]) == 2
    assert task_result.metadata["remediation"]["actionsRequired"] == [
        "Fix configuration X",
        "Update environment variable Y"
    ]
    assert "actionsExecuted" not in task_result.metadata["remediation"]
```

#### Test 3.3: No Task Updates for Remediation Execution

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Mode is VERIFY
- Validation completes (pass or fail)

**When**:
- Task is finalized

**Then**:
- TaskUpdate includes validation results only
- No remediation status updates
- Task metadata structure excludes remediation execution fields
- User receives report summary

```python
def test_verify_mode_no_remediation_updates():
    """
    Test that VERIFY mode doesn't update Task with remediation execution data.

    Expected Result: FAIL - Task update filtering not implemented
    """
    task = create_validation_task(module_id="folders")
    mode = "VERIFY"

    validation_result = {"status": "PASS", "passRate": 100}

    # Track TaskUpdate calls
    task_updates = []
    def mock_task_update(task_id, updates):
        task_updates.append(updates)

    # Expected: No remediation fields in updates
    # Actual: Not implemented
    with patch('TaskUpdate', mock_task_update):
        task_result = execute_validation_task(task, mode)

    # Assertions
    final_update = task_updates[-1]
    assert "validation" in final_update["metadata"]

    # Verify remediation execution fields are absent
    if "remediation" in final_update["metadata"]:
        remediation = final_update["metadata"]["remediation"]
        assert "actionsExecuted" not in remediation
        assert "autoExecuted" not in remediation
```

### Test Category 4: Mode Transition & Consistency

#### Test 4.1: Mode Affects All Pipeline Modules

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Multiple validation tasks in pipeline
- Mode is set to NEW_SETUP, UPDATE, or VERIFY

**When**:
- runValidationPipeline executes all tasks

**Then**:
- All tasks respect the global mode setting
- No individual task overrides mode
- Consistent behavior across entire pipeline
- Pipeline summary reflects mode-specific statistics

```python
def test_mode_consistency_across_pipeline():
    """
    Test that mode setting is respected by all modules in pipeline.

    Expected Result: FAIL - Mode propagation not implemented
    """
    context = ValidationContext(project_root="/test/project")
    mode = "UPDATE"

    # Track mode used by each validator
    modes_used = []

    def mock_execute_validation_task(task, mode):
        modes_used.append(mode)
        return {"status": "PASS"}

    # Expected: All tasks use same mode
    # Actual: Mode propagation not implemented
    with patch('execute_validation_task', mock_execute_validation_task):
        pipeline_result = run_validation_pipeline(context, mode)

    # Assertions
    assert all(m == "UPDATE" for m in modes_used)
    assert len(modes_used) == 8  # All 8 modules
```

#### Test 4.2: Mode Transitions Without State Leakage

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Pipeline with 8 modules
- Mode transitions between executions (NEW_SETUP → VERIFY)

**When**:
- Different modes are used in separate pipeline runs

**Then**:
- First run (NEW_SETUP): All modules auto-remediate
- Second run (VERIFY): No modules attempt remediation
- Mode change affects all modules uniformly
- No state leakage between runs

```python
def test_mode_transition_no_state_leakage():
    """
    Test that mode changes between runs don't cause state leakage.

    Expected Result: FAIL - Mode isolation not implemented
    """
    context = ValidationContext(project_root="/test/project")

    # First run: NEW_SETUP mode
    result_1 = run_validation_pipeline(context, "NEW_SETUP")
    remediation_count_1 = result_1["actions"]["executed"]

    # Second run: VERIFY mode (same context)
    result_2 = run_validation_pipeline(context, "VERIFY")
    remediation_count_2 = result_2["actions"]["executed"]

    # Assertions
    assert remediation_count_1 > 0, "NEW_SETUP should remediate"
    assert remediation_count_2 == 0, "VERIFY should not remediate"
```

### Expected Test Results (RED Phase)

When these test scenarios are implemented and run, they should ALL FAIL with errors indicating that mode-specific remediation logic does not exist:

```
FAIL: test_new_setup_auto_remediation
  KeyError: 'remediation' not in task.metadata

FAIL: test_new_setup_remediation_metadata_tracking
  KeyError: 'remediation' not in task.metadata

FAIL: test_new_setup_revalidation_after_remediation
  AssertionError: Validator only called once, expected 2 calls

FAIL: test_update_mode_interactive_remediation
  AssertionError: AskUserQuestion was not called

FAIL: test_update_mode_skip_remediation_on_decline
  AssertionError: Remediator was called when it should be skipped

FAIL: test_update_mode_proceed_on_user_approval
  KeyError: 'userApproved' not in remediation metadata

FAIL: test_update_mode_track_user_decision
  KeyError: 'userPrompted' not in remediation metadata

FAIL: test_verify_mode_never_remediate
  AssertionError: Remediator was called in VERIFY mode

FAIL: test_verify_mode_report_only
  KeyError: 'actionsRequired' not in remediation metadata

FAIL: test_verify_mode_no_remediation_updates
  AssertionError: Remediation execution fields present in VERIFY mode

FAIL: test_mode_consistency_across_pipeline
  AssertionError: Mode not propagated to all tasks

FAIL: test_mode_transition_no_state_leakage
  AssertionError: Remediation occurred in VERIFY mode

12 test scenarios failed, 0 passed
```

### TDD Status for Mode-Specific Remediation (PHASE 3)

- [ ] RED: Test scenarios documented (12 scenarios defined)
- [ ] GREEN: Implementation with mode-specific remediation logic
- [ ] REFACTOR: Code quality improvements

## Test Scenarios: Task-based Progress Display

**Purpose**: Test the Task-based progress display functionality that shows real-time pipeline execution status using TaskList.

**TDD Phase**: RED (Test Documentation Only - Implementation Not Started)

### Test Category 1: Progress Table Display

#### Test 1.1: Display All 8 Modules with Correct Status

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Validation pipeline with 8 modules defined in VALIDATION_PIPELINE
- TaskList contains tasks with `wm-setup: true` metadata
- Tasks have varying statuses: completed, in_progress, pending

**When**:
- `printPipelineProgress(current_step=3, total_steps=8)` is called

**Then**:
- Progress table displays exactly 8 rows (one per module)
- Each row shows: Module ID, Name, Status Icon, Details
- Module order matches VALIDATION_PIPELINE order
- Table header includes: "Module", "Status", "Details"

```python
def test_progress_table_displays_all_modules():
    """
    Test that progress table shows all 8 modules in correct order.

    Expected Result: FAIL - printPipelineProgress function not implemented yet
    """
    # Setup: Create tasks for all modules
    context = {"claude_dir": ".claude"}
    mode = "NEW_SETUP"

    # Create tasks (7 modules, Module 7 skipped in NEW_SETUP)
    tasks = createValidationTasks(context, mode)

    # Expected: printPipelineProgress renders table with 8 rows
    # Actual: Function doesn't exist
    output = printPipelineProgress(current_step=3, total_steps=7)

    # Verify table structure
    assert "Module" in output
    assert "Status" in output
    assert "Details" in output

    # Verify all modules present (7 active + 1 skipped)
    for module in VALIDATION_PIPELINE:
        assert module["name"] in output
```

#### Test 1.2: Status Icons Display Correctly

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Tasks with various statuses in TaskList:
  - completed tasks → ✅ PASS
  - failed tasks → ❌ FAIL
  - tasks with warnings → ⚠️ WARN
  - in_progress tasks → ⏳ RUNNING
  - pending tasks → ⏸️ WAIT

**When**:
- `printPipelineProgress()` is called

**Then**:
- Each module displays correct status icon based on task status
- Status derived from Task.status field
- Icons match specification:
  - ✅ for status="completed" and no failures
  - ❌ for status="completed" with failures
  - ⚠️ for status="completed" with warnings
  - ⏳ for status="in_progress"
  - ⏸️ for status="pending"

```python
def test_status_icons_display_correctly():
    """
    Test that correct status icons are shown based on task status.

    Expected Result: FAIL - Status icon mapping not implemented
    """
    # Setup: Create tasks with different statuses
    context = {"claude_dir": ".claude"}

    # Mock TaskList with different statuses
    mock_tasks = [
        Mock(status="completed", metadata={"wm-setup": True, "failures": 0}),  # ✅
        Mock(status="completed", metadata={"wm-setup": True, "failures": 2}),  # ❌
        Mock(status="completed", metadata={"wm-setup": True, "warnings": 3}),  # ⚠️
        Mock(status="in_progress", metadata={"wm-setup": True}),               # ⏳
        Mock(status="pending", metadata={"wm-setup": True}),                   # ⏸️
    ]

    # Expected: Icons rendered based on status
    # Actual: Icon mapping logic doesn't exist
    output = printPipelineProgress(current_step=2, total_steps=5)

    # Verify status icons
    assert "✅" in output, "PASS icon missing"
    assert "❌" in output, "FAIL icon missing"
    assert "⚠️" in output, "WARN icon missing"
    assert "⏳" in output, "RUNNING icon missing"
    assert "⏸️" in output, "WAIT icon missing"
```

#### Test 1.3: Module Order Matches VALIDATION_PIPELINE Order

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- VALIDATION_PIPELINE with 8 modules in specific order
- Tasks created from pipeline definition

**When**:
- `printPipelineProgress()` is called

**Then**:
- Table rows appear in same order as VALIDATION_PIPELINE
- Module IDs match: "config", "local", "plugin", "skill", "docker", "ui", "runtime", "integration"

```python
def test_module_order_matches_pipeline():
    """
    Test that progress table preserves VALIDATION_PIPELINE order.

    Expected Result: FAIL - Order preservation logic not implemented
    """
    context = {"claude_dir": ".claude"}
    mode = "VERIFY"

    # Create tasks
    tasks = createValidationTasks(context, mode)

    # Expected: Table rows in VALIDATION_PIPELINE order
    # Actual: Order logic doesn't exist
    output = printPipelineProgress(current_step=4, total_steps=8)

    # Extract module IDs from output
    lines = output.split("\n")
    module_rows = [line for line in lines if "|" in line and "Module" not in line]

    # Verify order matches VALIDATION_PIPELINE
    expected_order = [m["id"] for m in VALIDATION_PIPELINE]
    for i, module_id in enumerate(expected_order):
        assert module_id in module_rows[i], f"Module {module_id} not in position {i}"
```

### Test Category 2: Running Module Display

#### Test 2.1: Currently Running Module Shows Indicator

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- One task with status="in_progress" in TaskList
- Other tasks have status="completed" or "pending"

**When**:
- `printPipelineProgress()` is called

**Then**:
- Running module shows ⏳ spinner/indicator
- Only the in_progress task shows RUNNING status
- Other tasks show their respective statuses

```python
def test_running_module_shows_indicator():
    """
    Test that in-progress module displays running indicator.

    Expected Result: FAIL - Running indicator logic not implemented
    """
    context = {"claude_dir": ".claude"}

    # Mock TaskList with one in_progress task
    mock_tasks = [
        Mock(status="completed", metadata={"wm-setup": True, "moduleId": "config"}),
        Mock(status="completed", metadata={"wm-setup": True, "moduleId": "local"}),
        Mock(status="in_progress", metadata={"wm-setup": True, "moduleId": "plugin"}),
        Mock(status="pending", metadata={"wm-setup": True, "moduleId": "skill"}),
    ]

    # Expected: Plugin module shows ⏳ RUNNING
    # Actual: Running detection logic doesn't exist
    output = printPipelineProgress(current_step=3, total_steps=4)

    # Find the plugin row
    plugin_row = [line for line in output.split("\n") if "plugin" in line.lower()][0]

    # Verify running indicator
    assert "⏳" in plugin_row, "Running indicator not shown"
    assert "RUNNING" in plugin_row or "Running" in plugin_row
```

#### Test 2.2: Only One Module Shows RUNNING at a Time

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Multiple tasks in TaskList
- Only one task has status="in_progress"

**When**:
- `printPipelineProgress()` is called

**Then**:
- Exactly one module shows RUNNING status
- No multiple modules show ⏳ simultaneously

```python
def test_only_one_module_running():
    """
    Test that only one module can be in RUNNING state.

    Expected Result: FAIL - Multiple running detection not implemented
    """
    context = {"claude_dir": ".claude"}

    # Mock TaskList
    mock_tasks = [
        Mock(status="completed", metadata={"wm-setup": True}),
        Mock(status="in_progress", metadata={"wm-setup": True}),
        Mock(status="pending", metadata={"wm-setup": True}),
        Mock(status="pending", metadata={"wm-setup": True}),
    ]

    # Expected: Exactly one ⏳ in output
    # Actual: Validation logic doesn't exist
    output = printPipelineProgress(current_step=2, total_steps=4)

    # Count running indicators
    running_count = output.count("⏳")
    assert running_count == 1, f"Expected 1 running module, found {running_count}"
```

#### Test 2.3: RUNNING Status Derived from Task Status

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Task with status="in_progress" in TaskList
- Task metadata includes `{"wm-setup": true, "moduleId": "plugin"}`

**When**:
- `printPipelineProgress()` retrieves task status

**Then**:
- RUNNING status is derived from `Task.status == "in_progress"`
- Not based on hardcoded values or external state

```python
def test_running_derived_from_task_status():
    """
    Test that RUNNING status comes from Task.status field.

    Expected Result: FAIL - Task status integration not implemented
    """
    context = {"claude_dir": ".claude"}

    # Create real task with in_progress status
    task = TaskCreate(
        subject="Validate Plugin System",
        status="in_progress",
        metadata={"wm-setup": True, "moduleId": "plugin"}
    )

    # Expected: printPipelineProgress reads Task.status
    # Actual: Task integration doesn't exist
    output = printPipelineProgress(current_step=3, total_steps=8)

    # Verify RUNNING derived from task
    plugin_row = [line for line in output.split("\n") if "plugin" in line.lower()][0]
    assert "⏳" in plugin_row

    # Change task status to completed
    task.status = "completed"
    output_after = printPipelineProgress(current_step=4, total_steps=8)
    plugin_row_after = [line for line in output_after.split("\n") if "plugin" in line.lower()][0]

    # Verify status changed in display
    assert "✅" in plugin_row_after
    assert "⏳" not in plugin_row_after
```

### Test Category 3: Completed Module Display

#### Test 3.1: Completed Modules Show Pass Rate

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Task with status="completed"
- Task metadata includes validation results: `{"passed": 17, "total": 20, "failed": 3}`

**When**:
- `printPipelineProgress()` is called

**Then**:
- Completed module shows pass rate in Details column
- Format: "85% (17/20)" or similar
- Percentage calculated as: (passed / total) * 100

```python
def test_completed_modules_show_pass_rate():
    """
    Test that completed modules display pass rate statistics.

    Expected Result: FAIL - Pass rate calculation not implemented
    """
    context = {"claude_dir": ".claude"}

    # Mock completed task with results
    task = Mock(
        status="completed",
        metadata={
            "wm-setup": True,
            "moduleId": "config",
            "passed": 17,
            "total": 20,
            "failed": 3
        }
    )

    # Expected: Pass rate shown as "85% (17/20)"
    # Actual: Pass rate logic doesn't exist
    output = printPipelineProgress(current_step=1, total_steps=8)

    # Find config row
    config_row = [line for line in output.split("\n") if "config" in line.lower()][0]

    # Verify pass rate format
    assert "85%" in config_row or "17/20" in config_row
```

#### Test 3.2: Pass Rate Format Validation

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Multiple completed tasks with different pass rates
- Edge cases: 100% pass, 0% pass, partial pass

**When**:
- `printPipelineProgress()` formats pass rates

**Then**:
- Format is consistent: "XX% (passed/total)"
- Percentages rounded to nearest integer
- Both percentage and fraction shown

```python
def test_pass_rate_format():
    """
    Test pass rate formatting for various scenarios.

    Expected Result: FAIL - Format validation not implemented
    """
    test_cases = [
        {"passed": 20, "total": 20, "expected": "100% (20/20)"},
        {"passed": 0, "total": 20, "expected": "0% (0/20)"},
        {"passed": 15, "total": 20, "expected": "75% (15/20)"},
        {"passed": 17, "total": 20, "expected": "85% (17/20)"},
    ]

    for case in test_cases:
        task = Mock(
            status="completed",
            metadata={
                "wm-setup": True,
                "moduleId": "test",
                "passed": case["passed"],
                "total": case["total"]
            }
        )

        # Expected: Formatted pass rate
        # Actual: Formatter doesn't exist
        output = printPipelineProgress(current_step=1, total_steps=1)

        assert case["expected"] in output, f"Expected '{case['expected']}' in output"
```

#### Test 3.3: Status Derived from Task Completed Status

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Task with status="completed"
- Task tracked in TaskList

**When**:
- `printPipelineProgress()` checks task completion

**Then**:
- Completion status derived from `Task.status == "completed"`
- Results metadata only read for completed tasks
- Pending/in_progress tasks do not show pass rates

```python
def test_status_derived_from_task_completed():
    """
    Test that completed status comes from Task.status field.

    Expected Result: FAIL - Task status check not implemented
    """
    context = {"claude_dir": ".claude"}

    # Mock tasks with different statuses
    mock_tasks = [
        Mock(status="completed", metadata={"wm-setup": True, "passed": 10, "total": 10}),
        Mock(status="in_progress", metadata={"wm-setup": True}),
        Mock(status="pending", metadata={"wm-setup": True}),
    ]

    # Expected: Only completed task shows pass rate
    # Actual: Status filtering doesn't exist
    output = printPipelineProgress(current_step=1, total_steps=3)

    lines = output.split("\n")

    # First task should show pass rate
    assert "100%" in lines[1] or "10/10" in lines[1]

    # Other tasks should NOT show pass rates
    assert "100%" not in lines[2]
    assert "100%" not in lines[3]
```

### Test Category 4: printPipelineProgress Function

#### Test 4.1: Function Prints Formatted Table

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- Function signature: `printPipelineProgress(current_step: int, total_steps: int)`
- TaskList contains validation tasks

**When**:
- Function is called with current_step=3, total_steps=8

**Then**:
- Returns formatted table string
- Includes header row with column names
- Includes separator row (---|---|---)
- Includes data rows for each module

```python
def test_print_pipeline_progress_format():
    """
    Test that printPipelineProgress returns formatted table.

    Expected Result: FAIL - Function doesn't exist
    """
    # Expected: Function prints formatted table
    # Actual: Function not defined
    output = printPipelineProgress(current_step=3, total_steps=8)

    # Verify table structure
    lines = output.split("\n")

    # Header row
    assert "Module" in lines[0]
    assert "Status" in lines[0]
    assert "Details" in lines[0]

    # Separator row
    assert "---" in lines[1]

    # Data rows (8 modules)
    assert len([line for line in lines if "|" in line]) >= 9  # header + separator + 8 rows
```

#### Test 4.2: Uses TaskList to Get Current Status

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- TaskList.list() returns all tasks
- Tasks contain status and metadata fields

**When**:
- `printPipelineProgress()` is called

**Then**:
- Function calls TaskList.list() to get tasks
- Filters tasks by `metadata.wm-setup == true`
- Uses task status to determine display

```python
def test_uses_tasklist_for_status():
    """
    Test that printPipelineProgress integrates with TaskList.

    Expected Result: FAIL - TaskList integration not implemented
    """
    # Mock TaskList.list()
    with patch('TaskList.list') as mock_list:
        mock_list.return_value = [
            Mock(status="completed", metadata={"wm-setup": True, "moduleId": "config"}),
            Mock(status="in_progress", metadata={"wm-setup": True, "moduleId": "plugin"}),
        ]

        # Expected: Function calls TaskList.list()
        # Actual: Integration doesn't exist
        output = printPipelineProgress(current_step=2, total_steps=8)

        # Verify TaskList.list was called
        mock_list.assert_called_once()

        # Verify output reflects task statuses
        assert "✅" in output  # completed task
        assert "⏳" in output  # in_progress task
```

#### Test 4.3: Filters by wm-setup Metadata Marker

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- TaskList contains both wm-setup tasks and non-wm-setup tasks
- wm-setup tasks have `metadata.wm-setup = true`

**When**:
- `printPipelineProgress()` retrieves tasks

**Then**:
- Only tasks with `metadata.wm-setup == true` are included
- Non-wm-setup tasks are ignored
- Prevents contamination from unrelated tasks

```python
def test_filters_by_wm-setup_metadata():
    """
    Test that only wm-setup tasks are displayed.

    Expected Result: FAIL - Metadata filtering not implemented
    """
    # Mock TaskList with mixed tasks
    with patch('TaskList.list') as mock_list:
        mock_list.return_value = [
            Mock(status="completed", metadata={"wm-setup": True, "moduleId": "config"}),
            Mock(status="completed", metadata={"wm-setup": False, "moduleId": "other"}),
            Mock(status="completed", metadata={"moduleId": "another"}),  # no wm-setup key
            Mock(status="in_progress", metadata={"wm-setup": True, "moduleId": "plugin"}),
        ]

        # Expected: Only 2 wm-setup tasks shown
        # Actual: Filtering logic doesn't exist
        output = printPipelineProgress(current_step=2, total_steps=2)

        # Verify only wm-setup tasks included
        assert "config" in output.lower()
        assert "plugin" in output.lower()
        assert "other" not in output.lower()
        assert "another" not in output.lower()
```

### Expected Test Results (RED Phase)

When these test scenarios are implemented and run, they should ALL FAIL with errors indicating that Task-based progress display functionality does not exist:

```
FAIL: test_progress_table_displays_all_modules
  NameError: name 'printPipelineProgress' is not defined

FAIL: test_status_icons_display_correctly
  NameError: name 'printPipelineProgress' is not defined

FAIL: test_module_order_matches_pipeline
  NameError: name 'printPipelineProgress' is not defined

FAIL: test_running_module_shows_indicator
  NameError: name 'printPipelineProgress' is not defined

FAIL: test_only_one_module_running
  NameError: name 'printPipelineProgress' is not defined

FAIL: test_running_derived_from_task_status
  NameError: Task integration not implemented

FAIL: test_completed_modules_show_pass_rate
  NameError: Pass rate calculation not implemented

FAIL: test_pass_rate_format
  NameError: Format validation not implemented

FAIL: test_status_derived_from_task_completed
  NameError: Status filtering not implemented

FAIL: test_print_pipeline_progress_format
  NameError: name 'printPipelineProgress' is not defined

FAIL: test_uses_tasklist_for_status
  NameError: TaskList integration not implemented

FAIL: test_filters_by_wm-setup_metadata
  NameError: Metadata filtering not implemented

12 test scenarios failed, 0 passed
```

### TDD Status for Task-based Progress Display (PHASE 4)

- [ ] RED: Test scenarios documented (12 scenarios defined)
- [ ] GREEN: Implementation of printPipelineProgress with TaskList integration
- [ ] REFACTOR: Code quality improvements

## Test Scenarios: Pipeline Summary from TaskList

**Purpose**: Test the `generatePipelineSummary` function that collects validation task results from TaskList and generates a comprehensive pipeline summary.

**TDD Phase**: RED (Test Documentation Only - Implementation Not Started)

**Context**: PHASE 3 is complete. Now we're testing the summary generation using TaskList instead of receiving results as a parameter.

### Test Category 1: Summary Count Tests

#### Test 1.1: Passed Count Matches Completed Tasks with PASS Result

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks created with `wm-setup: true` metadata marker
- Tasks with IDs: folders, skills, agents, hooks-config, hooks-scripts, settings, runtime, domains
- 5 tasks have status="completed" and result="PASS"
- 2 tasks have status="completed" and result="WARN"
- 1 task has status="completed" and result="FAIL"

**When**:
- `generatePipelineSummary()` is called (no parameters - uses TaskList internally)

**Then**:
- Summary.modules.passed == 5
- Count matches exactly the number of tasks with status="completed" AND result="PASS"

```python
def test_passed_count_from_tasklist():
    """
    Test that passed count correctly aggregates from TaskList.

    Expected Result: FAIL - generatePipelineSummary doesn't use TaskList yet
    """
    # Setup: Create 5 tasks with PASS result
    for module_id in ["folders", "skills", "agents", "hooks-config", "settings"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Setup: Create 2 tasks with WARN result
    for module_id in ["hooks-scripts", "domains"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "WARN"
            },
            status="completed"
        )

    # Setup: Create 1 task with FAIL result
    TaskCreate(
        subject="Validate runtime",
        metadata={
            "wm-setup": True,
            "moduleId": "runtime",
            "result": "FAIL"
        },
        status="completed"
    )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["modules"]["passed"] == 5
    assert summary["modules"]["warned"] == 2
    assert summary["modules"]["failed"] == 1
```

#### Test 1.2: Warned Count Matches Completed Tasks with WARN Result

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- 3 tasks have status="completed" and result="WARN"
- 5 tasks have status="completed" and result="PASS"

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.modules.warned == 3
- Count matches exactly the number of tasks with status="completed" AND result="WARN"

```python
def test_warned_count_from_tasklist():
    """
    Test that warned count correctly aggregates from TaskList.

    Expected Result: FAIL - generatePipelineSummary doesn't filter by result="WARN"
    """
    # Setup: Create tasks with various results
    warned_modules = ["skills", "agents", "hooks-config"]
    passed_modules = ["folders", "hooks-scripts", "settings", "runtime", "domains"]

    for module_id in warned_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "WARN"
            },
            status="completed"
        )

    for module_id in passed_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["modules"]["warned"] == 3
    assert summary["modules"]["passed"] == 5
    assert summary["modules"]["total"] == 8
```

#### Test 1.3: Failed Count Matches Completed Tasks with FAIL Result

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- 2 tasks have status="completed" and result="FAIL"
- 6 tasks have status="completed" and result="PASS"

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.modules.failed == 2
- Count matches exactly the number of tasks with status="completed" AND result="FAIL"

```python
def test_failed_count_from_tasklist():
    """
    Test that failed count correctly aggregates from TaskList.

    Expected Result: FAIL - generatePipelineSummary doesn't filter by result="FAIL"
    """
    # Setup: Create tasks with various results
    failed_modules = ["folders", "runtime"]
    passed_modules = ["skills", "agents", "hooks-config", "hooks-scripts", "settings", "domains"]

    for module_id in failed_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "FAIL",
                "blocking": True
            },
            status="completed"
        )

    for module_id in passed_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["modules"]["failed"] == 2
    assert summary["modules"]["passed"] == 6
```

#### Test 1.4: Skipped Count Matches Pending Tasks that are Blocked

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- 2 tasks have status="pending" (blocked by failed blocking module)
- 6 tasks have status="completed" with various results

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.modules.skipped == 2
- Count matches the number of tasks with status="pending" that were blocked
- Skipped tasks should have metadata indicating why they were skipped

```python
def test_skipped_count_from_tasklist():
    """
    Test that skipped count correctly identifies blocked tasks.

    Expected Result: FAIL - generatePipelineSummary doesn't track skipped tasks
    """
    # Setup: Blocking module fails
    TaskCreate(
        subject="Validate folders",
        metadata={
            "wm-setup": True,
            "moduleId": "folders",
            "result": "FAIL",
            "blocking": True
        },
        status="completed"
    )

    # Setup: Subsequent modules are skipped
    for module_id in ["skills", "agents"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "skipped": True,
                "skipReason": "Blocked by failed folders module"
            },
            status="pending"
        )

    # Setup: Other modules complete successfully
    for module_id in ["hooks-config", "hooks-scripts", "settings", "runtime", "domains"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["modules"]["skipped"] == 2
    assert summary["modules"]["failed"] == 1
    assert summary["modules"]["passed"] == 5
```

### Test Category 2: Overall Status Tests

#### Test 2.1: Overall Status is PASS When All Modules Pass

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- All tasks have status="completed" and result="PASS"
- No warnings, no failures, no skips

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.overall == "PASS"
- Summary.blocked == False

```python
def test_overall_pass_when_all_pass():
    """
    Test that overall status is PASS when all modules pass.

    Expected Result: FAIL - generatePipelineSummary doesn't calculate overall from TaskList
    """
    # Setup: All modules pass
    for module_id in ["folders", "skills", "agents", "hooks-config", "hooks-scripts", "settings", "runtime", "domains"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["overall"] == "PASS"
    assert summary["blocked"] == False
    assert summary["modules"]["passed"] == 8
    assert summary["modules"]["warned"] == 0
    assert summary["modules"]["failed"] == 0
```

#### Test 2.2: Overall Status is WARN When Any Module Has Warnings But No Failures

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- 2 tasks have result="WARN"
- 6 tasks have result="PASS"
- No tasks have result="FAIL"

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.overall == "WARN"
- Summary.blocked == False

```python
def test_overall_warn_when_warnings_exist():
    """
    Test that overall status is WARN when warnings exist but no failures.

    Expected Result: FAIL - generatePipelineSummary doesn't prioritize WARN correctly
    """
    # Setup: Some modules warn
    warned_modules = ["skills", "hooks-scripts"]
    passed_modules = ["folders", "agents", "hooks-config", "settings", "runtime", "domains"]

    for module_id in warned_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "WARN"
            },
            status="completed"
        )

    for module_id in passed_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["overall"] == "WARN"
    assert summary["blocked"] == False
    assert summary["modules"]["warned"] == 2
    assert summary["modules"]["failed"] == 0
```

#### Test 2.3: Overall Status is FAIL When Any Blocking Module Fails

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- 1 task with moduleId="folders" has result="FAIL" and blocking=True
- Remaining tasks may have various statuses (PASS, WARN, or skipped)

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.overall == "FAIL"
- Summary.blocked == True
- Summary reflects that a blocking module failed

```python
def test_overall_fail_when_blocking_module_fails():
    """
    Test that overall status is FAIL when a blocking module fails.

    Expected Result: FAIL - generatePipelineSummary doesn't check blocking flag
    """
    # Setup: Blocking module fails
    TaskCreate(
        subject="Validate folders",
        metadata={
            "wm-setup": True,
            "moduleId": "folders",
            "result": "FAIL",
            "blocking": True
        },
        status="completed"
    )

    # Setup: Other modules may warn or pass
    TaskCreate(
        subject="Validate skills",
        metadata={
            "wm-setup": True,
            "moduleId": "skills",
            "result": "WARN"
        },
        status="completed"
    )

    for module_id in ["agents", "hooks-config", "hooks-scripts", "settings", "runtime", "domains"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["overall"] == "FAIL"
    assert summary["blocked"] == True
    assert summary["modules"]["failed"] == 1
```

#### Test 2.4: Overall Status is PARTIAL When Non-Blocking Module Fails

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- 1 task with moduleId="skills" has result="FAIL" and blocking=False
- All other tasks have result="PASS"

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.overall == "PARTIAL"
- Summary.blocked == False
- Summary indicates partial success with non-critical failures

```python
def test_overall_partial_when_nonblocking_module_fails():
    """
    Test that overall status is PARTIAL when a non-blocking module fails.

    Expected Result: FAIL - generatePipelineSummary doesn't support PARTIAL status
    """
    # Setup: Non-blocking module fails
    TaskCreate(
        subject="Validate skills",
        metadata={
            "wm-setup": True,
            "moduleId": "skills",
            "result": "FAIL",
            "blocking": False
        },
        status="completed"
    )

    # Setup: All other modules pass
    for module_id in ["folders", "agents", "hooks-config", "hooks-scripts", "settings", "runtime", "domains"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["overall"] == "PARTIAL"
    assert summary["blocked"] == False
    assert summary["modules"]["failed"] == 1
    assert summary["modules"]["passed"] == 7
```

### Test Category 3: Actions Tally Tests

#### Test 3.1: actionsExecuted Count from Task Metadata

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList (all completed)
- Each task has metadata.remediation.actionsExecuted list
- Total actions executed: 12 (summed across all tasks)

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.actions.executed == 12
- Count aggregates from all task.metadata.remediation.actionsExecuted

```python
def test_actions_executed_aggregation():
    """
    Test that actionsExecuted count aggregates from all task metadata.

    Expected Result: FAIL - generatePipelineSummary doesn't read from task metadata
    """
    # Setup: Tasks with various action counts
    actions_per_module = {
        "folders": 3,
        "skills": 2,
        "agents": 1,
        "hooks-config": 0,
        "hooks-scripts": 4,
        "settings": 2,
        "runtime": 0,
        "domains": 0
    }

    for module_id, action_count in actions_per_module.items():
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS",
                "remediation": {
                    "actionsExecuted": [f"Action_{i}" for i in range(action_count)]
                }
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    expected_total = sum(actions_per_module.values())  # 12
    assert summary["actions"]["executed"] == expected_total
```

#### Test 3.2: actionsRequired Count from Task Metadata

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList (all completed)
- Each task has metadata.remediation.actionsRequired list
- Total actions required: 18 (summed across all tasks)

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.actions.required == 18
- Count aggregates from all task.metadata.remediation.actionsRequired

```python
def test_actions_required_aggregation():
    """
    Test that actionsRequired count aggregates from all task metadata.

    Expected Result: FAIL - generatePipelineSummary doesn't read from task metadata
    """
    # Setup: Tasks with various required action counts
    actions_per_module = {
        "folders": 3,
        "skills": 5,
        "agents": 2,
        "hooks-config": 1,
        "hooks-scripts": 4,
        "settings": 3,
        "runtime": 0,
        "domains": 0
    }

    for module_id, action_count in actions_per_module.items():
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "WARN" if action_count > 0 else "PASS",
                "remediation": {
                    "actionsRequired": [f"RequiredAction_{i}" for i in range(action_count)]
                }
            },
            status="completed"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    expected_total = sum(actions_per_module.values())  # 18
    assert summary["actions"]["required"] == expected_total
```

#### Test 3.3: Actions Tally Aggregates from All Completed Tasks

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList
- 6 tasks completed (with action metadata)
- 2 tasks pending (should not contribute to action tally)

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary.actions counts only include completed tasks
- Pending tasks do not contribute to action tallies

```python
def test_actions_tally_only_completed_tasks():
    """
    Test that actions tally only includes completed tasks.

    Expected Result: FAIL - generatePipelineSummary counts pending tasks
    """
    # Setup: 6 completed tasks with actions
    completed_modules = ["folders", "skills", "agents", "hooks-config", "hooks-scripts", "settings"]
    for i, module_id in enumerate(completed_modules):
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS",
                "remediation": {
                    "actionsExecuted": [f"Action_{i}"],
                    "actionsRequired": [f"RequiredAction_{i}"]
                }
            },
            status="completed"
        )

    # Setup: 2 pending tasks (should not contribute)
    pending_modules = ["runtime", "domains"]
    for module_id in pending_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "remediation": {
                    "actionsExecuted": ["ShouldNotCount"],
                    "actionsRequired": ["ShouldNotCount"]
                }
            },
            status="pending"
        )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["actions"]["executed"] == 6  # Only completed tasks
    assert summary["actions"]["required"] == 6  # Only completed tasks
```

### Test Category 4: generatePipelineSummary Function Tests

#### Test 4.1: generatePipelineSummary Returns Formatted Summary Dict

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks in TaskList (various statuses)
- Tasks have complete metadata (result, remediation, blocking flags)

**When**:
- `summary = generatePipelineSummary()` is called

**Then**:
- Returns dict with keys: overall, blocked, modules, actions, timestamp
- modules dict has keys: total, passed, warned, failed, skipped
- actions dict has keys: executed, required
- timestamp is ISO format

```python
def test_generate_pipeline_summary_structure():
    """
    Test that generatePipelineSummary returns correctly structured dict.

    Expected Result: FAIL - generatePipelineSummary doesn't use TaskList yet
    """
    # Setup: Create mix of task statuses
    TaskCreate(
        subject="Validate folders",
        metadata={"wm-setup": True, "moduleId": "folders", "result": "PASS"},
        status="completed"
    )
    TaskCreate(
        subject="Validate skills",
        metadata={"wm-setup": True, "moduleId": "skills", "result": "WARN"},
        status="completed"
    )
    TaskCreate(
        subject="Validate agents",
        metadata={"wm-setup": True, "moduleId": "agents", "result": "FAIL", "blocking": False},
        status="completed"
    )

    # Execute
    summary = generatePipelineSummary()

    # Assertions: Structure
    assert "overall" in summary
    assert "blocked" in summary
    assert "modules" in summary
    assert "actions" in summary
    assert "timestamp" in summary

    # Assertions: modules keys
    assert set(summary["modules"].keys()) == {"total", "passed", "warned", "failed", "skipped"}

    # Assertions: actions keys
    assert set(summary["actions"].keys()) == {"executed", "required"}

    # Assertions: timestamp format
    from datetime import datetime
    datetime.fromisoformat(summary["timestamp"])  # Should not raise
```

#### Test 4.2: Uses TaskList to Collect All Validation Tasks

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 8 validation tasks exist in TaskList
- Tasks have metadata.wm-setup=True marker
- No parameters passed to generatePipelineSummary()

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Function internally calls TaskList() to retrieve tasks
- Filters tasks by metadata.wm-setup=True
- Processes all matching tasks for summary generation

```python
def test_generate_pipeline_summary_uses_tasklist():
    """
    Test that generatePipelineSummary uses TaskList internally.

    Expected Result: FAIL - generatePipelineSummary still uses results parameter
    """
    # Setup: Create validation tasks with wm-setup marker
    for module_id in ["folders", "skills", "agents", "hooks-config", "hooks-scripts", "settings", "runtime", "domains"]:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,  # Filter marker
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Setup: Create non-wm-setup task (should be ignored)
    TaskCreate(
        subject="Other task",
        metadata={"wm-setup": False, "moduleId": "other"},
        status="completed"
    )

    # Execute (no parameters - must use TaskList internally)
    summary = generatePipelineSummary()

    # Assertions
    assert summary["modules"]["total"] == 8  # Only wm-setup tasks
    assert summary["modules"]["passed"] == 8
```

#### Test 4.3: Filters by wm-setup=true Metadata Marker

- [ ] **Test Status**: Pending (RED phase)

**Given**:
- 10 tasks in TaskList
- 8 tasks have metadata.wm-setup=True (validation tasks)
- 2 tasks have metadata.wm-setup=False or missing (other tasks)

**When**:
- `generatePipelineSummary()` is called

**Then**:
- Summary only includes tasks with wm-setup=True
- Other tasks are ignored
- modules.total reflects only wm-setup tasks

```python
def test_generate_pipeline_summary_filters_wm-setup():
    """
    Test that generatePipelineSummary filters by wm-setup=true marker.

    Expected Result: FAIL - generatePipelineSummary doesn't filter by wm-setup
    """
    # Setup: wm-setup validation tasks
    wm-setup_modules = ["folders", "skills", "agents", "hooks-config", "hooks-scripts", "settings", "runtime", "domains"]
    for module_id in wm-setup_modules:
        TaskCreate(
            subject=f"Validate {module_id}",
            metadata={
                "wm-setup": True,
                "moduleId": module_id,
                "result": "PASS"
            },
            status="completed"
        )

    # Setup: Non-wm-setup tasks (should be ignored)
    TaskCreate(
        subject="Custom validation task",
        metadata={"wm-setup": False, "moduleId": "custom"},
        status="completed"
    )
    TaskCreate(
        subject="Manual task",
        metadata={"moduleId": "manual"},  # wm-setup key missing
        status="completed"
    )

    # Execute
    summary = generatePipelineSummary()

    # Assertions
    assert summary["modules"]["total"] == 8  # Only 8 wm-setup tasks
    assert summary["modules"]["passed"] == 8
```

### Expected Test Results (RED Phase)

When these test scenarios are implemented and run, they should ALL FAIL with errors indicating that the TaskList-based implementation does not exist:

```
FAIL: test_passed_count_from_tasklist
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_warned_count_from_tasklist
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_failed_count_from_tasklist
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_skipped_count_from_tasklist
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_overall_pass_when_all_pass
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_overall_warn_when_warnings_exist
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_overall_fail_when_blocking_module_fails
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_overall_partial_when_nonblocking_module_fails
  AttributeError: 'PARTIAL' status not implemented in generatePipelineSummary

FAIL: test_actions_executed_aggregation
  KeyError: 'remediation' not in task.metadata

FAIL: test_actions_required_aggregation
  KeyError: 'remediation' not in task.metadata

FAIL: test_actions_tally_only_completed_tasks
  AssertionError: Expected 6 actions, got 8 (pending tasks incorrectly counted)

FAIL: test_generate_pipeline_summary_structure
  TypeError: generatePipelineSummary() takes 2 positional arguments but 0 were given

FAIL: test_generate_pipeline_summary_uses_tasklist
  TypeError: generatePipelineSummary() missing required argument 'results'

FAIL: test_generate_pipeline_summary_filters_wm-setup
  AssertionError: Expected 8 total modules, got 10 (filter not applied)

14 test scenarios failed, 0 passed
```

### TDD Status for Pipeline Summary from TaskList (PHASE 4)

- [ ] RED: Test scenarios documented (14 scenarios defined)
- [ ] GREEN: Implementation using TaskList API
- [ ] REFACTOR: Code quality improvements

## References

- Validators: [../validators/](../validators/)
- Remediators: [../remediators/](../remediators/)
- Registries: [../registries/](../registries/)
- Progress Tracking: [progress-tracking.md](./progress-tracking.md)
- Task Tools Guide: [../../wm/rules/components/task-tool-planning-guide.md](../../wm/rules/components/task-tool-planning-guide.md)
