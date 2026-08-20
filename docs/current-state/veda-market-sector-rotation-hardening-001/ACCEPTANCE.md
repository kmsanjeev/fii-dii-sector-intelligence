# Acceptance and decision

Review gates:

- Gate A data/taxonomy trust: `PASS_WITH_CONDITION` — current taxonomy is
  explicit; historical membership is unavailable.
- Gate B relative strength: `PASS` — equal-weight current constituent returns
  and NIFTY 50 benchmark proxy are deterministic and traceable.
- Gate C breadth: `PASS_WITH_CONDITION` — coverage is explicit and missing is
  not zero; evidence quality is reduced for partial sectors.
- Gate D rotation/persistence: `PASS_WITH_CONDITION` — bounded 21-file history
  distinguishes improving/weakening and requires multiple observations;
  long-history persistence remains unavailable.
- Gate E institutional context: `PASS` — no sector-specific attribution is
  claimed; scope is market-level context only.
- Gate F provider integration: `PASS` — VEDA consumes the additive contract
  through the existing provider.
- Gate G governance: `PASS` — PRED, EMP, ML, RAG, Jyotish and BEBOS unchanged.
- Gate H engineering quality: `PASS` — focused/static checks and both full
  repository suites passed; final Git release verification remains procedural.

Decision: `VEDA_MARKET_SECTOR_ROTATION_HARDENING_OPERATIONAL_WITH_CONDITIONS`.

Conditions are the current-constituent/survivorship limitation, stale official
index compatibility data, one-day institutional date lag in the live sample,
and absence of direct sector-level institutional flow.
