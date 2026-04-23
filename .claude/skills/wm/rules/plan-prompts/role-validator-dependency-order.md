---
title: Dependency Order Validation
role: validator
type: role
priority: HIGH
---

# Dependency Order Validation

<role>Plan Validator</role>
<responsibility>Validate dependency order and identify optimization opportunities</responsibility>

## Instructions

<instructions>
Follow these steps for dependency order validation:

1. **Build Dependency Graph**
   - Collect all PHASE/Task dependencies
   - Represent as DAG (Directed Acyclic Graph)
   - Include both explicit and implicit dependencies

2. **Check for Circular Dependencies**
   - DFS-based cycle detection
   - Report discovered cycles in detail
   - Provide resolution suggestions

3. **Identify Missing Dependencies**
   - Analyze code/data dependencies
   - Review logical sequence relationships
   - Recommend missing dependencies

4. **Critical Path Analysis**
   - Calculate longest path
   - Identify bottleneck points
   - Analyze shortening opportunities

5. **Identify Parallelization Opportunities**
   - Find independent Task groups
   - Mark parallel execution sections
   - Consider resource constraints
</instructions>

## Dependency Types

<dependency_types>
**HARD (Strong Dependency)**
- Predecessor completion required
- Code, schema, interface dependencies
- Build/runtime error if violated

**SOFT (Weak Dependency)**
- Recommended but bypassable
- Can substitute with Mock
- Consider during parallel development

**INTEGRATION (Integration Dependency)**
- Individual development possible
- Required at integration point
- Separate integration Task recommended
</dependency_types>

## Output Format

<output_format>
Output fields: `dependency_validation` (status), `circular_dependency_check`, `missing_dependency_check`, `critical_path_analysis` (path, bottlenecks, optimization), `parallelization_analysis` (groups, efficiency), `recommendations[]`

> Full JSON example: `_output-formats.md#validation`
</output_format>

## Dependency Graph Visualization

<dependency_graph>
```
Example dependency graph:

PHASE-1 Tasks:
    +-----------+
    | TASK-1.1  | (User Entity Test)
    +-----+-----+
          |
          v
    +-----------+
    | TASK-1.2  | (User Entity Impl)
    +-----+-----+
          |
    +-----+-----+
    |           |
    v           v
+------+   +------+
|T-2.1 |   |T-2.4 |  (Parallelizable)
+--+---+   +--+---+
   |          |
   v          v
+------+   +------+
|T-2.2 |   |T-2.5 |
+--+---+   +--+---+
   |          |
   +----+-----+
        v
   +-----------+
   | TASK-2.3  | (AuthService - Bottleneck)
   +-----+-----+
         |
    +----+----+
    |         |
    v         v
+------+   +------+
|T-3.1 |   |T-3.4 |  (Parallelizable)
+------+   +------+
```
</dependency_graph>

## Validation Rules

<validation_rules>
**Circular Dependency Check**
```
Algorithm: DFS-based cycle detection

function hasCycle(node, visited, recStack):
    visited[node] = true
    recStack[node] = true

    for each neighbor of node:
        if not visited[neighbor]:
            if hasCycle(neighbor, visited, recStack):
                return true
        else if recStack[neighbor]:
            return true  // Cycle found

    recStack[node] = false
    return false
```

**Missing Dependency Check**
```
Check items:
1. File import relationships → Depends on file creation Task
2. Interface usage → Depends on interface definition Task
3. Data schema usage → Depends on schema definition Task
4. External service usage → Depends on service setup Task
```

**Critical Path Calculation**
```
Algorithm: Topological Sort + Longest Path

1. Determine execution order via topological sort
2. Calculate longest path to each node
3. Longest path = Critical Path
```
</validation_rules>

## Constraints

<constraints>
- Circular dependency found: CRITICAL (immediate resolution required)
- Missing HARD dependency found: ERROR
- Critical Path exceeds 80% of total Tasks: WARNING
- Parallelization efficiency below 50%: WARNING
</constraints>

## Efficiency Score Calculation

```
Parallelization efficiency score:

Efficiency = (Theoretical minimum time / Sequential execution time) × 100

Theoretical minimum time = Critical Path length
Sequential execution time = Sum of all Task times

Example:
- Total 20 Tasks, 1 hour each = 20 hours sequential
- Critical Path 8 Tasks = 8 hours theoretical minimum
- Efficiency = (8/20) × 100 = 40%

Grades:
- 80%+: Well optimized
- 60-79%: Good
- 40-59%: Needs improvement
- Below 40%: Severe bottleneck
```

## Common Issues and Solutions

```
Circular Dependency
   TASK-A → TASK-B → TASK-C → TASK-A

   Solutions:
   - Extract common dependency (TASK-Common)
   - Dependency inversion via interfaces
   - Redefine Task scope

Excessive Serialization
   All Tasks depend on previous Task

   Solutions:
   - Identify independent features
   - Parallelize by layer
   - Utilize Mocks

Hidden Dependencies
   Used in code but not explicitly declared

   Solutions:
   - Automate import analysis
   - Verify in code review
   - Enforce explicit dependency declaration
```

Reference: [Coverage Check](role-validator-coverage-check.md)
