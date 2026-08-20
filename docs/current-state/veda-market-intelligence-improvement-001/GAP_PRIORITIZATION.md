# Gap prioritization

| Priority | Gap | Decision | Reason |
|---|---|---|---|
| P0 | Missing/stale data was not explicit in formal responses | Remediated | Prevents false current/zero interpretations |
| P0 | Formal provider lacked normalized freshness/provenance | Remediated | Required for VEDA trust-aware UX |
| P1 | Scheduled event dates could look like current data | Remediated | Separates event date from dataset update time |
| P1 | Legacy date-valued `freshness` compatibility | Preserved | Avoids breaking existing consumers |
| P2 | Provider-wide live latency budget and operational telemetry | Deferred | Requires live service and production observation |
| P2 | Legacy FII Ruff debt outside this change | Deferred | Not safe to mix unrelated cleanup |

No gap authorizes a source, RAG, ML, prediction or identity migration.
