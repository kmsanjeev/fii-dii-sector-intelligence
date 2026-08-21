# Root cause

Decision: `OTHER_PROVEN_CAUSE` with secondary `DUPLICATE_SERVICE_INVOCATION`
and `BLOCKING_IO/CPU` limited to synchronous pandas work inside the existing
request path.

The controlled cProfile trace before remediation measured approximately
`1.45s` for one local `STOCK_CONFIRMATION` call. The institutional snapshot
consumed `1.076s`; the stock contract consumed `0.349s`; fundamental evidence
consumed `0.145s`; corporate context was not a material independent cost.
The institutional contract called `_participant_snapshot` 12 times and
`_cash_snapshot` 8 times per request. Each participant snapshot recomputed
rolling windows across the full history.

This was not caused by a new fundamental acquisition network call, VEDA
self-HTTP, broad candidate discovery in stock mode, serialization of raw
datasets, or a new provider client. The reported approximately 4.1s sample is
classified as not reproduced under this controlled environment; cold/host
variance may have contributed to that earlier observation, but the duplicate
rolling work was a demonstrated code defect.

No stale-data workaround was used. No validation, freshness, provenance,
alignment, evidence-quality, or institutional-scope check was removed.
