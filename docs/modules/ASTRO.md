# ASTRO INTELLIGENCE (AstroFinance / Vedic Layer)
## Capital Flow Intelligence Platform | Updated 2026-07-15

---

# Module Overview

A secondary, experimental intelligence layer applying Vedic/Parashari
astrology and W.D. Gann price-time analysis to the market. Two genuinely
different signal types exist under the "Astro" name and must not be
conflated:

1. **Sector transit signal** (`AstroEngine`) — a daily mundane-astrology
   reading, identical for every stock sharing a sector. This is what the
   "Astro" gauge in the 8-score stock header shows.
2. **Stock/personal natal chart** (`KundliEngine` + `kundli_calculator.py`)
   — a genuine per-entity chart, cast for the stock's own listing moment
   (mundane/foundation-chart technique) or a person's actual birth data.
   Surfaced only in the separate Kundli card, not the 8-gauge header.

Retroactively documented and correctness-fixed under ADR-022
(Phase ASTRO-FIX, 2026-07-15) — see that ADR for the full defect list and
roadmap. This doc describes the module as it stands after that fix.

---

# Completion Status: 70% (core engines complete; see Known Gaps)

---

# Engines

## AstroEngine — engines/intelligence/astro_engine.py

Daily sector-level mundane transit signal for all 31 NSE sectors.

Method: Swiss Ephemeris `FLG_SIDEREAL` (Lahiri ayanamsha, True Node for
Rahu/Ketu) — fixed under ADR-022 from a prior PyEphem-tropical-labeled-
as-sidereal bug. Planet dignity (exaltation/debilitation/own-sign),
planet-pair aspects with orbs, Moon phase, eclipse proximity, and a
hardcoded planet-to-sector rulership table (`SECTOR_RULERS`) drive a
`BUY/HOLD/CAUTION/EXIT/AVOID` action per sector.

Knowledge sources cited in the engine's own docstring: A Trader's Guide to
Financial Astrology (Pesavento & Smoleny, 2015), Financial Astrology
Almanac 2023, Stock Market Astrology (Banerjee, 2009 — Indian/NSE
sector-planet mapping), Planetary Effects to Financial Market.

Output: `data/intelligence/astro_signals.csv` (31 rows, regenerated
daily) + `data/intelligence/market_astro_context.json` (market-wide
pulse, including the exact Lahiri ayanamsha value used, for auditability).

Scheduled: `daily_refresh.py` -> `AF_astro_engine` (60s budget).

## KundliEngine — engines/intelligence/kundli_engine.py

Canonical Vedic natal-chart calculator. Used directly for stock/company
and country charts, and as the calculation core for personal charts
(`kundli_calculator.py` delegates to it — see below).

Method: Swiss Ephemeris, exact Lahiri (Chitrapaksha) ayanamsha via
`swe.get_ayanamsa_ut()`, Whole Sign houses (Parashari standard), True
Node. 12 divisional charts (D1-D12, D16, D20, D30, D60) computed but only
D1 currently feeds the financial score (see Known Gaps). 3-level
Vimshottari Dasha (Mahadasha/Antardasha/Pratyantardasha). 8 classical
yogas detected (Gaja Kesari, Dhana, Raja, Viparita Raja, Kemdrum, Neecha
Bhanga, Kala Sarpa, Parivartana), each mapped to a fixed financial-score
delta.

**Stock charts**: `compute_stock(symbol, listing_date, exchange='NSE')`
treats the stock's NSE/BSE listing date + **10:00 IST** + the exchange's
own city coordinates (Mumbai, 18.934N/72.8296E) as the entity's "birth" —
a mundane/foundation-chart technique, the same family as national-
independence charts. The 10:00 time is **not** an arbitrary guess: it is
NSE's SEBI-mandated commencement time for normal trading on every new
listing, following the mandatory Special Pre-Open Session (09:00-09:45
IST price discovery) — confirmed by spike research under ADR-022. Known
exception: a rare ceremonial "Muhurat listing" for a marquee IPO has its
own announced timing; no per-symbol override exists for this yet.

Financial houses are given a bespoke corporate reinterpretation (2H
balance sheet, 5H speculation/derivatives, 8H sudden events/M&A, 10H
management/reputation, 11H revenue/profits) rather than classical human
significations — only 5 of 12 houses currently feed the score (see Known
Gaps: no full Bhava Phal).

**Human/country charts**: `compute_human(name, date_str, time_str, lat,
lon, tz_offset)` and `compute_country(country_name)` (hardcoded inception
charts for India, USA, UK, China, Japan, Germany, Pakistan, Russia,
France, Brazil).

Outputs: `data/intelligence/kundli_signals.csv` (2,053 NSE symbols,
bulk-run 2026-07-15) + `data/intelligence/kundli/{symbol}_kundli.json`
per-symbol cache. Scheduled: `daily_refresh.py` -> `KU_kundli_engine`
(180s budget).

## GannEngine — engines/intelligence/gann_engine.py

W.D. Gann price/time tools: Square of 9 (`degree(N) = MOD(SQRT(N)*180 -
225, 360)`), Gann Fan angles (1x1...4x1), planetary price lines
(sidereal longitude read directly as a price number), solar time cycles.
Numerology built on planetary longitude, not astrology proper — kept in
this module because it shares the Swiss Ephemeris sidereal core and
consumes `kundli_signals.csv`.

Depends on `kundli_signals.csv` (must run after KundliEngine) and
`price_momentum.csv` (current prices). Output:
`data/intelligence/gann_signals.csv` (2,052 rows). Scheduled:
`daily_refresh.py` -> `KU_gann_engine` (60s budget).

## KundliInterpretator — engines/intelligence/kundli_interpretator.py

Narrative layer: takes a `KundliEngine` chart (+ optional `GannEngine`
output) and produces bullish/bearish factor lists, a re-derived
BUY...AVOID signal, and an optional 2-3 sentence LLM narrative via
`engines/common/llm_client.py`. Feeds the "Report" tab of `KundliCard.tsx`.

## kundli_calculator.py — engines/ai/chatbot/tools/kundli_calculator.py

Personal Kundli for the chat tool (`generate_personal_kundli`). Since
Phase ASTRO-FIX, all position/Ascendant/ayanamsha math delegates to a
module-level `KundliEngine` instance — this file's own PyEphem +
linear-ayanamsha-approximation pipeline was removed. What remains unique
to this file: Panchang (5-limb Vedic almanac), dosha detection (Manglik,
Shani, Guru-Chandal, Surya-Chandal, Shani-Chandra), Lal Kitab remedies
(a separate, non-Parashari folk-astrology system used only for remedies),
functional-nature/yogakaraka-by-lagna analysis, city geocoding (built-in
~90-city dict -> learned cache -> Nominatim/OpenStreetMap), and the full
pre-formatted text report the chatbot outputs verbatim. Life-area
narratives (career/love/education/finance) delegate further to
`kundli_interpreter.py` (`generate_life_readings`) and
`kundli_life_guide.py` (`build_life_guide` — good/bad period timeline,
Sade Sati check).

---

# Chat/RAG Integration

`intent_router.py` classifies `ASTRO` (sector transit questions) and
`KUNDLI` (personal chart questions, with a hard override: any message
containing a date pattern + place-like keyword force-routes to KUNDLI).
`tool_registry.py` exposes `get_astro_signal(sector)` and
`generate_personal_kundli(...)` as LLM-callable tools.

`faiss_indexer.py` declares `ASTRO` as a RAG domain, but it is currently
**empty**: the prior 3,173-vector index was orphaned (source PDFs
unavailable) and has been retired to `faiss_ASTRO.index.retired` (not
deleted — reversible if the PDFs are located). Separately,
`retriever.py`'s `DOMAIN_KEYWORDS` dict never routes queries to `ASTRO`
regardless of index state — a fix needed alongside any future
re-ingestion.

---

# Data Paths

```
data/intelligence/astro_signals.csv               31 sectors, daily
data/intelligence/market_astro_context.json        market pulse + ayanamsha used
data/intelligence/kundli_signals.csv               2053 NSE stocks
data/intelligence/kundli/{symbol}_kundli.json       per-symbol chart cache
data/intelligence/gann_signals.csv                 2052 stocks
data/intelligence/rag_knowledge/faiss/faiss_ASTRO.index.retired   orphaned, retired
```

---

# Known Gaps (see ADR-022 for the full roadmap)

- No full Bhava Phal (12-house) analysis for stocks — only 5 houses feed
  the score; a rich planet-in-house/house-lord-in-house table exists
  (`kundli_life_guide.py`) but only on the personal-chart path.
- No Ashtakavarga (bindu house-strength) or Shadbala (6-fold planetary
  strength) anywhere — yogas and dasha periods get a fixed score delta
  regardless of how strong the planets involved actually are.
- No Varshphal (annual/Tajika chart) for period-bound predictions.
- **Not wired into `trade_conviction_engine.py`** — the astrology signal
  currently has zero influence on the platform's actual recommendations.
- No signal-efficacy validation (IC/decile/hit-rate) — unlike every other
  factor in `conviction_screener.csv`, astrology has never been backfilled
  into the SA-1 `score_snapshot` archive.
- `astro_engine.py`'s `SECTOR_RULERS` includes Uranus/Neptune rulership
  for some sectors (e.g. Neptune -> Oil & Gas) — a Western financial-
  astrology trope with no classical Vedic (9-graha) citation.
- No North/South Indian diamond/grid chart renderer — `ReportPage.tsx`
  only draws a Western-style circular zodiac wheel.

---

# Dependencies

`pyswisseph==2.10.3.2`, `ephem==4.2.1` (both in `requirements.txt` since
Phase ASTRO-FIX). `data/NSE/equity_master/equity_master.csv` (listing
dates), `data/intelligence/price_momentum.csv` (Gann current prices).

---

# Architecture Reference

docs/decisions/ADR-022-AstroFinance-Vedic-Intelligence-Layer.md
