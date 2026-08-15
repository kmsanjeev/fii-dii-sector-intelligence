# P027 Runtime Validation

P027 is deterministic and adds zero routine provider calls. Runtime probes exercise Career, Wealth, Education, Marriage, Progeny, Health, contradiction, timing conflict, missing-data, and multi-chart inputs through the existing Jyotisha calculation/evidence path. Each probe must return a non-empty trace without changing chart facts.

The existing `/api/chat` path remains owned by ChatEngine. P027 failure is isolated from normal chat fallback.
