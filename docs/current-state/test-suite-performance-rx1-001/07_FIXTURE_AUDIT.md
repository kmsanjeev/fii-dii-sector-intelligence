# Fixture and isolation audit

- `tests/conftest.py` provides shared session fixtures and an autouse test
  boundary logger. No fixture mutation was required.
- The expensive P024/P025/P026 setup was caused by each domain inventory's
  unbounded repository traversal, not by an unsafe shared fixture.
- Temporary-root inventory tests retain historical recursive behavior, so
  synthetic fixture classification remains isolated and deterministic.
- No test assertion was removed, weakened, skipped unconditionally, or made
  tolerant.
- No global cache or mutable production state was introduced.
