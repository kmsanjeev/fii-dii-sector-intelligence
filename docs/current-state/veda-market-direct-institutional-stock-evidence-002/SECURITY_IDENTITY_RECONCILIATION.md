# Security identity reconciliation

The existing canonical identity loader remains the authority: NSE equity
master symbol mapping is combined with the fundamentals master ISIN/company
mapping. The 1.1 contract now exposes the resolution result per stock and in
each disclosed record.

States:

- `EXACT_IDENTITY`: identified canonical symbol and valid ISIN, with source
  company names agreeing;
- `HIGH_CONFIDENCE_MAPPED`: identified canonical symbol but ISIN is missing or
  not valid in the current master;
- `REVIEW_REQUIRED`: unknown or insufficient identity evidence, or source name
  conflict.

Measured local coverage on 2026-08-21:

| Metric | Result |
|---|---:|
| canonical master symbols | 2,560 |
| symbols with any evidence | 2,493 |
| symbols with disclosed-deal evidence | 1,327 |
| symbols with ownership evidence | 1,994 |
| symbols with both | 828 |
| symbols resolved to a master identity | 2,154 |
| symbols requiring/unresolved in union coverage | 339 |
| symbols with resolved ISIN | 2,008 |

Before 002, these identity-resolution and coverage metrics were not measured
as governed contract fields. This is a measurement baseline, not a claim that
the underlying source universe increased.
