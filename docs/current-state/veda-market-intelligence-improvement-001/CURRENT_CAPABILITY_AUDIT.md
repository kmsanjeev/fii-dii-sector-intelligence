# Current capability audit

## Existing capability

The FII-DII runtime already exposes market regime/context, indices,
institutional flow, sectors, stock intelligence and corporate intelligence
through the existing FastAPI routers. VEDA already has a formal read-only
Market provider and a separate transitional legacy bridge.

## Observed gap

Before this activity, formal responses exposed load timestamps and/or dated
rows but did not provide one structured answer to: whether the data is live,
delayed, stale, unavailable or merely scheduled; which source produced it; and
what limitations apply. Several numeric response fields also used `0` as a
fallback for absent values, which could be mistaken for a measured zero.

## Reuse decision

`REUSE > EXTEND`: the existing `data_loader`, FastAPI routers, VEDA provider
adapter and contract fixtures were extended. No parallel Market engine,
retriever or database was created.

## Baseline

- FII-DII starting commit: `5d1bf2a0c2b8ded6d9ed703389dba2368e562580`.
- VEDA starting commit: `53ab5b2653478af10b70857ad60a0d205a14e9b0`.
- FII focused API/guardrail baseline: 19 passed.
- VEDA Market/public/legacy focused baseline: 40 passed.
