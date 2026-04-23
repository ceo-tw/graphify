---
title: Code Exploration
type: enhancer
source: .claude/docs/claude-code-prompt/06-code-generation/code-exploration.md
applicable_to: architect, tactical
priority: HIGH
---

# Enhancer: Code Exploration

> Thoroughly explore codebase before making changes to understand existing patterns

## Purpose

- Ensure understanding of existing code before proposing changes
- Identify project conventions
- Discover reusable existing utilities

## Pattern

<code_exploration>
ALWAYS read and understand relevant files before proposing code edits.
Do not speculate about code you have not inspected. If the user references
a specific file/path, you MUST open and inspect it before explaining or
proposing fixes.

Be rigorous and persistent in searching code for key facts. Thoroughly
review the style, conventions, and abstractions of the codebase before
implementing new features or abstractions.
</code_exploration>

## Thorough Investigation Pattern

<thorough_investigation>
Before answering questions or proposing changes:

1. Read all directly relevant files
2. Check related files (imports, dependencies)
3. Review similar existing code for patterns
4. Verify function signatures and types
5. Understand the context and conventions

Only then:
- Make claims about code
- Propose changes
- Suggest implementations

Quote specific code and line numbers when making points.
</thorough_investigation>

## Exploration Checklist

<exploration_checklist>
[ ] Read the target file(s)
[ ] Check imports and dependencies
[ ] Review related files for patterns
[ ] Verify types and interfaces
[ ] Look for existing utilities
[ ] Check test files for expected behavior
[ ] Review recent git history if relevant
</exploration_checklist>

## When to Use

- During architecture design (understanding existing patterns)
- During Task decomposition (understanding existing structure)
- When adding new components (understanding conventions)
- When planning refactoring (understanding impact scope)

## Systematic Exploration

<systematic_exploration>
Explore the codebase systematically:

1. **Structure**: Understand project layout
   - ls, glob for file structure
   - Identify key directories

2. **Entry Points**: Find where things start
   - Main files, exports
   - Public interfaces

3. **Dependencies**: Map relationships
   - Imports and exports
   - Module boundaries

4. **Patterns**: Identify conventions
   - Naming patterns
   - Code organization
   - Error handling style

5. **Tests**: Check expected behavior
   - Test files show intended usage
   - Edge cases documented
</systematic_exploration>

## Integration Example

```python
# Architect analysis with thorough exploration
role_prompt = Read("rules/role-architect-component-design.md")
enhancer = Read("rules/enhancer-code-exploration.md")

combined = f"""
{role_prompt}

{enhancer}

Before designing new components:
1. Find and read similar existing components
2. Understand project's component structure patterns
3. Check for reusable utilities
"""

Task(subagent_type="design", prompt=combined, model="opus")  # or planner-task for TACTICAL
```

## Task-Specific Exploration

### For Bug Fixing

<bug_exploration>
When fixing bugs:

1. Read error message/stack trace
2. Read file(s) mentioned in error
3. Read related files (called functions, imports)
4. Check test files for expected behavior
5. Review git history for recent changes
6. Then form hypothesis and fix
</bug_exploration>

### For Feature Implementation

<feature_exploration>
When implementing features:

1. Find similar existing features
2. Study their implementation patterns
3. Identify shared utilities
4. Review coding conventions
5. Check related tests
6. Then implement following patterns
</feature_exploration>

### For Refactoring

<refactor_exploration>
When refactoring:

1. Read all code to be refactored
2. Map all usages (grep for references)
3. Understand current patterns
4. Check tests that verify behavior
5. Plan minimal change path
6. Then refactor incrementally
</refactor_exploration>

## Large Codebase Strategy

<large_codebase_exploration>
For large codebases:

1. Start with project structure (README, docs)
2. Use Explore agent for broad searches
3. Focus on relevant modules
4. Follow import chains
5. Don't try to read everything

Key files to find first:
- Entry points (main, index)
- Configuration (config files)
- Type definitions
- Test files (show usage patterns)
</large_codebase_exploration>

## DO and DON'T

**DO:**
- Read files before making claims
- Quote specific line numbers
- Note existing patterns
- Check for similar implementations

**DON'T:**
- Propose changes without reading code
- Assume function signatures
- Ignore existing conventions
- Skip checking for utilities

## Related

- [Investigate Before Answering](enhancer-investigate-before-answering.md)
- [Structured Research](enhancer-structured-research.md)

## Source

Extracted from: `.claude/docs/claude-code-prompt/06-code-generation/code-exploration.md`
