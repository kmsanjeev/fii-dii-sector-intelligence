# GUI PLATFORM
## Capital Flow Intelligence Platform | Updated 2026-06-30

---

# Module Overview

10-page React application. Dark terminal aesthetic (#0A0D14). Score-first layout.
Users understand market conditions within 3 seconds of opening the app.

---

# Status: NOT STARTED (Phase 11, after FastAPI Backend)

---

# Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS + shadcn/ui |
| State | Zustand (global: regime, selected sector/symbol) |
| Data Fetching | TanStack Query v5 (auto-refetch every 5 min) |
| Routing | React Router v6 |
| Charts (flows) | Recharts (area, bar, treemap) |
| Charts (price) | TradingView Lightweight Charts (OHLCV candlestick) |
| Backend | FastAPI + Uvicorn (Phase 10) |
| WebSocket | Regime/sector push updates |

---

# Design System

Colors:
- Background: #0A0D14 (dark terminal)
- Surface: #141720
- Border: #1E2332
- Score gradient: red (0) -> amber (40) -> green (65) -> emerald (80+)

Components:
- ScoreGauge: circular 0-100 score ring with color gradient
- FlowCard: participant score with trend direction
- CapFlowBadge: STRONG_CANDIDATE / EMERGING / WATCHLIST pill
- RegimeBanner: NEUTRAL/DISTRIBUTION/ACCUMULATION header strip
- SectorTile: sector name + combined_score + rotation_signal

---

# 10 Pages (Build Order)

GUI-1: AppShell (dark layout, sidebar nav, regime badge in header)
GUI-2: Design System (ScoreGauge, FlowCard, CapFlowBadge, RegimeBanner, SectorTile)
GUI-3: Dashboard (regime card, top sectors, top stocks, participant conviction bars)
GUI-4: Sector Intelligence (Treemap heatmap + rotation signal table + drill-down)
GUI-5: Stock Watchlist (sortable/filterable table, 2441 symbols)
GUI-6: Stock Detail (OHLCV + participant flow overlay + corporate events timeline)
GUI-7: Participant Intelligence (FII/DII/PRO/CLIENT timeline + conviction + divergence)
GUI-8: Corporate Intelligence (deal table + event calendar + confidence heatmap)
GUI-9: AI Chat (WebSocket interface, markdown rendering, tool-use citations)
GUI-10: Settings (alert prefs, Telegram setup, data freshness status)

---

# Directory

frontend/
  src/
    components/ui/         <- shadcn/ui base components
    components/platform/   <- ScoreGauge, FlowCard, SectorTile, etc.
    pages/                 <- 10 page components
    hooks/                 <- useMarketRegime, useSectors, useWatchlist
    store/                 <- Zustand stores
    api/                   <- TanStack Query + axios clients
    main.tsx
  package.json
  vite.config.ts
  tailwind.config.ts

---

# Dependencies

- Phase 10 (FastAPI Backend) must be running
- Node.js 18+ required
