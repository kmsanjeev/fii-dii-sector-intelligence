# MODULE DMB — DAILY MARKET BRIEF

Module-wise session log. Append-only per phased development protocol.

---

## Session 2026-07-11 — Phase DMB-1 (COMPLETE)

Mandate: 31-section institutional pre-market brief, auto-generated 08:45
IST, delivered before market open. Design doc: docs/modules/DAILY_MARKET_BRIEF.md
(gate-1) with HONEST availability matrix -- 24/31 sections wired; deferred
with reasons: macro calendar, IPO/GMP, analyst ratings, India 10Y, GIFT
premium, delivery% (not in bhavcopy cache schema). The brief NEVER invents.

### Engines (engines/briefing/)
- global_snapshot_engine: 29 yfinance tickers batched (5d daily bars ->
  last/prev/chg%); yfinance justified -- global data has no NSE source.
- market_breadth_engine: A/D from last TWO bhavcopies (schema: SYMBOL,
  SERIES, *_PRICE, TTL_TRD_QNTY -- NO delivery column); 52w counts from
  technical_indicators prox columns; index technicals via yfinance 1y.
- index_options_engine: FO UDiFF (FinInstrmTp IDO/IDF, TckrSymb, StrkPric,
  OptnTp, OpnIntrst, ChngInOpnIntrst, UndrlygPric); nearest expiry; PCR,
  max pain (writer-pain minimisation), OI walls, futures buildup read.
  BUG CAUGHT LIVE: without spot filtering, sparse far expiries put both
  walls on one strike (BANKNIFTY 59000-59000) -- resistance must be the
  biggest call wall ABOVE spot, support the biggest put wall BELOW.
- dmb_engine: assembler; deterministic bias (global chg clamp +-1.5,
  A/D >1.5/<0.7, PCR >1.1/<0.7, regime map); LLM synthesis DATA-LOCKED
  (facts list only, ===INTEL=== split, deterministic fallback);
  data/reports/DMB_YYYY-MM-DD.md archive.

### GOTCHAS
- participant_intelligence columns are FII_flow_score (lowercase f) --
  not FII_Flow_Score.
- news_signals score column is sentiment_7d, headline is latest_headline.
- DataFrame.get(col, default) returns a SCALAR if default is None-ish --
  guard with explicit column checks.

### Delivery
- telegram_bot.send_document (multipart); digest via send_raw.
- Scheduler job daily_market_brief 03:15 UTC Mon-Fri, misfire 1800s,
  worker thread. Registered alongside 18:00 pipeline (log-confirmed).

### Verified live
29/29 tickers, A/D 3.04, NIFTY PCR 0.80 / maxpain 24050 / 23600-24500,
FII/DII trends, LLM exec summary, Telegram digest + document received.
