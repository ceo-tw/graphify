---
title: Output Formats Reference
type: reference
version: 1.0.0
---

# Output Formats Reference

> Centralized output format definitions for all roles

## Strategic Role Output

### Phase Decomposition Output {#phase-decomposition}

```json
{
  "phases": [
    {
      "id": "PHASE-1",
      "name": "Phase Name",
      "goal": "Clear goal",
      "deliverables": ["Deliverable 1", "Deliverable 2"],
      "dependencies": ["PHASE-0"],
      "test_strategy": "Verification method",
      "estimated_complexity": "LOW | MEDIUM | HIGH"
    }
  ],
  "dependency_graph": {
    "PHASE-1": [],
    "PHASE-2": ["PHASE-1"]
  },
  "risks": [
    {
      "category": "Technical",
      "description": "Risk description",
      "impact": "HIGH",
      "mitigation": "Mitigation strategy"
    }
  ]
}
```

## Architect Role Output

### Component Design Output {#component-design}

```json
{
  "architecture": {
    "pattern": "Layered | Hexagonal | Microservices",
    "rationale": "Reason for selection"
  },
  "components": [
    {
      "name": "ComponentName",
      "layer": "Domain | Application | Infrastructure | Presentation",
      "responsibility": "Single responsibility description",
      "dependencies": ["Component1"],
      "interfaces": {
        "provided": ["IService"],
        "required": ["IRepository"]
      }
    }
  ],
  "data_flow": {
    "primary_flow": ["UI", "Controller", "Service", "Repository"],
    "events": ["UserCreated", "OrderPlaced"],
    "state_management": "Redux | Context | Server State"
  },
  "integration_points": [
    {
      "name": "External Payment API",
      "type": "API",
      "protocol": "REST",
      "error_handling": "Retry with exponential backoff"
    }
  ],
  "trade_offs": [
    {
      "decision": "Hexagonal over Layered",
      "pros": ["Testability", "Flexibility"],
      "cons": ["Initial complexity"]
    }
  ]
}
```

## Tactical Role Output

### Task Breakdown Output {#task-breakdown}

```json
{
  "phase_id": "PHASE-1",
  "tasks": [
    {
      "id": "TASK-1.1",
      "name": "Define User entity",
      "layer": "Domain",
      "tdd_phase": "RED | GREEN | REFACTOR",
      "description": "Task description",
      "deliverables": ["src/domain/entities/User.ts"],
      "acceptance_criteria": ["Criteria 1"],
      "dependencies": []
    }
  ],
  "execution_order": ["TASK-1.1", "TASK-1.2"],
  "parallel_groups": [
    {
      "tasks": ["TASK-1.4", "TASK-1.5"],
      "note": "Independent layers, parallelizable"
    }
  ],
  "layer_sequence": {
    "Domain": ["TASK-1.1"],
    "Application": ["TASK-1.2"],
    "Infrastructure": ["TASK-1.3"],
    "Presentation": ["TASK-1.4"]
  }
}
```

## Validator Role Output

### Validation Output {#validation}

```json
{
  "validation_summary": {
    "status": "PASS | FAIL | WARNING",
    "coverage_score": 95,
    "issues_found": 2,
    "critical_issues": 0
  },
  "coverage_analysis": {
    "prd_to_phase": {
      "total_requirements": 10,
      "covered": 9,
      "missing": ["REQ-007: Password reset"]
    },
    "phase_to_task": {
      "total_deliverables": 15,
      "covered": 15,
      "missing": []
    }
  },
  "dependency_analysis": {
    "circular_dependencies": [],
    "missing_dependencies": [],
    "critical_path_length": 12,
    "parallelization_opportunities": 3
  },
  "issues": [
    {
      "severity": "CRITICAL | ERROR | WARNING | INFO",
      "type": "MISSING_COVERAGE | CIRCULAR_DEP | ...",
      "description": "Issue description",
      "recommendation": "Suggested fix"
    }
  ]
}
```
