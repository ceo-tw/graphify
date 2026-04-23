---
name: e2e-test
type: workflow
description: Playwright E2E test orchestrator. Manages test planning, generation, healing, and execution via plan/generate/heal/run commands.
argument-hint: plan|generate|heal|run [target]
allowed-tools:
  - Agent
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - TaskCreate
  - TaskGet
  - TaskUpdate
  - TaskList
  - mcp__playwright__playwright_close
  - mcp__playwright__clear_codegen_session
  - mcp__playwright__get_codegen_session
  - mcp__playwright__start_codegen_session
---

# E2E Test

Integrated skill for Playwright browser automation testing. Orchestrates test planning, generation, and healing through specialized subagents.

---

## MANDATORY: Pre-Operation Cleanup

**Cleanup is required before every operation.** Previous sessions may cause conflicts.

| Step | Command | Note |
|------|---------|------|
| 1. Close browser | `playwright_close` | Always run first |
| 2. Clear session | `clear_codegen_session(sessionId)` | If session ID exists from previous run |

**Why cleanup is mandatory:**
- Browser instances persist across tool calls
- Codegen sessions retain state (action logs, page references)
- Stale state → selector mismatch, timeouts, test flakiness

---

## Workflow Overview

| Step | Description |
|------|-------------|
| **0. CLEANUP** | `playwright_close` + `clear_codegen_session` (if ID exists) |
| **1. Parse** | Extract operation (plan/generate/heal/run) and target |
| **2. Route** | Dispatch to appropriate subagent (see table below) |
| **3. Report** | Output results and cleanup status |

### Step 2: Subagent Routing

| Operation | Agent | Actions |
|-----------|-------|---------|
| **plan** | playwright-test-planner | Explore website → Map flows → Design scenarios → Save plan |
| **generate** | playwright-test-generator | Extract items → Initialize session → Execute → Generate test |
| **heal** | playwright-test-healer | Identify failures → Debug → Analyze → Fix → Verify |
| **run** | Direct Bash | `npx playwright test {pattern}` |

---

## Usage

```bash
/e2e-test <command> [arguments]
```

| Command | Arguments | Description | Subagent |
|---------|-----------|-------------|----------|
| `plan` | `<url>` | 웹사이트 테스트 계획 생성 | playwright-test-planner |
| `generate` | `<plan-file>` or `<item>` | 계획에서 테스트 생성 | playwright-test-generator |
| `heal` | `[test-file]` | 실패한 테스트 수정 | playwright-test-healer |
| `run` | `[pattern]` | 테스트 실행 | Direct (Bash) |

**Examples:**
```bash
/e2e-test plan https://todomvc.com
/e2e-test generate specs/todo-plan.md
/e2e-test generate "1.1 Add Valid Todo"
/e2e-test heal
/e2e-test heal tests/login.spec.ts
/e2e-test run
```

---

## Step 0: Cleanup Protocol

**Execute before every operation:**

```python
# 1. Close browser
result = playwright_close()
# "No browser instance to close" → OK, proceed

# 2. Clear session (if ID exists)
if known_session_id:
    clear_codegen_session(sessionId=known_session_id)
    # "Session not found" → OK, proceed

print("✅ Cleanup complete. Ready for new operation.")
```

---

## MANDATORY: Post-Operation Screenshot Cleanup

**Execute after workflow completion.** Prevents screenshot file accumulation.

| Step | Command | Note |
|------|---------|------|
| 1. Delete session screenshots | `rm -f .playwright-mcp/{session-id}*.png` | Delete by session ID pattern |
| 2. Clean old (optional) | `find .playwright-mcp -name "*.png" -mtime +1 -delete` | Delete >24h old |

**Why screenshot cleanup is MUST:**
- Efficient disk space usage
- Prevent accidental Git commits
- Keep project folder clean

---

## Step 1: Parse Command

```python
def parse_command(arguments: str) -> dict:
    parts = arguments.strip().split(maxsplit=1)
    if not parts:
        return {"operation": "help"}

    operation = parts[0].lower()
    target = parts[1] if len(parts) > 1 else None

    # Validation
    if operation == "plan" and not (target and target.startswith("http")):
        raise ValueError("plan requires URL (http:// or https://)")

    if operation == "generate" and not target:
        raise ValueError("generate requires plan file or test item")

    return {"operation": operation, "target": target}
```

---

## Step 2: Route to Subagent

### 2A. Plan → playwright-test-planner

**Use case:** Generate E2E test plan for new application

**When to use:**
- Starting E2E tests for new project
- Expanding test coverage for existing features
- Documenting tests for QA team

```python
# Cleanup first
playwright_close()

Task(
    subagent_type="playwright-test-planner",
    prompt=f"""
    Create E2E test plan for: {target_url}

    Workflow:
    1. Initialize session with start_codegen_session
    2. Navigate to URL with playwright_navigate
    3. Analyze page structure with playwright_get_visible_html
    4. Explore app with playwright_* tools
    5. Identify key user flows
    6. Design test scenarios:
       - Happy path
       - Edge cases
       - Error handling
    7. Save to specs/<app>-plan.md with Write tool

    Output: specs/<app>-plan.md
    """,
    model="sonnet"
)
```

**Output:** `specs/<app-name>-plan.md` - Contains numbered test cases, steps, expected results

### 2B. Generate → playwright-test-generator

**Use case:** Generate executable Playwright tests from test plan

**When to use:**
- Converting planned test items to code
- Creating new tests for specific scenarios
- Automating manual test cases

**Input formats:**
1. Full plan: `specs/todo-plan.md`
2. Specific item: `"1.1 Add Valid Todo"`
3. Plan + item: `specs/todo-plan.md#1.1`

```python
# Cleanup first
playwright_close()

Task(
    subagent_type="playwright-test-generator",
    prompt=f"""
    Generate Playwright test for:

    <test-suite>{item.suite_name}</test-suite>
    <test-name>{item.test_name}</test-name>
    <test-file>{item.output_file}</test-file>
    <seed-file>{item.seed_file or 'N/A'}</seed-file>
    <body>
    {item.steps}
    </body>

    Workflow:
    1. Initialize session with start_codegen_session
    2. Navigate to URL with playwright_navigate
    3. Execute each step with playwright_* tools
    4. Read logs with get_codegen_session
    5. Write test file with end_codegen_session or Write
    """,
    model="sonnet"
)
```

**Output:** `tests/<scenario-name>.spec.ts` - Single test within describe block

### 2C. Heal → playwright-test-healer

**Use case:** Auto-fix failing Playwright tests

**When to use:**
- Tests fail after app changes
- Selector updates needed
- Timing/synchronization issues
- Assertion value mismatch

```python
# Cleanup first
playwright_close()

Task(
    subagent_type="playwright-test-healer",
    prompt=f"""
    Fix failing Playwright tests.

    Scope: {target or "all tests"}

    Workflow:
    1. Identify failures via npx playwright test (Bash)
    2. For each failure:
       - Run npx playwright test <file> --debug (Bash)
       - Analyze error
       - Check page structure with playwright_get_visible_html
       - Identify root cause
       - Apply fix with Edit
       - Verify
    3. Iterate until all tests pass or marked with test.fixme()

    Output: List of fixed files, remaining issues
    """,
    model="sonnet"
)
```

**Output:** Fixed test files, unfixable tests marked with `test.fixme()`

### 2D. Run → Direct Execution

**Use case:** Execute Playwright tests and check results

```python
# Cleanup first (browser cleanup)
playwright_close()

pattern = target or ""
result = Bash(
    command=f"npx playwright test {pattern} --reporter=list",
    timeout=300000
)

if result.exit_code == 0:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed. Run `/e2e-test heal` to fix.")
```

---

## Step 3: Report Results

```
════════════════════════════════════════════════════════════════
[E2E-TEST] Operation Complete
════════════════════════════════════════════════════════════════

Operation: {operation}
Target: {target}
Status: ✅ Success | ❌ Failed

Results:
• {result_details}

Generated Files:
• {file_paths}

Cleanup Status:
• Browser: Closed
• Session: Cleared
• Screenshots: {count} files deleted

Next Steps:
• /e2e-test {suggested_next_command}

════════════════════════════════════════════════════════════════
```

---

## Decision Tree

| User Request | Command |
|--------------|---------|
| "테스트 계획 만들어" / "test plan" | `/e2e-test plan <url>` |
| "테스트 생성해" / "generate tests" | `/e2e-test generate <plan>` |
| "테스트 실패해" / "tests failing" | `/e2e-test heal` |
| "테스트 실행해" / "run tests" | `/e2e-test run` |
| (불명확) | AskUserQuestion으로 확인 |

---

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Browser timeout | Slow page load | Increase timeout, check network |
| Element not found | Selector changed | Run `/e2e-test heal` |
| Session conflict | Previous session active | Run cleanup protocol |
| Navigation failed | URL error | Verify URL accessibility |

---

## Best Practices

### Test Plan
- ✅ 구체적, 재현 가능한 단계
- ✅ 명확한 예상 결과
- ✅ 독립적인 테스트 (의존성 없음)
- ❌ 모호한 설명

### Test Generation
- ✅ 파일당 단일 테스트
- ✅ 설명적인 테스트 이름
- ✅ 각 단계 전 주석
- ✅ data-testid 우선 사용
- ❌ 하드코딩된 대기 시간
- ❌ networkidle (deprecated)

### Test Healing
- ✅ 근본 원인 수정
- ✅ 견고한 selector (role, text, testid)
- ✅ 수정 불가 시 설명과 함께 fixme()
- ❌ 임시방편 수정

---

## Screenshot Storage

### Current Configuration

Screenshots are stored in `.playwright-mcp/` directory at project root.

| Item | Configuration |
|------|---------------|
| **Storage Location** | `.playwright-mcp/` |
| **Auto Cleanup** | ✅ Deleted automatically on workflow completion |
| **Git Management** | Excluded via `.gitignore` |

**Usage example:**
```python
playwright_screenshot(
    name="page-state",
    downloadsDir=".playwright-mcp/"
)
```

---

## Related Resources

| Resource | Path | Description |
|----------|------|-------------|
| Planner Agent | `.claude/agents/playwright-test-planner.md` | Website exploration and planning |
| Generator Agent | `.claude/agents/playwright-test-generator.md` | Test code generation |
| Healer Agent | `.claude/agents/playwright-test-healer.md` | Test debugging and fixing |
| MCP Tools | `references/mcp-tools.md` | Playwright MCP tools reference |
| Screenshot Cleanup Guide | `../../docs/guides/e2e-screenshot-cleanup.md` | Guide for cleaning existing screenshots |
