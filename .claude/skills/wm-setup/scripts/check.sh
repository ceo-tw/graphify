#!/usr/bin/env bash
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"
if [ "${BASH_VERSINFO[0]:-0}" -lt 4 ]; then echo "ERROR: check.sh requires bash 4+ (found $BASH_VERSION). macOS: brew install bash. See BIN-009 in .claude/skills/wm-setup/rules/registries/binaries.yaml" >&2; exit 2; fi
# check.sh — wm-setup dependency validator (CLI entry point)
#
# Usage:
#   check.sh [--json] [--category <name>] [--module <id>]
#
# Options:
#   --json              Output JSON (orchestrator format) instead of markdown table
#   --category <name>   Check only a specific category:
#                         binaries, graph-data, playwright, env-vars,
#                         skills, agents, hooks, folders, settings, domains
#   --module <id>       Check only a specific item by ID (e.g. BIN-001)
#
# Exit codes:
#   0  All items PASS
#   1  Any HARD FAIL found
#   2  SOFT FAIL only (no HARD FAIL)
#
# Examples:
#   check.sh
#   check.sh --json | jq '.summary'
#   check.sh --category binaries
#   check.sh --module BIN-001

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

# ─── Argument Parsing ─────────────────────────────────────────────────────────

OPT_JSON=0
OPT_CATEGORY=""
OPT_MODULE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      OPT_JSON=1
      shift
      ;;
    --category)
      OPT_CATEGORY="${2:-}"
      shift 2
      ;;
    --module)
      OPT_MODULE="${2:-}"
      shift 2
      ;;
    --help|-h)
      sed -n '2,20p' "$0" | sed 's/^# \{0,2\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# ─── State Tracking ───────────────────────────────────────────────────────────

declare -A RESULTS_STATUS   # id -> PASS|FAIL|MISS|WARN|SKIP
declare -A RESULTS_HARD     # id -> true|false
declare -A RESULTS_NAME     # id -> name
declare -A RESULTS_CATEGORY # id -> category
declare -A RESULTS_DETAIL   # id -> detail message

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_WARN=0
TOTAL_SKIP=0
HARD_FAIL_COUNT=0
SOFT_FAIL_COUNT=0

# ─── Per-Category Checkers ────────────────────────────────────────────────────

check_binaries() {
  local file
  file="$(registry_file binaries)"
  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard verify_cmd version_regex status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    verify_cmd="$(yaml_extract_field "${file}" "${id}" "verify_command")"
    version_regex="$(yaml_extract_field "${file}" "${id}" "version_regex")"
    [ -z "${hard}" ] && hard="false"

    detail=""
    status="${STATUS_FAIL}"

    if [ -n "${verify_cmd}" ]; then
      if eval "${verify_cmd}" >/dev/null 2>&1; then
        status="${STATUS_PASS}"
        detail="OK"
      else
        status="${STATUS_FAIL}"
        detail="verify command failed: ${verify_cmd}"
        # Special: check if binary at all exists before complex verify
        if command -v "${name}" >/dev/null 2>&1 && [ -n "${version_regex}" ]; then
          detail="binary found but version check failed (required: ${version_regex})"
          status="${STATUS_WARN}"
        fi
      fi
    else
      # Simple: check if binary exists in PATH
      if check_binary "${name}"; then
        status="${STATUS_PASS}"
        detail="binary found in PATH"
      else
        status="${STATUS_FAIL}"
        detail="binary not found in PATH or at expected path"
      fi
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "binaries" "${detail}"
  done
}

check_graph_data() {
  local file
  file="$(registry_file graph-data)"
  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard verify_cmd path status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    path="$(yaml_extract_field "${file}" "${id}" "path")"
    verify_cmd="$(yaml_extract_field "${file}" "${id}" "verify_command")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if [ -n "${verify_cmd}" ]; then
      if eval "${verify_cmd}" >/dev/null 2>&1; then
        status="${STATUS_PASS}"
        detail="OK"
      else
        if [ -n "${path}" ] && [ -f "${path}" ]; then
          status="${STATUS_WARN}"
          detail="file exists but verify_command failed (empty graph?): ${verify_cmd}"
        else
          status="${STATUS_FAIL}"
          detail="file not found: ${path:-unknown}"
        fi
      fi
    elif [ -n "${path}" ]; then
      if check_file "${path}"; then
        status="${STATUS_PASS}"
        detail="file exists: ${path}"
      else
        status="${STATUS_FAIL}"
        detail="file not found: ${path}"
      fi
    else
      status="${STATUS_SKIP}"
      detail="no path or verify_command defined"
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "graph-data" "${detail}"
  done
}

check_playwright() {
  local file
  file="$(registry_file playwright)"
  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard verify_cmd status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    verify_cmd="$(yaml_extract_field "${file}" "${id}" "verify_command")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    # Playwright browsers: use npx playwright install --dry-run to check
    # If dry-run says "N browsers to install" -> not installed
    # Simpler check: see if the browser binary exists under playwright cache
    local pw_cache
    pw_cache="${HOME}/.cache/ms-playwright"

    case "${name}" in
      chromium)
        if find "${pw_cache}" -name "chrome" -o -name "chromium" 2>/dev/null | grep -q .; then
          status="${STATUS_PASS}"
          detail="chromium found in playwright cache"
        else
          status="${STATUS_MISS}"
          detail="chromium not installed (run: cd src/admin-portal && npx playwright install chromium)"
        fi
        ;;
      firefox)
        if find "${pw_cache}" -name "firefox" 2>/dev/null | grep -q .; then
          status="${STATUS_PASS}"
          detail="firefox found in playwright cache"
        else
          status="${STATUS_MISS}"
          detail="firefox not installed (run: cd src/admin-portal && npx playwright install firefox)"
        fi
        ;;
      webkit)
        if find "${pw_cache}" -name "WebKit" -o -name "webkit" -o -name "Webkit" 2>/dev/null | grep -q .; then
          status="${STATUS_PASS}"
          detail="webkit found in playwright cache"
        else
          status="${STATUS_MISS}"
          detail="webkit not installed (run: cd src/admin-portal && npx playwright install webkit)"
        fi
        ;;
      *)
        # Fall back to verify_command
        if [ -n "${verify_cmd}" ] && eval "${verify_cmd}" >/dev/null 2>&1; then
          status="${STATUS_PASS}"
          detail="OK"
        else
          status="${STATUS_MISS}"
          detail="${name} not found"
        fi
        ;;
    esac

    record_result "${id}" "${name}" "${status}" "${hard}" "playwright" "${detail}"
  done
}

check_env_vars() {
  local file
  file="$(registry_file env-vars)"
  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if check_env_var "${name}"; then
      status="${STATUS_PASS}"
      local val
      val="$(printenv "${name}")"
      detail="set: ${val}"
    else
      if [ "${hard}" = "true" ]; then
        status="${STATUS_FAIL}"
      else
        status="${STATUS_MISS}"
      fi
      detail="${name} is not set"
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "env-vars" "${detail}"
  done
}

check_skills() {
  local file
  file="$(registry_file skills)"
  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard path status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    path="$(yaml_extract_field "${file}" "${id}" "path")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if [ -n "${path}" ] && [ -f "${path}" ]; then
      status="${STATUS_PASS}"
      detail="SKILL.md exists"
    else
      status="${STATUS_FAIL}"
      detail="not found: ${path:-unknown}"
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "skills" "${detail}"
  done
}

check_agents() {
  local file
  file="$(registry_file agents)"
  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard path status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    path="$(yaml_extract_field "${file}" "${id}" "path")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if [ -n "${path}" ] && [ -f "${path}" ]; then
      status="${STATUS_PASS}"
      detail="agent file exists"
    else
      status="${STATUS_FAIL}"
      detail="not found: ${path:-unknown}"
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "agents" "${detail}"
  done
}

check_folders() {
  local file
  file="$(registry_file folders)"
  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard path status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    path="$(yaml_extract_field "${file}" "${id}" "path")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if [ -n "${path}" ] && [ -d "${path}" ]; then
      status="${STATUS_PASS}"
      detail="directory exists"
    else
      status="${STATUS_FAIL}"
      detail="directory not found: ${path:-unknown}"
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "folders" "${detail}"
  done
}

check_hooks() {
  local file
  file="$(registry_file hooks)"

  if [ ! -f "${file}" ]; then
    return 0
  fi

  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard status detail path kind

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    path="$(yaml_extract_field "${file}" "${id}" "path")"
    kind="$(yaml_extract_field "${file}" "${id}" "kind")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if [ "${kind}" = "script" ] && [ -n "${path}" ]; then
      if [ -f "${path}" ] && [ -x "${path}" ]; then
        status="${STATUS_PASS}"
        detail="script exists and is executable"
      elif [ -f "${path}" ]; then
        status="${STATUS_WARN}"
        detail="script exists but not executable (run: chmod +x ${path})"
      else
        status="${STATUS_FAIL}"
        detail="script not found: ${path}"
      fi
    else
      # Config hook: existence in settings.json — simplified check
      if [ -f ".claude/settings.json" ]; then
        if grep -q "${name}" ".claude/settings.json" 2>/dev/null; then
          status="${STATUS_PASS}"
          detail="found in settings.json"
        else
          status="${STATUS_FAIL}"
          detail="not found in .claude/settings.json"
        fi
      else
        status="${STATUS_FAIL}"
        detail=".claude/settings.json not found"
      fi
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "hooks" "${detail}"
  done
}

check_settings() {
  local file
  file="$(registry_file settings)"

  if [ ! -f "${file}" ]; then
    return 0
  fi

  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard status detail verify_cmd

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    verify_cmd="$(yaml_extract_field "${file}" "${id}" "verify_command")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if [ -n "${verify_cmd}" ]; then
      if eval "${verify_cmd}" >/dev/null 2>&1; then
        status="${STATUS_PASS}"
        detail="OK"
      else
        status="${STATUS_FAIL}"
        detail="verify failed: ${verify_cmd}"
      fi
    else
      status="${STATUS_SKIP}"
      detail="no verify_command defined"
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "settings" "${detail}"
  done
}

check_domains() {
  local file
  file="$(registry_file domains)"

  if [ ! -f "${file}" ]; then
    return 0
  fi

  local ids
  ids="$(yaml_extract_ids "${file}")"

  for id in ${ids}; do
    local name hard path status detail

    name="$(yaml_extract_field "${file}" "${id}" "name")"
    hard="$(yaml_extract_field "${file}" "${id}" "hard")"
    path="$(yaml_extract_field "${file}" "${id}" "path")"
    [ -z "${hard}" ] && hard="false"

    detail=""

    if [ -n "${path}" ] && [ -d "${path}" ]; then
      status="${STATUS_PASS}"
      detail="domain directory exists"
    elif [ -n "${path}" ] && [ -f "${path}" ]; then
      status="${STATUS_PASS}"
      detail="domain file exists"
    else
      status="${STATUS_MISS}"
      detail="not found: ${path:-unknown}"
    fi

    record_result "${id}" "${name}" "${status}" "${hard}" "domains" "${detail}"
  done
}

# ─── Result Recording ─────────────────────────────────────────────────────────

record_result() {
  local id="$1"
  local name="$2"
  local status="$3"
  local hard="$4"
  local category="$5"
  local detail="$6"

  RESULTS_STATUS["${id}"]="${status}"
  RESULTS_HARD["${id}"]="${hard}"
  RESULTS_NAME["${id}"]="${name}"
  RESULTS_CATEGORY["${id}"]="${category}"
  RESULTS_DETAIL["${id}"]="${detail}"

  case "${status}" in
    PASS) TOTAL_PASS=$((TOTAL_PASS + 1)) ;;
    FAIL|MISS)
      TOTAL_FAIL=$((TOTAL_FAIL + 1))
      if [ "${hard}" = "true" ]; then
        HARD_FAIL_COUNT=$((HARD_FAIL_COUNT + 1))
      else
        SOFT_FAIL_COUNT=$((SOFT_FAIL_COUNT + 1))
      fi
      ;;
    WARN) TOTAL_WARN=$((TOTAL_WARN + 1)) ;;
    SKIP) TOTAL_SKIP=$((TOTAL_SKIP + 1)) ;;
  esac
}

# ─── Single-Module Check ──────────────────────────────────────────────────────

check_single_module() {
  local id="$1"
  local cat
  cat="$(category_for_id "${id}")"

  if [ "${cat}" = "unknown" ]; then
    abort "Unknown module ID: ${id}. Cannot infer category."
  fi

  "check_${cat//-/_}" 2>/dev/null || "check_${cat}" 2>/dev/null || true

  # Filter to just the requested ID
  for key in "${!RESULTS_STATUS[@]}"; do
    if [ "${key}" != "${id}" ]; then
      unset "RESULTS_STATUS[${key}]"
      unset "RESULTS_HARD[${key}]"
      unset "RESULTS_NAME[${key}]"
      unset "RESULTS_CATEGORY[${key}]"
      unset "RESULTS_DETAIL[${key}]"
    fi
  done
}

# ─── Output: Markdown Table ───────────────────────────────────────────────────

output_markdown() {
  local ts
  ts="$(date '+%Y-%m-%d %H:%M:%S')"

  echo ""
  echo -e "${COLOR_BOLD}wm-setup Status Report${COLOR_RESET}"
  echo "Timestamp: ${ts}"
  hr

  local categories=()
  if [ -n "${OPT_CATEGORY}" ]; then
    categories=("${OPT_CATEGORY}")
  else
    # Collect unique categories from results, in pipeline order
    local pipeline_order="folders skills agents hooks settings binaries env-vars graph-data playwright domains"
    for cat in ${pipeline_order}; do
      for id in "${!RESULTS_CATEGORY[@]}"; do
        if [ "${RESULTS_CATEGORY[${id}]}" = "${cat}" ]; then
          categories+=("${cat}")
          break
        fi
      done
    done
  fi

  # Deduplicate categories
  local seen_cats=()
  local unique_cats=()
  for cat in "${categories[@]}"; do
    local found=0
    for seen in "${seen_cats[@]}"; do
      [ "${seen}" = "${cat}" ] && found=1 && break
    done
    if [ $found -eq 0 ]; then
      unique_cats+=("${cat}")
      seen_cats+=("${cat}")
    fi
  done

  for cat in "${unique_cats[@]}"; do
    echo ""
    echo -e "${COLOR_BOLD}CATEGORY: ${cat}${COLOR_RESET}"
    printf "%-12s %-35s %-6s %-6s %-50s\n" "ID" "Name" "Status" "Type" "Detail"
    printf "%-12s %-35s %-6s %-6s %-50s\n" "────────────" "───────────────────────────────────" "──────" "──────" "──────────────────────────────────────────────────"

    # Sort IDs for consistent output
    local cat_ids=()
    for id in "${!RESULTS_CATEGORY[@]}"; do
      [ "${RESULTS_CATEGORY[${id}]}" = "${cat}" ] && cat_ids+=("${id}")
    done

    # Sort IDs
    IFS=$'\n' sorted_ids=($(sort <<<"${cat_ids[*]}")); unset IFS

    for id in "${sorted_ids[@]}"; do
      local name="${RESULTS_NAME[${id}]}"
      local status="${RESULTS_STATUS[${id}]}"
      local hard="${RESULTS_HARD[${id}]}"
      local detail="${RESULTS_DETAIL[${id}]}"
      local severity
      severity="$([ "${hard}" = "true" ] && echo "HARD" || echo "SOFT")"

      local color
      color="$(status_color "${status}")"

      printf "%-12s %-35s ${color}%-6s${COLOR_RESET} %-6s %-50s\n" \
        "${id}" "${name:0:34}" "${status}" "${severity}" "${detail:0:49}"
    done
  done

  echo ""
  hr
  echo "Summary:"
  printf "  PASS: %3d  |  FAIL: %3d  |  WARN: %3d  |  SKIP: %3d\n" \
    "${TOTAL_PASS}" "${TOTAL_FAIL}" "${TOTAL_WARN}" "${TOTAL_SKIP}"
  if [ "${HARD_FAIL_COUNT}" -gt 0 ]; then
    echo -e "  ${COLOR_RED}HARD FAIL: ${HARD_FAIL_COUNT}  (blocking: wm cannot proceed without these)${COLOR_RESET}"
  fi
  if [ "${SOFT_FAIL_COUNT}" -gt 0 ]; then
    echo -e "  ${COLOR_YELLOW}SOFT FAIL: ${SOFT_FAIL_COUNT}  (degraded: wm runs in reduced mode)${COLOR_RESET}"
  fi
  hr
}

# ─── Output: JSON ─────────────────────────────────────────────────────────────

output_json() {
  local ts
  ts="$(date '+%Y-%m-%dT%H:%M:%S')"

  # Collect by category
  local categories_json=""
  local all_items_json=""
  local first_cat=1

  local pipeline_order="folders skills agents hooks settings binaries env-vars graph-data playwright domains"
  for cat in ${pipeline_order}; do
    local items_json=""
    local first_item=1
    local cat_pass=0 cat_fail=0 cat_warn=0 cat_skip=0

    # Collect IDs for this category
    local cat_ids=()
    for id in "${!RESULTS_CATEGORY[@]}"; do
      [ "${RESULTS_CATEGORY[${id}]}" = "${cat}" ] && cat_ids+=("${id}")
    done

    [ ${#cat_ids[@]} -eq 0 ] && continue

    IFS=$'\n' sorted_ids=($(sort <<<"${cat_ids[*]}")); unset IFS

    for id in "${sorted_ids[@]}"; do
      local name="${RESULTS_NAME[${id}]}"
      local status="${RESULTS_STATUS[${id}]}"
      local hard="${RESULTS_HARD[${id}]}"
      local detail="${RESULTS_DETAIL[${id}]}"

      # Get install command from registry
      local reg_file
      reg_file="$(registry_file "${cat}")"
      local install_cmd
      install_cmd="$(yaml_extract_install_command "${reg_file}" "${id}")"
      # Escape for JSON
      install_cmd="${install_cmd//\\/\\\\}"
      install_cmd="${install_cmd//\"/\\\"}"
      detail="${detail//\"/\\\"}"

      case "${status}" in
        PASS) cat_pass=$((cat_pass+1)) ;;
        FAIL|MISS) cat_fail=$((cat_fail+1)) ;;
        WARN) cat_warn=$((cat_warn+1)) ;;
        SKIP) cat_skip=$((cat_skip+1)) ;;
      esac

      if [ $first_item -eq 0 ]; then items_json+=","; fi
      first_item=0
      items_json+="{\"id\":\"${id}\",\"name\":\"${name}\",\"status\":\"${status}\",\"hard\":${hard},\"detail\":\"${detail}\",\"install_command\":\"${install_cmd}\"}"
    done

    if [ $first_cat -eq 0 ]; then categories_json+=","; fi
    first_cat=0
    categories_json+="{\"module\":\"${cat}\",\"items\":[${items_json}],\"counts\":{\"pass\":${cat_pass},\"fail\":${cat_fail},\"warn\":${cat_warn},\"skip\":${cat_skip}}}"
  done

  local overall_status="PASS"
  if [ "${HARD_FAIL_COUNT}" -gt 0 ]; then
    overall_status="HARD_FAIL"
  elif [ "${SOFT_FAIL_COUNT}" -gt 0 ]; then
    overall_status="SOFT_FAIL"
  fi

  printf '{"timestamp":"%s","overall_status":"%s","summary":{"pass":%d,"fail":%d,"warn":%d,"skip":%d,"hard_fail":%d,"soft_fail":%d},"modules":[%s]}\n' \
    "${ts}" "${overall_status}" \
    "${TOTAL_PASS}" "${TOTAL_FAIL}" "${TOTAL_WARN}" "${TOTAL_SKIP}" \
    "${HARD_FAIL_COUNT}" "${SOFT_FAIL_COUNT}" \
    "${categories_json}"
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
  require_bash4

  if [ -n "${OPT_MODULE}" ]; then
    # Single-module mode
    local cat
    cat="$(category_for_id "${OPT_MODULE}")"
    if [ "${cat}" = "unknown" ]; then
      abort "Unknown module ID prefix: ${OPT_MODULE}"
    fi
    # Map category name to check function (replace - with _)
    local fn="check_${cat//-/_}"
    if declare -f "${fn}" > /dev/null; then
      "${fn}"
    else
      abort "No check function for category: ${cat}"
    fi
  elif [ -n "${OPT_CATEGORY}" ]; then
    # Category mode
    local fn="check_${OPT_CATEGORY//-/_}"
    if declare -f "${fn}" > /dev/null; then
      "${fn}"
    else
      abort "Unknown category: ${OPT_CATEGORY}. Valid: $(all_registry_categories | tr '\n' ' ')"
    fi
  else
    # All categories
    check_folders
    check_skills
    check_agents
    check_hooks
    check_settings
    check_binaries
    check_env_vars
    check_graph_data
    check_playwright
    check_domains
  fi

  # Output
  if [ "${OPT_JSON}" -eq 1 ]; then
    output_json
  else
    output_markdown
  fi

  # Exit code
  if [ "${HARD_FAIL_COUNT}" -gt 0 ]; then
    exit "${EXIT_HARD_FAIL}"
  elif [ "${SOFT_FAIL_COUNT}" -gt 0 ] || [ "${TOTAL_FAIL}" -gt 0 ]; then
    exit "${EXIT_SOFT_FAIL}"
  else
    exit "${EXIT_ALL_PASS}"
  fi
}

main "$@"
