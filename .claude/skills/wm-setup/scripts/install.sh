#!/usr/bin/env bash
# install.sh — wm-setup dependency installer (CLI entry point)
#
# Usage:
#   install.sh [--mode NEW_SETUP|UPDATE] [--ids id1,id2,...] [--dry-run]
#
# Options:
#   --mode NEW_SETUP  Install all items from all registries (full install)
#   --mode UPDATE     Install only FAIL items (detected by check.sh --json)
#   --ids id1,id2     Comma-separated list of item IDs to install
#   --dry-run         Print install commands without executing them
#
# Dependency order (respected automatically):
#   folders -> python3.12 -> graphify -> jq -> node/npm -> env-vars ->
#   graph-data -> skills -> agents -> hooks -> settings -> playwright -> domains
#
# Exit codes:
#   0  All installs succeeded
#   1  One or more installs failed
#
# PyPI guard:
#   install.sh will ABORT if any install_command contains 'pip install graphifyy'
#   (PyPI graphifyy is upstream fork, must not install from PyPI).
#   Always installs graphify from: git+https://github.com/ceo-tw/graphify.git@v4
#
# Logs:
#   Success/failure details written to:
#   .claude/skills/wm-setup/logs/install-<timestamp>.log

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

# ─── Argument Parsing ─────────────────────────────────────────────────────────

OPT_MODE=""
OPT_IDS=""
OPT_DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      OPT_MODE="${2:-}"
      shift 2
      ;;
    --ids)
      OPT_IDS="${2:-}"
      shift 2
      ;;
    --dry-run)
      OPT_DRY_RUN=1
      shift
      ;;
    --help|-h)
      sed -n '2,25p' "$0" | sed 's/^# \{0,2\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Validate mode
if [ -n "${OPT_MODE}" ]; then
  case "${OPT_MODE}" in
    NEW_SETUP|UPDATE) ;;
    *) abort "Unknown --mode: ${OPT_MODE}. Valid: NEW_SETUP, UPDATE" ;;
  esac
fi

# ─── Log Setup ────────────────────────────────────────────────────────────────

mkdir -p "${LOG_DIR}"
INSTALL_LOG="${LOG_DIR}/install-$(date '+%Y%m%d-%H%M%S').log"
touch "${INSTALL_LOG}"

log_install() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "${INSTALL_LOG}"
}

log_install "=== wm-setup install.sh started ==="
log_install "Mode: ${OPT_MODE:-auto} | IDs: ${OPT_IDS:-all} | DryRun: ${OPT_DRY_RUN}"

# ─── ID Resolution ────────────────────────────────────────────────────────────

# resolve_ids — determine which item IDs to install
# Returns newline-separated list of IDs in dependency order
resolve_ids() {
  if [ -n "${OPT_IDS}" ]; then
    # User-specified IDs: parse comma-separated list
    echo "${OPT_IDS}" | tr ',' '\n' | tr -d ' '
    return 0
  fi

  if [ "${OPT_MODE}" = "NEW_SETUP" ]; then
    # All items from all registries
    for cat in $(all_registry_categories); do
      local file
      file="$(registry_file "${cat}")"
      if [ -f "${file}" ]; then
        yaml_extract_ids "${file}"
      fi
    done
    return 0
  fi

  if [ "${OPT_MODE}" = "UPDATE" ] || [ -z "${OPT_MODE}" ]; then
    # Run check.sh --json and collect FAIL/MISS IDs
    if [ "${OPT_DRY_RUN}" -eq 1 ]; then
      log INFO "Dry-run: would run check.sh --json to detect FAIL items"
      # Return a representative set for dry-run demo
      echo "BIN-001"
      echo "GRAPH-001"
      echo "GRAPH-002"
      return 0
    fi

    local check_output
    if check_output="$(bash "${SCRIPT_DIR}/check.sh" --json 2>/dev/null)"; then
      : # all pass, nothing to install
    else
      : # has failures — extract from JSON
    fi

    if command -v python3 >/dev/null 2>&1 && [ -n "${check_output:-}" ]; then
      python3 - <<PYEOF 2>/dev/null
import json, sys
try:
    data = json.loads('''${check_output}''')
    for module in data.get('modules', []):
        for item in module.get('items', []):
            if item.get('status') in ('FAIL', 'MISS'):
                print(item['id'])
except Exception as e:
    pass
PYEOF
    elif command -v jq >/dev/null 2>&1 && [ -n "${check_output:-}" ]; then
      echo "${check_output}" | jq -r '.modules[].items[] | select(.status == "FAIL" or .status == "MISS") | .id'
    fi
    return 0
  fi
}

# sort_ids_by_dependency_order IDS — sort IDs by dependency order
sort_ids_by_dependency_order() {
  local ids=("$@")

  # Dependency order: assign numeric rank to each ID prefix
  rank_of() {
    local id="$1"
    case "${id}" in
      FLD-*)    echo 10 ;;
      BIN-003)  echo 20 ;;  # python3.12 before graphify
      BIN-001)  echo 25 ;;  # graphify after python3.12
      BIN-002)  echo 26 ;;  # jq after graphify (needed for graph verify)
      BIN-007)  echo 27 ;;  # node
      BIN-008)  echo 28 ;;  # npm
      BIN-004|BIN-005|BIN-006) echo 30 ;;  # kubectl, docker, gh
      ENV-*)    echo 40 ;;
      GRAPH-001) echo 51 ;; # build-summary first
      GRAPH-002) echo 52 ;; # _global second
      GRAPH-*)  echo 53 ;;  # domain graphs last
      SKL-*)    echo 60 ;;
      AGT-*)    echo 61 ;;
      HSC-*|HSS-*) echo 62 ;;
      SET-*)    echo 63 ;;
      PW-*)     echo 70 ;;
      DOM-*)    echo 80 ;;
      *)        echo 50 ;;
    esac
  }

  # Build rank-prefixed list and sort
  local ranked=()
  for id in "${ids[@]}"; do
    ranked+=("$(rank_of "${id}"):${id}")
  done

  IFS=$'\n' sorted=($(sort -t: -k1,1n <<<"${ranked[*]}")); unset IFS

  for entry in "${sorted[@]}"; do
    echo "${entry#*:}"
  done
}

# ─── Install One Item ─────────────────────────────────────────────────────────

install_item() {
  local id="$1"
  local cat
  cat="$(category_for_id "${id}")"
  local file
  file="$(registry_file "${cat}")"

  if [ ! -f "${file}" ]; then
    log WARN "Registry file not found for ${id}: ${file}"
    return 0
  fi

  local name
  name="$(yaml_extract_field "${file}" "${id}" "name")"
  [ -z "${name}" ] && name="${id}"

  local install_cmd
  install_cmd="$(yaml_extract_install_command "${file}" "${id}")"

  if [ -z "${install_cmd}" ]; then
    log WARN "${id} (${name}): no install_command defined in registry — skipping"
    log_install "SKIP ${id}: no install_command"
    return 0
  fi

  # PyPI guard — must check BEFORE executing
  pypi_guard "${install_cmd}"

  local verify_cmd
  verify_cmd="$(yaml_extract_field "${file}" "${id}" "verify_command")"

  if [ "${OPT_DRY_RUN}" -eq 1 ]; then
    echo ""
    echo "[dry-run] ${id} (${name})"
    echo "  install: ${install_cmd}"
    if [ -n "${verify_cmd}" ]; then
      echo "  verify:  ${verify_cmd}"
    fi
    return 0
  fi

  log INFO "Installing ${id} (${name})..."
  log_install "START ${id} (${name}): ${install_cmd}"

  # Execute install command
  local stderr_file
  stderr_file="$(mktemp /tmp/wm-setup-install-stderr.XXXXXX)"

  set +e
  eval "${install_cmd}" 2>"${stderr_file}"
  local exit_code=$?
  set -e

  if [ "${exit_code}" -ne 0 ]; then
    local last_stderr
    last_stderr="$(tail -20 "${stderr_file}" 2>/dev/null || echo "no stderr captured")"
    log FAIL "${id} (${name}): install failed (exit ${exit_code})"
    log_install "FAIL ${id}: exit=${exit_code}"
    log_install "STDERR (last 20 lines):"
    log_install "${last_stderr}"
    echo "  Last error output:" >&2
    tail -5 "${stderr_file}" >&2 || true
    rm -f "${stderr_file}"
    return 1
  fi

  rm -f "${stderr_file}"

  # Post-install verification
  if [ -n "${verify_cmd}" ]; then
    log INFO "  Verifying ${id}..."
    set +e
    eval "${verify_cmd}" >/dev/null 2>&1
    local verify_exit=$?
    set -e

    if [ "${verify_exit}" -eq 0 ]; then
      log OK "${id} (${name}): installed and verified"
      log_install "OK ${id}: verified"
    else
      log WARN "${id} (${name}): installed but verification failed"
      log WARN "  verify command: ${verify_cmd}"
      log_install "WARN ${id}: installed but verify failed: ${verify_cmd}"
    fi
  else
    log OK "${id} (${name}): installed (no verify_command)"
    log_install "OK ${id}: installed (no verify)"
  fi
}

# ─── Special Handlers ─────────────────────────────────────────────────────────

# graphify_install — special handling for BIN-001 (graphify fork install)
graphify_install() {
  local file
  file="$(registry_file binaries)"
  local install_cmd
  install_cmd="$(yaml_extract_field "${file}" "BIN-001" "install_command")"

  # Final PyPI guard check
  pypi_guard "${install_cmd}"

  # Verify the install command explicitly uses ceo-tw fork
  if ! echo "${install_cmd}" | grep -q "ceo-tw/graphify"; then
    abort "BIN-001 graphify install_command does not reference ceo-tw fork. Check registries/binaries.yaml BIN-001.install_command"
  fi

  install_item "BIN-001"

  # Post-install: verify version prefix
  local venv_graphify=".claude/graphify/.venv/bin/graphify"
  if [ -f "${venv_graphify}" ]; then
    local version
    version="$("${venv_graphify}" --version 2>/dev/null || echo "unknown")"
    if ! echo "${version}" | grep -qE "^graphify[[:space:]]+0\.5\."; then
      log WARN "graphify version check: expected 0.5.x, got: ${version}"
      log WARN "Consider reinstalling: .claude/graphify/.venv/bin/pip install --force-reinstall 'git+https://github.com/ceo-tw/graphify.git@v4'"
    else
      log OK "graphify version OK: ${version}"
    fi

    # Verify required subcommands
    local missing_cmds=""
    for subcmd in resolve callers callees blast; do
      if ! "${venv_graphify}" --help 2>&1 | grep -q "${subcmd}"; then
        missing_cmds="${missing_cmds} ${subcmd}"
      fi
    done

    if [ -n "${missing_cmds}" ]; then
      log WARN "graphify missing required subcommands:${missing_cmds}"
      log WARN "Installed version may not be the ceo-tw fork. Verify branch v4 was used."
    else
      log OK "graphify subcommands verified: resolve, callers, callees, blast"
    fi
  fi
}

# env_var_install ID — install an env-var by writing to settings.local.json
env_var_install() {
  local id="$1"
  local file
  file="$(registry_file env-vars)"
  local name
  name="$(yaml_extract_field "${file}" "${id}" "name")"
  local example_val
  example_val="$(yaml_extract_field "${file}" "${id}" "example_value")"

  if [ "${OPT_DRY_RUN}" -eq 1 ]; then
    echo ""
    echo "[dry-run] ${id} (${name})"
    echo "  Would write to .claude/settings.local.json:"
    echo "    { \"env\": { \"${name}\": \"<value>\" } }"
    return 0
  fi

  local current_dir
  current_dir="$(pwd)"
  local suggested_val="${current_dir}"

  if [ "${id}" = "ENV-002" ]; then
    suggested_val="${current_dir}/.claude/skills"
  fi

  local settings_file=".claude/settings.local.json"
  mkdir -p ".claude"

  if [ -f "${settings_file}" ]; then
    # Check if already set in settings.local.json
    if grep -q "\"${name}\"" "${settings_file}" 2>/dev/null; then
      log OK "${id} (${name}): already in settings.local.json"
      return 0
    fi

    # Add to existing file using python3
    if command -v python3 >/dev/null 2>&1; then
      python3 - <<PYEOF 2>/dev/null
import json, sys
try:
    with open('${settings_file}', 'r') as f:
        settings = json.load(f)
    if 'env' not in settings:
        settings['env'] = {}
    settings['env']['${name}'] = '${suggested_val}'
    with open('${settings_file}', 'w') as f:
        json.dump(settings, f, indent=2)
    print("OK")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
    else
      # Fallback: manual guidance
      log WARN "python3 not available. Add manually to ${settings_file}:"
      log WARN "  { \"env\": { \"${name}\": \"${suggested_val}\" } }"
      return 0
    fi
  else
    # Create new settings.local.json
    printf '{\n  "env": {\n    "%s": "%s"\n  }\n}\n' "${name}" "${suggested_val}" > "${settings_file}"
  fi

  log OK "${id} (${name}): written to ${settings_file} = ${suggested_val}"
  log_install "OK ${id}: written to settings.local.json"
}

# ─── Main Install Loop ────────────────────────────────────────────────────────

main() {
  require_bash4

  log INFO "wm-setup install.sh"
  log INFO "Mode: ${OPT_MODE:-auto} | DryRun: ${OPT_DRY_RUN}"
  log INFO "Log: ${INSTALL_LOG}"
  echo ""

  # Resolve IDs to install
  local ids_raw
  ids_raw="$(resolve_ids)"

  if [ -z "${ids_raw}" ]; then
    log OK "Nothing to install. All dependencies are satisfied."
    log_install "Nothing to install"
    exit 0
  fi

  # Convert to array and sort by dependency order
  local ids_arr=()
  while IFS= read -r line; do
    [ -n "${line}" ] && ids_arr+=("${line}")
  done <<< "${ids_raw}"

  local sorted_ids=()
  while IFS= read -r line; do
    [ -n "${line}" ] && sorted_ids+=("${line}")
  done < <(sort_ids_by_dependency_order "${ids_arr[@]}")

  local total=${#sorted_ids[@]}
  local installed=0
  local failed=0
  local skipped=0

  log INFO "Items to install: ${total}"
  echo ""

  for id in "${sorted_ids[@]}"; do
    # Special handlers for specific items
    case "${id}" in
      BIN-001)
        # graphify requires special handling
        if graphify_install; then
          installed=$((installed+1))
        else
          failed=$((failed+1))
          log_install "FAIL ${id}"
        fi
        ;;
      ENV-*)
        # env-vars require user notification
        if env_var_install "${id}"; then
          installed=$((installed+1))
        else
          skipped=$((skipped+1))
        fi
        ;;
      *)
        # Generic install
        if install_item "${id}"; then
          installed=$((installed+1))
        else
          failed=$((failed+1))
        fi
        ;;
    esac
  done

  echo ""
  hr
  echo "Install Summary:"
  printf "  Installed: %d  |  Failed: %d  |  Skipped: %d  |  Total: %d\n" \
    "${installed}" "${failed}" "${skipped}" "${total}"

  if [ "${failed}" -gt 0 ]; then
    log FAIL "Some installs failed. See log: ${INSTALL_LOG}"
    hr
    log_install "=== COMPLETED with ${failed} failures ==="
    exit 1
  fi

  if [ "${OPT_DRY_RUN}" -eq 0 ]; then
    log OK "All installs completed successfully."
    log OK "Run check.sh to verify final state."
  fi

  hr
  log_install "=== COMPLETED successfully ==="
  exit 0
}

main "$@"
