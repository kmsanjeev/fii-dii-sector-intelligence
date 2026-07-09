# CHANGELOG

## Project

Capital Flow Intelligence Platform

---

# Version 4.25.0

Phase CH-Fix -- KLineChart Pro Bug Fixes + Watchlist Polish + Stock Page Nav

Date: 2026-07-09

Status: Completed

Commits: 3c2ba0f, 383455e, 1bac08b

---

## Summary

Resolved all known defects in the KLineChart Pro integration discovered during QA.
Five root bugs fixed: volume bars invisible (wrong indicator placement), symbol search
results invisible (Pro library CSS variable typo with 3 dashes), watchlist autocomplete
not firing as-you-type (Pro binds "change" not "input" event), chart resize lag when
panels open/close, and watchlist missing LTP prices.

Second pass fixed multi-symbol add (space/comma/newline delimiters now parsed correctly),
added a custom SymbolSearchBar in the top bar with live-as-you-type search and full
arrow-key navigation, registered VOLMain (custom canvas draw indicator on price pane),
and wired watchlist keyboard navigation (ArrowUp/Down/Enter/Escape).

Added Stock Page button that navigates from /fullchart/:symbol back to /stocks/:symbol.

## Root Causes Documented

- KLineChart Pro v0.1.1 CSS bug: `.klinecharts-pro-list` uses `var(---klinecharts-pro-text-color)`
  (three dashes = undefined variable). Text color falls back to black on dark modal -- invisible.
  Fix: inject override CSS on mount targeting the correct 2-dash variable name.
- Pro v0.1.1 input bug: `c5` component binds `addEventListener("change", ...)` not `"input"`.
  DOM `change` event fires only on blur/Enter -- never on keystroke. Cannot patch without
  forking Pro. Fix: built `SymbolSearchBar` component in the top bar that does debounced
  API search on every keystroke, with keyboard nav independent of Pro.
- VOLMain: `IndicatorSeries.Volume` conflicts with price pane. Fix: use `IndicatorSeries.Price`
  + `figures: []` + custom `draw()` callback that paints bars at `bounding.bottom` via
  `xAxis.convertToPixel(barIndex)`. Returns `true` to skip all default rendering.

## New Files

- frontend/src/indicators/customIndicators.ts -- VOLMain moved here from FullChartPage;
  full indicator registry (VWAP, Supertrend, HMA, VOLMain) in one side-effect import

## Modified Files

- frontend/src/pages/FullChartPage.tsx:
  * CSS fix injection on mount (3-dash Pro typo)
  * SymbolSearchBar component: debounced 180ms API search, ArrowDown/Up/Enter/Escape nav,
    click-outside close with 180ms onBlur delay (onMouseDown fires before onBlur)
  * WatchlistPanel: multi-symbol tokenization via `/[\s,\n\r]+/` split;
    suppress autocomplete when input contains space/comma (multi-symbol mode);
    keyboard nav (ArrowDown/Up/Enter/Escape) in autocomplete dropdown
  * WatchlistPanel: LTP + abs change + change% fetched from daily bars, polled 60s
  * ResizeObserver on chart container: `_chartApi.resize()` on every dimension change
  * Stock Page button: `navigate('/stocks/:symbol')` button in top bar
  * VOLMain indicator in mainIndicators list (no _chartApi hack needed)

---

# Version 4.24.0

Phase CH-v2 -- KLineChart Pro Migration + Custom Indicators + TradingView Style

Date: 2026-07-09

Status: Completed

Commits: 298304b, 5825cba, bc9c79b, 3d9f54d, ce1ef01

---

## Summary

Replaced the lightweight-charts v1 chart implementation with KLineChart Pro v0.1.1
(klinecharts v9.8.12 core). Pro provides 30+ built-in indicators, drawing tools,
multi-pane layout, a built-in period selector, and a native toolbar -- eliminating
the need to hand-build all chart UI.

Implemented a full Datafeed adapter (searchSymbols, getHistoryKLineData, subscribe/
unsubscribe). Fixed the IST timezone registration issue (Asia/Kolkata absent from Pro's
hardcoded tz list -- registered manually with the correct UTC+5:30 offset).

Added a live settings panel for candle type, up/down colors, grid, font size, axis labels,
and crosshair style. Applied TradingView dark preset tokens and closed 6 remaining feature
gaps (snapshot button, period labels, drawing tools wiring, etc.).

Registered 3 custom indicators for the NSE context:
- VWAP: session-resetting, resets at UTC date boundary for each timeframe
- Supertrend (7, 3): Wilder ATR-based, teal bull / red bear lines with null gaps
- HMA (9): Hull Moving Average via double WMA; lag-reduced, smooth

## New Files

- frontend/src/lib/customIndicators.ts -- VWAP, Supertrend, HMA (later moved to
  frontend/src/indicators/customIndicators.ts in v4.25.0 refactor)

## Modified Files

- frontend/package.json: added klinecharts@9.8.12 + @klinecharts/pro@0.1.1
- frontend/src/pages/FullChartPage.tsx:
  * Full rewrite: KLineChartPro constructor with OurDatafeed, CHART_STYLES tokens
  * Period mapping: 5M/15M/1H/1D/1W/1M/3M -> Period objects
  * IST timezone fix: manual registration with UTC+5:30 before Pro init
  * Live settings panel: 8 configurable options, calls pro.setStyles() on change
  * TradingView dark preset applied via setStyles() call
  * Snapshot: canvas compositing (getBoundingClientRect) -> PNG download
  * WatchlistPanel: localStorage cfip-wl, multi-list, rename kept from v1
  * mainIndicators: ['EMA', 'VOLMain']; subIndicators: ['MACD', 'RSI']
  * dispose() + innerHTML reset on unmount and symbol change

---

# Version 4.23.0

Phase CH-v1 -- Full-Page TradingView-Style Chart (lightweight-charts)

Date: 2026-07-09

Status: Completed (superseded by v4.24.0 KLineChart Pro migration)

Commits: d031de1, 25be351

---

## Summary

Built the first full-page chart implementation at /fullchart/:symbol using
lightweight-charts. Rendered a candlestick + volume histogram with three toggleable
overlay indicators (EMA 20/50/200, Bollinger Bands 20/2) and a synced RSI(14) sub-pane.
All indicator math computed client-side (EMA, BB, Wilder RSI smoothing).

Added corporate action markers (D/B/S/R), a 7-timeframe selector, a live OHLCV + indicator
legend on crosshair hover, and an expand button on StocksPage that opens the chart from
the current timeframe.

Fixed RSI sync issues and toggle state bugs in a follow-up commit; added Snapshot (PNG)
and a Watchlist panel with localStorage persistence.

This implementation was superseded by the KLineChart Pro migration (v4.24.0) after
recognising that maintaining indicator rendering, drawing tools, and toolbar state
from scratch was not the right long-term approach for a professional chart.

## New Files

- frontend/src/pages/FullChartPage.tsx -- 537 lines, full-viewport route outside AppShell

## Modified Files

- frontend/src/App.tsx: /fullchart/:symbol route added, rendered outside AppShell (no nav bar)
- frontend/src/pages/StocksPage.tsx: [+] Full Chart button in chart toolbar

---

# Version 4.22.0

Phase TI -- Technical Indicators: RSI, MACD, ATR, Bollinger Bands, OBV, ADX

Date: 2026-07-08

Status: Completed

Commits: 27bfe9b, ccfbe6e

---

## Summary

Extended the technical engine with 6 additional indicators grouped into three layers:
Trend Structure (ADX), Momentum (RSI, MACD, BB), and Volatility & Volume (ATR, OBV).
Each indicator carries a label/signal field suitable for display without requiring
the frontend to interpret raw numbers.

Redesigned the Technical Indicators card in StocksPage into a 3-layer grid layout
matching the institutional trading framework: Trend -> Momentum -> Execution.

Also ran a full data pipeline refresh to bring bhavcopy and all derived intelligence
outputs up to 2026-07-08.

## New Indicator Fields (technical_indicators.csv)

- RSI (14, Wilder): rsi_14, rsi_signal (OVERBOUGHT/BULLISH/NEUTRAL/BEARISH/OVERSOLD)
- MACD (12,26,9): macd_line, macd_signal_line, macd_hist, macd_crossover (BULLISH_CROSS/BEARISH_CROSS/NEUTRAL)
- ATR (14, Wilder): atr_14, atr_pct (as % of price, for stop-loss sizing)
- Bollinger Bands (20,2): bb_upper, bb_lower, bb_mid, bb_pct_b, bb_bandwidth, bb_squeeze (bool)
- OBV: obv_slope_20d (ACCUMULATING/DISTRIBUTING)
- ADX (14): adx_14, adx_strength (STRONG/MODERATE/RANGING), plus_di_14, minus_di_14

## Modified Files

- engines/intelligence/technical_engine.py: added 6 indicator computation blocks; 2718 symbols
- backend/routers/stocks.py: expose all new indicator fields in /api/stocks/{symbol}
- frontend/src/api/client.ts: extend TechnicalIndicators type with 18 new fields
- frontend/src/pages/StocksPage.tsx: redesigned Technical card into 3-layer grid

---

# Version 4.21.0

Phase SH -- Stocks Page 8-Score Panel + 5-Quarter Shareholding Trends

Date: 2026-07-08

Status: Completed

Commits: 334d539, 72ed4c8, f34bf04, b9308b7

---

## Summary

Two parallel upgrades to the stock detail page:

First, the header score panel was expanded from 4 to 8 scores to match the printed
intelligence report: Bull Run, Price, ML Bull, ML Accum., Sector Flow, Deal, Valuation,
and Astro. The Astro score (range +/-100) is normalised to 0-100 for the ScoreGauge.
All typography violations (fontSize < 10) were fixed across the entire StocksPage --
over 15 elements updated to minimum 10px for legibility.

Second, shareholding history was extended to 5-quarter holding trend cards with QoQ
delta indicators. The XBRL fraction-scale bug was fixed: NSE changed the filing format
in newer quarters (Q2FY26+) to store percentages as 0-1 fractions instead of 0-100 values.
Auto-detection added (if field sum < 2.0 and >= 2 non-null fields, multiply by 100).
Historical data was corrected for 76,170 rows; holding_trends.csv rebuilt to 14,264 rows
covering 8 consecutive quarters per symbol (Q1FY25-Q4FY26).

## Modified Files

- frontend/src/pages/StockDetailPage.tsx:
  * 8-score header panel (Bull Run, Price, ML Bull, ML Accum., Sector Flow, Deal, Valuation, Astro)
  * Astro score normalisation from +/-100 -> 0-100 for ScoreGauge
  * ScoreChip: label fontSize 9->10, sub fontSize 8->10, fontWeight 600
  * 15+ fontSize violations fixed (FundTile, DMARow, TechSection, AnnItem, ConsensusCard,
    BullRun breakdown, PricePerformance, HoldingTrends, Management tiles, News/Insider/Concall)
  * C.dim replaced with C.muted for readable date/count text
- frontend/src/pages/StocksPage.tsx:
  * 8-score panel added (matching StockDetailPage)
  * All fontSize < 10 violations removed
- engines/fundamentals/shareholding_engine.py:
  * XBRL fraction scale auto-detection in _parse_one()
  * 76,170 rows historical data recalculated with correct scale

---

# Version 4.20.0

Phase UI-S -- Social Pulse Card Fix + Sectors Intelligence Upgrades

Date: 2026-07-08

Status: Completed

Commits: 5f5f2f1, bf4ff0d, d0800b8, 844ebf3

---

## Summary

Fixed the Social Pulse card on Dashboard -- frontend types were misaligned with the
X/Nitter backend (missing impact_score field, wrong is_direct -> is_x rename, new
category constants). Widened HandleCard to 260px, added X badge and category chip.

Exposed the Phase FPI sector FPI signals (built in v4.19.0) through two frontend-facing
upgrades on the Sectors page:
- Relative cross-sectional score: each sector's combined flow score shown as a
  percentile rank vs all other sectors, with a colour-coded regime badge (BULLISH/
  BEARISH/NEUTRAL) and FII regime indicator sourced from participant_intelligence.csv
- Dashboard heatmap: fixed dual-score rendering bug where both flow and momentum
  scores were showing the same value; added legible typography to heatmap cards
  (min 11px on all labels, contrast-safe colour tokens)

## Modified Files

- backend/routers/social_pulse.py: added impact_score, is_x, new category constants;
  frontend type contract aligned
- frontend/src/api/client.ts: add impact_score field; rename is_direct -> is_x;
  add INDIA_GOVT/INDIA_REGULATOR/G20_LEADER/MULTILATERAL/GEOPOLITICAL category types
- frontend/src/pages/Dashboard.tsx:
  * HandleCard: X badge, category chip, 260px width, cleaner avatar styling
  * New CAT_ACCENT + CAT_LABEL colour maps for the 5 new categories
  * Heatmap dual-score fix: sector_score and momentum_score now read from correct fields
  * Card typography: all text >= 11px, high-contrast muted tokens
- backend/routers/sectors.py: added fpi_signals join to sector rotation endpoint;
  relative cross-sectional score (percentile rank among all 29 sectors) in response
- frontend/src/pages/Sectors.tsx: FII regime badge (green BULLISH / red BEARISH /
  grey NEUTRAL) based on participant_intelligence regime field; relative score column
  added to sector table; colour coding on cross-sectional scores

---

# Version 4.19.0

Phase FPI -- NSDL/CDSL/SEBI Fortnightly FPI Sector Engine + 3-Factor Sector Rotation

Date: 2026-07-08

Status: Completed

Commit: 41a403a

---

## Summary

Added a 14-year FPI sector ownership time-series (Apr 2012 - Jun 2026) by scraping
NSDL/CDSL/SEBI fortnightly sector-wise FPI AUC reports. Upgraded the sector rotation
engine from a 2-factor proxy (F&O flow + price) to a 3-factor model using direct
FPI ownership data. Enables EARLY_ROTATION detection -- when FPI accumulates a sector
before F&O or price reflects it.

## New Files

- engines/fpi/sector_fpi_engine.py  -- HTML scraper for 3 sources:
  NSDL static files (2018-19, 2025-26), CDSL (2012-2023), SEBI (2012-2014);
  unified N-formula column parser; UTF-16LE decoding for older CDSL files;
  incremental with recovery queue; 8690 rows, 284 dates fetched

- engines/fpi/fpi_sector_signal_engine.py  -- Rolling Z-scores (26-fortnight window)
  on AUC and net investment; aggregates multiple raw-name variants per sector;
  outputs STRONG_ACCUMULATION / DISTRIBUTION signals with continuous score

- data/reference/sector_nsdl_mapping.csv  -- 90+ raw sector name variants mapped
  to platform taxonomy (NSDL, CDSL, SEBI name differences across 14 years)

## Modified Files

- engines/participant/sector_rotation_intelligence_engine.py:
  Added _load_fpi_signals() method; upgraded combined score to 3 factors:
  F&O flow 40% + FPI AUC 35% + price momentum 25%; EARLY_ROTATION signal now
  fires when FPI accumulates while F&O still bearish (e.g. INFRASTRUCTURE at
  FPI=+39.9, FII=-65.4 on 2026-07-03)

- engines/orchestration/daily_refresh.py:
  Added FPI_A_sector_fpi_fetch and FPI_B_sector_fpi_signals stages before 6C

- engines/common/config.py: added FPI_DIR = NSE_DIR / 'fpi'

## Data Coverage

- 8690 rows, 284 fortnightly dates from 2012-04-15 to 2026-06-30
- Source mix: CDSL 4852 rows (2012-Jun 2023), NSDL 3838 rows (2018-19, 2025-26)
- 58 dates in recovery queue (Jul 2023 - Apr 2025 gap: both CDSL and NSDL blocked)
- 136 unique raw sector names normalized to 17 platform sectors

## Sector Signals as of 2026-07-03

| Sector | AUC Z52 | Net Z52 | Signal |
|--------|---------|---------|--------|
| INFRASTRUCTURE | +0.42 | +2.00 | ACCUMULATION |
| FINANCIAL_SERVICES | +0.68 | +0.23 | NEUTRAL |
| FMCG | -2.01 | -1.33 | STRONG_DISTRIBUTION |
| IT | -2.11 | -0.86 | DISTRIBUTION |
| METAL | +1.74 | -2.06 | DISTRIBUTION |
| CEMENT | -0.48 | -2.25 | DISTRIBUTION |

---

# Version 4.18.0

Phase PULSE -- Intelligence Ticker (Social Pulse horizontal auto-scroll)

Date: 2026-07-07

Status: Completed

Commit: 71552a2

---

## Summary

Horizontally auto-scrolling Intelligence Ticker added to Dashboard above the
News Section. Shows 15 named "handles" (4 direct RSS + 11 synthetic topic clusters)
each with up to 5 latest items. No X/Twitter API required -- uses official government,
central bank RSS feeds plus keyword-filtered news pool for guaranteed coverage.

## Architecture: 2-tier hybrid

### Tier 1 -- Direct official feeds (confirmed live)
- @FedReserve: Federal Reserve press releases
- @ECB: European Central Bank speeches + press releases
- @BBCWorld: BBC World News RSS
- @BBCBusiness: BBC Business RSS

### Tier 2 -- Synthetic topic clusters (keyword-filtered from news pool)
15 unique handles covering: Geopolitical, India Policy (PMO/RBI/SEBI),
US Markets, Corporate India (Reliance/Tata/HDFC/Infosys/Adani),
Commodities & FX, Global Macro, Earnings Season, Market Movers,
India Deals & Defence, Energy & Climate, Tech & AI.
All 15 handles verified live (5 items each) in pre-commit test.

## New Files

### `backend/routers/social_pulse.py`
- GET /api/social-pulse -> { handles, active, total, cached_at }
- 20 RSS feeds fetched in parallel via asyncio.gather
- Pools all items, deduplicates by title, then filters per handle keywords
- Direct handle results from official feeds bypass keyword filter
- 30-min in-memory TTL cache

## Modified Files

### `backend/main.py` -- social_pulse.router at /api/social-pulse

### `frontend/src/api/client.ts`
- SocialPulseItem, SocialPulseHandle, SocialPulseResponse types
- fetchSocialPulse() function

### `frontend/src/pages/Dashboard.tsx`
- SocialPulse component with HandleCard sub-component
- CSS @keyframes pulse-scroll infinite horizontal animation
- Cards triplicated for seamless loop; speed proportional to handle count
- PAUSE/RESUME button; left/right fade-mask gradient edges
- HandleCard: category-colored left border + avatar circle + items list
  with sentiment dots (green/red/grey) and relative time
- Placed between F&O Participant Flows and News Section (Row 3B)

---

# Version 4.17.0

Phase NEWS -- Dashboard Global News Intelligence Feed

Date: 2026-07-07

Status: Completed

Commit: 1e4a1c6

---

## Summary

Real-time global market news section added to Dashboard, placed between
F&O Participant Flows and Sector Heatmap. Fetches from 9 RSS sources in parallel
(CNBC, Reuters, Yahoo Finance, ET Markets, Livemint, Moneycontrol, Business Standard)
with 30-minute server-side caching. No API keys required.

## New Files

### `backend/routers/news.py` -- async RSS aggregator
- 9 global feeds: CNBC Markets, Reuters Business, Reuters Markets, Yahoo Finance,
  ET Markets, ET Top, Business Standard, Moneycontrol, Livemint
- httpx.AsyncClient + asyncio.gather for concurrent parallel fetch (all feeds at once)
- xml.etree.ElementTree RSS parsing (zero extra dependencies)
- In-memory TTL cache: 1800s (30 min) with automatic refresh
- Sentiment engine: POSITIVE / NEGATIVE / NEUTRAL via keyword sets
- Region tagger: INDIA / GLOBAL per feed source
- Category tagger: EQUITIES / MACRO / FLOWS / EARNINGS / COMMODITIES / FOREX / IPO / CRYPTO / OTHER
- Dedup by URL, sorted by published_ts desc, 50-item cap
- GET /api/news endpoint

## Modified Files

### `backend/main.py`
- Added news.router import and include_router registration

### `frontend/src/api/client.ts`
- Added NewsItem type (title, url, source, published, published_ts, summary, sentiment, region, category)
- Added NewsResponse type + fetchNews() function

### `frontend/src/pages/Dashboard.tsx`
- Added NewsSection component with:
  * Category filter bar (ALL + 8 categories) with color-coded buttons
  * Region filter (ALL / INDIA / GLOBAL) tabs
  * Responsive auto-fill grid (minmax 260px cards)
  * NewsCard: source + region + category badges, 3-line headline,
    sentiment badge (green/red/grey), relative time, external link icon
  * "Show 12 / Show all N articles" toggle
  * Cache-age display + manual Refresh button
  * 5-minute auto-refetch via useQuery
- Placed NewsSection between Row 3 (F&O Flows) and Row 4 (Sector Heatmap)

---

# Version 4.16.0

Phase KU -- Vedic Kundli + W.D. Gann Intelligence Layer

Date: 2026-07-07

Status: Completed

Commit: fdd9b29

---

## Summary

Full Vedic natal chart (Kundli) system using Swiss Ephemeris (pyswisseph) with
Lahiri ayanamsha. Covers stocks (IPO date), humans, and country inception charts.
W.D. Gann Square of 9, planetary price lines, and solar time cycles integrated.
6-tab UI card in StocksPage. All data lazy-loaded via API on user request.

## New Files

### `engines/intelligence/kundli_engine.py` -- KU-1
- pyswisseph with Lahiri ayanamsha (Sidm_LAHIRI) + Whole Sign houses
- 9 Vedic grahas (Sun through Saturn) + Rahu/Ketu (True Node)
- Divisional charts D1/D2/D3/D4/D7/D9/D10/D11/D12/D16/D20/D30/D60
- Vimshottari Dasha to Pratyantardasha level (120-year cycle, all 27 nakshatras)
- Planetary dignities: exalted/moolatrikona/own_sign/friendly/neutral/enemy/debilitated
- Special aspects: Mars (4th/8th), Jupiter (5th/9th), Saturn (3rd/10th)
- Yoga detection: Gaja Kesari, Dhana, Raja, Viparita Raja, Neecha Bhanga, Kemdrum, Kala Sarpa, Parivartana
- Financial house analysis: 2H(wealth), 5H(speculation), 8H(volatility), 10H(management), 11H(revenue)
- Transit analysis: current planetary positions vs natal chart
- IPO Kundli: 9 exchange registries (NSE/BSE/NYSE/NASDAQ/LSE/TSE/SSE/HKEX/SGX/ASX)
- Country inception charts: India/USA/UK/China/Japan/Germany/Pakistan/Russia/France/Brazil
- Batch runner: per-symbol JSON cache + kundli_signals.csv summary

### `engines/intelligence/gann_engine.py` -- KU-2
- Square of 9: degree(N) = MOD((sqrt(N)*180 - 225), 360)
- Support/resistance: (sqrt(P) +/- angle/180)^2 at all 8 compass angles
- Gann Fan: 7 angle lines (4x1, 3x1, 2x1, 1x1, 1x2, 1x3, 1x4)
- Planetary Lines: geocentric sidereal lon -> price mapping (configurable price_factor)
- Solar time cycles: 90/180/270/360-day turning points from Aries ingress
- Price-time convergence zones: within 20% price of planetary level within 90 days
- Batch: gann_signals.csv with SO9 degree, R1/S1 for all stocks

### `engines/intelligence/kundli_interpretator.py` -- KU-3
- Rule-based bullish/bearish factor extraction from kundli dict
- 9 dasha financial interpretations per planet (Venus FMCG, Jupiter banking, etc.)
- Yoga financial scoring (+25 Dhana to -15 Kemdrum)
- Jupiter/Saturn transit triggers (return, opposition)
- Signal: STRONG_BUY / BUY / HOLD / CAUTION / EXIT / AVOID
- LLM narrative via llm_client.py (on-demand, not batched)

### `backend/routers/kundli.py` -- KU-4
- GET /api/stocks/{symbol}/kundli -- natal chart with JSON cache fallback
- POST /api/kundli/human -- human natal chart
- GET /api/kundli/country/{name} -- country inception chart
- GET /api/kundli/gann/{symbol} -- Gann analysis at current price
- GET /api/kundli/gann/market/planetary-lines -- all planetary price lines
- GET /api/kundli/bulk/status -- bulk run status
- POST /api/kundli/bulk/run -- trigger background bulk computation

### `frontend/src/components/platform/KundliCard.tsx` -- KU-5
- 6 tabs: Overview | Planets | Houses | Dasha | Gann | Report
- Lazy-loaded: API call only fires on user expand (no cold-load penalty)
- Planets table: sign, house, nakshatra, pada, dignity, retrograde
- Financial houses: strength badge, lord dignity, occupants
- Dasha tab: current period + outlook + full mahadasha timeline table
- Gann tab: SO9 degree, R/S levels, solar cycles, planetary price lines table
- Report tab: signal badge, score, bullish/bearish factors, narrative

## Modified Files

- `backend/main.py`: registered kundli router
- `engines/orchestration/daily_refresh.py`: KU_kundli_engine + KU_gann_engine stages added
- `frontend/src/pages/StocksPage.tsx`: KundliCard added after ASTRO SIGNAL section

## Outputs

- `data/intelligence/kundli/` -- per-symbol JSON natal charts (created on first bulk run)
- `data/intelligence/kundli_signals.csv` -- summary: lagna, mahadasha, yogas, signal per stock
- `data/intelligence/gann_signals.csv` -- SO9 degree, R1/S1 per stock at current price

## Technical Notes

- pyswisseph is the Swiss Ephemeris Python binding; swe.SIDM_LAHIRI for Lahiri ayanamsha
- Whole Sign houses: Ascendant sign = 1st house, each sign = next house
- Navamsa (D9): movable=same, fixed=9th from, dual=5th from; each segment = 3deg20min
- Vimshottari: 120-year cycle; nakshatra->lord->balance determines starting dasha
- Gann: verified formula; test at 2800 gives R1=2853, S1=2747 (degree=299.7, Southeast)
- RELIANCE (listing 2000-11-18): Sagittarius Lagna, Venus Mahadasha until 2032, Parivartana yoga

---

# Version 4.15.0

Phase AF -- AstroFinance Intelligence Layer

Date: 2026-07-05

Status: Completed

Commits: 8159d1c, da83713

---

## Summary

Three-sub-phase AstroFinance integration adds planetary intelligence to the
decision platform. Indian/Vedic planet-sector mapping (Banerjee 2009) combined
with Western aspect theory (Pesavento 2015) and 6 financial astrology PDFs
ingested into the RAG knowledge base.

## New Files

### `engines/ai/knowledge/book_ingestion_engine.py` -- AF-1
- Extracts all 6 AstroFinance PDFs using pdfplumber (ASCII encoding fallback)
- Chunks at sentence boundaries (~600 chars, 80-char overlap)
- Tags domain="ASTRO"; appends to documents.jsonl (idempotent via doc_id check)
- Result: 3,173 ASTRO documents ingested, faiss_ASTRO.index 4.8MB

### `engines/intelligence/astro_engine.py` -- AF-2
- Daily planetary computation using ephem library
- Planets: Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn/Uranus/Neptune + Rahu/Ketu
- Rahu: mean node formula (Omega = 125.0445 - 1934.136 * T)
- Sign strength: exaltation +4, own sign +3, neutral 0, debilitation -3
- Aspect types: conjunction/sextile/square/trine/opposition with financial polarity
- Moon phase illumination + waxing/waning signal
- Eclipse proximity detection (Rahu = uptrend, Ketu = downtrend)
- Bradley Siderograph-style market score
- Planet-sector mapping: 31 NSE sectors per Vedic Indian system
- Outputs: astro_signals.csv (31 rows), market_astro_context.json

### `frontend/src/components/platform/AstroSignalCard.tsx` -- AF-3
- Action badge with color coding (BUY/HOLD/CAUTION/EXIT/AVOID)
- Astro score bar (-100 to +100)
- Planet state chips with sign strength colors
- Retrograde warning banners (orange highlight)
- Moon phase, eclipse warnings, market pulse, source book disclaimer

## Modified Files

- `engines/ai/knowledge/faiss_indexer.py`: added ASTRO to DOMAINS list
- `backend/services/data_loader.py`: registers astro_signals.csv + get_astro_context()
- `backend/routers/stocks.py`: adds astro{} block to stock detail endpoint
- `frontend/src/pages/StocksPage.tsx`: renders ASTRO SIGNAL section (before CORPORATE)
- `frontend/src/api/client.ts`: added astro? type to Stock
- `engines/ai/chatbot/tools/data_tools.py`: get_astro_signal() function
- `engines/ai/chatbot/tools/tool_registry.py`: get_astro_signal tool schema
- `engines/ai/chatbot/intent_router.py`: ASTRO intent keywords + system prompt
- `engines/orchestration/daily_refresh.py`: AF_astro_engine stage after C1_trade_conviction

## Current Astro Signals (2026-07-05)

- BUY: BANKING, DIVERSIFIED (Jupiter in Leo, benefic aspects, score +31.9)
- HOLD: SHIPPING, AMC, FMCG, HOSPITALITY, TEXTILE
- CAUTION: IT, TELECOM, MEDIA, AVIATION, LOGISTICS (Mercury RETROGRADE)
- EXIT: AUTO, CAPITAL_GOODS, METAL, DEFENSE (Mars negative aspects, -40 to -59)
- AVOID: PHARMA, HEALTHCARE, REALTY, CEMENT, INFRA (Saturn DEBILITATED in Aries)
- Market overall: BEARISH (-49.0 Bradley score)

---

# Version 4.14.0

Phase 12C -- Forward Return Labels (True Supervised ML Training)

Date: 2026-07-03

Status: Completed

---

## Summary

Phase 12C breaks the circular dependency where Phase 12 models were trained on
Phase 8B rule-based labels (they were just learning to replicate rules, not
predict future price performance). A new label generator computes REALIZED
forward returns from bhavcopy history, and a new model trained on those returns
provides a true supervised signal. Feature matrix grows from 76 to 77 columns.

## Problem Solved

Old training target: label_enc derived from Phase 8B bull_run_probability.csv
  -> Model learns to replicate rule-based scoring, circular dependency
New training target: is_up_15_45d = stock actually rises 15%+ in 45 sessions
  -> Model trained on realized outcomes from 2024-2026 bhavcopy history

## New Files

### `engines/ml/label_generator.py` -- NEW
- Loads 790 sessions of adjusted_equity parquets (~3 years)
- Builds close/high/low/vol pivot matrices
- For each symbol: computes TA-Lib indicators over full series (RSI, MACD, %B, ADX, DMA200, vol ratio)
- 53 reference dates (every 10 sessions, 2024-03-12 to 2026-03-24)
- At each ref date: extracts feature values + computes 20D/45D/60D forward returns
- Binary labels: is_up_10_20d, is_up_15_45d, is_up_20_60d
- Output: data/intelligence/ml_forward_labels.csv
  103,071 rows | 2590 symbols | positive rate 14.4% (is_up_15_45d)

### `engines/ml/forward_return_model.py` -- NEW
- Loads ml_forward_labels.csv; target = is_up_15_45d (primary label)
- XGBoost with scale_pos_weight=6.94 (handles 6:1 class imbalance)
- TimeSeriesSplit(n_splits=5) cross-validation (no future leakage)
- CV AUC: 0.628 +/- 0.015 (meaningful signal; random = 0.50)
- Current scoring: joins today's features from technical_pattern_features.csv +
  technical_indicators.csv + price_momentum.csv (same 6 feature columns)
- Model: data/intelligence/ml_features/models/forward_return_xgb.json
- Output: data/intelligence/ml_forward_return_scores.csv (2723 symbols)
- Top scored: KAYNES 81.3, VEDL 80.2, ZAGGLE 79.6, DPABHUSHAN 78.3

### `engines/ml/feature_engineering.py` -- MODIFIED
- Added FWD_RETURN_SCORES path constant
- Added _add_forward_return_score() method
- Added "forward_return_score" to feature_cols
- Added method call in _build_matrix() after Phase 12B block

## Outputs Updated
- data/intelligence/ml_forward_labels.csv -- 103,071 rows (new)
- data/intelligence/ml_forward_return_scores.csv -- 2723 symbols (new)
- data/intelligence/ml_features/feature_matrix.parquet -- 2406 x 77 cols
- All ML ensemble models retrained (accumulation, bull_run, combined scorer)

## Execution Order (Phase 12C)
1. py -3.11 -m engines.ml.label_generator
2. py -3.11 -m engines.ml.forward_return_model
3. py -3.11 engines/ml/feature_engineering.py
4. py -3.11 engines/ml/accumulation_model.py
5. py -3.11 engines/ml/bull_run_model.py
6. py -3.11 -m engines.ml.ml_scorer

## Notes
- forward_return_score (0-100) is an orthogonal signal to rule-based label_enc
- Both signals now coexist in the feature matrix; ensemble models use both
- The 14.4% positive rate reflects real market difficulty: only ~1 in 7 stocks
  achieves 15%+ gain in 2 months at a random entry point
- AUC 0.628 is competitive with published academic results for return prediction

---

# Version 4.13.0

Phase 12B -- Technical Strategy Pattern Features (RSI, MACD, Bollinger, ADX)

Date: 2026-07-03

Status: Completed

---

## Summary

Phase 12B adds 8 technical oscillator and trend-strength features to the ML feature
matrix, computed via TA-Lib from 300 sessions of adjusted bhavcopy parquets.
Feature matrix grows from 68 to 76 columns. All 3 ML models retrained.

## New Features Added (8)

### RSI (14-period Wilder)
- `rsi_14` -- continuous RSI value; 98.6% coverage; clipped 0-100
- `rsi_zone_enc` -- OVERSOLD(<=30)=2, NEUTRAL=1, OVERBOUGHT(>=70)=0
  dist: 2147 NEUTRAL, 182 OVERBOUGHT, 44 OVERSOLD (market currently elevated)

### MACD (12, 26, 9)
- `macd_hist` -- MACD histogram = MACD line - signal line; continuous; clipped -50..50
- `macd_signal_enc` -- BULLISH=2 (hist>0 and rising), BEARISH=0 (hist<0 and falling), NEUTRAL=1
  dist: 1216 NEUTRAL, 709 BEARISH, 448 BULLISH

### Bollinger Bands (20, 2-sigma)
- `bb_pct_b` -- %B = (close - lower) / (upper - lower); 0=at lower, 1=at upper; clipped -0.5..1.5
- `bb_squeeze` -- band width as % of middle band; lower = tighter squeeze / potential breakout

### ADX (14-period)
- `adx_14` -- trend strength 0-100; >25 = trending
- `adx_trending` -- binary flag: 1 if ADX > 25
  dist: 932 trending (39%), 1441 not trending (61%)

## New Files

### `engines/ml/technical_feature_engine.py` -- NEW
- Reads last 300 adjusted_equity parquets (same source as technical_engine.py)
- Builds close/high/low pivot matrices; computes TA-Lib indicators per symbol
- RSI/MACD/Bollinger use close prices; ADX uses close+high+low
- Minimum 50 sessions required per symbol; 2664 computed, 72 skipped
- Output: data/intelligence/technical_pattern_features.csv (2664 rows, 100% populated)
- Guardrail: atomic write (.tmp -> shutil.move), skip-with-warning on missing source

### `engines/ml/feature_engineering.py` -- MODIFIED
- Added TECH_PATTERNS path constant
- Added _add_technical_patterns() method (reads CSV, clips ranges, left-merge)
- Added 8 new feature names to feature_cols
- Added method call in _build_matrix() after Phase 12A block

## Outputs Updated
- data/intelligence/technical_pattern_features.csv -- 2664 symbols, as_of 2026-06-30
- data/intelligence/ml_features/feature_matrix.parquet -- 2406 x 76 cols
- data/intelligence/ml_accumulation_scores.csv -- retrained
- data/intelligence/ml_bull_run_scores.csv -- retrained
- data/intelligence/ml_scores_combined.csv -- rescored 2406 symbols

## Execution Order (Phase 12B)
1. py -3.11 -m engines.ml.technical_feature_engine
2. py -3.11 engines/ml/feature_engineering.py
3. py -3.11 engines/ml/accumulation_model.py
4. py -3.11 engines/ml/bull_run_model.py
5. py -3.11 -m engines.ml.ml_scorer

---

# Version 4.12.0

Phase 12A -- ML Feature Enrichment (Fundamentals + Technical + F&O)

Date: 2026-07-03

Status: Completed

---

## Summary

Phase 12A enriches the ML feature matrix from 57 to 68 features by integrating
fundamentals, technicals, and F&O intelligence into the XGBoost/LightGBM models.
All 3 ML engines (feature_engineering, accumulation_model, bull_run_model) retrained
and scored on the full 2406-symbol universe.

## New Features Added (11)

### Extended Financials (from Phase 15B extended_financials.csv)
- `opm_pct` -- Operating Profit Margin %; 70.9% coverage; clipped -50..80
- `roce_pct` -- Return on Capital Employed %; 68.7% coverage; clipped -20..60
- `sales_growth_3y` -- 3Y Sales CAGR %; 67.3% coverage; clipped -20..100

### Valuation Features (from Phase 15 valuation_scores.csv)
- `pe_ratio_log` -- log1p(PE ratio) clipped 0..5.5; handles negative PE as NaN; 61.3%
- `roe_pct` -- Return on Equity %; 70.5% coverage
- `valuation_label_enc` -- CHEAP_QUALITY=3, FAIRLY_VALUED=2, EXPENSIVE=1, LOSS=0; 71.0%
- `yoy_revenue_pct` -- YoY revenue growth; effectively null in current source (data gap)
- `yoy_profit_pct` -- YoY profit growth; effectively null in current source (data gap)

### Technical Features (from Phase A technical_indicators.csv)
- `vs_dma_200` -- % vs 200-DMA; 79.8% coverage; clipped -60..100
- `trend_signal_enc` -- UPTREND=2, NEUTRAL=1, DOWNTREND=0; 99.7% coverage

### F&O Features (from Phase A fno_intelligence.csv)
- `fno_oi_signal_enc` -- BULLISH=2, NEUTRAL=1, BEARISH=0; 8.8% (211 F&O stocks only)

## Changes

### `engines/ml/feature_engineering.py` -- MODIFIED
- Added 4 path constants: EXT_FIN, VAL_SCORES, TECH_IND, FNO_INTEL
- Added 3 encoding maps: VALUATION_MAP, TREND_MAP, FNO_OI_MAP
- Added 4 _add_*() method bodies: _add_extended_financials, _add_valuation_features,
  _add_technical_features, _add_fno_features
- All methods follow established pattern: exists-check, usecols read, upper-norm,
  clip/encode, left-merge on symbol, skip-with-warning if source missing
- 4 method calls wired into _build_matrix(); 11 feature names added to feature_cols
- Feature matrix now: 2406 rows x 68 cols (was 57)

## Outputs Updated
- data/intelligence/ml_features/feature_matrix.parquet -- 2406 x 68
- data/intelligence/ml_accumulation_scores.csv -- 2406 rows
- data/intelligence/ml_bull_run_scores.csv -- 2406 rows
- data/intelligence/ml_scores_combined.csv -- 2406 rows

## Known Data Gaps
- yoy_revenue_pct / yoy_profit_pct: only 5/2084 non-null in source valuation_scores.csv
  (Phase 15 pipeline does not compute these metrics for most symbols yet)
  Trees ignore fully-null features without error; will auto-activate when source fills.

## Phase Roadmap
- Phase 12B: Technical strategy pattern features (RSI, MACD, Bollinger, ADX)
- Phase 12C: Forward return labels (supervised learning, break circular dependency)

---

# Version 4.11.0

Phase 15B — Extended Financials Engine (OPM / ROCE / Book Value / Sales Growth)

Date: 2026-07-03

Status: Completed

---

## Summary

Built Phase 15B Extended Financials Engine to compute the 4 balance-sheet-derived metrics
that were previously showing "---" in the StocksPage fundamentals grid:
- OPM% (Operating Profit Margin = EBITDA / Revenue)
- ROCE% (Return on Capital Employed = annualised EBIT / Capital Employed)
- Book Value per share (Total Equity / Shares Outstanding)
- Sales Growth CAGR over best-available history (1-3 years depending on data)

Extends the existing NSE XBRL infrastructure (Phase 15A) to also parse balance sheet tags.

## Changes

### Engine: `engines/fundamentals/extended_financials_engine.py` — NEW
- Fetches balance sheet XBRL fields from the same NSE filing URLs as Phase 15A
- New XBRL tags extracted: ProfitBeforeTax, FinanceCosts, DepreciationDepletionAndAmortisationExpense,
  TotalAssets, TotalCurrentLiabilities, EquityShareCapital, OtherEquity
- Per-symbol aggregation: OPM from EBITDA(=PBT+FC+Dep)/Revenue, ROCE from EBIT*4/CapEmp,
  Book Value from TotalEquity / EPS-derived shares, Sales Growth CAGR from quarterly revenue history
- Outputs: data/NSE/results/extended_financials.csv + extended_quarterly_raw.csv (raw cache)
- Run modes: default (6 windows), --backfill (+ 5 historical for 3Y growth), --agg-only
- Full guardrail compliance: atomic writes, rate limiting, retry+backoff, recovery queue

### Backend: `backend/services/data_loader.py`
- Added extended_financials source (data/NSE/results/extended_financials.csv)

### Backend: `backend/routers/stocks.py`
- Phase 15B merge into fundamentals dict: book_value_per_share, opm_pct, roce_pct,
  sales_growth_3y_pct, sales_growth_years, capital_employed_cr, total_equity_cr

### Backend: `backend/routers/data_ops.py`
- Registered extended_financials_15b and extended_financials_15b_backfill engine entries

### Frontend: `frontend/src/pages/StocksPage.tsx`
- Book Value tile: shows book_value_per_share with total_equity_cr sub-label
- OPM tile: shows opm_pct with EBITDA value (>=20% green, >=10% teal, <0% red)
- ROCE tile: shows roce_pct with capital_employed_cr sub-label (>=20% green)
- Sales Growth tile: dynamic label (1Y/2Y/3Y based on actual data available)
- Fixed deal_signals type cast from Record<string,unknown> to Record<string,string|number|null>

## Commits
- c5cc994: feat(phase-15b): Extended Financials Engine -- OPM, ROCE, Book Value, Sales Growth 3Y
- 7e02c0c: fix(phase-15b): correct share-sort fallback and NaT comparison

---

# Version 4.10.0

Multi-Provider LLM Client + Phase F/G/H Engine Runs

Date: 2026-07-03

Status: Completed

---

## Summary

Migrated all Phase F/H LLM engines from Anthropic API (exhausted credits) to a shared
multi-provider fallback client. Fixed NSE PIT API field mapping for insider trades.
Executed all Phase F, G, and H engines with real data — all outputs now populated.

## Changes

### Shared LLM Client (`engines/common/llm_client.py`) — NEW
- OpenAI-compatible fallback chain: Groq -> Cerebras -> Gemini -> OpenRouter -> Together
- Per-provider 5-minute cooldown on 429/credit errors
- timeout=15.0s to prevent Groq slow-response hangs
- Confirmed working: Groq (llama-3.1-8b-instant), Cerebras (gemma-4-31b)

### Phase F Engine Bug Fixes
- `engines/intelligence/insider_trade_engine.py`: NSE PIT API always returns buyValue=0
  Fix: use secVal for trade value + tdpTransactionType for direction; SIGNAL_DAYS 30->90
  Result: 3 signals — HCLTECH +34.3 Cr STRONG_BUY, DMART +1.05 Cr BUY
- `engines/intelligence/news_sentiment_engine.py`: migrated to llm_client; stale cache cleared
  Result: 54 news signals across 54 symbols
- `engines/intelligence/concall_signal_engine.py`: migrated to llm_client
  Result: 400 symbols scored, concall_summary.csv (400 rows)
- `engines/intelligence/agm_intelligence_engine.py`: migrated to llm_client
  Result: 400 rows, 13 HIGH governance risk, 25 dividend signals, 137 mgmt changes

### Phase G Runs
- `engines/intelligence/purity_engine.py`: 225 tags boosted (all index-based), avg purity 0.6082
- `engines/intelligence/consensus_engine.py`: 540 symbols, 45 BUY, 8 SELL

### Phase H Runs
- `engines/intelligence/theme_momentum_engine.py`: first snapshot saved (2026-07-03.csv)
  Momentum delta will compute from second run onwards

### Backend
- `backend/routers/stocks.py`: AGM signal block added to /api/stocks/{symbol}
  Returns governance_risk, dividend_signal, management_change, capex_confirm, key_decision

### ML Updated
- `engines/ml/feature_engineering.py`: feature_matrix.parquet now 2406 x 57 features
  (includes concall_guidance_score, concall_sentiment_score, consensus_score, etc.)
- `engines/ml/ml_scorer.py`: ml_scores_combined.csv updated (2406 symbols)

## Commits

`d5821f4` `bd83553`

---

# Version 4.9.0

Theme Intelligence Phases E-H Complete

Date: 2026-07-03

Status: Completed

---

## Summary

Extended the theme intelligence layer with 4 new phases covering alt-data signals,
purity refinement, multi-signal consensus, Google Trends, AGM governance intelligence,
and daily theme momentum tracking.

## Changes

### Phase E (50-Theme Taxonomy)
- `engines/intelligence/theme_intelligence_engine.py`: extended to 50 themes across 10 categories
- `data/reference/theme_tagging.csv`: 3000+ symbol-theme-purity tags with multi-theme support
- Commit: 0b96a43

### Phase F (Alt-Data Engines)
- `engines/intelligence/news_sentiment_engine.py`: RSS (Mint + MoneyControl) -> Claude Haiku -> news_signals.csv
- `engines/intelligence/insider_trade_engine.py`: NSE PIT API, 211 F&O symbols, 30D insider_signals.csv
- `engines/intelligence/concall_signal_engine.py`: XBRL analyst meets -> Claude Haiku -> concall_summary.csv
- `engines/ml/feature_engineering.py`: 7 new ML features (theme_score_max, news_sentiment_7d, insider_score, etc.)
- `backend/routers/stocks.py`: /api/stocks/{symbol} now returns news/insider/concall blocks
- `frontend/src/pages/StockDetailPage.tsx`: NewsCard, InsiderCard, ConcallCard, ConsensusCard components

### Phase G (Purity Refinement + Consensus)
- `engines/intelligence/purity_engine.py`: 4-signal purity boosters (NSE index, concall, news, insider)
- `engines/intelligence/consensus_engine.py`: 4-factor weighted consensus score (concall 35%, insider 25%, news 20%, deals 20%)
- `backend/routers/stocks.py`: consensus block added to stock detail endpoint
- `frontend/src/pages/StockDetailPage.tsx`: ConsensusCard with 4 sub-signal mini-bars

### Phase H (Google Trends + AGM + Theme Momentum)
- `engines/intelligence/trend_intelligence_engine.py`: 50-theme pytrends keyword map, weekly cache, RISING/FALLING/STABLE
- `engines/intelligence/agm_intelligence_engine.py`: Claude Haiku extracts governance_risk/dividend/capex/mgmt signals
- `engines/intelligence/theme_momentum_engine.py`: daily snapshots, delta + phase_transition detection, P11 Telegram alert
- `alerts/alert_engine.py`: P11_THEME_ROTATION type + _check_theme_rotation()
- `backend/services/data_loader.py`: 3 new sources (trend_scores, agm_signals, theme_momentum)
- `backend/routers/themes.py`: _build_trend_map() + _build_momentum_map() enriching theme API responses
- `frontend/src/pages/ThemesPage.tsx`: trend direction badge (TREND UP/DN), phase transition badge, MomDelta column
- Commit: 41cbb50

---

# Version 4.6.0

Chat Engine Robustness + Project Migration to D:\Projects

Date: 2026-07-02

Status: Completed

---

## Summary

Fixed two Groq chat reliability issues and migrated the entire project from
`C:\Users\hp\fii-dii-sector-intelligence` to `D:\Projects\fii-dii-sector-intelligence`
without breaking Git history or any functionality.

## Changes

- `engines/ai/chatbot/chat_engine.py`:
  - `parallel_tool_calls=False` added — prevents Llama 3.3 70B from generating
    malformed XML-style function calls (`<function=name{args}/>`) instead of JSON
  - Tool loop restructured: `break` on `tool_use_failed` → final text-only call
  - Final forced call uses clean synthesised prompt (tool results only, not full history)
    to prevent model confusion when MAX_TOOL_ROUNDS is exhausted
  - Rate limit (429) now surfaced as a readable message in both tool loop and final call
  - `MAX_TOOL_ROUNDS` reduced 5 → 3 (each round costs 2-5k tokens on Groq free tier)
- Project root: `D:\Projects\fii-dii-sector-intelligence` (migrated via robocopy)
  - 52,323 files, ~21 GB, 0 failures
  - Git remote URL (HTTPS) and history unchanged — GitHub connection intact

## Commits

`af498cd` `6dbacd3`

---

# Version 4.5.0

Groq Migration — Anthropic API replaced with Groq llama-3.3-70b-versatile (free tier)

Date: 2026-07-02

Status: Completed

---

## Summary

Replaced the Phase 14 chatbot backend (Anthropic claude-sonnet-4-6) with Groq's free-tier
`llama-3.3-70b-versatile` model to eliminate API costs during development. Anthropic API
key is retained in .env for Phase 16 management sentiment only.

## Changes

- `engines/ai/chatbot/chat_engine.py` — full rewrite for Groq:
  - Model: `llama-3.3-70b-versatile` via `groq` Python package
  - `_to_groq_tools()`: converts Anthropic `input_schema` format to OpenAI/Groq
    `{"type":"function","function":{...,"parameters":...}}` format at module load
  - Agentic loop uses `msg.tool_calls` (OpenAI format) instead of Anthropic `stop_reason`
  - History uses OpenAI message format: `role:"tool"` + `tool_call_id` for tool results
  - System prompt injected as first message in `messages` list (not separate API arg)
- `engines/ai/chatbot/tools/tool_registry.py` — tool schemas retained as Anthropic format
  (converted at load time via `_to_groq_tools()`)
- `backend/routers/chat.py` — env var check changed from `ANTHROPIC_API_KEY` to `GROQ_API_KEY`
- `.env` — `GROQ_API_KEY` added; `ANTHROPIC_API_KEY` retained for Phase 16

## Packages

`groq` Python package installed

---

# Version 4.4.0

Phase D — Chat Page full implementation

Date: 2026-07-02

Status: Completed

---

## Summary

Replaced the 17-line ChatPage.tsx placeholder (Phase 11) with a full 355-line production
chat UI backed by the Phase 14 Groq chatbot endpoint.

## Changes

- `frontend/src/pages/ChatPage.tsx` — complete rewrite:
  - Multi-turn session via `session_id` (persists across sends on same page load)
  - Intent badge (MARKET / SECTOR / STOCK / CORPORATE / RESEARCH) on each assistant reply
  - `TypingDots` animation while waiting for API response
  - 6 suggested prompt chips visible on first turn (auto-hide after first message)
  - Auto-resize textarea (1–4 lines), Shift+Enter for newline, Enter to send
  - `New Chat` button resets session and clears history
  - API error banner when GROQ_API_KEY is not configured
  - WELCOME message pre-populated; capability domain chips shown on first turn
- `frontend/src/api/client.ts` — added:
  - `ChatResponseData` type: `{ reply, session_id, intent }`
  - `sendChat(message, session_id?)` helper
  - `resetChatSession(session_id)` helper

---

# Version 4.3.0

Phase C — Trade Conviction Alerts (P9/P10)

Date: 2026-07-02

Status: Completed

---

## Summary

Built the server-side trade conviction engine and two new alert types (P9 TRADE_CONVICTION,
P10 OI_SIGNAL_FLIP) that fire daily based on the same 7-factor score used by Phase B's
TradeIntelligenceCard frontend component.

## Changes

- `engines/intelligence/trade_conviction_engine.py` (new):
  - 7-factor conviction score for 2,406 symbols: trend/DMA (25%), F&O OI (20%),
    sector rotation (15%), shareholding QoQ (15%), valuation (10%), ML score (10%),
    management sentiment (5%)
  - Output: `data/intelligence/trade_conviction_scores.csv` (2406 rows)
  - Action labels: STRONG_BUY / BUY / HOLD / REDUCE / EXIT
- `alerts/alert_engine.py` — added P9 TRADE_CONVICTION + P10 OI_SIGNAL_FLIP alert types
  - P9: fires when conviction_score >= 75 and action in (STRONG_BUY, BUY); capped 3/day
  - P10: fires on OI signal flip (LONG_BUILDUP ↔ SHORT_BUILDUP); capped 5/day
- Alert types total: 10 (was 7)

## Commits

`6b40076`

---

# Version 4.2.0

Phase B — Trade Intelligence Card with entry/exit synthesis

Date: 2026-07-02

Status: Completed

---

## Summary

Built the WHY BUY / EXIT WATCH synthesis panel on StockDetailPage and enriched all
stock listing endpoints with technical/F&O/ML bulk fields.

## Changes

- `frontend/src/components/platform/TradeIntelligenceCard.tsx` (new):
  - `computeTradeSignal(data)`: 7-factor conviction score (0–100) from existing stock data
  - Factors: trend/DMA (25%), OI signal (20%), sector rotation (15%), shareholding QoQ (15%),
    valuation (10%), ML bull run score (10%), management sentiment (5%)
  - Entry zone: LTP ±2%; stop loss: max(dma_200×0.98, close×0.90); trail: ×1.05
  - `ScoreBar`: 0–100 gradient bar with STRONG BUY / BUY / HOLD / REDUCE / EXIT labels
  - Action colors: STRONG BUY=#22C55E, BUY=#10B981, HOLD=#F59E0B, REDUCE=#F97316, EXIT=#EF4444
- `backend/routers/stocks.py`:
  - `_enrich_bulk(df)`: merges `trend_signal`, `vs_dma_200`, `prox_52w_high` from technical;
    `oi_signal` from fno_intel; `ml_bull_run_score`, `accumulation_score` from ml_scores
  - `get_stock_detail()`: added `sector_rotation_signal` via join with sector_rotation_intelligence.csv
  - Both `get_watchlist()` and `get_all_stocks()` call `_enrich_bulk()`
- `frontend/src/api/client.ts`:
  - Added `sector_rotation_signal?`, `trend_signal?`, `oi_signal?`, `ml_bull_run_score?`,
    `accumulation_score?`, `holding_trends?`, `management?` fields to `Stock` type
- `frontend/src/pages/WatchlistPage.tsx`:
  - Added `ActionBadge` component (STR BUY/BUY/HOLD/REDUCE/EXIT from label+trend+oi)
  - New ACTION column in stock table
- `frontend/src/pages/Dashboard.tsx`:
  - Quick action badge on EMERGING watchlist cards using `stock.trend_signal`
- Backend endpoints: 20 total (was 16)

## Commits

`552cf0e` `bbfe947`

---

# Version 4.1.0

Phase A — Technical + F&O Intelligence + Market Context Dashboard

Date: 2026-07-02

Status: Completed

---

## Summary

Added real-time technical indicators (52W H/L, DMAs, trend signal) and F&O intelligence
(futures OI, OI signal) for the full stock universe, plus a market PCR pulse dashboard.

## Changes

- `engines/intelligence/technical_engine.py` (new):
  - 52W High/Low proximity, 20/50/200 DMA, trend_signal (STRONG_UPTREND to STRONG_DOWNTREND)
  - Output: `data/intelligence/technical_indicators.csv` (2717 rows)
- `engines/intelligence/fno_engine.py` (new):
  - Per-stock futures OI, 1D/5D OI delta, oi_signal (LONG_BUILDUP / SHORT_COVER / etc.)
  - Output: `data/intelligence/fno_intelligence.csv` (211 F&O stocks)
- `data/intelligence/market_context.json` — market PCR + regime pulse
- GUI: Market Pulse dashboard panel added (PCR, regime, breadth counts)

## Commits

`bbfe947` `1ae9443`

---

# Version 4.0.0

Generation 4 — Investment Operating System Complete (Phases 17-25)

Date: 2026-07-02

Status: Completed

---

## Summary

All 9 Generation 4 phases built and integrated. Platform now covers the full investment
loop: data → intelligence → alerts → GUI → research → portfolio → execution → commercial.

## Phases Completed

| Phase | Name | Key Outputs |
|-------|------|-------------|
| 17 | Symbol Change History | engines/foundation/symbol_change_engine.py; 1038 renames |
| 18 | Corporate Announcements | engines/corporate/; NSE XBRL announcement fetcher |
| 19 | Daily Intelligence Refresh | engines/orchestration/refresh_scheduler.py; APScheduler 18:00 IST |
| 20 | Portfolio Engine | engines/portfolio/; transactions.csv, P&L, sector allocation |
| 21 | Backtesting Framework | engines/backtest/; 3 strategies, 5 horizons, Sharpe/drawdown metrics |
| 22 | Broker Adapter (R/O) | engines/broker/; Dhan + CSV adapters; broker sync engine |
| 23 | Research Platform | engines/research/; 2406-symbol screener, comparator, notes engine |
| 24 | Execution Platform | engines/execution/; risk engine, paper/live orders, signal recommender |
| 25 | Commercial Platform | backend/auth/; SQLite sessions, roles, API keys; auth off by default |

## GUI Pages Added (Phases 17-25)

Portfolio, Backtest, Broker, Research, Execution, Admin (auth config)
GUI total: 14 pages (was 10)

---

# Version 3.12.0

Charts Page: OHLCV candlestick + intraday + IST timestamps + bhavcopy parquet cache

Date: 2026-07-02

Status: Completed

---

## Summary

Built a full-featured Charts page within the React GUI (Phase 11 enhancement) with
TradingView Lightweight Charts v5.2.0, multiple timeframe selectors (5M/15M/1H intraday
and 1D/1W/3M/1Y/3Y/5Y daily), bhavcopy parquet as primary OHLCV source with IST timestamp
correction, and a stock intelligence panel. Fixed multiple v5 API compatibility bugs.

## Changes

- `backend/routers/charts.py` (new router):
  - `GET /api/charts/{symbol}/ohlcv` -- bhavcopy parquet primary + price adjustment pipeline
  - `GET /api/charts/{symbol}/intraday` -- nselib 5M/15M/1H candles with IST offset correction
  - IST_OFFSET = 19800 seconds: lightweight-charts renders unix as UTC; adding offset makes
    IST times display correctly (09:15 IST open shows as 09:15, not 03:45)
  - Deduplication of timestamps in intraday responses (seen set)
- `frontend/src/pages/ChartsPage.tsx` (new page):
  - Timeframe selector: 5M, 15M, 1H (intraday) | 1D, 1W, 3M, 1Y, 3Y, 5Y (daily)
  - TradingView Lightweight Charts v5.2.0 candlestick + volume histogram
  - Reset button; errors caught via useState (ErrorBoundary cannot catch useEffect errors)
  - Removed TradingView attribution watermark logo
  - Stock intelligence panel: bull_run_score, sector, label, price_score
- `frontend/src/App.tsx`: added /charts route
- `backend/main.py`: included charts router

## Bug Fixes

- `chart.priceScale('vol')` -> `volume.priceScale()` (v5 API naming change)
- `useEffect` errors caught via state flag -- ErrorBoundary cannot intercept hook errors
- Duplicate timestamps from nselib response deduplicated server-side
- `from_date`/`to_date` date math corrected for 3M/3Y/5Y ranges
- Volume histogram uses `createHistogramSeries` (not `createVolumeSeries`) in v5

## Commits

`48c6bcf` `93cc755` `31dfb18` `19953ae` `456fcd9` `da40bec` `9e2d389`

---

# Version 3.11.0

Server startup scripts + backend port fix

Date: 2026-07-01

Status: Completed

---

## Summary

Created permanent server startup/shutdown scripts and fixed backend port mismatch (Vite proxy
targets port 8001 but backend was starting on 8000 by default) that caused blank frontend data.

## Changes

- `start.ps1` (new): launches backend (port 8001) and frontend dev server (port 5173) as
  detached OS-level processes via `Start-Process -WindowStyle Hidden`. Survives Claude session
  termination. Idempotent -- checks if port already occupied before starting.
- `stop.ps1` (new): kills both servers by port using netstat PID lookup and Stop-Process.
- `backend/main.py`: startup docstring corrected to show `--port 8001` command.

## Root Cause

Vite proxy in `frontend/vite.config.ts` targets `http://localhost:8001` but backend was
being launched with default `--port 8000`. All API calls silently returned ECONNREFUSED,
causing blank data on every frontend page.

## Commit

`87e252f` -- chore: add start/stop scripts + fix backend port to 8001

---

# Version 3.10.0

Phase 15C -- Shareholding Engine: full historical backfill + data validation + moved to Acquisition section

Date: 2026-07-01

Status: Completed

---

## Summary

Shareholding Engine upgraded with full historical backfill (FY2008 to present), incremental processing,
per-window data validation, and pipeline moved from Fundamentals to Data Acquisition section
in both backend and frontend.

## Changes

- `engines/fundamentals/shareholding_engine.py`: major upgrade
  - Added `_generate_all_windows()`: dynamically generates all quarterly windows from Q1FY09 to current
  - Added `--backfill` flag: fetches all historical quarters oldest-first (incremental: skips done labels)
  - Added `--windows N` flag: fetch N most-recent quarters (default: 1 for incremental mode)
  - Added `--validate` flag: prints per-window data quality report (FII coverage %, symbol count, sum sanity)
  - Per-window validation: min 50 symbols guard, promoter+public sum check, schema validation
  - Historical coverage: NSE SHP API has meaningful data from Q4FY08 (1,264 symbols); pre-FY08 skipped
  - Incremental by default: loads existing quarterly_shp.csv and skips already-fetched windows
- `backend/routers/data_ops.py`:
  - Renamed `fundamentals_15c` → `shp_acquisition` (incremental, --windows 1)
  - Renamed `fundamentals_15c_full` → `shp_acquisition_full` (--backfill, full history)
  - Added `shp_acquisition` to `ACQUISITION_PIPELINE`
  - Moved shareholding status from `fundamentals` dict to `acquisition` dict in /api/data/status
- `frontend/src/pages/DataControlPage.tsx`:
  - Updated ENGINE_MAP: `shareholding: 'shp_acquisition'`
  - Shareholding now appears in DATA ACQUISITION section table (not FUNDAMENTALS)
  - Health bar counts updated to use named variables (acqLen, intLen, funLen)

## Data Availability Note

NSE SHP API returns 0 records before FY05, 10 records for Q4FY05, ~1,264 for Q4FY08.
Practical historical start: Q1FY09 (Apr-Jun 2008). Pre-XBRL era (before 2008) not parseable.
"Since 1995" backfill is not feasible from NSE electronic filings; engine auto-skips those windows.

---

# Version 3.9.0

Phase 15A/15B -- Financial Results + Valuation Engine

Date: 2026-07-01

Status: Completed

---

## Summary

Rewrote Phase 15A financial results engine to fetch real NSE XBRL data using
filing-season date windows. Phase 15B valuation engine fixed to read parquet cache.
Backend upgraded to 22 engines with fundamentals status section.

## Changes

- `engines/fundamentals/financial_results_engine.py`: complete rewrite
  - Replaced FETCH_PERIODS (financial period dates) with FILING_WINDOWS (filing-season dates)
  - Calls get_financial_results_master() directly; skips entries where xbrl ends in /xbrl/-
  - Concurrent XBRL parsing via ThreadPoolExecutor
  - Output: 4,181 rows, 2,084 symbols, Q2FY25 + Q3FY25 coverage (99% EQ universe)
  - Validated: RELIANCE 128,260cr, TCS 63,973cr, INFY 41,764cr match NSE actuals
- `engines/fundamentals/valuation_engine.py`: two fixes
  - _load_prices: reads .parquet from STOCK_HISTORY_CACHE (not .csv)
  - _compute_ttm: uses date_end column (quarterly_results schema)
  - Output: 2,084 symbols, 1,685 PE ratios, 2,034 ROE values, 4 valuation labels
- `backend/routers/data_ops.py`: added 3 Phase 15 engines + fundamentals status section
- `frontend/src/pages/DataControlPage.tsx`: added FUNDAMENTALS section + ENGINE_MAP entries

## Known Gaps

- Major banks (HDFCBANK, ICICIBANK, SBIN) missing from XBRL -- different schema (~5/2083 = 0.24% miss)
- yfinance disabled by default -- empty quarterly_income_stmt for all NSE.NS tickers

## Commit

`228902d` -- fix: valuation engine parquet cache + date_end column
`ec09e7c` -- feat: Phase 15A financial results engine + backend + frontend

---

# Version 3.8.2

Progress bars + Phase 6C pd.NA crash fix

Date: 2026-06-30

Status: Completed

---

## Summary

Added `tqdm` progress bars to engines that process large loops (Phases 5A, 7B, 7C)
and fixed a `TypeError` crash in Phase 6C when printing the sector rotation table.

## Changes

- `participant_acquisition_engine.py` (5A): progress bars on F&O and cash date loops
- `corporate_action_intelligence_engine.py` (7C): progress bar on 28-file CSV loading loop
- `corporate_event_calendar_engine.py` (7B): progress bar on chunked 30-day download loop
- `sector_rotation_intelligence_engine.py` (6C): fixed `int(pd.NA)` TypeError in
  `_print_summary()` -- replaced `or 0` chain with explicit `pd.isna()` guard

## Verification

Full stack run (Phases 5–14) completed successfully with all phases PASS.
Phase 6C no longer crashes when combined_rank contains pd.NA (nullable Int64).

## Commit

`768c662` -- Add progress bars to Phases 5A/7B/7C and fix Phase 6C pd.NA crash

---

# Version 3.8.1

Phase 16B Fix -- AnnouncementFetcher bulk API rewrite

Date: 2026-06-30

Status: Completed

---

## Summary

Fixed `announcement_fetcher.py` to use nselib bulk `corporate_actions_for_equity(period='6M')`
instead of the non-existent `shareholding_patterns()` method. Added `_fetch_bulk()` and
`_parse_bulk()` methods. Fixed date normalization bug (premature truncation before regex).

## Results

- `board_announcements.csv`: 527 records, 471 symbols (DIVIDEND 446, BONUS 24, BUYBACK 19)
- `management_sentiment.csv`: 471 symbols scored (POSITIVE 435, NEUTRAL 36)
- Note: HoldingTrendEngine still defaults to STABLE (no nselib shareholding API available)

## Commit

`da5623f` -- Fix announcement_fetcher.py: add _fetch_bulk() using nselib bulk corporate_actions

---

# Version 3.8

Phase 16 -- Management Intelligence Layer

Date: 2026-06-30

Status: Completed

---

## Summary

Built the Management Intelligence Layer (Phase 16) in `engines/management/` -- 3 engines:
holding trend, announcement fetcher, and management sentiment scorer with optional Claude AI tone.

## Engines Built

| File | Purpose |
|------|---------|
| engines/management/holding_trend_engine.py | QoQ promoter/FII/DII delta + 7 conviction signals |
| engines/management/announcement_fetcher.py | Board meeting fetch + 8-type keyword classification |
| engines/management/management_sentiment_engine.py | Rule-based + Claude AI tone score (0-100) |

## Output Files

data/NSE/shareholding/holding_trends.csv -- promoter/FII/DII QoQ deltas, conviction_signal
data/NSE/shareholding/board_announcements.csv -- classified board announcements
data/NSE/shareholding/management_sentiment.csv -- management_score, management_label

---

# Version 3.7

Phase 15 -- Financial Results + Valuation Engine

Date: 2026-06-30

Status: Completed

---

## Summary

Built two financial fundamentals engines (Phase 15): quarterly results fetcher and
valuation scorer with P/E + ROE + growth composite.

## Engines Built

| File | Purpose |
|------|---------|
| engines/fundamentals/financial_results_engine.py | Quarterly P&L via nselib bulk + yfinance fallback |
| engines/fundamentals/valuation_engine.py | P/E, ROE, growth scoring -> valuation_label |

## Notes

NSE XBRL archive endpoint returns 404 intermittently. Engine handles gracefully.
Valuation scores compute from available data and skip missing symbols.

---

# Version 3.6

Phase 13-14 -- RAG Knowledge Base + AI Chatbot

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete AI intelligence layer: RAG knowledge base (Phase 13) with hybrid
BM25 + FAISS retrieval, and the AI chatbot (Phase 14) with Claude tool use + RAG context.

## Phase 13 -- RAG Knowledge Base

| File | Purpose |
|------|---------|
| engines/ai/knowledge/document_builder.py | 1091 text documents from 6 intelligence CSVs |
| engines/ai/knowledge/bm25_indexer.py | BM25Okapi sparse keyword index |
| engines/ai/knowledge/faiss_indexer.py | sentence-transformers dense index, 6 domain indexes |
| engines/ai/knowledge/retriever.py | RRF hybrid fusion, domain auto-detection |
| engines/ai/knowledge/index_updater.py | Daily rebuild pipeline |

## Phase 14 -- AI Chatbot

| File | Purpose |
|------|---------|
| engines/ai/chatbot/intent_router.py | Keyword intent detection (MARKET/SECTOR/STOCK/CORPORATE) |
| engines/ai/chatbot/tools/data_tools.py | 11 data access functions over intelligence CSVs |
| engines/ai/chatbot/tools/tool_registry.py | Anthropic API tool schemas + dispatch |
| engines/ai/chatbot/chat_engine.py | Multi-turn agentic loop with RAG injection |
| backend/routers/chat.py | POST /api/chat, in-memory session management |

## Packages Installed

sentence-transformers==5.6.0, faiss-cpu==1.14.3, rank-bm25==0.2.2, anthropic==0.113.0

---

# Version 3.5

Phase 12 -- ML Intelligence Layer

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete ML Intelligence Layer (Phase 12) in `engines/ml/` -- 4 engines:
feature engineering, accumulation model (XGBoost), bull run ensemble (LightGBM+XGBoost),
and daily inference scorer. Produces 2 new intelligence CSVs and saves trained model files.

---

## Engines Built

| File | Purpose |
|------|---------|
| engines/ml/feature_engineering.py | Builds 24-feature snapshot matrix from 6 intelligence CSVs |
| engines/ml/accumulation_model.py | XGBoost binary classifier, target: label_enc >= 3 |
| engines/ml/bull_run_model.py | LightGBM (0.6) + XGBoost (0.4) ensemble, multi-class |
| engines/ml/ml_scorer.py | Daily orchestrator: rebuild features + load models + score all |

## Output Files

| Output | Description |
|--------|-------------|
| data/intelligence/ml_features/feature_matrix.parquet | 2441 symbols x 24 features |
| data/intelligence/ml_accumulation_scores.csv | XGBoost binary scores (0-100) |
| data/intelligence/ml_bull_run_scores.csv | Ensemble scores + per-class probabilities |
| data/intelligence/ml_shap_values.csv | SHAP feature importance for top 100 symbols |
| data/intelligence/ml_scores_combined.csv | Daily combined output |
| data/intelligence/ml_features/models/ | Saved model files (XGBoost .json, LightGBM .txt) |

## Feature Groups (24 features)

Phase 8B scores: bull_run_score, price_score, sector_flow_score, deal_score,
                 corporate_score, regime_multiplier
Price:           ret_30d, ret_90d, ret_365d, vol_ratio
Sector:          sector_FII_flow, sector_combined_score, rotation_signal_enc (ordinal 0-5)
Participant:     part_FII_flow, part_DII_flow, part_smart_money, regime_enc (ordinal 0-4)
Corporate:       corp_confidence, deal_net_cr

## Packages Installed

xgboost==3.2.0, lightgbm==4.6.0, scikit-learn==1.9.0, shap==0.51.0
pyarrow upgraded 15.0.0 -> 24.0.0 (numpy 2.x compatibility)
pandas upgraded 2.2.0 -> 3.0.3 (sklearn dependency)

## Known Limitations (by design)

- Target is score-based proxy (not actual forward price return) until bhavcopy
  time-series target generation is available in a future phase
- TimeSeriesSplit CV on snapshot data is artificial; true CV requires time-series features
- ML scores are correlated with rule-based scores (same underlying features)

---

# Version 3.4

Phase 11 — React GUI

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete React GUI (Phase 11) in `frontend/` — 10 pages, 5 platform components,
TypeScript build clean, Vite proxy to FastAPI backend.

---

## Pages Built

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | / | Regime, flows, top sectors, EMERGING watchlist |
| Sectors | /sectors | All 29 sectors grouped by rotation_signal |
| Sector Detail | /sectors/:sector | Sector scores + top 10 stocks |
| Watchlist | /watchlist | Paginated 2441 symbols table with label filter |
| Stock Detail | /stocks/:symbol | 4-factor gauges, price performance, deal signals |
| Participant | /participant | FII/DII/PRO/CLIENT cards + 90D area chart |
| Corporate | /corporate | Deals table + upcoming catalysts |
| AI Chat | /chat | Phase 14 placeholder |
| Settings | /settings | Freshness, alert config, platform info |

## Platform Components

ScoreGauge, CapFlowBadge, FlowCard, RegimeBanner, SectorTile, AppShell

## Tech Stack

React 18 + TypeScript + Vite + Tailwind CSS + Zustand + TanStack Query + Recharts

---

# Version 3.3

Phase 10 — FastAPI Backend

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete FastAPI Backend (Phase 10) in `backend/` — REST API serving all 11
intelligence CSVs via 16 endpoints, in-memory data loader with 60min auto-reload,
and WebSocket live ticker.

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app entry point, CORS, startup, /health |
| `backend/services/data_loader.py` | Thread-safe CSV cache, 60min background reload |
| `backend/routers/market.py` | /api/market/regime + freshness |
| `backend/routers/participant.py` | /api/participant/latest + history |
| `backend/routers/sectors.py` | /api/sectors (all 29) + history + detail |
| `backend/routers/stocks.py` | /api/stocks (2441) + watchlist + detail + momentum |
| `backend/routers/corporate.py` | /api/corporate/deals + catalysts + confidence + events |
| `backend/ws/live_ticker.py` | WebSocket /ws/live (regime + sectors every 30s) |

---

## Test Results (2026-06-30)

16/16 endpoints PASS. Key data:
- NEUTRAL regime | FII +10.91 | DII -4.52
- 29 sectors | 2441 symbols | 225 EMERGING
- 12 upcoming catalysts | 1111 corporate confidence scores

---

## Packages Added

- fastapi==0.138.2
- uvicorn[standard] (watchfiles, httptools)

---

# Version 3.2

Phase 9 — Alert System

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete Alert System (Phase 9) in `alerts/` — five files covering signal
evaluation, cooldown tracking, Telegram delivery, daily digest, and APScheduler orchestration.

---

## Files Created

| File | Phase | Purpose |
|------|-------|---------|
| `alerts/alert_engine.py` | 9A | Evaluates 6 intelligence CSVs, emits 7 alert types |
| `alerts/alert_store.py` | 9B | Cooldown tracking, dedup, atomic JSON state |
| `alerts/telegram_bot.py` | 9C | Telegram Bot API delivery, HTML formatting |
| `alerts/daily_digest.py` | 9D | 18:30 IST daily intelligence summary |
| `alerts/alert_scheduler.py` | 9E | APScheduler: digest + post-market checks |
| `docs/decisions/ADR-021-Alert-System-Architecture.md` | — | Architecture decision record |

---

## Alert Types (Priority Order)

| Priority | Type | Cooldown | Source |
|----------|------|---------|--------|
| P1 | REGIME_CHANGE | None | participant_intelligence.csv |
| P2 | STRONG_CANDIDATE | 72h | bull_run_probability.csv |
| P3 | SECTOR_ROTATION | 48h | sector_rotation_intelligence.csv |
| P4 | INSTITUTIONAL_DEAL | 48h | institutional_deal_signals.csv |
| P5 | CORPORATE_CONFIDENCE | 48h | corporate_confidence_scores.csv |
| P6 | PARTICIPANT_DIVERGENCE | 48h | participant_intelligence.csv |
| P7 | DAILY_DIGEST | 24h | all layers |

---

## Test Results (2026-06-30)

- alert_engine: 118 alerts on first run (P1 regime change + P3/P4/P5/P6)
- alert_store: cooldown filter verified
- daily_digest: 690-char HTML digest with 5 sections
- alert_scheduler: APScheduler imports and jobs verified

---

## Packages Added

- APScheduler==3.11.3
- python-telegram-bot==21.11.1

---

# Version 3.1

Phase 8 — Bull Run Probability Engine (8A / 8B)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the Bull Run Probability Engine in `engines/intelligence/` — two engines that combine
all previously built intelligence layers into a per-stock bull run probability score.

---

## Engines Created

| File | Phase | Output |
|------|-------|--------|
| `engines/intelligence/price_momentum_engine.py` | 8A | `data/intelligence/price_momentum.csv` |
| `engines/intelligence/bull_run_probability_engine.py` | 8B | `data/intelligence/bull_run_probability.csv` + watchlist |

---

## Intelligence Architecture

### Price Momentum Score (Phase 8A)
- Reads 5 reference bhavcopy dates: latest, 30D, 60D, 90D, 365D ago
- Reads 22 bhavcopy files for 20D volume average
- Per-symbol: ret_30d, ret_60d, ret_90d, ret_365d, vol_ratio, sector_rel_30d
- All metrics percentile-ranked (0-100) across 2441-symbol universe
- Composite price_score: ret_30d (35%) + ret_90d (25%) + ret_365d (20%) + sector_rel (15%) + vol (5%)
- Handles dual bhavcopy schema (pre/post-2020 column names)
- 2441 symbols scored, as_of_date: 2026-06-10

### Bull Run Probability Score (Phase 8B)
- 4-factor weighted combination:
  - Price Momentum Score: 30% (from 8A, already 0-100)
  - Sector Capital Flow Score: 25% (FII_flow_score from sector_rotation_intelligence.csv rescaled 0-100)
  - Institutional Deal Score: 25% (inst_net_value_cr percentile-ranked; neutral 50 if no deal data)
  - Corporate Confidence Score: 20% (confidence_score_12m clipped [-3,6] rescaled 0-100)
- Market Regime Multiplier from institutional_positioning_history.csv:
  - ACCUMULATION: ×1.10  DISTRIBUTION: ×0.80  others: ×0.90
- Final score clipped to [0, 100]

### 2026-06-30 Results
- 2441 symbols scored
- Regime: DISTRIBUTION (×0.80 multiplier)
- Score range: 12.3 to 54.9 (DISTRIBUTION caps ceiling below 65)
- EMERGING: 16 symbols (max possible in DISTRIBUTION regime)
- WATCHLIST: 1599 symbols
- NEUTRAL: 824 symbols
- AVOID: 2 symbols
- Top candidates: ADANIENSOL (55), ADANIENT (51), GMRAIRPORT (50), CRAFTSMAN (48), EMCURE (48)

---

# Version 3.0

Phase 7 — Corporate Intelligence Layer (7A / 7B / 7C)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the Corporate Intelligence Layer (`engines/corporate/`) per ADR-020 Domain 3+4.
Three engines provide stock-level intelligence that feeds into the Bull Run Probability
engine (Phase 8): institutional deal signals, upcoming catalysts, and corporate confidence scores.

---

## Deliverables

### Engines (engines/corporate/)
- `block_bulk_deal_engine.py` (7A) — incremental downloader for NSE block/bulk deals.
  Classifies each client as FII/MF/INSURANCE/PROMOTER/RETAIL via keyword matching.
  Computes 30D net institutional buying per symbol → deal_signal.
- `corporate_event_calendar_engine.py` (7B) — downloads event calendar (board meetings,
  results dates) from 2023-01-01 to present. Identifies upcoming catalysts in next 60D,
  prioritized by event type × sector_rotation_intelligence combined score.
- `corporate_action_intelligence_engine.py` (7C) — processes all 40,517 existing corporate
  actions (1999-2026). Classifies DIVIDEND/BONUS/SPLIT/BUYBACK/RIGHTS/MERGER/AGM_EGM.
  Extracts amounts/ratios. Computes rolling 12M corporate confidence score per symbol.

### New Data Files
- `data/intelligence/block_bulk_deals.csv` — 12,467 rows (6M block/bulk deal history)
- `data/intelligence/institutional_deal_signals.csv` — 361 symbols, 30D net signals
- `data/intelligence/event_calendar.csv` — 33,839 rows (2023-2026)
- `data/intelligence/upcoming_catalysts.csv` — next 60D events, priority scored
- `data/intelligence/corporate_action_signals.csv` — 40,517 classified actions (1999-2026)
- `data/intelligence/corporate_confidence_scores.csv` — 1,111 symbols, 12M rolling score

---

## Design Decisions

- Financial results via nselib XBRL endpoint returns 404 — skipped for this phase
- Management Intelligence (NLP, transcripts) — deferred to Phase 8+ (requires AI pipeline)
- Shareholding patterns — deferred (data not yet acquired)
- Participant classification: keyword matching on client name (heuristic, good enough for FII/MF detection)
- Corporate confidence weights: BUYBACK +3 > BONUS +2 > SPLIT +1 > DIVIDEND +0.5 > RIGHTS -0.5
- Catalyst score = purpose_priority × 10 + sector_combined_score / 10 (blends event type + sector flow)

---

# Version 2.9

Phase 6 — Sector Rotation + Capital Flow Engines (6A / 6B / 6C)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built three sector-level capital flow engines that weight-allocate total participant F&O flows
to each of the 29 platform sectors using daily bhavcopy turnover weights, then derive rolling
flow scores, z-score normalisation, rotation signals, and a combined price + flow intelligence snapshot.

---

## Deliverables

### Engines (engines/participant/)
- `sector_capital_flow_engine.py` (6A) — reads 7813 bhavcopy files (2016-2026, dual schema support
  for pre-2020 and post-2020 column formats), weight-allocates FII/DII/PRO/CLIENT OI and Volume flows
  to 29 platform sectors by daily turnover weight. Incremental.
- `sector_flow_score_engine.py` (6B) — OI delta, rolling 5D/20D/60D sums, z-score flow scores
  (-100..+100) per sector per participant. Full rebuild.
- `sector_rotation_intelligence_engine.py` (6C) — combines flow scores + NSE index price momentum
  (from Phase 3 index_strength.csv) into rotation signal, capital flow alignment, and combined rank.
  Outputs both a latest snapshot and a full time-series.

### New Data Files
- `data/intelligence/sector_capital_flows.csv` — 74,269 rows, 29 sectors x 2561 dates (2016-2026)
- `data/intelligence/sector_flow_scores.csv` — 74,269 rows, 35 cols per sector per date
- `data/intelligence/sector_rotation_intelligence.csv` — 29-row snapshot (latest date)
- `data/intelligence/sector_rotation_history.csv` — full time-series for GUI charting

---

## Design Decisions

- Turnover weight allocation: `sector_weight = sector_turnover / total_market_turnover` (close x qty / 1e7 crores)
- Dual bhavcopy schema: pre-2020 uses CLOSE/TOTTRDQTY columns; post-2020 uses CLOSE_PRICE/TTL_TRD_QNTY
- Z-score: 252-day rolling window, clipped to +/-3, scaled to +/-100 (consistent with Phase 5B)
- Combined score: 60% participant flow score (leading) + 40% price momentum (confirming)
- Rotation quadrants: STRONG_ACCUMULATION (flow+, price+), EARLY_ROTATION (flow+, price-),
  PRICE_LED (flow-, price+), DISTRIBUTION (flow-, price-)
- NSE index -> platform sector: static mapping covering 32 NSE indices to 29 platform sectors

---

# Version 2.8

Phase 5 — Participant Intelligence Layer (5A / 5B / 5C)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the Participant Intelligence Layer (`engines/participant/`) per ADR-016.
Three engines track capital flow by participant category (FII, DII, PRO, CLIENT)
across F&O and cash market channels.

---

## Deliverables

### Engines (engines/participant/)
- `participant_acquisition_engine.py` (5A) — incremental downloader for F&O OI/Volume +
  new cash market flows history; fills gap 2026-06-03 to today; extends cash history from 2024-01-01
- `participant_flow_engine.py` (5B) — OI delta, rolling sums (5D/20D/60D), normalized
  z-score flow scores (−100..+100) per participant; full rebuild on run
- `participant_intelligence_engine.py` (5C) — conviction (% positive days in 20D window),
  Smart Money Score, Retail Score, divergence signals, Market Opportunity, ensemble Market Regime

### New Data Files
- `data/historical/institutional/cash_market_flows_history.csv` — cash flows by FPI/MF/Insurance/Retail (2024+)
- `data/intelligence/participant_flow_scores.csv` — rolling metrics + normalized scores
- `data/intelligence/participant_intelligence.csv` — conviction, divergence, smart money, regime

### Module Context
- `engines/participant/CLAUDE.md` — data sources, schemas, F&O net formula, column quirks
- `engines/participant/__init__.py` — package init

---

## Design Decisions

- F&O net position = futures only (Index + Stock Long − Short); options excluded for cleaner signal
- Score normalisation: rolling z-score over 252-day window, clipped ±3, scaled to ±100
- Market Regime ensemble: Smart Money 50%, DII 25%, Cash Institutional 25%
- Market Opportunity = max(0, Smart) × max(0, −Retail) / 100 — fires when smart money accumulates AND retail sells
- Backward compatible with Phase 7 institutional_positioning_history.csv (21-column schema preserved)

---

---

# Purpose

This document records all major project milestones, architecture decisions, strategic changes, documentation updates, and development achievements.

The changelog serves as the historical record of the platform's evolution.

---

# Versioning Philosophy

The platform follows milestone-based versioning.

Major versions are created when:

* Architecture changes significantly
* New intelligence layers are introduced
* Strategic direction changes
* Major modules are completed

---

# Version 2.7

Phase 4D — NSE Constituents Engine V1

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the NSE index constituent downloader using `nsearchives.nseindia.com/content/indices/`
(open endpoint, no auth required). Downloads 30 NSE indices in one run — 12 broad-market
cap-tier indices + 18 sector/theme/strategy indices. Produces one constituent CSV per index
plus a master `index_membership.csv` mapping each symbol to all its indices with sector hints.

---

## Deliverables

### Engine
- `engines/foundation/nse_constituents_engine_v1.py` — complete rewrite (class-based, all guardrails)

### Outputs (data/NSE/indices/)
- `nifty_50_constituents.csv` through `nifty_smallcap_250_constituents.csv` — 30 files, one per index
- `index_membership.csv` — 506 unique symbols; columns: symbol, index_names, sector_hints, dominant_sector_hint
- `reports/download_registry.csv` — status per index (30 SUCCESS, 0 FAILED)
- `reports/constituents_recovery_queue.csv` — empty (all succeeded)

### Index Coverage (30 indices, 2519 constituent rows total)
Broad market (12): NIFTY 50, NEXT 50, 100, 200, 500, MIDCAP 50/100/150, SMALLCAP 100/250, LARGEMIDCAP 250, MIDSMALLCAP 400
Sector (14): AUTO, PHARMA, IT, METAL, FMCG, MEDIA, REALTY, BANK, PSU BANK, HEALTHCARE, OIL & GAS, ENERGY, FINANCIAL SERVICES 25/50, CONSUMER DURABLES
Strategy/PSU (4): COMMODITIES, MNC, CPSE, PSE

### Key Verifications
- TCS → dominant_sector_hint=IT ✅
- HDFCBANK → dominant_sector_hint=BANKING ✅
- MARUTI → dominant_sector_hint=AUTO ✅
- ONGC → dominant_sector_hint=ENERGY ✅
- SUNPHARMA → sector_hints=HEALTHCARE|PHARMA ✅
- All 30 downloads: HTTP 200, schema valid, EQ series filter applied

### Not Available on nsearchives (for future work)
NIFTY FINANCIAL SERVICES (main), NIFTY PRIVATE BANK, NIFTY CHEMICALS, NIFTY CEMENT,
NIFTY INFRASTRUCTURE, NIFTY TOTAL MARKET, NIFTY INDIA DEFENCE, NIFTY EV,
NIFTY INDIA DIGITAL, NIFTY INDIA MANUFACTURING, NIFTY TRANSPORTATION & LOGISTICS

---

# Version 2.6

Phase 4C — Classification Engine V4 Completion

Date:

2026-06-30

Status:

Completed

---

## Summary

Rewrote `classification_engine_v4.py` as a proper 5-level hierarchical classifier using
industry_master as primary lookup. Applied symbol-level corrections for all 71 previously
OTHER symbols, reducing OTHER from 71 to 10 (genuinely miscellaneous businesses).
Coverage improved from 96.7% → 99.53% non-OTHER. Also writes `company_classification_v4.csv`
with source tracking (INDUSTRY_MASTER / SYMBOL_CORRECTION / KEYWORD_MATCH / MANUAL_OVERRIDE).

---

## Deliverables

### Engine
- `engines/fundamentals/classification_engine_v4.py` — complete rewrite (hierarchical, 5 levels, all guardrails)

### Outputs
- `data/reference/company_classification_v4.csv` — 2123 rows, 7 cols (with SOURCE tracking)
- `data/NSE/equity_master/company_fundamentals_master.csv` — UPDATED (99.53% coverage)
- `data/NSE/equity_master/classification_coverage_report.csv` — metrics snapshot
- `data/NSE/equity_master/classification_review_queue.csv` — 10 symbols needing manual review
- `data/NSE/equity_master/classification_sector_counts.csv` — per-sector counts

### Key Corrections in SYMBOL_CORRECTIONS Dict (60 symbols reclassified from OTHER)
- ICICIAMC / NAM-INDIA / UTIAMC → AMC / FINANCIALISATION
- SUPRAJIT / MAJESAUT / PTL → AUTO / EV_TRANSITION
- HARSHA / INTLCONV / SANGHVIMOV / DYNAMATECH / OMNI / TEXINFRA → CAPITAL_GOODS
- INDIQUBE / NESCO / NIRLON / SMARTWORKS / EFCIL / HEMIPROP / WEWORK / MERCANTILE → REALTY
- CYBERTECH / GENESYS / SASKEN / DSSL / REDINGTON → IT / DIGITAL_INDIA
- SPCENET → TELECOM / DIGITAL_INDIA
- DEVYANI / ADVENTHTL → HOSPITALITY / PREMIUMISATION
- GICL / TARACHAND / TVSSCS → LOGISTICS / LOGISTICS_MODERNISATION
- DBSTOCKBRO / ALANKIT / CMSINFO / RADIANTCMS / PRUDENT / ICDSLTD → FINANCIAL_SERVICES
- SOUTHWEST / KOTYARK → ENERGY; SHIVAUM / GOYALALUM / MSTCLTD → METAL
- RUCHINFRA / ELITECON → INFRASTRUCTURE; VIKASLIFE / FLEXITUFF / RUBFILA / SICAGEN / IWP → CHEMICALS
- KOTHARIPRO / VINCOFE / GOLDIAM → FMCG; UMAEXPORTS → AGRICULTURE; LAHOTIOV → TEXTILES
- TOUCHWOOD → MEDIA; ACEINTEG → DEFENCE; CNL → RETAIL; BLUSPRING → POWER
- STCINDIA / MMTC → DIVERSIFIED / PSU_REVIVAL

### Remaining OTHER (10 — genuinely miscellaneous, no dominant sector)
AARVI, AKG, DEVX, KAPSTON, KRYSTAL, LANDSMILL, METROGLOBL, QUESS, SIS, UDS
(staffing / facility management / export trading / startup incubator)

### Final State after Phase 4C
- Total symbols: 2,123
- Classified (non-OTHER): 2,113 (99.53%)
- OTHER: 10 (0.47%)
- UNCLASSIFIED: 0

---

# Version 2.5

Phase 4B — Industry Master Engine

Date:

2026-06-29

Status:

Completed

---

## Summary

Built the authoritative industry_nse → sector_platform + theme_platform lookup table covering
all 183 unique NSE industry classifications across 2123 symbols. Immediately applied the master
back to improve company_fundamentals_master.csv to 96.7% sector coverage and 100% theme coverage.

---

## Deliverables

### Engine
- `engines/fundamentals/industry_master_engine.py` — complete rewrite (class-based, all guardrails)

### Outputs
- `data/reference/mapping/industry_master.csv` — 183 rows, 10 columns (authoritative lookup table)
- `data/NSE/equity_master/company_fundamentals_master.csv` — UPDATED (96.7% sector, 100% theme)

### Bug Fixes (in engine development)
- `_manual_theme` column NaN propagation — fixed by initializing to "" before loop
- `float('nan')` is truthy in Python — fixed with `pd.notna()` guard

### Industry Groups (10 groups across 183 industries)
- MANUFACTURING: 59 industries
- CONSUMER: 31 industries
- INFRASTRUCTURE_ENERGY: 30 industries
- FINANCIAL_SERVICES: 20 industries
- TECHNOLOGY: 19 industries
- HEALTHCARE: 10 industries
- REAL_ESTATE: 6 industries
- OTHER: 5 industries (DISTRIBUTORS, DIVERSIFIED COMMERCIAL SERVICES, etc.)
- AGRICULTURE: 2 industries
- DIVERSIFIED: 1 industry

### Key Corrections Applied
- DIVERSIFIED COMMERCIAL SERVICES (37 cos): IT → OTHER (staffing/facility mgmt ≠ IT)
- COAL (3 cos): POWER → ENERGY with PSU_REVIVAL theme
- PACKAGING (31 cos): OTHER → CHEMICALS with CHINA_PLUS_ONE theme
- PAPER AND PAPER PRODUCTS (21 cos): OTHER → CHEMICALS
- FURNITURE HOME FURNISHING (10 cos): OTHER → REALTY
- HOUSEWARE (4 cos): OTHER → FMCG
- AMUSEMENT PARKS (3 cos): OTHER → HOSPITALITY

### Final State after Phase 4B
- ISIN: 100%
- Sector classified (non-OTHER): 96.7%
- Theme populated: 96.3% (strings only; 3.7% = OTHER sector → no theme, by design)
- No industries in review queue (all 183 at high confidence)

---

# Version 2.4

Phase 4A — Company Fundamentals Master Engine

Date:

2026-06-29

Status:

Completed

---

## Summary

Built the authoritative company master for all 2123 EQ active symbols.
Passes all 4 spec success criteria. Resolves the ADANIPORTS→LOGISTICS classification bug.
Output at `data/NSE/equity_master/company_fundamentals_master.csv`.

---

## Deliverables

### Engine
- `engines/fundamentals/company_fundamentals_master_engine.py` — complete rewrite (class-based, all guardrails)

### Outputs
- `data/NSE/equity_master/company_fundamentals_master.csv` — 2123 rows, 15 columns
- `data/NSE/equity_master/fundamentals_review_queue.csv` — 103 symbols for manual review
- `data/NSE/equity_master/fundamentals_coverage_report.csv` — coverage metrics

### Supporting Data
- `data/reference/mapping/manual_override.csv` — created with 8 known misclassification corrections

### Success Criteria (all PASS)
- industry_nse populated: 100% (spec: 95%+)
- ISIN null count: 0 (spec: ZERO)
- listing_date null count: 0 (spec: ZERO)
- ADANIPORTS sector: LOGISTICS (spec: LOGISTICS/PORTS not AEROSPACE)

### Coverage
- ISIN: 100%
- Sector classified (non-OTHER): 95.1%
- Theme classified: 94.8%
- Market cap known: 100%

### Key Fixes Applied
- ADANIPORTS: CHEMICALS (Screener error) → LOGISTICS via manual_override.csv
- ONGC: AGRI (Screener error) → ENERGY via manual_override.csv
- TCS + consulting firms: PROFESSIONAL_SERVICES → IT via SECTOR_NORMALIZE fix
- Packaging companies: mapped to CHEMICALS (packaging materials)
- Education companies: mapped to HEALTHCARE (theme alignment)

### Architecture
- SECTOR_NORMALIZE dict: 44 mappings (28 canonical + 16 legacy/alternate names)
- SECTOR_TO_THEME dict: 25 sector → theme mappings (basic; Phase 4B refines via industry_master)
- manual_override.csv applied last — immutable (G-C-02)
- All guardrails: atomic write, schema validation, empty df guard, universe size check

---

# Version 2.3

ML / AI / Chatbot Architecture — Modules 14, 15, 16 Added

Date:

2026-06-29

Status:

Completed

---

## Summary

Designed and documented ML Intelligence, AI Knowledge Base (RAG), and Chatbot Platform layers.
Added 3 new modules (14, 15, 16) to MODULE_REGISTRY. Platform now has a clear roadmap from raw
NSE data through ML scoring → RAG retrieval → conversational AI interface. Claude API
(claude-sonnet-4-6) selected as the LLM backbone. Chat history restructured to module-wise append files.

---

## Deliverables

### Architecture Document
- `docs/architecture/ML_AI_CHATBOT_ARCHITECTURE.md` — full ML/AI/Chatbot spec (8 sections)

### New Modules
- Module 14: ML Intelligence Layer (0%, Planned) — XGBoost/LightGBM accumulation, sector rotation, bull run, anomaly, NLP classification
- Module 15: AI Knowledge Base / RAG (0%, Planned) — FAISS + BM25 hybrid retrieval over all intelligence outputs
- Module 16: Chatbot Platform (0%, Planned) — 7 agents, tool registry, WebSocket, React chat UI

### Module Updates
- Module 07 (AI Platform): Architecture expanded with full Claude API integration spec

### Process Changes
- Chat history restructured to module-wise append files (`chat history/module_NN_<name>.md`)
- Old session-based files deprecated — all new entries append to module files

### ADR References
- ADR-021: ML Intelligence Layer
- ADR-022: RAG Knowledge Base
- ADR-023: Chatbot / Conversational AI

---

## Build Dependencies (ML/AI/Chatbot cannot start until)

1. Phase 4A (Company Fundamentals Master Engine) — unblocks ML-1 Feature Engineering
2. Phase 3B outputs (intelligence CSVs) — unblocks RAG-1 (available now for partial indexing)
3. Phase 6 (Sector Rotation Engines) — unblocks ML-4 Sector Rotation Model

---

# Version 2.2

GUI Architecture Planning — React + FastAPI Implementation Plan

Date:

2026-06-29

Status:

Completed

---

## Summary

Designed and documented the full React-based GUI for the Capital Flow Intelligence Platform.
Created `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` covering technology stack, design system,
13 pages, 13 build phases, FastAPI backend contract, state management, and IST-aware utilities.
Module 08 (GUI Platform) advances from 10% to 25%.

---

## Deliverables

### Architecture Document
- `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` — 15-section complete build specification

### Technology Decisions (Locked)
- Frontend: React 18 + TypeScript + Vite
- Styling: Tailwind CSS + CSS Variables (dark terminal theme)
- Charts: Recharts (heatmaps/flows) + TradingView Lightweight Charts (OHLCV)
- Server State: TanStack Query v5
- Client State: Zustand
- Routing: React Router v6
- Backend: FastAPI + Uvicorn (already in requirements.txt)
- Real-time: WebSocket — live flow ticker during market hours only

### Design System (Defined)
- Dark terminal palette (#0A0D14 background)
- Participant colors: FII=Blue, DII=Indigo, PRO=Amber, CLIENT=Pink
- Score gradient: Red (0-30) → Amber (30-60) → Green (60-80) → Emerald (80-100)
- 3-Second Rule: market regime + FII net + top sector visible on landing

### Pages Designed (13 total)
Dashboard, Market, Sectors, SectorDetail, Themes, ThemeDetail,
Stocks (screener), StockDetail, Portfolio, Research, AI Assistant, Reports, Settings

### Build Phases Defined (GUI-1 through GUI-13)
GUI-1: AppShell → GUI-4: FastAPI data wiring (needs Phase 4A) → GUI-9: AI Assistant → GUI-13: Auth

### Key Components Specified
- `CapitalFlowCascade` — Sankey: Market → Sector → Theme → Stock
- `SectorHeatmap` — Recharts Treemap (size=market cap, color=flow score)
- `FlowCard` — FII/DII/PRO/CLIENT buy/sell/net with 7-day sparkline
- `OhlcvChart` — TradingView LC with delivery % + FII flow overlay panes

### FastAPI Contract
- 14 REST endpoints + 1 WebSocket (`/ws/live-flow`)
- Standard envelope: `{ status, data, meta: { generated_at, data_as_of, cache_hit } }`

### Session Protocol
- `chat history/session_2026_06_29_gui_plan.md` saved
- Memory updated in `memory/project_fii_dii.md`

---

# Version 2.1

Phase 3B: Guardrail Utility Library + Complete Test Suite

Date:

2026-06-29

Status:

Completed

---

## Summary

Implemented the complete guardrail utility library (`engines/common/guardrails.py`) with 55
functions covering all 12 guardrail sections, paired with a full pytest test suite across 16 test
files (~400 test cases). Introduced phased development protocol: every phase ends with a session
log saved to `chat history/`, memory update, and CHANGELOG entry.

---

## Deliverables

### Guardrail Library
- `engines/common/guardrails.py` — 55 utility functions, all logging at DEBUG level
- All 12 guardrail sections covered (Data, API, Symbol, Price, Classification, Corporate Actions,
  Intelligence, Financial Results, Trading Calendar, Institutional, System, Performance)

### Test Infrastructure
- `pytest.ini` — DEBUG logging to `tests/logs/pytest_debug.log`
- `tests/conftest.py` — 10 shared fixtures + autouse `log_test_boundaries`
- `requirements.txt` — added pytest>=8.0.0 and pytest-mock>=3.0.0

### Guardrail Test Files (tests/guardrails/)
12 files covering G-D-01 through G-PERF-04 (all 55 rules)

### Edge Case Test Files (tests/edge_cases/)
4 files covering India-specific edge cases: mergers/IPOs, circuit breakers,
PSU/holding co classification, institutional T+1 lag, Budget Day, F&O expiry

### Supporting Files
- `tests/CLAUDE.md` — test directory context for future sessions
- `chat history/session_2026_06_29_phase3b_guardrails_and_tests.md` — session log
- `memory/project_fii_dii.md` — updated with Phase 3B completion + phased dev protocol

### Process Improvements
- Phased development protocol established (session log + memory update + changelog after every phase)

---

# Version 2.0

Claude AI Development Infrastructure Release

Date:

2026-06-29

Status:

Completed

---

## Summary

Established complete AI-assisted development infrastructure: master Claude guide,
directory-level skill files (CLAUDE.md), platform guardrails, and edge case registry.
This release makes Claude a self-sufficient platform architect without re-reading project
docs on every session.

---

## Deliverables

### Claude Skill Files (CLAUDE.md)
- `CLAUDE.md` (root) — master project rules, critical path, guardrail summary
- `engines/CLAUDE.md` — engine directory map, template, compliance checklist
- `engines/common/CLAUDE.md` — shared utility reference card
- `engines/fundamentals/CLAUDE.md` — Phase 4 spec, classification edge cases
- `engines/acquisition/CLAUDE.md` — data download rules, recovery patterns
- `engines/intelligence/CLAUDE.md` — planned intelligence engine specs
- `engines/foundation/CLAUDE.md` — index/constituent management
- `data/CLAUDE.md` — canonical data paths, lifecycle, edge cases
- `fetchers/CLAUDE.md` — legacy context, migration roadmap
- `docs/CLAUDE.md` — documentation governance, ADR creation rules
- `alerts/CLAUDE.md` — Telegram delivery rules
- `sheets/CLAUDE.md` — Google Sheets integration rules
- `storage/CLAUDE.md` — atomic write patterns, storage managers

### Governance Documents
- `docs/CLAUDE_MASTER_DEV_GUIDE.md` — 16-section master reference
- `docs/governance/GUARDRAILS.md` — 12-section, 55 rules, full edge case registry

### Technical Debt Catalogued
- 5 files marked for removal (legacy/backup/stubs)
- Data path discrepancy documented (`data/NSE Data/` → `data/NSE/`)
- 8 known issues catalogued with root causes

---

# Version 1.0

Documentation Foundation Release

Date:

2026-06-03

Status:

Completed

---

## Summary

Established complete project governance and documentation framework.

The project evolved from an informal FII/DII analytics initiative into a formally documented Capital Flow Intelligence Platform.

---

## Deliverables

### Governance Layer

Completed:

PROJECT_SCOPE.md

MASTER_ROADMAP.md

MODULE_REGISTRY.md

MASTER_CHECKLIST.md

DEVELOPMENT_GOVERNANCE.md

RESEARCH_PIPELINE.md

CHANGELOG.md

---

### Architecture Layer

Completed:

MASTER_ARCHITECTURE.md

DATA_ARCHITECTURE.md

AI_ARCHITECTURE.md

GUI_ARCHITECTURE.md

BROKER_ARCHITECTURE.md

---

### Module Documentation

Completed:

INSTITUTIONAL_INTELLIGENCE.md

SECTOR_INTELLIGENCE.md

THEME_INTELLIGENCE.md

STOCK_INTELLIGENCE.md

FUNDAMENTAL_INTELLIGENCE.md

AI_PLATFORM.md

GUI_PLATFORM.md

EXECUTION_PLATFORM.md

---

### Architecture Decision Records

Completed:

ADR-001 Raw Data Never Modified

ADR-002 NSE Data Structure

ADR-003 On Demand Cache

ADR-004 Listing Date Aware Processing

ADR-005 Nselib First Policy

ADR-006 Gross Flow Preservation

ADR-007 Sector Theme Stock Capital Flow Model

ADR-008 Cache Maintenance Strategy

ADR-009 Intelligence Layer Separation

ADR-010 AI First User Experience

ADR-011 Infographic First Visualization

ADR-012 Research Before Development

ADR-013 Broker Independence Architecture

ADR-014 Module Driven Development

ADR-015 Documentation Mandatory Before Release

---

# Strategic Architecture Update

Date:

2026-06-03

Status:

Completed

---

## Change

Project positioning updated from:

```text
FII/DII Intelligence Platform
```

to:

```text
Capital Flow Intelligence Platform
```

---

## Reason

The platform is no longer focused solely on institutional activity.

The platform now tracks market participation across:

FII

DII

PRO

CLIENT

and analyzes how capital moves through the broader market ecosystem.

---

## New Strategic Framework

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
    ↓
Fundamental Validation
    ↓
Portfolio
    ↓
Execution
```

This framework now serves as the primary architectural model for all future development.

---

# Participant Intelligence Initiative

Date:

2026-06-03

Status:

Approved

---

## Objective

Expand Institutional Intelligence into Participant Intelligence.

---

## Participants

FII

DII

PRO

CLIENT

---

## Planned Outputs

Participation Scores

Conviction Scores

Divergence Scores

Smart Money Scores

Retail Sentiment Scores

Participant Reports

Participant Dashboards

Participant Infographics

---

## Planned Engines

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

## Planned AI Capability

AI Participant Analyst

---

# Institutional Intelligence Milestone

Date:

2026-06-01

Status:

Completed

---

## Achievement

Institutional historical dataset integrity reached:

100%

---

## Results

Coverage:

100%

Integrity:

100%

Missing Dates:

0

---

## Deliverables

Historical Engine

Backfill Engine

Integrity Engine

Regime Engine

Trend Engine Foundation

---

# Data Architecture Milestone

Date:

2026-06-02

Status:

Completed

---

## Achievement

Long-term data architecture finalized.

---

## Decisions

Year-wise Bhavcopy Storage

On-Demand Cache Generation

Listing Date Aware Processing

Raw Data Preservation

Cache Maintenance Strategy

---

## Final Structure

```text
data/

NSE Data/

    bhavcopy/

        equity/

            <YEAR>/

                bhavcopy_YYYYMMDD.csv

        f&o/

            <YEAR>/

                fo_YYYYMMDD.csv

    equity_master/

    corporate_actions/

    shareholding/

    results/

    announcements/

cache/

    stock_history/
```

---

# Research Governance Milestone

Date:

2026-06-03

Status:

Completed

---

## Achievement

Research-first development process adopted.

---

## Framework

```text
Idea
    ↓
Research
    ↓
Validation
    ↓
Architecture
    ↓
Development
    ↓
Testing
    ↓
Documentation
    ↓
Release
```

---

## Result

All future major development initiatives must follow the research pipeline.

---

# User Experience Milestone

Date:

2026-06-03

Status:

Completed

---

## Achievement

AI-first and infographic-first platform philosophy adopted.

---

## Principles

AI First User Experience

Infographic First Visualization

Three Second Understanding Rule

Progressive Disclosure

Broker Independence

Human Approval Required

---

# Current Development State

Date:

2026-06-03

---

## Completed

Governance Framework

Architecture Framework

Documentation Framework

Institutional Intelligence Foundation

Data Architecture

Research Framework

---

## Active Development

Sector Intelligence Expansion

Theme Intelligence Expansion

Participant Intelligence Planning

---

## Planned

Stock Intelligence

Fundamental Intelligence

AI Platform Expansion

GUI Platform

Execution Platform

Research Platform

Commercial Platform

---

# Next Milestone

Version 1.1

Participant Intelligence Foundation

---

## Planned Deliverables

ADR-016 Participant Intelligence Framework

PARTICIPANT_INTELLIGENCE.md

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

## Expected Outcome

Transition from:

Institutional Intelligence

to

Participant Intelligence

as the primary capital flow analysis layer.

---

# Long-Term Vision

Build the world's most comprehensive Capital Flow Intelligence Platform capable of:

Tracking Participant Behavior

↓

Detecting Capital Flow

↓

Identifying Opportunities

↓

Explaining Opportunities

↓

Managing Portfolios

↓

Executing Trades

↓

Monitoring Outcomes

through a unified AI-powered investment operating system.

---

# Current Project Status

Overall Estimated Completion:

25%

---

## Strategic Focus

Current Priority:

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

capital flow discovery and opportunity identification.

This remains the central objective of the platform.

## Version 1.3

### Architecture

- Added ADR-018 Market Data Reliability Framework

### Key Decisions

- Runtime data integrity validation
- Self-healing data architecture
- Automated incremental backup strategy
- Weekly recovery point framework
- Secondary backup repository requirement
- Disaster recovery hierarchy
- Metadata-only registry architecture
