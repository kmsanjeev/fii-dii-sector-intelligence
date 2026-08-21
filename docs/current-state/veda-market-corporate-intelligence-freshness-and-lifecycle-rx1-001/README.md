# VEDA-MARKET-CORPORATE-INTELLIGENCE-FRESHNESS-AND-LIFECYCLE-RX1-001

Status: OPERATIONAL_WITH_CONDITIONS

This activity extends the existing provider-owned Corporate Intelligence
contract without changing `corporate-intelligence-1.0`, source ownership,
Market ownership, scheduler architecture, RAG, prediction, ML, EMP, Jyotish,
or BEBOS boundaries.

Decision: `VEDA_MARKET_CORPORATE_INTELLIGENCE_FRESHNESS_AND_LIFECYCLE_RX1_OPERATIONAL_WITH_CONDITIONS`.

The principal production root cause was the official NSE event-calendar request
being routed through `nselib`, whose Brotli response decoding failed. The
engine caught the exception, returned an empty result, left the last valid
dataset in place, and its module entry point ignored the false return value.
The daily orchestration stage already included 7B; the defect was silent source
refresh failure, not a missing scheduler stage.

RX1 now uses the existing provider `nse_client` session with identity content
encoding, writes an explicit refresh-state record, preserves the last valid
dataset on failure, returns a non-zero module status on source failure, adds
row retrieval timestamps for newly acquired event-calendar rows, and exposes
bounded retrieval/lifecycle metadata in Corporate Intelligence responses.

Historical rows retain null retrieval timestamps. No timestamp is fabricated.
Historical quarterly `filing_date` values with truncated years remain invalid;
freshness uses valid `date_end` values and declares that basis explicitly.

Evidence files:

- `ROOT_CAUSE.md`
- `SOURCE_FRESHNESS.md`
- `RETRIEVAL_METADATA.md`
- `LIFECYCLE_LINEAGE.md`
- `ACQUISITION_AND_REFRESH.md`
- `BEFORE_AFTER_COVERAGE.md`
- `IMPLEMENTATION_INVENTORY.md`
- `VALIDATION.md`
- `ACCEPTANCE.md`
