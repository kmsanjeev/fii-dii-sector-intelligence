# Data inventory

| Layer | Existing source | Role | Authority/limitation |
|---|---|---|---|
| Identity | `data/NSE/equity_master/equity_master.csv` | NSE symbol, company, ISIN, series, active state | canonical local identity |
| Identity/fundamentals master | `company_fundamentals_master.csv` | sector, industry, category, dated ownership snapshot | dated master, not live valuation |
| Price | per-symbol `nsecache/stock_history/*.parquet` | OHLCV windows and volume | daily cache; complete windows are explicit |
| Technical | `technical_indicators.csv` | existing trend/technical facts | provider-generated, dated |
| Momentum | `price_momentum.csv` | existing longer-window context | retained as legacy/local context |
| Sector | `sector_rotation_intelligence.csv` | sector leadership, breadth, relative strength | sector-rotation-1.1; no duplicate calculation |
| Ownership/deals | shareholding, holding trends, institutional deal signals | ownership/deal context | not equivalent to live institutional buying |
| Fundamentals | valuation, extended financials, quarterly results | valuation/quality/growth facts | sparse and date-misaligned by design |
| Corporate | announcements, event calendar | announcement/effective/event context | event is not automatically a catalyst |
| Market context | participant flow scores | market-level context | never attributed to a stock |

Missing fields remain missing; they are never filled with zero.
