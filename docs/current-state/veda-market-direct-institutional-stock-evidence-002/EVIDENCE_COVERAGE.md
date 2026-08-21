# Evidence coverage

`build_evidence_coverage()` is a deterministic diagnostic over the current
local frames and canonical masters; it is not a per-request full-dataset scan.

2026-08-21 result:

```text
master_symbols=2560
symbols_with_any_evidence=2493
symbols_with_deal_evidence=1327
symbols_with_ownership_evidence=1994
symbols_with_both=828
symbols_resolved_to_master=2154
symbols_unresolved=339
symbols_with_resolved_isin=2008
latest_deal_date=2026-08-19
latest_ownership_quarter_end=2026-06-30
participant_unique_names=2533
```

The coverage set is local and source-limited. It must not be interpreted as
coverage of all listed securities, all institutional activity, or all FII/DII
transactions.
