---
name: git-workflow
type: workflow
description: Manages git branching operations (create/complete branches, recommend actions, pull with conflict detection) based on project's configured Git Workflow (GitHub Flow, GitFlow, GitLab Flow).
argument-hint: create|complete|pull [type] [name]
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
  - Skill
  - Agent
user-invocable: true
---

# Git Workflow Skill

Manages git branching operations based on the project's configured workflow.

Supports four modes:
- **create**: Create a feature/fix branch for a plan
- **complete**: Push, merge, and clean up a branch after work is done
- **pull**: Pull remote changes with conflict detection and impact analysis
- **recommend** (default): Analyze context and recommend git operations

---

## 0. Mode Dispatch

Parse the `args` string to determine mode:

| Args Pattern | Mode |
|-------------|------|
| `create {work_type} {plan_name}` | **create** |
| `complete {plan_name}` | **complete** |
| `pull [source] [target]` | **pull** |
| _(empty or other)_ | **recommend** (legacy default) |

```
if args starts with "create" → Section 6 (Create Mode)
if args starts with "complete" → Section 7 (Complete Mode)
if args starts with "pull" → Section 8 (Pull Mode)
else → Section 1 (Recommend Mode)
```

---

## 1. Recommend Mode (Execution Flow)

```
Read Settings → Analyze Context → Load Workflow Rules → Apply Decision Matrix → AskUserQuestion
```

### Step 1: Read Workflow Setting

Read `.claude/settings.json` and extract `env.GIT_WORKFLOW`.

```
Supported values: "github-flow" | "gitflow" | "gitlab-flow"
```

**If `GIT_WORKFLOW` is not set or has an invalid value:**
- Default to `"github-flow"`
- Set internal flag: `WORKFLOW_FALLBACK = true`
- Prepend fallback notice to all AskUserQuestion messages:
  > "settings flow 미정의 - GitHub-Flow로 기본 진행됩니다. 다음 내용에 대해 의사결정해주세요."

### Step 2: Analyze Current Context

Run these commands to gather context:

```bash
# Current branch
git branch --show-current

# Changed files (staged + unstaged)
git status --short
```

**Extract from context:**
- `CURRENT_BRANCH`: the active branch name
- `CHANGED_FILES`: list of modified/added/deleted files
- `HAS_CODE_CHANGES`: true if any changed file matches trigger extensions (see Section 4)
- `WORK_TYPE`: inferred from branch prefix or caller input (see Section 3)

### Step 3: Load Workflow Rules

Based on the detected workflow, read the corresponding rule file:

| Workflow | Rule File |
|----------|-----------|
| `github-flow` | `rules/workflows/github-flow.md` |
| `gitflow` | `rules/workflows/gitflow.md` |
| `gitlab-flow` | `rules/workflows/gitlab-flow.md` |

Follow the decision matrix defined in that rule file.

### Step 4: Apply Decision Matrix

The rule file contains a decision matrix mapping `(CURRENT_BRANCH, WORK_TYPE)` to one of three actions:

| Action | Meaning |
|--------|---------|
| **BLOCK** | Direct work on this branch is forbidden. Must create a new branch. |
| **PROCEED** | Current branch is correct for this work type. Continue working. |
| **RECOMMEND** | Work appears complete. Recommend PR/MR creation. |

### Step 5: Present Recommendation via AskUserQuestion

Format all recommendations in **Korean**.

**For BLOCK / RECOMMEND actions:**

Determine the recommended branch name using:
1. Work type → branch prefix mapping (Section 3)
2. Naming conventions validation (`rules/naming-conventions.md`)
3. Workflow-specific source branch rules

**AskUserQuestion format:**

```
Question: "{작업 유형}으로 판단됩니다. {분기 원점}에서 {recommended_branch_name}으로 진행(권장)"
Options:
  1. "{recommended_branch_name} 브랜치 생성 (권장)"
  2. "현재 브랜치에서 계속 작업"
  3. "다른 브랜치명 지정"
```

If `WORKFLOW_FALLBACK = true`, prepend the fallback notice before the question.

**For PROCEED action:**
- No AskUserQuestion needed
- Output brief confirmation: `"현재 브랜치({CURRENT_BRANCH})에서 작업을 계속합니다."`

---

## 2. Branch Name Validation

Before recommending any branch name, validate it against `rules/naming-conventions.md`.

**Validation checks:**
1. Lowercase only (no uppercase letters)
2. Hyphen separators (no underscores, spaces, or special chars)
3. Max 50 characters total
4. Single slash only (no nested paths like `feature/auth/login`)
5. No trailing period or special characters
6. Branch prefix must be in the workflow's allowed types list

**On validation failure:**
- Generate corrected name
- Present via AskUserQuestion:
  ```
  Question: "브랜치명 '{original}' 이(가) 네이밍 규칙에 맞지 않습니다. 수정된 이름을 사용하시겠습니까?"
  Options:
    1. "'{corrected}' 사용 (권장)"
    2. "다른 이름 직접 입력"
  ```

---

## 3. Work Type to Branch Prefix Mapping

| Work Type | Branch Prefix | Description |
|-----------|---------------|-------------|
| NEW_DEVELOPMENT | `feature/` | New feature implementation |
| MODIFICATION | `feature/` | Enhancement to existing feature |
| BUG_FIX (normal) | `fix/` | Non-critical bug fix |
| BUG_FIX (critical/production) | `hotfix/` | Production-impacting urgent fix |
| Refactoring | `refactor/` | Code restructuring without behavior change |
| Documentation | `docs/` | Documentation-only changes |
| Chore | `chore/` | Maintenance, dependency updates, config |

**Work type inference from current branch:**
- If already on a prefixed branch (e.g., `feature/`, `fix/`), infer from prefix
- If on `main`, `develop`, or environment branch, require explicit classification

---

## 4. Trigger Conditions

This skill activates when code files are detected in changed files.

### Trigger file extensions

**Backend**: `.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.go`, `.java`, `.kt`, `.swift`, `.dart`, `.sql`
**Frontend**: `.html`, `.css`, `.scss`, `.less`, `.vue`, `.svelte`
**Config as code**: `.json`, `.yaml`, `.yml`, `.toml` (only when bundled with code changes)
**Infrastructure**: `Dockerfile`, `.tf`, `.hcl`, `.sh`, `.bash`

### Excluded
- Files matching `.gitignore` patterns
- `.md` files alone do not trigger this skill

### Manual invocation
- User can invoke directly via `/git-workflow`
- Can be called by other skills (e.g., `wm`) via `Skill` tool

---

## 5. Integration Notes

### wm Pipeline Integration

This skill integrates with the wm execution pipeline:
- **create mode**: Called before `worktree-manager create` to establish a feature branch
- **complete mode**: Called after `worktree-manager complete` to push and merge to main
- **recommend mode**: Standalone analysis (user-invocable via `/git-workflow`)

### Pipeline Flow

```
wm Execution →
  git-workflow create {work_type} {plan_name}   # Step 3.2: feature branch
  worktree-manager create {plan_name} --base {feature_branch}  # Step 4: worktree on feature branch
  dev-executor / qa / ...                        # Steps 5-6: implementation
  worktree-manager complete {plan_name} --base {feature_branch}  # Step 7: squash to feature
  git-workflow complete {plan_name}               # Step 8: feature → main merge + push
```

---

## 6. Create Mode

**Invocation**: `Skill(skill="git-workflow", args="create {work_type} {plan_name}")`

### Execution Flow

1. **Read Settings**: Read `.claude/settings.json` → extract `env.GIT_WORKFLOW` (default: `github-flow`)

2. **Map work_type to branch prefix** (use Section 3 mapping table):
   - `NEW_DEVELOPMENT` / `MODIFICATION` → `feature/`
   - `BUG_FIX` → `fix/`
   - `BUG_FIX_CRITICAL` → `hotfix/`
   - etc.

3. **Generate branch name**: `{prefix}{plan_name}`
   - Example: `create NEW_DEVELOPMENT add-auth` → `feature/add-auth`

4. **Validate branch name** (Section 2 rules):
   - Apply naming conventions from `rules/naming-conventions.md`
   - Auto-correct if needed (lowercase, hyphens, length)

5. **Check for remote conflicts**:
   ```bash
   git fetch origin
   git ls-remote --heads origin {branch_name}
   ```
   - If branch exists remotely → present AskUserQuestion with alternatives

6. **Create branch**:
   ```bash
   git checkout -b {branch_name}
   ```

7. **Output result**:
   ```
   FEATURE_BRANCH={branch_name}
   ```

### Error Handling

- **Remote conflict**: AskUserQuestion with suffix options (e.g., `feature/add-auth-v2`)
- **Invalid work_type**: AskUserQuestion listing valid work types
- **Naming validation failure**: Auto-correct and confirm via AskUserQuestion

---

## 7. Complete Mode

**Invocation**: `Skill(skill="git-workflow", args="complete {plan_name}")`

### Execution Flow

1. **Detect current branch**:
   ```bash
   git branch --show-current
   ```
   - Store as `CURRENT_BRANCH`

2. **Check for uncommitted changes**:
   ```bash
   git status --porcelain
   ```
   - If changes exist → error: "커밋되지 않은 변경사항이 있습니다. 먼저 커밋하세요."

3. **Read settings**: Read `.claude/settings.json` → check `env.PR_AUTO_CREATE`
   - If `PR_AUTO_CREATE` is set → **Team mode**
   - Otherwise → **Solo mode** (default)

4. **Push to remote**:
   ```bash
   git push -u origin {CURRENT_BRANCH}
   ```

5. **Merge strategy** (based on mode):

   #### Solo Mode (default)
   ```bash
   git checkout main
   git pull origin main
   git merge --ff-only {CURRENT_BRANCH}
   ```
   - If fast-forward fails → attempt `git merge {CURRENT_BRANCH}` with merge commit
   - On success → delete feature branch:
     ```bash
     git branch -d {CURRENT_BRANCH}
     git push origin --delete {CURRENT_BRANCH}
     ```

   #### Team Mode (PR_AUTO_CREATE set)
   ```bash
   gh pr create --title "feat({plan_name}): {CURRENT_BRANCH}" --body "Plan: {plan_name}"
   ```
   - Output: PR URL

6. **Output completion report**:
   ```
   GIT_WORKFLOW_COMPLETE=true
   MERGE_TARGET=main
   MODE={solo|team}
   ```

---

## 8. Pull Mode

**Invocation**: `/git-pull` 또는 `Skill(skill="git-workflow", args="pull [source] [target]")`

Git pull with conflict detection, resolution, and impact analysis.

### Arguments

| Args Pattern | Source | Target |
|-------------|--------|--------|
| (none) | `origin/main` | current branch |
| `{branch}` | `origin/{branch}` | current branch |
| `{remote/branch}` | `{remote/branch}` | current branch |
| `{remote/branch} {target}` | `{remote/branch}` | `{target}` |

### Execution Flow

1. **Pre-Check**: 현재 상태 확인, dirty tree 시 stash (AskUserQuestion)
2. **Fetch & Analyze**: `git fetch`, incoming commit 수/내용 확인
3. **Conflict Dry-Run (MUST)**: `git merge --no-commit --no-ff` 후 `git merge --abort`
   - No conflicts → Step 4로 자동 진행
   - Conflicts → 영향 분석 수행 후 해결 방식 AskUserQuestion (theirs/ours/abort)
4. **Execute Merge**: `git merge {remote/branch} --no-edit`
5. **Impact Analysis**: Explore agent로 import/참조 검증
6. **Report**: 한국어 종합 보고서 (머지 요약, 변경사항, 충돌 해결 상세, 참조 검증)
7. **Cleanup**: stash 복원

### Conflict Resolution

충돌 발생 시 **반드시 영향 분석을 먼저 수행**한 후 의사결정을 요청합니다:

1. origin/main에서 새로 적용되는 변경사항 분석
2. origin/main 기준 해결 시 폐기되는 로컬 변경사항 분석
3. Explore agent로 다른 로컬 영향 여부 확인
4. 분석 결과 보고 후 해결 방식 선택 요청

### Error Handling

| Error | Action |
|-------|--------|
| Fetch failed | Report error, suggest retry |
| Merge abort by user | Clean state, report "중단됨" |
| Stash conflict on pop | Warn user, keep stash, report |
| No remote branch | Report "원격 브랜치를 찾을 수 없습니다: {branch}" |
