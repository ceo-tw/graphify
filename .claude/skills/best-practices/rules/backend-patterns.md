# Backend Patterns

> Auto-loaded by dev-executor when backend domain is detected.

## Repository Pattern

Separate data access from business logic:

```typescript
// Repository: data access only
async function findUsersByTenant(tenantId: TenantId): Promise<User[]> {
  return sql`SELECT * FROM users WHERE tenant_id = ${tenantId}`
}

// Service: business logic
async function getActiveUsers(tenantId: TenantId): Promise<User[]> {
  const users = await findUsersByTenant(tenantId)
  return users.filter(u => u.status === 'active')
}
```

## Immutability

Never mutate objects directly:

```typescript
// BAD
user.status = 'active'

// GOOD
const updatedUser = { ...user, status: 'active' as const }
```

## N+1 Prevention

```typescript
// BAD: N queries in a loop
for (const user of users) {
  const orders = await sql`SELECT * FROM orders WHERE user_id = ${user.id}`
}

// GOOD: Single batch query
const userIds = users.map(u => u.id)
const orders = await sql`SELECT * FROM orders WHERE user_id = ANY(${userIds})`
```

## Error Handling

```typescript
// Centralized error handler in Hono
app.onError((err, c) => {
  if (err instanceof ValidationError) return c.json({ error: { code: 'VALIDATION_ERROR', message: err.message } }, 400)
  if (err instanceof AuthError) return c.json({ error: { code: 'UNAUTHORIZED', message: 'Authentication required' } }, 401)
  logger.error('Unhandled error', { error: err, path: c.req.path })
  return c.json({ error: { code: 'INTERNAL_ERROR', message: 'Internal server error' } }, 500)
})
```

## Caching (Redis Cache-Aside)

```typescript
async function getTenantSettings(tenantId: TenantId) {
  const cacheKey = `tenant:${tenantId}:settings`
  const cached = await redis.get(cacheKey)
  if (cached) return JSON.parse(cached)

  const settings = await sql`SELECT * FROM tenant_settings WHERE tenant_id = ${tenantId}`
  await redis.setex(cacheKey, 3600, JSON.stringify(settings))
  return settings
}

// Invalidate on write
async function updateTenantSettings(tenantId: TenantId, updates: Partial<Settings>) {
  await sql`UPDATE tenant_settings SET ... WHERE tenant_id = ${tenantId}`
  await redis.del(`tenant:${tenantId}:settings`)
}
```

## Transaction Boundaries

Use transactions for multi-step operations:

```typescript
await sql.begin(async (tx) => {
  const [account] = await tx`
    SELECT credits FROM accounts WHERE tenant_id = ${tenantId} FOR UPDATE
  `
  if (account.credits < amount) throw new Error('Insufficient credits')
  await tx`UPDATE accounts SET credits = credits - ${amount} WHERE tenant_id = ${tenantId}`
  await tx`INSERT INTO transactions (tenant_id, amount, type) VALUES (${tenantId}, ${amount}, 'debit')`
})
```

## Multi-Tenant RBAC

```typescript
// Middleware: extract tenant and verify role
app.use('/admin/*', async (c, next) => {
  const { activeTenantId, role } = c.get('auth')
  if (role !== 'admin') return c.json({ error: { code: 'FORBIDDEN' } }, 403)
  await next()
})
```
