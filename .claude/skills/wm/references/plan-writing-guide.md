# Plan Writing Guide (Detail)

## Planning Agent Model Rule (MUST)

Planning agents (design, planner-task) MUST use `model="opus"`.

| Agent | Model | Rationale |
|-------|-------|-----------|
| `design` | **opus** | Architecture decisions require strongest model |
| `planner-task` | **opus** | Task decomposition + self-validation requires strongest model |

## Plan Document Location

`.claude/plans/{feature-name}.md`

### Plan Document Paths

| Document Type | Path Pattern | Description |
|---------------|--------------|-------------|
| PRD | `.claude/plans/{feature-name}.md` | Root-level PRD document |
| DESIGN | `.claude/plans/{feature-name}-DESIGN.md` | Architecture + ERD (unified) |
| TASKS | `.claude/plans/{feature-name}-TASKS-PHASE-{num}.md` | Task breakdown per PHASE |

## Plan Structure (Module Assembly)

**Section 0 is MANDATORY** in every plan. For **Complex types** (NEW_DEVELOPMENT, MODIFICATION, BUG_FIX Complex/E2E, MULTI_INTENT), wm directly injects the execution process template from the corresponding process file during Step 4 (Plan Writing). Worktree steps are included only if selected during planning. For **Simple types** (BUG_FIX Simple, DOCUMENTATION, DOCUMENTATION_BATCH, INQUIRY, REPORT, CLEANUP), execution proceeds directly with a minimal Section 0.

### Section 0 Template Injection

**Complex types**: wm reads the process file and copies the `## Plan Template` block into Section 0.

```python
# wm Step 4: Read process file and inject template
process_file_path = f"${{CLAUDE_SKILL_DIR}}/{process_file}"
process_content = Read(process_file_path)
# Extract "## Plan Template (Copy to Plan Document)" section
# Copy into plan document as Section 0
```

**Simple types**: Include a minimal line.

```markdown
## 0. Pre-Execution Required Steps (MUST)

- [ ] execution skip (auto) -- {TYPE} type, {COMPLEXITY} complexity
```

> **Pre-Approval Check**: Before `ExitPlanMode`, verify Section 0 exists. If missing, add it now.

## Required Sections

| # | Section | Description |
|---|---------|-------------|
| **0** | **Pre-Execution Required Steps** | MANDATORY - Use template above |
| 1 | Problem Definition | Current state -> Goal |
| 2 | Clarified Requirements | Checkbox list (`- [ ]`) with specific items |
| 3 | Verification Method | How to verify completion |

### Component Assembly by Type

| Type | problem | requirements | verification |
|------|---------|--------------|--------------|
| NEW_DEVELOPMENT | Yes | Yes | Yes |
| MODIFICATION | Yes | Yes | Yes |
| BUG_FIX | Yes | Yes | Yes |
| INQUIRY | Yes | Yes | Yes |
| REPORT | Yes | Yes | Yes |
| CLEANUP | Yes | Yes | Yes |
| DOCUMENTATION | Yes | Yes | No |
| MULTI_INTENT | Yes | Yes | Yes |
| RESTORATION | No | No | No |

## Writing Order

1. Determine type (NEW_DEVELOPMENT, MODIFICATION, BUG_FIX, etc.)
2. For MULTI_INTENT: Extract individual intents and their priorities
3. **Read process file** (Complex types) and extract Plan Template
4. **Write Section 0 first** (inject template for Complex, minimal for Simple)
5. Write freely:
   - `## 1. Problem Definition`
   - `## 2. Detailed Requirements`
   - `## 3. Verification`
6. Verify Section 0 exists before proceeding
7. Report to user and get approval (ExitPlanMode)

## Task Tool Consideration (Parallel Planning)

| Situation | Task Tool Usage |
|-----------|-----------------|
| Independent PHASE decomposition | TaskCreate + parallel planner-task |
| Multiple design areas | TaskCreate + parallel design agents |
| Independent Explore targets | TaskCreate + parallel Explore agents |
| Batch document modifications | TaskCreate + parallel edits |

> **Reference**: [Task Tool Planning Guide](../rules/components/task-tool-planning-guide.md)

## Checkbox Format

Requirements, execution processes, and verification items in plan documents must use `- [ ]` checkboxes for progress tracking.

## Language Rules

Language output is controlled by the `"language"` setting in `.claude/settings.json`. No explicit language directives are needed in plan documents.
