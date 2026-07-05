# Capital Flow Intelligence Platform — Data Flow Diagram

**Version:** 4.6 | **Updated:** 2026-07-02

---

## Overview

The platform ingests raw NSE market data and transforms it through five sequential intelligence layers into actionable capital flow signals delivered via alerts, APIs, and a React GUI.

```
RAW NSE DATA  →  ACQUISITION  →  INTELLIGENCE  →  AI/ML  →  APPLICATION  →  USER INTERFACES
```

---

## Layer 1 — Raw Data Sources

```
NSE Archives / Live APIs
│
├── Bhavcopy Equity          data/bhavcopy/equity/1995-2026/   7,813 daily CSV files
│                            data/NSE/bhavcopy/equity/YYYY/     (canonical target)
├── Bhavcopy F&O             NSE F&O OI + Volume 2016-2026
├── Corporate Actions        data/NSE/corporate_actions/        1999-2026 · 28 year files · 40,517 rows
├── NSE XBRL Results         NSE live API (XBRL endpoint)       4,181 quarterly P&L rows
├── NSE Shareholding API     nselib quarterly_shp               7,228 rows Q2FY25-Q1FY26
├── Block / Bulk Deals       nselib bulk_deals                  12,467 deals (6M rolling)
├── Corporate Announcements  NSE XBRL announcement API          incremental per symbol
├── Symbol Change History    nsearchives symbolchange.csv       1,038 NSE symbol renames
└── Index Constituents       nsearchives indices/               30 NSE index CSV files
```

---

## Layer 2 — Acquisition & Foundation

```
engines/acquisition/  engines/foundation/  engines/fundamentals/
│
├── Phase 1  bhavcopy_import_engine          → data/NSE/bhavcopy/equity/YYYY/*.csv
│            equity_master_engine            → data/NSE/equity_master/equity_master.csv (2123 EQ)
│
├── Phase 2  classification_engine_v4        → data/reference/company_classification_v4.csv
│                                              (99.53% coverage, 27 sectors, 18 themes)
│
├── Phase 4A company_fundamentals_master_engine → data/NSE/equity_master/company_fundamentals_master.csv
│                                                 (2123 symbols, 100% ISIN + listing_date)
├── Phase 4B industry_master_engine          → data/reference/mapping/industry_master.csv (183 industries)
├── Phase 4C classification_engine_v4 final  → 99.53% non-OTHER
├── Phase 4D nse_constituents_engine         → data/NSE/indices/index_membership.csv (506 symbols)
│
├── Phase 5A participant_acquisition_engine  → data/historical/institutional/
│                                              institutional_positioning_history.csv (2581 rows)
│                                              cash_market_flows_history.csv
│
├── Phase 15 financial_results_engine        → data/NSE/results/quarterly_results.csv (4181 rows)
│            shareholding_engine             → data/NSE/shareholding/quarterly_shp.csv (7228 rows)
│
├── Phase 17 symbol_change_engine            → data/NSE/equity_master/symbol_change_history.csv
│                                              (1038 renames: IIFLWAM→360ONE etc.)
│
└── Phase 18 announcement_fetcher            → data/intelligence/company_announcements.csv
             corporate_announcements_engine  → data/intelligence/announcement_signals.csv
```

---

## Layer 3 — Intelligence Engines

All outputs land in `data/intelligence/` unless noted.

```
engines/participant/  engines/corporate/  engines/intelligence/  engines/management/
│
├── Phase 5B  participant_flow_engine         → participant_flow_scores.csv     (2581 rows, 62 cols)
│             [input: institutional_positioning_history.csv]                    rolling OI delta, z-scores ±100
│
├── Phase 5C  participant_intelligence_engine → participant_intelligence.csv    (2581 rows)
│             [input: participant_flow_scores.csv]                              regime, Smart Money, divergence
│
├── Phase 6A  sector_capital_flow_engine      → sector_capital_flows.csv       (74,269 rows 2016-2026)
│             [input: bhavcopy 7813 files + participant flows]                  turnover-weighted FII/DII attribution
│
├── Phase 6B  sector_flow_score_engine        → sector_flow_scores.csv         (74,269 rows)
│             [input: sector_capital_flows.csv]                                 rolling 5D/20D/60D + z-scores
│
├── Phase 6C  sector_rotation_intelligence_engine → sector_rotation_intelligence.csv (29 rows snapshot)
│                                                   sector_rotation_history.csv      (full time-series)
│             [input: sector_flow_scores + index_strength]
│             Signals: STRONG_ACCUMULATION | EARLY_ROTATION | PRICE_LED | NEUTRAL | DISTRIBUTION
│
├── Phase 7A  block_bulk_deal_engine          → block_bulk_deals.csv            (12,467 rows)
│                                               institutional_deal_signals.csv  (361 symbols, 30D net)
│
├── Phase 7B  corporate_event_calendar_engine → event_calendar.csv             (33,839 rows 2023-2026)
│                                               upcoming_catalysts.csv          (next 60D, scored)
│
├── Phase 7C  corporate_action_intelligence_engine → corporate_action_signals.csv   (40,517 classified)
│                                                     corporate_confidence_scores.csv (1,111 symbols)
│
├── Phase 8A  price_momentum_engine           → price_momentum.csv             (2441 symbols)
│             [input: bhavcopy parquet cache]  ret_30d/60d/90d/365d, vol_ratio, price_score
│
├── Phase 8B  bull_run_probability_engine     → bull_run_probability.csv       (2441 symbols)
│                                               bull_run_watchlist.csv         (225 EMERGING)
│             [input: price_momentum + sector_rotation + deal_signals + corporate_confidence]
│             4-factor: price(30%) + sector_flow(25%) + deals(25%) + corporate(20%)
│             Labels: STRONG_CANDIDATE | EMERGING | WATCHLIST | NEUTRAL | AVOID
│
├── Phase 15B valuation_engine                → valuation_scores.csv           (2084 symbols)
│             [input: quarterly_results + stock_price_cache]                   P/E, ROE, valuation_label
│
├── Phase 16  holding_trend_engine            → data/NSE/shareholding/holding_trends.csv
│             announcement_fetcher            → data/NSE/shareholding/board_announcements.csv (527 rows)
│             management_sentiment_engine     → data/NSE/shareholding/management_sentiment.csv (471 rows)
│             [input: quarterly_shp + board_announcements + Anthropic API for tone]
│
├── Phase A   technical_engine                → technical_indicators.csv       (2717 rows)
│             [input: bhavcopy parquet cache]  52W H/L, 20/50/200 DMA, trend_signal
│
├── Phase A   fno_engine                      → fno_intelligence.csv           (211 F&O stocks)
│                                               market_context.json             (PCR + regime pulse)
│             [input: bhavcopy F&O OI data]    oi_signal: LONG_BUILDUP | SHORT_COVER | SHORT_BUILDUP | LONG_UNWIND
│
└── Phase C   trade_conviction_engine         → trade_conviction_scores.csv    (2406 symbols)
              [input: technical + fno + sector_rotation + shareholding + valuation + ml + management]
              7-factor: trend(25%) + OI(20%) + sector(15%) + shp_delta(15%) + valuation(10%) + ML(10%) + mgmt(5%)
              Actions: STRONG_BUY | BUY | HOLD | REDUCE | EXIT
```

---

## Layer 4 — AI / ML Intelligence

```
engines/ml/  engines/ai/knowledge/  engines/ai/chatbot/
│
├── Phase 12  feature_engineering    → ml_features/feature_matrix.parquet   (2441 × 24 features)
│             [input: 6 intelligence CSVs]
│             Feature groups: Phase8B scores + price momentum + sector flow + participant + corporate
│
├── Phase 12  accumulation_model     → ml_features/models/accumulation.json (XGBoost classifier)
│             bull_run_model         → ml_features/models/bull_run.txt       (LightGBM + XGBoost ensemble)
│             ml_scorer              → ml_accumulation_scores.csv            (2441 symbols)
│                                      ml_bull_run_scores.csv
│                                      ml_scores_combined.csv               (daily combined output)
│
├── Phase 13  document_builder       → 1,091 text documents from 6 intelligence CSVs
│             bm25_indexer           → BM25Okapi sparse keyword index
│             faiss_indexer          → FAISS dense indexes (6 domain: market/sector/stock/corporate/ml/fund)
│             hybrid_retriever       → RRF fusion (BM25 + FAISS), top_k=5 per query
│
└── Phase 14  intent_router          → MARKET | SECTOR | STOCK | CORPORATE | RESEARCH
              data_tools             → 11 functions accessing intelligence CSVs
              tool_registry          → Anthropic → Groq/OpenAI tool schema conversion
              chat_engine            → Groq llama-3.3-70b-versatile
                                       parallel_tool_calls=False (prevents Llama XML bug)
                                       MAX_TOOL_ROUNDS=3 (100k token/day budget)
                                       RAG context injection → system prompt
```

---

## Layer 5 — Application Layer

```
alerts/  engines/orchestration/  backend/  engines/portfolio+backtest+broker+research+execution/
│
├── Phase 9   alert_engine          → evaluates 6 intelligence CSVs daily
│             alert_store           → cooldown tracking (JSON state file)
│             telegram_bot          → Telegram Bot API HTML delivery
│             daily_digest          → 18:30 IST intelligence summary
│             alert_scheduler       → APScheduler: digest@18:30 + checks@19:00 IST
│
│             10 Alert Types:
│             P1  REGIME_CHANGE          → no cooldown
│             P2  STRONG_CANDIDATE       → 72h cooldown
│             P3  SECTOR_ROTATION        → 48h cooldown
│             P4  INSTITUTIONAL_DEAL     → 48h cooldown
│             P5  CORPORATE_CONFIDENCE   → 48h cooldown
│             P6  PARTICIPANT_DIVERGENCE → 48h cooldown
│             P7  DAILY_DIGEST           → 24h cooldown
│             P8  CATALYST               → 48h cooldown
│             P9  TRADE_CONVICTION       → cap 3/day
│             P10 OI_SIGNAL_FLIP         → cap 5/day
│
├── Phase 10  FastAPI backend            → port 8001
│             data_loader               → in-memory CSV cache, 60min auto-reload
│             20 REST endpoints + WebSocket /ws/live
│
│             Endpoint Map:
│             GET  /health                         → datasets_loaded count
│             GET  /api/market/regime              → regime, smart money, conviction
│             GET  /api/market/context             → + PCR, cash flows, breadth
│             GET  /api/participant/latest         → FII/DII/PRO/CLIENT + divergence + opportunity
│             GET  /api/participant/history        → 252D time-series
│             GET  /api/sectors                    → 29 sectors with rotation signals
│             GET  /api/sectors/:sector            → sector detail + top 10 stocks
│             GET  /api/stocks                     → 2406 symbols paginated (+ _enrich_bulk)
│             GET  /api/stocks/watchlist           → label-filtered + _enrich_bulk
│             GET  /api/stocks/:symbol             → full stock detail incl. tech/fno/ml/shp
│             GET  /api/corporate/deals            → block/bulk deals
│             GET  /api/corporate/catalysts        → upcoming events (60D)
│             GET  /api/corporate/confidence       → corporate confidence scores
│             GET  /api/charts/:symbol/ohlcv       → bhavcopy parquet OHLCV
│             GET  /api/charts/:symbol/intraday    → nselib 5M/15M/1H candles
│             POST /api/chat                       → Groq chatbot, session-aware
│             GET  /api/broker/status              → broker connection status
│             GET  /api/broker/holdings            → live holdings enriched with intelligence
│             POST /api/broker/sync                → trigger holdings refresh
│             +auth, portfolio, backtest, research, execution endpoints
│
├── Phase 19  refresh_scheduler       → APScheduler daily pipeline 18:00 IST
│             Pipeline: 5A→6A→6B→6C→7A→18→8A→8B→12→13→9
│
├── Phase 20  portfolio_engine        → transactions.csv, unrealised P&L, sector allocation
├── Phase 21  backtest_engine         → 3 strategies, 5 horizons, Sharpe/drawdown/win-rate
├── Phase 22  broker_adapter          → Dhan API + CSV import; broker sync engine
├── Phase 23  screener_engine         → 2406-symbol screener (15 filters), comparator, notes
├── Phase 24  execution_engine        → risk engine, paper/live orders, signal recommender
└── Phase 25  auth store              → SQLite sessions, roles, API keys (off by default)
```

---

## Layer 6 — User Interfaces

```
frontend/ (React 18 + TypeScript + Vite, port 5173)
│
├── Dashboard         /              Market regime, PCR, flows, sectors, watchlist
├── Sectors           /sectors       29 sectors grouped by rotation signal
├── Sector Detail     /sectors/:s    Sector scores + top 10 stocks
├── Watchlist         /watchlist     2441 symbols, paginated, label filter, ACTION badge
├── Stock Detail      /stocks/:sym   7-factor TradeIntelligenceCard + all intelligence panels
├── Participant       /participant   FII/DII/PRO/CLIENT cards + 90D area chart
├── Corporate         /corporate     Block/bulk deals + upcoming catalysts
├── Charts            /charts        TradingView OHLCV (5M/15M/1H + 1D-5Y), IST timestamps
├── Portfolio         /portfolio     Positions, P&L, sector allocation
├── Backtest          /backtest      Strategy replay, equity curve, Sharpe metrics
├── Broker            /broker        Live holdings from Dhan, enriched with platform intelligence
├── Research          /research      Screener (15 filters), stock comparator, thesis notes
├── Execution         /execution     Signal recommender, risk engine, paper/live orders
├── AI Chat           /chat          Groq Llama chatbot, 6 suggested prompts, session-aware
├── Data Control      /data          Engine runner, acquisition pipeline, freshness monitor
├── Settings          /settings      Platform config, alert config, broker connections
├── Login             /login         JWT auth (enabled via /api/auth/setup)
└── Admin             /admin         Auth config, user management (admin role only)
│
Telegram Bot (live)
├── P1-P10 alert delivery (HTML formatted)
├── Daily digest 18:30 IST
└── Post-market signal checks 19:00 IST
```

---

## Data Dependency Tree (key chains)

```
NSE Bhavcopy
    └── equity_master (2123 EQ symbols)
        └── company_fundamentals_master (sector/theme/ISIN)
            └── classification_v4 (99.53% coverage)
                │
                ├── sector_capital_flow (6A)  ←─ bhavcopy 7813 files (turnover weights)
                │   └── sector_flow_scores (6B)
                │       └── sector_rotation_intelligence (6C)  ←─ index_strength (Phase 3)
                │           └── bull_run_probability (8B)  ←─ price_momentum (8A)
                │               └── ML models (Phase 12)
                │                   └── trade_conviction_scores (Phase C)
                │
                └── participant_flows (5B)  ←─ institutional_positioning_history (5A)
                    └── participant_intelligence (5C)  → Market Regime
                        └── alert_engine (Phase 9)
                            └── Telegram delivery

financial_results (Phase 15)
    └── valuation_scores (15B)
        └── trade_conviction_scores (Phase C)  ←─ (one of 7 factors)

quarterly_shp (Phase 15C)
    └── holding_trends (Phase 16)
        └── trade_conviction_scores (Phase C)  ←─ (QoQ delta factor)
```

---

## Groq / AI Data Flow

```
User Query (ChatPage.tsx)
    │
    ▼
POST /api/chat  →  intent_router (keyword → MARKET/SECTOR/STOCK/CORPORATE/RESEARCH)
    │
    ▼
chat_engine.py
    ├── RAG retrieval: hybrid_retriever.retrieve(query, domain)
    │       ├── BM25 sparse search (keyword match)
    │       └── FAISS dense search (sentence-transformer embedding)
    │           → RRF fusion top-5 → injected into system prompt
    │
    ├── Tool loop (MAX_TOOL_ROUNDS=3, parallel_tool_calls=False):
    │       Groq llama-3.3-70b-versatile selects from 11 tools:
    │       get_market_context | get_participant_flows | get_sectors_by_signal
    │       get_stock_bull_run | get_sector_detail | get_corporate_deals
    │       get_upcoming_catalysts | get_top_stocks | get_ml_scores
    │       get_stock_technical | get_fno_intelligence
    │
    │       Each tool reads from intelligence CSVs in data/intelligence/
    │       Tool results appended to messages → next round
    │
    └── Final answer generated (or fallback plain-text call if tool_use_failed/rate_limit)
```

---

## Intelligence Signal Cascade (per stock, daily)

```
bhavcopy[symbol, date]
    │ close, volume, high, low
    ▼
price_momentum_engine
    │ ret_30d, ret_90d, ret_365d, vol_ratio, price_score
    ▼                          ▼
technical_engine          fno_engine
    │ DMA20/50/200             │ futures OI, oi_signal
    │ trend_signal             │ LONG_BUILDUP / SHORT_COVER
    ▼                          ▼
bull_run_probability_engine ←─ sector_rotation_intelligence (sector signal)
    │                      ←─ institutional_deal_signals (block/bulk net)
    │                      ←─ corporate_confidence_scores (12M rolling)
    │ bull_run_score, label (EMERGING / STRONG_CANDIDATE / ...)
    ▼
ml_scorer (Phase 12)
    │ accumulation_score, ml_bull_run_score
    ▼
trade_conviction_engine (Phase C)  ←─ valuation_scores (P/E, ROE)
    │                              ←─ holding_trends (QoQ FII/DII deltas)
    │                              ←─ management_sentiment (tone score)
    │ conviction_score (0-100)
    │ action: STRONG_BUY | BUY | HOLD | REDUCE | EXIT
    ▼
alert_engine (P9 TRADE_CONVICTION ≥ 75)
    │
    ▼
Telegram → TradeIntelligenceCard (frontend)
```

---

## File Count Summary

| Layer | Location | Files / Rows |
|-------|----------|-------------|
| Raw bhavcopy | data/bhavcopy/equity/ | 7,813 CSV files |
| Intelligence outputs | data/intelligence/ | ~20 CSV + JSON files |
| NSE structured data | data/NSE/ | equity_master, results, shareholding, corporate_actions |
| Cache | data/cache/stock_history/ | per-symbol OHLCV parquet |
| Engines | engines/ | ~50+ Python files across 12 subdirectories |
| Backend | backend/ | main.py + 15+ routers |
| Frontend | frontend/src/ | 14 pages + ~10 components |
| AI indexes | data/intelligence/rag_indexes/ | FAISS .index + BM25 .pkl |
