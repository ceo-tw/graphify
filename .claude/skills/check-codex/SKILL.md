---
name: check-codex
type: workflow
description: "[DEPRECATED] Activates codex review protocol for plan execution. Uses codex-review for document artifacts (design, tasks) and codex:rescue for code review after each PHASE. Handles feedback fix loop (max 2 retries) and final comprehensive review. Invoke with /check-codex or /check-codex {plan-path}."
argument-hint: "[plan-file-path (optional)]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Skill
  - Agent
  - AskUserQuestion
  - TaskCreate
  - TaskGet
  - TaskList
  - TaskUpdate
user-invocable: true
---

> WARNING: **DEPRECATED**: This skill is deprecated.
>
> Use `review-orchestrator` agent instead, which invokes `codex:rescue` (plugin skill)
> internally via `Skill("codex:rescue", ...)` with automatic Bash fallback.
>
> - Primary entry point: `Agent(subagent_type="review-orchestrator", ...)`
> - Plugin dependency: `codex:rescue` (install via plugin marketplace)
> - This file is retained for legacy callers; scheduled removal in next quarter.
>
> **[DEPRECATED] 2026-04-20**
>
> 이 skill은 `review-orchestrator` agent(`.claude/agents/review-orchestrator.md`)로 이관되었습니다.
> - **신규 plan**: wm 기본 플로우를 사용하세요. Review Gate가 review-orchestrator를 자동 호출합니다.
> - **레거시 호환**: 수동 `/check-codex` 호출은 여전히 동작합니다. 다만 새 호출자는 사용하지 마세요.
> - **마이그레이션**: 상세 내역 `.claude/plans/swift-merging-badger.md` 참조.

# Check-Codex Skill

Automates codex-powered review at each process boundary during plan execution.
Invoke with `/check-codex` (auto-detects plan from current session) or `/check-codex {plan-path}`.

**Key dependencies**: This skill delegates reviews to two codex skills depending on the artifact type:
- `codex-review` -- document artifact validation (design docs, task breakdowns)
- `codex:rescue` -- code review and implementation diagnosis

**Model**: Both skills use the Codex CLI system default (`~/.codex/config.toml`), currently **gpt-5.4** with `reasoning_effort=xhigh`. The `codex-review` SKILL.md references "o4" in its description, but the actual `codex exec` command passes no `--model` flag, so it inherits the CLI default (gpt-5.4).

---

## 0. Prerequisites

1. A plan file (`.claude/plans/*.md`) must already exist with PHASE structure in Section 2.
2. This skill is used alongside wm's execution phase (Section 6).
3. After invoking `/check-codex`, proceed with wm plan execution -- the protocol applies automatically.

---

## 1. Initialization

### Step 1.1: Resolve Plan File

If a plan path argument is provided, use it directly.
If no argument is provided, auto-detect from the current session's plan context:

```python
if not plan_path_argument:
    # 1. Check current session context -- look for plan path referenced in
    #    recent conversation (e.g., from prior /wm invocation or plan approval)
    # 2. If not found in session, query TaskList() for tasks with plan metadata
    tasks = TaskList()
    plan_paths_from_tasks = set(t.metadata.get("plan_path") for t in tasks if t.metadata.get("plan_path"))

    if len(plan_paths_from_tasks) == 1:
        plan_path = plan_paths_from_tasks.pop()
    elif len(plan_paths_from_tasks) > 1:
        AskUserQuestion("Multiple plans found in this session. Which plan should be reviewed?",
                        options=[{"label": p} for p in plan_paths_from_tasks])
        return
    else:
        # 3. Fallback: most recently modified plan file
        plan_files = Glob(".claude/plans/*.md")
        plan_files = [f for f in plan_files if "/complete/" not in f]
        if not plan_files:
            AskUserQuestion("No plan found in current session or .claude/plans/. Please provide the plan file path.")
            return
        plan_path = plan_files[0]
else:
    plan_path = plan_path_argument

plan_content = Read(plan_path)
```

### Step 1.2: Extract PHASE List

Parse `### PHASE N: {name}` patterns from Section 2 of the plan file to build the PHASE list.

### Step 1.3: Record Baseline Commit

Save current HEAD commit as the baseline for cumulative diff calculations.

```bash
BASELINE_COMMIT=$(git rev-parse HEAD)
```

### Step 1.4: Report Protocol Activation

Report to user:

```
[check-codex] Codex review protocol activated
- Plan: {plan_path}
- PHASEs: {N}
- Baseline commit: {BASELINE_COMMIT}
- Model: gpt-5.4 (Codex CLI default)
- Review scope: Cumulative diff from baseline
- Max feedback retries: 2 per step
- Skill mapping:
  - design complete     -> codex-review (document validation)
  - planner-task complete -> codex-review (document validation)
  - dev-executor PHASE complete -> codex:rescue (code review)
  - qa complete         -> SKIP (qa agent handles this)
  - All PHASEs complete -> codex:rescue (comprehensive review)
```

---

## 2. Process-Specific Review Protocol

Different codex skills are used depending on the process step that just completed.

### 2.A: Document Review (after design / planner-task)

Use `codex-review` skill for document artifact validation.

**After design completes:**
```python
Skill(skill="codex-review", args=f"--file {design_doc_path}")
# codex-review auto-classifies *-DESIGN.md files
# Reviews: completeness, clarity, consistency, measurability
# Severity: CRITICAL (blocks next step) / WARNING / INFO
```

**After planner-task completes:**
```python
Skill(skill="codex-review", args=f"--file {tasks_doc_path}")
# codex-review auto-classifies *-TASKS*.md files
# Reviews: task decomposition quality, dependency correctness, TDD coverage
```

**Feedback handling**: If CRITICAL issues found, apply feedback fix loop (Section 4). WARNING/INFO are logged but do not block.

### 2.B: Code Review (after each dev-executor PHASE)

Use `codex:rescue` for code-level review after each PHASE's dev-executor completes.

#### Step 2.B.1: Collect Cumulative Diff

```bash
git diff --name-only ${BASELINE_COMMIT}..HEAD
git diff --stat ${BASELINE_COMMIT}..HEAD
```

#### Step 2.B.2: Invoke codex:rescue

```python
Skill(skill="codex:rescue", args=
    f"Review the cumulative code changes for PHASE {N}/{TOTAL} of plan {plan_path}.\n\n"
    f"PHASE: {phase_name}\n"
    f"Requirements:\n{phase_requirements}\n\n"
    f"Changed files (cumulative from {BASELINE_COMMIT}):\n{changed_files_list}\n\n"
    f"Review checklist:\n"
    f"1. Implementation completeness vs PHASE requirements\n"
    f"2. Code quality (bugs, security, performance)\n"
    f"3. Project convention compliance (CLAUDE.md, stack-conventions.md)\n"
    f"4. Test coverage adequacy\n"
    f"5. Integration issues with previous PHASEs\n\n"
    f"If issues: list file:line references with fixes.\n"
    f"If clean: return 'LGTM - proceed to next PHASE'."
)
```

**Feedback handling**: Apply feedback fix loop (Section 4) for CRITICAL/HIGH issues.

### 2.C: QA Complete -- SKIP

After qa agent completes, **no additional codex review is performed**. The qa agent's own validation is sufficient at this step. Proceeding directly to the next PHASE or final review.

---

## 3. Final Comprehensive Review

Execute after all PHASEs complete (post-qa of the last PHASE).

### Step 3.1: Collect Full Change Scope

```bash
git diff --name-only ${BASELINE_COMMIT}..HEAD
git diff --stat ${BASELINE_COMMIT}..HEAD
git log --oneline ${BASELINE_COMMIT}..HEAD
```

### Step 3.2: Comprehensive codex:rescue Review

```python
Skill(skill="codex:rescue", args=
    f"Comprehensive review of full plan completion.\n\n"
    f"Plan: {plan_path}\n"
    f"All {TOTAL} PHASEs completed.\n\n"
    f"Requirements:\n{all_requirements}\n\n"
    f"Changed files (cumulative from {BASELINE_COMMIT}):\n{all_changed_files}\n\n"
    f"Commit history:\n{commit_log}\n\n"
    f"Comprehensive checklist:\n"
    f"1. All plan requirements implemented and verified\n"
    f"2. Cross-PHASE integration (interface mismatches, missing connections)\n"
    f"3. Architecture consistency\n"
    f"4. Security vulnerabilities (OWASP Top 10)\n"
    f"5. Performance (N+1 queries, re-renders, missing indexes)\n"
    f"6. Full test coverage\n"
    f"7. Project convention final check\n\n"
    f"If issues: list with severity (CRITICAL/HIGH/MEDIUM/LOW) and file:line.\n"
    f"If clean: return 'LGTM - full plan completion approved'."
)
```

### Step 3.3: Final Feedback Fix Loop

Same feedback fix loop as Section 4 (max 2 retries).

### Step 3.4: Final Report

```
[check-codex] Full plan comprehensive review complete
- Plan: {plan_path}
- PHASEs: {TOTAL} completed
- Final review result: {LGTM | Fixed | Escalated}
- Total codex reviews: {total_review_count}
- Total feedback fixes: {total_fix_count}
```

---

## 4. Feedback Fix Loop (Shared)

Used by Sections 2.A, 2.B, and 3 when codex review returns actionable feedback.

```python
MAX_RETRIES = 2
retry_count = 0

while has_feedback(codex_result) and retry_count < MAX_RETRIES:
    retry_count += 1

    # Send feedback to dev-executor for fixes
    fix_agent = Agent(
        subagent_type="dev-executor",
        prompt=f"Fix issues found by codex review "
               f"(attempt {retry_count}/{MAX_RETRIES}):\n\n"
               f"{codex_result.feedback}\n\n"
               f"Minimize change scope. Fix only the specific items flagged.",
        run_in_background=True
    )
    # Wait for fix completion

    # Re-verify with the SAME codex skill that found the issue
    # (codex-review for document issues, codex:rescue for code issues)
    codex_result = re_invoke_codex(
        f"Re-verification after feedback fix "
        f"(attempt {retry_count + 1}/{MAX_RETRIES + 1}).\n\n"
        f"Previous feedback:\n{previous_feedback}\n\n"
        f"Verify all previous issues are resolved."
    )

if has_feedback(codex_result) and retry_count >= MAX_RETRIES:
    # Escalate to user
    AskUserQuestion(
        question=f"[check-codex] Codex review has unresolved issues after {MAX_RETRIES} retries. "
                 f"How to proceed?",
        options=[
            {"label": "Continue anyway", "description": "Log remaining issues and proceed"},
            {"label": "Fix manually", "description": "Pause for manual fix, then re-verify"}
        ]
    )
```

---

## 5. Decision Criteria

### has_feedback() Evaluation

| Response Pattern | Verdict | Action |
|-----------------|---------|--------|
| "LGTM", "no issues", "approved" | No feedback | Proceed to next step |
| Specific file/line fix suggestions | Has feedback | Enter fix loop |
| Optional improvement suggestions | Needs triage | Fix CRITICAL/HIGH only, log MEDIUM/LOW |

### Severity-Based Handling

| Severity | Action |
|----------|--------|
| CRITICAL | Must fix -- blocks progression (security, data loss) |
| HIGH | Must fix -- blocks progression (bugs, functional errors) |
| MEDIUM | Log only, recommended but proceed |
| LOW | Log only, proceed |

---

## 6. Legacy Manual Usage Only

> **NOTE**: wm 자동 연동은 `review-orchestrator` agent로 이관되었습니다. 이 섹션은 수동 `/check-codex` 호출의 레거시 호환성을 위해서만 유지됩니다. 새로운 plan에서는 wm 기본 플로우를 사용하세요.

수동으로 `/check-codex`를 직접 호출하는 경우에만 아래 흐름이 적용됩니다.

```
User: /check-codex .claude/plans/my-feature.md
-> Initialization (parse PHASEs, record baseline commit)

Manual invocation flow:

  After design doc is ready:
  -> [check-codex] codex-review on design doc
     -> fix loop if CRITICAL (max 2)

  After tasks doc is ready:
  -> [check-codex] codex-review on tasks doc
     -> fix loop if CRITICAL (max 2)

  After each dev-executor PHASE completes:
    PHASE N:
      -> [check-codex] codex:rescue code review (cumulative diff)
         -> fix loop if CRITICAL/HIGH (max 2)

  Final (after all PHASEs):
  -> [check-codex] codex:rescue comprehensive review (full cumulative diff)
     -> fix loop if CRITICAL/HIGH (max 2)
  -> Completion report
```

새 호출자는 이 skill 대신 `review-orchestrator` agent(`.claude/agents/review-orchestrator.md`)를 참조하세요.

---

## 7. Constraints

| Rule | Description |
|------|-------------|
| Code changes via dev-executor only | check-codex never modifies code directly. All fixes go through dev-executor Agent |
| Max 2 retries | Per review point: feedback fix + re-verify max 2 times |
| Mandatory escalation | After 2 retries with remaining issues, must escalate to user via AskUserQuestion |
| Cumulative diff scope | Code review scope is always cumulative from baseline commit |
| MEDIUM/LOW skip | Severity MEDIUM and below: log only, do not block progression |
| QA skip | No codex review after qa -- qa agent's own validation is sufficient |
| Same skill re-verify | Re-verification uses the same codex skill that found the issue |

---

## 8. Model Reference

Both codex skills use the Codex CLI system default from `~/.codex/config.toml`:

```toml
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
```

| Skill | Invocation | Model | Purpose |
|-------|-----------|-------|---------|
| `codex-review` | `Skill(skill="codex-review", args="--file {path}")` | gpt-5.4 (CLI default) | Document validation (PRD, DESIGN, TASKS) |
| `codex:rescue` | `Skill(skill="codex:rescue", args="...")` | gpt-5.4 (CLI default) | Code review, diagnosis, implementation |

Note: `codex-review`'s SKILL.md mentions "o4" in its description text, but the actual `codex exec` command does not pass `--model`, so it uses the CLI default (gpt-5.4). To explicitly override, add `--model gpt-5.4` to the codex exec command in the codex-review skill.
