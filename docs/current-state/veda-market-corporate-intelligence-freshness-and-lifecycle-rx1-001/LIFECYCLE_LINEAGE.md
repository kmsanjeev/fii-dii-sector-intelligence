# Lifecycle and lineage governance

Lifecycle status is assigned only from explicit source language. Supported
states include `ANNOUNCED`, `SCHEDULED`, `RESCHEDULED`, `AMENDED`,
`CANCELLED`, `WITHDRAWN`, `TERMINATED` and `COMPLETED` where the source text
supports that state. A passed scheduled date remains non-completion evidence.

Each event now carries additive lifecycle fields:

```text
parent_event_id
related_event_ids
lifecycle_group_id
version
lineage_method
lineage_confidence
state_method
```

The default lifecycle group is the deterministic event ID. No fuzzy joins,
semantic similarity, or cross-source inference is performed. Linkage remains
`UNKNOWN` unless a future source supplies an explicit stable reference.

The contract keeps these distinctions explicit:

- MOU/LOI is not an order contract;
- acquisition announcement is not acquisition completion;
- approval is not execution or receipt of funds;
- fundraising approval is not fundraising completion;
- scheduled board/result event is not a completed event;
- corporate disclosure is not a price or recommendation signal.

The audited RELIANCE response contained 11 events, all with
`lineage_method=UNKNOWN`; this is correct bounded behavior, not a failed fuzzy
linkage attempt.
