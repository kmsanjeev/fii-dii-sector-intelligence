# Acceptance

Decision: `VEDA_MARKET_INTRADAY_DATA_FOUNDATION_BLOCKED`.

The code foundation and bounded contracts are implemented with conditions, but
the programme is not called operational because the current account has no
verified Dhan access token/Data API entitlement. This is a truthful source
gate, not a yfinance fallback. Required next gate: provide/verify authorized
provider access, run bounded representative historical/quote/option/live
validation, record coverage/performance, then re-evaluate this programme.

No automated trading, BUY/SELL, Intraday intelligence, RAG, PRED, EMP, ML,
Jyotish, BEBOS or EOD Swing/Positional semantic change occurred.

## Deterministic acceptance register

| Gate | Result | Evidence / condition |
|---|---|---|
| Existing intraday inventory and compatibility boundaries | PASS | yfinance charts, `/ws/live`, broker holdings/orders, and EOD paths were audited and retained with their original semantics. |
| Official primary provider seam | PASS_WITH_CONDITION | DhanHQ 2.2.0 is the explicit adapter; credentials and Data API entitlement are not exposed or logged. |
| Exact provider identity | PASS | Security ID, exchange segment, provider instrument type, expiry/strike/option type and mapping metadata are preserved; fuzzy matching is rejected. |
| Session/timezone model | PASS | Asia/Kolkata, pre-open, regular, post-close, weekend, holiday/special/unknown states are explicit. |
| Candle normalization/aggregation/quality | PASS | Parallel arrays, missing OI, OHLC, volume, OI-last, session boundaries, closure and quality flags are covered by focused tests. |
| Local bounded storage/read contract | PASS_WITH_CONDITION | Partitioned Parquet and de-duplication are deterministic; provider-backed identity read remains gated. |
| VEDA capability routing | PASS_WITH_CONDITION | `market.intraday.data` is additive and preserves `CREDENTIALS_UNAVAILABLE`; no second market engine was created. |
| No unsafe fallback or production leakage | PASS | No yfinance fallback, strategy, signal, prediction, ML, order, execution or alert path was added. |
| Focused validation | PASS | FII API/intraday checks 10/10; VEDA full regression 93/93. |
| Provider historical/quote/options/live validation | BLOCKED | No `DHAN_ACCESS_TOKEN`; entitlement and representative provider responses cannot be verified. |
| Operational release decision | BLOCKED | Must remain `VEDA_MARKET_INTRADAY_DATA_FOUNDATION_BLOCKED` until the provider gate is completed. |
