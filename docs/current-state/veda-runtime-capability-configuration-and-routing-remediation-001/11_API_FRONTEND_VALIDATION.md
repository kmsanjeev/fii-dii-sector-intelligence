# API and Frontend Validation

The API exposes effective capability states, including `voice_enabled`, rather than only raw environment booleans. Disabled auxiliary operations return the central typed policy result. The frontend uses the effective state for attachment/review/repository controls and voice input/output controls; it retains an optimistic initial voice state only until the first backend capability snapshot, while backend execution remains authoritative.

Frontend validation: 8 Vitest files, 29 tests passed. TypeScript/Vite production build passed. The build emitted only the existing large-chunk warning.
