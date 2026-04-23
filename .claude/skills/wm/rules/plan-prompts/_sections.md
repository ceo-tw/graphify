---
title: Sections and Categories
version: 1.0.0
---

# Plan Prompts Sections

## Role Categories

### Strategic Role (Strategic Analysis)

**Agent**: wm (Plan Writing)
**Purpose**: Decompose PRD requirements into PHASE units, establish strategic plans

| Prompt | Description | Priority |
|--------|-------------|----------|
| deep-questioning | 4-stage questioning for goal extraction (WHAT/WHY/WHO/DONE) | HIGH |
| phase-decomposition | PRD to PHASE decomposition | HIGH |
| dependency-analysis | Inter-PHASE dependency identification | HIGH |
| risk-assessment | Risk identification and mitigation strategy | MEDIUM |

**GSD Integration Notes**:
- `deep-questioning`: Applied in wm Plan Writing step, generates `goals_to_verify[]`
- Output used by qa agent Step 2.7 (Goal Achievement Verification)
- Reference: `guide-deep-questioning.md`

### Architect Role (Architecture Analysis)

**Agent**: design
**Purpose**: System architecture design, component structure definition

| Prompt | Description | Priority |
|--------|-------------|----------|
| component-design | Component structure and responsibility design | HIGH |
| data-flow | Data flow and state management | HIGH |
| integration-points | Inter-system integration point definition | MEDIUM |

### Tactical Role (Tactical Analysis)

**Agent**: planner-task
**Purpose**: Decompose PHASEs into executable Tasks, determine implementation order

| Prompt | Description | Priority |
|--------|-------------|----------|
| task-breakdown | PHASE to Task decomposition | HIGH |
| tdd-ordering | TDD order (RED→GREEN→REFACTOR) | HIGH |
| layer-inference | Layer order inference | MEDIUM |

### Validator Role (Validation Analysis)

**Agent**: planner-task (Self-Validation), qa
**Purpose**: Validate plan completeness and consistency

| Prompt | Description | Priority |
|--------|-------------|----------|
| coverage-check | PRD vs PHASE/Task coverage | HIGH |
| dependency-order | Dependency order validation | HIGH |
| goal-verification | Goal achievement verification (qa Step 2.7) | HIGH |

**GSD Integration Notes**:
- `goal-verification`: QA agent validates implementation against `goals_to_verify[]` from wm (Plan Writing)
- Input: `goals_to_verify[]` from Task metadata (from wm Plan Writing)
- Output: Achievement rate (%) and unmet goals report
- Reference: `guide-deep-questioning.md`, `qa.md` Step 2.7

## Enhancer Categories

### Core Enhancers (Always Applicable)

| Enhancer | Source | Purpose |
|----------|--------|---------|
| investigate-before-answering | hallucination-prevention.md | Prevent speculation without code verification |
| verbosity-control | verbosity-balance.md | Output detail level control |

### Task-Specific Enhancers

| Enhancer | Source | Best For |
|----------|--------|----------|
| parallel-execution | parallel-tool-calling.md | Parallel exploration/analysis |
| structured-research | research-gathering.md | Hypothesis-based investigation |
| code-exploration | code-exploration.md | Codebase exploration |

## Loading Order

### Recommended Loading Sequence

1. **Role Index** - Role overview
2. **Specific Role Prompt** - Task-specific prompt
3. **Core Enhancers** - Core enhancement patterns
4. **Task-Specific Enhancers** - Optional enhancement patterns

### Example Loading

```python
# Strategic planning task
prompts_to_load = [
    "role-strategic-index.md",           # Overview
    "role-strategic-phase-decomposition.md",  # Main task
    "enhancer-investigate-before-answering.md",  # Core
    "enhancer-parallel-execution.md"     # For parallel analysis
]
```

## Composition Rules

### Prompt + Enhancer Combination

```
[Role Prompt]
+ [Core Enhancers] (always)
+ [Task-Specific Enhancers] (as needed)
= [Combined Prompt for Plan Agent]
```

### Role + Enhancer Matrix

| Role | Required Enhancers | Optional Enhancers |
|------|-------------------|-------------------|
| Strategic | investigate-before-answering | structured-research, parallel-execution |
| Architect | investigate-before-answering, code-exploration | verbosity-control, parallel-execution |
| Tactical | investigate-before-answering, code-exploration | parallel-execution |
| Validator | investigate-before-answering | verbosity-control |

### Conflicts and Precedence

1. Role prompts define the primary task
2. Enhancers augment behavior, don't override
3. If conflict exists, role prompt takes precedence
4. Multiple enhancers stack additively

## Centralized References

| Reference | File | Contents |
|-----------|------|----------|
| Criteria | `_common-criteria.md` | XML criteria for all roles |
| Output Formats | `_output-formats.md` | JSON output examples |
| Sections | `_sections.md` | This file - navigation and composition |

## Naming Conventions

### File Naming

| Pattern | Example | Type |
|---------|---------|------|
| `role-{role}-index.md` | `role-strategic-index.md` | Index |
| `role-{role}-{task}.md` | `role-strategic-phase-decomposition.md` | Role Prompt |
| `enhancer-{pattern}.md` | `enhancer-parallel-execution.md` | Enhancer |

### Tag Conventions

```xml
<role>Strategic Planner</role>
<responsibility>Brief description</responsibility>
<instructions>Step-by-step guide</instructions>
<output_format>Expected format</output_format>
<constraints>Limitations</constraints>
```

## Quality Criteria

### Role Prompts

- [ ] Clear role definition
- [ ] Specific instructions (numbered steps)
- [ ] Defined output format
- [ ] Realistic constraints
- [ ] No overlap with other roles

### Enhancers

- [ ] Source document linked
- [ ] Applicable roles specified
- [ ] Additive behavior (no override)
- [ ] Minimal token footprint
- [ ] Clear value proposition
