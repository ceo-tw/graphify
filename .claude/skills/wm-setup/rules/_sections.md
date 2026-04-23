# wm-setup Rules Sections

This file defines the categories of rules, organized by directory structure.
Follows the wm skill pattern with modular architecture.

---

## Section 1: Registries (Data Layer)

**Impact: HIGH**

YAML-based data registries. Single-file modification for adding new items.

| Directory | File | Impact | Description |
|-----------|------|--------|-------------|
| registries/ | _registry-schema.md | HIGH | Schema definition for all registries |
| registries/ | skills.yaml | HIGH | 10 core skills (CRITICAL: wm, solve) |
| registries/ | agents.yaml | HIGH | 12 core agents |
| registries/ | hooks.yaml | HIGH | 7 hook configs + 9 scripts |
| registries/ | folders.yaml | HIGH | 11 required folders |
| registries/ | settings.yaml | HIGH | env, plugins, config, MCP |

---

## Section 2: Validators (Logic Layer)

**Impact: HIGH**

Validation logic for each module. Implements `_validator-interface.md`.

| Directory | File | Impact | Order | Blocking |
|-----------|------|--------|-------|----------|
| validators/ | _validator-interface.md | HIGH | - | - |
| validators/ | folder-validator.md | CRITICAL | 1 | Yes |
| validators/ | skills-validator.md | HIGH | 2 | No |
| validators/ | agents-validator.md | HIGH | 3 | No |
| validators/ | hooks-config-validator.md | HIGH | 4 | No |
| validators/ | hooks-scripts-validator.md | HIGH | 5 | No |
| validators/ | settings-validator.md | HIGH | 6 | No |

---

## Section 3: Remediators (Action Layer)

**Impact: HIGH**

Remediation logic for each module. Implements `_remediation-interface.md`.

| Directory | File | Impact | Auto-Fix |
|-----------|------|--------|----------|
| remediators/ | _remediation-interface.md | HIGH | - |
| remediators/ | folder-remediation.md | CRITICAL | Yes |
| remediators/ | skills-remediation.md | HIGH | Partial |
| remediators/ | agents-remediation.md | HIGH | Partial |
| remediators/ | hooks-config-remediation.md | HIGH | No |
| remediators/ | hooks-scripts-remediation.md | HIGH | Partial |
| remediators/ | settings-remediation.md | HIGH | No |

---

## Section 4: Orchestration (Control Layer)

**Impact: CRITICAL**

Pipeline control and workflow management.

| Directory | File | Impact | Description |
|-----------|------|--------|-------------|
| orchestration/ | validation-orchestrator.md | CRITICAL | 6-module sequential pipeline |
| orchestration/ | workflow-orchestration.md | CRITICAL | Main entry point |
| orchestration/ | progress-tracking.md | MEDIUM | Progress display |

---

## Section 5: Components (Reusable)

**Impact: CRITICAL to HIGH**

Reusable components for specific workflow steps.

| Directory | File | Impact | Description |
|-----------|------|--------|-------------|
| components/ | context-gate.md | CRITICAL | Step 0 - Verify /context data |
| components/ | shell-env-check.md | HIGH | Step 1.5 - Environment variables |

---

## Section 6: Processes (Mode-Specific)

**Impact: HIGH**

Mode-specific workflow definitions.

| Directory | File | Impact | Description |
|-----------|------|--------|-------------|
| processes/ | new-setup.md | HIGH | Fresh project setup workflow |
| processes/ | update.md | HIGH | Existing project update workflow |
| processes/ | verify.md | MEDIUM | Verification-only workflow |

---

## Section 7: Guides (Reference)

**Impact: MEDIUM**

Reference documentation and templates.

| Directory | File | Impact | Status |
|-----------|------|--------|--------|
| guides/ | project-detection.md | HIGH | Active |
| guides/ | tech-detection.md | HIGH | Active |
| guides/ | tech-mapping.md | HIGH | Active |
| guides/ | checklist-template.md | MEDIUM | Active |
| guides/ | report-template.md | MEDIUM | Active |
| guides/ | skill-registry.md | MEDIUM | **Migrated → registries/** |
| guides/ | agent-registry.md | MEDIUM | **Migrated → registries/** |
| guides/ | validation.md | HIGH | **Migrated → validators/** |
| guides/ | remediation.md | HIGH | **Migrated → remediators/** |

---

## Directory Structure

```
rules/
├── _sections.md              # This file
├── _template.md              # Rule file template
│
├── registries/               # ✨ NEW: YAML data
│   ├── _registry-schema.md
│   ├── skills.yaml
│   ├── agents.yaml
│   ├── hooks.yaml
│   ├── folders.yaml
│   └── settings.yaml
│
├── validators/               # ✨ NEW: Validation logic
│   ├── _validator-interface.md
│   ├── folder-validator.md
│   ├── skills-validator.md
│   ├── agents-validator.md
│   ├── hooks-config-validator.md
│   ├── hooks-scripts-validator.md
│   └── settings-validator.md
│
├── remediators/              # ✨ NEW: Remediation logic
│   ├── _remediation-interface.md
│   ├── folder-remediation.md
│   ├── skills-remediation.md
│   ├── agents-remediation.md
│   ├── hooks-config-remediation.md
│   ├── hooks-scripts-remediation.md
│   └── settings-remediation.md
│
├── orchestration/
│   ├── validation-orchestrator.md  # ✨ NEW: Pipeline
│   ├── workflow-orchestration.md
│   └── progress-tracking.md
│
├── components/
│   ├── context-gate.md
│   └── shell-env-check.md
│
├── processes/
│   ├── new-setup.md
│   ├── update.md
│   └── verify.md
│
└── guides/
    ├── project-detection.md
    ├── tech-detection.md
    ├── tech-mapping.md
    ├── checklist-template.md
    ├── report-template.md
    ├── agent-registry.md     # (Legacy - migrated)
    ├── skill-registry.md     # (Legacy - migrated)
    ├── validation.md         # (Legacy - migrated)
    └── remediation.md        # (Legacy - migrated)
```

---

## Loading Strategy

### Pipeline Loading

```python
# Step 0: Context Gate
Read("rules/components/context-gate.md")

# Step 1: Mode Detection
Read("rules/orchestration/workflow-orchestration.md")
Read("rules/guides/project-detection.md")

# Step 1.5: Environment Check
Read("rules/components/shell-env-check.md")

# Step 2-5: Validation Pipeline
Read("rules/orchestration/validation-orchestrator.md")

# For each module in pipeline:
#   1. Read registry: registries/{module}.yaml
#   2. Read validator: validators/{module}-validator.md
#   3. If issues → Read remediator: remediators/{module}-remediation.md

# Step 6: Report
Read("rules/guides/report-template.md")
```

### On-Demand Loading

Validators and remediators are loaded only when needed:

```python
# Only load folder-validator for module 1
if current_module == "folders":
    Read("rules/validators/folder-validator.md")
    if validation_failed:
        Read("rules/remediators/folder-remediation.md")
```

---

## Pattern Alignment

This structure extends the wm skill pattern:

| wm skill | wm-setup |
|----------|------------|
| rules/components/ | rules/components/ |
| rules/processes/ | rules/processes/ |
| rules/orchestration/ | rules/orchestration/ |
| rules/rules/ | rules/guides/ |
| - | **rules/registries/** (new) |
| - | **rules/validators/** (new) |
| - | **rules/remediators/** (new) |

---

## Migration Notes

The following files have been migrated to the new architecture:

| Old Location | New Location | Status |
|--------------|--------------|--------|
| guides/skill-registry.md | registries/skills.yaml | Migrated |
| guides/agent-registry.md | registries/agents.yaml | Migrated |
| guides/validation.md | validators/*.md | Migrated |
| guides/remediation.md | remediators/*.md | Migrated |

Legacy files are kept for reference but should not be used.

---

## Template

See [_template.md](_template.md) for the standard rule file format.
