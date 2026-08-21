# Instrument Identity

The canonical identity is exact and provider-mapped. It keeps equity, index,
future and option identity separate and retains provider security ID, segment,
underlying, expiry, strike, option type and ISIN where supplied.

Unknown or symbol-only mappings return `IDENTITY_REVIEW_REQUIRED`; no fuzzy
matching is permitted. Provider master version/date is part of the identity
metadata. The official Dhan instrument-list URL is recorded in
`PROVIDER_AND_ENTITLEMENT_DECISION.md`; provider raw data is local-only and
ignored.
