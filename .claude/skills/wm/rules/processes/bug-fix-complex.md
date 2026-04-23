# BUG_FIX (Complex) Process

Process to follow for complex bug fixes.

---

## Plan Template (Copy to Plan Document)

Copy this entire block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **BUG_FIX (Complex)** type.

**Execute via Task tool with the following Agents** (in order):

- [ ] 1. `root-cause-finder` → Root cause identification with 5 Whys analysis
- [ ] 2. `bug-fixer` → TDD-style fix (regression test first, with build-error-resolver fallback)
- [ ] 3. Review Gate → `review-orchestrator` single call (qa always; security-reviewer conditional; feedback fix loop internal)
  - verdict LGTM / FIX_APPLIED → proceed
  - verdict ESCALATE → report unresolved issues to user
- [ ] 3.x. Knowledge Recording → `knowledge-keeper` (only when verdict != ESCALATE)
- [ ] 4. Cleanup (invoke plan-cleanup skill)

Step 1 (root-cause-finder): Analysis only - no code changes.
Step 2 (bug-fixer): TDD-style fix with regression test first.
Step 3 (Review Gate): review-orchestrator single sub-agent call. qa always invoked internally; security-reviewer invoked internally when auth/payment/tenant changes detected; QA feedback fix loop handled internally (max 2 retries).
Step 3.x (Knowledge Recording): knowledge-keeper runs after verdict != ESCALATE, before Cleanup.
Step 4 (Cleanup): Only after successful verification.

### Agents Used

| Agent | Purpose | Background | Condition |
|-------|---------|------------|-----------|
| `root-cause-finder` | 5 Whys root cause analysis | Yes | Always |
| `bug-fixer` | TDD-style bug fix | Yes | Always |
| `build-error-resolver` | Build error resolution | Yes | On build failure |
| `review-orchestrator` | Review Gate — single entry point for all review concerns | Yes | Always (Step 3) |
| `qa` | Full test verification | Yes | Invoked internally by review-orchestrator |
| `codex:rescue` | Code review via codex plugin (`Skill("codex:rescue", ...)` with Bash fallback + plugin-unavailable graceful degradation) | Yes (plugin) | Invoked internally by review-orchestrator on fix-branch changes |
| `security-reviewer` | Security audit | Yes | Invoked internally by review-orchestrator; conditional on auth/payment/tenant changes |
| `performance-optimizer` | Performance analysis | Yes | Invoked internally by review-orchestrator; conditional |
| `knowledge-keeper` | Document resolution pattern | Yes | Post-review (Step 3.x, after verdict != ESCALATE) |

> **⛔ EXECUTION GUIDE**: wm injects this template during Step 4 (Plan Writing), then reads this process file during Step 6 (Execution) for the **Agent Invocation Pattern**. This plan has WHAT to do (checkboxes above); the process file has HOW to do it (Task/Skill call patterns).
> Process file: `rules/processes/bug-fix-complex.md`

## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| root-cause-finder | - | pending | - | 5 Whys analysis |
| bug-fixer | - | pending | - | TDD-style fix |
| build-error-resolver | - | pending | - | Build error resolution (on failure) |
| review-orchestrator | - | pending | - | Review Gate (qa + security + fix loop internally) |
| knowledge-keeper | - | pending | - | Document resolution (post-review) |

### Quality Gate Checklist (CRITICAL)

Before completion, verify:

- [ ] **Build/Compile success**: No build errors
- [ ] **Existing tests pass**: All existing tests Pass
- [ ] **Regression test added**: Test to prevent bug recurrence
- [ ] **Lint/Type-check pass**: Code style and type checks Pass
- [ ] **Bug verification**: Original bug is fixed
- [ ] **No side effects**: No impact on existing features

---

### ⛔ Agent Invocation Rules (CRITICAL - MUST READ)

> **VIOLATION WARNING**:
> - Direct Edit/Write without Agent = **PROCESS VIOLATION**
> - Skipping Agent call = **PROCESS VIOLATION**

**All code changes MUST go through Agents. Main Context (wm) NEVER uses Edit/Write directly.**

### Agent Invocation Pattern (MANDATORY)

```python
# Step 0: Load Deferred Tools (CRITICAL - FIRST ACTION)
# Task tools are deferred tools and must be loaded via ToolSearch.
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")

# [GAP-5a] root-cause-finder 선행 graphify blast (5 Whys Step 3-4 보강)
# 버그 증상에 등장하는 심볼/URL의 blast-radius를 사전 수집하여 전파 범위 분석을 강화.
# 사전 미상이면 skip (root-cause-finder가 자체 분석).
GLOBAL_GRAPH="$CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json"
rca_blast_hint = ""
if bug_has_symbol_or_url and Bash(f"test -f {GLOBAL_GRAPH} && echo OK"):
    rca_blast_hint = Bash(
        f"$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify blast "
        f"<bug-symbol-id> --edges calls --json --graph {GLOBAL_GRAPH} "
        f"| jq '.nodes | map(.source_file) | unique' 2>/dev/null || echo '[]'"
    )

# Step 1: root-cause-finder (Analysis only - no code changes)
agent1 = Agent(
    subagent_type="root-cause-finder",
    prompt=f"Plan path: {plan_path}\nBug description: ...\n"
           + (f"[GAP-5a] 사전 blast-radius (전파 영향 파일):\n{rca_blast_hint}\n"
              f"이 영향 범위를 5 Whys의 Step 3-4 (원인의 실제 전파 경로) 분석에 활용하라.\n"
              if rca_blast_hint else "")
           + f"Perform 5 Whys analysis...",
    run_in_background=True
)
# Log agentId, wait for completion

# Step 2: bug-fixer (TDD-style fix)
# [GAP-5b] bug-fixer는 수정 대상 함수의 graphify callers를 확인하여 회귀 테스트 경계를 자동 제안
fixer_callers_hint = ""
if bug_has_target_function and Bash(f"test -f {GLOBAL_GRAPH} && echo OK"):
    fixer_callers_hint = Bash(
        f"$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify callers "
        f"<target-fn-id> --edges calls,calls_http --max-hops 3 --json "
        f"--graph {GLOBAL_GRAPH} | jq '.nodes | map(.source_file) | unique' 2>/dev/null "
        f"|| echo '[]'"
    )

agent2 = Agent(
    subagent_type="bug-fixer",
    prompt=f"Plan path: {plan_path}\nRoot cause: ...\n"
           + (f"[GAP-5b] 수정 대상 함수의 callers (회귀 테스트 경계):\n{fixer_callers_hint}\n"
              f"위 호출자 파일의 기존 테스트가 여전히 통과하는지 반드시 검증하라.\n"
              if fixer_callers_hint else "")
           + f"Write regression test first, then fix.\n"
             f"TDD 사이클(Red->Green->Refactor)을 따르라. 서비스별 테스트 인프라는 best-practices/rules/test-infrastructure.md 참조.\n"
             f"실패 시 self-recovery protocol (progress-tracking.md 3.6)을 따르라.",
    run_in_background=True
)
# Log agentId, wait for completion
# ⚠️ BUILD ERROR: bug-fixer가 빌드 에러로 실패 시
#    → build-error-resolver 자동 호출 → bug-fixer 재실행

# Step 3: Review Gate — review-orchestrator single call
# CRITICAL: security=True is always set for bug fixes (auth/payment/tenant drift possible).
# performance trigger is conditional on the nature of the fix.
FALLBACK_VERDICT = {
    "verdict": "ESCALATE",
    "reason": "stalled",          # one of: stalled | malformed_json | timeout | agent_killed
    "plan_path": plan_path,
    "qa": "SKIP",
    "security": "SKIP",
    "performance": "SKIP",
    "ui": {"status": "SKIP"},
    "unresolved_issues": [{
        "severity": "HIGH",
        "file": "<orchestrator>",
        "line": 0,
        "category": "standards",
        "summary": "review-orchestrator did not return a valid verdict JSON"
    }],
    "next_action": "escalate_to_user"
}

ro = Agent(
    subagent_type="review-orchestrator",
    model="opus",
    prompt=json.dumps({
        "plan_path": plan_path,
        "phase": 1,
        "total_phases": 1,
        "baseline_commit": BASELINE_COMMIT,
        "scope": "final",
        "triggers": {
            "security": True,   # always True for bug fixes — RBAC/contract drift possible
            "performance": changes_involve_performance_sensitive_code,
            "ui": False,
            "docs": False
        }
    }),
    run_in_background=True
)
# CRITICAL: timeout=900000ms (orchestrator 내부 sub-agent 600s + synthesis + fix loop)
raw = TaskOutput(task_id=ro.agent_id, block=True, timeout=900000)

try:
    verdict = json.loads(extract_last_json_block(raw))
    if "verdict" not in verdict:
        raise ValueError("verdict field missing")
except (JSONDecodeError, ValueError):
    FALLBACK_VERDICT["reason"] = "malformed_json"
    verdict = FALLBACK_VERDICT

# Step 3.x: Knowledge Recording (only when verdict != ESCALATE)
if verdict["verdict"] in ("LGTM", "FIX_APPLIED"):
    kb_agent = Agent(
        subagent_type="knowledge-keeper",
        prompt=f"Plan path: {plan_path}\nDocument bug resolution pattern. "
               f"Review verdict: {verdict['verdict']}. "
               f"Record root cause, fix approach, and regression test strategy.",
        run_in_background=True
    )
    TaskOutput(task_id=kb_agent.agent_id, block=True)
elif verdict["verdict"] == "ESCALATE":
    report_to_user(
        f"Review Orchestrator ESCALATE:\n"
        f"- qa={verdict.get('qa')} security={verdict.get('security')} "
        f"perf={verdict.get('performance')} ui={verdict.get('ui', {}).get('status')}\n"
        f"- unresolved: {verdict.get('unresolved_issues', [])}"
    )
    # 사용자 결정 대기 — Step 4 Cleanup 진행하지 않음

# Step 4: Cleanup (AFTER successful verification, verdict != ESCALATE)
if verdict["verdict"] in ("LGTM", "FIX_APPLIED"):
    Skill(skill="plan-cleanup", args=f"{plan_name}")
```

---

## When to Use

Use this process when:

| Condition | This Process | Alternative |
|-----------|--------------|-------------|
| Cause unclear, analysis needed | ✅ Complex | - |
| Modifications across multiple files | ✅ Complex | - |
| Reproduction is difficult/intermittent | ✅ Complex | - |
| Potential for widespread impact | ✅ Complex | - |
| Cause is clear, single file fix | - | Simple |
| E2E/UI/browser related | - | E2E/Frontend |

**Detection priority** (from SKILL.md):
1. E2E/Frontend keyword → `bug-fix-e2e.md`
2. Simple criteria met → `bug-fix-simple.md`
3. All other cases → `bug-fix-complex.md` (this process)

---

## Agent Roles

| Agent | Role | Output |
|-------|------|--------|
| `root-cause-finder` | 5 Whys analysis, root cause identification | Root cause analysis document |
| `bug-fixer` | TDD-style fix (regression test first) | Fixed code + tests |
| `qa` | Full test verification | QA report |
| `knowledge-keeper` | Document resolution pattern | Knowledge document |

---

## 5 Whys Analysis Example

```
Problem: Session not maintained after login
Why 1: Cookie not being set
Why 2: Set-Cookie header missing from response
Why 3: Cookie setting code missing in auth middleware
Why 4: Accidentally deleted during refactoring
Why 5: Not caught in code review

Root cause: Cookie setting code was deleted during refactoring
```

---

## TDD-Style Fix

1. **RED**: Write test that reproduces the bug first
2. **GREEN**: Minimal fix to pass the test
3. **REFACTOR**: Clean up code

---

## Notes

1. **Root cause identification required**: Don't just fix symptoms, resolve the cause
2. **Regression test first**: Write tests to prevent bug recurrence
3. **Document knowledge**: Document patterns to prevent similar bugs
4. **Commit**: After completion, commit changes using `commit` skill

---

## Shared Rules

> See [process-base.md](process-base.md) for Agent Execution Guidelines, Agent Invocation Rules, and Plan Cleanup.
