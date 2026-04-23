# Onboarding Directory

**Purpose**: Runtime validation and post-VERIFY checklist system for Claude Code setup

## Overview

This directory contains files for the **7th validation module** (Runtime Checks),
which executes exclusively in VERIFY mode to validate runtime environment,
MCP connectivity, and actual system state.

**Note**: With the addition of the Domain Structure module (Module 8),
the total pipeline now contains 8 modules, but Runtime Checks remains Module 7.

## Files

### 1. runtime-checks.yaml (Registry)

**Type**: YAML Registry
**Purpose**: Defines 6 categories of runtime checks
**Used By**: runtime-validator.md

**Categories**:
- `RC-MCP`: MCP server connectivity (3 checks)
- `RC-ENV`: Environment variable values (2 checks)
- `RC-PERM`: Permission configuration (1 check)
- `RC-PLUG`: Plugin functionality (2 checks)
- `RC-HOOK`: Hook script integration (1 check)
- `RC-AGENT`: Agent/Skill file parsing (2 checks)

**Total Checks**: 11 (3 CRITICAL, 6 WARNING, 2 INFO)

---

### 2. runtime-validator.md (Validator)

**Type**: Validation Module
**Purpose**: 7th validator in the pipeline (VERIFY mode only)
**Order**: 7/8
**Blocking**: False (report-only)

**Key Functions**:
- `validate()` - Main entry point
- `checkMCPConnectivity()` - Verify MCP servers
- `checkEnvironmentValues()` - Compare env values
- `checkPermissionConfig()` - Check permissions
- `checkPluginFunctionality()` - Test plugins
- `checkHookIntegration()` - Verify hooks
- `checkAgentWorkflow()` - Parse agent files
- `aggregateResults()` - Combine results

**Interface**: Conforms to `_validator-interface.md`

---

### 3. post-verify-workflow.md (Process)

**Type**: Process Documentation
**Purpose**: Detailed workflow for Step 4.5 in VERIFY mode

**Contents**:
- Workflow steps diagram
- Category execution order
- Output format examples
- Integration with validation pipeline
- Error handling strategies
- Timeout behavior

**References**: verify.md, validation-orchestrator.md

---

### 4. post-verify-checklist.md (User Guide)

**Type**: User-Facing Documentation
**Purpose**: Manual testing guide for runtime verification

**Contents**:
- 6 category testing procedures
- Copy-paste shell commands
- Expected results for each check
- Troubleshooting guides
- Common issues and solutions

**Target Audience**: Users running `/wm-setup` VERIFY mode

---

### 5. README.md (this file)

**Type**: Directory Documentation
**Purpose**: Overview of onboarding directory contents

---

## Integration Points

### With Validation Pipeline

```python
# In validation-orchestrator.md
VALIDATION_PIPELINE[6] = {
    "order": 7,
    "moduleId": "runtime",
    "moduleName": "Runtime Checks",
    "validator": "onboarding/runtime-validator.md",
    "remediator": None,
    "registry": "onboarding/runtime-checks.yaml",
    "blocking": False,
    "verifyModeOnly": True  # <-- Key flag
}
```

### With VERIFY Mode

```python
# In verify.md - Step 4.5
if mode == "VERIFY":
    # Execute static validators (1-6)
    static_results = runValidators(1, 6)

    # Execute runtime validator (7)
    runtime_result = runValidator(module=7)

    # Generate user checklist
    generateChecklist(runtime_result)
```

### With Registry Schema

```yaml
# Extends _registry-schema.md with new type
type: "runtime-checks"

categories:
  - id: "RC-XXX"
    checks:
      - testType: "list_tools|value_compare|..."
```

## Workflow Summary

```
User runs: /wm-setup (VERIFY mode detected)
    ↓
Modules 1-6: Static validation (folders, skills, agents, hooks, settings)
    ↓
Module 7: Runtime validation (THIS DIRECTORY)
    ├─ Load runtime-checks.yaml
    ├─ Execute 6 category checks
    ├─ Aggregate results
    └─ Generate post-verify-checklist.md content
    ↓
Module 8: Domain Structure validation
    ├─ Load domains.yaml
    ├─ Verify domain directories and AGENTS.md files
    └─ Check guide file references
    ↓
Report: Show 8-module summary + checklist guide
```

## VERIFY Mode Only

**Important**: This module only runs in VERIFY mode, not in NEW_SETUP or UPDATE.

```python
if step.get("verifyModeOnly") and mode != "VERIFY":
    skip_module()  # Module 7 skipped in NEW_SETUP/UPDATE
```

## File Relationships

```
runtime-checks.yaml
    ↓ (loaded by)
runtime-validator.md
    ↓ (called by)
validation-orchestrator.md (Module 7)
    ↓ (referenced in)
verify.md (Step 4.5)
    ↓ (workflow detailed in)
post-verify-workflow.md
    ↓ (generates)
post-verify-checklist.md (user guide)
```

## Usage Examples

### 1. Running VERIFY Mode

```bash
# User action
/wm-setup

# Claude detects VERIFY mode
# Executes all 8 modules
# Shows post-verify checklist
```

### 2. Reviewing Runtime Results

```
[7/8] Runtime Checks: ⚠️ WARN (73%)
    - RC-MCP: ✅ PASS
    - RC-ENV: ⚠️ WARN (1 mismatch)
    - RC-PERM: ✅ PASS
    - RC-PLUG: ❌ FAIL (1 plugin not responding)
    - RC-HOOK: ⚠️ WARN (1 hook not configured)
    - RC-AGENT: ✅ PASS

See: post-verify-checklist.md for manual testing
```

### 3. Following Checklist

User opens `post-verify-checklist.md` and:
1. Tests failed/warned items manually
2. Applies fixes
3. Re-runs `/wm-setup` to verify

## Maintenance

### Adding New Runtime Checks

1. Edit `runtime-checks.yaml`:
   ```yaml
   - id: "RTC-XXX-NNN"
     name: "New Check"
     testType: "..."
     # ... other fields
   ```

2. If new testType:
   - Update `runtime-validator.md` with new check function
   - Update `_registry-schema.md` with new testType docs

3. Add manual testing guide to `post-verify-checklist.md`

### Modifying Categories

1. Update category definitions in `runtime-checks.yaml`
2. Update corresponding function in `runtime-validator.md`
3. Update user guide in `post-verify-checklist.md`
4. Update workflow documentation if execution order changes

## References

### Internal References

- [runtime-checks.yaml](./runtime-checks.yaml)
- [runtime-validator.md](./runtime-validator.md)
- [post-verify-workflow.md](./post-verify-workflow.md)
- [post-verify-checklist.md](./post-verify-checklist.md)

### External References

- [validation-orchestrator.md](../orchestration/validation-orchestrator.md)
- [verify.md](../processes/verify.md)
- [_validator-interface.md](../validators/_validator-interface.md)
- [_registry-schema.md](../registries/_registry-schema.md)

## Version History

- **v1.0.0** (2026-01-27): Initial implementation
  - 6 categories, 11 checks
  - VERIFY mode only
  - Non-blocking validation
