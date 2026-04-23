#!/bin/bash
# Claude Code Status Line
# Format: [Model] ████░░░░░░ XX.X% | ➜ directory git:(branch)

input=$(cat)

# === Model ===
MODEL_FULL=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
MODEL=$(echo "$MODEL_FULL" | awk '{print $1}')

# === Context Usage ===
CONTEXT_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
USAGE=$(echo "$input" | jq '.context_window.current_usage // null')

if [ "$USAGE" != "null" ]; then
    CURRENT=$(echo "$USAGE" | jq '.input_tokens + .cache_creation_input_tokens + .cache_read_input_tokens + .output_tokens')
    # 소수점 1자리 퍼센트 (awk 사용)
    PERCENT=$(awk "BEGIN {printf \"%.1f\", $CURRENT * 100 / $CONTEXT_SIZE}")
    PERCENT_INT=${PERCENT%.*}

    # 프로그레스 바 생성 (10칸)
    FILLED=$((PERCENT_INT / 10))
    [ "$FILLED" -gt 10 ] && FILLED=10
    EMPTY=$((10 - FILLED))

    BAR=""
    for ((i=0; i<FILLED; i++)); do BAR+="█"; done
    for ((i=0; i<EMPTY; i++)); do BAR+="░"; done

    # 색상 (어두운 초록 < 50%, 어두운 노랑 50-74%, 어두운 빨강 >= 75%)
    if [ "$PERCENT_INT" -ge 75 ]; then
        CTX_COLOR="\033[2;31m"
    elif [ "$PERCENT_INT" -ge 50 ]; then
        CTX_COLOR="\033[2;33m"
    else
        CTX_COLOR="\033[2;32m"
    fi

    CONTEXT_INFO="${CTX_COLOR}${BAR}\033[0m ${PERCENT}%"
else
    CONTEXT_INFO="░░░░░░░░░░ 0%"
fi

# === Directory and Git ===
cwd=$(echo "$input" | jq -r '.workspace.current_dir')
dir_name=$(basename "$cwd")

if git -C "$cwd" rev-parse --git-dir > /dev/null 2>&1; then
    branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null || echo "detached")

    if ! git -C "$cwd" --no-optional-locks diff --quiet 2>/dev/null || \
       ! git -C "$cwd" --no-optional-locks diff --cached --quiet 2>/dev/null; then
        git_status=" git:($branch) ✗"
    else
        git_status=" git:($branch)"
    fi
else
    git_status=""
fi

# === OUTPUT ===
printf "\033[90m[\033[0m\033[37m%s\033[0m\033[90m]\033[0m %b | \033[1;32m➜\033[0m \033[36m%s\033[0m%s" \
    "$MODEL" "$CONTEXT_INFO" "$dir_name" "$git_status"
