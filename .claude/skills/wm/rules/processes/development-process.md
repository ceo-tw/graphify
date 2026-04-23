# Development Process (NEW_DEVELOPMENT / MODIFICATION)

Unified process for feature development and modification.

---

## Plan Template (Copy to Plan Document)

Copy this entire block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **{NEW_DEVELOPMENT|MODIFICATION}** type.

**Execute via Task tool with the following Agents** (in order):

- [ ] 1. `design` → Architecture design {+ impact analysis for MODIFICATION}
- [ ] 2. `planner-task` → Task decomposition (includes self-validation)
- [ ] 3. `dev-executor` → Implementation (with build-error-resolver fallback)
- [ ] 4. Review Gate → `review-orchestrator` (single sub-agent call)
  - qa, security-reviewer, performance-optimizer: invoked internally by review-orchestrator
  - Verdict: LGTM → proceed | FIX_APPLIED → proceed with log | ESCALATE → AskUserQuestion
- [ ] 5. Post-QA (CONDITIONAL):
  - [ ] 5a. `/confluence-update` skill → Confluence doc update [MANUAL: user invocation]
- [ ] 6. Cleanup (invoke plan-cleanup skill)

Steps 1-2 proceed sequentially (output dependencies).
Step 3 (dev-executor): **Parallel execution REQUIRED** for independent TASKs.
Step 4 (Review Gate): review-orchestrator single sub-agent call (timeout=900000ms). qa, security-reviewer, performance-optimizer are invoked internally. QA Feedback Loop (max 2 retries, 900s each) is handled internally by review-orchestrator Step 7.
Step 5 (Post-QA): conditional, non-blocking.
Step 6 (Cleanup): Only after successful verification.

> **⚠️ REQUIRED**: Follow [Parallel Execution Pattern](../policies/pattern-parallel-execution.md)

### Task Tool Checklist (Consider at each stage)

**Planning stage (Steps 1-3.1)**
- [ ] Can independent PHASEs be decomposed in parallel?
- [ ] Are design areas independent enough for parallel analysis?
- [ ] Can Explore agents be run in parallel?
- [ ] Can documents be created/modified in parallel?

**Implementation stage (Step 5)**
- [ ] Can independent TASKs be executed in parallel? **(REQUIRED)**

**Verification stage (Steps 6-7)**
- [ ] Can QA and knowledge-keeper be run in parallel? **(REQUIRED)**

**For YES items in the checklist above** → Use [TaskList-based parallel execution pattern](../policies/pattern-parallel-execution.md)

> **Reference**: [Task Tool Planning Guide](../components/task-tool-planning-guide.md) - Detailed guide for Task tool usage during planning stages

### Agents Used

| Agent | Purpose | Background | Condition |
|-------|---------|------------|-----------|
| `design` | Architecture design, ERD | Yes | Always |
| `planner-task` | Task decomposition + self-validation | Yes | Always |
| `dev-executor` | Implementation | Yes | Always |
| `build-error-resolver` | Build error resolution | Yes | On build failure |
| `review-orchestrator` | Review Gate — single sub-agent, returns JSON verdict | Yes | Always (Step 4) |
| `qa` | Testing and verification (invoked internally by review-orchestrator) | Yes | Always |
| `codex:rescue` | Code review via codex plugin (invoked internally by review-orchestrator; `Skill("codex:rescue", ...)` with Bash fallback + `skipped=true, skip_reason="plugin_not_installed"` detection) | Yes (plugin) | Always (code changes) |
| `security-reviewer` | Security audit (invoked internally by review-orchestrator) | Yes | Auth/payment/tenant changes |
| `performance-optimizer` | Performance analysis (invoked internally by review-orchestrator) | Yes | Perf-sensitive changes |
| `/confluence-update` skill | Confluence doc update | Manual | User invocation |

> **⛔ EXECUTION GUIDE**: wm injects this template during Step 4 (Plan Writing), then reads this process file during Step 6 (Execution) for the **Agent Invocation Pattern**. This plan has WHAT to do (checkboxes above); the process file has HOW to do it (Task/Skill call patterns).
> Process file: `rules/processes/development-process.md`

## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| design | - | pending | - | Architecture design |
| planner-task | - | pending | - | Task decomposition + self-validation |
| dev-executor | - | pending | - | Implementation |
| build-error-resolver | - | pending | - | Build error resolution (on failure) |
| review-orchestrator | - | pending | - | Review Gate (returns JSON verdict; qa/security/perf invoked internally) |

### Quality Gate Checklist (CRITICAL)

Before completion, verify:

- [ ] **Build/Compile success**: No build errors
- [ ] **Existing tests pass**: All existing tests Pass
- [ ] **New tests added**: Tests included for new features
- [ ] **Lint/Type-check pass**: Code style and type checks Pass
- [ ] **Feature verification**: Works as specified in requirements
- [ ] **Regression test**: No impact on existing features

---

### ⛔ Agent Invocation Rules (CRITICAL - MUST READ)

> **VIOLATION WARNING**:
> - Direct Edit/Write without Agent = **PROCESS VIOLATION**
> - Sequential execution of independent tasks = **PROCESS VIOLATION**
> - Skipping Agent call = **PROCESS VIOLATION**

**All code changes MUST go through Agents. Main Context (wm) NEVER uses Edit/Write directly.**

### EXECUTION INVARIANTS (MUST - Applies to all development tasks)

| # | Rule | Description | Violation |
|---|------|-------------|-----------|
| 1 | **dev-executor MUST** | All code changes must go through `dev-executor`. Direct Edit/Write calls from Main Context are **strictly prohibited**. | **PROCESS VIOLATION** |
| 2 | **Parallel Review MUST** | Before running `dev-executor`, you must analyze TASK dependencies and execute independent TASKs in parallel. Sequential execution of independent TASKs is **strictly prohibited**. | **PROCESS VIOLATION** |

> **Verification method**: Before Step 5 execution, query all TASKs with `TaskList()`, analyze `blockedBy` relationships to identify groups that can run concurrently. If 2 or more independent TASKs exist, they must be executed in parallel with `run_in_background=True`.

> **NOTE (Worktree temporarily disabled)**: Do not use the `isolation="worktree"` option until a conflict prevention strategy is established.

### Agent Invocation Pattern (MANDATORY) — v2

```python
# Step 0: Load Deferred Tools (CRITICAL - FIRST ACTION)
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")

# ──────────────────────────────────────────────────────────
# Steps 1-2: Sequential (output dependencies)
# ──────────────────────────────────────────────────────────

# [A-2] Step 0.5: knowledge-graph-navigator 선행 호출 (MODIFICATION 타입 전용)
# 목적: design이 실제 blast-radius·god-node·manifest refs·violations를 사전 수신
# 제약: (1) 60초 타임아웃, (2) navigator는 read-only JSON 반환, (3) build-summary.json 미존재 시 skip
# CAVEAT: TaskOutput 은 free-text 반환. navigator에게 "반드시 ```json fenced code block"으로 JSON을 감싸 반환"을 강제.
#         파싱 실패 시 free-text 그대로 design에 주입 (fail-safe).
nav_json_block = ""
if plan_type == "MODIFICATION":
    preflight = Bash(
        "test -f $CLAUDE_PROJECT_DIR/.claude/architecture/graph/build-summary.json "
        "&& echo READY || echo NOT_BUILT"
    )
    if "READY" in preflight:
        nav_agent = Agent(
            subagent_type="knowledge-graph-navigator",
            model="sonnet",
            prompt=(
                f"Plan path: {plan_path}\n"
                f"이 계획에 영향 받는 도메인·god-node·blast-radius·manifest refs·violations를 "
                f"JSON으로 반환하라. 반드시 마크다운 ```json fenced code block으로 감싸서 출력할 것. "
                f"스키마: {{coordinates, blast_radius, god_nodes_involved, manifest_refs, "
                f"violations, recommendations, limitations}}. "
                f"코드 수정·manifest 수정·커밋 금지."
            ),
            run_in_background=True
        )
        TaskOutput(task_id=nav_agent.agent_id, block=True, timeout=60000)
        nav_raw = get_agent_output(nav_agent)
        # JSON fenced block 추출 시도; 실패 시 raw 텍스트 주입
        nav_json_block = extract_fenced_json_or_raw(nav_raw)

# Step 1: design
agent1 = Agent(
    subagent_type="design",
    model="opus",
    prompt=f"Plan path: {plan_path}\nCreate architecture...\n"
           + (f"[A-2] 사전 blast-radius 분석 (knowledge-graph-navigator):\n{nav_json_block}\n"
              f"위 결과의 god_nodes_involved·blast_radius·manifest_refs·violations를 설계의 "
              f"Type Design Checklist 및 cross-service 영향 평가에 반드시 반영하라.\n"
              if nav_json_block else "")
           + f"Context7 MCP가 사용 가능하면 최신 API 문서를 확인하라. 불가능하면 training knowledge를 활용하라.\n"
             f"API 설계 시 stack-conventions.md의 API 패턴을 따르라.",
    run_in_background=True
)
# Log agentId to Agent Execution Log table, wait for completion

# Step 1.5: Type design checks are now integrated into design agent's Type Design Checklist

# Step 2: planner-task (includes self-validation)
# [A-3] navigator 결과(nav_json_block)의 blast_radius·god_nodes_involved를 PHASE blockedBy 제안에 활용
# 실제 node id 사전 미상이면 자동 skip (fail-safe) — PHASE 제목 포함 심볼만 graphify blast 시도
agent2 = Agent(
    subagent_type="planner-task",
    model="opus",
    prompt=f"Plan path: {plan_path}\nCreate task breakdown...\n"
           + (f"[A-3] navigator blast-radius 사전 분석:\n{nav_json_block}\n"
              f"공통 downstream 노드를 공유하는 PHASE는 Task blockedBy 로 제안하라.\n"
              f"Clean Architecture 순서를 naming이 아니라 실제 directed edge 교집합으로 검증하라.\n"
              if nav_json_block else ""),
    run_in_background=True
)
# Log agentId, wait for completion

# Step 2.5: Test strategy analysis is now integrated into planner-task's Check 5 (Self-Validation)

# ──────────────────────────────────────────────────────────
# Step 3: dev-executor (PARALLEL REQUIRED for independent TASKs)
# ──────────────────────────────────────────────────────────
executable_tasks = [t for t in TaskList() if is_executable(t)]
agents = []
for task in executable_tasks:
    TaskUpdate(taskId=task.id, status="in_progress")
    agent = Agent(
        subagent_type="dev-executor",
        prompt=f"Task: {task.id}\n{task.description}\n"
               f"TDD 사이클(Red->Green->Refactor)을 따르라. 서비스별 테스트 인프라는 best-practices/rules/test-infrastructure.md 참조.\n"
               f"Context7 MCP가 사용 가능하면 최신 API 문서를 확인하라. 불가능하면 training knowledge를 활용하라.\n"
               f"실패 시 self-recovery protocol (see progress-tracking.md 3.6)을 따르라.",
        run_in_background=True
    )
    agents.append((task.id, agent))
# Wait for all parallel agents
# ⚠️ BUILD ERROR 분기: dev-executor가 tsc/next build 에러로 실패 시
#    → build-error-resolver 자동 호출 → dev-executor 재실행
for task_id, agent in agents:
    result = TaskOutput(task_id=agent.agent_id, block=True)
    if result_has_build_error(result):
        resolver = Agent(
            subagent_type="build-error-resolver",
            model="sonnet",
            prompt=f"Build error in task {task_id}:\n{result.error}\n"
                   f"workspace별 tsconfig, @/ alias 차이를 고려하여 해결하라.",
            run_in_background=True
        )
        TaskOutput(task_id=resolver.agent_id, block=True)
        # dev-executor 재실행
        retry_agent = Agent(
            subagent_type="dev-executor",
            prompt=f"Task: {task_id}\n(빌드 에러 해결 후 재실행)",
            run_in_background=True
        )
        TaskOutput(task_id=retry_agent.agent_id, block=True)

# ──────────────────────────────────────────────────────────
# Step 4: Review Gate (review-orchestrator 단일 호출)
# ──────────────────────────────────────────────────────────
# graphify-matrix-diff (api/rbac/contract) 선행 Bash 호출은 review-orchestrator 내부
# Step 1에서 수행된다. Main context에서는 Bash로 직접 호출하지 않는다.
#
# qa, security-reviewer, performance-optimizer는 review-orchestrator가 내부에서
# 조건부로 호출한다 (Step 5 fan-out). Main은 JSON verdict만 수신한다.
#
# QA Feedback Loop (GAN evaluator, max 2 retries)은 review-orchestrator 내부
# Step 7에서 수행된다. Main 측 loop 로직은 완전히 제거되었다.

ro = Agent(
    subagent_type="review-orchestrator",
    model="opus",
    prompt=json.dumps({
        "plan_path": plan_path,
        "phase": current_phase,
        "total_phases": total_phases,
        "baseline_commit": BASELINE_COMMIT,
        "scope": "phase",            # or "final" — 마지막 PHASE 완료 시
        "triggers": {
            "security": changes_involve_security_sensitive_code,
            "performance": changes_involve_performance_sensitive_code,
            "ui": changes_involve_ui_code,
            "docs": changes_involve_plan_docs
        }
    }),
    run_in_background=True
)

# CRITICAL: timeout은 반드시 900000ms
# (orchestrator 내부 sub-agent 600s + synthesis + fix loop 여유)
raw = TaskOutput(task_id=ro.agent_id, block=True, timeout=900000)

# JSON 파싱 실패 시 fallback ESCALATE (orchestrator가 stalled/killed 된 경우)
FALLBACK_VERDICT = {
    "verdict": "ESCALATE",
    "reason": "stalled",          # one of: stalled | malformed_json | timeout | agent_killed
    "plan_path": plan_path,
    "phase": current_phase,
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

try:
    verdict = json.loads(extract_last_json_block(raw))
    if "verdict" not in verdict:
        raise ValueError("verdict field missing")
except (JSONDecodeError, ValueError):
    FALLBACK_VERDICT["reason"] = "malformed_json"
    verdict = FALLBACK_VERDICT

# 3-way 분기
if verdict["verdict"] in ("LGTM", "FIX_APPLIED"):
    # FIX_APPLIED: review-orchestrator 내부 fix loop가 이미 수정 완료
    # Step 6 Cleanup 진행
    pass
elif verdict["verdict"] == "ESCALATE":
    report_to_user(
        f"Review Orchestrator ESCALATE:\n"
        f"- qa={verdict.get('qa')} security={verdict.get('security')} "
        f"perf={verdict.get('performance')} ui={verdict.get('ui', {}).get('status')}\n"
        f"- unresolved: {verdict.get('unresolved_issues', [])}"
    )
    # 사용자 결정 대기 (AskUserQuestion)

# ──────────────────────────────────────────────────────────
# Step 5: Post-QA (conditional)
# ──────────────────────────────────────────────────────────
# performance-optimizer는 review-orchestrator 내부에서 조건부 호출된다.
# verdict의 performance 필드("PASS" | "ADVISORY" | "SKIP")로 결과를 확인한다.
# 수동 직접 호출이 필요한 예외 케이스(예: 독립 성능 프로파일링 세션)는
# 사용자가 별도로 /wm performance-deep-dive 를 호출한다.

# 5a: Confluence doc updates → /confluence-update skill (manual user invocation)

# ──────────────────────────────────────────────────────────
# Step 6: Cleanup (AFTER successful verification)
# ──────────────────────────────────────────────────────────
# [C-1] QA 통과 후 변경 도메인만 증분 그래프 업데이트 (LLM 비용 0 — 코드 파일만 재추출)
# Pass 3 semantic extraction은 기본 OFF. docs/ADR 변경 시는 수동 `graphify add` 필요.
# git post-commit hook이 더 자연스러우므로 optional — 생략 시 다음 세션에서 한 번만 수동 실행.
for domain in affected_domains:
    Bash(
        f"cd $CLAUDE_PROJECT_DIR/.claude/architecture/graph/{domain} 2>/dev/null && "
        f"$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify update corpus 2>&1 | tail -30 "
        f"|| echo '(skip update: domain not found)'"
    )

Skill(skill="plan-cleanup", args=f"{plan_name}")
```

---

## When to Use

| Type | When to Use |
|------|-------------|
| **NEW_DEVELOPMENT** | New feature that doesn't exist in codebase |
| **MODIFICATION** | Changes to existing features, API updates, refactoring |

### Examples

| Request | Type |
|---------|------|
| "Add user authentication" | NEW_DEVELOPMENT |
| "Change login to use OAuth" | MODIFICATION |
| "Refactor database layer" | MODIFICATION |
| "Add new API endpoint" | NEW_DEVELOPMENT |

---

## Agent Roles

| Agent | Base Role | MODIFICATION Additions |
|-------|-----------|------------------------|
| `design` | Architecture design, ERD | + Compatibility review with existing design |
| `planner-task` | Task decomposition, TDD workflow, self-validation | + Include regression test tasks, verify regression test inclusion |
| `dev-executor` | Implementation | + Integration with existing code |
| `qa` | Testing and verification | + **Regression tests required** |

---

## Type-Specific Notes

### NEW_DEVELOPMENT

- Focus on clean architecture and proper abstraction
- No existing constraints to consider

### MODIFICATION

- **Impact analysis required**: Identify effects on other features
- **Consider compatibility**: Maintain existing API/interface compatibility or plan migration
- **Regression tests required**: Verify existing features are not affected

---

## Execution Pattern

```python
# Sequential steps (1-2): Output dependencies
Agent(subagent_type="design", model="opus", prompt="...", run_in_background=True)
# Wait for completion...
Agent(subagent_type="planner-task", model="opus", prompt="...", run_in_background=True)
# Wait for completion... (planner-task includes self-validation)

# Step 3: TaskList-based dev-executor parallel execution
all_tasks = TaskList()

# Filter only Tasks for current feature (identified by metadata.feature)
feature_tasks = [t for t in all_tasks if t.metadata.get("feature") == feature_name]

def is_executable(task):
    """Check if Task is executable (pending + all blockedBy completed)"""
    if task.status != "pending":
        return False
    if not task.blockedBy:
        return True
    # Check all Tasks in blockedBy are completed
    for dep_id in task.blockedBy:
        dep = TaskGet(taskId=dep_id)
        if dep.status != "completed":
            return False
    return True

# Execute in dependency order (loop)
while any(t.status == "pending" for t in feature_tasks):
    executable = [t for t in feature_tasks if is_executable(t)]
    if not executable:
        break  # No more executable Tasks (circular dependency or complete)

    # Parallel execution: run all executable Tasks simultaneously
    agents = []
    for task in executable:
        current = TaskGet(taskId=task.id)          # Staleness prevention: check current state
        if current.status != "pending":
            continue  # Already updated elsewhere
        TaskUpdate(taskId=task.id, status="in_progress")
        agent = Agent(
            subagent_type="dev-executor",
            prompt=f"Execute task: {task.id}\n{task.description}",
            run_in_background=True
        )
        agents.append((task.id, agent))

    # Wait for all parallel executions to complete
    for task_id, agent in agents:
        TaskOutput(task_id=agent.agent_id, block=True, timeout=300000)
        current = TaskGet(taskId=task_id)          # Staleness prevention: recheck before completion
        TaskUpdate(taskId=task_id, status="completed")

    # Refresh feature_tasks state (for next loop iteration)
    feature_tasks = [TaskGet(taskId=t.id) for t in feature_tasks]

# Step 4: QA...

# Step 5: Cleanup (AFTER successful verification)
Skill(skill="plan-cleanup", args=f"{plan_name}")
```

---

## Parallel Execution (MUST)

> **⚠️ REQUIRED**: Follow [Parallel Execution Pattern](../policies/pattern-parallel-execution.md)

Independent TASKs at step 5 (dev-executor) MUST execute in parallel.

### TaskList-Based Parallel Execution

Follow this pattern when executing Step 5:

1. **TaskList() query**: Automatically retrieve Claude Code Task list
2. **Feature filtering**: Filter only current feature Tasks by `metadata.feature`
3. **is_executable() check**: `status == "pending"` AND all `blockedBy` completed
4. **Parallel execution**: Run all executable Tasks simultaneously with `run_in_background=True`
5. **Wait and loop**: After completion, proceed to next executable Task group

### Dependency Handling

| blockedBy state | Action |
|-----------------|--------|
| `[]` (none) | Immediately executable |
| Some pending | Wait for those Tasks to complete |
| All completed | Immediately executable |
| Circular dependency | Pre-validated in planner-task self-validation (should not occur)

---

## Common Rules

1. **TaskList-based parallel execution**: Query `TaskList()` then execute Tasks with `blockedBy == []` in parallel
2. **planner-task self-validation**: planner-task performs PHASE coverage, dependency order, architecture order, domain info checks before returning
3. **Code changes through Agents**: Direct Edit/Write in Main context is prohibited
4. **Task state management**: Set `in_progress` before execution, `completed` after via TaskUpdate
5. **Staleness prevention**: Must call `TaskGet` to check current state before every `TaskUpdate` call

---

## Shared Rules

> See [process-base.md](process-base.md) for Agent Execution Guidelines, Agent Invocation Rules, and Plan Cleanup.
