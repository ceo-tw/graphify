---
name: wm-setup
type: workflow
description: |
  Unified Claude Code + wm workflow setup skill. Validates and installs all wm dependencies:
  graphify (ceo-tw fork, v0.5.x), 19 graphs (_global + 18 domains), Playwright browsers,
  jq/kubectl/docker/gh, Python 3.12, Node, MCP servers, hooks, env-vars.
  Three modes: NEW_SETUP (fresh machine auto-install), UPDATE (fill missing), VERIFY (read-only health check).
  Invoke with /wm-setup. Replaces deprecated /quickstart.
allowed-tools:
  - Agent
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
  - TaskGet
  - TaskList
  - Skill
  - Read
  - Write
  - Bash
  - Glob
  - Grep
user-invocable: true
hooks:
  PostToolUse:
    - matcher: "Agent"
      hooks:
        - type: command
          command: "echo '[WM-SETUP] Subagent completed'"
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: |
            echo '[WM-SETUP-COMPLETE] wm workflow dependencies verified. Ready for /wm.'
---

# wm-setup

> **Purpose**: Single-entry setup for wm workflow — validates and installs all dependencies
> **Modes**: NEW_SETUP / UPDATE / VERIFY
> **Scope**: 12-module validation pipeline (8 base + 4 wm-specific)
> **Replaces**: /quickstart (deprecated)

---

## Invocation

```
/wm-setup              # auto-detect mode
/wm-setup VERIFY       # force VERIFY mode (read-only)
/wm-setup UPDATE       # force UPDATE mode (fill missing)
/wm-setup NEW_SETUP    # force NEW_SETUP mode (auto install all)
```

---

## Architecture Overview

### Modular Structure

```
.claude/skills/wm-setup/
├── SKILL.md                          # This file (user entry point)
├── scripts/
│   ├── check.sh                      # CLI validator entry point
│   ├── install.sh                    # CLI installer entry point
│   ├── _lib.sh                       # Shared bash functions
│   └── README.md
├── tests/
│   ├── test-phase5.sh
│   └── ...
└── rules/
    ├── registries/                   # YAML data sources (single-file modification)
    │   ├── skills.yaml
    │   ├── agents.yaml
    │   ├── hooks.yaml
    │   ├── folders.yaml
    │   ├── settings.yaml
    │   ├── domains.yaml
    │   ├── binaries.yaml             # graphify, jq, python3.12, kubectl, docker, gh, node, npm
    │   ├── graph-data.yaml           # 20 items: build-summary + _global + 18 domains
    │   ├── playwright.yaml           # chromium, firefox, webkit
    │   └── env-vars.yaml             # CLAUDE_PROJECT_DIR, CLAUDE_SKILL_DIR
    ├── validators/                   # Validation logic (11 files)
    ├── remediators/                  # Remediation logic (11 files)
    ├── orchestration/                # Pipeline control
    │   ├── validation-orchestrator.md
    │   └── workflow-orchestration.md
    ├── processes/                    # Mode-specific workflows
    │   ├── new-setup.md
    │   ├── update.md
    │   └── verify.md
    ├── components/
    │   ├── context-gate.md
    │   └── shell-env-check.md
    └── onboarding/
        ├── runtime-checks.yaml
        └── runtime-validator.md
```

### 12-Module Pipeline

```
Module  Registry              blocking  mode-scope
──────  ──────────────────    ────────  ──────────────────────────
 1/12   folders.yaml          YES       ALL
 2/12   skills.yaml           No        ALL
 3/12   agents.yaml           No        ALL
 4/12   hooks.yaml (config)   No        ALL
 5/12   hooks.yaml (scripts)  No        ALL
 6/12   settings.yaml         No        ALL
 7/12   binaries.yaml         YES*      ALL        (* graphify only)
 8/12   env-vars.yaml         No        ALL
 9/12   graph-data.yaml       YES**     ALL        (** GRAPH-001,002 only)
10/12   playwright.yaml       No        ALL        (soft/degraded)
11/12   runtime-checks.yaml   No        VERIFY only
12/12   domains.yaml          No        ALL
```

---

## Step 0: Mode Detection

**Reference**: `rules/orchestration/workflow-orchestration.md`

Detect mode using the following logic (unless user forces a mode via argument):

```
1. Check if .claude/ directory exists at project root
   - Does NOT exist → NEW_SETUP

2. Check if graphify venv is installed and correct version
   - Missing or wrong version → NEW_SETUP

3. Calculate completeness score:
   - Run scripts/check.sh --json (or inline equivalent)
   - Count FAIL items
   - FAIL count = 0 → VERIFY
   - FAIL count > 0 → UPDATE

4. User argument override:
   - /wm-setup VERIFY → force VERIFY
   - /wm-setup UPDATE → force UPDATE
   - /wm-setup NEW_SETUP → force NEW_SETUP
```

Mode summary:

| Mode | Trigger | Behavior |
|------|---------|----------|
| NEW_SETUP | No .claude/ or graphify missing | Auto-remediate all modules without asking |
| UPDATE | .claude/ present but FAIL items found | Show status report, ask user consent, remediate selected |
| VERIFY | All items pass | Read-only: report status + runtime checks |

---

## Step 1: Load Deferred Tools

Before using TaskCreate / TaskUpdate / TaskGet / TaskList, load them:

```
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList")
```

---

## Step 2: Run Validation Orchestrator

Load and execute the orchestrator:

```
Read: rules/orchestration/validation-orchestrator.md
```

The orchestrator runs all 12 modules sequentially, producing a JSON result per module:

```json
{
  "module": "binaries",
  "items": [
    {
      "id": "BIN-001",
      "name": "graphify",
      "status": "FAIL",
      "hard": true,
      "detail": "Binary not found at .claude/graphify/.venv/bin/graphify",
      "install_hint": "python3.12 -m venv .claude/graphify/.venv && .claude/graphify/.venv/bin/pip install 'git+https://github.com/ceo-tw/graphify.git@v4'",
      "referenced_by": [".claude/skills/wm/SKILL.md", ".claude/agents/review-orchestrator.md"]
    }
  ],
  "counts": { "pass": 7, "fail": 1, "warn": 0, "skip": 0 }
}
```

Collect all module results into `pipeline_results[]`.

---

## Step 3: Present Status Report

Render a markdown status table grouped by category. Output directly in the conversation.

### Status Report Format

```
wm-setup Status Report
Mode: UPDATE | Timestamp: 2026-04-21 14:30:00
────────────────────────────────────────────────────────────────────────

CATEGORY: binaries
| ID      | Name           | Status | Severity | Install Command (shortened)              | Referenced By               |
|---------|----------------|--------|----------|------------------------------------------|-----------------------------|
| BIN-001 | graphify       | FAIL   | HARD     | python3.12 -m venv .claude/graphify/...  | wm/SKILL.md, review-orc.md  |
| BIN-002 | jq             | PASS   | HARD     | brew install jq                          | validator scripts, hooks     |
| BIN-003 | python3.12     | PASS   | HARD     | brew install python@3.12                 | BIN-001                      |
| BIN-004 | kubectl        | SKIP   | —        | (inactive for graphify)                  | (deprecated)                 |
| BIN-005 | docker         | SKIP   | —        | (inactive for graphify)                  | (deprecated)                 |
| BIN-006 | gh             | WARN   | SOFT     | brew install gh                          | git-workflow/SKILL.md        |
| BIN-007 | node           | SKIP   | —        | (inactive for graphify; pure Python)     | (deprecated)                 |
| BIN-008 | npm            | SKIP   | —        | (inactive for graphify; pure Python)     | (deprecated)                 |

CATEGORY: graph-data
| ID       | Name                    | Status | Severity | Install Command (shortened)              | Referenced By               |
|----------|-------------------------|--------|----------|------------------------------------------|-----------------------------|
| GRAPH-001| build-summary           | FAIL   | HARD     | node ... build-all-graphs.ts             | wm/SKILL.md §1 Precondition |
| GRAPH-002| _global                 | FAIL   | HARD     | graphify build ./src --directed ...      | review-orchestrator.md      |
| GRAPH-003| domain:agents-orc       | FAIL   | SOFT     | node ... build-all-graphs.ts --only ...  | review-orchestrator.md      |
| ...      | ...                     | ...    | ...      | ...                                      | ...                         |

CATEGORY: playwright
| ID     | Name      | Status | Severity | Install Command                               | Referenced By           |
|--------|-----------|--------|----------|-----------------------------------------------|-------------------------|
| PW-001 | chromium  | MISS   | SOFT     | cd src/admin-portal && npx playwright install | e2e-test/SKILL.md       |
| PW-002 | firefox   | MISS   | SOFT     | cd src/admin-portal && npx playwright install | e2e-test/SKILL.md       |
| PW-003 | webkit    | MISS   | SOFT     | cd src/admin-portal && npx playwright install | e2e-test/SKILL.md       |

CATEGORY: env-vars
| ID      | Name               | Status | Severity | Install Hint                              | Referenced By           |
|---------|--------------------|--------|----------|-------------------------------------------|-------------------------|
| ENV-001 | CLAUDE_PROJECT_DIR | PASS   | HARD     | export CLAUDE_PROJECT_DIR=$(pwd)          | wm/SKILL.md, hooks      |
| ENV-002 | CLAUDE_SKILL_DIR   | MISS   | SOFT     | export CLAUDE_SKILL_DIR=$(pwd)/.claude... | wm/SKILL.md             |

CATEGORY: skills
| ID      | Name         | Status | Severity | Path                                  |
|---------|--------------|--------|----------|---------------------------------------|
| SKL-001 | wm           | PASS   | CRITICAL | .claude/skills/wm/SKILL.md            |
| SKL-002 | wm-setup     | PASS   | CRITICAL | .claude/skills/wm-setup/SKILL.md      |
| ...     | ...          | ...    | ...      | ...                                   |

CATEGORY: agents
| ID      | Name                       | Status | Severity | Path                                       |
|---------|----------------------------|--------|----------|--------------------------------------------|
| AGT-001 | review-orchestrator        | PASS   | CRITICAL | .claude/agents/review-orchestrator.md      |
| ...     | ...                        | ...    | ...      | ...                                        |

CATEGORY: folders
| ID      | Name                       | Status | Severity | Path                                       |
|---------|----------------------------|--------|----------|--------------------------------------------|
| FLD-001 | .claude                    | PASS   | HARD     | .claude/                                   |
| ...     | ...                        | ...    | ...      | ...                                        |

CATEGORY: hooks (config)
| ID      | Name              | Status | Severity | Config Key                  |
|---------|-------------------|--------|----------|-----------------------------|
| HSC-001 | sensitive-file-g. | PASS   | HARD     | PreToolUse/bash-dangerous   |
| ...     | ...               | ...    | ...      | ...                         |

CATEGORY: hooks (scripts)
| ID      | Name              | Status | Severity | Script Path                            |
|---------|-------------------|--------|----------|-----------------------------------------|
| ...     | ...               | ...    | ...      | ...                                     |

CATEGORY: settings
| ID      | Name              | Status | Severity | Key                                     |
|---------|-------------------|--------|----------|-----------------------------------------|
| ...     | ...               | ...    | ...      | ...                                     |

CATEGORY: domains
| ID      | Name              | Status | Severity | Expected Path                           |
|---------|-------------------|--------|----------|-----------------------------------------|
| ...     | ...               | ...    | ...      | ...                                     |

────────────────────────────────────────────────────────────────────────
Summary:
  PASS:  42  |  FAIL: 21  |  WARN: 3  |  SKIP: 0
  HARD FAIL:  3  (blocking: wm cannot proceed without these)
  SOFT FAIL: 18  (degraded: wm runs in reduced mode)
────────────────────────────────────────────────────────────────────────
```

**Status values**:
- `PASS` — item verified successfully
- `FAIL` — item missing or invalid
- `MISS` — item not installed (soft only, same as FAIL but for optional items)
- `WARN` — item exists but version or config is suboptimal
- `SKIP` — item not applicable in current mode

**Severity values**:
- `HARD` — blocking; wm workflow cannot function without this item
- `SOFT` — non-blocking; wm runs in degraded mode if missing

---

## Step 4: User Consent (UPDATE and NEW_SETUP modes only)

**Skip this step in VERIFY mode.**

If any FAIL items exist in UPDATE or NEW_SETUP mode, present consent dialog using `AskUserQuestion`:

```
Question: "wm-setup found N FAIL items (H hard, S soft).

[Hard FAIL] (wm blocked without these):
  - BIN-001 graphify: not installed
  - GRAPH-001 build-summary: missing

[Soft FAIL] (wm degraded without these):
  - PW-001 chromium: not installed
  - PW-002 firefox: not installed
  - ... (16 more)

How would you like to proceed?"

Options:
  1. "Auto install all (Recommended)"     - Install hard + soft items
  2. "Install hard only"                  - Install only hard-blocked items
  3. "Show install commands only (manual)" - Print commands, no execution
  4. "Cancel"                             - Exit without changes
```

**In NEW_SETUP mode**: Skip AskUserQuestion, proceed as if "Auto install all" was selected.

### Consent Option Mapping

| Choice | Action |
|--------|--------|
| Auto install all | remediate all FAIL items (hard + soft) |
| Install hard only | remediate only items where hard=true |
| Show install commands | print install_command for each FAIL item, no execution |
| Cancel | output summary with manual steps link, exit |

### Manual Steps Output (for "Show install commands" or "Cancel")

```
Manual Installation Steps
=========================

[HARD] BIN-001 graphify
  Command: python3.12 -m venv .claude/graphify/.venv && \
           .claude/graphify/.venv/bin/pip install 'git+https://github.com/ceo-tw/graphify.git@v4'
  Verify:  .claude/graphify/.venv/bin/graphify --version
  Note:    NEVER use pip install graphifyy (PyPI) — that is the upstream fork lacking URL features

[HARD] GRAPH-001 build-summary
  Command: node --experimental-strip-types --no-warnings scripts/graphify/build-all-graphs.ts
  Verify:  test -f .claude/architecture/graph/build-summary.json

[SOFT] PW-001 chromium
  Command: cd src/admin-portal && npx playwright install chromium
  Verify:  cd src/admin-portal && npx playwright install --dry-run chromium | grep -qv 'install'

...

Run .claude/skills/wm-setup/scripts/install.sh --ids BIN-001,GRAPH-001 for automated install.
```

---

## Step 5: Execute Remediation

**Reference**: Load the appropriate remediator for each FAIL item's category.

For each item to remediate (per consent choice):

```
1. Load remediator:
   Read: rules/remediators/<category>-remediation.md

2. Execute install_command from registry:
   - If install_command_macos and install_command_linux exist, detect OS first:
     OS=$(uname -s)  # Darwin = macOS, Linux = Linux

3. CRITICAL guard for graphify (BIN-001):
   - NEVER run: pip install graphifyy
   - ALWAYS use: .claude/graphify/.venv/bin/pip install 'git+https://github.com/ceo-tw/graphify.git@v4'
   - After install, verify: .claude/graphify/.venv/bin/graphify --version | grep -E '^graphify 0\.5\.'
   - If version check fails: report error with remediation hint

4. After each install:
   - Run verify_command
   - Log result to .claude/skills/wm-setup/logs/install-<timestamp>.log
   - If FAIL: capture last 20 lines of stderr, append to log

5. Report per-item result inline
```

### Remediation Order (dependency-aware)

Install in this order to respect dependencies:

```
1. folders (must exist before any file writes)
2. binaries.python3.12 (required for graphify venv)
3. binaries.graphify (requires python3.12)
4. binaries.jq (required for graph-data verify)
5. binaries.node, binaries.npm (required for graph builds)
6. binaries.kubectl, binaries.docker, binaries.gh (independent)
7. env-vars (write to settings.local.json — requires user approval before each write)
8. graph-data.build-summary (requires node)
9. graph-data._global (requires graphify)
10. graph-data.domain:* (requires node + graphify)
11. skills, agents (copy/create files)
12. hooks (config + scripts)
13. settings
14. playwright (requires npm/npx)
15. domains
```

### env-vars Remediation Special Rule

Before writing to `.claude/settings.local.json`, always show the proposed change and ask:

```
AskUserQuestion:
  Question: "wm-setup wants to add CLAUDE_PROJECT_DIR to .claude/settings.local.json.
  
  [Proposed change]
  {
    \"env\": {
      \"CLAUDE_PROJECT_DIR\": \"/path/to/project\"
    }
  }
  
  Approve?"
  Options:
    1. "Yes, write to settings.local.json"
    2. "No, I'll add it manually to my shell profile"
```

---

## Step 6: Re-verify and Final Report

After remediation completes (or if mode=VERIFY), re-run all validators and output the final report.

### Final Report Format

```
wm-setup Final Report
Mode: UPDATE | Timestamp: 2026-04-21 14:35:00
────────────────────────────────────────────────────────────────────────

Installed: 3 items
  [OK] BIN-001 graphify 0.5.4 (ceo-tw fork)
  [OK] GRAPH-001 build-summary
  [OK] GRAPH-002 _global (23,418 nodes)

Skipped (soft): 18 items
  - PW-001 chromium
  - PW-002 firefox
  ...

Still failing: 0 items

────────────────────────────────────────────────────────────────────────
```

### Final Status Verdict

Evaluate and output one of three verdicts:

**ALL PASS verdict**:
```
wm is ready for /wm.
All 12 validation modules passed. No degraded capabilities.
Run /wm to start the development workflow.
```

**SOFT FAIL only verdict**:
```
wm is ready in degraded mode.
Missing soft dependencies: chromium, firefox, webkit (Playwright browsers)
Impact: E2E tests (e2e-test skill) will not run.
Core wm workflow (review, plan, develop, bug-fix) is fully operational.
Run /wm-setup UPDATE to install missing items when needed.
```

**HARD FAIL verdict**:
```
wm cannot proceed.
Missing hard dependencies:
  - BIN-001 graphify: review-orchestrator Graphify Fast Pass disabled
  - GRAPH-001 build-summary: wm precondition check will fail

Manual steps required:
  python3.12 -m venv .claude/graphify/.venv
  .claude/graphify/.venv/bin/pip install 'git+https://github.com/ceo-tw/graphify.git@v4'
  node --experimental-strip-types --no-warnings scripts/graphify/build-all-graphs.ts

Or run: .claude/skills/wm-setup/scripts/install.sh --mode UPDATE
```

---

## graphify Installation Reference (CRITICAL)

**NEVER install from PyPI** (`pip install graphifyy`). The PyPI package (`graphifyy`) is the upstream
`safishamsi/graphify` which lacks URL-centric features required by wm workflow.

| Source | Package | Features | wm compatible |
|--------|---------|----------|---------------|
| PyPI `graphifyy` | upstream v0.4.x | AST, community, god-node only | NO |
| `safishamsi/graphify` (upstream git) | upstream | same | NO |
| `ceo-tw/graphify` (fork, branch v4) | v0.5.x | URL overlay, directed, resolve/callers/callees/blast/init-ignore | YES (required) |

**Correct install command**:
```bash
python3.12 -m venv .claude/graphify/.venv
.claude/graphify/.venv/bin/pip install "git+https://github.com/ceo-tw/graphify.git@v4"
```

**Version verification**:
```bash
.claude/graphify/.venv/bin/graphify --version
# Must output: graphify 0.5.x
```

**Feature verification**:
```bash
.claude/graphify/.venv/bin/graphify --help | grep -E 'resolve|callers|callees|blast|init-ignore'
# Must show all 5 subcommands
```

---

## VERIFY Mode Special: Runtime Checks

In VERIFY mode, after the standard 12-module pipeline, run runtime validation:

**Reference**: `rules/onboarding/runtime-validator.md`

Runtime checks include:
- MCP server connectivity (serena, memory, playwright, atlassian, context7, tavily, pencil, shadcn)
- graphify binary functional test (resolve a sample path)
- NATS connection status (if NATS_ENABLED=true)
- Node.js/npm version compatibility

Output actions required in Korean for user-facing issues:

```
Actions Required (2 items)

[Module 11] runtime-checks
- Issue: MCP server 'serena' not responding
- Impact: Symbolic code navigation disabled (find_symbol, get_symbols_overview will fail)
- Resolution:
  - (Recommended) Check Claude Code MCP settings and restart Claude Code
  - (Optional) Verify serena server binary exists and is executable

Next Steps

1. [HIGH] MCP server serena
   -> Claude Code settings.json > mcpServers > serena 설정 확인 후 재시작

Auto fix: /wm-setup UPDATE for interactive fix.
```

---

## Error Handling Reference

| Error | Recovery |
|-------|----------|
| graphify wrong version (not 0.5.x) | Reinstall from fork: `pip install --force-reinstall git+https://github.com/ceo-tw/graphify.git@v4` |
| graphify from PyPI detected | Abort + warn: "PyPI graphifyy detected — reinstalling from ceo-tw fork" |
| graph build fails (TypeScript error) | Check node version >= 22; check `scripts/graphify/build-all-graphs.ts` exists |
| Empty graph.json (0 nodes) | Source directory may be empty or wrong; check domain path in registry |
| Playwright install fails | May need system deps: `npx playwright install-deps chromium` |
| env-var write rejected by user | Guide: add to ~/.zshrc or .zprofile manually |
| Folder creation blocked (permissions) | Report path, request manual `mkdir -p <path>` |
| settings.local.json parse error | Show current file, offer to reset to minimal valid JSON |

---

## Registry Reference

| Registry | Items | Hard | Soft | Validator |
|----------|-------|------|------|-----------|
| folders.yaml | 11+ | all | 0 | folder-validator.md |
| skills.yaml | 22+ | varies | varies | skills-validator.md |
| agents.yaml | 12+ | varies | varies | agents-validator.md |
| hooks.yaml | 16+ | varies | varies | hooks-config-validator.md + hooks-scripts-validator.md |
| settings.yaml | 16+ | varies | varies | settings-validator.md |
| domains.yaml | varies | 0 | all | domains-validator.md |
| binaries.yaml | 8 | 7 | 1 | binaries-validator.md |
| graph-data.yaml | 20 | 2 | 18 | graph-data-validator.md |
| playwright.yaml | 3 | 0 | 3 | playwright-validator.md |
| env-vars.yaml | 2 | 1 | 1 | env-vars-validator.md |

**Schema**: `rules/registries/_registry-schema.md`

---

## CLI Scripts Reference

For external or automated use (CI, session hooks, manual verification):

```bash
# Check all dependencies (human-readable)
.claude/skills/wm-setup/scripts/check.sh

# Check all dependencies (JSON output for automation)
.claude/skills/wm-setup/scripts/check.sh --json

# Check specific category
.claude/skills/wm-setup/scripts/check.sh --category binaries

# Check specific item
.claude/skills/wm-setup/scripts/check.sh --module BIN-001

# Install specific items (dry-run)
.claude/skills/wm-setup/scripts/install.sh --dry-run --ids BIN-001,GRAPH-001,GRAPH-002

# Install all hard-fail items
.claude/skills/wm-setup/scripts/install.sh --mode UPDATE

# Full install (NEW_SETUP)
.claude/skills/wm-setup/scripts/install.sh --mode NEW_SETUP
```

Exit codes:
- `0` = all PASS
- `1` = any HARD FAIL
- `2` = SOFT FAIL only (no HARD FAIL)

---

## Return Format

```json
{
  "status": "SUCCESS|DEGRADED|HARD_FAIL|CANCELLED",
  "setup_mode": "NEW_SETUP|UPDATE|VERIFY",
  "pipeline": {
    "passed": 42,
    "failed": 0,
    "warned": 2,
    "skipped": 0
  },
  "hard_fail_items": [],
  "soft_fail_items": ["PW-001", "PW-002", "PW-003"],
  "installed_items": ["BIN-001", "GRAPH-001", "GRAPH-002"],
  "verdict": "wm is ready in degraded mode. Missing: Playwright browsers (E2E tests disabled)."
}
```

---

## Quick Reference

### Typical First-Time Setup Sequence

```
1. /wm-setup               → detects NEW_SETUP or UPDATE mode
2. Status report shown      → review HARD FAIL items
3. "Auto install all"       → installs graphify fork + builds 19 graphs
4. Final report             → verify graphify 0.5.x + graph node counts
5. /wm {your task}          → wm workflow now fully operational
```

### Verification Commands

```bash
# graphify version (must be 0.5.x)
.claude/graphify/.venv/bin/graphify --version

# _global graph node count (must be > 0)
jq '.nodes | length' .claude/architecture/graph/_global/graphify-out/graph.json

# Total domain graph count (must be 19)
ls .claude/architecture/graph/ | wc -l

# Full check
.claude/skills/wm-setup/scripts/check.sh --json | jq '.summary'
```

### Priority Classification for VERIFY Mode Output

| Module | Priority |
|--------|----------|
| folders | CRITICAL |
| skills, agents, binaries, graph-data | HIGH |
| hooks-config, hooks-scripts, runtime | MEDIUM |
| settings, env-vars, playwright, domains | LOW |
