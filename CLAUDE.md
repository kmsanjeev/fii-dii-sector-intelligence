# CAPITAL FLOW INTELLIGENCE PLATFORM — CLAUDE CONTEXT

## IDENTITY
**Repo:** fii-dii-sector-intelligence | **Domain:** India institutional market intelligence
**Mission:** Identify capital flow (Participant → Sector → Theme → Stock) before broad market recognition.
This is a **decision intelligence platform**, not a screener.

## AI OPERATING MODE
Act as: Senior System Architect + Lead Python Developer + Quant Research Engineer.
Never act as: tutor, explainer, or generic assistant.

## MANDATORY CODING RULES (NON-NEGOTIABLE)
1. Deliver COMPLETE copy-paste-ready files — never partial snippets or patches
2. Provide `git add / git commit / git push` commands after every code change
3. Freeze architecture with user before writing any code
4. Use incremental processing with recovery mechanisms
5. Handle 4500+ symbol universe in every engine — never assume small dataset
6. Listing-date-aware processing: never process data before a stock's listing date
7. Raw data is IMMUTABLE — never modify files under `data/bhavcopy/` or `data/NSE/`
8. Cache is DISPOSABLE — never treat it as source of truth

## DATA ACQUISITION PRIORITY (always enforce)
1. nselib (primary)  2. NSE API  3. Alternative sources  4. yFinance (last resort)

## CANONICAL DATA PATHS (from engines/common/config.py — authoritative)
```
data/
├── NSE/                          ← Structured NSE data (USE THIS)
│   ├── bhavcopy/equity/YYYY/     ← Target for imported bhavcopy (config: NSE_EQUITY_BHAVCOPY_DIR)
│   ├── bhavcopy/fno/YYYY/
│   ├── equity_master/            ← equity_master.csv + company_fundamentals_master.csv
│   ├── indices/                  ← index constituent CSVs
│   ├── corporate_actions/        ← Phase 5, currently empty
│   ├── results/                  ← Phase 4, currently empty
│   └── shareholding/             ← Phase 4, currently empty
├── bhavcopy/equity/1995-2026/    ← OLD location, raw imported data (legacy)
│                                    ⚠ config now points to data/NSE/bhavcopy/ instead
├── BSE/                          ← Future, no engines yet
├── cache/stock_history/          ← Per-symbol OHLCV (config: STOCK_HISTORY_CACHE)
├── historical/institutional/     ← institutional_positioning_history.csv
├── intelligence/                 ← Derived outputs (rebuildable)
└── reference/mapping/            ← Sector/theme mapping tables
```
**WARNING:** `data/NSE Data/` (with space) does NOT exist — fix any engine referencing it.
**WARNING:** `data/bhavcopy/` is the OLD location. New engines write to `data/NSE/bhavcopy/` via config constants.

## PHASE STATUS (June 2026)
| Phase | Name                    | Status     |
|-------|-------------------------|------------|
| 1     | Foundation Layer        | ✅ 100%   |
| 2     | Classification          | 🟡 70% engine / 37% symbol coverage |
| 3     | Index Intelligence      | ✅ 100%   |
| 4     | Fundamentals Layer      | 🔴 0% — **CRITICAL BOTTLENECK** |
| 5     | Corporate Intelligence  | ⚪ blocked |
| 6     | Management Intelligence | ⚪ blocked |
| 7     | Institutional Intel     | ✅ 100%   |
| 8     | Bull Run Discovery      | 🟡 40%    |

**MASTER RULE: Do NOT build new intelligence engines until `company_fundamentals_master_engine.py` is complete.**

## CRITICAL PATH (current)
```
1. Company Fundamentals Master Engine     → engines/fundamentals/company_fundamentals_master_engine.py
2. Industry Master Engine                 → engines/fundamentals/industry_master_engine.py
3. NSE Constituents Auto Downloader       → engines/foundation/nse_constituents_engine_v1.py (expand)
4. Classification Engine V4 completion   → engines/fundamentals/classification_engine_v4.py
5. Participant Intelligence Layer         → engines/participant/ (new dir, per ADR-016)
6. Sector Rotation + Capital Flow Engines
7. Corporate Intelligence Layer           → per ADR-020
8. Management Intelligence Layer          → per ADR-020
9. Bull Run Probability Engine
```

## FILES MARKED FOR REMOVAL (confirm before deleting)
- `engines/index_intelligence_engine_v1_backup.py` — backup copy, redundant
- `engines/intelligence/index_intelligence_engine_v2.py` — 80-line stub
- `engines/intelligence/leadership_persistence_engine_v2.py` — 30-line stub
- `engines/fundamentals/security_master_engine.py` — superseded by v2
- `engines/classification_engine.py` — v1, superseded by v4

## KEY KNOWN BUGS
- ADANIPORTS classifies as AEROSPACE (wrong) — should be LOGISTICS/PORTS
  Root cause: Industry Master missing. Fix: complete industry_master_engine.py first.

## MANDATORY GUARDRAILS (enforce in every engine)
Full spec: `docs/governance/GUARDRAILS.md`

| ID | Rule | How |
|----|------|-----|
| G-D-01 | Raw data IMMUTABLE | Raise if target path exists before writing raw file |
| G-D-02 | Atomic writes | Write to `.tmp`, then `shutil.move()` — never direct write |
| G-D-03 | No empty DataFrames | Check `df.empty` before any file write |
| G-D-04 | Schema validation | Validate required columns + nulls before saving |
| G-D-05 | No duplicate dates | `safe_append()` — deduplicate by date before concat |
| G-A-01 | Rate limiting | `time.sleep(cfg.API_DELAY)` between every nselib call |
| G-A-02 | Retry + backoff | 3 retries with exponential delay on every API call |
| G-A-03 | Recovery queue | Write failed items to `NSE/recovery_queue.csv` |
| G-A-04 | Market hours guard | No heavy batch ops during 09:15–15:30 IST |
| G-S-01 | EQ series only | `df = df[df["series"] == "EQ"]` at universe entry |
| G-S-02 | Listing date aware | Filter files by listing_date before reading |
| G-S-04 | Universe size check | Raise if equity_master has < 1800 EQ symbols |
| G-C-01 | No null sectors | `fillna("UNCATEGORIZED")` then log to review queue |
| G-C-02 | Manual override frozen | Always apply manual_override.csv last, immutably |
| G-P-01 | No negative prices | Drop rows where Open/High/Low/Close ≤ 0 |
| G-P-02 | OHLC consistency | High ≥ Low ≥ 0; High ≥ Open/Close |
| G-I-01 | Min 5 sessions | Return `None` (not 0) if data < 5 trading days |
| G-I-04 | NaN handling | Never `fillna(0)` on price/volume/flow — masks real gaps |
| G-SYS-01 | Env var guard | Check all required env vars at module startup |
| G-SYS-02 | Git security | No data CSVs, no credentials ever committed |

## KEY EDGE CASES (quick reference)
- **Weekend dates:** Not missing — NSE closed Sat/Sun. Skip silently.
- **Mahurat trading:** 1-hour Diwali session — real data, low volume, process normally
- **Circuit breaker halt:** Partial day — bhavcopy still exists, not a gap
- **Zero volume day:** Log warning, do not drop — may be valid circuit limit hit
- **F&O expiry (last Thu):** Higher volume expected — not anomalous
- **ISIN duplicates (merger):** Keep active symbol, flag retired one as DELISTED
- **Conglomerates:** Use primary revenue segment for classification (ITC → FMCG)
- **T+1 institutional lag:** FII/DII data may arrive next day — wait until 18:00 IST before flagging missing
- **Pre-2016 OI data:** Not available — do not backfill participant OI before 2016
- **ETFs/REITs in bhavcopy:** Filter out using EXCLUDE_KEYWORDS before classification

## ARCHITECTURE REFERENCE
Full guide: `docs/CLAUDE_MASTER_DEV_GUIDE.md` (16 sections)
Guardrails: `docs/governance/GUARDRAILS.md` (12 sections, 55 rules)
Module specs: `docs/modules/`
ADR decisions: `docs/decisions/`
