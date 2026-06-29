# Session Log — 2026-06-29 | GUI Planning Phase

## What Was Accomplished

Created `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` — the complete React implementation plan for the Capital Flow Intelligence Platform GUI.

## Key Decisions Made

### Tech Stack (finalized)
- **Frontend:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS v3 + CSS custom properties for dark theme
- **Charts:** Recharts (heatmaps/flows) + TradingView Lightweight Charts (OHLCV)
- **State:** TanStack Query (server) + Zustand (client)
- **Routing:** React Router v6 with nested layouts
- **Backend:** FastAPI (already in requirements.txt) + Uvicorn
- **Real-time:** WebSocket for live flow ticker during market hours only

### Design System
- Dark terminal theme (bg: #0A0D14 near-black)
- FII=Blue, DII=Indigo, PRO=Amber, CLIENT=Pink (consistent participant color coding)
- Score gradient: 0-30 Red → 30-60 Amber → 60-80 Green → 80-100 Emerald
- 3-Second Rule: regime + FII net + top sector visible immediately on Dashboard

### Architecture
- `gui/` directory inside project root (co-located with engines)
- `api/` directory for FastAPI backend serving engine outputs as JSON
- 13 pages with clear routing hierarchy
- 5 user modes: Child, Investor, Trader, Professional, Admin
- Mobile: bottom nav + simplified cards; heavy analytics = desktop only

### Key Components Designed
- `CapitalFlowCascade` — Sankey diagram: Market → Sector → Theme → Stock
- `SectorHeatmap` — Recharts Treemap, size=market cap, color=flow score
- `FlowCard` — FII/DII/PRO/CLIENT buy/sell/net with 7-day sparkline
- `RegimeCard` — "ACCUMULATION | Risk-On" hero badge
- `OhlcvChart` — TV Lightweight Charts with delivery % + FII overlay panes

### FastAPI Contract
- Base: `http://localhost:8000/api/v1`
- 14 REST endpoints + 1 WebSocket (`/ws/live-flow`)
- Standard response envelope: `{ status, data, meta: { generated_at, data_as_of, cache_hit } }`

### IST-Aware Formatting
- `formatIST()` using date-fns-tz
- `formatINR()` for ₹Cr display
- WebSocket connects only during 09:14–15:31 IST

## Implementation Phases Defined (13 phases: GUI-1 to GUI-13)
1. AppShell → 2. Design System → 3. Dashboard (mock) → 4. FastAPI + real data
→ 5. Sectors/Themes → 6. Stocks → 7. Market → 8. Portfolio
→ 9. AI Assistant → 10. Reports → 11. WebSocket → 12. Mobile → 13. Auth

## Important Dependency
**GUI-4 (real data wiring) requires Phase 4A (Company Fundamentals Master Engine) to be complete.**
Do not start GUI-4 until `engines/fundamentals/company_fundamentals_master_engine.py` exists.

## How to Start Building
User should say "start GUI-1" to begin with the AppShell implementation.
