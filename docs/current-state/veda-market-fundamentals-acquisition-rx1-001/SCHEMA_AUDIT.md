# Schema and provenance audit

The normalized result retains:

- `symbol`, `date_start`, `date_end`, `quarter_label`, `window_label`
- normalized ISO `filing_date` where parseable
- `revenue_cr`, `net_profit_cr`, `eps`, `rounding`
- `standalone_or_consolidated`
- compatibility `source`

The canonical identity is:

```text
symbol + date_start + date_end + standalone_or_consolidated + source + filing_date
```

Exact duplicate filing versions are removed. Statement variants and distinct
filing dates are retained as separate observations, allowing a restatement or
source-version review. Negative revenue/profit/EPS values remain negative;
missing values remain missing.

Historical malformed filing dates already present in the local legacy corpus
are not silently rewritten by this activity. Newly normalized records reject
unparseable filing dates rather than truncating them.
