# Validation

Focused FII cross-layer/upstream tests: `36 passed`.

Focused VEDA Market/routing/public tests: `37 passed` with existing deprecation
warnings only.

Live FII HTTP scenarios passed for overview, leadership discovery and symbol
analysis across RELIANCE, LT, HDFCBANK, TCS and INFY. Live VEDA queries passed
for overview, “Where is smart money moving?”, sector confirmation and
RELIANCE broader context.

Warm performance samples (10 samples after warm-up):

- upstream: Market p50 approximately `11 ms`, institutional `~524 ms`, sector
  `~43 ms`, stock `~227 ms`;
- FII cross-layer overview: p50 `803.2 ms`, p90 `857.7 ms`;
- VEDA cross-layer query: p50 `791.4 ms`, p90 `859.6 ms`.

No internal multi-thousand-stock loop is used. Symbol analysis skips candidate
discovery and composes only the requested stock context.
