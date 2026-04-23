# Progress Tracking Rules

> **Core Orchestrator Rules for main context (wm skill)**
>
> main context (wm skill) manages "whether progress is being made correctly", not "what needs to be done".
> Each agent knows how to execute its specific tasks.

---

## 1. Checkbox Update Timing

### 1.1 Status Notation

| Notation | Status | Description |
|----------|--------|-------------|
| `- [ ]` | Pending | Not yet started |
| `- [~]` | In Progress | Agent currently running (optional) |
| `- [x]` | Completed | Successfully finished |
| `- [!]` | Failed | Failed or aborted |
| `- [-]` | Deleted | Task permanently removed (partial_fix, intent abandoned, cleanup) |

### 1.2 Update Rules

```
Before start  → - [ ]  (maintain default state)
During run    → - [~]  (optional, recommended for background agents)
After done    → - [x]  (only after verifying results!)
On failure    → - [!]  (record failure reason)
On deletion   → - [-]  (record deletion reason, e.g., "partial_fix", "intent abandoned")
```

**Core Principle**: Update checkbox **only after** confirming agent completion

---

## 2. Background Agent Completion Verification

### 2.1 Basic Pattern

```markdown
## Background Agent Execution and Verification Procedure

### Step 1: Execute Agent
Task(
  subagent_type="design",
  prompt="...",
  run_in_background=True
)
→ Result: agent_id, output_file returned

### Step 2: Wait and Verify Completion
Method A: TaskOutput(task_id=agent_id, block=True, timeout=300000)
Method B: Read(output_file) with repeated checks

### Step 3: Validate Results
- Check for completion signals ("completed", "done") in agent output
- Verify artifact files exist
- Check for error messages

### Step 4: Update Checkbox
On success: Edit(plan_file, old="- [ ] 1.", new="- [x] 1.")
On failure: Edit(plan_file, old="- [ ] 1.", new="- [!] 1. (failure reason)")
```

### 2.2 Parallel Agent Execution (MUST When Independent)

> **⚠️ REQUIRED**: Follow [Parallel Execution Pattern](../policies/pattern-parallel-execution.md)

Independent agents MUST run in parallel. Sequential execution of independent work is a process violation.

```markdown
## Tracking Parallel Execution

1. Start all agents
   - Agent A → task_id_a
   - Agent B → task_id_b

2. Check completion for each
   - TaskOutput(task_id=task_id_a, block=False) → check status
   - TaskOutput(task_id=task_id_b, block=False) → check status

3. Proceed when all complete
   - If any fails → apply failure handling rules
```

---

## 3. Failure Handling Rules

### 3.1 Retry Policy

| Failure Type | Retry | Max Attempts | Follow-up |
|-------------|-------|--------------|-----------|
| Transient errors (timeout, etc.) | Yes | 3 | Report to user |
| Validation failure (QA, etc.) | Yes | 2 | Retry with feedback |
| HARD GATE failure | No | - | Stop immediately, user decision |
| Resource exhaustion | No | - | Request user resolution |

### 3.2 Failure Type Classification Table

| Failure Type | Trigger Conditions | Action | Max Retries |
|-------------|-------------------|--------|-------------|
| **Transient** | Timeout, network error, MCP connection failure | Auto-retry with backoff | 3 |
| **Build Error** | tsc error, next build failure, workspace dependency issue | Route to `build-error-resolver` agent | 2 |
| **QA Validation** | Test failures, code quality violations, coverage < 80% | QA feedback loop: re-invoke `dev-executor` with `actionable_issues` | 2 |
| **Security** | `security-reviewer` finds CRITICAL issues | Route back to `dev-executor` with security fix instructions | 1 |
| **HARD GATE** | Authentication bypass detected, tenant isolation broken, secrets in code | Stop immediately, user decision required | 0 |
| **Resource Exhaustion** | Context overflow, token limit, agent stuck in loop | Apply self-recovery protocol (see 3.6 below), then escalate | 1 |

### 3.3 Failure Record Format

```markdown
- [!] 3. `qa` → QA validation
  - Failed at: 2024-01-24 14:30
  - Reason: 3 tests failed (auth.test.ts)
  - Retries: 1/2 completed
  - Status: Awaiting retry
  - Actionable issues: [see qa output JSON]
```

### 3.4 QA Feedback Loop Tracking

Track QA retries explicitly in the Agent Execution Log:

```markdown
| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| qa (attempt 1) | abc123 | failed | 14:30 | Initial verification |
| dev-executor (fix) | def456 | completed | 14:35 | Fix actionable_issues from qa |
| qa (attempt 2) | ghi789 | completed | 14:40 | Re-verification after fix |
```

**Loop-operator safety rules apply**:
- Max 2 QA retries (3 total attempts)
- Stall detection: if >80% of issues overlap between attempts → escalate
- Scope reduction after first retry: focus on CRITICAL issues only

### 3.5 Loop Safety Rules (from loop-operator)

These rules apply to all retry loops (QA feedback, build error, agent failure):

| Rule | Trigger | Action |
|------|---------|--------|
| **Max Retry** | QA: 2 retries, Build: 2, Agent: 3 | Escalate to user |
| **Stall Detection** | >80% issue overlap in N=2 consecutive attempts | Pause + shrink scope; N=3 -> escalate |
| **Retry Storm** | >5 invocations in 60 seconds | Pause 10s, then escalate |
| **Scope Reduction** | After first retry fails | Focus on CRITICAL issues only, skip WARNING/INFO |
| **Cost Guard** | >20 total agent invocations | Warn; >30 -> escalate with summary |

### 3.6 Agent Self-Recovery Protocol (from agent-introspection-debugging)

When an agent encounters failure, it follows this 4-phase protocol:

1. **CAPTURE**: Record what failed, what was expected, how many times, tools used
2. **DIAGNOSE**: Match against 6 known patterns:
   - Infinite Loop: same action 3+ times -> stop, try different angle
   - Context Overflow: truncated results -> shrink scope to 1 file/function
   - Wrong Hypothesis: fix applied but same error -> re-examine assumptions
   - Connection Error: MCP/API failures -> retry once, then use alternatives
   - File Mismatch: edit fails on old_string -> re-read file
   - Build Cascade: fix 1 error, 3 appear -> revert, analyze full error list
3. **RECOVER**: Restate objective -> verify state -> shrink scope -> run 1 check -> retry with adjustment
4. **REPORT**: Generate introspection report (pattern, root cause, recovery action, lessons)

**Escalation**: After 3 failed recovery attempts, scope exceeds capability, ambiguous requirements, or data integrity risk.

### 3.7 HARD GATE Failure

**HARD GATE triggers** (stop immediately, no auto-retry):
- `security-reviewer` reports tenant_id isolation breach
- Hardcoded secrets detected in staged files
- Authentication bypass path found
- Payment flow without idempotency
- Database migration with data loss risk

```markdown
## HARD GATE Failure Handling

1. Stop immediately
2. Report to user:
   - Failed step and agent
   - Failure reason with specific file:line references
   - Severity classification
   - Possible solutions (ranked by safety)
3. Await user decision:
   - Manual resolution and resume
   - Skip this step (with justification)
   - Abort entire process
```

---

## 4. Plan Document Synchronization

### 4.1 Update Timing

| Event | Items to Update |
|-------|-----------------|
| Step start | Status `- [~]` (optional) |
| Step complete | Status `- [x]`, artifact path |
| Step failed | Status `- [!]`, failure reason |
| Tasks deleted | Status `- [-]`, deletion reason, affected task count |
| Process complete | Completion time, final summary |

### 4.2 Artifact Path Recording

```markdown
## Artifact Recording Example

- [x] 1. `design` → Architecture design
  - Artifact: `.claude/plans/{feature-name}-DESIGN.md`

- [x] 2. `planner-task` → Task decomposition + self-validation
  - Artifact: `.claude/plans/{feature-name}-TASKS.md`
```

### 4.3 Agent Execution Log (agentId Tracking)

Every Plan document must include an Agent Execution Log section.
See `SKILL.md` section "6. Execution" for detailed agentId logging pattern.

**Key Points**:
- Extract `agent_id` when `Task()` returns
- Log to Plan document immediately before proceeding
- Update status on completion (`in_progress` → `completed`/`failed`)

**Purpose**: Enables context restoration and agent resume after context compression.

### 4.4 Synchronization Rules

```
Principle: Update plan document **immediately** after each step completes

1. Change checkbox status
2. Add artifact path (if applicable)
3. Add notes/remarks (if needed)
4. Proceed to next step
```

---

## 5. Important Notes

### This IS main context (wm skill)'s responsibility

- Progress tracking and recording
- Agent completion verification
- Plan document synchronization
- Retry/abort decisions on failure

### This is NOT main context (wm skill)'s responsibility

- Detailed execution methods (each agent's responsibility)
- Phase/Task Planning Guide (agents load as skill)
- Quality Gates detailed criteria (QA agent's responsibility)
- Checkpoint save/restore (restore-context skill's responsibility)
