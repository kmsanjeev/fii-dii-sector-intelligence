# Data freshness and provenance audit

The loader now derives metadata from provider-local files and their date
columns. The contract is intentionally conservative:

`LIVE`, `INTRADAY`, `EOD`, `DELAYED`, `STALE`, `HISTORICAL`,
`QUALITY_WARNING`, and `UNAVAILABLE` are explicit states. Formal responses
include `as_of`, `source`, `freshness`, `last_successful_update`, and
`limitations` under `data_status`.

## Observed provider-local state at validation preparation

| Dataset family | State | As of | Limitation |
|---|---|---|---|
| Market/participant | DELAYED | 2026-08-19 | Provider rows were behind the runtime date |
| Sector | DELAYED | 2026-08-19 | FPI evidence was materially older than the latest sector rows |
| Stock | EOD | 2026-08-20 | No additional limitation observed |
| Corporate | STALE | 2026-08-19 | Scheduled event dates are not freshness timestamps |

These are observations of local provider files, not claims that a missing
dataset is zero or current. Scheduled event dates are deliberately excluded
from the normal latest-date calculation; their file update time is used and a
limitation is retained.

## Missing-data policy

Missing, non-finite and unavailable numeric values remain `null`/`None` in
formal responses. Optional unavailable datasets are reported in limitations;
they do not silently lower a measured value to zero.

## Process health versus data freshness

The contract reports dataset freshness independently from process health. A
healthy HTTP process can serve stale data, and an unavailable/failed dataset
does not become a valid zero. The VEDA adapter propagates the structured state
while retaining its predecessor date-valued `freshness` field for compatibility.
