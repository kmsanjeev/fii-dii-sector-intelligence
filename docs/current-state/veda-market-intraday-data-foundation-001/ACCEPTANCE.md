# Acceptance

Decision: `VEDA_MARKET_INTRADAY_DATA_FOUNDATION_OPERATIONAL_WITH_CONDITIONS`.

The code foundation and bounded contracts are implemented with conditions, but
the account has a verified Dhan access token/profile but an inactive Data API
entitlement. Real historical, quote, option and live validation therefore
remain blocked. This is a truthful source gate, not a yfinance fallback. The
required next gate is provider-specific entitlement resolution followed by
bounded representative validation.

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
| VEDA capability routing | PASS_WITH_CONDITION | `market.intraday.data` is additive and propagates authenticated/entitlement-blocked status; no second market engine was created. |
| No unsafe fallback or production leakage | PASS | No yfinance fallback, strategy, signal, prediction, ML, order, execution or alert path was added. |
| Focused validation | PASS | FII API/intraday checks 10/10; VEDA full regression 93/93. |
| Provider historical/quote/options/live validation | PASS_WITH_CONDITION | Authentication/profile passed; Data API entitlement is inactive, so representative market-data responses remain blocked and live-session validation is pending. |
| Operational release decision | PASS_WITH_CONDITION | `VEDA_MARKET_INTRADAY_DATA_FOUNDATION_OPERATIONAL_WITH_CONDITIONS`; provider-specific entitlement resolution remains required. |
