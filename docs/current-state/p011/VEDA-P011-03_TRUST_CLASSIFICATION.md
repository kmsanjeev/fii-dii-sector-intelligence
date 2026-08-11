# Trust Classification

Runtime retrieval distinguishes these classes:
- `APPROVED_CORE`
- `REVIEWED_INTERNAL`
- `LEGACY_UNSOURCED`
- `LOCAL_PLATFORM_EVIDENCE`
- `TEMPORARY_EXTERNAL_RESEARCH`
- `DISCOVERY_ONLY`
- `ML_PREDICTION`

Current P011 implementation actively renders:
- approved core
- local platform evidence
- reviewed internal memory
- legacy unsourced knowledge
- predictive ML signals

Temporary external research remains a separate chat path from P008-R1 and is not merged into approved-core truth.
