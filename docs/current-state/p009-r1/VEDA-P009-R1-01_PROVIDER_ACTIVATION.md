# VEDA-P009-R1 — Provider Activation

Date: August 11, 2026

## Capability Matrix

| Provider | Search | Fetch | Auth Required | Enabled | Healthy After Validation | Suitable | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ddgs-search` | Yes | No | No | Yes | Yes | Yes | real external search provider used for the live pilot |
| `requests-fetch` | No | Yes | No | Yes | Yes | Yes | real external HTTP retrieval provider used for the live pilot |
| `vedic-astrology-local` | Yes | Yes | No | Yes | Yes | Yes | controlled fallback provider for governed local corpus |
| `synthetic-fixture` | Yes | Yes | No | Yes | Yes | test-only | retained for non-live platform tests |

## Activation Result

- `ddgs-search` was implemented, configured, enabled, and validated.
- `requests-fetch` was implemented, configured, enabled, and validated.
- external status moved from `LOCAL ONLY` to `ACTIVE`.

## Runtime Controls

External execution still requires explicit environment enablement:

```text
VEDA_RESEARCH_EXTERNAL_ENABLED=true
VEDA_RESEARCH_EXTERNAL_SEARCH_ENABLED=true
VEDA_RESEARCH_EXTERNAL_RETRIEVAL_ENABLED=true
```

Persistent autonomous runtime remains opt-in through:

```text
VEDA_RESEARCH_RUNTIME_ENABLED=true
```

Fresh installations do not begin external research by default.

