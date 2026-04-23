#!/bin/bash
#
# worktree-manager.sh - Git Worktree 자동화 관리 스크립트
#
# 사용법:
#   ./worktree-manager.sh create <plan-name> [--base <branch>]  # 새 worktree 생성
#   ./worktree-manager.sh complete <plan-name> [--yes] [--base <branch>]  # 완료 (squash merge)
#   ./worktree-manager.sh abort <plan-name>            # 중단 (삭제)
#   ./worktree-manager.sh list                         # 활성 worktree 목록
#   ./worktree-manager.sh status <plan-name>           # 상태 확인
#
# 옵션:
#   --yes, -y    대화형 프롬프트 없이 자동 진행 (자동화 환경용)
#   --base <branch>  분기 원점 브랜치 지정 (기본값: main)
#
# Exit Codes:
#   0  - 성공
#   1  - 일반 오류 (인자 부족, 사용법 오류)
#   2  - Worktree/브랜치 존재하지 않음
#   3  - Git 작업 실패 (merge conflict 등)
#   4  - 파일 시스템 오류
#

set -euo pipefail

# 프로젝트 루트 디렉토리 찾기
# Priority 1: CLAUDE_PROJECT_DIR 환경변수
# Priority 2: Git 메인 저장소 루트 (worktree인 경우 메인 repo 찾기)
# Priority 3: 스크립트 위치 기준

get_main_project_root() {
    # Priority 1: 환경변수
    if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
        echo "${CLAUDE_PROJECT_DIR}"
        return 0
    fi

    # Priority 2: Git worktree인 경우 메인 저장소 찾기
    local git_common_dir
    git_common_dir="$(git rev-parse --git-common-dir 2>/dev/null)" || true

    if [[ -n "${git_common_dir}" && "${git_common_dir}" != ".git" ]]; then
        # Worktree 환경: common dir의 상위가 메인 저장소
        # git_common_dir은 /path/to/main/.git 형태
        local main_repo
        main_repo="$(dirname "${git_common_dir}")"
        echo "${main_repo}"
        return 0
    fi

    # Priority 3: 스크립트 위치 기준
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "$(cd "${script_dir}/../.." && pwd)"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(get_main_project_root)"

# 설정
WORKTREE_BASE="${PROJECT_ROOT}/tree"
PLANS_ACTIVE="${PROJECT_ROOT}/.claude/plans"
PLANS_COMPLETE="${PROJECT_ROOT}/.claude/plans/complete"
BRANCH_PREFIX="plan"

# 전역 옵션
AUTO_YES=false
BASE_BRANCH="main"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# 사용법 출력
usage() {
    cat << EOF
사용법: $(basename "$0") <command> [plan-name] [options]

Commands:
  create <plan-name> [--base <branch>]   새 worktree 및 브랜치 생성
  complete <plan-name> [--yes] [--base <branch>]  작업 완료 (push + squash merge + 정리)
  abort <plan-name>            작업 중단 (worktree 삭제, 변경사항 버림)
  list                         활성 worktree 목록 표시
  status <plan-name>           특정 worktree 상태 확인

Options:
  --yes, -y          대화형 프롬프트 없이 자동 진행 (Claude Code 자동화용)
                     complete 명령에서 커밋되지 않은 변경사항을 자동으로 커밋함
  --base <branch>    분기 원점 브랜치 지정 (기본값: main)
                     create: 지정 브랜치에서 worktree 분기
                     complete: 지정 브랜치로 squash merge

Environment Variables:
  CLAUDE_PROJECT_DIR   설정 시 PROJECT_ROOT로 사용 (Claude Code 환경)

Exit Codes:
  0  성공
  1  일반 오류 (인자 부족, 사용법 오류)
  2  Worktree/브랜치 존재하지 않음
  3  Git 작업 실패 (merge conflict 등)
  4  파일 시스템 오류

Examples:
  $(basename "$0") create feature-auth
  $(basename "$0") create feature-auth --base feature/main-branch
  $(basename "$0") complete feature-auth
  $(basename "$0") complete feature-auth --yes  # 자동화 환경
  $(basename "$0") complete feature-auth --yes --base feature/main-branch
  $(basename "$0") list
EOF
}

# plan-name에서 파일명 추출 (PLAN_ 접두사 제거, .md 확장자 제거)
normalize_plan_name() {
    local name="$1"
    # PLAN_ 접두사 제거
    name="${name#PLAN_}"
    # .md 확장자 제거
    name="${name%.md}"
    echo "$name"
}

# 새 worktree 생성
create_worktree() {
    local plan_name
    plan_name=$(normalize_plan_name "$1")
    local base_branch="${2:-${BASE_BRANCH}}"
    local branch_name="${BRANCH_PREFIX}/${plan_name}"
    local worktree_path="${WORKTREE_BASE}/${plan_name}"

    log_info "Worktree 생성 시작: ${plan_name}"

    # 이미 존재하는지 확인
    if [[ -d "${worktree_path}" ]]; then
        log_warning "Worktree가 이미 존재합니다: ${worktree_path}"
        echo "${worktree_path}"  # 경로 출력 (자동화에서 사용)
        return 0
    fi

    # 브랜치가 이미 존재하는지 확인
    if git show-ref --verify --quiet "refs/heads/${branch_name}"; then
        log_warning "브랜치가 이미 존재합니다: ${branch_name}"
        log_info "기존 브랜치로 worktree 생성..."
        git worktree add "${worktree_path}" "${branch_name}"
    else
        # 새 브랜치와 함께 worktree 생성
        git worktree add -b "${branch_name}" "${worktree_path}" "${base_branch}"
    fi

    log_success "Worktree 생성 완료!"
    echo ""
    echo "┌─────────────────────────────────────────────────────┐"
    echo "│  Worktree Information                               │"
    echo "├─────────────────────────────────────────────────────┤"
    echo "│  Path:   ${worktree_path}"
    echo "│  Branch: ${branch_name}"
    echo "└─────────────────────────────────────────────────────┘"
    echo ""
    log_info "작업 완료 후 다음 명령어를 사용하세요:"
    echo "  완료: $(basename "$0") complete ${plan_name}"
    echo "  중단: $(basename "$0") abort ${plan_name}"

    # 자동화에서 사용할 수 있도록 경로 출력
    echo ""
    echo "WORKTREE_PATH=${worktree_path}"
}

# 작업 완료 (squash merge)
complete_worktree() {
    local plan_name
    plan_name=$(normalize_plan_name "$1")
    local base_branch="${2:-${BASE_BRANCH}}"
    local branch_name="${BRANCH_PREFIX}/${plan_name}"
    local worktree_path="${WORKTREE_BASE}/${plan_name}"
    local plan_file="${PLANS_ACTIVE}/PLAN_${plan_name}.md"

    log_info "Worktree 완료 처리 시작: ${plan_name}"

    # Worktree 존재 확인
    if [[ ! -d "${worktree_path}" ]]; then
        log_error "Worktree가 존재하지 않습니다: ${worktree_path}"
        return 2
    fi

    # 현재 디렉토리 저장
    local original_dir
    original_dir=$(pwd)

    # worktree에서 커밋되지 않은 변경사항 확인
    cd "${worktree_path}"
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "커밋되지 않은 변경사항이 있습니다."
        git status --short
        echo ""

        if [[ "${AUTO_YES}" == true ]]; then
            # 비대화형 모드: 자동으로 커밋
            log_info "[--yes] 모든 변경사항을 자동으로 커밋합니다."
            git add -A
            git commit -m "feat(${plan_name}): finalize changes before merge

🤖 Auto-committed via worktree-manager --yes flag"
            log_success "자동 커밋 완료"
        else
            # 대화형 모드: 사용자에게 확인
            read -p "모든 변경사항을 커밋하시겠습니까? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git add -A
                git commit -m "feat(${plan_name}): finalize changes before merge"
            else
                log_error "커밋 없이 완료할 수 없습니다."
                cd "${original_dir}"
                return 1
            fi
        fi
    fi

    # 메인 프로젝트로 이동
    cd "${PROJECT_ROOT}"

    # 원격에 브랜치 push (옵션)
    log_info "원격 브랜치에 push 중..."
    if git push -u origin "${branch_name}" 2>/dev/null; then
        log_success "원격 push 완료"
    else
        log_warning "원격 push 실패 (원격 저장소가 없거나 권한 문제일 수 있음)"
    fi

    # 대상 브랜치로 전환
    log_info "${base_branch} 브랜치로 전환 중..."
    git checkout "${base_branch}"
    git pull origin "${base_branch}" 2>/dev/null || true

    # Squash merge
    log_info "Squash merge 실행 중..."
    if git merge --squash "${branch_name}"; then
        # 커밋 메시지 생성
        local commit_msg
        commit_msg=$(cat << EOF
feat(plan): complete ${plan_name}

Plan completed and merged via worktree-manager.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)
        git commit -m "${commit_msg}"
        log_success "Squash merge 완료"
    else
        log_error "Merge conflict 발생. 수동으로 해결해주세요."
        log_info "충돌 해결 후 다음 명령어로 재시도:"
        echo "  git add . && git commit"
        echo "  $(basename "$0") complete ${plan_name}"
        cd "${original_dir}"
        return 3
    fi

    # Worktree 삭제
    log_info "Worktree 삭제 중..."
    if ! git worktree remove "${worktree_path}"; then
        log_error "Worktree 삭제 실패. 강제 삭제를 시도합니다."
        git worktree remove --force "${worktree_path}" || {
            log_error "강제 삭제도 실패했습니다."
            return 4
        }
    fi

    # 로컬 브랜치 삭제
    log_info "로컬 브랜치 삭제 중..."
    git branch -D "${branch_name}"

    # 원격 브랜치 삭제 (존재하는 경우)
    if git ls-remote --exit-code --heads origin "${branch_name}" &>/dev/null; then
        log_info "원격 브랜치 삭제 중..."
        git push origin --delete "${branch_name}" 2>/dev/null || true
    fi

    # 계획 파일 이동 (날짜 폴더로)
    if [[ -f "${plan_file}" ]]; then
        log_info "계획 파일을 complete/로 이동 중..."
        today=$(date '+%Y-%m-%d')
        target_dir="${PLANS_COMPLETE}/${today}"
        mkdir -p "${target_dir}"
        mv "${plan_file}" "${target_dir}/"
        log_success "계획 파일 이동 완료: ${target_dir}/"
    else
        log_warning "계획 파일을 찾을 수 없습니다: ${plan_file}"
    fi

    cd "${original_dir}"

    log_success "🎉 Worktree 완료 처리 성공!"
    echo ""
    echo "┌─────────────────────────────────────────────────────┐"
    echo "│  Summary                                            │"
    echo "├─────────────────────────────────────────────────────┤"
    echo "│  ✅ Squash merged to ${base_branch}"
    echo "│  ✅ Worktree removed                                │"
    echo "│  ✅ Branch deleted                                  │"
    echo "│  ✅ Plan moved to .claude/plans/complete/YYYY-MM-DD │"
    echo "└─────────────────────────────────────────────────────┘"

    return 0
}

# 작업 중단
abort_worktree() {
    local plan_name
    plan_name=$(normalize_plan_name "$1")
    local branch_name="${BRANCH_PREFIX}/${plan_name}"
    local worktree_path="${WORKTREE_BASE}/${plan_name}"

    log_info "Worktree 중단 처리 시작: ${plan_name}"

    # Worktree 존재 확인
    if [[ ! -d "${worktree_path}" ]]; then
        log_warning "Worktree가 존재하지 않습니다: ${worktree_path}"
    else
        # Worktree 강제 삭제
        log_info "Worktree 강제 삭제 중..."
        git worktree remove --force "${worktree_path}" || {
            log_error "Worktree 삭제 실패"
            return 4
        }
    fi

    # 로컬 브랜치 삭제
    if git show-ref --verify --quiet "refs/heads/${branch_name}"; then
        log_info "로컬 브랜치 삭제 중..."
        git branch -D "${branch_name}"
    fi

    log_success "Worktree 중단 처리 완료"
    log_info "계획 파일은 active/에 유지됩니다 (재시도 가능)"

    return 0
}

# 활성 worktree 목록
list_worktrees() {
    log_info "활성 Worktree 목록:"
    echo ""

    if [[ ! -d "${WORKTREE_BASE}" ]] || [[ -z "$(ls -A "${WORKTREE_BASE}" 2>/dev/null)" ]]; then
        echo "  (활성 worktree 없음)"
        return 0
    fi

    echo "┌──────────────────────┬────────────────────────────────┬──────────────┐"
    echo "│ Plan Name            │ Path                           │ Branch       │"
    echo "├──────────────────────┼────────────────────────────────┼──────────────┤"

    for dir in "${WORKTREE_BASE}"/*/; do
        if [[ -d "${dir}" ]]; then
            local name
            name=$(basename "${dir}")
            local branch
            branch=$(git -C "${dir}" branch --show-current 2>/dev/null || echo "unknown")
            printf "│ %-20s │ %-30s │ %-12s │\n" "${name}" "./tree/${name}" "${branch}"
        fi
    done

    echo "└──────────────────────┴────────────────────────────────┴──────────────┘"

    return 0
}

# 특정 worktree 상태
status_worktree() {
    local plan_name
    plan_name=$(normalize_plan_name "$1")
    local branch_name="${BRANCH_PREFIX}/${plan_name}"
    local worktree_path="${WORKTREE_BASE}/${plan_name}"

    log_info "Worktree 상태: ${plan_name}"
    echo ""

    if [[ ! -d "${worktree_path}" ]]; then
        log_error "Worktree가 존재하지 않습니다: ${worktree_path}"
        return 2
    fi

    echo "┌─────────────────────────────────────────────────────┐"
    echo "│  Worktree Status                                    │"
    echo "├─────────────────────────────────────────────────────┤"
    echo "│  Path:   ${worktree_path}"
    echo "│  Branch: ${branch_name}"
    echo "└─────────────────────────────────────────────────────┘"
    echo ""

    log_info "Git Status:"
    git -C "${worktree_path}" status --short

    echo ""
    log_info "Recent Commits:"
    git -C "${worktree_path}" log --oneline -5

    # JSON 형식 출력 (자동화에서 파싱용)
    echo ""
    echo "# JSON Output for automation:"
    local changes_count
    changes_count=$(git -C "${worktree_path}" status --porcelain | wc -l | tr -d ' ')
    local commits_ahead
    commits_ahead=$(git -C "${worktree_path}" rev-list --count main..HEAD 2>/dev/null || echo "0")

    cat << EOF
{
  "plan_name": "${plan_name}",
  "worktree_path": "${worktree_path}",
  "branch": "${branch_name}",
  "uncommitted_changes": ${changes_count},
  "commits_ahead_of_main": ${commits_ahead}
}
EOF

    return 0
}

# 옵션 파싱
parse_options() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --yes|-y)
                AUTO_YES=true
                shift
                ;;
            --base)
                if [[ -n "${2:-}" ]]; then
                    BASE_BRANCH="$2"
                    shift 2
                else
                    log_error "--base 옵션에 브랜치명이 필요합니다."
                    exit 1
                fi
                ;;
            *)
                # 알 수 없는 옵션은 무시 (명령어나 plan-name일 수 있음)
                shift
                ;;
        esac
    done
}

# 메인
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    # 전체 인자에서 옵션 파싱
    parse_options "$@"

    local command="$1"
    shift

    # 옵션이 아닌 첫 번째 인자를 plan_name으로 사용
    local plan_name=""
    local skip_next=false
    for arg in "$@"; do
        if [[ "${skip_next}" == true ]]; then
            skip_next=false
            continue
        fi
        if [[ "$arg" == "--base" ]]; then
            skip_next=true
            continue
        fi
        if [[ ! "$arg" =~ ^- ]]; then
            plan_name="$arg"
            break
        fi
    done

    case "${command}" in
        create)
            if [[ -z "${plan_name}" ]]; then
                log_error "plan-name이 필요합니다."
                usage
                exit 1
            fi
            create_worktree "${plan_name}" "${BASE_BRANCH}"
            ;;
        complete)
            if [[ -z "${plan_name}" ]]; then
                log_error "plan-name이 필요합니다."
                usage
                exit 1
            fi
            complete_worktree "${plan_name}" "${BASE_BRANCH}"
            ;;
        abort)
            if [[ -z "${plan_name}" ]]; then
                log_error "plan-name이 필요합니다."
                usage
                exit 1
            fi
            abort_worktree "${plan_name}"
            ;;
        list)
            list_worktrees
            ;;
        status)
            if [[ -z "${plan_name}" ]]; then
                log_error "plan-name이 필요합니다."
                usage
                exit 1
            fi
            status_worktree "${plan_name}"
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            log_error "알 수 없는 명령어: ${command}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
