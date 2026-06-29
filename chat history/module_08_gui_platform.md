# Chat History — Module 08: GUI Platform

> **Append-only. Add new entries at the bottom. Never overwrite.**
> Covers: React frontend, FastAPI backend bridge, design system

---

## Session: 2026-06-29 — GUI Architecture Planning

### Context
User requested: "Also, plan a graphical user interface according to the project description and to access the application using react, UI/UX."

### Technology Stack (Locked)
| Layer | Choice |
|-------|--------|
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS + CSS Variables |
| Charts | Recharts (heatmaps) + TradingView Lightweight Charts (OHLCV) |
| Server State | TanStack Query v5 |
| Client State | Zustand |
| Routing | React Router v6 |
| Backend | FastAPI + Uvicorn (already in requirements.txt) |
| Real-time | WebSocket — live flow ticker (market hours 09:14–15:31 IST only) |

### Design System
- Background: `#0A0D14` (dark terminal)
- Participant colors: FII=`#3B82F6` (Blue), DII=`#6366F1` (Indigo), PRO=`#F59E0B` (Amber), CLIENT=`#EC4899` (Pink)
- Score gradient: Red (0–30) → Amber (30–60) → Green (60–80) → Emerald (80–100)
- 3-Second Rule: market regime + FII net + top sector visible on landing within 3 seconds
- 5 user modes: Child | Investor | Trader | Professional | Admin

### Pages (13 total)
Dashboard, Market, Sectors, SectorDetail, Themes, ThemeDetail, Stocks (screener), StockDetail, Portfolio, Research, AI Assistant, Reports, Settings

### Key Components
- `CapitalFlowCascade` — Sankey: Market → Sector → Theme → Stock (hero component)
- `SectorHeatmap` — Recharts Treemap (size=market cap, color=flow score)
- `FlowCard` — FII/DII/PRO/CLIENT buy/sell/net + 7-day sparkline
- `OhlcvChart` — TradingView LC with delivery% + FII flow overlay panes

### FastAPI Contract
- 14 REST endpoints + 1 WebSocket (`/ws/live-flow`)
- Standard envelope: `{ status, data, meta: { generated_at, data_as_of, cache_hit } }`

### Build Phases (GUI-1 through GUI-13)
GUI-1 AppShell → GUI-2 Design System → GUI-3 Dashboard (mock) → GUI-4 Real data wiring (needs Phase 4A) → GUI-5 Sectors → GUI-6 Stocks Screener → GUI-7 Stock Detail → GUI-8 Themes → GUI-9 AI Chat → GUI-10 Portfolio → GUI-11 Research → GUI-12 Reports → GUI-13 Auth

### Files Created
| File | Notes |
|------|-------|
| `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` | 15-section complete build spec |
| `docs/governance/MODULE_REGISTRY.md` | Module 08 updated: 10% → 25%, ACTIVE DEVELOPMENT |
| `docs/governance/CHANGELOG.md` | v2.2 added |

### Critical Dependency
GUI-4 (real data wiring) requires Phase 4A (Company Fundamentals Master Engine) to be complete.  
GUI-1 through GUI-3 can proceed immediately with mock data.

### Next Actions for This Module
1. Begin GUI-1: AppShell (`gui/src/components/layout/AppShell.tsx`, `Sidebar.tsx`, `Topbar.tsx`)
2. GUI-2: Design system tokens, typography, participant color variables
3. GUI-3: Dashboard skeleton with mock FII/DII flow cards and placeholder Sankey
4. Hold GUI-4 until Phase 4A is complete

---
