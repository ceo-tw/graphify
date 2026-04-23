# Planning Agents Guide Component

This guide provides structured templates for wm's planning agents, ensuring consistent and high-quality planning output.

---

## Planning Agent Type System

wm's planning agents perform 2 roles (PHASE decomposition is done directly by wm):

| Type | Purpose | Custom Agent | Model | Primary Use |
|------|---------|--------------|-------|-------------|
| **TACTICAL** | PHASE → Task breakdown + self-validation | `planner-task` | opus | Task planning |
| **ARCHITECT** | Component/architecture design | `design` | opus | Design decisions |

### Type Selection Guide

```
What is your planning goal?
├─ Decompose PRD into PHASEs → wm (Plan Writing, Step 4)
├─ Break down PHASE into Tasks → TACTICAL (planner-task, includes self-validation)
└─ Design architecture/components → ARCHITECT (design)
```

### Type Reference

> **Full details**: See the [Expected Output Format](#expected-output-format) section below for templates and expected output formats per type.

---

## Process-to-Type Mapping

| Process | Primary Type | Secondary Type |
|---------|--------------|----------------|
| NEW_DEVELOPMENT | ARCHITECT | TACTICAL |
| MODIFICATION | ARCHITECT | TACTICAL |
| BUG_FIX (Complex) | TACTICAL | - |
| INQUIRY | - | - |
| REPORT | - | - |
| CLEANUP | - | - |

---

## Agent Invocation Patterns

Custom agent invocation patterns for each type:

```python
# ARCHITECT: design
Task(
    subagent_type="design",
    description="<Brief 3-5 word description>",
    prompt="...",
    run_in_background=True
)

# TACTICAL: planner-task (includes self-validation)
Task(
    subagent_type="planner-task",
    description="<Brief 3-5 word description>",
    prompt="...",
    run_in_background=True
)
```

---

## Structured Prompt Template

When invoking planning agents, use this structured format:

```python
Task(
    subagent_type="<design|planner-task>",
    description="<Brief 3-5 word description>",
    prompt="""
## Planning Goal
<Clear planning purpose statement>

## Input Context
- Document: <input document path or content>
- Constraints: <project constraints>
- Project Type: <tech stack>

## Role Prompt
{role_prompt_content}

## Enhancers
{enhancer_content}

## Expected Output
- <expected result 1>
- <expected result 2>
- <expected result 3>

## Planning Depth: <Standard|Deep>
""",
    model="opus",
    run_in_background=True
)
```

### Template Sections Explained

| Section | Purpose | Example |
|---------|---------|---------|
| **Planning Goal** | Clear planning purpose | "Decompose PRD into PHASEs" |
| **Input Context** | Define input scope | PRD path, constraints, tech stack |
| **Role Prompt** | Role-specific instructions | role-strategic-*.md content |
| **Enhancers** | Additional guidance | enhancer-*.md content |
| **Expected Output** | Define output format | phases[], tasks[], architecture |
| **Planning Depth** | Set analysis depth | Standard, Deep |

---

## Model Selection Guide

| Type | Agent | Recommended Model | Rationale |
|------|-------|-------------------|-----------|
| **TACTICAL** | `planner-task` | opus | Task decomposition + self-validation needs reasoning |
| **ARCHITECT** | `design` | opus | Design decisions require analysis |

---

## Planning Depth Details

| Level | Analysis Scope | Use For |
|-------|----------------|---------|
| **Standard** | Core requirements | Most planning tasks |
| **Deep** | Edge cases, risks | Complex features |

### Standard
- Core requirement analysis
- Main dependency identification
- Basic risk assessment
- Best for: Typical feature planning

### Deep
- Edge case analysis
- Alternative approach evaluation
- Comprehensive risk mitigation
- Best for: Complex, high-risk features

---

## Background Execution

Use `run_in_background=True` based on type:

| Type | Agent | Background | Rationale |
|------|-------|------------|-----------|
| TACTICAL | `planner-task` | **Yes** | Task breakdown + self-validation requires analysis |
| ARCHITECT | `design` | **Yes** | Design analysis takes time |

---

## Task Tool Integration

Planning agents can leverage Task tools for parallel execution and progress tracking.

### When to Use Task Tools in Planning

| Scenario | Task Tool Usage | Example |
|----------|-----------------|---------|
| Multiple independent PHASEs | TaskCreate + parallel Task agents | Decompose PHASE-1 and PHASE-2 simultaneously |
| Multi-area design | TaskCreate + parallel design agents | UI design + API design in parallel |
| Multiple Explore targets | TaskCreate + parallel Explore agents | Auth patterns + API routes exploration |
| Document batch updates | TaskCreate + parallel updates | Update PRD + Design + Tasks docs |

### TaskList Pattern for Planning

```python
# 1. Create planning tasks for independent work
TaskCreate(subject="Decompose PHASE-1", description="...", metadata={"planning": True})
TaskCreate(subject="Decompose PHASE-2", description="...", metadata={"planning": True})

# 2. Execute in parallel
all_tasks = TaskList()
planning_tasks = [t for t in all_tasks if t.metadata.get("planning") and t.status == "pending"]

agents = []
for task in planning_tasks:
    current = TaskGet(taskId=task.id)              # Staleness prevention
    if current.status != "pending":
        continue
    TaskUpdate(taskId=task.id, status="in_progress")
    agent = Task(subagent_type="planner-task", prompt=f"{task.description}", run_in_background=True)
    agents.append((task.id, agent))

# 3. Wait and update
for task_id, agent in agents:
    TaskOutput(task_id=agent.agent_id, block=True)
    current = TaskGet(taskId=task_id)              # Staleness prevention
    TaskUpdate(taskId=task_id, status="completed")
```

> **Reference**: [Task Tool Planning Guide](task-tool-planning-guide.md) for detailed patterns

---

## Role Prompt Integration

Plan types integrate with plan-prompts rules:

```
.claude/skills/wm/rules/plan-prompts/
├── role-tactical-*.md       ← Used by planner-task agent
├── role-architect-*.md      ← Used by design agent
└── enhancer-*.md            ← Used by all types
```

### Loading Role Prompts

```python
# Example: Load role prompt and enhancers
role_prompt = Read("skills/wm/rules/plan-prompts/role-strategic-phase-decomposition.md")
enhancers = [
    Read("skills/wm/rules/plan-prompts/enhancer-investigate-before-answering.md"),
    Read("skills/wm/rules/plan-prompts/enhancer-structured-research.md")
]
combined_enhancers = "\n\n".join(enhancers)
```

---

## Expected Output Format

### TACTICAL Output (planner-task)
```yaml
phase_id: "PHASE-1"
tasks:
  - id: "TASK-1-1"
    subject: "Task title"
    tdd_stage: "RED|GREEN|REFACTOR"
    layer: "domain|application|infrastructure|presentation"
execution_order: []
parallel_groups: []
```

### ARCHITECT Output (design)
```yaml
architecture:
  pattern: "Clean Architecture"
  layers: []
components: []
data_flow: {}
integration_points: []
trade_offs: []
```

---

## Quick Reference Examples

See the [Expected Output Format](#expected-output-format) section above for output formats per type.

---

## Integration with WM Processes

This guide is referenced by:
- [Development Process](../processes/development-process.md) - Uses design, planner-task
- [MODIFICATION Process](../processes/development-process.md) - Uses planner-task, design
- [BUG_FIX Complex](../processes/bug-fix-complex.md) - Uses planner-task
- [WM SKILL.md](../../SKILL.md) - Main planning workflow
