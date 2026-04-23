---
title: Registry Schema Definition
impact: HIGH
impactDescription: Defines structure for all registry YAML files
tags: [schema, registry]
used_by: [wm-setup, validators]
---

# Registry Schema Definition

**Impact: HIGH** - Schema definitions for all registry YAML files

## Overview

This document defines the schema for registry files used by wm-setup validation.
All registries use YAML format for easy parsing and single-file modification.

## Common Schema

```yaml
# All registry files MUST have these fields
version: "1.0"                    # Schema version
type: "skills|agents|hooks|folders|settings"
last_updated: "YYYY-MM-DD"        # Last modification date

items:                            # List of registry items
  - id: "XXX-NNN"                 # Unique identifier
    name: "item-name"             # Human-readable name
    priority: "CRITICAL|HIGH|MEDIUM|LOW"
    # ... type-specific fields
```

## Type-Specific Schemas

### Skills Registry Schema

```yaml
items:
  - id: "SKL-001"
    name: "skill-name"
    path: ".claude/skills/{name}/SKILL.md"
    priority: "CRITICAL|HIGH|MEDIUM"
    tags: ["orchestration", "testing", ...]
    triggerKeywords: ["keyword1", "keyword2"]
    dependencies: ["dependency1"]
    validation:
      type: "exists"              # Check file existence
```

### Agents Registry Schema

```yaml
items:
  - id: "AGT-001"
    name: "agent-name"
    path: ".claude/agents/{name}.md"
    priority: "CRITICAL|HIGH|MEDIUM"
    category: "core|bug-resolution|e2e-testing"
    invokes: ["other-agent"]
    invokedBy: ["skill-name|agent-name"]
    validation:
      type: "exists"
```

### Hooks Registry Schema

```yaml
items:
  # Hook Configuration (settings.json entries)
  - id: "HCF-001"
    name: "hook-config-name"
    type: "config"
    event: "PreToolUse|PostToolUse|UserPromptSubmit|..."
    matcher: "Edit|Write|..."
    scriptPath: ".claude/hooks/script.sh"
    priority: "CRITICAL|HIGH|MEDIUM"

  # Hook Script (actual script files)
  - id: "HSC-001"
    name: "script-name.sh"
    type: "script"
    path: ".claude/hooks/script-name.sh"
    usedBy: ["HCF-001", "HCF-002"]
    priority: "HIGH|MEDIUM"
```

### Folders Registry Schema

```yaml
items:
  - id: "FLD-001"
    name: "folder-name"
    path: ".claude/folder-path"
    priority: "CRITICAL|HIGH|MEDIUM"
    description: "Purpose of this folder"
    blocking: true|false          # If true, validation stops on missing
    validation:
      type: "exists"
```

### Settings Registry Schema

```yaml
items:
  # Environment Variables
  - id: "ENV-001"
    name: "VARIABLE_NAME"
    type: "env"
    required: true|false
    defaultValue: "value"
    recommendedValue: "recommended"        # NEW: Recommended value for production
    recommendedRationale: "explanation"    # NEW: Why this value is recommended
    description: "Variable purpose"

  # Plugins
  - id: "PLG-001"
    name: "plugin-name"
    type: "plugin"
    packageName: "plugin-name@scope"
    required: true|false
    recommendedConfig:                     # NEW: Recommended plugin configuration
      option1: value1
      option2: value2

  # MCP Servers
  - id: "MCP-001"
    name: "server-name"
    type: "mcp"
    required: true|false
    testCommand: "mcp__server__command"    # NEW: Command to test connectivity
    expectedTools:                         # NEW: Expected tool names
      - "tool1"
      - "tool2"

  # Other settings
  - id: "CFG-001"
    name: "setting-name"
    type: "config"
    path: "settings.path"
    expectedValue: "value"
```

## Validation Integration

Validators read these registries and perform checks:

```python
def validate_registry(registry_path: str) -> ValidationResult:
    """
    1. Load YAML registry
    2. For each item, run validation based on item.validation.type
    3. Return aggregated results
    """
```

## Adding New Items

To add a new skill/agent/hook:

1. Open the appropriate registry YAML file
2. Add new item with unique ID following pattern (e.g., SKL-011)
3. Validator will automatically detect and validate

**Single file modification** - No need to update multiple files.

### Runtime Checks Registry Schema

```yaml
version: "1.0"
type: "runtime-checks"
last_updated: "YYYY-MM-DD"

categories:
  - id: "RC-XXX"                          # Category ID (RC-MCP, RC-ENV, RC-PERM, etc.)
    name: "Category Name"
    description: "Category description"
    checks:
      - id: "RTC-XXX-NNN"                 # Check ID (RTC-MCP-001, etc.)
        name: "Check name"
        testType: "list_tools|value_compare|config_check|tool_call|exec_script|file_parse"
        severity: "CRITICAL|WARNING|INFO"
        required: true|false
        remediation: "Manual action description"

        # Type-specific fields (depending on testType):

        # For list_tools:
        server: "mcp-server-name"
        expectedTools: ["tool1", "tool2"]

        # For value_compare:
        envVar: "VARIABLE_NAME"
        recommendedValue: "value"
        rationale: "Why this value"

        # For config_check:
        configPath: "path.in.settings"
        checkType: "contains|equals"
        expectedPatterns: ["pattern1"]

        # For tool_call:
        plugin: "plugin-name"
        testCommand: "command description"
        expectedResult: "expected result"

        # For exec_script:
        hookType: "PreToolUse|PostToolUse"
        matcher: "tool-name"
        scriptPath: "path/to/script.sh"
        expectedExitCode: 0

        # For file_parse:
        pattern: "file/glob/pattern"
        checkType: "frontmatter_valid|syntax_check"
```

**Categories**:
- `RC-MCP`: MCP server connectivity and tool availability
- `RC-ENV`: Environment variable value comparison
- `RC-PERM`: Permission configuration checks
- `RC-PLUG`: Plugin functionality tests
- `RC-HOOK`: Hook script integration tests
- `RC-AGENT`: Agent/Skill file validation

**Used By**: `runtime-validator.md` (7th validation module, VERIFY mode only)

### Binaries Registry Schema

```yaml
version: "1.0"
type: "binaries"
last_updated: "YYYY-MM-DD"

items:
  - id: "BIN-001"
    name: "binary-name"
    kind: "binary"
    path: "optional/path/to/binary"         # Only if not on system PATH
    priority: "CRITICAL|HIGH|MEDIUM|LOW"
    hard: true|false                         # true=wm workflow blocked, false=degraded mode
    referenced_by: [...]                     # Files/modules that require this binary
    install_source: "url"                    # Source URL (for non-standard installs)
    install_command: "command"               # Standard install command
    install_command_macos: "brew install X"  # macOS-specific install
    install_command_linux: "apt-get install" # Linux-specific install
    install_command_darwin: "..."            # Darwin-specific (alias for macos)
    install_command_editable_fallback: "..." # Developer editable install alternative
    pypi_forbidden: true|false              # true=PyPI version is wrong, use install_source
    verify_command: "cmd --version"
    version_regex: "^name\\s+1\\.2\\."      # Regex to validate version output
    version_requirement: ">=22"             # Semantic version constraint string
    required_features:                       # Subcommands/flags to verify in --help
      - "subcommand1"
      - "--flag"
    verify_note: "optional note about verify"
    validation:
      type: "binary_exists|version_check|custom"
    validation_order: 0                          # See note below
```

**`validation_order` field** (optional, Binaries registry only):

- **Type**: integer
- **Default**: inherit registry file order (i.e., position in `items` list)
- **Purpose**: explicit ordering hint for items that must be validated before their registry ID would suggest. Lower values = earlier. `0` is reserved for "validate first".
- **Use case**: BIN-009 (`bash`) must run before BIN-001 (`graphify`) because the validator scripts themselves require bash 4+. Setting `validation_order: 0` on the bash entry ensures the preflight guard runs first regardless of ID sort order.
- **Implementation note**: the current `check.sh` implementation honors this via its own preflight guard; a future refactor may consume this field directly from the registry.

### Graph Data Registry Schema

```yaml
version: "1.0"
type: "graph-data"
last_updated: "YYYY-MM-DD"

items:
  - id: "GRAPH-001"
    name: "item-name"
    kind: "file"
    path: ".claude/architecture/graph/..."
    priority: "CRITICAL|HIGH"
    hard: true|false
    referenced_by: [...]
    install_command: "node ... build-all-graphs.ts"
    verify_command: "jq -e '.nodes|length>0' <path>"
    validation:
      type: "file_exists|custom"
```

### Playwright Registry Schema

```yaml
version: "1.0"
type: "playwright"
last_updated: "YYYY-MM-DD"

items:
  - id: "PW-001"
    name: "chromium|firefox|webkit"
    kind: "browser"
    priority: "HIGH"
    hard: false
    referenced_by: [...]
    install_command: "cd src/admin-portal && npx playwright install <browser>"
    verify_command: "cd src/admin-portal && npx playwright install --dry-run <browser> | grep -qv 'install'"
    validation:
      type: "custom"
```

### Env-Vars Registry Schema

```yaml
version: "1.0"
type: "env-vars"
last_updated: "YYYY-MM-DD"

items:
  - id: "ENV-001"
    name: "VARIABLE_NAME"
    kind: "env-var"
    priority: "CRITICAL|HIGH|MEDIUM"
    hard: true|false
    referenced_by: [...]
    description: "Variable purpose"
    install_command: "# Shell config or settings.local.json instruction"
    verify_command: "test -n \"$VARIABLE_NAME\""
    example_value: "example"
    fallback: "How to derive when not set"
    validation:
      type: "env_exists"
```

## References

- [skills.yaml](./skills.yaml)
- [agents.yaml](./agents.yaml)
- [hooks.yaml](./hooks.yaml)
- [folders.yaml](./folders.yaml)
- [settings.yaml](./settings.yaml)
- [binaries.yaml](./binaries.yaml)
- [graph-data.yaml](./graph-data.yaml)
- [playwright.yaml](./playwright.yaml)
- [env-vars.yaml](./env-vars.yaml)
- [runtime-checks.yaml](../onboarding/runtime-checks.yaml)
