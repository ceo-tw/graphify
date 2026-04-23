---
title: Frontend Development Reference
type: guide
impact: HIGH
used_by: [design, planner-task, dev-executor]
---

# Frontend Development Reference

> **Purpose**: Essential principles for /planner workflow in Next.js/React projects
> **Scope**: Generic patterns for frontend projects, adaptable to project-specific needs

---

## 1. UI Component Rules (Required)

### 1.1 Component Location Guidelines

```
Allowed: import { Button } from "@/components/ui/button"
         -> Actual path: {ui_components_dir}/*

Prohibited: Creating new base components in src/components/ui/
Prohibited: Duplicating or reimplementing shadcn/ui components
```

**tsconfig.json path alias verification:**
```json
{
  "paths": {
    "@/components/ui/*": ["./{ui_components_dir}/*"]
  }
}
```

### 1.2 Adding New UI Components

1. Create in `{ui_components_dir}/`
2. Follow shadcn/ui style guide
3. Write test file together

### 1.3 Pre-Creation Verification Checklist

**CRITICAL**: Before creating new UI component, verify the following

#### Step 1: Check for Duplicates (MANDATORY)

```python
# Verification automatically performed by dev-executor
Glob(pattern="*.tsx", path="{ui_components_dir}/")

# Currently available components (58+):
# Button, Card, Dialog, Tabs, Table, Badge, Alert, Skeleton,
# Input, Checkbox, Select, Form, Calendar, Popover, Tooltip,
# Avatar, Progress, Separator, Sheet, Drawer, Command, etc.
```

- [ ] Check if same component exists in `{ui_components_dir}/`
- [ ] Review if existing component combination can solve the need
- [ ] Check if shadcn/ui official library provides it

#### Step 2: Location Verification

- [ ] Accessible via `@/components/ui/*` path alias
- [ ] Created in `{ui_components_dir}/`
- [ ] Verify `tsconfig.json` path alias configuration

#### Step 3: Quality Assurance

- [ ] Follows shadcn/ui patterns (style, Props API)
- [ ] Covers basic states (default, hover, disabled, focus)
- [ ] Test file written (`*.test.tsx`)
- [ ] JSDoc documentation

### 1.4 Violation Handling

```
If component created in src/components/ui/:
   -> Stop immediately, move to packages/ui-registry

If shadcn/ui component duplicated:
   -> Change to use original (fix import path)

If path alias not used (relative import):
   -> ESLint error, fix to @/components/ui/* format

If duplicate component created:
   -> dev-executor validation fails, change to use existing
```

---

## 2. Data Fetching Patterns (Required)

### 2.1 Query Key Factory Pattern

**All React Query hooks use Key Factory pattern:**

```typescript
// src/lib/hooks/use-{domain}-data.ts
export const domainKeys = {
  all: ["domain"] as const,
  list: (filters?: Filters) => [...domainKeys.all, "list", filters] as const,
  detail: (id: string) => [...domainKeys.all, "detail", id] as const,
};
```

### 2.2 staleTime Guidelines

| Data Characteristic | staleTime | Example |
|---------------------|-----------|---------|
| Real-time required | 0 | Error alerts |
| Frequently changes | 2 min | Quota (rolling window) |
| Aggregated data | 5 min | UI KPIs, charts |
| Static data | 30 min+ | Settings, metadata |

### 2.3 Custom Hook Writing

```typescript
export function useDomainData() {
  const { startDate, endDate } = useMonthFilter();  // Filter context integration
  const dateRange = { startDate, endDate };

  return useQuery({
    queryKey: domainKeys.list(dateRange),
    queryFn: () => getDomainData(dateRange),
    staleTime: 5 * 60 * 1000,
  });
}
```

---

## 3. Chart Conventions (Required)

### 3.1 Color System - CSS Variables

```tsx
// Correct usage
stroke="var(--primary)"
fill="var(--background)"
stopColor="hsl(var(--chart-1))"

// Transparency adjustment
stroke="color-mix(in oklab, var(--primary) 60%, transparent)"

// Prohibited: Hardcoded colors
stroke="#8884d8"
```

### 3.2 ChartConfig Pattern

```typescript
const chartConfig: ChartConfig = {
  sessions: {
    label: "Sessions",
    color: "hsl(var(--chart-1))",
  },
  conversations: {
    label: "Conversations",
    color: "hsl(var(--chart-2))",
  },
};
```

### 3.3 Common Style Rules

| Element | Property | Value |
|---------|----------|-------|
| `CartesianGrid` | `strokeDasharray` | `"3 3"` |
| `CartesianGrid` | `vertical` | `false` |
| `XAxis/YAxis` | `tickLine` | `false` |
| `XAxis/YAxis` | `axisLine` | `false` |

---

## 4. File Length Limits (Required)

### 4.1 Rules

| File Type | Limit | Action |
|-----------|-------|--------|
| General source | 500 lines | Plan split when approaching 400 |
| Test files | No limit | Split by describe blocks if needed |

### 4.2 Split Strategy

When exceeding 500 lines:
1. **Constants/Types** -> Separate `types.ts`, `constants.ts`
2. **Sub-components** -> Extract to separate files
3. **Utility functions** -> Move to `utils/` directory

---

## 5. PHASE Decomposition Guide (Frontend-Specific)

### 5.1 Frontend Feature PHASE Order

```
PHASE 1: Types & Data Layer
  - Type definitions (interfaces, types)
  - API integration (services, hooks)
  - Query Key Factory

PHASE 2: Core Components
  - Presentational components
  - State management (Context/hooks)
  - Basic layout

PHASE 3: Feature Integration
  - Container components
  - Error/loading states
  - Routing integration

PHASE 4: Polish (optional)
  - Animation
  - Responsive layout
  - Accessibility improvements
```

### 5.2 Layer Mapping

| Clean Architecture | Frontend Equivalent |
|--------------------|---------------------|
| Domain | `types/`, interfaces |
| Application | `lib/hooks/`, `lib/services/` |
| Adapters | `components/` |
| Infrastructure | `app/api/`, external API clients |

---

## 6. Error Handling Patterns

### 6.1 React Query Error State

```tsx
const { data, isLoading, isError, error } = useDomainData();

if (isLoading) return <Skeleton />;
if (isError) return <ErrorState message={error?.message} />;
if (!data?.length) return <EmptyState />;

return <DataView data={data} />;
```

### 6.2 Priority

```
1. isLoading -> Skeleton UI
2. isError -> Error message
3. isEmpty -> Empty state message
4. Normal -> Data render
```

---

## 7. Quality Commands

```bash
# Full quality check
bun run quality  # lint + type-check + test

# Individual checks
bun run lint
bun run type-check
bun run test

# Test specific file
bun test src/components/FeatureComponent.test.tsx
```

---

## 8. Project-Specific Guidelines Reference

Check additional guidelines in your project's AGENTS.md file:

- **Frontend projects**: `{frontend_dir}/AGENTS.md` - Project-specific patterns, conventions
- **Project root**: `{project_dir}/AGENTS.md` - Overall project guidelines
