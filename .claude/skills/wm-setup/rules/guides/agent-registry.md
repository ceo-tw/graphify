---
title: Core Agents Registry
impact: MEDIUM
impactDescription: 10 essential agents for workflow automation
tags: [guide, registry]
used_by: [wm-setup]
---

# Core Agents Registry

**Impact: MEDIUM** - Reference list of 10 agents for comprehensive workflow automation

## Overview

This registry defines the 10 core agents that exist in the Claude Code agent hierarchy.
Used by wm-setup to verify agent configuration.

## Agent Registry

```typescript
interface AgentDefinition {
  name: string;
  purpose: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM";
  path: string;
  invokes?: string[];
  invokedBy?: string[];
}
```

## Agent Hierarchy

```
User Request (via wm skill)
    |
    v
Intent Classification (Step 1)
    |
    +--> NEW_DEVELOPMENT/MODIFICATION
    |        |
    |        +--> [design] --> Architecture
    |        |
    |        +--> [planner-task] --> Task Breakdown (with Self-Validation)
    |        |
    |        +--> [dev-executor] --> Implementation (TDD)
    |                 |
    |                 +--> [qa] --> Quality Assurance
    |
    +--> BUG_FIX (Simple/Complex/E2E)
    |        |
    |        +--> [root-cause-finder] --> 5 Whys Analysis
    |        |
    |        +--> [bug-fixer] --> TDD Bug Fix
    |        |
    |        +--> [knowledge-keeper] --> Document Resolution
    |
    +--> INQUIRY
    |        |
    |        +--> [Explore] --> Codebase Analysis (4 types)
    |        |        |
    |        |        +--> LOCATE: 파일/심볼 위치 찾기
    |        |        +--> ANALYZE: 구조/관계 분석
    |        |        +--> COLLECT: 정보 수집
    |        |        +--> ASSESS: 영향도/품질 평가
    |        |
    |        +--> Direct Response --> Analysis Report
    |
    +--> REPORT
    |        |
    |        +--> Information Gathering --> File/Status Check
    |        |
    |        +--> Report Generation --> Formatted Output
    |
    +--> MULTI_INTENT
    |        |
    |        +--> Intent Decomposition
    |        |
    |        +--> Sequential Routing --> Per-intent process
    |
    +--> CLEANUP
    |        |
    |        +--> plan-cleanup skill --> Archive/Delete files
    |
    +--> RESTORATION
             |
             +--> restore-context skill --> Checkpoint Recovery
```

## Core Agents List (10 Agents + 1 Built-in)

### design (HIGH)

```yaml
name: design
purpose: Architecture and technical design
priority: HIGH
path: .claude/agents/design.md
invokes: []
invokedBy: [wm skill]
```

**Outputs**: Architecture documents, ERD diagrams

### planner-task (HIGH)

```yaml
name: planner-task
purpose: Break phases into executable tasks with TDD workflow and self-validation
priority: HIGH
path: .claude/agents/planner-task.md
invokes: []
invokedBy: [wm skill]
```

**Outputs**: Task lists, work breakdown structure
**Self-Validation**: Scope, dependencies, acceptance criteria

### dev-executor (CRITICAL)

```yaml
name: dev-executor
purpose: Execute implementation tasks with TDD workflow
priority: CRITICAL
path: .claude/agents/dev-executor.md
invokes: [qa]
invokedBy: [wm skill]
```

**Responsibilities**: Red-Green-Refactor pattern, code implementation

### qa (HIGH)

```yaml
name: qa
purpose: Comprehensive QA validation
priority: HIGH
path: .claude/agents/qa.md
invokes: []
invokedBy: [dev-executor]
```

**Responsibilities**: Implementation validation, code quality, tests, documentation

### root-cause-finder (HIGH)

```yaml
name: root-cause-finder
purpose: Find root cause using 5 Whys methodology
priority: HIGH
path: .claude/agents/root-cause-finder.md
invokes: []
invokedBy: [solve skill]
```

**Methodology**: Bug reproduction, scope analysis, 5 Whys analysis

### bug-fixer (HIGH)

```yaml
name: bug-fixer
purpose: Implement bug fix using TDD approach
priority: HIGH
path: .claude/agents/bug-fixer.md
invokes: []
invokedBy: [solve skill]
```

**Methodology**: Write failing regression test, minimal fix, refactor

### knowledge-keeper (MEDIUM)

```yaml
name: knowledge-keeper
purpose: Record bug resolution to knowledge base
priority: MEDIUM
path: .claude/agents/knowledge-keeper.md
invokes: []
invokedBy: [solve skill]
```

**Outputs**: Searchable patterns, Memory MCP entities

### playwright-test-planner (MEDIUM)

```yaml
name: playwright-test-planner
purpose: Create comprehensive E2E test plans
priority: MEDIUM
path: .claude/agents/playwright-test-planner.md
invokes: [playwright-test-generator]
invokedBy: [e2e-test skill]
```

**Use cases**: Web application E2E testing

### playwright-test-generator (MEDIUM)

```yaml
name: playwright-test-generator
purpose: Generate automated browser tests using Playwright
priority: MEDIUM
path: .claude/agents/playwright-test-generator.md
invokes: []
invokedBy: [playwright-test-planner]
```

### playwright-test-healer (MEDIUM)

```yaml
name: playwright-test-healer
purpose: Debug and fix failing Playwright tests
priority: MEDIUM
path: .claude/agents/playwright-test-healer.md
invokes: []
invokedBy: [e2e-test skill]
```

### Explore (HIGH) - Built-in

```yaml
name: Explore
purpose: Codebase exploration with 4 type system
priority: HIGH
path: N/A (built-in subagent)
invokes: []
invokedBy: [wm skill - INQUIRY process]
```

**Explore Types**:
- LOCATE: 파일/심볼 위치 찾기
- ANALYZE: 구조/관계 분석
- COLLECT: 정보 수집
- ASSESS: 영향도/품질 평가

**Note**: Claude Code에 내장된 에이전트로 별도 설치 불필요

## Verification Function

```python
def verifyAgents(context_data: dict) -> dict:
    """
    Verify installed agents against core list.

    Args:
        context_data: Parsed /context output

    Returns:
        {
            "installed": ["design", ...],
            "missing": ["bug-fixer", ...],
            "pass_rate": 85
        }
    """
    core_agents = [
        "design", "planner-task",
        "dev-executor", "qa", "root-cause-finder", "bug-fixer",
        "knowledge-keeper", "playwright-test-planner",
        "playwright-test-generator", "playwright-test-healer"
    ]

    installed = []
    missing = []

    project_agents = context_data.get("agents", {}).get("project", [])

    for agent in core_agents:
        if agent in project_agents:
            installed.append(agent)
        else:
            missing.append(agent)

    return {
        "installed": installed,
        "missing": missing,
        "pass_rate": (len(installed) / len(core_agents)) * 100
    }
```

## Agent Categories

### Core Development (4 agents)

| Agent | Priority | Purpose |
|-------|----------|---------|
| design | HIGH | Architecture design |
| planner-task | HIGH | Task breakdown (with self-validation) |
| dev-executor | CRITICAL | TDD implementation |
| qa | HIGH | Quality assurance |

### Bug Resolution (3 agents)

| Agent | Priority | Purpose |
|-------|----------|---------|
| root-cause-finder | HIGH | 5 Whys analysis |
| bug-fixer | HIGH | TDD bug fix |
| knowledge-keeper | MEDIUM | Resolution documentation |

### E2E Testing (3 agents)

| Agent | Priority | Purpose |
|-------|----------|---------|
| playwright-test-planner | MEDIUM | Test planning |
| playwright-test-generator | MEDIUM | Test generation |
| playwright-test-healer | MEDIUM | Test debugging |

### Analysis (1 built-in agent)

| Agent | Priority | Purpose |
|-------|----------|---------|
| Explore | HIGH | Codebase exploration (4 types) |

## When to Apply

- During wm-setup agent verification
- When generating setup recommendations
- For agent installation guidance

## References

- [skill-registry.md](./skill-registry.md) - Skills that invoke agents
- [checklist-template.md](./checklist-template.md) - Checklist items
- [remediation.md](./remediation.md) - Fix instructions
