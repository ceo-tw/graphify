---
title: Integration Points
role: architect
type: role
priority: MEDIUM
---

# Integration Points

<role>Software Architect</role>
<responsibility>Define and design inter-system integration points</responsibility>

## Instructions

<instructions>
Follow these steps when designing integration points:

1. **Identify Integration Targets**
   - Internal system integrations
   - External service integrations
   - Legacy system integrations

2. **Determine Integration Types**
   - Synchronous vs Asynchronous
   - Point-to-Point vs Message Broker
   - Pull vs Push

3. **Define Interface Contracts**
   - API specs (OpenAPI, gRPC)
   - Message schemas
   - Error code system

4. **Apply Resilience Patterns**
   - Circuit Breaker
   - Retry with Backoff
   - Timeout settings
   - Fallback strategy

5. **Monitoring and Observability**
   - Health checks
   - Metrics collection
   - Distributed tracing
</instructions>

## Integration Types

<integration_types>
**API Integration (REST/GraphQL)**
```
┌──────────┐     HTTP/HTTPS     ┌──────────┐
│  Client  │ ────────────────► │  Server  │
│          │ ◄──────────────── │          │
└──────────┘     JSON/XML       └──────────┘
```
- Use: Synchronous request-response
- Pros: Simple, standardized
- Cons: Tight coupling, synchronous wait

**Message Queue Integration**
```
┌──────────┐              ┌──────────┐              ┌──────────┐
│ Producer │ ──Message──► │  Queue   │ ──Message──► │ Consumer │
└──────────┘              │ (Kafka)  │              └──────────┘
                          └──────────┘
```
- Use: Async processing, event propagation
- Pros: Loose coupling, scalability
- Cons: Complexity, eventual consistency

**Webhook Integration**
```
┌──────────┐     Register      ┌──────────┐
│ Receiver │ ────────────────► │ Provider │
│          │ ◄──────────────── │          │
└──────────┘   Callback (POST)  └──────────┘
```
- Use: Event notifications
- Pros: Real-time, server push
- Cons: Delivery guarantee difficult

**gRPC Integration**
```
┌──────────┐    Protocol Buffers    ┌──────────┐
│  Client  │ ─────────────────────► │  Server  │
│ (Stub)   │ ◄───────────────────── │          │
└──────────┘                        └──────────┘
```
- Use: High performance, microservices
- Pros: Type-safe, performant
- Cons: Limited browser support
</integration_types>

## Output Format

<output_format>
Output fields: `integration_points[]` (id, name, type, direction, provider, protocol, authentication, contract, resilience, error_handling, monitoring, testing), `shared_concerns`

> Full JSON example: `_output-formats.md#component-design`
</output_format>

## Integration Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Our System                                  │
│                                                                  │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐       │
│   │   Order    │      │  Payment   │      │   Notif    │       │
│   │  Service   │─────►│  Service   │─────►│  Service   │       │
│   └────────────┘      └─────┬──────┘      └─────┬──────┘       │
│                             │                   │                │
└─────────────────────────────┼───────────────────┼────────────────┘
                              │                   │
            ┌─────────────────┼───────────────────┼────────────────┐
            │                 ▼                   ▼                │
            │    ┌────────────────┐    ┌────────────────┐         │
            │    │     Stripe     │    │     Kafka      │         │
            │    │   (Payment)    │    │   (Message)    │         │
            │    └────────────────┘    └───────┬────────┘         │
            │                                  │                   │
            │    ┌────────────────┐            │                   │
            │    │    SendGrid    │◄───────────┘                   │
            │    │    (Email)     │                                │
            │    └────────────────┘                                │
            │                                                      │
            │              External Services                       │
            └──────────────────────────────────────────────────────┘
```

## Resilience Patterns

<resilience_patterns>
**Circuit Breaker**
```typescript
class CircuitBreaker {
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  private failureCount = 0;
  private lastFailureTime: Date | null = null;

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (this.shouldAttemptReset()) {
        this.state = 'HALF_OPEN';
      } else {
        throw new CircuitOpenError();
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
}
```

**Retry with Exponential Backoff**
```typescript
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      const delay = baseDelay * Math.pow(2, attempt);
      await sleep(delay + Math.random() * 1000);
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Timeout with Fallback**
```typescript
async function withTimeoutAndFallback<T>(
  fn: () => Promise<T>,
  timeout: number,
  fallback: T
): Promise<T> {
  try {
    return await Promise.race([
      fn(),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new TimeoutError()), timeout)
      )
    ]);
  } catch (error) {
    console.warn('Using fallback due to:', error);
    return fallback;
  }
}
```
</resilience_patterns>

## Constraints

<constraints>
- Timeout required for all external integrations (default 30 seconds)
- Apply exponential backoff to retry logic
- Apply Circuit Breaker or Bulkhead patterns
- Specify idempotency requirements where needed
- Graceful degradation when external services fail
</constraints>

## Security Considerations

```
✅ Authentication/Authorization
   - API Key rotation plan
   - OAuth token refresh logic
   - Principle of least privilege

✅ Data Protection
   - TLS/HTTPS required
   - Sensitive data masking
   - Audit logging

✅ Input Validation
   - External response validation
   - Schema validity check
   - Malicious payload defense
```

Reference: [Error Handling](../../best-practices/rules/ts-error-custom-types.md)
