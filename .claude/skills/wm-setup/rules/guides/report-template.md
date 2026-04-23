---
title: Onboarding Report Template
impact: MEDIUM
impactDescription: Structured 8-section analysis report
tags: [template]
used_by: [wm-setup]
migrated_from: onboarding-report.md
---

# Onboarding Report Template

**Impact: MEDIUM** - Standardized report format for project analysis results

## Overview

8-section report format that summarizes project analysis, checklist results,
and provides actionable recommendations.

## Report Structure

```typescript
interface OnboardingReport {
  header: ReportHeader;
  sections: ReportSection[];
  summary: ReportSummary;
  generatedAt: string;
}

interface ReportHeader {
  projectName: string;
  analysisDate: string;
  overallScore: number;      // 0-100%
  overallStatus: "READY" | "NEEDS_WORK" | "CRITICAL";
}

interface ReportSection {
  number: number;            // 1-8
  title: string;
  content: string;
  status: "PASS" | "WARN" | "FAIL";
}
```

## Section Definitions

### Section 1: Executive Summary

```markdown
## 1. Executive Summary

**Project**: {projectName}
**Analysis Date**: {date}
**Overall Readiness**: {score}% ({status})

### Key Findings

- MCP: {mcp_count} servers connected
- Skills: {skills_count}/11 configured
- Agents: {agents_count}/11 available
- Tech Stack: {tech_list}

### Critical Actions

1. {action_1}
2. {action_2}
```

### Section 2: MCP Configuration

```markdown
## 2. MCP Configuration

### Connected Servers

| Server | Status | Tools Available |
|--------|--------|-----------------|
| Serena | ACTIVE | 28 tools |
| Playwright | ACTIVE | 32 tools |
| Memory | ACTIVE | 12 tools |
| Tavily | ACTIVE | 4 tools |

### Missing Servers

- None (all recommended servers connected)

### Tool Verification

- [x] File operations (Serena)
- [x] Browser automation (Playwright)
- [x] Knowledge graph (Memory)
- [x] Web search (Tavily)
```

### Section 3: Skills Analysis

```markdown
## 3. Skills Analysis

### Installed Skills ({count}/11)

| Skill | Source | Status |
|-------|--------|--------|
| planner | project | ACTIVE |
| solve | project | ACTIVE |
| research | project | ACTIVE |

### Missing Skills

| Skill | Purpose | Priority |
|-------|---------|----------|
| e2e-test | Test orchestration | HIGH |

### Recommendations

1. Install e2e-test skill for test automation
```

### Section 4: Agents Configuration

```markdown
## 4. Agents Configuration

### Available Agents ({count}/11)

| Agent | Type | Purpose |
|-------|------|---------|
| 0-user-question | project | Intent classification |
| design | project | Architecture design |

### Missing Agents

| Agent | Impact | Remediation |
|-------|--------|-------------|
| bug-fixer | MEDIUM | Copy from template |

### Agent Hierarchy

```
wm (entry point)
  |-> design
  |-> planner-task
  |-> dev-executor
      |-> qa
```
```

### Section 5: Project Structure

```markdown
## 5. Project Structure

### Configuration Files

| File | Status | Notes |
|------|--------|-------|
| CLAUDE.md | PRESENT | Valid |
| AGENTS.md | PRESENT | Valid |
| settings.json | PRESENT | Valid |

### Directory Structure

```
.claude/
  agents/       (11 files)
  skills/       (11 directories)
  hooks/        (3 files)
  scripts/      (2 files)
```

### Memory Files Loaded

- CLAUDE.md (root instructions)
- AGENTS.md (agent guidelines)
```

### Section 6: Domain Structure

```markdown
## 6. Domain Structure

### Detected Domains

| Domain | Directory | Status | Priority |
|--------|-----------|--------|----------|
| frontend | dashboard/ | ✅ VALID | HIGH |
| backend | collector/ | ✅ VALID | HIGH |
| database | docker/ | ✅ VALID | CRITICAL |
| client | client/ | ✅ VALID | MEDIUM |
| deploy | deploy/ | ✅ VALID | HIGH |
| tray-app | tray-app/ | ✅ VALID | MEDIUM |

### Domain Configuration

| Domain | AGENTS.md | Guide File | Tech Stack |
|--------|-----------|------------|------------|
| frontend | ✅ PRESENT | ✅ guide-frontend.md | Next.js, React, TypeScript |
| backend | ✅ PRESENT | - | Node.js, TypeScript |
| database | ✅ PRESENT | - | ClickHouse, Docker |

### Missing Domains

- None detected (all expected domains configured)

### Domain Registry

- Registry file: `.claude/skills/wm-setup/rules/registries/domains.yaml`
- Total domains: 6
- Status: ✅ CONFIGURED
```

### Section 7: Tech Stack Analysis

```markdown
## 7. Tech Stack Analysis

### Detected Technologies

| Technology | Version | Best Practices |
|------------|---------|----------------|
| TypeScript | 5.x | AVAILABLE |
| React | 18.x | AVAILABLE |
| Next.js | 14.x | AVAILABLE |

### Best Practices References

| Tech | Reference File | Status |
|------|----------------|--------|
| TypeScript | rules/typescript.md | LOADED |
| React | rules/react.md | LOADED |

### Missing References

- None detected
```

### Section 8: Recommendations

```markdown
## 8. Recommendations

### Immediate Actions (Priority: HIGH)

1. [ ] Install missing skill: e2e-test
2. [ ] Configure missing agent: bug-fixer

### Suggested Improvements (Priority: MEDIUM)

1. [ ] Add pre-commit hooks for code quality
2. [ ] Configure memory graph for project context

### Optional Enhancements (Priority: LOW)

1. [ ] Set up background agents for long tasks
2. [ ] Configure custom slash commands
```

## Generation Function

```python
def generateReport(
    analysis_result: dict,
    checklist: list[ChecklistCategory]
) -> OnboardingReport:
    """
    Generate full onboarding report.

    Args:
        analysis_result: Output from runAnalysis()
        checklist: Output from generateChecklist()

    Returns:
        Complete OnboardingReport structure
    """
    # Calculate overall score
    total_pass = sum(c["passRate"] for c in checklist)
    overall_score = total_pass / len(checklist)

    status = "READY" if overall_score >= 90 else \
             "NEEDS_WORK" if overall_score >= 70 else "CRITICAL"

    return {
        "header": {
            "projectName": analysis_result.get("project_name", "Unknown"),
            "analysisDate": datetime.now().isoformat(),
            "overallScore": overall_score,
            "overallStatus": status
        },
        "sections": [
            generateExecutiveSummary(analysis_result, checklist),
            generateMCPSection(analysis_result),
            generateSkillsSection(analysis_result),
            generateAgentsSection(analysis_result),
            generateProjectSection(analysis_result),
            generateDomainsSection(analysis_result),
            generateTechSection(analysis_result),
            generateRecommendations(analysis_result, checklist)
        ],
        "generatedAt": datetime.now().isoformat()
    }
```

## Output Rendering

```python
def renderReport(report: OnboardingReport) -> str:
    """Render report to markdown string."""
    lines = [
        f"# Onboarding Analysis Report",
        f"",
        f"**Project**: {report['header']['projectName']}",
        f"**Date**: {report['header']['analysisDate']}",
        f"**Score**: {report['header']['overallScore']:.0f}%",
        f"**Status**: {report['header']['overallStatus']}",
        f"",
        "---",
        ""
    ]

    for section in report["sections"]:
        lines.append(section["content"])
        lines.append("")

    return "\n".join(lines)
```

## When to Apply

- After wm-setup analysis completion
- When generating project setup reports
- For documentation of project state

## References

- [checklist-template.md](./checklist-template.md) - Checklist input
- [../orchestration/workflow-orchestration.md](../orchestration/workflow-orchestration.md) - Analysis source
