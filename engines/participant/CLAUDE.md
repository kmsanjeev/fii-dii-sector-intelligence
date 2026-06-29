# ENGINES/PARTICIPANT — CLAUDE CONTEXT

## PURPOSE
Participant Intelligence Layer — Phase 5 per ADR-016.
Tracks capital flow by participant category (FII, DII, PRO, CLIENT).
This is the foundational intelligence layer of the Capital Flow cascade:
Participant → Sector → Theme → Stock.

## BUILD SEQUENCE

| Phase | Engine | Status |
|-------|--------|--------|
| 5A | participant_acquisition_engine.py | ✅ Done |
| 5B | participant_flow_engine.py | ✅ Done |
| 5C | participant_intelligence_engine.py | ✅ Done |

## DATA SOURCES (nselib)

| Function | Data | Granularity |
|----------|------|-------------|
| `derivatives.participant_wise_open_interest(date)` | F&O OI by FII/DII/PRO/CLIENT | Daily snapshot |
| `derivatives.participant_wise_trading_volume(date)` | F&O Volume by FII/DII/PRO/CLIENT | Daily flow |
| `derivatives.fii_derivatives_statistics(date)` | FII futures buy/sell contracts | Daily |
| `capital_market.category_turnover_cash(date)` | Cash market flows by FPI/MF/Insurance/Retail | Daily flow |

## DATA FILES

| File | Path | Description |
|------|------|-------------|
| institutional_positioning_history.csv | `data/historical/institutional/` | F&O OI + Volume 2016–present |
| cash_market_flows_history.csv | `data/historical/institutional/` | Cash market flows 2024–present |
| participant_flow_scores.csv | `data/intelligence/` | Rolling scores + normalized scores |
| participant_intelligence.csv | `data/intelligence/` | Conviction, divergence, smart money |

## PARTICIPANT DEFINITIONS

| Label | nselib "Client Type" | Meaning |
|-------|---------------------|---------|
| FII | "FII" | Foreign Institutional Investors |
| DII | "DII" | Domestic Institutional Investors (MF + Insurance) |
| PRO | "Pro" | Proprietary / Professional traders |
| CLIENT | "Client" | Retail / non-institutional |

## F&O NET POSITION FORMULA
Net futures position = Future_Index_Long + Future_Stock_Long - Future_Index_Short - Future_Stock_Short
(Options excluded — futures give cleaner directional signal)

## KNOWN NSE COLUMN QUIRKS
- nselib returns column names with trailing spaces: 'Future Stock Short       ', 'Total Long Contracts      '
- Always strip column names before processing: `df.columns = df.columns.str.strip()`

## KEY GUARDRAILS
- G-A-01: 1s rate limit between API calls
- G-A-02: 3 retries with exponential backoff (NSE often returns empty for holidays)
- G-A-03: Failed dates → recovery_queue
- G-D-02: Atomic writes (.tmp → shutil.move)
- G-D-03: No empty DataFrame writes
- Pre-2016: F&O participant data unavailable — do not backfill before 2016-01-01
