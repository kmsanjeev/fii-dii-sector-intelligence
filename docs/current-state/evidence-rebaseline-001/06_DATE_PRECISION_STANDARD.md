# Date Precision Standard

`EXACT_DAY` is primary confirmatory precision. `MONTH_INTERVAL` is secondary
and requires interval-aware analysis. `YEAR_INTERVAL` is exploratory only.
Missing dates are `NOT_AVAILABLE`; do not synthesize January 1 or another
midpoint. Birth time precision and event date precision are separate fields.
