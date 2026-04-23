---
title: Onboarding Checklist Template
impact: MEDIUM
impactDescription: 91-item comprehensive setup verification
tags: [template]
used_by: [wm-setup]
migrated_from: onboarding-report.md
---

# Onboarding Checklist Template

**Impact: MEDIUM** - Structured checklist for project setup verification

## Overview

91-item checklist organized into 11 categories for comprehensive project onboarding.
Each item has status tracking: PASS, FAIL, SKIP, or PENDING.

## Checklist Structure

```typescript
interface ChecklistItem {
  id: string;           // e.g., "MCP-001"
  category: string;     // e.g., "MCP Setup"
  item: string;         // Description
  status: "PASS" | "FAIL" | "SKIP" | "PENDING";
  notes?: string;       // Optional remediation notes
}

interface ChecklistCategory {
  name: string;
  items: ChecklistItem[];
  passRate: number;     // 0-100%
}
```

## Categories and Items

### 1. MCP Setup (9 items)

| ID | Item | Expected |
|----|------|----------|
| MCP-001 | Serena MCP connected | mcp__plugin_serena_serena |
| MCP-002 | Playwright MCP connected | mcp__playwright |
| MCP-003 | Memory MCP connected | mcp__memory |
| MCP-004 | Tavily MCP connected | mcp__tavily |
| MCP-005 | MCP tools accessible | /mcp shows tools |
| MCP-006 | Serena project activated | activate_project called |
| MCP-007 | Memory graph readable | read_graph works |
| MCP-008 | Playwright browser ready | screenshot works |
| MCP-009 | Search capability ready | tavily_search works |

### 2. Skills Setup (10 items)

| ID | Item | Expected |
|----|------|----------|
| SKL-001 | wm skill | Planning workflows |
| SKL-002 | solve skill | Problem solving |
| SKL-003 | research skill | Deep research |
| SKL-004 | codebase-explorer skill | LSP navigation |
| SKL-005 | code-quality skill | Code analysis |
| SKL-006 | e2e-test skill | Test orchestration |
| SKL-007 | worktree-manager skill | Git worktree |
| SKL-008 | restore-context skill | Context recovery |
| SKL-009 | skill-creator skill | Skill authoring |
| SKL-010 | dev-status skill | Progress tracking |

### 3. Agents Setup (10 items)

| ID | Item | Expected |
|----|------|----------|
| AGT-001 | design | Architecture design |
| AGT-002 | planner-task | Task breakdown |
| AGT-003 | dev-executor | Implementation |
| AGT-004 | qa | Quality assurance |
| AGT-005 | root-cause-finder | 5 Whys analysis |
| AGT-006 | bug-fixer | Bug resolution |
| AGT-007 | knowledge-keeper | Knowledge documentation |
| AGT-008 | playwright-test-planner | E2E test planning |
| AGT-009 | playwright-test-generator | E2E test generation |
| AGT-010 | playwright-test-healer | E2E test debugging |

### 4. Project Structure (8 items)

| ID | Item | Expected |
|----|------|----------|
| PRJ-001 | CLAUDE.md exists | Root instructions |
| PRJ-002 | AGENTS.md exists | Agent guidelines |
| PRJ-003 | .claude/ directory | Config folder |
| PRJ-004 | settings.json valid | Project settings |
| PRJ-005 | Git repository | .git/ exists |
| PRJ-006 | package.json | Node project |
| PRJ-007 | tsconfig.json | TypeScript config |
| PRJ-008 | .gitignore configured | Ignore patterns |

### 5. Memory Files (8 items)

| ID | Item | Expected |
|----|------|----------|
| MEM-001 | CLAUDE.md loaded | In memory files |
| MEM-002 | AGENTS.md loaded | In memory files |
| MEM-003 | Context map defined | Section present |
| MEM-004 | Domain rules present | Per-domain rules |
| MEM-005 | Tech stack documented | Stack defined |
| MEM-006 | Conventions documented | Code style |
| MEM-007 | Environment documented | Env requirements |
| MEM-008 | Golden rules defined | Critical rules |

### 6-11. Additional Categories (44 items)

- **Tech Stack Detection** (8 items): Language, framework, tooling
- **Best Practices** (8 items): Per-technology references
- **Hooks Configuration** (8 items): PreToolUse, PostToolUse, etc.
- **Testing Setup** (8 items): Playwright, Jest, E2E
- **Documentation** (6 items): Guides, READMEs
- **Security** (6 items): Secrets, permissions

## Generation Function

```python
def generateChecklist(analysis_result: dict) -> list[ChecklistCategory]:
    """
    Generate checklist from analysis results.

    Args:
        analysis_result: Output from runAnalysis()

    Returns:
        List of categories with evaluated items
    """
    categories = []

    # Evaluate each category
    mcp_items = evaluateMCPSetup(analysis_result.get("context_data", {}))
    skills_items = evaluateSkillsSetup(analysis_result.get("context_data", {}))
    agents_items = evaluateAgentsSetup(analysis_result.get("context_data", {}))
    project_items = evaluateProjectStructure(analysis_result.get("project_state", {}))

    categories.append({"name": "MCP Setup", "items": mcp_items})
    categories.append({"name": "Skills Setup", "items": skills_items})
    categories.append({"name": "Agents Setup", "items": agents_items})
    categories.append({"name": "Project Structure", "items": project_items})

    # Calculate pass rates
    for category in categories:
        passed = sum(1 for item in category["items"] if item["status"] == "PASS")
        category["passRate"] = (passed / len(category["items"])) * 100

    return categories
```

## Output Format

```markdown
## Onboarding Checklist Summary

| Category | Pass Rate | Status |
|----------|-----------|--------|
| MCP Setup | 89% (8/9) | PASS |
| Skills Setup | 100% (10/10) | PASS |
| Agents Setup | 90% (9/10) | PASS |
| Project Structure | 100% (8/8) | PASS |

### Failed Items

- [ ] AGT-009: knowledge-keeper - Not configured

### Remediation Required

See remediation.md for fix instructions.
```

## When to Apply

- During initial wm-setup analysis
- After project configuration changes
- For setup verification audits

## References

- [report-template.md](./report-template.md) - Full report generation
- [remediation.md](./remediation.md) - Fix instructions
