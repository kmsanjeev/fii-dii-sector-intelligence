# Module 10 — FastAPI Backend
## Phase 10 Complete | 2026-06-30

---

## What Was Built

### Directory Structure

backend/
  __init__.py
  main.py                          <- FastAPI app entry point
  routers/
    __init__.py
    market.py                      <- /api/market/*
    sectors.py                     <- /api/sectors/*
    stocks.py                      <- /api/stocks/*
    participant.py                  <- /api/participant/*
    corporate.py                   <- /api/corporate/*
  services/
    __init__.py
    data_loader.py                  <- CSV in-memory cache, 60min auto-reload
  ws/
    __init__.py
    live_ticker.py                  <- WebSocket /ws/live (regime + sectors every 30s)

### backend/services/data_loader.py

Loads all 11 intelligence CSVs at startup into _data dict.
Thread-safe reads via threading.Lock.
Background daemon thread auto-reloads every 3600 seconds.
get(key) -> Optional[DataFrame]
freshness() -> dict of load timestamps

11 datasets: participant_intel, participant_flows, sector_rotation, sector_flows,
  bull_run, bull_run_watchlist, deal_signals, event_calendar, upcoming_catalysts,
  corporate_confidence, price_momentum

### backend/main.py

FastAPI app with:
- CORS for React dev ports (3000, 5173, 5174)
- @app.on_event("startup") -> data_loader.startup()
- 5 routers: market, sectors, stocks, participant, corporate
- /ws/live WebSocket (live_ticker_endpoint)
- /health and / root endpoints

Start: py -3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs

### API Endpoints (16 tested, all PASS)

Market:
  GET /health                              200 {status, datasets_loaded, datasets_total}
  GET /api/market/regime                   200 {regime, smart_money_score, fii_conviction_pct, flow_scores, data_date}
  GET /api/market/freshness                200 {key: timestamp}

Participant:
  GET /api/participant/latest              200 {Market_Regime, Smart_Money_Score, FII_conviction, divergences}
  GET /api/participant/history?limit=N     200 {rows: [...], count}

Sectors:
  GET /api/sectors                         200 {sectors: [29 items], count: 29}
  GET /api/sectors/{sector}                200 {sector detail + top 10 stocks}
  GET /api/sectors/history?limit=N         200 {rows, count}

Stocks:
  GET /api/stocks/watchlist?label=EMERGING&limit=50  200 {stocks, count}
  GET /api/stocks?page=1&per_page=100      200 {total: 2441, stocks, page, per_page}
  GET /api/stocks/{symbol}                 200 {bull_run_score, components, price, deal_signals, corporate_confidence}
  GET /api/stocks/{symbol}/momentum        200 {price_score, ret_30d/90d/365d, vol_ratio, sector_rel_30d}

Corporate:
  GET /api/corporate/deals?min_cr=50&limit=50  200 {deals, count}
  GET /api/corporate/catalysts             200 {catalysts: 12 events, count}
  GET /api/corporate/confidence?min_score=2.0  200 {confidence_scores, count}
  GET /api/corporate/events?limit=100      200 {events, count}

WebSocket:
  WS /ws/live                              Pushes {ts, market_hours, regime, top_sectors} every 30s

### Key Bug Fixed

event_calendar.csv uses "event_date" column (not "date"). Fixed in corporate.py:
  date_col = "event_date" if "event_date" in df.columns else "date"

NaN handling: all routers apply _clean() utility to replace float('nan') with None
before serialization (Python json.dumps rejects NaN per RFC 8259).

---

## Packages Installed

fastapi==0.138.2
uvicorn[standard] (watchfiles, httptools)

---

## Test Results (2026-06-30)

16/16 endpoints: ALL PASS
Top results:
  NEUTRAL regime | FII +10.91 | DII -4.52 | 29 sectors
  ADANIENSOL score 61.79 | PHARMA sector detail OK
  2441 symbols paginated | 12 upcoming catalysts

---

## Next Steps

Phase 11 -- React GUI:
  npm create vite@latest frontend -- --template react-ts
  cd frontend && npm install tailwindcss @tailwindcss/vite zustand @tanstack/react-query
  Start with GUI-1 (AppShell) then GUI-2 (Design System)
