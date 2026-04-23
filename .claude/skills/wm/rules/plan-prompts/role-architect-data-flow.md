---
title: Data Flow Design
role: architect
type: role
priority: HIGH
---

# Data Flow Design

<role>Software Architect</role>
<responsibility>Design data flow and state management strategy</responsibility>

## Instructions

<instructions>
Follow these steps when designing data flow:

1. **Analyze Current Data Flow**
   - Understand existing state management patterns
   - Identify data sources (API, DB, Local)
   - Confirm data transformation points

2. **Determine Data Flow Pattern**
   - Unidirectional vs Bidirectional
   - Synchronous vs Asynchronous
   - Push vs Pull

3. **Establish State Management Strategy**
   - Server state vs Client state
   - Global state vs Local state
   - Caching strategy

4. **Design Event Flow**
   - Define event types
   - Determine event handler location
   - Manage side effects

5. **Error Handling Flow**
   - Error propagation path
   - Recovery strategy
   - User feedback
</instructions>

## Data Flow Patterns

<data_flow_patterns>
**Unidirectional Data Flow**
```
┌───────────┐    Action    ┌───────────┐    State    ┌───────────┐
│   View    │ ───────────► │  Store    │ ───────────► │   View    │
│ (UI)      │              │ (Redux)   │              │ (Update)  │
└───────────┘              └───────────┘              └───────────┘
```
- Pros: Predictable, easy debugging
- Use: React, Redux, Flux

**Event-Driven**
```
┌───────────┐             ┌───────────┐             ┌───────────┐
│ Publisher │ ──Event──►  │ Event Bus │ ──Event──► │ Subscriber│
└───────────┘             └───────────┘             └───────────┘
```
- Pros: Loose coupling, scalability
- Use: Microservices, Real-time systems

**Request-Response**
```
┌───────────┐   Request   ┌───────────┐
│  Client   │ ───────────► │  Server   │
│           │ ◄─────────── │           │
└───────────┘   Response   └───────────┘
```
- Pros: Simple, synchronous processing
- Use: REST API, GraphQL
</data_flow_patterns>

## Output Format

<output_format>
Output fields: `current_state`, `data_flow_design` (pattern, rationale, primary_flow), `state_management` (server_state, client_state), `events[]`, `error_handling`

> Full JSON example: `_output-formats.md#component-design`
</output_format>

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                          │
│                                                                  │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐       │
│   │   Pages    │◄────►│   Hooks    │◄────►│   State    │       │
│   │            │      │            │      │ (Zustand)  │       │
│   └────────────┘      └─────┬──────┘      └────────────┘       │
│                             │                                    │
│                             ▼                                    │
│                      ┌────────────┐                             │
│                      │React Query │                             │
│                      │  (Cache)   │                             │
│                      └─────┬──────┘                             │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Server (API)                              │
│                                                                  │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐       │
│   │ Controller │─────►│  Service   │─────►│ Repository │       │
│   └────────────┘      └────────────┘      └─────┬──────┘       │
│                                                  │               │
└──────────────────────────────────────────────────┼───────────────┘
                                                   │
                                                   ▼
                                            ┌────────────┐
                                            │  Database  │
                                            └────────────┘
```

## Constraints

<constraints>
- Prioritize using existing state management tools
- Require clear rationale when introducing new state management tools
- Minimize global state (only when necessary)
- Clearly distinguish server state from client state
- Error handling required for all async operations
</constraints>

## State Classification

```
Server State
├── User data
├── Business data
├── Configuration data
└── → React Query, SWR, Apollo Client

Client State
├── UI state (modal, sidebar)
├── Form state (input values, validation)
├── Session state (auth tokens)
└── → Zustand, Jotai, Context
```

Reference: [React Best Practices](../../best-practices/rules/react-state-local.md)
