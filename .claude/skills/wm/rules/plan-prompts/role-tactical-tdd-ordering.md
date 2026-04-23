---
title: TDD Ordering
role: tactical
type: role
priority: HIGH
---

# TDD Ordering

<role>Tactical Planner</role>
<responsibility>Order Tasks according to TDD workflow (RED→GREEN→REFACTOR)</responsibility>

## Instructions

<instructions>
Follow these steps when applying TDD ordering:

1. **Identify Test Targets**
   - Confirm list of features to implement
   - Define testable behaviors for each feature
   - Identify edge cases

2. **Design RED Phase**
   - Write failing tests first
   - Clarify why tests fail
   - Define interfaces/contracts

3. **Design GREEN Phase**
   - Minimal implementation to pass tests
   - "Just make it work"
   - Avoid complex optimizations

4. **Design REFACTOR Phase**
   - Improve code quality
   - Remove duplication
   - Enhance clarity
   - Confirm tests still pass

5. **Repeat Cycle**
   - Move to next feature
   - Maintain entire test suite
</instructions>

## TDD Workflow

<tdd_workflow>
```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD Development Cycle                         │
│                                                                  │
│  1. RED (Failing Test)                                          │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ • Write test before implementation                       │ │
│     │ • Run test → Confirm failure (red)                       │ │
│     │ • Verify test fails for correct reason                   │ │
│     │ • Define interface and expected behavior                 │ │
│     └─────────────────────────────────────────────────────────┘ │
│                            │                                     │
│                            ▼                                     │
│  2. GREEN (Test Passes)                                         │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ • Write minimal code to pass test                        │ │
│     │ • Use "fastest way to pass"                              │ │
│     │ • Prioritize working code over perfection                │ │
│     │ • Hard-coding OK (temporarily)                           │ │
│     └─────────────────────────────────────────────────────────┘ │
│                            │                                     │
│                            ▼                                     │
│  3. REFACTOR (Code Improvement)                                 │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ • Remove duplication                                     │ │
│     │ • Use clear names                                        │ │
│     │ • Apply design patterns                                  │ │
│     │ • Run tests after each change → Confirm pass            │ │
│     └─────────────────────────────────────────────────────────┘ │
│                            │                                     │
│                            └──────────► Return to 1 (next func)  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
</tdd_workflow>

## Output Format

<output_format>
Output fields: `feature`, `tdd_cycles[]` (cycle, target, red, green, refactor), `test_pyramid`, `execution_order[]`

> Full JSON example: `_output-formats.md#task-breakdown`
</output_format>

## TDD Rules

<tdd_rules>
**Rules to Always Follow**

1. **Test First**
   - Write tests before implementation code
   - Confirm tests fail before implementing

2. **One at a Time**
   - Add only one test at a time
   - Pass that test before moving to next

3. **Minimal Implementation**
   - Do NOT write "good enough" code in GREEN phase
   - Minimal code only to pass tests

4. **Refactoring Discipline**
   - Refactor only when tests pass
   - No new features during refactoring
   - Run tests after each change

5. **Tests are Code**
   - Test code is also subject to refactoring
   - Remove test duplication
   - Maintain readable tests
</tdd_rules>

## Constraints

<constraints>
- Test Task required before all implementation Tasks
- No excessive design in GREEN phase
- No new features in REFACTOR phase
- Test coverage target: 80% or higher
- Each TDD cycle completable within 1-2 hours
</constraints>

## Common Mistakes

```
❌ Implementation without tests
   "Just implement first, test later"
   → Always test first

❌ Too large RED phase
   "All test cases at once"
   → One test at a time

❌ Seeking perfection in GREEN
   "Might as well do it all now"
   → Minimal implementation, REFACTOR later

❌ Skipping REFACTOR
   "It works, that's enough"
   → Required to prevent technical debt

❌ Refactoring when tests pass
   "This part could be better too"
   → Start new RED cycle
```

## Test Types by Phase

```
Test types per TDD cycle:

Domain Layer (Unit Tests)
├── Entity tests
├── Value Object tests
└── Domain Service tests

Application Layer (Unit + Integration)
├── Use Case tests
├── Service tests (mocked dependencies)
└── Integration tests (real dependencies)

Infrastructure Layer (Integration)
├── Repository tests (test DB)
└── External API tests (mocked/sandbox)

Presentation Layer (Component + E2E)
├── Component tests
├── Page tests
└── E2E tests
```

Reference: [Layer Inference](role-tactical-layer-inference.md)
