---
title: Verbosity Control
type: enhancer
source: .claude/docs/claude-code-prompt/03-communication-style/verbosity-balance.md
applicable_to: all
priority: MEDIUM
---

# Enhancer: Verbosity Control

> Adjust output detail level appropriately for the situation

## Purpose

- Maintain appropriate detail level for task type
- Improve efficiency by removing unnecessary explanations
- Focus on important information

## Default Behavior

Claude 4.5 model default characteristics:
- **More direct and grounded**: Fact-based progress reporting
- **More conversational**: Natural and fluent communication
- **Less verbose**: Can skip detailed summaries for efficiency

## Verbosity Levels

### Level 1: Minimal (Actions Only)

<verbosity_minimal>
Execute actions silently. Report only:
- Errors that need attention
- Final results
- Questions when blocked
</verbosity_minimal>

**Use for**: Automated tasks, repetitive tasks

### Level 2: Progress Updates

<verbosity_progress>
Provide brief progress updates:
- Current action (1 line)
- Result (1-2 lines)
- Next step if continuing
</verbosity_progress>

**Use for**: General analysis tasks

### Level 3: Detailed Explanations

<verbosity_detailed>
Explain your reasoning and actions:
- What you're doing and why
- What you found
- Your analysis and recommendations
- Next steps with rationale
</verbosity_detailed>

**Use for**: Architecture decisions, complex analysis

### Level 4: Educational (Teaching Mode)

<verbosity_educational>
Explain everything in detail as if teaching:
- Why each action is taken
- What the code does
- Concepts being applied
- Best practices being followed
This helps the user learn from the process.
</verbosity_educational>

**Use for**: Learning purposes, onboarding

## When to Use

| Task Type | Recommended Level |
|-----------|-------------------|
| Strategic Analysis | Detailed (Level 3) |
| Architecture Design | Detailed (Level 3) |
| Task Breakdown | Progress (Level 2) |
| Validation | Progress (Level 2) |
| Quick Checks | Minimal (Level 1) |

## Context-Specific Verbosity

<adaptive_verbosity>
Adjust verbosity based on task:

**Brief** (1-2 lines):
- Simple fixes
- Routine operations
- Automated tasks

**Moderate** (paragraph):
- Code changes
- Analysis results
- Recommendations

**Detailed** (full explanation):
- Architecture decisions
- Complex debugging
- Learning exercises
- When user asks "why"
</adaptive_verbosity>

## Integration Example

```python
# Tactical analysis with progress updates
role_prompt = Read("rules/role-tactical-task-breakdown.md")
enhancer = Read("rules/enhancer-verbosity-control.md")

combined = f"""
{role_prompt}

<verbosity_progress>
Report brief progress at each analysis step:
- Item currently being analyzed
- Summary of findings
- Next step
</verbosity_progress>
"""

Task(subagent_type="planner-task", prompt=combined, model="opus")  # or other planning agents
```

## Tool Use Reporting

<tool_use_reporting>
When using tools:

**Before**: Don't announce what you're about to do
**After**: Brief summary of what was found/done

Example:
Bad: "I'm going to read the file now..."
Good: [Read file] "The function is on line 45, uses JWT tokens."
</tool_use_reporting>

## Progress Reporting Pattern

For long-running tasks:

<progress_reporting>
For multi-step tasks, provide status updates:

Starting: [task name]
Step 1/5: [brief description] - Done
Step 2/5: [brief description] - In progress
...
Complete: [summary of what was accomplished]

Keep updates to 1 line per step.
</progress_reporting>

## DO and DON'T

**DO:**
- Match verbosity to task complexity
- Front-load important information
- Use structured output for complex results

**DON'T:**
- Explain every tool call before making it
- Add unnecessary commentary
- Repeat information already shown

## Related

- [Parallel Execution](enhancer-parallel-execution.md)
- [Investigate Before Answering](enhancer-investigate-before-answering.md)

## Source

Extracted from: `.claude/docs/claude-code-prompt/03-communication-style/verbosity-balance.md`
