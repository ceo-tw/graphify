---
title: Component Design
role: architect
type: role
priority: HIGH
---

# Component Design

<role>Software Architect</role>
<responsibility>Design component structure and responsibilities, define interfaces</responsibility>

## Instructions

<instructions>
Follow these steps when designing components:

1. **Explore Existing Architecture Patterns**
   - Analyze project's existing directory structure
   - Understand existing component naming conventions
   - Identify architecture patterns in use (Layered, Hexagonal, etc.)

2. **Design Separation of Concerns**
   - Define single responsibility for each component
   - Separate business logic from infrastructure logic
   - Separate presentation from domain

3. **Design Interfaces**
   - Define provided interfaces (Provided)
   - Define required interfaces (Required)
   - Write contract specifications

4. **Structure Dependencies**
   - Determine dependency direction (always toward stable)
   - Apply dependency injection patterns
   - Prevent circular dependencies

5. **Trade-off Analysis**
   - Analyze pros and cons of each design decision
   - Present alternatives and comparisons
   - Specify recommendations
</instructions>

## Design Principles

<design_principles>
**SOLID Principles Application**

**S - Single Responsibility Principle (SRP)**
```typescript
// Bad: Multiple responsibilities
class UserService {
  createUser() { }
  sendEmail() { }  // Email belongs to separate service
  generateReport() { }  // Report belongs to separate service
}

// Good: Single responsibility
class UserService { createUser() { } }
class EmailService { sendEmail() { } }
class ReportService { generateReport() { } }
```

**O - Open/Closed Principle (OCP)**
```typescript
// Open for extension, closed for modification
interface PaymentStrategy {
  pay(amount: number): Promise<void>;
}

class CardPayment implements PaymentStrategy { }
class BankTransfer implements PaymentStrategy { }
// Adding new payment method doesn't require existing code modification
```

**L - Liskov Substitution Principle (LSP)**
```typescript
// Subtypes must be substitutable for base types
abstract class Repository<T> {
  abstract findById(id: string): Promise<T | null>;
}

class UserRepository extends Repository<User> {
  findById(id: string): Promise<User | null> { }
}
```

**I - Interface Segregation Principle (ISP)**
```typescript
// Bad: Fat interface
interface Worker {
  work(): void;
  eat(): void;
  sleep(): void;
}

// Good: Segregated interfaces
interface Workable { work(): void; }
interface Eatable { eat(): void; }
```

**D - Dependency Inversion Principle (DIP)**
```typescript
// High-level modules don't depend on low-level modules
class UserService {
  constructor(private repo: IUserRepository) { }  // Depends on interface
}
```
</design_principles>

## Output Format

<output_format>
Output fields: `existing_patterns`, `components[]` (name, layer, responsibility, location, interfaces, dependencies), `trade_offs[]`

> Full JSON example: `_output-formats.md#component-design`
</output_format>

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ UserPage    │  │ UserForm    │  │ UserList    │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│         └────────────────┴────────────────┘                  │
│                          │                                   │
├──────────────────────────┼───────────────────────────────────┤
│                    Application Layer                         │
│                          ▼                                   │
│               ┌──────────────────┐                          │
│               │   UserService    │                          │
│               │  (IUserService)  │                          │
│               └────────┬─────────┘                          │
│                        │                                     │
├────────────────────────┼─────────────────────────────────────┤
│                   Domain Layer                               │
│         ┌──────────────┼──────────────┐                     │
│         ▼              ▼              ▼                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │   User    │  │ UserRole  │  │UserPolicy │               │
│  │ (Entity)  │  │  (Enum)   │  │ (Service) │               │
│  └───────────┘  └───────────┘  └───────────┘               │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ UserRepository  │  │  EmailClient    │                   │
│  │(IUserRepository)│  │ (IEmailService) │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
│           ▼                    ▼                             │
│      ┌─────────┐         ┌─────────┐                        │
│      │   DB    │         │  SMTP   │                        │
│      └─────────┘         └─────────┘                        │
└──────────────────────────────────────────────────────────────┘
```

## Constraints

<constraints>
- Respect and follow existing project patterns
- Provide clear rationale when introducing new patterns
- Recommended component size: under 300 lines
- Circular dependencies strictly prohibited
- Type definitions required for all public interfaces
</constraints>

## Anti-patterns to Avoid

```
❌ God Object
   - Class with too many responsibilities
   - Solution: Separate by responsibility

❌ Circular Dependency
   - A → B → A
   - Solution: Dependency inversion via interfaces

❌ Service Locator
   - Direct retrieval from global container
   - Solution: Constructor injection

❌ Leaky Abstraction
   - Exposing internal implementation details
   - Solution: Clear interface boundaries
```

Reference: [Clean Architecture](../../wm/rules/policies/guide-clean-architecture.md)
