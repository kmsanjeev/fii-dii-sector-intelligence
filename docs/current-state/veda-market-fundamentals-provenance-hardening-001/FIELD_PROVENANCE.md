# Field provenance

`fundamental-evidence-1.0` emits one observation per field. Each observation
contains `source`, `source_dataset`, `source_authority`,
`direct_or_derived`, `period`, `dates`, `freshness`, `status`,
`missing_reason`, `applicability`, and `limitations`.

Quarterly revenue, profit and EPS are summed into TTM only when four unique,
comparable period ends have valid values. Year-over-year values require eight
valid comparable periods. Negative values are retained; missing, invalid and
not-applicable values are not converted to zero.

The legacy `roe_pct` output is explicitly `UNTRUSTED_SOURCE` because the
existing valuation engine populated it with net margin. It is not surfaced as
ROE in the new evidence authority. PE/PB remain ratios and do not become a
valuation conclusion.
