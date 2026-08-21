# Existing Intraday Inventory

| Component | Actual behavior | Governance classification | Decision |
|---|---|---|---|
| `backend/routers/charts.py` | yfinance 5M/15M/1H query-time OHLCV; no persistence | `CHART_ONLY`, `LEGACY_CHART_SOURCE_ONLY` | Preserve; do not use for governed data |
| `backend/ws/live_ticker.py` | Regime, smart-money score, top sectors and heartbeat every ~30 seconds | `INTELLIGENCE_HEARTBEAT` | Preserve; not a price feed |
| `engines/broker/dhan_adapter.py` | Holdings, positions and trade history | `PORTFOLIO_ONLY` | Preserve broker/data boundary |
| `engines/execution/dhan_order_adapter.py` | Order execution adapter | `EXECUTION_ONLY` | No Intraday foundation caller |
| `.github/workflows/intraday.yml` | Manual explanatory placeholder | `LEGACY/NOT_ENABLED` | No acquisition activation in this phase |
| `backend/services/intraday_foundation.py` | Normalized seam, quality, storage and provider status | `CANDIDATE_FOR_REUSE` | Governed foundation |
