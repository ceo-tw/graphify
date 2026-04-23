# INQUIRY Process

Process to follow for analysis/investigation requests.

---

## Plan Template (Copy to Plan Document)

Copy this entire block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **INQUIRY** type.

Proceed in the following order:

- [ ] 1. Perform analysis with **Explore** agent
- [ ] 2. Organize results
- [ ] 3. Report to user
- [ ] 4. Cleanup (invoke plan-cleanup skill)

If code modification is needed, create a separate plan as MODIFICATION type.

### Agents Used

| Agent | Purpose | Background |
|-------|---------|------------|
| **Explore** | Codebase analysis | Yes (for complex analysis) |

## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| Explore | - | pending | - | {analysis purpose} |

### Verification Checklist (INQUIRY)

No code changes - analysis only:

- [ ] **Analysis complete**: All investigation targets covered
- [ ] **Results documented**: Findings organized and clear
- [ ] **User reported**: Analysis delivered to user

---

### ⛔ Agent Invocation Rules (CRITICAL - MUST READ)

> **VIOLATION WARNING**:
> - Direct Glob/Grep without Explore agent = **PROCESS VIOLATION**
> - Skipping Explore agent for complex analysis = **PROCESS VIOLATION**

**INQUIRY uses Explore agent for codebase analysis. Main Context does NOT use direct Glob/Grep.**

### Agent Invocation Pattern (MANDATORY)

```python
# Step 1: Explore agent for analysis
agent1 = Agent(
    subagent_type="Explore",
    description="Analyze {target}",
    prompt="""
## Exploration Goal
Analyze implementation patterns and structure of {target}

## Search Targets
- Path: {search_paths}
- Pattern: {file_patterns}
- Keywords: {keywords}

## Expected Output
- Patterns/approaches in use
- Code flow
- Key component relationships

## Thoroughness Level: Medium

## Essential Files Output
5-10 core files
Format: path:line - role/purpose
""",
    model="haiku",
    run_in_background=True
)
# Log agentId to Agent Execution Log table above
# Wait for completion with TaskOutput(task_id=agent1.agent_id)

# Step 2-3: Organize results and report (Main context OK for reporting)
# Summarize findings and present to user

# Step 4: Cleanup
Skill(skill="plan-cleanup", args=f"{plan_name}")
```
```

---

## When to Use

Use this process when:
- User requests analysis, investigation, or understanding of code
- No code modification is required
- Goal is to provide information/explanation

### Examples

| Request | Type |
|---------|------|
| "Analyze code structure" | ✅ INQUIRY |
| "Understand how auth works" | ✅ INQUIRY |
| "Why is this bug happening?" | ✅ INQUIRY (but may lead to BUG_FIX) |
| "Show test coverage" | REPORT (quantitative) |
| "Fix this bug" | BUG_FIX |

---

## Characteristics

- **No code modification**: Only analysis and investigation
- **Use Explore agent**: Codebase exploration
- **Document results**: Organize and report analysis results

---

## Explore Agent Usage Pattern

> **MUST**: Always use Explore agent for file exploration. Direct Glob/Grep is **PROHIBITED**.
> **Type**: INQUIRY uses **ANALYZE** type from [Explore Prompt Guide](../components/explore-prompt-guide.md)
> **Template**: See [explore-types-reference.md](../components/explore-types/explore-types-reference.md) ANALYZE section

```python
# CORRECT: Use ANALYZE type for INQUIRY process
Agent(
    subagent_type="Explore",
    description="{brief_description}",
    prompt="""
## Exploration Goal
Analyze implementation patterns and structure of {target}

## Search Targets
- Path: {search_paths}
- Pattern: {file_patterns}
- Keywords: {keywords}

## Expected Output
- Patterns/approaches in use
- Code flow
- Key component relationships

## Thoroughness Level: Medium

## Essential Files Output
5-10 core files
Format: path:line - role/purpose
""",
    model="haiku",  # haiku fixed for all Explore types
    run_in_background=True
)

# PROHIBITED: Direct Glob/Grep
# Glob(...)  ❌
# Grep(...)  ❌
```

### Model Selection

- **All Explore types**: `model="haiku"` (fixed for cost efficiency)
- **Exception only**: `model="sonnet"` for architecture deep-dive (Very thorough)
- See [Explore Prompt Guide - Model Selection](../components/explore-prompt-guide.md#model-selection-haiku-fixed) for details

### Agent Execution Log Template

```markdown
## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| Explore | - | pending | - | Codebase analysis |
```

---

## Example Analysis Requests

| Request Example | Explore Prompt |
|-----------------|----------------|
| "Analyze code structure" | "Analyze the overall directory structure and main modules of the project" |
| "Understand auth logic" | "Analyze the flow and structure of authentication-related code" |
| "Show dependency relationships" | "Analyze inter-module dependency relationships" |

---

## Result Report Format

```markdown
## Analysis Results

### 1. Summary
[Key findings]

### 2. Details
[Specific analysis results]

### 3. Follow-up Actions (if applicable)
[Propose separate plan if code modifications are needed]
```

---

## Notes

1. **No code modification**: INQUIRY only performs analysis
2. **Separate plan for modifications**: Create new plan as MODIFICATION/BUG_FIX
3. **Clear result delivery**: Organize in a format user can understand
4. **Agent Execution Log**: Include log table from Plan Template for tracking Explore agent

---

## Shared Rules

> See [process-base.md](process-base.md) for Agent Execution Guidelines and Plan Cleanup.
