---
title: Backend Development Reference
type: guide
impact: HIGH
used_by: [design, planner-task, dev-executor, bug-fixer]
domain: backend
---

# Backend Development Reference

> **Purpose**: Essential principles for /planner workflow in TypeScript backend projects
> **Scope**: Generic patterns for backend services, adaptable to project-specific needs

---

## 1. TypeScript Configuration (Required)

### 1.1 Strict Mode

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true
  }
}
```

### 1.2 Path Aliases

```typescript
// Correct usage
import { ClickHouseClient } from "@/lib/db/clickhouse";
import { JsonlRecord } from "@claude-monitoring/jsonl-types";

// Prohibited: Relative imports for shared modules
import { JsonlRecord } from "../../../packages/jsonl-types";
```

---

## 2. Zod Schema Validation (Required)

### 2.1 Schema Definition Pattern

```typescript
// src/lib/services/{domain}/validator.ts
import { z } from "zod";

// Raw input schema
export const RawRecordSchema = z.object({
  uuid: z.string().uuid(),
  sessionId: z.string(),
  timestamp: z.string().datetime(),
  // ... other fields
});

// Normalized output schema
export const NormalizedRecordSchema = RawRecordSchema.extend({
  normalized_at: z.string().datetime(),
  pii_masked: z.boolean().default(false),
});

export type RawRecord = z.infer<typeof RawRecordSchema>;
export type NormalizedRecord = z.infer<typeof NormalizedRecordSchema>;
```

### 2.2 Validation Usage

```typescript
// Always validate at API boundaries
export async function POST(request: Request) {
  const body = await request.json();

  // Parse and validate
  const result = RawRecordSchema.safeParse(body);

  if (!result.success) {
    return Response.json({
      success: false,
      errors: result.error.flatten(),
    }, { status: 400 });
  }

  const validated = result.data;
  // ... process validated data
}
```

### 2.3 Schema Transformation

```typescript
// Use transform for normalization
const NormalizeSchema = RawRecordSchema.transform((data) => ({
  ...data,
  session_id: data.sessionId,  // camelCase to snake_case
  timestamp: new Date(data.timestamp).toISOString(),
}));
```

---

## 3. Error Handling Patterns (Required)

### 3.1 Try-Catch Pattern

```typescript
// Service layer error handling
export async function processRecords(records: RawRecord[]): Promise<ProcessResult> {
  try {
    const normalized = await normalizeAll(records);
    const inserted = await insertBatch(normalized);

    return {
      success: true,
      processed: inserted.count,
      failed: 0,
    };
  } catch (error) {
    // Log structured error
    console.error("[processRecords] Failed:", {
      recordCount: records.length,
      error: error instanceof Error ? error.message : String(error),
    });

    throw new ProcessingError("Failed to process records", { cause: error });
  }
}
```

### 3.2 Custom Error Classes

```typescript
// src/lib/errors/index.ts
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    options?: ErrorOptions
  ) {
    super(message, options);
    this.name = this.constructor.name;
  }
}

export class ValidationError extends AppError {
  constructor(message: string, options?: ErrorOptions) {
    super(message, "VALIDATION_ERROR", 400, options);
  }
}

export class DatabaseError extends AppError {
  constructor(message: string, options?: ErrorOptions) {
    super(message, "DATABASE_ERROR", 500, options);
  }
}
```

### 3.3 API Error Response Format

```typescript
// Consistent error response
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

// Usage in route handler
catch (error) {
  if (error instanceof ValidationError) {
    return Response.json({
      success: false,
      error: {
        code: error.code,
        message: error.message,
      },
    }, { status: 400 });
  }

  // Default 500 error
  return Response.json({
    success: false,
    error: {
      code: "INTERNAL_ERROR",
      message: "An unexpected error occurred",
    },
  }, { status: 500 });
}
```

---

## 4. Logging Standards (Required)

### 4.1 Structured Logging

```typescript
// Use structured log format
console.log("[ServiceName] Action:", {
  action: "insertBatch",
  recordCount: records.length,
  duration: endTime - startTime,
});

// Error logging with context
console.error("[ServiceName] Error:", {
  action: "insertBatch",
  error: error.message,
  stack: error.stack,
  context: { recordCount, batchId },
});
```

### 4.2 Log Levels

| Level | Use Case |
|-------|----------|
| `console.log` | General information, success |
| `console.warn` | Recoverable issues, deprecation |
| `console.error` | Errors, failures |
| `console.debug` | Development debugging (use sparingly) |

---

## 5. Testing Requirements (Required)

### 5.1 Test Structure

```
src/lib/services/{domain}/
├── service.ts
├── service.test.ts    # Co-located test file
├── validator.ts
└── validator.test.ts  # Co-located test file
```

### 5.2 Test Pattern

```typescript
// service.test.ts
import { describe, expect, it, beforeEach, mock } from "bun:test";
import { processRecords } from "./service";

describe("processRecords", () => {
  beforeEach(() => {
    // Reset mocks
  });

  it("should process valid records successfully", async () => {
    const records = [createMockRecord()];
    const result = await processRecords(records);

    expect(result.success).toBe(true);
    expect(result.processed).toBe(1);
  });

  it("should handle empty array", async () => {
    const result = await processRecords([]);

    expect(result.processed).toBe(0);
  });

  it("should throw ValidationError for invalid records", async () => {
    const invalidRecords = [{ invalid: true }];

    await expect(processRecords(invalidRecords))
      .rejects.toThrow(ValidationError);
  });
});
```

### 5.3 Coverage Target

```
Business logic: ≥80% coverage
Critical paths: 100% coverage
Edge cases: All identified cases covered
```

---

## 6. Clean Architecture Layer Mapping

### 6.1 Directory to Layer Mapping

| Layer | Directory Pattern | Purpose |
|-------|-------------------|---------|
| Domain | `src/lib/domain/`, `src/lib/entities/` | Business entities, value objects |
| Application | `src/lib/services/`, `src/lib/usecases/` | Business logic, use cases |
| Adapters | `src/app/api/`, `src/lib/db/` | HTTP handlers, DB clients |
| Infrastructure | `src/lib/config/`, external integrations | Configuration, framework setup |

### 6.2 Dependency Rules

```
✅ Allowed:
   Domain ← Application ← Adapters ← Infrastructure

❌ Prohibited:
   Domain → Application (Domain importing from Application)
   Application → Adapters (Application importing from Adapters)
```

### 6.3 Verification Commands

```bash
# Check for violations
grep -r "from.*\/adapters" src/lib/domain/
grep -r "from.*\/infrastructure" src/lib/services/
```

---

## 7. PHASE Decomposition Guide (Backend-Specific)

### 7.1 Backend Feature PHASE Order

```
PHASE 1: Types & Validation Layer
  - Type definitions (interfaces, Zod schemas)
  - Validation logic
  - Shared types export

PHASE 2: Service Layer
  - Business logic services
  - Data transformation
  - Error handling

PHASE 3: Data Access Layer
  - Database clients
  - Repository implementations
  - Query builders

PHASE 4: API Layer
  - Route handlers
  - Request/Response formatting
  - Error response handling
```

### 7.2 Layer Mapping

| Clean Architecture | Backend Equivalent |
|--------------------|---------------------|
| Domain | `types/`, Zod schemas |
| Application | `lib/services/` |
| Adapters | `app/api/`, `lib/db/` |
| Infrastructure | Database clients, external APIs |

---

## 8. File Length Limits (Required)

### 8.1 Rules

| File Type | Limit | Action |
|-----------|-------|--------|
| Service files | 300 lines | Split into sub-services |
| Route handlers | 150 lines | Extract to service layer |
| Test files | No limit | Split by describe blocks if needed |

### 8.2 Split Strategy

When exceeding limits:
1. **Constants/Types** → Separate `types.ts`, `constants.ts`
2. **Validators** → Extract to `validator.ts`
3. **Sub-services** → Split by responsibility

---

## 9. Quality Commands

```bash
# Full quality check
bun run quality  # lint + type-check + test

# Individual checks
bun run lint
bun run type-check
bun run test

# Test specific file
bun test src/lib/services/jsonl/ingestion.test.ts
```

---

## 10. Project-Specific Guidelines Reference

Check additional guidelines in your project's AGENTS.md file:

- **Backend projects**: `{backend_dir}/AGENTS.md` - Project-specific patterns, API conventions
- **Project root**: `{project_dir}/AGENTS.md` - Overall project guidelines
