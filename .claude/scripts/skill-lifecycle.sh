#!/bin/bash
#
# skill-lifecycle.sh - Skill activation/deactivation management
#
# 사용법:
#   ./skill-lifecycle.sh [--repo-root PATH] activate <skill-name>
#   ./skill-lifecycle.sh [--repo-root PATH] deactivate <skill-name>
#   ./skill-lifecycle.sh [--repo-root PATH] status <skill-name>
#   ./skill-lifecycle.sh [--repo-root PATH] list
#
# Options:
#   --repo-root PATH    Explicitly specify the repository root (recommended for worktree context)
#
# Exit Codes:
#   0  - Success
#   1  - General error (missing arguments, usage error)
#   2  - Skill not found
#   3  - Already in target state
#   4  - File system error
#   5  - Safety validation failed (cross-contamination prevented)
#

set -euo pipefail

#------------------------------------------------------------------------------
# Path Resolution & Safety Functions
#------------------------------------------------------------------------------

# Detect if a directory is a git worktree
# Returns 0 (true) if worktree, 1 (false) if main repo or not a git repo
is_worktree() {
    local target_dir="${1:-.}"
    local git_file="${target_dir}/.git"

    # In a worktree, .git is a FILE containing "gitdir: /path/to/main/.git/worktrees/<name>"
    # In main repo, .git is a DIRECTORY
    [[ -f "$git_file" ]]
}

# Validate operation context to prevent cross-contamination
# Args: $1 = target_root path where operation will be performed
# Returns: 0 if safe, 5 if blocked
validate_operation_context() {
    local target_root="$1"
    local current_pwd="$PWD"

    # Safety Check: If we're in a worktree but target is main repo, REFUSE
    if is_worktree "$current_pwd" && ! is_worktree "$target_root"; then
        log_error "SAFETY: Refusing to operate on main repo from worktree context"
        log_error "  Current directory: $current_pwd (worktree)"
        log_error "  Target directory:  $target_root (main repo)"
        log_error ""
        log_error "To fix: Use --repo-root parameter with explicit worktree path:"
        log_error "  $0 --repo-root \"$current_pwd\" <command> <skill-name>"
        return 5
    fi

    # Safety Check: If CLAUDE_PROJECT_DIR is set and doesn't match target, warn
    if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]] && [[ "${CLAUDE_PROJECT_DIR}" != "${target_root}" ]]; then
        log_warning "CLAUDE_PROJECT_DIR mismatch:"
        log_warning "  Environment: ${CLAUDE_PROJECT_DIR}"
        log_warning "  Target:      ${target_root}"
        log_warning "  Proceeding with target path..."
    fi

    return 0
}

# Get project root directory with safety checks
# Priority 1: --repo-root parameter (explicit, safest)
# Priority 2: CLAUDE_PROJECT_DIR environment variable
# Priority 3: Script location (with worktree detection)
get_main_project_root() {
    # Priority 1: Explicit --repo-root parameter (handled in main())
    # This function is called after EXPLICIT_REPO_ROOT is set

    if [[ -n "${EXPLICIT_REPO_ROOT:-}" ]]; then
        echo "${EXPLICIT_REPO_ROOT}"
        return 0
    fi

    # Priority 2: Environment variable
    if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
        echo "${CLAUDE_PROJECT_DIR}"
        return 0
    fi

    # Priority 3: Script location
    # Note: This ALWAYS resolves to script's actual location, which may be:
    # - Main repo if invoked as: /path/to/main/.claude/scripts/skill-lifecycle.sh
    # - Worktree if invoked as: /path/to/worktree/.claude/scripts/skill-lifecycle.sh
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "${script_dir}/../.." && pwd
}

# Global variable for explicit repo root (set by --repo-root parameter)
EXPLICIT_REPO_ROOT=""

PROJECT_ROOT="$(get_main_project_root)"

# 설정
CLAUDE_ROOT="${PROJECT_ROOT}/.claude"
SKILLS_DIR="${CLAUDE_ROOT}/skills"
ARCHIVE_DIR="${CLAUDE_ROOT}/archive/skills"
MANIFEST="${CLAUDE_ROOT}/archive/manifest.json"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

#------------------------------------------------------------------------------
# Skill Aliases (for backward compatibility)
#------------------------------------------------------------------------------
# When deprecated skill names are requested, redirect to new names with warning

# Resolve skill alias to actual name
# Args: $1 = skill_name
# Returns: resolved skill name (prints to stdout)
resolve_skill_alias() {
    local skill_name="$1"

    # Define aliases inline to avoid associative array issues with set -u
    case "$skill_name" in
        "onboarding-agent"|"quickstart")
            log_warning "DEPRECATED: 'onboarding-agent'/'quickstart' has been renamed to 'wm-setup'"
            log_warning "Please use 'wm-setup' in the future"
            echo "wm-setup"
            ;;
        *)
            echo "$skill_name"
            ;;
    esac
}

# 사용법 출력
usage() {
    cat << EOF
사용법: $(basename "$0") [--repo-root PATH] <command> <skill-name>

Options:
  --repo-root PATH          Explicitly specify repository root directory
                            (Recommended when working in worktree context)

Commands:
  activate <skill-name>     Restore skill from archive to active skills
  deactivate <skill-name>   Move skill from active to archive
  status <skill-name>       Show skill status (active/archived/not found)
  list                      List all archived skills

Exit Codes:
  0  - Success
  1  - General error (missing arguments, usage error)
  2  - Skill not found
  3  - Already in target state
  4  - File system error
  5  - Safety validation failed (cross-contamination prevented)

Examples:
  # In main repository
  $(basename "$0") deactivate wm-setup
  $(basename "$0") activate wm-setup

  # In worktree (explicit path recommended)
  $(basename "$0") --repo-root /path/to/worktree deactivate test-skill
  $(basename "$0") --repo-root "\$PWD" list

EOF
    exit 1
}

#------------------------------------------------------------------------------
# Command Functions
#------------------------------------------------------------------------------

# Deactivate skill (move to archive)
deactivate_skill() {
    local skill_name="$1"
    local src="${SKILLS_DIR}/${skill_name}"
    local dst="${ARCHIVE_DIR}/${skill_name}"

    log_info "[1/5] Safety validation..."

    # Safety Check: Validate operation context
    if ! validate_operation_context "${PROJECT_ROOT}"; then
        return 5
    fi

    log_info "[2/5] Validating skill: ${skill_name}..."

    # Validation: Check if already deactivated (check archive first)
    if [[ -d "$dst" ]]; then
        log_warning "Already deactivated: ${skill_name}"
        return 3
    fi

    # Validation: Check if skill exists in active directory
    if [[ ! -d "$src" ]]; then
        log_error "Skill not found: ${skill_name}"
        return 2
    fi

    # Pre-flight checks
    log_info "[3/5] Pre-flight checks..."

    # Check write permission for archive directory
    if [[ -d "${ARCHIVE_DIR}" ]] && [[ ! -w "${ARCHIVE_DIR}" ]]; then
        log_error "No write permission: ${ARCHIVE_DIR}"
        return 4
    fi

    # Check manifest is writable
    if [[ ! -w "${MANIFEST}" ]]; then
        log_error "Manifest not writable: ${MANIFEST}"
        return 4
    fi

    # Count files to be moved
    local file_count
    file_count=$(find "$src" -type f 2>/dev/null | wc -l | tr -d ' ')
    log_info "Files to move: ${file_count}"

    # Create archive directory if needed
    mkdir -p "${ARCHIVE_DIR}"

    # Move skill directory
    log_info "[4/5] Moving files..."
    if ! mv "$src" "$dst"; then
        log_error "Failed to move skill directory"
        return 4
    fi

    # Update manifest
    log_info "[5/5] Updating manifest..."
    if ! update_manifest "$skill_name" "$src" "$dst"; then
        log_error "Manifest update failed (skill moved but not recorded)"
        return 4
    fi

    log_success "${skill_name} deactivated (${file_count} files moved)"
    return 0
}

# Update manifest.json with archive entry
update_manifest() {
    local skill_name="$1"
    local from="$2"
    local to="$3"

    # Ensure manifest exists
    if [[ ! -f "${MANIFEST}" ]]; then
        log_error "Manifest not found: ${MANIFEST}"
        return 4
    fi

    # Count files and lines in archived skill
    local files_count
    local total_lines
    files_count=$(find "$to" -type f 2>/dev/null | wc -l | tr -d ' ')
    total_lines=$(find "$to" -name "*.md" -type f -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")

    # Add entry to manifest.json using jq
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    jq --arg name "$skill_name" \
       --arg archived_at "$timestamp" \
       --arg from "$from" \
       --arg to "$to" \
       --argjson files "$files_count" \
       --argjson lines "$total_lines" \
       '.archived_skills += [{
           name: $name,
           archived_at: $archived_at,
           archived_from: $from,
           archived_to: $to,
           reason: "manual",
           files_count: $files,
           total_lines: $lines
       }]' "$MANIFEST" > "${MANIFEST}.tmp"

    # Atomic replace
    if ! mv "${MANIFEST}.tmp" "$MANIFEST"; then
        log_error "Failed to update manifest"
        return 4
    fi

    log_info "Manifest updated"
    return 0
}

# Activate skill (restore from archive)
activate_skill() {
    local skill_name="$1"
    local src="${ARCHIVE_DIR}/${skill_name}"
    local dst="${SKILLS_DIR}/${skill_name}"

    log_info "[1/5] Safety validation..."

    # Safety Check: Validate operation context
    if ! validate_operation_context "${PROJECT_ROOT}"; then
        return 5
    fi

    log_info "[2/5] Validating skill: ${skill_name}..."

    # Validation: Check if skill exists in archive
    if [[ ! -d "$src" ]]; then
        # Check if already active
        if [[ -d "$dst" ]]; then
            log_info "Already active: ${skill_name}"
            return 3
        else
            log_error "Skill not found in archive: ${skill_name}"
            return 2
        fi
    fi

    # Check for name collision (shouldn't happen, but defensive)
    if [[ -d "$dst" ]]; then
        log_warning "Name collision - skill already exists in skills/"
        return 4
    fi

    # Pre-flight checks
    log_info "[3/5] Pre-flight checks..."

    # Check write permission for skills directory
    if [[ ! -w "${SKILLS_DIR}" ]]; then
        log_error "No write permission: ${SKILLS_DIR}"
        return 4
    fi

    # Check manifest is writable
    if [[ ! -w "${MANIFEST}" ]]; then
        log_error "Manifest not writable: ${MANIFEST}"
        return 4
    fi

    # Count files to be moved
    local file_count
    file_count=$(find "$src" -type f 2>/dev/null | wc -l | tr -d ' ')
    log_info "Files to restore: ${file_count}"

    # Move skill directory
    log_info "[4/5] Moving files..."
    if ! mv "$src" "$dst"; then
        log_error "Failed to move skill directory"
        return 4
    fi

    # Verify skill structure
    if [[ ! -f "${dst}/SKILL.md" ]]; then
        log_warning "SKILL.md not found - skill may not function correctly"
    fi

    # Update manifest (remove entry)
    log_info "[5/5] Updating manifest..."
    jq --arg name "$skill_name" \
       '.archived_skills = [.archived_skills[] | select(.name != $name)]' \
       "$MANIFEST" > "${MANIFEST}.tmp"

    if ! mv "${MANIFEST}.tmp" "$MANIFEST"; then
        log_error "Failed to update manifest"
        return 4
    fi

    log_success "${skill_name} activated (${file_count} files restored)"
    log_info "Run /${skill_name} to use the skill"
    return 0
}

# Check skill status
check_status() {
    local skill_name="$1"

    if [[ -d "${SKILLS_DIR}/${skill_name}" ]]; then
        log_info "Status: ACTIVE"
        log_info "Location: ${SKILLS_DIR}/${skill_name}"
        return 0
    elif [[ -d "${ARCHIVE_DIR}/${skill_name}" ]]; then
        log_info "Status: ARCHIVED"
        log_info "Location: ${ARCHIVE_DIR}/${skill_name}"
        return 0
    else
        log_error "Skill not found: ${skill_name}"
        return 2
    fi
}

# List archived skills
list_archived() {
    if [[ ! -f "${MANIFEST}" ]]; then
        log_warning "No manifest file found: ${MANIFEST}"
        return 0
    fi

    local count
    count=$(jq -r '.archived_skills | length' "${MANIFEST}")

    if [[ ${count} -eq 0 ]]; then
        log_info "No archived skills"
        return 0
    fi

    log_info "Archived skills (${count}):"
    jq -r '.archived_skills[] | "  - \(.name) (archived: \(.archived_at))"' "${MANIFEST}"
}

#------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------

main() {
    # Parse --repo-root parameter if provided
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --repo-root)
                if [[ $# -lt 2 ]] || [[ "$2" == -* ]]; then
                    log_error "--repo-root requires a path argument"
                    usage
                fi
                export EXPLICIT_REPO_ROOT="$2"
                shift 2

                # Re-initialize paths with explicit root
                PROJECT_ROOT="$(get_main_project_root)"
                CLAUDE_ROOT="${PROJECT_ROOT}/.claude"
                SKILLS_DIR="${CLAUDE_ROOT}/skills"
                ARCHIVE_DIR="${CLAUDE_ROOT}/archive/skills"
                MANIFEST="${CLAUDE_ROOT}/archive/manifest.json"

                log_info "Using explicit repo root: ${PROJECT_ROOT}"
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                ;;
            *)
                # First non-option argument is the command
                break
                ;;
        esac
    done

    # Argument validation
    if [[ $# -lt 1 ]]; then
        log_error "Missing command"
        usage
    fi

    local command="$1"
    shift

    case "${command}" in
        deactivate)
            if [[ $# -lt 1 ]]; then
                log_error "Missing skill name"
                usage
            fi
            # Resolve skill alias for backward compatibility
            local resolved_name
            resolved_name=$(resolve_skill_alias "$1")
            deactivate_skill "$resolved_name"
            ;;
        activate)
            if [[ $# -lt 1 ]]; then
                log_error "Missing skill name"
                usage
            fi
            # Resolve skill alias for backward compatibility
            local resolved_name
            resolved_name=$(resolve_skill_alias "$1")
            activate_skill "$resolved_name"
            ;;
        status)
            if [[ $# -lt 1 ]]; then
                log_error "Missing skill name"
                usage
            fi
            # Resolve skill alias for backward compatibility
            local resolved_name
            resolved_name=$(resolve_skill_alias "$1")
            check_status "$resolved_name"
            ;;
        list)
            list_archived
            ;;
        *)
            log_error "Unknown command: ${command}"
            usage
            ;;
    esac
}

main "$@"
