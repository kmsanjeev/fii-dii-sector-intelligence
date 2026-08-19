# Frontend discovery validation

Vitest now uses a durable discovery boundary in `frontend/vite.config.ts`:

- include: `src/test/**/*.{test,spec}.{ts,tsx}`
- exclude: `**/node_modules/**`, `**/node_modules.*/*`, and `.git`

This excludes ignored dependency-backup trees while retaining all repository
tests in the source test directory. Full discovery completed with 8 test files
and 29 tests passing. `npm run build` also completed successfully; the existing
large-chunk warning is nonblocking.
