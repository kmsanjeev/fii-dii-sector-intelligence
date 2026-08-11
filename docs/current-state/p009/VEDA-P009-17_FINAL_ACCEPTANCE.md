# P009 Final Acceptance

Status: PASS WITH CONDITIONS

Accepted capabilities:
- backend-owned autonomous research worker
- persisted scheduler and worker lease
- provider state, cooldown, fallback, and runtime controls
- daily and weekly digests
- due-run execution independent of the Admin UI
- candidate enrichment and duplicate suppression under repeated cycles
- unsafe external target rejection before retrieval

Conditions:
- external provider code exists but remains disabled by default;
- unless a live externally configured run is executed in the target environment, external research must be reported as not active.

Boundaries preserved:
- Approved Core Knowledge is not auto-modified
- production astrology rules are not auto-modified
- production astrology calculations are unchanged
