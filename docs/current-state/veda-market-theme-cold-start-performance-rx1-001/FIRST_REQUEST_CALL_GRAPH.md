# First-request call graph

```text
Theme route
  -> governed_theme_intelligence.summary()
      -> _ensure_loaded()
          -> registry/source validation
          -> membership snapshot load OR bounded source build
      -> 15 bounded Theme projections
          -> validated price projection load OR bounded price projection build
          -> equal-weight returns and breadth
          -> leadership state
      -> response serialization
  -> VEDA read-only provider adapter (for VEDA queries)
```

Pre-remediation trace for a fresh FII process:

| Component | Calls | Wall-time contribution |
|---|---:|---:|
| Membership/source initialization | 16 guarded calls; 2 CSV reads | approximately 2.46s |
| Theme return batches | 15 | approximately 17.81s |
| Price Parquet reads | 2,106 | all current member files |
| Benchmark loader | 16 | negligible |
| Stock service calls | 0 | none |
| Corporate/Fundamental/Institutional member calls | 0 | none |
| Self-HTTP calls | 0 | none |

The 17.81s figure is the wall time of concurrent batches; the summed Parquet
read durations were larger because reads overlapped.

Post-remediation first request with valid artifacts:

| Component | Result |
|---|---:|
| Membership snapshot load | 0.093s |
| Price projection load | 0.016s |
| CSV reads | 0 |
| Parquet reads | 0 |
| Internal summary | 0.342s |
