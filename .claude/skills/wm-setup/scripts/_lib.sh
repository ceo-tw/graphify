#!/usr/bin/env bash
# _lib.sh — Shared functions for wm-setup scripts
# Source this file: source "$(dirname "$0")/_lib.sh"

set -euo pipefail

# ─── Constants ────────────────────────────────────────────────────────────────

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY_DIR="${SKILL_DIR}/rules/registries"
LOG_DIR="${SKILL_DIR}/logs"

# Status codes
STATUS_PASS="PASS"
STATUS_FAIL="FAIL"
STATUS_MISS="MISS"
STATUS_WARN="WARN"
STATUS_SKIP="SKIP"

# Exit codes
EXIT_ALL_PASS=0
EXIT_HARD_FAIL=1
EXIT_SOFT_FAIL=2

# Colors (disabled if not a terminal)
if [ -t 1 ]; then
  COLOR_RED='\033[0;31m'
  COLOR_GREEN='\033[0;32m'
  COLOR_YELLOW='\033[1;33m'
  COLOR_CYAN='\033[0;36m'
  COLOR_BOLD='\033[1m'
  COLOR_RESET='\033[0m'
else
  COLOR_RED=''
  COLOR_GREEN=''
  COLOR_YELLOW=''
  COLOR_CYAN=''
  COLOR_BOLD=''
  COLOR_RESET=''
fi

# ─── Logging ──────────────────────────────────────────────────────────────────

# log LEVEL message
log() {
  local level="$1"
  shift
  local msg="$*"
  local ts
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  case "$level" in
    INFO)  echo -e "${COLOR_CYAN}[INFO]${COLOR_RESET}  ${msg}" ;;
    OK)    echo -e "${COLOR_GREEN}[PASS]${COLOR_RESET}  ${msg}" ;;
    FAIL)  echo -e "${COLOR_RED}[FAIL]${COLOR_RESET}  ${msg}" ;;
    WARN)  echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET}  ${msg}" ;;
    DEBUG) [ "${WM_DEBUG:-0}" = "1" ] && echo -e "[DEBUG] ${msg}" ;;
    *)     echo -e "${msg}" ;;
  esac
}

# log_file — append to install log file
log_file() {
  local logfile="${LOG_DIR}/install-$(date '+%Y%m%d-%H%M%S').log"
  mkdir -p "${LOG_DIR}"
  echo "$*" >> "${logfile}"
  echo "${logfile}"
}

# abort MESSAGE — print error and exit 1
abort() {
  echo -e "${COLOR_RED}[ABORT]${COLOR_RESET} $*" >&2
  exit 1
}

# ─── OS Detection ─────────────────────────────────────────────────────────────

detect_os() {
  local raw
  raw="$(uname -s)"
  case "${raw}" in
    Darwin) echo "macos" ;;
    Linux)  echo "linux" ;;
    *)      echo "unknown" ;;
  esac
}

OS="$(detect_os)"

# ─── YAML Parsing ─────────────────────────────────────────────────────────────

# yaml_extract_ids FILE — extract all id: values from a registry YAML file
yaml_extract_ids() {
  local file="$1"
  if [ ! -f "${file}" ]; then
    echo "" ; return 0
  fi
  grep -E '^\s+- id:' "${file}" | awk '{print $NF}' | tr -d '"' | tr -d "'"
}

# yaml_extract_field FILE ID FIELD — extract a scalar field value for a given id
# Uses python3 for reliable YAML parsing
yaml_extract_field() {
  local file="$1"
  local item_id="$2"
  local field="$3"

  if command -v python3 >/dev/null 2>&1; then
    python3 - <<PYEOF 2>/dev/null
import sys
try:
    import yaml
    with open('${file}') as f:
        doc = yaml.safe_load(f)
    for item in doc.get('items', []):
        if str(item.get('id', '')) == '${item_id}':
            val = item.get('${field}', '')
            print(str(val) if val is not None else '')
            sys.exit(0)
except Exception:
    pass
sys.exit(0)
PYEOF
  else
    # Fallback: grep-based extraction (less reliable for multiline values)
    # Find the block starting at the id, then extract the field within that block
    awk "
      /id: ['\"]?${item_id}['\"]?/ { in_block=1 }
      in_block && /^  - id:/ && !/id: ['\"]?${item_id}['\"]?/ { in_block=0 }
      in_block && /^\s+${field}:/ { sub(/.*${field}: */, \"\"); gsub(/['\"]/, \"\"); print; exit }
    " "${file}" 2>/dev/null || echo ""
  fi
}

# yaml_extract_field_os FILE ID — returns install_command_macos or install_command_linux based on OS
yaml_extract_install_command() {
  local file="$1"
  local item_id="$2"

  local cmd=""
  if [ "${OS}" = "macos" ]; then
    cmd="$(yaml_extract_field "${file}" "${item_id}" "install_command_macos")"
  elif [ "${OS}" = "linux" ]; then
    cmd="$(yaml_extract_field "${file}" "${item_id}" "install_command_linux")"
  fi

  # Fall back to generic install_command if OS-specific not found
  if [ -z "${cmd}" ]; then
    cmd="$(yaml_extract_field "${file}" "${item_id}" "install_command")"
  fi

  echo "${cmd}"
}

# ─── Registry Helpers ────────────────────────────────────────────────────────

# registry_file CATEGORY — return path to registry YAML for a category name
registry_file() {
  local category="$1"
  echo "${REGISTRY_DIR}/${category}.yaml"
}

# all_registry_categories — list all known registry categories
all_registry_categories() {
  echo "binaries"
  echo "graph-data"
  echo "playwright"
  echo "env-vars"
  echo "skills"
  echo "agents"
  echo "hooks"
  echo "folders"
  echo "settings"
  echo "domains"
}

# category_for_id ID — infer category from ID prefix
category_for_id() {
  local id="$1"
  case "${id}" in
    BIN-*)    echo "binaries" ;;
    GRAPH-*)  echo "graph-data" ;;
    PW-*)     echo "playwright" ;;
    ENV-*)    echo "env-vars" ;;
    SKL-*)    echo "skills" ;;
    AGT-*)    echo "agents" ;;
    HSC-*|HSS-*) echo "hooks" ;;
    FLD-*)    echo "folders" ;;
    SET-*)    echo "settings" ;;
    DOM-*)    echo "domains" ;;
    *)        echo "unknown" ;;
  esac
}

# ─── Verification Helpers ─────────────────────────────────────────────────────

# run_verify_command CMD — run a verify_command; return 0=pass, 1=fail
run_verify_command() {
  local cmd="$1"
  if [ -z "${cmd}" ]; then
    return 1
  fi
  eval "${cmd}" >/dev/null 2>&1
}

# check_binary NAME — return 0 if binary exists in PATH
check_binary() {
  command -v "$1" >/dev/null 2>&1
}

# check_env_var NAME — return 0 if env var is non-empty
check_env_var() {
  local val
  val="$(printenv "$1" 2>/dev/null || echo "")"
  [ -n "${val}" ]
}

# check_file PATH — return 0 if file exists and is non-empty
check_file() {
  [ -f "$1" ] && [ -s "$1" ]
}

# ─── JSON Output Helpers ──────────────────────────────────────────────────────

# json_item ID NAME STATUS HARD DETAIL — emit a JSON object for one item
json_item() {
  local id="$1"
  local name="$2"
  local status="$3"
  local hard="$4"
  local detail="$5"
  printf '{"id":"%s","name":"%s","status":"%s","hard":%s,"detail":"%s"}' \
    "${id}" "${name}" "${status}" "${hard}" "${detail}"
}

# ─── Formatting ───────────────────────────────────────────────────────────────

# status_color STATUS — return color code for status
status_color() {
  case "$1" in
    PASS) echo "${COLOR_GREEN}" ;;
    FAIL|MISS) echo "${COLOR_RED}" ;;
    WARN) echo "${COLOR_YELLOW}" ;;
    *) echo "${COLOR_RESET}" ;;
  esac
}

# hr — print horizontal rule
hr() {
  echo "────────────────────────────────────────────────────────────────────────"
}

# table_row — print a padded table row
# Usage: table_row COL1_WIDTH COL1 COL2_WIDTH COL2 ...
table_row() {
  # Simple version: just print tab-separated
  local -a args=("$@")
  local i=0
  local line=""
  while [ $i -lt ${#args[@]} ]; do
    local width="${args[$i]}"
    local val="${args[$((i+1))]}"
    line+="$(printf "%-${width}s" "${val}")"
    i=$((i+2))
  done
  echo "${line}"
}

# ─── Sanity Guards ────────────────────────────────────────────────────────────

# require_bash4 — abort if bash version < 4
require_bash4() {
  if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    abort "Bash 4+ required (current: ${BASH_VERSION}). On macOS: brew install bash"
  fi
}

# require_jq — abort if jq is not installed
require_jq() {
  if ! check_binary jq; then
    abort "jq is required but not installed. Install: brew install jq (macOS) or apt-get install jq (Linux)"
  fi
}

# pypi_guard CMD — abort if CMD contains 'pip install graphifyy' (PyPI forbidden pattern)
pypi_guard() {
  local cmd="$1"
  if echo "${cmd}" | grep -qE 'pip install graphifyy|pip3 install graphifyy'; then
    abort "PyPI graphifyy install detected and blocked. graphifyy on PyPI is the upstream fork lacking wm URL features. Use: pip install 'git+https://github.com/ceo-tw/graphify.git@v4' instead. See binaries.yaml BIN-001."
  fi
}
