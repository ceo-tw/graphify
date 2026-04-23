---
title: Clean Architecture Reference
type: guide
impact: HIGH
used_by: [design, planner-task, dev-executor]
---

# Clean Architecture Reference

> **Purpose**: This document provides the canonical reference for Clean Architecture principles used by all planning and development agents.

---

## 1. 4-Layer Architecture

Clean Architecture separates concerns into 4 concentric layers. Inner layers are closer to business rules, outer layers are closer to the external world (UI, DB, frameworks).

```
+--------------------------------------------------+
|          Infrastructure Layer                     |
|  +--------------------------------------------+  |
|  |        Adapters Layer                      |  |
|  |  +--------------------------------------+  |  |
|  |  |     Application Layer                |  |  |
|  |  |  +--------------------------------+  |  |  |
|  |  |  |    Domain Layer                |  |  |  |
|  |  |  |  (Business Rules)              |  |  |  |
|  |  |  |  - Entities                    |  |  |  |
|  |  |  |  - Value Objects               |  |  |  |
|  |  |  |  - Domain Services             |  |  |  |
|  |  |  +--------------------------------+  |  |  |
|  |  |  - Use Cases                         |  |  |
|  |  |  - DTOs                              |  |  |
|  |  |  - Port Interfaces                   |  |  |
|  |  +--------------------------------------+  |  |
|  |  - Controllers                             |  |
|  |  - Presenters                              |  |
|  |  - Repository Implementations              |  |
|  +--------------------------------------------+  |
|  - Database Drivers                              |
|  - Web Frameworks                                |
|  - External APIs                                 |
+--------------------------------------------------+
```

### Layer 1: Domain (Core Business Logic)

**Responsibility**:
- Express core business rules
- Completely independent of external tech stack
- Most stable, least frequently changed area

**Components**:
- **Entities**: Core business objects (e.g., User, Order, Product)
- **Value Objects**: Immutable value objects (e.g., Email, Money, Address)
- **Domain Services**: Domain logic not belonging to entities
- **Domain Events**: Events occurring in domain

**Directory Structure Example**:
```
src/domain/
  entities/
    User.ts
    Order.ts
  value-objects/
    Email.ts
    Money.ts
  services/
    PricingService.ts
```

**Rules**:
- No external library imports (pure language features only)
- No Application/Adapters/Infrastructure layer references
- Only express business rules

### Layer 2: Application (Use Cases)

**Responsibility**:
- Orchestrate system Use Cases
- Implement business flow using Domain objects
- Define contracts with external world (Port Interfaces)

**Components**:
- **Use Cases**: Specific function implementation (e.g., CreateUserUseCase)
- **DTOs**: Data transfer objects (Input/Output)
- **Port Interfaces**: External dependency abstraction (Repository, Notification, etc.)

**Directory Structure Example**:
```
src/application/
  usecases/
    CreateUser.ts
    ProcessPayment.ts
  dtos/
    CreateUserDTO.ts
    PaymentDTO.ts
  ports/
    UserRepository.ts (interface)
    EmailService.ts (interface)
```

**Rules**:
- Only reference Domain layer
- Define Port Interfaces (implementation in Adapters)
- No Adapters/Infrastructure layer references
- No concrete tech stack dependency

### Layer 3: Adapters (Interface)

**Responsibility**:
- Implement Application's Ports
- Translation layer between external world and Application
- Controllers, Presenters, Repository implementations

**Components**:
- **Controllers**: HTTP request handling
- **Presenters**: Response format transformation
- **Repository Implementations**: Actual implementation of Port interfaces
- **Gateways**: External API integration

**Directory Structure Example**:
```
src/adapters/
  controllers/
    UserController.ts
  presenters/
    UserPresenter.ts
  repositories/
    UserRepositoryImpl.ts
  gateways/
    PaymentGateway.ts
```

**Rules**:
- Implement Application layer's Port interfaces
- Can reference Domain, Application layers
- Don't depend directly on Infrastructure details (use DI)

### Layer 4: Infrastructure (External Systems)

**Responsibility**:
- Actual tech stack implementation
- Database, web framework, external libraries
- Replaceable plugins

**Components**:
- **Database Drivers**: ORM setup, connection management
- **Web Frameworks**: Express, Fastify, etc. setup
- **External Services**: AWS SDK, payment SDK, etc.
- **Config**: Environment config, DI container setup

**Directory Structure Example**:
```
src/infrastructure/
  database/
    prisma.ts
    migrations/
  web/
    express-app.ts
  config/
    di-container.ts
  external/
    stripe-client.ts
```

**Rules**:
- Can reference all layers
- Actual tech stack implementation
- Replaceable (easy to change DB, framework)

---

## 2. Dependency Rule

**Core Principle**: Dependencies must always point **inward**.

```
Infrastructure  ->  Adapters  ->  Application  ->  Domain
(outer)                                            (inner)

Yes: Infrastructure can know Adapters
Yes: Adapters can know Application
Yes: Application can know Domain
No: Domain cannot know anything (completely independent)
```

### Dependency Inversion Principle

When outer layers need to provide functionality to inner layers, use **interfaces**.

```typescript
// Correct: Application defines Port interface
// src/application/ports/UserRepository.ts
export interface UserRepository {
  save(user: User): Promise<void>;
  findById(id: string): Promise<User | null>;
}

// src/application/usecases/CreateUser.ts
export class CreateUserUseCase {
  constructor(private userRepository: UserRepository) {} // Interface dependency

  async execute(dto: CreateUserDTO): Promise<User> {
    const user = User.create(dto);
    await this.userRepository.save(user);
    return user;
  }
}

// Adapters implements (dependency inversion)
// src/adapters/repositories/UserRepositoryImpl.ts
export class UserRepositoryImpl implements UserRepository {
  constructor(private prisma: PrismaClient) {} // Infrastructure dependency OK

  async save(user: User): Promise<void> {
    await this.prisma.user.create({ data: user.toJSON() });
  }
}

// Infrastructure injects
// src/infrastructure/config/di-container.ts
const userRepository = new UserRepositoryImpl(prismaClient);
const createUserUseCase = new CreateUserUseCase(userRepository);
```

---

## 3. Component Classification by Layer

| Component Type | Layer | Reason |
|----------------|-------|--------|
| **Entity** (User, Order) | Domain | Core business object |
| **Value Object** (Email, Money) | Domain | Immutable value with business rules |
| **Domain Service** (PricingService) | Domain | Domain logic not in entities |
| **Use Case** (CreateUser) | Application | System function orchestration |
| **DTO** (CreateUserDTO) | Application | Data transfer contract |
| **Port Interface** (UserRepository) | Application | External dependency abstraction |
| **Controller** (UserController) | Adapters | HTTP request handling |
| **Repository Impl** (UserRepositoryImpl) | Adapters | Port implementation |
| **Gateway** (PaymentGateway) | Adapters | External API integration |
| **ORM Config** (Prisma setup) | Infrastructure | Tech stack setup |
| **Web Framework** (Express setup) | Infrastructure | Framework bootstrap |
| **DI Container** | Infrastructure | Dependency assembly |

---

## 4. Task Order Guide (Domain First)

Following Clean Architecture, **implement from inner layers first**.

### Implementation Order

```
STEP 1: Domain Layer
    - Entity, Value Object, Domain Service

STEP 2: Application Layer
    - Use Case, DTO, Port Interface

STEP 3: Adapters Layer
    - Controller, Repository Impl, Gateway

STEP 4: Infrastructure Layer
    - DI Container, Framework Setup
```

### Layer Dependency Rules

```
Yes: TASK-007 (Application) can start after PHASE 1 (Domain) complete
Yes: TASK-011 (Adapters) can start after PHASE 2 (Application) complete
No: TASK-007 (Application) cannot start before TASK-001 (Domain) complete
```

---

## 5. Agent Usage Guide

### design Agent

**Design verification checklist**:
- [ ] Components placed in correct layers?
- [ ] Dependencies point inward?
- [ ] Port interfaces defined in Application?
- [ ] Infrastructure is replaceable?

### planner-task Agent

**Task decomposition checklist**:
- [ ] Domain layer Tasks are first priority?
- [ ] Application Tasks start after Domain complete?
- [ ] Adapters Tasks start after Application complete?
- [ ] Each Task follows layer dependency rules?

### dev-executor Agent

**Implementation verification**:
- [ ] Domain files have no external library imports
- [ ] Application uses only Port interfaces
- [ ] Adapters implement Ports
- [ ] Infrastructure assembles with DI

---

## 6. FAQ

### Q1: Are all 4 layers needed for every project?

**A**: No. Adjust based on project scale.

- **Small project**: Domain + Application layers only
- **Medium project**: Domain + Application + Adapters (Infrastructure merged into Adapters)
- **Large project**: Full 4-layer separation

**Key principle**: Even if layers are reduced, **dependencies must point inward**.

### Q2: Where to place Shared Kernel?

**A**: Domain layer or separate common module.

```
src/
  shared/ (or common/)
    Result.ts (common result type)
    DomainEvent.ts (event base)
    ValueObject.ts (VO base class)
  domain/
    entities/
  application/
```

**Rule**: Shared Kernel is part of Domain layer - no external dependencies.

---

## 7. Layer Inference Patterns

> Automatic Clean Architecture layer inference from file path.

### Frontend Project (Next.js/React)

| Path Pattern | Layer | Description | Example |
|--------------|-------|-------------|---------|
| `/types/`, `/entities/`, `/models/` | domain | Type definitions, entities | `src/types/user.ts` |
| `/lib/services/`, `/hooks/`, `/utils/` | application | Business logic, utilities | `src/lib/services/auth.ts` |
| `/components/`, `/pages/`, `/app/` | adapters | UI components, pages | `src/components/Button.tsx` |
| `/config/`, `/providers/`, `/middleware/` | infrastructure | Config, framework integration | `src/providers/theme.tsx` |
| `/__tests__/`, `.test.`, `.spec.` | (test) | Inherits layer from corresponding source | `components/__tests__/` → adapters |

### Backend Project (General)

| Path Pattern | Layer | Description |
|--------------|-------|-------------|
| `/domain/`, `/entities/` | domain | Domain models |
| `/application/`, `/usecases/` | application | Use cases |
| `/adapters/`, `/controllers/`, `/repositories/` | adapters | Adapter implementations |
| `/infrastructure/`, `/config/` | infrastructure | Infrastructure |

### Inference Priority

1. **Explicit path matching**: Matches patterns in tables above
2. **Filename hint**: `.entity.ts` → domain, `.controller.ts` → adapters
3. **Default**: Frontend → adapters, Backend → application

### Layer Inference Examples

```
dashboard/src/components/monitoring/monitoring-page-client.tsx
→ /components/ matches → Layer: adapters

dashboard/src/lib/services/team-scores/index.ts
→ /lib/services/ matches → Layer: application

dashboard/src/types/evaluation.ts
→ /types/ matches → Layer: domain

dashboard/src/app/(dashboard)/monitoring/page.tsx
→ /app/ matches → Layer: adapters (page component)

dashboard/src/config/db.ts
→ /config/ matches → Layer: infrastructure
```

### Usage Example (Code)

```python
def infer_layer(file_path: str, project_type: str = "frontend") -> str:
    """Infer Clean Architecture Layer from file path"""

    # Frontend patterns
    if project_type == "frontend":
        patterns = {
            "domain": ["/types/", "/entities/", "/models/"],
            "application": ["/lib/services/", "/hooks/", "/utils/"],
            "adapters": ["/components/", "/pages/", "/app/"],
            "infrastructure": ["/config/", "/providers/", "/middleware/"]
        }
    else:
        # Backend patterns
        patterns = {
            "domain": ["/domain/", "/entities/"],
            "application": ["/application/", "/usecases/"],
            "adapters": ["/adapters/", "/controllers/", "/repositories/"],
            "infrastructure": ["/infrastructure/", "/config/"]
        }

    for layer, layer_patterns in patterns.items():
        for pattern in layer_patterns:
            if pattern in file_path:
                return layer

    # Default
    return "adapters" if project_type == "frontend" else "application"
```
