# DAILY MARKET BRIEF (DMB)
## Pre-Market Institutional Briefing Note | Module Design
### Phase DMB-1 | 2026-07-11 | Gate-1 freeze

---

# 1. OBJECTIVE

An institutional-grade pre-market report, generated automatically every
trading day at **08:45 IST**, delivered to Telegram (executive digest +
full report as an attached document) and saved to `data/reports/`.
Reading it for 10-15 minutes before 09:15 should cover everything that
can influence the session.

# 2. SECTION AVAILABILITY MATRIX (HONEST)

The user's 31-section spec, mapped to real data sources:

| # | Section | DMB-1 status | Source |
|---|---------|--------------|--------|
| 1 | Executive Summary | YES | synthesized from all sections (LLM, data-locked) |
| 2 | Overnight Global Markets | YES | yfinance (Dow/Nasdaq/S&P/Europe/Nikkei/HSI/Shanghai/Kospi/ASX) |
| 3 | GIFT Nifty | BEST-EFFORT | GIFT ticker unreliable on free feeds; Nifty futures proxy via yfinance; marked when unavailable |
| 4 | Global Futures | YES | yfinance (YM=F, NQ=F, ES=F) |
| 5 | Commodities | YES | yfinance (Gold/Silver/Brent/WTI/NatGas/Copper) |
| 6 | Currency | YES | yfinance (USDINR, DXY, EURUSD, USDJPY) |
| 7 | Bonds | PARTIAL | US10Y yes (yfinance ^TNX); India 10Y no free feed -> marked N/A |
| 8 | Volatility | YES | ^INDIAVIX + ^VIX via yfinance |
| 9 | FII/DII Activity | YES | existing participant engines + institutional history (5/20d trends) |
| 10 | F&O Data | YES | FO bhavcopy (UDiFF): OI buildup classes per stock + index |
| 11 | Options Chain Snapshot | YES | FO bhavcopy: top Call/Put OI, PCR, max pain, S/R, expected range (NIFTY + BANKNIFTY) |
| 12 | SGX/GIFT Arbitrage | DEFERRED | depends on S3 reliability |
| 13 | Sector Heat Map | YES | sector_rotation_intelligence.csv |
| 14 | Sector Rotation | YES | same + FPI signals |
| 15 | Major News | YES | news_sentiment.csv / news_signals.csv (existing engine) |
| 16 | Macro Events Today | DEFERRED | no free structured economic calendar; LLM-generating events would hallucinate -- refused |
| 17 | IPO Watch / GMP | DEFERRED | no free GMP source; refused over fabrication |
| 18 | Corporate Actions Today | YES | corporate_actions + event_calendar.csv |
| 19 | Earnings Calendar | YES | event_calendar.csv (today/tomorrow/this week) |
| 20 | Stocks in News | YES | news_signals.csv sentiment split |
| 21 | Block Deals | YES | block_bulk_deals.csv + institutional_deal_signals.csv |
| 22 | Insider Activity | YES | insider_trades.csv / insider_signals.csv |
| 23 | Analyst Upgrades | DEFERRED | no free brokerage-consensus source |
| 24 | Technical Market Summary | YES | NIFTY/BANKNIFTY via yfinance daily history (RSI/MACD/DMA/S&R); stocks from technical_indicators.csv |
| 25 | Breadth | YES | latest equity bhavcopy: A/D, 52w H/L, delivery%, volume |
| 26 | Market Internals | YES | breadth + PCR + market_context.json |
| 27 | Institutional Scanner | YES | conviction_screener + bull_run + volume/delivery shocks from bhavcopy |
| 28 | Risk Dashboard | YES | data-driven risks (VIX level, currency move, crude move, regime, news negatives); no speculative geopolitics |
| 29 | Trading Plan | YES | rule-synthesized from bias + levels + regime |
| 30 | Actionable Watchlist | YES | conviction HIGH (buy), trade_conviction (swing), momentum/breakout from screeners, AVOID label |
| 31 | AI Market Intelligence | YES | scores computed from existing signals + one LLM synthesis pass (data-locked prompt) |

DEFERRED sections appear in the report with an explicit "not wired -- no
trustworthy free source" line rather than fabricated content. That honesty
rule is non-negotiable: the DMB never invents data.

# 3. ARCHITECTURE

```
08:45 IST (Mon-Fri, APScheduler -- separate job from the 18:00 pipeline)
  |
  1. engines/briefing/global_snapshot_engine.py
       yfinance batch -> global_snapshot.csv (indices, futures, commodities,
       FX, bonds, VIX; last/prev/chg%; fetch failures marked, never guessed)
  2. engines/briefing/market_breadth_engine.py
       latest equity bhavcopy -> breadth (A/D, 52w H/L, delivery%, volume)
       + NIFTY/BANKNIFTY daily technicals (yfinance history: RSI, MACD,
       DMA 20/50/200, S/R from swing highs-lows) -> market_breadth.csv
  3. engines/briefing/index_options_engine.py
       latest FO bhavcopy -> NIFTY/BANKNIFTY nearest expiry: PCR, max pain,
       top 3 Call/Put OI strikes, OI-change buildup, expected range
       -> index_options.csv
  4. engines/briefing/dmb_engine.py  (the assembler)
       reads the 3 fresh CSVs + 12 existing intelligence files
       -> renders data/reports/DMB_YYYY-MM-DD.md (full report)
       -> AI synthesis (Section 1 + 31) via llm_client with a DATA-LOCKED
          prompt (only provided numbers; explicit "do not invent")
       -> Telegram: executive digest message + full .md as document
```

Design rules:
- Every engine degrades gracefully: a failed source becomes an "N/A
  (source unavailable)" line in the report, never a crash, never a guess
- yfinance usage is justified under the acquisition-priority rule: global
  market data has no nselib/NSE source; for anything NSE the existing
  engines remain the source of truth
- The 18:00 pipeline is untouched; DMB is read-only over its outputs
- Report style: plain markdown, ASCII tables, sections in the user's
  specified institutional reading order

# 4. DELIVERY

- `data/reports/DMB_YYYY-MM-DD.md` (kept; the reports folder is the archive)
- Telegram message: executive summary + trading plan + watchlist heads
- Telegram document: the full report file
- GUI page: Phase DMB-2 (deferred; file + Telegram first)

# 5. RISKS

- yfinance pre-market coverage for some Asian tickers can lag ~15 min
- 08:45 run needs the machine awake; scheduler uses misfire grace 30 min
- LLM synthesis quality varies by provider; the data-locked prompt and a
  deterministic fallback (rule-based summary) cap the damage
