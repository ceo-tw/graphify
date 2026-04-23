# Process Base (Shared Components)

Common sections shared across all process files. Referenced by individual process files to avoid duplication.

---

## Agent Execution Guidelines

**Key Requirements**:
1. Use `run_in_background=True` for all agents
2. Log agentId to plan's Agent Execution Log after launch
3. Independent agents MUST run in parallel where possible
4. All code changes on code files through Agents only - Main Context NEVER uses Edit/Write on code files directly
   - wm (Main Context) may use Edit directly on plan documents (checkboxes, Agent Execution Log, etc.)
   - Only code file modifications must go through Agents

---

## Agent Invocation Rules

> **VIOLATION WARNING**:
> - Direct Edit/Write on code files without Agent = **PROCESS VIOLATION**
> - Sequential execution of independent tasks = **PROCESS VIOLATION**
> - Skipping Agent call = **PROCESS VIOLATION**

---

## Plan Cleanup

After workflow completion:
```python
Skill(skill="plan-cleanup", args="{plan_name}")
```

**Note**: Cleanup failure is non-blocking. Workflow completion is prioritized.
