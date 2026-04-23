# Test Infrastructure by Service

## admin-api / billing-api

- **Runner**: Node.js native test runner + `assert`
- **Location**: `tests/` directory (mirrors src structure)
- **Run all**: `npm test`
- **Run single**:
  ```bash
  node --experimental-test-module-mocks --import=tsx --no-warnings --test tests/routes/settings-plans.test.ts
  ```

## admin-portal

- **Runner**: Vitest + happy-dom + React Testing Library
- **Location**: `__tests__/` subdirectories alongside source files
- **Config**: `vitest.config.ts` (globals: true, happy-dom environment)
- **Run all**: `npx vitest`
- **Run single**: `npx vitest run components/billing/__tests__/paid-plan-view.test.tsx`
- **IMPORTANT**: Always use `renderWithProviders()` from `__tests__/test-utils.tsx`
  - Wraps `QueryClientProvider` with retry disabled
  - Required for all component tests

## Coverage Requirements

- **Minimum**: 80% across unit + integration tests
- **Required coverage types**:
  - Happy path (core functionality)
  - Edge cases (empty input, max values, special characters)
  - Error paths (invalid input, network failures, auth failures)
  - Boundary conditions (pagination limits, rate limits)
  - Multi-tenant isolation (verify tenant_id filtering)
