# VEDA-MARKET-THEME-COLD-START-PERFORMANCE-RX1-001

Status: `VEDA_MARKET_THEME_COLD_START_PERFORMANCE_RX1_OPERATIONAL_WITH_CONDITIONS`

This bounded remediation separates governed static Theme membership from the
dynamic price projection used by Theme performance. It does not implement
historical Theme membership, change Theme semantics, move calculations into
VEDA, or reopen Corporate, Fundamentals, institutional-source research, RAG,
PRED, EMP, ML, Jyotish, or BEBOS.

The canonical pre-serving command is:

```text
py -3.11 scripts/build_governed_theme_snapshot.py --write-cache
```

It validates/builds the local ignored runtime artifacts before interactive
Theme use. The request path validates and loads those artifacts and rebuilds
only when governed source or price-manifest inputs change.

See `BASELINE.md`, `FIRST_REQUEST_CALL_GRAPH.md`, `ROOT_CAUSE.md`,
`SNAPSHOT_LIFECYCLE.md`, `REMEDIATION.md`, `POST_BENCHMARK.md`,
`VALIDATION.md`, and `ACCEPTANCE.md`.
