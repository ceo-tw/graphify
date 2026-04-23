---
title: Layer Inference
role: tactical
type: role
priority: MEDIUM
---

# Layer Inference

<role>Tactical Planner</role>
<responsibility>Infer layer structure from functional requirements and determine implementation order</responsibility>

## Instructions

<instructions>
Follow these steps when inferring layers:

1. **Analyze Feature**
   - Identify data/entities the feature handles
   - Identify business rules
   - Confirm external system integration needs

2. **Map to Layers**
   - Place each element in appropriate layer
   - Define layer boundaries clearly
   - Verify dependency direction (always inward)

3. **Determine Implementation Order**
   - Start from Domain layer
   - Expand to outer layers
   - Follow dependency direction

4. **Define Interfaces**
   - Identify inter-layer interfaces
   - Specify contracts
   - Apply Ports and Adapters pattern

5. **Validate**
   - Confirm no circular dependencies
   - Confirm no layer violations
   - Verify Clean Architecture principles
</instructions>

## Layer Definition

<layer_definition>
```
┌─────────────────────────────────────────────────────────────────┐
│                         Layers Overview                          │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   PRESENTATION LAYER                       │  │
│  │  • UI Components, Pages                                    │  │
│  │  • Controllers, API Routes                                 │  │
│  │  • View Models, Presenters                                 │  │
│  │  • Depends on: Application                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    APPLICATION LAYER                       │  │
│  │  • Use Cases, Application Services                         │  │
│  │  • DTOs (Data Transfer Objects)                           │  │
│  │  • Command/Query Handlers                                  │  │
│  │  • Depends on: Domain                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      DOMAIN LAYER                          │  │
│  │  • Entities, Value Objects                                 │  │
│  │  • Domain Services                                         │  │
│  │  • Repository Interfaces (Ports)                          │  │
│  │  • Depends on: Nothing (independent)                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            ▲                                     │
│                            │ implements                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  INFRASTRUCTURE LAYER                      │  │
│  │  • Repository Implementations (Adapters)                   │  │
│  │  • External API Clients                                    │  │
│  │  • Database Access, ORM                                    │  │
│  │  • Depends on: Domain (interface implementation)           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
</layer_definition>

## Output Format

<output_format>
Output fields: `feature`, `layer_analysis` (domain, application, infrastructure, presentation), `implementation_order[]` (phase, layer, tasks, rationale)

> Full JSON example: `_output-formats.md#task-breakdown`
</output_format>

## Layer Inference Rules

<inference_rules>
**Keyword-based Layer Inference**

| Keyword | Layer | Example |
|---------|-------|---------|
| Entity, Model, Aggregate | Domain | User, Order, Product |
| Value Object | Domain | Email, Money, Address |
| Repository Interface | Domain | IUserRepository |
| Use Case, Service | Application | RegisterUserUseCase |
| DTO, Command, Query | Application | CreateUserDto |
| Repository Impl | Infrastructure | PrismaUserRepository |
| API Client | Infrastructure | StripeClient |
| Controller, Handler | Presentation | AuthController |
| Component, Page | Presentation | LoginForm, HomePage |

**Dependency Direction Rules**

```
Presentation → Application → Domain ← Infrastructure
                                  │
                                  └─ (implements relationship)

✅ OK: Presentation uses Application
✅ OK: Application uses Domain
✅ OK: Infrastructure implements Domain interface
❌ NO: Domain uses Infrastructure
❌ NO: Application uses Presentation
```
</inference_rules>

## Constraints

<constraints>
- Domain layer NEVER depends on other layers
- Infrastructure implements Domain interfaces only
- Presentation uses Application layer directly only
- No layer skipping (Presentation → Domain directly not allowed)
- Maintain hierarchy within each layer
</constraints>

## Common Patterns

```
Feature: User Order

Domain Layer:
  └── Order (Entity)
  └── OrderItem (Entity)
  └── Money (Value Object)
  └── IOrderRepository (Interface)

Application Layer:
  └── CreateOrderUseCase
  └── CreateOrderDto
  └── OrderResponseDto

Infrastructure Layer:
  └── PrismaOrderRepository (implements IOrderRepository)
  └── PaymentGatewayClient

Presentation Layer:
  └── OrderController
  └── OrderForm (Component)
  └── CheckoutPage (Page)
```

## Layer Violation Examples

```
❌ Domain → Infrastructure dependency
class User {
  constructor(private prisma: PrismaClient) {}  // Wrong!
}

✅ Correct approach: Use interface
// Domain
interface IUserRepository { save(user: User): Promise<void> }

// Infrastructure
class PrismaUserRepository implements IUserRepository { }


❌ Presentation → Domain direct access
// In React Component
const user = new User(email, password);  // Wrong!
await prismaClient.user.create(user);

✅ Correct approach: Go through Application layer
const useCase = new RegisterUserUseCase(repository);
const result = await useCase.execute(dto);
```

Reference: [Component Design](role-architect-component-design.md)
