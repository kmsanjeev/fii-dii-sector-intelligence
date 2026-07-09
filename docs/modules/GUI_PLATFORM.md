# GUI PLATFORM
## Capital Flow Intelligence Platform | Updated 2026-07-09

---

# Module Overview

15-page React application. Dark terminal aesthetic (#0A0D14). Score-first layout.
Users understand market conditions within 3 seconds of opening the app.

---

# Status: COMPLETE 100% (Phase 11 + CH extensions)

Phase 11 delivered all core pages. Subsequent phases added:
- Phase CH: KLineChart Pro full-page chart (/fullchart/:symbol)
- Phase TI: Technical indicator redesign (RSI/MACD/ATR/BB/OBV/ADX card)
- Phase SH: 8-score header panel + 5-quarter shareholding trend cards
- Phase UI-S: Sectors relative score + FII regime badge + Social Pulse card fix

---

# Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript + Vite |
| Styling | Inline styles (dark design system via C.* tokens) + Recharts |
| State | Zustand (global: regime, selected sector/symbol) |
| Data Fetching | TanStack Query v5 (auto-refetch every 5 min) |
| Routing | React Router v6 |
| Charts (flows) | Recharts (area, bar, treemap) |
| Charts (OHLCV) | KLineChart Pro v0.1.1 (klinecharts v9.8.12 core) |
| Backend | FastAPI + Uvicorn (port 8001, Phase 10) |
| WebSocket | Regime/sector push updates |

---

# Design System

Colors (C.* token object defined in each page):
- Background: #0A0D14 (dark terminal)
- Surface: #141720
- Border: #1E2332
- Score gradient: red (0) -> amber (40) -> green (65) -> emerald (80+)
- Text minimum: 10px enforced across all pages (typography audit 2026-07-08)

Components:
- ScoreGauge: circular 0-100 score ring with color gradient
- ScoreChip: compact label + value chip for 8-score header panel
- FlowCard: participant score with trend direction
- CapFlowBadge: STRONG_CANDIDATE / EMERGING / WATCHLIST pill
- RegimeBanner: NEUTRAL/DISTRIBUTION/ACCUMULATION header strip
- SectorTile: sector name + combined_score + rotation_signal + relative rank
- AstroSignalCard: planet chips, retrograde warning, sector astro signals
- KundliCard: 6-tab Vedic chart UI (Overview/Planets/Houses/Dasha/Gann/Report)
- TradeIntelligenceCard: 7-factor entry/exit synthesis (Phase B)

---

# 15 Pages

| Page | Route | Status | Notes |
|------|-------|--------|-------|
| Dashboard | / | COMPLETE | Regime, top sectors, top stocks, Social Pulse, participant bars |
| Sectors | /sectors | COMPLETE | Treemap heatmap, rotation table, relative cross-sectional score, FII regime badge |
| Sector Detail | /sectors/:id | COMPLETE | Sector drill-down, constituent stocks, flow history |
| Stocks | /stocks | COMPLETE | 2441-symbol table, 15 filters, sort, pagination |
| Stock Detail | /stocks/:symbol | COMPLETE | 8-score panel, 6 tech indicator layers, 5-quarter SHP, KundliCard, AstroCard, TradeCard |
| Participant | /participant | COMPLETE | FII/DII/PRO/CLIENT timeline, conviction bars, smart money divergence |
| Corporate | /corporate | COMPLETE | Deal table, event calendar, confidence heatmap |
| Chat | /chat | COMPLETE | WebSocket, markdown, tool-use citations, Kundli tool |
| Portfolio | /portfolio | COMPLETE | Transactions, P&L, allocation (Phase 20) |
| Backtest | /backtest | COMPLETE | 3 strategies, 5 horizons, Sharpe (Phase 21) |
| Broker | /broker | COMPLETE | Dhan R/O sync, positions (Phase 22) |
| Research | /research | COMPLETE | Screener, comparator, notes (Phase 23) |
| Execution | /execution | COMPLETE | Risk engine, paper/live orders, signal recommender (Phase 24) |
| Admin | /admin | COMPLETE | Auth config, API keys, data freshness (Phase 25) |
| Full Chart | /fullchart/:symbol | COMPLETE | KLineChart Pro: 30+ indicators, drawing tools, VWAP/ST/HMA/VOLMain, watchlist, settings panel |

---

# Full Chart Page (/fullchart/:symbol)

Built in Phase CH. Rendered outside AppShell (full-viewport, no sidebar).

**Library:** KLineChart Pro v0.1.1 + klinecharts v9.8.12
**Datafeed (OurDatafeed):**
- searchSymbols: /charts/symbols?q= with debounce
- getHistoryKLineData: /api/stocks/{symbol}/ohlcv?tf=&limit=
- subscribe/unsubscribe: 60s polling interval for live data

**Timeframes:** 5M / 15M / 1H / 1D / 1W / 1M / 3M

**Custom Indicators (frontend/src/indicators/customIndicators.ts):**
- VWAP: session-resetting at UTC date boundary; IndicatorSeries.Price
- Supertrend(7,3): Wilder ATR; teal bull / red bear with null gaps for segment coloring
- HMA(9): Hull MA via double WMA; lag-reduced smooth line
- VOLMain: canvas draw() on price pane (IndicatorSeries.Price + figures:[]);
  paints 20% bottom zone bars via bounding.bottom + xAxis.convertToPixel(barIndex);
  returns true from draw() to skip default rendering

**Settings Panel:** candle type, up/down colors, grid, font size, axes, crosshair (setStyles())

**Watchlist Panel:** localStorage cfip-wl; multi-list; LTP + abs change + change% (60s poll);
  multi-symbol add (space/comma/newline delimiters); autocomplete with arrow key nav

**Known Library Bugs Worked Around:**
- Pro v0.1.1 CSS: `var(---klinecharts-pro-text-color)` (3 dashes) -> inject override CSS on mount
- Pro v0.1.1 input: binds "change" event not "input" -> SymbolSearchBar component in top bar
  with debounced API search and full keyboard navigation (independent of Pro's internal search)

---

# Directory

```
frontend/
  src/
    indicators/
      customIndicators.ts      <- VOLMain, VWAP, Supertrend, HMA (side-effect import)
    pages/
      Dashboard.tsx            <- Social Pulse, heatmap, participant bars
      Sectors.tsx              <- Treemap, rotation table, FII badge, relative score
      SectorDetailPage.tsx
      StocksPage.tsx           <- 2441-symbol screener, 8-score panel
      StockDetailPage.tsx      <- Full stock detail, 8-score header, SHP trends
      FullChartPage.tsx        <- KLineChart Pro, OurDatafeed, WatchlistPanel, SymbolSearchBar
      ParticipantPage.tsx
      CorporatePage.tsx
      ChatPage.tsx
      PortfolioPage.tsx
      BacktestPage.tsx
      BrokerPage.tsx
      ResearchPage.tsx
      ExecutionPage.tsx
      AdminPage.tsx
    api/
      client.ts                <- All API types + axios; /api/stocks/{symbol} returns 8-score fields
    components/
      TradeIntelligenceCard.tsx
    App.tsx                    <- Routes; /fullchart renders outside AppShell
  package.json                 <- klinecharts@9.8.12, @klinecharts/pro@0.1.1
  vite.config.ts
```

---

# Dependencies

- Phase 10 (FastAPI Backend) must be running on port 8001
- Node.js 18+ required
- KLineChart Pro requires: `npm install klinecharts @klinecharts/pro`
