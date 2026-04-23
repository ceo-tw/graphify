---
name: wm
type: workflow
description: "Unified workflow manager. Systematically manages all tasks including development, bug fixes, analysis, and reporting. Use when: (1) starting new feature development, (2) systematically resolving bugs, (3) code analysis or research is needed. Invoke with /wm command."
argument-hint: [task description]
allowed-tools:
  - Agent  # subagent spawn (renamed from Task -> Agent in v2.1.63)
  # AskUserQuestion excluded — including in allowed-tools causes question UI to not display and auto-submit with empty response
  # ExitPlanMode excluded — including in allowed-tools causes approval UI to not display and auto-approve
  - EnterPlanMode  # restored — when /wm is invoked, user has already expressed Plan Mode intent, so no double-confirmation needed
  - Read
  - Write
  - Edit
  - Skill
  # Agent Teams orchestration (used in Section 6 Execution)
  - TeamCreate
  - TeamDelete
  - SendMessage
  # Task management (Agent Teams lead + dev-executor parallel execution)
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
user-invocable: true
hooks:
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "bash \"${CLAUDE_SKILL_DIR}/scripts/wm-track-plan.sh\""
  PreToolUse:
    - matcher: "ExitPlanMode"
      hooks:
        - type: command
          command: "bash \"${CLAUDE_SKILL_DIR}/scripts/wm-plan-gate.sh\""
---

# Workflow Manager (wm)

Simplified planning skill that leverages Plan mode's built-in mechanisms.

> **EXECUTION INVARIANTS** (applies to all development tasks):
> 1. **dev-executor MUST**: All code changes must be performed through `dev-executor`. Direct Edit/Write calls from Main Context are **FORBIDDEN**.
> 2. **Parallel Review MUST**: Before executing `dev-executor`, you must analyze inter-TASK dependencies and execute independent TASKs in parallel.

---

## 0. Plan Mode Entry (CRITICAL)

> **Reference**: [Plan Mode Tools Guide](rules/components/plan-mode-tools-guide.md)

When `/wm` is invoked, **immediately call `EnterPlanMode()`** before any other tool.

**Plan Mode Rules**: Read-only (only plan document writing allowed), Explore agent required for search (direct Glob/Grep forbidden), no execution before approval.

---

## 1. File Exploration Rules (MUST)

> **Full details**: [Exploration Rules](references/exploration-rules.md)

When file exploration is needed, route requests through the **4-tier fallback** below. Reading known file paths with `Read()` is always allowed.

**[A-1] File exploration fallback order** (evaluate top-down; first match wins):

1. **URL / exact-symbol request** → `graphify resolve` / `graphify callees` / `graphify callers` / `graphify blast` on the `_global` directed graph.
   - Triggers: URL prefix (`/portal/*`, `/api/*`), route params (`:id`), identifier tokens (snake_case / PascalCase / camelCase, ≥ 3 chars).
   - Example: "재시작 버튼에서 500 에러" + URL `/portal/agents/:id` → `graphify resolve /portal/agents/:id --json --graph $GLOBAL_GRAPH`.

2. **Natural-language / concept question** → `knowledge-graph-navigator` agent, which delegates to `graphify query` (v0.5.6+).
   - Triggers: wh-markers (`어떻게`, `왜`, `무엇`, `how`, `why`, `what`, `?`); request without exact identifier; ≥ 5-token free-form prose.
   - Example: "현재 graphify 에서 tenant isolation 을 구현하는 함수들은?" → navigator → `graphify query "tenant isolation" --budget 1500 --min-confidence INFERRED --json --graph $GLOBAL_GRAPH`.

3. **Two-node path request** → `knowledge-graph-navigator` agent, which delegates to `graphify path` (v0.5.6+).
   - Triggers: two quoted identifiers; explicit "from X to Y" / "between A and B" / arrow `A -> B`.
   - Example: "billing.service.ts 의 createInvoice 에서 stripe.charges.create 까지 경로" → navigator → `graphify path "createInvoice" "stripe.charges.create" --json`.

4. **Explore agent (fallback)** → `Agent(subagent_type="Explore", model="haiku")`.
   - Triggers: tiers (1)-(3) all return 0 hits; non-code artifact search (docs, config, asset); user explicitly requests broad scan.

**Mixed input**: try (1) first to extract the URL/symbol chain, then (2) to semantically augment with concept matches. Example: `"/portal/agents/172 에서 tenant isolation 구현"` → (1) resolves URL chain, (2) augments with tenant-isolation semantic neighbors.

| Tier | Action | Tool |
|------|--------|------|
| 1 | URL/symbol structural lookup | `Bash("graphify resolve/callees/callers/blast ... --json --graph $GLOBAL_GRAPH")` (read-only; Plan Mode safe) |
| 2 | NL concept question | `Agent(subagent_type="knowledge-graph-navigator")` → wraps `graphify query` |
| 3 | Two-node path | `Agent(subagent_type="knowledge-graph-navigator")` → wraps `graphify path` |
| 4 | Broad search (fallback) | `Agent(subagent_type="Explore", model="haiku")` |
| — | Read known file path | `Read("/path/to/known/file.ts")` |

**Graphify CLI quick reference** (all read-only, no file writes — Plan Mode safe):
```bash
GLOBAL_GRAPH=$CLAUDE_PROJECT_DIR/.claude/architecture/graph/_global/graphify-out/graph.json
GRAPHIFY=$CLAUDE_PROJECT_DIR/.claude/graphify/.venv/bin/graphify

# Tier 1: URL -> FE page + 1-hop neighbors
$GRAPHIFY resolve /portal/agents/:id --json --graph $GLOBAL_GRAPH

# Tier 1: exact id/label from a symbol keyword (fuzzy not supported by resolve)
jq --arg kw "<symbol>" '.nodes[] | select(.label | test($kw; "i")) | {id,label,kind,source_file}' $GLOBAL_GRAPH | head -20

# Tier 1: downstream chain (FE -> API -> handler)
$GRAPHIFY callees <node-id> --edges calls,calls_http,handled_by --max-hops 5 --json --graph $GLOBAL_GRAPH

# Tier 2 (via navigator): NL question -> semantic subgraph (v0.5.6+)
$GRAPHIFY query "tenant isolation" --budget 1500 --min-confidence INFERRED --json --graph $GLOBAL_GRAPH

# Tier 3 (via navigator): shortest path between two symbols (v0.5.6+)
$GRAPHIFY path "createInvoice" "stripe.charges.create" --json --graph $GLOBAL_GRAPH
```

**Fallback rule**: if `callees`/`callers` returns 0 on a Hono route (v0.5.2 §12.3c: anonymous inline handlers not traced), fall back to `Grep` on the namespace.function pattern, or escalate to Tier 2 (`query`) for concept-level hits.

**Precondition**: `test -f $CLAUDE_PROJECT_DIR/.claude/architecture/graph/build-summary.json` — if missing, run `/wm-setup` to install graphify + build graphs. Navigator will emit `warnings: ["graph older than 7d; ..."]` in its JSON response when the `_global` graph mtime exceeds 7 days (`schema_version: "2"`).

---

## 2. Request Type Classification (Enhanced)

> **Full details**: [Type Classification](references/type-classification.md)

Analyze user requests to determine the type. **wm performs all detection directly** (MULTI_INTENT, code file detection included).

| Type | Worktree | Complexity |
|------|----------|------------|
| NEW_DEVELOPMENT | No (temporarily disabled) | Complex |
| MODIFICATION | No (temporarily disabled) | Complex |
| BUG_FIX (Complex/E2E) | No (temporarily disabled) | Complex |
| BUG_FIX (Simple) | No | Simple |
| INQUIRY / REPORT / CLEANUP | No | Simple |
| DOCUMENTATION | No | Simple |
| DOCUMENTATION_BATCH | No | Simple |
| MULTI_INTENT | Depends | Complex |
| RESTORATION | Inherit | - |

### Enhanced Detection (performed directly by wm)

1. **MULTI_INTENT detection**: When requests contain "AND", "also", numbered lists, etc., apply `classify_multi_intent` logic. Classify as MULTI_INTENT when 2+ independent intents are detected.
2. **Code file detection**: If classified as DOCUMENTATION type but plan content references `.ts`, `.tsx`, `.py` etc. code files, suggest reclassification to MODIFICATION (AskUserQuestion).

> **Functions Reference**: [type-classification-functions.md](rules/components/type-classification-functions.md)

---

## 3. Requirements Clarification

If information is insufficient, clarify with `AskUserQuestion`.

| Trigger | Action |
|---------|--------|
| Ambiguous request | Ask for clarification |
| Multiple approaches | Present options |
| Confidence < 95% | Confirm intent |
| Code files in DOCUMENTATION plan | Ask MODIFICATION reclassification |

**Rules**: Mark recommended option with "(recommended)", max 3 attempts. Subagents use `clarification-protocol` skill instead of AskUserQuestion.

> **Templates**: [pattern-clarification.md](rules/policies/pattern-clarification.md)

---

## 4. Plan Writing (with Template Injection)

> **Full details**: [Plan Writing Guide](references/plan-writing-guide.md)

Write the plan document once clarification is complete. Location: `.claude/plans/{feature-name}.md`

**Claude writes (MUST include in order):**

| # | Section | Description |
|---|---------|-------------|
| **0** | **Pre-Execution Required Steps** | MANDATORY (see below for Complex/Simple templates) |
| 1 | Problem Definition | Current state -> Goal |
| 2 | Clarified Requirements | Checkbox list (`- [ ]`), grouped by PHASE (Complex types) |
| 3 | Verification Method | How to verify completion |

### PHASE Structure in Section 2 (Complex types)

For Complex types (NEW_DEVELOPMENT, MODIFICATION), group requirements by PHASE in Section 2.
PHASE decomposition is performed directly by wm during the Plan Writing step.

```markdown
## 2. Clarified Requirements

### PHASE 1: {Core Domain}
- [ ] Requirement A
- [ ] Requirement B

### PHASE 2: {Application Layer}
- [ ] Requirement C (depends: PHASE 1)
- [ ] Requirement D

### PHASE 3: {Presentation / UI}
- [ ] Requirement E (depends: PHASE 2)
```

**PHASE decomposition guidelines**:
- 3-7 PHASEs, each 1-4 hours
- Explicit inter-PHASE dependencies (depends: PHASE N)
- Clean Architecture order recommended (Domain -> Application -> Adapters -> Infrastructure)
- Determine PHASEs after analyzing codebase with Explore agent

### Template Injection (performed directly by wm)

**Complex types** (NEW_DEVELOPMENT, MODIFICATION, BUG_FIX Complex/E2E, MULTI_INTENT):
1. Read the process file for the classified type (see [Process File Mapping](#process-file-mapping))
2. Copy the `## Plan Template` block from the process file into Section 0
3. Include the `## Agent Execution Log` table from the process file
4. For MULTI_INTENT: compose per-intent sections from each intent's process file (see [multi-intent.md](rules/processes/multi-intent.md))

**Simple types** (BUG_FIX Simple, DOCUMENTATION, DOCUMENTATION_BATCH, INQUIRY, REPORT, CLEANUP):
- Include minimal Section 0: `- [ ] execution skip (auto) -- {TYPE} type, {COMPLEXITY} complexity`

### Process File Mapping

| Plan Type | Process File Path |
|-----------|-------------------|
| NEW_DEVELOPMENT | [development-process.md](rules/processes/development-process.md) |
| MODIFICATION | [development-process.md](rules/processes/development-process.md) |
| BUG_FIX (Simple) | [bug-fix-simple.md](rules/processes/bug-fix-simple.md) |
| BUG_FIX (Complex) | [bug-fix-complex.md](rules/processes/bug-fix-complex.md) |
| BUG_FIX (E2E) | [bug-fix-e2e.md](rules/processes/bug-fix-e2e.md) |
| INQUIRY | [inquiry.md](rules/processes/inquiry.md) |
| REPORT | [report.md](rules/processes/report.md) |
| CLEANUP | [cleanup.md](rules/processes/cleanup.md) |
| MULTI_INTENT | (composite - per-intent process files) |

**Writing Order**: Determine type -> Read process file (Complex) -> Write Section 0 first -> Write Sections 1-3 -> Verify Section 0 exists -> Report to user -> ExitPlanMode.

---

## 5. Plan Reporting

Report to user after writing the plan document:
1. **Plan Summary** - What will be done
2. **Execution Process** - In what order
3. **Plan File Path** - Where to check details

Plan mode's built-in approval mechanism activates automatically (Approve/Modify/Cancel).

### plan-exit-gate.sh

ExitPlanMode triggers automatic validation: plans directory, recent plan file (15min), Section 1+2 existence, minimum 2 checkboxes.

### allowed-tools rules

| Tool | Status | Reason |
|------|--------|--------|
| `EnterPlanMode` | Included | No double-confirmation needed |
| `ExitPlanMode` | Excluded | User approval UI must display |
| `AskUserQuestion` | Excluded | User question UI must display |

---

## 6. Execution

> **Full details**: [Execution Guide](references/execution-guide.md)

### Step 0: Load Deferred Tools (CRITICAL - BEFORE any Task tool call)

Task tools (TaskCreate, TaskUpdate, TaskGet, TaskList) are **deferred tools** and must be loaded before execution begins:

```python
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")
```

> **WARNING**: Calling TaskList(), TaskCreate() etc. without this step will fail because the tools are not loaded.
> Even if registered in `allowed-tools`, that only handles **automatic permission approval**; **tool loading** requires ToolSearch.

### Step 1: Load Context (after Tool Loading)

Re-read the plan document and load the process file for the classified type.

```python
# 1. Re-read plan
plan_content = Read(plan_path)

# 2. Compute process file path
process_file_path = "${CLAUDE_SKILL_DIR}/" + process_file

# 3. Read process file (contains Agent Invocation Pattern)
process_content = Read(process_file_path)
```

### Step 2: Execution Mode Branch

After plan approval, branch by complexity: `"agent_teams"` -> Path A, `"task_based"` or null -> Path B (default). PHASE decomposition is performed in Step 4 Plan Writing.

### Step 3: Execution (per process file's Agent Invocation Pattern)

Follow the Agent Invocation Pattern from the process file exactly. See [Execution Guide](references/execution-guide.md) for full Path A (Agent Teams) and Path B (Task-based) procedures.

### Complexity-Based Branching

| Complexity | Flow |
|-----------|------|
| **Complex** | Step 1 (Load Context) -> Step 2 (Execution Mode) -> Step 3 (Execution per process file) |
| **Simple** | Skip to direct execution per process file's simple pattern |

### Execution Rules

| Rule | Description |
|------|-------------|
| Background execution | `run_in_background=True` for long-running agents |
| Code changes | Through Agents only (no direct Edit/Write) |
| Parallel execution | **REQUIRED** for independent agents/tasks |
| agentId logging | Log to Plan document **immediately** after Agent() call, before proceeding |
| Staleness prevention | `TaskGet` before every `TaskUpdate` |
| Deadlock detection | Run `detect_deadlock()` before parallel execution loop (see pattern-parallel-execution.md) |

### Error Handling Rules

| Failure Type | Handler | Max Retries | Escalation |
|-------------|---------|-------------|------------|
| Build error (tsc/next) | `build-error-resolver` agent | 2 | User |
| QA validation failure | QA feedback loop (dev-executor rework) — inside review-orchestrator Step 7 | 2 | User |
| Security CRITICAL | HARD GATE — stop immediately | 0 | User |
| Agent stuck/loop | Self-recovery protocol (see progress-tracking.md 3.6) | 3 | User |
| Transient (timeout/network) | Auto-retry with backoff | 3 | User |
| Review verdict ESCALATE | AskUserQuestion으로 사용자 에스컬레이션 | 0 retries | User decision |

See [Progress Tracking Rules](rules/orchestration/progress-tracking.md) for detailed failure type classification table.

### QA Feedback Loop (GAN Evaluator Pattern)

The QA Feedback Loop is performed **inside review-orchestrator** (Step 7) — Main context does not run this loop directly.

review-orchestrator内 feedback fix loop: max 2 retries, 900s per attempt. After 3 total failures the orchestrator returns `verdict: ESCALATE` with `unresolved_issues` and Main escalates to the user.

### Conditional Agent Invocation

Review agents are invoked via **`review-orchestrator` single sub-agent call** — Main context does not call qa, security-reviewer, or performance-optimizer directly:

| Agent | Condition | Phase |
|-------|-----------|-------|
| `review-orchestrator` | Always — Review Gate entry point | Step 4 (single Agent call, run_in_background=True, timeout 900s) |

Specialists invoked internally by review-orchestrator (not called from Main):
- `qa` — always invoked (Step 5 fan-out, 600s timeout)
- `security-reviewer` — invoked internally if `has_security` trigger is set (auth, payment, tenant, middleware code changed)
- `performance-optimizer` — invoked internally if `has_perf` trigger is set (route handlers, components, DB queries changed)
- `codex:rescue` (code review) — always-on, via review-orchestrator Step 5 | plugin skill — review-orchestrator 내부 fan-out 전용 (독립 호출 지양)

**Integrated into existing agents** (no longer separate invocations):
- Type design checks: `design` agent's Type Design Checklist
- Test strategy analysis: `planner-task` agent's Check 5 (Self-Validation)
- Database/SQL review: `qa` agent's verify_database_rules (Step 3)
- Silent failure detection: `qa` agent's Error Handling section (Step 6)
- Confluence docs: `/confluence-update` skill (manual invocation)
- `review-orchestrator`: qa / security-reviewer / performance-optimizer 3종을 단일 fan-out으로 통합 호출 + Graphify / codex / UI 포함
- `codex:rescue`: review-orchestrator Step 5에서 `Skill("codex:rescue", ...)` 로 내부 호출됨. Main context 또는 다른 agent에서 직접 호출하지 말 것 — review-orchestrator 진입점(`Agent(subagent_type="review-orchestrator", ...)`)을 사용할 것.

---

## 7. Jira Ticket Creation (Post-Approval)

계획 승인 후, 실행 시작 전에 Jira 티켓 생성 여부를 확인한다.

1. `AskUserQuestion`으로 질문: "승인된 계획을 Jira 티켓으로 생성할까요?"
   - 옵션: "생성 (Recommended)", "건너뛰기"
2. 사용자가 "생성"을 선택하면 `/plan-to-jira {plan-file-path}` skill을 호출
3. Jira 생성 완료 후 실행 단계(Section 6)로 진입

> **NOTE**: 사용자가 건너뛰기를 선택하면 바로 실행 단계로 진행한다. 실행 완료 후에도 `/plan-to-jira` 커맨드로 수동 생성할 수 있다.

---

## 8. Completion Report

> **Full details**: [Completion Template](references/completion-template.md)

Write completion report after all work is done.

---

## Reference Materials

### Key References

| Topic | Reference |
|-------|-----------|
| Exploration rules detail | [references/exploration-rules.md](references/exploration-rules.md) |
| Type classification detail | [references/type-classification.md](references/type-classification.md) |
| Plan writing detail | [references/plan-writing-guide.md](references/plan-writing-guide.md) |
| Execution detail | [references/execution-guide.md](references/execution-guide.md) |
| Completion template | [references/completion-template.md](references/completion-template.md) |
| Agent list | [AGENTS.md](../../architecture/AGENTS.md) |

### Orchestration
- [Progress Tracking](rules/orchestration/progress-tracking.md)

### User-Facing Output
- [Emoji Guidelines](rules/policies/pattern-emoji-guidelines.md) - **MUST** follow for Steps 4, 7

### Document Quality
- Document Quality Principles: `.claude/skills/wm/rules/policies/doc-quality-principles.md` (3원칙 + 적용 매트릭스)
