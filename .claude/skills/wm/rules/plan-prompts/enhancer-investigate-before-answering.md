---
title: Investigate Before Answering
type: enhancer
source: .claude/docs/claude-code-prompt/06-code-generation/hallucination-prevention.md
applicable_to: all
priority: CRITICAL
---

# Enhancer: Investigate Before Answering

> Never speculate without checking code first - always provide verified fact-based answers

## Purpose

- Prevent speculation without reading code
- Ensure analysis based on verified facts
- Minimize hallucination

## Pattern

<investigate_before_answering>
Never speculate about code you have not opened. If the user references a
specific file, you MUST read the file before answering. Make sure to
investigate and read relevant files BEFORE answering questions about the
codebase. Never make any claims about code before investigating unless you
are certain of the correct answer - give grounded and hallucination-free answers.
</investigate_before_answering>

## Extended Pattern

<code_investigation_protocol>
Before making any claims about code or proposing changes:

1. READ the file(s) in question - never assume content
2. VERIFY function signatures, types, and patterns exist as expected
3. CHECK for existing conventions in the codebase
4. CONFIRM dependencies and imports are available
5. UNDERSTAND the context before suggesting changes

If you cannot find specific information:
- Say "I couldn't find X in the codebase"
- Do NOT invent or assume what X might contain
- Ask for clarification if needed
</code_investigation_protocol>

## When to Use

- **Always** - This enhancer applies to all analysis tasks
- When answering questions about the codebase
- Before proposing changes
- During bug analysis and debugging
- When understanding existing patterns

## Integration Example

```python
# Strategic analysis with investigation
role_prompt = Read("rules/role-strategic-phase-decomposition.md")
enhancer = Read("rules/enhancer-investigate-before-answering.md")

combined = f"""
{role_prompt}

{enhancer}

Explore the target codebase first, then decompose into PHASEs.
"""

Task(subagent_type="design", prompt=combined, model="opus")  # or planner-task, dev-executor, qa
```

## Verification Checklist

| Check | Action |
|-------|--------|
| File exists | Use Glob or Read to confirm |
| Function signature | Read the actual function |
| Import paths | Verify imports are correct |
| Types | Check type definitions |
| Conventions | Review similar code in the project |
| Dependencies | Verify packages are available |

## DO and DON'T

**DO say:**
- "Let me read the file first to understand the implementation"
- "I couldn't find this function in the files I searched"
- "Based on the code I've read at line 45..."

**DO NOT say:**
- "This probably does X" (without reading)
- "Typically this would work like X" (assumptions)
- "I assume the implementation is X" (speculation)

## Related

- [Code Exploration](enhancer-code-exploration.md)
- [Structured Research](enhancer-structured-research.md)

## Source

Extracted from: `.claude/docs/claude-code-prompt/06-code-generation/hallucination-prevention.md`
