# Architectural Validation Tests

This directory contains tests that validate architectural patterns and ensure the codebase follows Server-Side Orchestration principles.

## Test Files

### `server-side-orchestration.test.tsx`
Validates that components follow the Server-Side Orchestration pattern:
- ✅ Server Actions are used for mutations
- ✅ `revalidatePath` is called after mutations
- ✅ Components receive `OrchestratedSessionState` as props
- ✅ No client-side data fetching in components
- ✅ Business logic stays in Python Domain Services

### `helpers.ts`
Test utilities for architectural validation:
- Component pattern validation
- Source code analysis helpers
- Mock data generators

## Running the Tests

```bash
# Run all architectural tests
npm test -- __tests__/architecture

# Run specific test file
npm test -- server-side-orchestration.test.tsx

# Run with coverage
npm test -- --coverage __tests__/architecture
```

## Integration Tests

See `../integration/` for:
- `backend-endpoints.test.ts` - Validates frontend-backend endpoint alignment
- `type-synchronization.test.ts` - Validates TypeScript/Pydantic type sync

## Architecture Rules Enforced

1. **Server Actions First**: All mutations must use Server Actions, not client-side `fetch`
2. **Dumb Components**: Components receive data as props, don't fetch data
3. **Backend as Source of Truth**: All business logic in Python Domain Services
4. **Type Safety**: Full type synchronization between frontend and backend

## Adding New Tests

When adding new components, ensure they:
1. Receive `OrchestratedSessionState` as a prop (if applicable)
2. Use Server Actions for mutations
3. Don't contain business logic
4. Are properly typed

Use the helpers in `helpers.ts` to validate patterns.
