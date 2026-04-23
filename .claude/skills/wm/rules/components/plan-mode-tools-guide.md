# Plan Mode Tools Guide

This guide provides patterns for using Plan Mode tools (EnterPlanMode, ExitPlanMode, Write) in the WM workflow.

---

## 1. Overview

Plan Mode is a restricted state designed for safe planning operations before code execution.

### Key Characteristics

| Aspect | Plan Mode | Normal Mode |
|--------|-----------|-------------|
| File modifications | Plan documents only | Any file |
| Search tools | Explore agent required | Direct Glob/Grep allowed |
| Execution | Prohibited | Allowed |
| Purpose | Planning and approval | Implementation |

---

## 2. EnterPlanMode()

### When to Call

**Immediately** on `/wm` skill invocation, before any other tool calls.

### Code Pattern

```python
# First action on /wm invocation (CRITICAL)
EnterPlanMode()  # Call before any other tool
```

### Why This is Critical

1. **Prevents accidental modifications**: Code changes are blocked until plan approval
2. **Enforces exploration constraints**: Direct Glob/Grep become prohibited
3. **Establishes planning context**: User expects planning, not immediate execution

### Error Prevention

```python
# ❌ WRONG: Using tools before EnterPlanMode
Task(subagent_type="Explore", ...)  # Violation!
EnterPlanMode()

# ✅ CORRECT: EnterPlanMode first
EnterPlanMode()
Task(subagent_type="Explore", ...)  # Now allowed
```

---

## 3. Plan Mode Rules

While in Plan Mode, these rules apply:

### Allowed Operations

| Operation | Tool | Notes |
|-----------|------|-------|
| File exploration | `Task(subagent_type="Explore")` | **Required** instead of direct Glob/Grep |
| Reading known files | `Read(path)` | Only when exact path is known |
| User clarification | `AskUserQuestion(...)` | For gathering requirements |
| Plan document writing | `Write(plan_path, ...)` | **Only** plan documents allowed |
| Plan document editing | `Edit(plan_path, ...)` | **Only** plan documents allowed |

### Prohibited Operations

| Operation | Reason |
|-----------|--------|
| Direct `Glob(...)` | Use Explore agent instead |
| Direct `Grep(...)` | Use Explore agent instead |
| `Write(code_path, ...)` | No code modifications in plan mode |
| `Edit(code_path, ...)` | No code modifications in plan mode |
| `Bash(...)` (most commands) | No execution before approval |
| Agent execution (`dev-executor`, etc.) | Wait for approval first |

---

## 4. Write(plan) Pattern

The only Write operations allowed in Plan Mode are for plan documents.

### Allowed Paths

```python
# Plan document paths
".claude/plans/{feature-name}.md"         # PRD
".claude/plans/{feature-name}-DESIGN.md"  # Design doc
".claude/plans/{feature-name}-TASKS-PHASE-{n}.md"  # Task breakdown
```

### Code Pattern

```python
plan_path = ".claude/plans/my-feature.md"

# Writing plan document (allowed in plan mode)
Write(
    file_path=plan_path,
    content="""# Feature Plan: My Feature

## 1. Problem Definition
...

## 2. Detailed Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## 4. Verification
- [ ] Verification step 1
"""
)
```

### Plan Document Structure

Plan documents must follow the structure defined in [Plan Prompt Guide](plan-prompt-guide.md).

---

## 5. ExitPlanMode()

### When to Call

After writing the plan document and reporting to the user.

### Code Pattern

```python
# 1. Write plan document
Write(file_path=plan_path, content=plan_content)

# 2. Report to user
print("""
## Plan Summary
- Feature: {feature_name}
- Type: {request_type}
- Plan file: {plan_path}
""")

# 3. Exit plan mode for approval with permission bypass
ExitPlanMode(
    allowedPrompts=[
        {"tool": "Bash", "prompt": "run tests"},
        {"tool": "Bash", "prompt": "run build"},
        {"tool": "Bash", "prompt": "run quality checks"},
        {"tool": "Bash", "prompt": "git operations"}
    ]
)
```

### allowedPrompts Parameter (IMPORTANT)

The `allowedPrompts` parameter enables the **"Yes, clear context and bypass permissions"** option.

| Without allowedPrompts | With allowedPrompts |
|------------------------|---------------------|
| Simple "yes/no" prompt | "Yes, clear context and bypass permissions" option |
| Manual approval for each Bash command | Pre-approved Bash commands run automatically |

**Common allowedPrompts patterns:**

```python
# Minimal set for most workflows
allowedPrompts=[
    {"tool": "Bash", "prompt": "run tests"},
    {"tool": "Bash", "prompt": "run build"},
    {"tool": "Bash", "prompt": "run quality checks"},
    {"tool": "Bash", "prompt": "git operations"}
]

# Extended set for full CI/CD workflows
allowedPrompts=[
    {"tool": "Bash", "prompt": "run tests"},
    {"tool": "Bash", "prompt": "run build"},
    {"tool": "Bash", "prompt": "run quality checks"},
    {"tool": "Bash", "prompt": "git operations"},
    {"tool": "Bash", "prompt": "install dependencies"},
    {"tool": "Bash", "prompt": "run linting"}
]
```

**Best Practice**: Always include `allowedPrompts` to enable streamlined approval flow.

### What Happens After ExitPlanMode

1. **User sees approval prompt**: Approve / Modify / Cancel
2. **If approved**: Execution phase begins (code modifications allowed)
3. **If modify requested**: Return to planning, revise the document
4. **If cancelled**: Workflow terminates

### Post-Approval Actions (MUST)

After approval, **load execution context and proceed**:

```python
# After ExitPlanMode approval
# 1. Re-read enriched plan
plan_content = Read(plan_path)
# 2. Load process file
process_content = Read(process_file_path)
# 3. Proceed to execution per process file
```

---

## 6. allowed-tools and Interactive Tool Rules

### Problem: Interactive Tools in allowed-tools

Including interactive tools in SKILL.md's `allowed-tools` causes the side effect of skipping user input UI.

| Tool Type | In allowed-tools | Result |
|-----------|-----------------|--------|
| Non-interactive (Read, Write, Task, etc.) | Permission check skipped | Normal -- no user input needed |
| **Interactive (AskUserQuestion)** | **Question UI auto-submitted** | **Empty response returned (bug)** |
| **Interactive (ExitPlanMode)** | **Approval UI auto-passed** | **Auto-approved (bug)** |
| **Mode switch (EnterPlanMode)** | Permission check skipped | **Normal -- /wm already signals intent** |

### Current Configuration

| Tool | In allowed-tools | Rationale |
|------|:----------------:|-----------|
| `EnterPlanMode` | **Yes** | /wm invocation already signals user intent -- double confirmation unnecessary |
| `ExitPlanMode` | **No** | User must see Approve/Modify/Cancel UI to review the plan |
| `AskUserQuestion` | **No** | User must see question UI and provide answers -- auto-submit returns empty |

### Rule

> **Never add `ExitPlanMode` or `AskUserQuestion` to `allowed-tools`.** These require user interaction. Including them causes the UI to be skipped, producing empty responses or auto-approvals.
>
> `EnterPlanMode` is safe to include because it is a mode switch, not a user decision point. When `/wm` is called, the user has already expressed intent to enter Plan Mode.

## 7. Integration with WM SKILL.md

This guide is referenced by:

- [WM SKILL.md](../../SKILL.md) - Section 0 (Plan Mode Entry), Section 5 (Plan Reporting)
- [Development Process](../processes/development-process.md) - Execution flow

### Workflow Context

```
/wm invocation
    │
    ├─► EnterPlanMode()           ← allowed-tools (auto-approved)
    │
    ├─► Exploration (Explore agent)
    │
    ├─► Clarification (AskUserQuestion)  ← NOT in allowed-tools (user UI shown)
    │
    ├─► Write(plan_path)          ← allowed-tools (auto-approved)
    │
    ├─► Report to user
    │
    └─► ExitPlanMode()            ← NOT in allowed-tools (approval UI shown)
         │
         ├─► plan-exit-gate.sh    ← Hook: wm plan validation
         │
         └─► User approval (Approve/Modify/Cancel)
              │
              └─► Load Context → Execution
```

---

## 8. Common Mistakes

### Mistake 1: Forgetting EnterPlanMode

```python
# ❌ /wm was invoked but EnterPlanMode not called
Task(subagent_type="Explore", ...)  # Violates plan mode constraint
```

### Mistake 2: Direct Search in Plan Mode

```python
EnterPlanMode()
Glob("**/*.ts")  # ❌ Prohibited - use Explore agent
```

### Mistake 3: Code Modification Before Approval

```python
EnterPlanMode()
Write("src/auth.ts", code)  # ❌ Only plan documents allowed
```

### Mistake 4: Skipping Context Loading

```python
ExitPlanMode()  # User approves
Task(subagent_type="dev-executor", ...)  # ❌ Must load context (re-read plan + process file) first
```

---

## 9. Quick Reference

| Phase | Action | Tool |
|-------|--------|------|
| Entry | Enter plan mode | `EnterPlanMode()` |
| Explore | Search codebase | `Task(subagent_type="Explore")` |
| Clarify | Ask user | `AskUserQuestion(...)` |
| Write | Create plan | `Write(plan_path, ...)` |
| Report | Show summary | Direct output to user |
| Exit | Request approval | `ExitPlanMode()` |
| Load Context | Read plan + process file | `Read(plan_path)` + `Read(process_file_path)` |
