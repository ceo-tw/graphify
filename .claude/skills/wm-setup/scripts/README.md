# wm-setup scripts

CLI entry points for wm-setup dependency validation and installation.

## Files

| File | Purpose |
|------|---------|
| `check.sh` | Validate all dependencies against registries |
| `install.sh` | Install missing dependencies from registries |
| `_lib.sh` | Shared bash functions (source by check.sh and install.sh) |

## check.sh

```bash
# Check all (human-readable table)
.claude/skills/wm-setup/scripts/check.sh

# Check all (JSON output)
.claude/skills/wm-setup/scripts/check.sh --json | jq '.summary'

# Check specific category
.claude/skills/wm-setup/scripts/check.sh --category binaries
.claude/skills/wm-setup/scripts/check.sh --category graph-data
.claude/skills/wm-setup/scripts/check.sh --category playwright
.claude/skills/wm-setup/scripts/check.sh --category env-vars

# Check specific item
.claude/skills/wm-setup/scripts/check.sh --module BIN-001
.claude/skills/wm-setup/scripts/check.sh --module GRAPH-002
```

Valid categories: `binaries`, `graph-data`, `playwright`, `env-vars`, `skills`, `agents`, `hooks`, `folders`, `settings`, `domains`

Exit codes:
- `0` All PASS
- `1` Any HARD FAIL found
- `2` SOFT FAIL only (no HARD FAIL)

## install.sh

```bash
# Dry-run specific IDs
.claude/skills/wm-setup/scripts/install.sh --dry-run --ids BIN-001,GRAPH-001,GRAPH-002

# Install specific IDs
.claude/skills/wm-setup/scripts/install.sh --ids BIN-001,GRAPH-001

# Install all FAIL items (UPDATE mode)
.claude/skills/wm-setup/scripts/install.sh --mode UPDATE

# Full install (NEW_SETUP mode — installs everything)
.claude/skills/wm-setup/scripts/install.sh --mode NEW_SETUP
```

Exit codes:
- `0` All installs succeeded
- `1` One or more installs failed

Logs written to: `.claude/skills/wm-setup/logs/install-<timestamp>.log`

## graphify PyPI Guard

install.sh will **abort** if any install_command contains `pip install graphifyy`.

The PyPI `graphifyy` package is the upstream `safishamsi/graphify` fork which lacks
URL-centric features required by wm workflow (`resolve`, `callers`, `callees`, `blast`).

Always install from ceo-tw fork:
```bash
python3.12 -m venv .claude/graphify/.venv
.claude/graphify/.venv/bin/pip install "git+https://github.com/ceo-tw/graphify.git@v4"
```

## Requirements

- bash 4+ (macOS default is bash 3.2 — install via `brew install bash`)
- python3 (for YAML parsing via PyYAML if available, grep-based fallback otherwise)
- jq (optional, used in JSON output path)
