# Validation record

## Focused validation

- FII governed portfolio and Theme tests: `10 passed`.
- VEDA Market provider/capability/routing/public-foundation tests: `41 passed`.
- Post-regression FII API baseline plus governed portfolio tests: `6 passed`.
- Ruff and compile checks passed for all touched Python files.
- FII full suite before snapshot repair: `1 failed, 1354 passed`; the sole
  failure was the intentionally changed API snapshot.
- The snapshot was regenerated to 153 paths/166 operations; the affected
  regression then passed, followed by the compact full-suite result
  `1355 passed`.

## HTTP validation

- FII `/health`: HTTP 200; 41/43 datasets loaded.
- FII `/api/portfolio/governed`: HTTP 200; contract version and explicit empty
  portfolio returned.
- VEDA `/api/v1/capabilities`: portfolio capability present, authenticated,
  entitlement `portfolio`, READ-only.
- Anonymous VEDA portfolio query: `AUTHENTICATION_REQUIRED`; no provider data
  forwarding.

## Determinism and safety

The new composition is deterministic for the same local inputs and reuses
existing provider artifacts. No new RAG store or rebuild is part of this
activity. No prediction, ML, astrology, EMP, broker or trading path changed.
