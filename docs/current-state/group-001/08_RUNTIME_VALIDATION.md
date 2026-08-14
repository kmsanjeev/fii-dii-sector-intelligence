# Runtime Validation

Optional group fields are backward-compatible additions to `ChatRequest`. Legacy requests omit them and use the existing single-user path. Group requests pass metadata to ChatEngine, which records bounded group analysis in the existing conversational diagnostics and adds group-aware prompt guidance without changing response ownership.

The focused API test verifies both legacy and group requests return HTTP 200. No empirical cases, prediction records, outcome records, or RAG documents are changed.

Ten deterministic runtime probes covered direct VEDA address, participant-only
address, disagreement, group summary, Hinglish, parent/child Jyotisha subject,
astrologer debate, conflict rise, de-escalation, and ambiguous addressee. Group
analysis measured 0.191 ms average and 0.314 ms p95 with zero provider calls.
