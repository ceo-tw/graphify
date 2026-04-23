# BUG_FIX (E2E/Frontend) Process

Process for frontend/E2E related bug fixes.

---

## Plan Template (Copy to Plan Document)

Copy this entire block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **BUG_FIX (E2E/Frontend)** type.

**Execute via Task tool with the following Agents** (in order):

- [ ] 0. Pre-cleanup: Close browser, clean sessions (`playwright_close()`)
- [ ] 1. `playwright-test-healer` → Diagnose and fix failing tests
- [ ] 2. Run tests: `npx playwright test`
- [ ] 3. If failures persist → `playwright-test-generator` for new tests
- [ ] 4. `qa` → Full verification
- [ ] 5. Post-cleanup: Delete temporary screenshots
- [ ] 6. Cleanup (invoke plan-cleanup skill)

Each step proceeds sequentially after the previous step is completed.

### Agents Used

| Agent | Purpose | Background |
|-------|---------|------------|
| `playwright-test-healer` | Test diagnosis and fix | Yes |
| `playwright-test-generator` | New test generation (if needed) | Yes |
| `qa` | Full verification | Yes |

> **⛔ EXECUTION GUIDE**: wm injects this template during Step 4 (Plan Writing), then reads this process file during Step 6 (Execution) for the **Agent Invocation Pattern**. This plan has WHAT to do (checkboxes above); the process file has HOW to do it (Task/Skill call patterns).
> Process file: `rules/processes/bug-fix-e2e.md`

## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| playwright-test-healer | - | pending | - | Test diagnosis and fix |
| playwright-test-generator | - | pending | - | New test generation |
| qa | - | pending | - | Full verification |

### Quality Gate Checklist (E2E)

Before completion, verify:

- [ ] **All E2E tests pass**: `npx playwright test` succeeds
- [ ] **No browser errors**: Console logs are clean
- [ ] **Screenshots cleaned**: Temporary files removed
- [ ] **Test stability**: No flaky tests introduced

---

### ⛔ Agent Invocation Rules (CRITICAL - MUST READ)

> **VIOLATION WARNING**:
> - Direct Edit/Write without Agent = **PROCESS VIOLATION**
> - Skipping Agent call = **PROCESS VIOLATION**

**All test changes MUST go through Agents. Main Context (wm) NEVER uses Edit/Write directly.**

### Agent Invocation Pattern (MANDATORY)

```python
# Step 0-A: Load Deferred Tools (CRITICAL - FIRST ACTION)
# Task tools are deferred tools and must be loaded via ToolSearch.
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")

# Step 0-B: Pre-cleanup (Main context OK for browser cleanup)
playwright_close()

# Step 1: playwright-test-healer
agent1 = Agent(
    subagent_type="playwright-test-healer",
    prompt=f"Plan path: {plan_path}\nFix E2E test failure:\n1. Run npx playwright test\n2. Analyze failure\n3. Fix test or code\n4. Verify",
    model="sonnet",
    run_in_background=True
)
# Log agentId to Agent Execution Log table above
# Wait for completion with TaskOutput(task_id=agent1.agent_id)

# Step 2: Run tests (Main context OK for bash)
Bash("npx playwright test")

# Step 3: If failures persist - playwright-test-generator
agent3 = Agent(
    subagent_type="playwright-test-generator",
    prompt=f"Plan path: {plan_path}\nGenerate new E2E test:\nTarget: ...\nExpected behavior: ...",
    model="sonnet",
    run_in_background=True
)
# Log agentId, wait for completion

# Step 4: qa
agent4 = Agent(
    subagent_type="qa",
    prompt=f"Plan path: {plan_path}\nVerify E2E tests...",
    run_in_background=True
)
# Log agentId, wait for completion

# Step 5: Post-cleanup (Main context OK)
Bash("rm -rf .playwright-mcp/screenshots/*")

# Step 6: Cleanup
Skill(skill="plan-cleanup", args=f"{plan_name}")
```
```

---

## E2E/Frontend Bug Detection Criteria

### E2E/Frontend (use this process)

- E2E test failures
- UI/screen bugs
- Browser behavior issues
- User flow errors
- Playwright test modifications needed

### Use Other Processes

- API/backend logic bugs → Complex
- Simple text/config errors → Simple

---

## Agent Roles

| Agent | Role | Output |
|-------|------|--------|
| `playwright-test-healer` | Diagnose and fix failing tests | Fixed test files |
| `playwright-test-generator` | Generate new tests (if needed) | New test files |
| `qa` | Full verification | QA report |

---

## Agent Call Patterns

### playwright-test-healer

```python
# Close browser first
playwright_close()

Agent(
    subagent_type="playwright-test-healer",
    prompt="""
    Fix E2E test failure:

    1. Run `npx playwright test` to confirm failures
    2. Analyze failure cause
    3. Fix test or code
    4. Verify by re-running tests
    """,
    model="sonnet",
    run_in_background=True
)
```

### playwright-test-generator

```python
Agent(
    subagent_type="playwright-test-generator",
    prompt="""
    Generate new E2E test:

    Test target: [describe target]
    Expected behavior: [describe expected behavior]
    """,
    model="sonnet",
    run_in_background=True
)
```

---

## Notes

1. **Browser cleanup required**: Call `playwright_close()` before and after work
2. **Screenshot management**: Saved to `.playwright-mcp/`, delete after work
3. **Unfixable tests**: Mark with `test.fixme()` and proceed

---

## Shared Rules

> See [process-base.md](process-base.md) for Agent Execution Guidelines, Agent Invocation Rules, and Plan Cleanup.
