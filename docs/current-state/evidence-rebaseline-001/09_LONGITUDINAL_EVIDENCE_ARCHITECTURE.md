# Longitudinal Evidence Architecture

Each subject has a stable internal ID, birth record and event records. Birth
provenance (`birth_source_ids`, quality, precision) is never merged with event
provenance (`event_source_ids`, date precision, verification). One subject may
have many events and many source claims. Source clusters identify copied or
derivative pages. Acquisition stores no chart feature values; feature
calculation happens only after a frozen preregistration and independent review.

Minimum state values: `AVAILABLE`, `VERIFIED`, `CONFLICTED`, `NOT_AVAILABLE`,
`REJECTED`, `RESEARCH_ONLY`.
