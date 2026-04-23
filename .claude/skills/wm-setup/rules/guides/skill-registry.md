---
title: Core Skills Registry
impact: MEDIUM
impactDescription: Essential skills for project setup
tags: [guide, registry]
used_by: [wm-setup]
---

# Core Skills Registry

**Impact: MEDIUM** - Reference list of core skills for comprehensive Claude Code setup

## Overview

This registry defines the core skills recommended for full Claude Code functionality.
Used by wm-setup to verify skill installation and guide missing skill setup.

## Skills Registry

```typescript
interface SkillDefinition {
  name: string;
  purpose: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM";
  path: string;
  dependencies?: string[];
  triggerKeywords: string[];
}
```

## Core Skills List

### 1. wm (CRITICAL)

```yaml
name: wm
purpose: 통합 워크플로우 매니저 - 요청 분류, 계획 생성, 프로세스 라우팅
priority: CRITICAL
path: .claude/skills/wm/SKILL.md
triggerKeywords: [plan, scope, breakdown, strategy, phases, analyze, investigate, 분석, 조사, report, status, 보고, 현황, cleanup, archive, 정리]
dependencies: []
```

**Capabilities**:
- Request classification (9 types):
  - NEW_DEVELOPMENT / MODIFICATION: 기능 개발
  - BUG_FIX (Simple/Complex/E2E): 버그 수정
  - INQUIRY: 분석/조사
  - REPORT: 상태 보고
  - CLEANUP: 파일 정리
  - MULTI_INTENT: 복합 요청
  - RESTORATION: 체크포인트 복원
- Explore 타입 시스템 (LOCATE, ANALYZE, COLLECT, ASSESS)
- Agent Execution Log (agentId 추적)
- Phase-based planning with approval workflow

### 2. solve (CRITICAL)

```yaml
name: solve
purpose: Systematic problem-solving via 6-step methodology
priority: CRITICAL
path: .claude/skills/solve/SKILL.md
triggerKeywords: [bug, debug, fix, investigate, root cause]
dependencies: []
```

**Methodology**: Define -> Collect -> Analyze -> Hypothesis -> Solve -> Document

### 3. research (HIGH)

```yaml
name: research
purpose: Deep research with 5-10 web searches
priority: HIGH
path: .claude/skills/research/SKILL.md
triggerKeywords: [research, find out, learn about, investigate]
dependencies: [WebSearch]
```

**Output**: Key summary with sources

### 4. codebase-explorer (HIGH)

```yaml
name: codebase-explorer
purpose: LSP-based codebase navigation
priority: HIGH
path: .claude/skills/codebase-explorer/SKILL.md
triggerKeywords: [find symbol, definition, references, calls]
dependencies: [serena MCP]
```

**Capabilities**: Symbol definitions, references, call hierarchy

### 5. code-quality (HIGH)

```yaml
name: code-quality
purpose: Code smell detection, refactoring, architecture review
priority: HIGH
path: .claude/skills/code-quality/SKILL.md
triggerKeywords: [refactor, clean up, code smell, review]
dependencies: []
```

### 6. e2e-test (HIGH)

```yaml
name: e2e-test
purpose: Playwright E2E test orchestration
priority: HIGH
path: .claude/skills/e2e-test/SKILL.md
triggerKeywords: [e2e, end-to-end, playwright, browser test]
dependencies: [playwright MCP]
```

**Commands**: plan, generate, heal, run

### 7. worktree-manager (MEDIUM)

```yaml
name: worktree-manager
purpose: Git worktree management for parallel development
priority: MEDIUM
path: .claude/skills/worktree-manager/SKILL.md
triggerKeywords: [worktree, parallel, branch]
dependencies: [git]
```

**Commands**: create, complete, abort, status

### 8. restore-context (MEDIUM)

```yaml
name: restore-context
purpose: Recover workflow state after context compression
priority: MEDIUM
path: .claude/skills/restore-context/SKILL.md
triggerKeywords: [restore, resume, continue, checkpoint]
dependencies: []
```

### 9. skill-creator (MEDIUM)

```yaml
name: skill-creator
purpose: Guide for creating new skills
priority: MEDIUM
path: .claude/skills/skill-creator/SKILL.md
triggerKeywords: [create skill, new skill, extend capabilities]
dependencies: []
```

### 10. dev-status (MEDIUM)

```yaml
name: dev-status
purpose: Development workflow progress tracking
priority: MEDIUM
path: .claude/skills/dev-status/SKILL.md
triggerKeywords: [status, progress, what stage, current phase]
dependencies: []
```

## Verification Function

```python
def verifySkills(context_data: dict) -> dict:
    """
    Verify installed skills against core list.

    Args:
        context_data: Parsed /context output

    Returns:
        {
            "installed": ["wm", "solve", ...],
            "missing": ["e2e-test", ...],
            "pass_rate": 82
        }
    """
    core_skills = [
        "wm", "solve", "research", "codebase-explorer",
        "code-quality", "e2e-test", "worktree-manager",
        "restore-context", "skill-creator", "dev-status"
    ]

    installed = []
    missing = []

    project_skills = context_data.get("skills", {}).get("project", [])

    for skill in core_skills:
        if skill in project_skills:
            installed.append(skill)
        else:
            missing.append(skill)

    return {
        "installed": installed,
        "missing": missing,
        "pass_rate": (len(installed) / len(core_skills)) * 100
    }
```

## Installation Guide

```python
def getInstallInstructions(missing_skill: str) -> str:
    """Get installation instructions for a missing skill."""
    instructions = {
        "wm": "Copy from .claude/skills/wm/",
        "solve": "Copy from .claude/skills/solve/",
        "research": "Copy from .claude/skills/research/",
        "codebase-explorer": "Copy from .claude/skills/codebase-explorer/",
        "code-quality": "Copy from .claude/skills/code-quality/",
        "e2e-test": "Copy from .claude/skills/e2e-test/",
        "worktree-manager": "Copy from .claude/skills/worktree-manager/",
        "restore-context": "Copy from .claude/skills/restore-context/",
        "skill-creator": "Copy from .claude/skills/skill-creator/",
        "dev-status": "Copy from .claude/skills/dev-status/"
    }
    return instructions.get(missing_skill, "See skill documentation")
```

## Skills by Priority

### CRITICAL (2)

| Skill | Purpose |
|-------|---------|
| wm | 통합 워크플로우 관리 (개발, 버그 수정, 분석, 보고, 정리) |
| solve | Problem solving |

### HIGH (4)

| Skill | Purpose |
|-------|---------|
| research | Deep research |
| codebase-explorer | LSP navigation |
| code-quality | Code analysis |
| e2e-test | E2E testing |

### MEDIUM (4)

| Skill | Purpose |
|-------|---------|
| worktree-manager | Git worktree |
| restore-context | Context recovery |
| skill-creator | Skill authoring |
| dev-status | Progress tracking |

## When to Apply

- During wm-setup skill verification
- When generating setup recommendations
- For skill installation guidance

## References

- [agent-registry.md](./agent-registry.md) - Agent templates
- [checklist-template.md](./checklist-template.md) - Checklist items
- [remediation.md](./remediation.md) - Fix instructions
