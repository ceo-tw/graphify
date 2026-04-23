# REPORT Process

Process to follow for status report requests.

---

## Plan Template (Copy to Plan Document)

Copy this entire block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **REPORT** type.

Proceed in the following order:

- [ ] 1. Collect data with **Explore** agent
- [ ] 2. Write report
- [ ] 3. Report to user
- [ ] 4. Cleanup (invoke plan-cleanup skill)

If follow-up actions are needed, create a separate plan.

### Agents Used

| Agent | Purpose | Background |
|-------|---------|------------|
| **Explore** | Data collection | Yes (for complex exploration) |

## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| Explore | - | pending | - | {data collection purpose} |

### Verification Checklist (REPORT)

No code changes - status assessment only:

- [ ] **Data collected**: All required metrics gathered
- [ ] **Report generated**: Quantitative data included
- [ ] **User reported**: Status delivered to user

---

### ⛔ Agent Invocation Rules (CRITICAL - MUST READ)

> **VIOLATION WARNING**:
> - Direct Glob/Grep without Explore agent = **PROCESS VIOLATION**
> - Skipping Explore agent for data collection = **PROCESS VIOLATION**

**REPORT uses Explore agent for data collection. Main Context does NOT use direct Glob/Grep.**

### Agent Invocation Pattern (MANDATORY)

```python
# Step 1: Explore agent for data collection
agent1 = Agent(
    subagent_type="Explore",
    description="Collect {target} data",
    prompt="""
## Exploration Goal
Collect data related to {target}

## Search Targets
- Path: {search_paths}
- Pattern: {file_patterns}
- Keywords: {keywords}

## Expected Output
- File list
- Classification by type
- Counts/statistics

## Thoroughness Level: Quick

## Essential Files Output
Representative 5-10 files
Format: path:line - type/category
""",
    model="haiku",
    run_in_background=True
)
# Log agentId to Agent Execution Log table above
# Wait for completion with TaskOutput(task_id=agent1.agent_id)

# Collect quantitative data (Main context OK for bash commands)
Bash("npm run test -- --coverage")

# Step 2-3: Write report and deliver (Main context OK for reporting)
# Organize data and present to user

# Step 4: Cleanup
Skill(skill="plan-cleanup", args=f"{plan_name}")
```
```

---

## INQUIRY vs REPORT

| Item | INQUIRY | REPORT |
|------|---------|--------|
| Purpose | Analysis/Investigation | Status assessment |
| Result | Analysis results | Quantitative report |
| Example | "Analyze code structure" | "Show test coverage" |

---

## Report Type Examples

| Report Type | Contents |
|-------------|----------|
| Test Coverage | Coverage %, uncovered areas |
| Code Quality | Lint results, type errors, tech debt |
| Dependency Status | Package list, versions, vulnerabilities |
| Build Status | Build success/failure, warning list |

---

## Report Format

```markdown
## Status Report: [Report Title]

### 1. Summary
[Key metrics and status]

### 2. Detailed Status
[Specific data]

### 3. Areas for Improvement (if applicable)
[Issues and improvement suggestions]

### 4. Follow-up Actions (if applicable)
[Propose separate plan if additional work is needed]
```

---

## Explore + Bash Usage

> **MUST**: Always use Explore agent for file exploration. Direct Glob/Grep is **PROHIBITED**.
> **Type**: REPORT uses **COLLECT** type from [Explore Prompt Guide](../components/explore-prompt-guide.md)
> **Template**: See [explore-types-reference.md](../components/explore-types/explore-types-reference.md) COLLECT section

```python
# CORRECT: Use COLLECT type for REPORT process
Agent(
    subagent_type="Explore",
    description="{brief_description}",
    prompt="""
## Exploration Goal
Collect data related to {target}

## Search Targets
- Path: {search_paths}
- Pattern: {file_patterns}
- Keywords: {keywords}

## Expected Output
- File list
- Classification by type
- Counts/statistics

## Thoroughness Level: Quick

## Essential Files Output
Representative 5-10 files
Format: path:line - type/category
""",
    model="haiku",  # haiku fixed for all Explore types
    run_in_background=True
)

# PROHIBITED: Direct Glob/Grep
# Glob(...)  ❌
# Grep(...)  ❌

# Collect quantitative data (in Main context)
Bash("npm run test -- --coverage")
```

### Thoroughness Level for Reports

- Status reports: `Quick` (file enumeration) - COLLECT type
- Trend analysis: `Medium` (pattern identification) - Consider ANALYZE type
- See [Explore Prompt Guide - Thoroughness Level Details](../components/explore-prompt-guide.md#thoroughness-level-details)

### Agent Execution Log Template

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| Explore | - | pending | - | Data collection |
```

---

## Notes

1. **Include quantitative data**: Express in numbers when possible
2. **No code modification**: REPORT only assesses status
3. **Separate follow-up actions**: Create separate plan if modifications needed
4. **Agent Execution Log**: Include log table from Plan Template for tracking Explore agent

---

## Shared Rules

> See [process-base.md](process-base.md) for Agent Execution Guidelines and Plan Cleanup.
