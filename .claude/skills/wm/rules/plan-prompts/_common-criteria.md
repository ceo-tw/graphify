---
title: Common Criteria Reference
type: reference
version: 1.0.0
---

# Common Criteria Reference

> Centralized criteria definitions for all roles

## Strategic Role Criteria

### Phase Decomposition

```xml
<phase_criteria>
1. Independently deployable
2. Clear goal and deliverables
3. Testable scope
4. Completable within 1-2 weeks
</phase_criteria>
```

### Dependency Types

```xml
<dependency_types>
- HARD: Must be completed first (e.g., Auth -> Authorization)
- SOFT: Preferred but parallelizable (e.g., UI -> API)
- NONE: Independent (e.g., Docs -> Implementation)
</dependency_types>
```

### Risk Categories

```xml
<risk_categories>
- Technical: Technical complexity, new technology adoption
- Resource: Personnel, time, tools
- External: External dependencies, third-party
- Integration: Existing system integration
</risk_categories>
```

## Architect Role Criteria

### Component Principles

```xml
<component_principles>
1. Single Responsibility Principle (SRP)
2. Interface Segregation Principle (ISP)
3. Dependency Inversion Principle (DIP)
4. Low coupling, high cohesion
</component_principles>
```

### Data Flow Patterns

```xml
<data_flow_patterns>
- Unidirectional: Unidirectional data flow (React, Redux)
- Event-Driven: Event-based communication
- Request-Response: Synchronous request/response
- Streaming: Real-time data streaming
</data_flow_patterns>
```

### Integration Types

```xml
<integration_types>
- API: REST, GraphQL, gRPC
- Message: Kafka, RabbitMQ, Redis Pub/Sub
- File: S3, File system
- Database: Direct connection, Views, Replicas
</integration_types>
```

## Tactical Role Criteria

### Task Criteria

```xml
<task_criteria>
1. Single concern (do one thing only)
2. Testable (verifiable result)
3. Completable within 30min-2hours
4. Clear completion criteria
</task_criteria>
```

### TDD Workflow

```xml
<tdd_workflow>
RED Phase:
  1. Write failing test
  2. Define interface

GREEN Phase:
  3. Minimal implementation to pass test
  4. Implement core logic

REFACTOR Phase:
  5. Code cleanup
  6. Performance optimization (if needed)
</tdd_workflow>
```

### Layer Order

```xml
<layer_order>
1. Domain: Entities, Value Objects, Domain Services
2. Application: Use Cases, App Services
3. Infrastructure: Repositories, External APIs
4. Presentation: UI Components, Pages
</layer_order>
```

## Validator Role Criteria

### Coverage Criteria

```xml
<coverage_criteria>
1. All PRD requirements mapped to PHASEs
2. All PHASE goals decomposed into Tasks
3. Test strategy exists for all Tasks
4. No missing requirements
</coverage_criteria>
```

### Dependency Rules

```xml
<dependency_rules>
1. No circular dependencies
2. All predecessor dependencies identified
3. Critical Path optimized
4. Parallelization opportunities maximized
</dependency_rules>
```

## Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| CRITICAL | Issue prevents plan execution | Fix immediately |
| ERROR | Serious gap or error | Fix before plan approval |
| WARNING | Potential issue or improvement needed | Review and decide |
| INFO | Informational recommendation | Optional implementation |
