# Phase Planning Guide

> **Source**: Migrated from `planning-guide-for-phase/SKILL.md`
> **Purpose**: Guidelines for creating PHASE-level strategic plans.
> **Used by**: wm (Plan Writing)

---

## PHASE Definition

A PHASE is a high-level unit of work with these characteristics:

| Attribute | Requirement |
|-----------|-------------|
| Duration | 1-4 hours |
| Verifiable | Independently testable and demonstrable |
| Deliverable | Clear working functionality |
| Rollback | Can be reverted independently |

## PHASE Decomposition Guidelines

### Number of PHASEs

- **Minimum**: 3 PHASEs
- **Maximum**: 7 PHASEs
- **Optimal**: 4-5 PHASEs for most features

### Decomposition Strategy

1. **Identify Core Value**
   - What is the minimum viable implementation?
   - This becomes PHASE 1

2. **Layer by Functionality**
   - Group related functionality
   - Each PHASE adds complete, testable features

3. **Consider Dependencies**
   - PHASEs with shared dependencies → sequential
   - Independent PHASEs → can be parallelized (v2)

### PHASE Types

| Type | Description | Example |
|------|-------------|---------|
| Foundation | Core entities, base structure | Domain models, DB schema |
| Feature | User-facing functionality | CRUD operations, UI |
| Integration | External connections | API integrations, auth |
| Polish | Quality improvements | Performance, UX |

## Clean Architecture Integration

Apply Clean Architecture principles when decomposing PHASEs:

### Layer-based PHASE Order

```
PHASE 1: Domain Layer
├── Entities, Value Objects
├── Domain Services
└── Repository Interfaces (Ports)

PHASE 2: Application Layer
├── Use Cases
├── Application Services
└── DTOs

PHASE 3: Adapters Layer
├── Controllers
├── Repository Implementations
└── External Service Adapters

PHASE 4: Infrastructure Layer
├── Framework Configuration
├── Database Setup
└── External API Clients
```

### Dependency Rule

| Layer | May Depend On | Must Not Depend On |
|-------|---------------|-------------------|
| Domain | Nothing | Application, Adapters, Infrastructure |
| Application | Domain | Adapters, Infrastructure |
| Adapters | Application, Domain | Infrastructure |
| Infrastructure | All layers | - |

### Code Placement Decision

| Question | Yes → | No → |
|----------|-------|------|
| Meaningful without framework? | Domain/Application | Adapters/Infrastructure |
| Reusable across applications? | Domain | Application |
| Communicates with external system? | Adapters | Inner layers |
| Depends on specific technology? | Infrastructure | Inner layers |

## Quality Gates

Each PHASE must satisfy before proceeding:

### Build Quality Gate
- [ ] Project builds without errors
- [ ] No syntax or compilation errors

### Test Quality Gate
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Unit test coverage ≥80% for business logic

### Code Quality Gate
- [ ] Linting passes
- [ ] Type checking passes
- [ ] No console.log or debug statements

### Functional Quality Gate
- [ ] Feature works as specified
- [ ] No regressions in existing features
- [ ] Edge cases handled

## TDD Integration

Each PHASE follows the TDD (Test-Driven Development) workflow:

### Red-Green-Refactor Cycle

```
Phase N: PHASE Name
├── 🔴 RED: Write Failing Tests First
│   ├── Write unit tests for target functionality
│   ├── Run tests → FAILS (expected)
│   └── Commit: "Add failing test for X"
│
├── 🟢 GREEN: Implement to Make Tests Pass
│   ├── Write minimal code to pass tests
│   ├── Run tests → PASSES
│   └── Commit: "Implement X to pass tests"
│
└── 🔵 REFACTOR: Clean Up Code
    ├── Improve code quality
    ├── Run tests → STILL PASSES
    └── Commit: "Refactor X for better design"
```

### Test Types per PHASE

| PHASE Type | Unit Tests | Integration Tests | E2E Tests |
|------------|-----------|------------------|-----------|
| Foundation | ≥80% | Critical paths | - |
| Feature | ≥80% | Component flow | Key flows |
| Integration | ≥70% | External APIs | - |
| Polish | Maintain | Maintain | Full journey |

## Templates

Load the templates below using Read tool when generating documents:

- [PRD Template](template-prd.md) - Use when generating PLAN document
- [Rollback Template](template-rollback.md) - Use when writing rollback strategy for each PHASE
- [Quality Gate Template](template-quality-gate.md) - PHASE quality gate checklist

## Technology-Specific References

Additional references by project type:

- **Frontend (React/Next.js)**: `guide-frontend.md`
  - Frontend PHASE decomposition guide
  - Layer Mapping (Clean → Frontend)
  - UI component rules, file length limits

- **Backend**: `guide-clean-architecture.md` (default)

## Decision Points

When uncertain about PHASE scope, invoke question agent:

```python
Task(
    subagent_type="question",
    prompt="""
    Planning Decision Needed:

    Context: {current_state}
    Options:
    1. {option_1}
    2. {option_2}

    Need user input to decide.
    """,
    model="opus"
)
```

## Common Anti-patterns

| Anti-pattern | Better Approach |
|--------------|-----------------|
| Too large PHASE (>4h) | Split into smaller PHASEs |
| Too small PHASE (<1h) | Combine with related work |
| Unclear deliverable | Define specific outcome |
| Hidden dependencies | Document all prerequisites |
| No rollback plan | Always define revert steps |
