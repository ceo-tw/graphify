---
name: solve
type: capability
description: "체계적 문제 해결 프로세스. 6단계 방법론(정의->수집->의사결정->분석->해결->문서화)으로 버그를 해결합니다. 사용 시점: (1) 원인 불명의 버그를 체계적으로 분석할 때, (2) 프로덕션 이슈를 근본 원인부터 해결할 때, (3) 복잡한 버그에 TDD 접근이 필요할 때. /solve 커맨드로 호출."
argument-hint: [버그 설명]
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
  - TaskUpdate
  - TaskGet
  - TaskList
  - WebSearch
user-invocable: true
hooks:
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: "echo '[SOLVE-COMPLETE] Problem solving process finished.'"
---

# solve

Systematic problem-solving skill for software development issues.

## Usage

```
/solve [problem description] [--5whys | --hypothesis]
```

**Examples:**
```
/solve Login fails with invalid token error
/solve API returns 500 on user creation --5whys
/solve Intermittent test failures in CI --hypothesis
```

---

## Options

```
  Option           Description
  ───────────────  ──────────────────────────────────────────────────────
  (default)        Full process with user decision on approach
  --5whys          Focus on 5 Whys root cause analysis in Phase 3
  --hypothesis     Enhanced hypothesis-driven approach in Phase 4
  ───────────────  ──────────────────────────────────────────────────────
```

---

## Workflow Overview

```
/solve Workflow
│
├─ Phase 1: Problem Definition
│   ├─ Parse problem description from arguments
│   ├─ Ask clarifying questions (AskUserQuestion)
│   └─ Create problem definition document
│
├─ Phase 2: Information Gathering
│   ├─ Git history analysis (recent changes)
│   ├─ Related file search
│   └─ Error log collection
│
├─ Phase 2.5: Decision Gate
│   ├─ Run complexity analysis
│   ├─ Present analysis results to user
│   ├─ Ask user to choose approach (5 options)
│   └─ Branch based on user selection
│
├─ [User Choice Branches]
│   │
│   ├─ Quick Fix
│   │   └→ bug-fixer agent (TDD) → Phase 6
│   │
│   ├─ Quick Fix + QA
│   │   └→ bug-fixer agent (TDD) → qa agent → Phase 6
│   │
│   ├─ Standard
│   │   └→ Phase 3 → Phase 4 → Phase 5 (bug-fixer) → Phase 6
│   │
│   ├─ Full Pipeline
│   │   └→ Phase 3 → Phase 4 → Phase 5 (bug-fixer) → qa agent → Phase 6
│   │
│   └─ Analysis Only
│       └→ Phase 3 → Phase 4 → Report → 2nd Decision → bug-fixer/종료
│
├─ Phase 3: Root Cause Analysis (if selected)
│   ├─ Call root-cause-finder agent (Task tool)
│   ├─ 5 Whys methodology
│   └─ Impact scope analysis
│
├─ Phase 4: Hypothesis Verification (if selected)
│   ├─ Form hypotheses based on analysis
│   ├─ Design verification experiments
│   └─ Execute and validate
│
├─ Phase 5: Resolution (if selected)
│   └─ Call bug-fixer agent for TDD fix
│
└─ Phase 6: Documentation
    ├─ Generate resolution report
    └─ Call knowledge-keeper for knowledge base update
```

> **Reference**: See [Task Integration](references/task-integration.md) for task creation, status updates, staleness prevention, and planner integration.

> **Reference**: See [Decision Gate & Execution Branches](references/decision-gate.md) for detailed Phase 2.5 logic and all branch implementations (Quick Fix, Quick Fix + QA, Standard, Full Pipeline, Analysis Only).

> **Reference**: See [Report Template & Completion Output](references/report-template.md) for Phase 6 documentation and final output format.

---

## Phase 1: Problem Definition

### 1.1 Parse Arguments

Extract problem description and options from $ARGUMENTS:

```python
# Parse arguments
problem_description = extract_description(ARGUMENTS)
options = {
    "5whys": "--5whys" in ARGUMENTS,
    "hypothesis": "--hypothesis" in ARGUMENTS
}
```

### 1.2 Clarify Problem (if needed)

If problem description is unclear, **use AskUserQuestion**:

```
Use AskUserQuestion with:
- questions array containing:
  - header: "Problem Details"
  - question: "Please provide more details about the issue."
  - options:
    - label: "Error message", description: "Specific error message or stack trace"
    - label: "Reproduction steps", description: "How to reproduce the issue"
    - label: "Recent changes", description: "Changes made before issue appeared"
    - label: "Environment info", description: "OS, version, configuration details"
  - multiSelect: true
```

### 1.3 Create Problem Definition

Save to `.claude/docs/solve/active/PROB-{timestamp}/problem.md`:

```markdown
# Problem Definition

## Basic Info
```
  Field        Value
  ───────────  ───────────────────
  Problem ID   PROB-{timestamp}
  Reported     {date}
  Status       Analyzing
  ───────────  ───────────────────
```

## Symptom
- **What**: {symptom description}
- **When**: {occurrence timing/conditions}
- **Where**: {location in codebase}
- **Severity**: Critical / High / Medium / Low

## Reproduction Steps
1. {step 1}
2. {step 2}
3. {step 3}

## Error Information
- **Error Message**: {message}
- **Stack Trace**: {if available}

## Impact Scope
- {description of affected areas}
```

---

## Phase 2: Information Gathering

### 2.1 Automatic Collection

```python
# Update task status
task_id = get_task_id_for_phase("2")
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="in_progress")

# Git recent changes
Bash(command="git log --oneline -10")

# Current branch status
Bash(command="git status")

# Recently modified files
Bash(command="git diff --name-only HEAD~5")
```

### 2.2 Related File Analysis

```python
# Search for files related to error keywords
related_files = Grep(pattern=error_keyword, output_mode="files_with_matches")

# Search in error message mentioned paths
if error_stack_trace:
    files_in_trace = extract_files_from_trace(error_stack_trace)
```

### 2.3 Record Gathered Information

Append to `analysis.md` in the problem directory.

> After Phase 2, proceed to Phase 2.5 Decision Gate. See [Decision Gate & Execution Branches](references/decision-gate.md) for the full decision logic and all execution branches.

---

## Phase 3: Root Cause Analysis

### 3.1 Invoke root-cause-finder Agent

```python
# Update Phase 3 task
task_id = get_task_id_for_phase("3")
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="in_progress")

# Use Task tool to invoke the agent
Task(
    subagent_type="root-cause-finder",
    prompt=f"""
    Analyze root cause for the following problem:

    [Problem Description]
    {problem_description}

    [Gathered Information]
    - Related files: {related_files}
    - Recent changes: {git_changes}
    - Error info: {error_info}

    Perform 5 Whys analysis and return:
    {{
      "reproduction": {{...}},
      "affected_scope": {{...}},
      "five_whys": {{...}},
      "root_cause": "...",
      "fix_suggestion": "..."
    }}
    """,
    model="opus"
)

current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="completed")
```

### 3.2 5 Whys Focus Mode (--5whys)

When `--5whys` option is specified, display detailed 5 Whys analysis:

```
============================================
[SOLVE] 5 Whys Analysis
============================================

Problem: {problem description}

Why 1: Why did {symptom} occur?
→ {cause 1}

Why 2: Why did {cause 1} happen?
→ {cause 2}

Why 3: Why did {cause 2} happen?
→ {cause 3}

Why 4: Why did {cause 3} happen?
→ {cause 4}

Why 5: Why did {cause 4} happen?
→ {root cause}

============================================
Root Cause: {root cause summary}
============================================
```

---

## Phase 4: Hypothesis Verification

### 4.1 Form Hypotheses

Based on root cause analysis:

```python
# Update Phase 4 task
task_id = get_task_id_for_phase("4")
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="in_progress")

hypotheses = [
    {
        "id": 1,
        "statement": "{X} is causing the issue",
        "prediction": "If we fix {X}, {Y} symptom will disappear",
        "test_method": "{how to verify}",
        "likelihood": "high/medium/low",
        "status": "pending"
    }
]
```

### 4.2 Hypothesis Mode (--hypothesis)

When `--hypothesis` option is specified, use enhanced hypothesis testing:

```
============================================
[SOLVE] Hypothesis Verification
============================================

### Hypothesis 1 (Likelihood: High)
- **Statement**: {X} is the root cause
- **Prediction**: Fixing {X} will resolve {Y}
- **Test Method**: {verification method}
- **Result**: [ ] Pending / [x] Confirmed / [ ] Rejected

### Hypothesis 2 (Likelihood: Medium)
...

============================================
```

### 4.3 Execute Verification

For each hypothesis:
1. Define expected outcome
2. Execute test
3. Compare results
4. Accept or reject hypothesis

```python
# After verification
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="completed")
```

---

## Phase 5: Resolution (bug-fixer)

### 5.1 Invoke bug-fixer Agent

```python
# Update Phase 5 task
task_id = get_task_id_for_phase("5")
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="in_progress")

Task(
    subagent_type="bug-fixer",
    prompt=f"""
    Fix the following bug using TDD approach:

    [Root Cause Analysis]
    {root_cause_result}

    [Fix Suggestion]
    {fix_suggestion}

    Follow RED-GREEN-REFACTOR cycle:
    1. RED: Write failing regression test
    2. GREEN: Minimal fix to pass test
    3. REFACTOR: Clean up code
    """,
    model="sonnet"
)
```

### 5.2 Verify Resolution

```python
# Run all tests
test_result = Bash(command="bun test")

if test_result.exit_code != 0:
    # Fix failed - may need iteration
    handle_fix_failure()
else:
    current = TaskGet(taskId=task_id)
    TaskUpdate(taskId=task_id, status="completed")
```

> After Phase 5, proceed to Phase 6. See [Report Template & Completion Output](references/report-template.md) for documentation format.

---

## Related Resources

```
  Resource          Path                                        Description
  ────────────────  ──────────────────────────────────────────  ──────────────────────────────────
  Methods Guide     references/methods.md                       5 Whys and Hypothesis methodology
  Complexity Guide  references/complexity.md                    Complexity analysis & recommendations
  Decision Gate     references/decision-gate.md                 Decision gate & execution branches
  Report Template   references/report-template.md               Phase 6 documentation & output
  Task Integration  references/task-integration.md              Task management & planner integration
  Root Cause Agent  .claude/agents/root-cause-finder.md       5 Whys analysis
  Bug Fixer Agent   .claude/agents/bug-fixer.md               TDD-based fixing
  QA Agent          .claude/agents/qa.md                      Quality validation
  Knowledge Keeper  .claude/agents/knowledge-keeper.md        Documentation
  Knowledge Base    .claude/docs/solve/knowledge-base/                Resolved issues
  Task Tool Guide   .claude/skills/wm/rules/components/task-tool-planning-guide.md
  ────────────────  ──────────────────────────────────────────  ──────────────────────────────────
```
