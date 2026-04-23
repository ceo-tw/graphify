---
title: Client Development Reference
type: guide
impact: HIGH
used_by: [design, planner-task, dev-executor]
domain: client
---

# Client Development Reference

> **Purpose**: Essential principles for /planner workflow in Shell Script client projects
> **Scope**: Generic patterns for shell script projects, adaptable to project-specific needs

---

## 1. Shell Script Standards (Required)

### 1.1 Shebang and Strict Mode

```bash
#!/bin/bash
# shellcheck disable=SC2034  # Optional: disable specific rules

# MANDATORY: Strict mode
set -euo pipefail

# -e: Exit on error
# -u: Error on undefined variable
# -o pipefail: Exit on pipe failure
```

### 1.2 ShellCheck Compliance

```bash
# All scripts MUST pass ShellCheck
shellcheck {client_dir}/scripts/*.sh

# Common suppressions (use sparingly with justification)
# shellcheck disable=SC2034  # Unused variable (exported elsewhere)
# shellcheck disable=SC2086  # Word splitting intended
```

---

## 2. Variable Naming (Required)

### 2.1 Naming Conventions (Google Shell Style)

```bash
# Environment variables: UPPER_SNAKE_CASE
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Local variables: lower_snake_case
local user_email="${GIT_EMAIL:-unknown}"
local config_dir="${HOME}/.config/claude-code"

# Constants: UPPER_SNAKE_CASE (readonly)
readonly DEFAULT_TIMEOUT=30
readonly CONFIG_VERSION="1.0.0"
```

### 2.2 Variable References

```bash
# Always use ${VAR} format (not $VAR)
echo "User: ${user_email}"
mkdir -p "${config_dir}"

# Always quote variables to prevent word splitting
rm -rf "${temp_dir}"  # ✅ Correct
rm -rf $temp_dir      # ❌ Dangerous

# Default values
local value="${OPTIONAL_VAR:-default_value}"
local required="${REQUIRED_VAR:?Variable is required}"
```

---

## 3. Function Patterns (Required)

### 3.1 Function Definition

```bash
# Use verb_noun naming pattern
function setup_environment() {
    local config_dir="${1:-$HOME/.config/claude-code}"

    # Create directory if not exists
    mkdir -p "${config_dir}"

    # Return success
    return 0
}

# Alternative syntax (also valid)
install_package() {
    local package_name="$1"
    # ...
}
```

### 3.2 Error Handling

```bash
function check_dependency() {
    local cmd="$1"

    if ! command -v "${cmd}" &> /dev/null; then
        echo "ERROR: ${cmd} is required but not installed." >&2
        exit 1
    fi
}

function safe_operation() {
    local file="$1"

    if [[ ! -f "${file}" ]]; then
        echo "WARN: File not found: ${file}" >&2
        return 1
    fi

    # Process file
    cat "${file}"
}
```

### 3.3 Input Validation

```bash
function validate_email() {
    local email="$1"

    if [[ ! "${email}" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$ ]]; then
        echo "ERROR: Invalid email format: ${email}" >&2
        return 1
    fi

    return 0
}
```

---

## 4. BATS Testing (Required)

### 4.1 Test File Structure

```bash
#!/usr/bin/env bats

# Test file: {client_dir}/tests/init_test.bats

setup() {
    # Runs before each test
    export TEST_DIR="$(mktemp -d)"
    export ORIGINAL_HOME="${HOME}"
    export HOME="${TEST_DIR}"
}

teardown() {
    # Runs after each test (even on failure)
    rm -rf "${TEST_DIR}"
    export HOME="${ORIGINAL_HOME}"
}

@test "init script creates config directory" {
    run ./scripts/init_claude_monitor.sh --dry-run

    [ "$status" -eq 0 ]
    [ -d "${HOME}/.config/claude-code" ]
}

@test "init script fails without required env var" {
    unset REQUIRED_VAR

    run ./scripts/init_claude_monitor.sh

    [ "$status" -ne 0 ]
    [[ "$output" =~ "ERROR" ]]
}
```

### 4.2 Test Assertions

```bash
# Status code assertion
[ "$status" -eq 0 ]           # Success
[ "$status" -ne 0 ]           # Failure

# Output assertions
[[ "$output" =~ "expected" ]] # Contains string
[[ "$output" == "exact" ]]    # Exact match

# File assertions
[ -f "${file}" ]              # File exists
[ -d "${dir}" ]               # Directory exists
[ -x "${script}" ]            # Is executable

# Line count assertions
[ "${#lines[@]}" -eq 3 ]      # Output has 3 lines
```

### 4.3 Test Execution

```bash
# Run single test file
bats {client_dir}/tests/init_test.bats

# Run all tests
bats {client_dir}/tests/*.bats

# Verbose output
bats --verbose-run {client_dir}/tests/*.bats
```

---

## 5. Fluent Bit Configuration (Required)

### 5.1 Configuration Structure

```ini
# {client_dir}/fluent-bit/fluent-bit.conf

[SERVICE]
    Flush        5
    Daemon       Off
    Log_Level    info
    Parsers_File parsers.conf

[INPUT]
    Name         tail
    Path         ${HOME}/.claude/projects/**/*.jsonl
    Tag          claude.*
    Parser       json
    Refresh_Interval 5
    Read_from_Head false

[FILTER]
    Name         lua
    Match        claude.*
    script       normalize.lua
    call         normalize

[OUTPUT]
    Name         http
    Match        *
    Host         ${OTEL_ENDPOINT:-localhost}
    Port         4318
    URI          /v1/logs
    Format       json
```

### 5.2 Lua Filter Pattern

```lua
-- {client_dir}/fluent-bit/normalize.lua

function normalize(tag, timestamp, record)
    -- Add normalized timestamp
    record["normalized_at"] = os.date("!%Y-%m-%dT%H:%M:%SZ")

    -- Convert camelCase to snake_case
    if record["sessionId"] then
        record["session_id"] = record["sessionId"]
        record["sessionId"] = nil
    end

    -- Add source tag
    record["source"] = "fluent-bit"

    return 1, timestamp, record
end
```

---

## 6. LaunchDaemon (macOS) (Required)

### 6.1 Plist Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company.fluent-bit</string>

    <key>ProgramArguments</key>
    <array>
        <string>__FLUENT_BIT_BIN__</string>
        <string>-c</string>
        <string>/usr/local/etc/fluent-bit/fluent-bit.conf</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/var/log/fluent-bit/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/var/log/fluent-bit/stderr.log</string>
</dict>
</plist>
```

### 6.2 Installation Commands

```bash
# Install daemon
sudo cp com.company.fluent-bit.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.company.fluent-bit.plist

# Uninstall daemon
sudo launchctl unload /Library/LaunchDaemons/com.company.fluent-bit.plist
sudo rm /Library/LaunchDaemons/com.company.fluent-bit.plist
```

---

## 7. Environment Variables (Required)

### 7.1 Claude Code Telemetry Variables

```bash
# Required for telemetry
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Resource attributes (user identification)
export OTEL_RESOURCE_ATTRIBUTES="service.name=claude-code,user.email=${GIT_EMAIL},department=${DEPARTMENT}"
```

### 7.2 Variable Documentation

| Variable | Required | Description |
|----------|----------|-------------|
| CLAUDE_CODE_ENABLE_TELEMETRY | Yes | Enable telemetry (1=on) |
| OTEL_METRICS_EXPORTER | Yes | Metrics export method (otlp) |
| OTEL_LOGS_EXPORTER | Yes | Logs export method (otlp) |
| OTEL_EXPORTER_OTLP_ENDPOINT | Yes | OTLP endpoint URL |
| OTEL_RESOURCE_ATTRIBUTES | Yes | User/service identification |

---

## 8. PHASE Decomposition Guide (Client-Specific)

### 8.1 Client Feature PHASE Order

```
PHASE 1: Script Design
  - Argument parsing
  - Environment validation
  - Function signatures

PHASE 2: Core Functions
  - Main business logic
  - Error handling
  - Utility functions

PHASE 3: Integration
  - LaunchDaemon/launchctl integration
  - Fluent Bit configuration
  - External service calls

PHASE 4: Testing & Polish
  - BATS test cases
  - Edge case handling
  - Documentation
```

### 8.2 Layer Mapping

| Clean Architecture | Client Equivalent |
|--------------------|-------------------|
| Domain | Environment variables, config files |
| Application | Core scripts (init, setup) |
| Adapters | Fluent Bit config, plist templates |
| Infrastructure | LaunchDaemon, system integration |

---

## 9. File Length Guidelines (Recommended)

### 9.1 Rules

| File Type | Limit | Action |
|-----------|-------|--------|
| Main scripts | 300 lines | Split into sourced modules |
| Utility modules | 200 lines | Further decompose |
| Test files | No limit | Split by functionality |

### 9.2 Script Organization

```bash
#!/bin/bash
# main_script.sh

set -euo pipefail

# Source utility modules
source "$(dirname "$0")/lib/utils.sh"
source "$(dirname "$0")/lib/validation.sh"
source "$(dirname "$0")/lib/installation.sh"

# Main execution
main() {
    validate_environment
    setup_directories
    install_components
}

main "$@"
```

---

## 10. Quality Commands

```bash
# Shell linting
shellcheck {client_dir}/scripts/*.sh

# Run BATS tests
bats {client_dir}/tests/*.bats

# Fluent Bit config validation
fluent-bit -c {client_dir}/fluent-bit/fluent-bit.conf --dry-run

# Check plist syntax
plutil -lint {client_dir}/config/*.plist
```

---

## 11. Project-Specific Guidelines Reference

Check additional guidelines in your project's AGENTS.md file:

- **Client projects**: `{client_dir}/AGENTS.md` or `{project_dir}/AGENTS.md` - Project-specific patterns, integration details
- **Project root**: `{project_dir}/AGENTS.md` - Overall project guidelines
