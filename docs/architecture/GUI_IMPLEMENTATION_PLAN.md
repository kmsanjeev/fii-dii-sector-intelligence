# GUI Implementation Plan — Capital Flow Intelligence Platform

**Status:** FULLY IMPLEMENTED | React + FastAPI  
**Date:** 2026-06-29 | **Last updated:** 2026-07-09  
**Supersedes:** `GUI_ARCHITECTURE.md` (vision doc) — this document is the build spec  
**IMPLEMENTATION NOTE:** Actual build differs from original plan in three areas:  
1. Styling: inline styles via C.* token objects (NOT Tailwind CSS / shadcn / Radix / Framer Motion)  
2. OHLCV charting: KLineChart Pro v0.1.1 (klinecharts v9.8.12) with custom indicators (NOT TradingView Lightweight Charts)  
3. Frontend directory: `frontend/` (NOT `gui/`)

---

## 1. Technology Stack

### Frontend
| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | React 18 + TypeScript | Component model, type safety, ecosystem |
| Build Tool | Vite | Fast HMR, ESM, smaller bundles than CRA |
| Styling | Inline styles via C.* token objects | Dark terminal theme; no Tailwind, no shadcn/ui, no Radix UI |
| Component Base | Custom components | No Radix UI primitives — all components hand-built with inline styles |
| Charts (flows) | Recharts | Recharts for sector heatmaps, flow charts |
| Charts (OHLCV) | KLineChart Pro v0.1.1 (klinecharts v9.8.12) | Candlestick + custom indicators (VOLMain/VWAP/Supertrend/HMA); NOT TradingView |
| State (server) | TanStack Query v5 (React Query) | Caching, refetch, background sync |
| State (client) | Zustand | Lightweight, no boilerplate for UI state |
| Routing | React Router v6 | Declarative, nested layouts |
| Animations | CSS transitions (inline styles) | No Framer Motion — transitions handled via inline style properties |
| Tables | TanStack Table v8 | Virtualized, sortable, filterable |
| Icons | Lucide React | Consistent, tree-shakeable |
| Date Handling | date-fns | IST-aware, no Moment.js |
| Forms | React Hook Form + Zod | Performant, typed validation |
| Notifications | Sonner | Toast notifications for alerts |

### Backend API (Python — bridging engines to frontend)
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (already in requirements.txt) |
| ASGI Server | Uvicorn |
| WebSocket | FastAPI WebSocket for live flow ticker |
| Auth | JWT + httpOnly cookies |
| CORS | FastAPI CORSMiddleware |
| Response Format | JSON — snake_case from Python → camelCase via interceptor |

---

## 2. Repository Structure

```
fii-dii-sector-intelligence/
├── frontend/                         ← React frontend (ACTUAL directory — NOT gui/)
│   ├── public/
│   │   ├── favicon.ico
│   │   └── index.html
│   ├── src/
│   │   ├── main.tsx                  ← Entry point
│   │   ├── App.tsx                   ← Router + Layout shell
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── api/                      ← All API calls (React Query hooks)
│   │   │   ├── client.ts             ← Axios instance with auth interceptor
│   │   │   ├── hooks/
│   │   │   │   ├── useDashboard.ts
│   │   │   │   ├── useMarket.ts
│   │   │   │   ├── useSectors.ts
│   │   │   │   ├── useThemes.ts
│   │   │   │   ├── useStocks.ts
│   │   │   │   ├── usePortfolio.ts
│   │   │   │   └── useInstitutional.ts
│   │   │   └── ws/
│   │   │       └── useFlowTicker.ts  ← WebSocket hook for live flows
│   │   │
│   │   ├── components/               ← Reusable UI components
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.tsx      ← Sidebar + Topbar + Main content
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Topbar.tsx        ← Market clock, regime badge, search
│   │   │   │   └── MobileNav.tsx
│   │   │   ├── cards/
│   │   │   │   ├── RegimeCard.tsx    ← "Risk-On / Accumulation" badge
│   │   │   │   ├── FlowCard.tsx      ← FII/DII/PRO/CLIENT buy-sell-net
│   │   │   │   ├── ScoreCard.tsx     ← Score with trend sparkline
│   │   │   │   └── AlertCard.tsx
│   │   │   ├── charts/
│   │   │   │   ├── SectorHeatmap.tsx ← Color-coded treemap/heatmap
│   │   │   │   ├── FlowWaterfall.tsx ← Buy → Sell → Net waterfall chart
│   │   │   │   ├── CapitalFlowCascade.tsx ← Market→Sector→Theme→Stock sunburst
│   │   │   │   ├── OhlcvChart.tsx    ← KLineChart Pro v0.1.1 (klinecharts v9.8.12)
│   │   │   │   ├── AccumulationChart.tsx ← Area chart with score overlay
│   │   │   │   ├── ParticipantPie.tsx ← FII/DII/PRO/CLIENT share pie
│   │   │   │   └── Sparkline.tsx
│   │   │   ├── tables/
│   │   │   │   ├── StockTable.tsx    ← Virtualized, sortable stock list
│   │   │   │   ├── SectorTable.tsx
│   │   │   │   └── FlowHistoryTable.tsx
│   │   │   ├── badges/
│   │   │   │   ├── RegimeBadge.tsx   ← "ACCUMULATION" / "DISTRIBUTION"
│   │   │   │   ├── ConfidenceBadge.tsx
│   │   │   │   └── SignalBadge.tsx
│   │   │   └── ui/                   ← Radix wrappers (Button, Input, etc.)
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Select.tsx
│   │   │       ├── Dialog.tsx
│   │   │       ├── Tooltip.tsx
│   │   │       └── Skeleton.tsx
│   │   │
│   │   ├── pages/                    ← One file per route
│   │   │   ├── Dashboard.tsx         ← / (home)
│   │   │   ├── Market.tsx            ← /market
│   │   │   ├── Sectors.tsx           ← /sectors
│   │   │   ├── SectorDetail.tsx      ← /sectors/:slug
│   │   │   ├── Themes.tsx            ← /themes
│   │   │   ├── ThemeDetail.tsx       ← /themes/:slug
│   │   │   ├── Stocks.tsx            ← /stocks (screener)
│   │   │   ├── StockDetail.tsx       ← /stocks/:symbol
│   │   │   ├── Portfolio.tsx         ← /portfolio
│   │   │   ├── Research.tsx          ← /research
│   │   │   ├── AiAssistant.tsx       ← /ai
│   │   │   ├── Reports.tsx           ← /reports
│   │   │   └── Settings.tsx          ← /settings
│   │   │
│   │   ├── store/                    ← Zustand stores
│   │   │   ├── useUIStore.ts         ← sidebar collapse, theme, mode
│   │   │   ├── useWatchlistStore.ts  ← watchlist symbols (persisted)
│   │   │   └── useFlowStore.ts       ← live flow ticker state
│   │   │
│   │   ├── types/                    ← TypeScript interfaces
│   │   │   ├── market.ts
│   │   │   ├── sector.ts
│   │   │   ├── stock.ts
│   │   │   ├── institutional.ts
│   │   │   └── portfolio.ts
│   │   │
│   │   ├── lib/                      ← Utilities
│   │   │   ├── formatters.ts         ← INR formatting, % formatting, IST dates
│   │   │   ├── colors.ts             ← Score→color mapping (green-yellow-red)
│   │   │   └── constants.ts          ← API base URL, WebSocket URL
│   │   │
│   │   └── styles/
│   │       └── globals.css           ← CSS variables (no Tailwind directives)
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env.example
│
└── api/                              ← FastAPI backend (actual: backend/)
    ├── main.py                       ← FastAPI app, CORS, routers
    ├── routers/
    │   ├── dashboard.py
    │   ├── market.py
    │   ├── sectors.py
    │   ├── themes.py
    │   ├── stocks.py
    │   ├── institutional.py
    │   ├── portfolio.py
    │   └── reports.py
    ├── models/                       ← Pydantic response models
    │   ├── market.py
    │   ├── sector.py
    │   └── stock.py
    └── services/                     ← Reads from engines/ outputs
        ├── sector_service.py
        ├── stock_service.py
        └── flow_service.py
```

---

## 3. Design System

### Color Palette (CSS Variables — supports dark/light)

```css
/* globals.css */
:root {
  /* Background */
  --bg-primary:   #0A0D14;   /* page background — near-black */
  --bg-surface:   #111827;   /* cards, sidebars */
  --bg-elevated:  #1F2937;   /* hover states, modals */
  --bg-border:    #374151;   /* card borders */

  /* Accent — Institutional Blue */
  --accent-primary:  #3B82F6;   /* FII/institutional color */
  --accent-secondary:#6366F1;   /* DII color */
  --accent-pro:      #F59E0B;   /* PRO color */
  --accent-client:   #EC4899;   /* CLIENT/retail color */

  /* Signal Colors */
  --signal-bull:    #10B981;   /* accumulation, positive */
  --signal-bear:    #EF4444;   /* distribution, negative */
  --signal-neutral: #6B7280;   /* neutral regime */
  --signal-watch:   #F59E0B;   /* watch zone */

  /* Score Gradient (0-100) */
  /* 0-30: Red  30-60: Amber  60-80: Green  80-100: Emerald */

  /* Text */
  --text-primary:   #F9FAFB;
  --text-secondary: #9CA3AF;
  --text-muted:     #6B7280;

  /* Chart Grid */
  --chart-grid:     #1F2937;
}
```

### Typography

```
Font: Inter (Google Fonts)
Monospace: JetBrains Mono (for prices, scores)

Scale:
  xs:   11px — table cells, badges
  sm:   13px — secondary labels
  base: 14px — body text
  lg:   16px — card headings
  xl:   20px — page headings
  2xl:  28px — hero numbers (FII net flow etc.)
  3xl:  36px — dashboard hero metric
```

### Score Color Mapping (`lib/colors.ts`)

NOTE: In the actual implementation, color tokens are defined in C.* objects (inline style token system) rather than Tailwind classes.

```typescript
// Actual implementation uses inline style objects via C.* token system, e.g.:
// color: C.bull  (#10B981)  — accumulation / positive
// color: C.bear  (#EF4444)  — distribution / negative
// background: C.surface     — card backgrounds
// The following Tailwind-class version is the original design spec only:
export function scoreToColor(score: number): string {
  if (score >= 80) return '#10B981'; // emerald — Strong accumulation
  if (score >= 60) return '#22C55E'; // green   — Accumulating
  if (score >= 40) return '#F59E0B'; // amber   — Neutral / watch
  if (score >= 20) return '#F97316'; // orange  — Weak / caution
  return '#EF4444';                   // red     — Distribution
}
```

---

## 4. Routing Architecture

```typescript
// App.tsx
<Routes>
  <Route element={<AppShell />}>
    <Route path="/"             element={<Dashboard />} />
    <Route path="/market"       element={<Market />} />
    <Route path="/sectors"      element={<Sectors />} />
    <Route path="/sectors/:slug" element={<SectorDetail />} />
    <Route path="/themes"       element={<Themes />} />
    <Route path="/themes/:slug" element={<ThemeDetail />} />
    <Route path="/stocks"       element={<Stocks />} />
    <Route path="/stocks/:symbol" element={<StockDetail />} />
    <Route path="/portfolio"    element={<Portfolio />} />
    <Route path="/research"     element={<Research />} />
    <Route path="/ai"           element={<AiAssistant />} />
    <Route path="/reports"      element={<Reports />} />
    <Route path="/settings"     element={<Settings />} />
  </Route>
</Routes>
```

---

## 5. Page Specifications

### Page 1: Dashboard (`/`)

**Purpose:** Answer "What is happening right now?" in under 3 seconds.

**Layout (3-column grid):**
```
┌─────────────────────────────────────────────────────────────┐
│ TOPBAR: [NIFTY 22,450 ▲0.8%] [Market: RISK-ON] [IST 14:32] │
├──────────┬──────────────────────────────────┬───────────────┤
│ SIDEBAR  │  ROW 1: Hero Metrics (4 cards)   │  LIVE FLOW    │
│          │  [Regime] [FII Net] [Top Sector]  │  TICKER       │
│ • Dashboard│ [Top Theme]                    │               │
│ • Market │                                  │  FII:+₹1,230Cr│
│ • Sectors│  ROW 2: Capital Flow Cascade     │  DII: +₹890Cr │
│ • Themes │  [Interactive Sunburst/Sankey]   │  PRO: -₹340Cr │
│ • Stocks │  Market→Sector→Theme→Stock       │  CLIENT:-₹780Cr│
│ • Portfolio                                 │               │
│ • Research│ ROW 3: Opportunity Grid         │  (WebSocket)  │
│ • AI     │  [Top 5 Sectors] [Top 5 Themes]  │               │
│ • Reports│  [Top 10 Stocks to Watch]        │               │
│ • Settings│                                 │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

**Key Components:**
- `RegimeCard` — large badge: "ACCUMULATION | Risk-On" with color
- `FlowCard` — FII/DII/PRO/CLIENT daily BUY/SELL/NET in ₹Cr
- `CapitalFlowCascade` — interactive Sankey: money → sectors → themes → stocks
- `OpportunityGrid` — sorted by score, click → detail page
- Live Flow Ticker (right panel) — WebSocket updates every 5 min during market hours

---

### Page 2: Market (`/market`)

**Purpose:** Full picture of market health.

**Sections:**
1. **Market Regime Panel** — Bull/Bear/Accumulation/Distribution with historical chart
2. **Index Dashboard** — NIFTY 50, MIDCAP 150, SMALLCAP 250, BANK NIFTY (4 cards)
3. **Institutional Flow Timeline** — Area chart: FII + DII flows for last 30 days
4. **Advance/Decline Chart** — Breadth visualization
5. **Volatility Monitor** — India VIX chart
6. **FII Segment Breakdown** — Cash vs F&O flows (table + bar)

---

### Page 3: Sectors (`/sectors`)

**Purpose:** Sector rotation at a glance.

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│  SECTOR HEATMAP (full width)                           │
│  29 sectors, color = 7-day flow score                  │
│  size = market cap weight, click → /sectors/:slug      │
├─────────────────────┬──────────────────────────────────┤
│  SECTOR RANKING     │  ROTATION CHART                  │
│  Table: Rank, Score │  4-quadrant (momentum vs score): │
│  7d Δ, FII Flow,    │  Leaders | Emerging              │
│  Momentum           │  Weakening | Laggards            │
└─────────────────────┴──────────────────────────────────┘
```

**`SectorDetail` (`/sectors/:slug`):**
- Sector description + stocks list
- FII flow history (30/90/180 days)
- Top 10 stocks by accumulation score (table)
- Themes belonging to this sector
- Capital flow chart: sector vs NIFTY 50

---

### Page 4: Themes (`/themes`)

**Purpose:** Narrative-level opportunity detection.

**Layout:** Same pattern as Sectors.
- 18 platform themes in heatmap
- Click → `/themes/:slug` with stocks under that theme
- Emerging theme badge: "NEW ▲" for themes appearing in last 30 days

---

### Page 5: Stocks (`/stocks`) — Screener

**Purpose:** Find stocks matching capital flow criteria.

**Filter Panel (left):**
```
• Sector: [dropdown — all 29]
• Theme: [dropdown — all 18]
• Accumulation Score: [slider 0-100]
• FII Activity: [Buying / Selling / Neutral]
• Market Cap: [Large / Mid / Small]
• Minimum Sessions: [5 / 20 / 60]
• Series: EQ only (always enforced)
```

**Results Panel (right):**
- Virtualized table (2000+ stocks)
- Columns: Symbol, Sector, Theme, Score, FII, DII, 7d Chg, Volume Ratio
- Row click → `/stocks/:symbol`

---

### Page 6: StockDetail (`/stocks/:symbol`)

**Purpose:** Complete picture of one stock.

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  [RELIANCE] [RELIANCE INDUSTRIES] [OIL & GAS]           │
│  ₹2,890.50  ▲ 1.24%   Vol: 3.2M   Del: 65.4%           │
├──────────────────────────┬──────────────────────────────┤
│  OHLCV CHART             │  SCORE CARDS (5 scores)      │
│  (TradingView LC)        │  Accumulation:  78/100 ●     │
│  Candlestick + Volume    │  Institutional: 65/100 ●     │
│  Overlay: Delivery %     │  Fundamental:   55/100 ●     │
│  Overlay: FII flow       │  Momentum:      82/100 ●     │
│                          │  Risk:          40/100 ●     │
├──────────────────────────┴──────────────────────────────┤
│  TABS: [Flow History] [Fundamentals] [CA Events] [AI]   │
│                                                          │
│  Flow History: 90-day FII/DII/PRO/CLIENT flow chart      │
│  Fundamentals: Revenue, PAT, QoQ/YoY growth sparklines  │
│  CA Events:   Splits, Bonuses, Dividends timeline        │
│  AI:          "Why is this stock moving?" AI summary     │
└─────────────────────────────────────────────────────────┘
```

---

### Page 7: Portfolio (`/portfolio`)

**Purpose:** Portfolio health in the context of capital flow.

**Sections:**
1. **Holdings Input** — CSV import or manual entry (symbol + qty + avg_price)
2. **Portfolio Score** — Weighted average of all holding scores
3. **Sector Exposure Donut** — How much % is in each sector vs NIFTY 50 weights
4. **Theme Exposure Donut** — Theme concentration
5. **Risk Matrix** — Risk score per holding (color-coded)
6. **AI Portfolio Review** — "Your portfolio has 40% in IT. IT momentum is weakening. Consider reducing."

---

### Page 8: AI Assistant (`/ai`)

**Purpose:** Natural language interface to all platform intelligence.

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  SELECT ANALYST ROLE                                  │
│  [Market Analyst] [Sector Analyst] [Stock Analyst]   │
│  [Portfolio Manager] [Research Assistant]             │
├──────────────────────────────────────────────────────┤
│                                                       │
│  AI CHAT AREA (scrollable)                            │
│  User: Which sectors are accumulating?                │
│  AI:   Based on 30-day flow data, BANKING (+₹4,200Cr) │
│        and IT (+₹2,800Cr) show strong FII inflows...  │
│                                                       │
│  [Context Cards appear inline with AI responses]      │
│                                                       │
├──────────────────────────────────────────────────────┤
│  QUICK PROMPTS:                                       │
│  [Top accumulating stocks] [Sectors weakening]        │
│  [What changed this week] [Risk in my portfolio]      │
│                                                       │
│  TYPE YOUR QUESTION... [Send]                         │
└──────────────────────────────────────────────────────┘
```

**AI Analyst Modes (Zustand state):**
- `market` — overall market context
- `sector` — sector rotation focus
- `stock` — individual stock analysis
- `portfolio` — portfolio review context
- `research` — research validation

---

### Page 9: Reports (`/reports`)

**Purpose:** Pre-generated intelligence reports.

**Categories (tabs):**
- Daily Briefing (auto-generated, last 30 days)
- Weekly Summary
- Monthly Review
- Research Reports
- Download as PDF

---

## 6. Key Components — Detailed Spec

### `CapitalFlowCascade` (Dashboard hero)

```typescript
// Interactive Sankey diagram showing money flow
// Data structure:
type CascadeNode = {
  id: string;          // "market" | "BANKING" | "PSU_BANKS" | "SBIN"
  level: 'market' | 'sector' | 'theme' | 'stock';
  flow_cr: number;     // ₹Cr (positive = buying, negative = selling)
  score: number;       // 0-100
  change_7d: number;   // % change
}

// Library: react-flow-renderer or custom SVG
// Color: green (buying) → red (selling)
// Click on node → navigate to relevant detail page
```

### `SectorHeatmap` (Sectors page)

```typescript
// Treemap where:
// - Size = market cap weight in NIFTY 500
// - Color = 7-day accumulation score (red→amber→green)
// - Hover = tooltip with FII flow + score
// - Click = navigate to /sectors/:slug
// Library: Recharts Treemap
```

### `OhlcvChart` (StockDetail)

```typescript
// KLineChart Pro v0.1.1 (klinecharts v9.8.12)
// Overlays:
//   - 20 EMA (orange)
//   - 50 EMA (blue)
//   - Volume histogram (bottom pane)
//   - Delivery % line (second pane, 0-100%)
//   - FII Flow bar (third pane, red/green)
```

### `FlowCard` (Dashboard + Market page)

```typescript
type FlowCardProps = {
  participant: 'FII' | 'DII' | 'PRO' | 'CLIENT';
  buy_cr: number;
  sell_cr: number;
  net_cr: number;
  trend: 'buying' | 'selling' | 'neutral';
  sparkline_7d: number[]; // last 7 net flows
}
// Color: FII=blue, DII=indigo, PRO=amber, CLIENT=pink
```

---

## 7. FastAPI Backend Contract

### Base URL: `http://localhost:8000/api/v1`

### Endpoints

```
GET  /dashboard/summary           → regime, top flows, top sectors, top themes
GET  /market/regime               → current regime + history
GET  /market/flow                 → today's FII/DII/PRO/CLIENT flows
GET  /sectors/                    → all 29 sectors with score + flow
GET  /sectors/{slug}              → single sector detail
GET  /sectors/{slug}/stocks       → stocks in sector with scores
GET  /themes/                     → all 18 themes with score + flow
GET  /themes/{slug}               → single theme detail
GET  /stocks/                     → paginated stock list with filters
GET  /stocks/{symbol}             → single stock full detail
GET  /stocks/{symbol}/flow        → 90-day flow history
GET  /stocks/{symbol}/ohlcv       → OHLCV data
GET  /stocks/{symbol}/fundamentals→ quarterly results
GET  /institutional/flow?days=30  → participant flow history
GET  /reports/                    → report list
GET  /reports/{id}                → report content

WS   /ws/live-flow                → WebSocket: live flow updates during market hours
```

### Standard Response Envelope

```typescript
interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  meta: {
    generated_at: string;  // ISO8601 IST
    data_as_of: string;    // trading date
    cache_hit: boolean;
  };
}
```

---

## 8. State Management

### TanStack Query (server state)

```typescript
// All API calls are React Query hooks
// Cache time: 5 minutes for most data
// Stale time: 1 minute (re-fetch in background)
// Real-time: WebSocket bypass for live ticker only

const { data, isLoading } = useQuery({
  queryKey: ['sectors', 'all'],
  queryFn: () => api.get('/sectors/'),
  staleTime: 60_000,
  refetchInterval: 300_000,  // refetch every 5 min during market hours
});
```

### Zustand (client-only state)

```typescript
// useUIStore
interface UIStore {
  sidebarCollapsed: boolean;
  theme: 'dark' | 'light';
  userMode: 'child' | 'investor' | 'trader' | 'professional' | 'admin';
  toggleSidebar: () => void;
  setMode: (mode: UIStore['userMode']) => void;
}

// useWatchlistStore (persisted to localStorage)
interface WatchlistStore {
  symbols: string[];
  addSymbol: (symbol: string) => void;
  removeSymbol: (symbol: string) => void;
}

// useFlowStore (WebSocket state)
interface FlowStore {
  connected: boolean;
  lastUpdate: string | null;
  liveFlows: Record<string, ParticipantFlow>;
}
```

---

## 9. IST-Aware Date Handling

```typescript
// lib/formatters.ts
import { format, parseISO } from 'date-fns';
import { toZonedTime } from 'date-fns-tz';

const IST_TZ = 'Asia/Kolkata';

export function formatIST(isoString: string, fmt = 'dd MMM yyyy HH:mm'): string {
  return format(toZonedTime(parseISO(isoString), IST_TZ), fmt);
}

export function formatINR(value: number): string {
  if (Math.abs(value) >= 100) return `₹${(value / 100).toFixed(0)}Cr`;  // Crores
  return `₹${value.toFixed(2)}Cr`;
}

export function formatPct(value: number, decimals = 2): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}
```

---

## 10. User Mode System

Controlled by `useUIStore.userMode`. Each mode gates specific features:

| Feature | Child | Investor | Trader | Professional | Admin |
|---------|-------|----------|--------|--------------|-------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sector/Theme | ✅ | ✅ | ✅ | ✅ | ✅ |
| Stocks Screener | ✅ (limited) | ✅ | ✅ | ✅ | ✅ |
| Portfolio | ❌ | ✅ | ✅ | ✅ | ✅ |
| Broker Execution | ❌ | ❌ | ✅ | ✅ | ✅ |
| Raw Data Access | ❌ | ❌ | ❌ | ✅ | ✅ |
| Admin Panel | ❌ | ❌ | ❌ | ❌ | ✅ |
| AI Assistant | ❌ | ✅ | ✅ | ✅ | ✅ |

---

## 11. Mobile Responsiveness

**Mobile-first components:**
- Bottom navigation bar (replaces sidebar on mobile)
- Card-based layouts (single column on < 768px)
- Simplified Dashboard: Regime → Top Flow → Watchlist only
- Heavy analytics (heatmaps, flow cascade) redirect to "Open on Desktop"

**Breakpoints (Tailwind):**
```
sm:  640px  — phone landscape
md:  768px  — tablet
lg:  1024px — desktop
xl:  1280px — wide desktop (full heatmaps)
2xl: 1536px — Bloomberg-style multi-panel
```

---

## 12. Performance Rules

1. **Code split every page** — `React.lazy()` on every route
2. **Skeleton loaders** — Never show empty space; always skeleton while loading
3. **Virtualize all tables** — TanStack Virtual for stock lists (2000+ rows)
4. **Image-free charts** — All charts rendered as SVG/Canvas (no PNGs)
5. **API response caching** — TanStack Query caches; backend returns `Cache-Control: max-age=60`
6. **WebSocket only during market hours** — detect 09:14–15:31 IST; disconnect outside
7. **Lazy-load heavy chart libs** — Recharts and TV Lightweight Charts loaded per page

---

## 13. Build & Dev Setup

```bash
# Setup — ACTUAL implementation (frontend/ directory)
cd frontend
npm install

# Actual packages installed (differs from original plan):
# npm install @tanstack/react-query @tanstack/react-table @tanstack/react-virtual
# npm install react-router-dom zustand
# npm install recharts                  ← flows/heatmaps
# npm install klinecharts               ← v9.8.12, OHLCV candlestick charts (NOT lightweight-charts)
# npm install lucide-react sonner date-fns date-fns-tz axios
# NO: @radix-ui/* framer-motion tailwindcss (NOT used in actual implementation)

# Dev
npm run dev            # Vite dev server → http://localhost:5173
py -3.11 -m uvicorn backend.main:app --port 8001 --reload  # FastAPI backend

# Build
npm run build          # Output: frontend/dist/
```

---

## 14. Implementation Phases

| Phase | Deliverable | Status |
|-------|------------|--------|
| GUI-1 | AppShell (sidebar, topbar, routing) | COMPLETE |
| GUI-2 | Design system (C.* tokens, inline styles, components) | COMPLETE |
| GUI-3 | Dashboard page | COMPLETE |
| GUI-4 | FastAPI backend + real data wiring | COMPLETE |
| GUI-5 | Sectors + Stock pages | COMPLETE |
| GUI-6 | Stocks screener + StockDetail with TradeIntelligenceCard | COMPLETE |
| GUI-7 | Market + Participant pages | COMPLETE |
| GUI-8 | Portfolio + Backtest + Broker + Research + Execution pages | COMPLETE |
| GUI-9 | AI Chat (multi-provider LLM via Groq/Cerebras/Gemini/OpenRouter) | COMPLETE |
| GUI-10 | Admin + Settings + Login pages | COMPLETE |
| GUI-11 | WebSocket live flow ticker | COMPLETE |
| GUI-B | KLineChart Pro OHLCV (Phase CH) | COMPLETE — klinecharts v9.8.12 |
| GUI-C | Custom indicators (Phase CH) | COMPLETE — VOLMain/VWAP/Supertrend/HMA |
| GUI-D | 8-score shareholding panel (Phase SH) | COMPLETE |
| GUI-E | Sectors + Social Pulse UI (Phase UI-S) | COMPLETE |

All 15 pages LIVE at http://localhost:5173.
