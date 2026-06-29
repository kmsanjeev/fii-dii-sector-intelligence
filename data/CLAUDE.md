# DATA DIRECTORY — CLAUDE CONTEXT

## IRON RULE (ADR-001)
Raw data under `data/NSE/bhavcopy/`, `data/bhavcopy/`, and `data/NSE/corporate/`
is the PERMANENT SOURCE OF TRUTH.
**It may never be modified, overwritten, or recalculated.**
Engines read from raw data; engines write to cache/, intelligence/, or NSE/ structured dirs.

## CANONICAL DIRECTORY MAP

```
data/
│
├── NSE/                                 ← PRIMARY structured data store
│   ├── bhavcopy/
│   │   ├── equity/YYYY/                 ← bhavcopy_YYYYMMDD.csv  (config: NSE_EQUITY_BHAVCOPY_DIR)
│   │   └── fno/YYYY/                    ← fno_bhavcopy_YYYYMMDD.csv
│   ├── equity_master/                   ← equity_master.csv, company_fundamentals_master.csv
│   │   └── reports/
│   ├── indices/                         ← index constituent CSVs (139 indices)
│   │   └── reports/
│   ├── corporate_actions/               ← Phase 5 target (empty now)
│   ├── results/                         ← Phase 4 target (empty now)
│   ├── shareholding/                    ← Phase 4 target (empty now)
│   └── announcements/                   ← Phase 5 target (empty now)
│
├── bhavcopy/                            ← LEGACY raw bhavcopy (1995–2026)
│   ├── equity/1995/ … equity/2026/      ← Old import location; read by legacy engines
│   └── fno/2025/, fno/2026/
│   ⚠ New engines must NOT write here. Read-only legacy path.
│
├── BSE/                                 ← Future (no engines yet, do not build)
│   ├── bhavcopy/equity/
│   └── bhavcopy/fno/
│
├── aggregated/                          ← Experimental (no engines; investigate before use)
│
├── cache/                               ← DISPOSABLE — rebuild anytime (config: CACHE_DIR)
│   ├── stock_history/                   ← Per-symbol OHLCV CSVs (config: STOCK_HISTORY_CACHE)
│   └── reports/
│
├── historical/                          ← Derived historical datasets
│   ├── fii_dii/
│   ├── institutional/                   ← institutional_positioning_history.csv
│   ├── sectors/
│   ├── stocks/
│   └── thematic/
│
├── intelligence/                        ← Derived intelligence outputs (rebuildable)
│   └── history/
│
├── reference/                           ← Reference tables (semi-permanent)
│   └── mapping/                         ← sector maps, theme maps, industry_master.csv (planned)
│       └── nse_holidays.csv             ← config: NSE_HOLIDAY_FILE
│
└── logs/                                ← Data pipeline logs
```

## DATA LIFECYCLE POLICY
| Layer | Location | Retention | Rebuild |
|-------|----------|-----------|---------|
| Raw Data | `data/NSE/bhavcopy/`, `data/bhavcopy/` | PERMANENT | Never |
| Cache | `data/cache/` | Temporary | Anytime |
| Intelligence | `data/intelligence/` | Keep | Anytime |
| Historical | `data/historical/` | Keep | Anytime |
| Reports | (future `data/reports/`) | Archive | Never |

## CACHE POLICY (ADR-003 + ADR-008)
- Cache is generated ON DEMAND — never pre-build for all 4500+ symbols
- Workflow: `Request → Check cache → Build if missing → Return`
- Heavy cache builds: after market hours (16:00+ IST) or weekends only
- Never treat cache as source of truth; raw data wins on conflict

## LISTING-DATE RULE (ADR-004)
Before processing any symbol, look up its `listing_date` from equity_master.
Only process bhavcopy files dated ON OR AFTER the listing date.
```python
# Example
listing = pd.to_datetime(equity_master.loc[symbol, "listing_date"])
files = [f for f in all_files if extract_date(f) >= listing.date()]
```

## PERFORMANCE DESIGN TARGETS
- Universe: 4500+ listed companies (design for this, even if current set is 2123)
- History: 30+ years of bhavcopy data
- On-demand cache for stock history (never full-universe pre-build)
- Full-universe scans: weekends only

## INSTITUTIONAL DATA EDGE CASES
| Edge Case | Rule |
|-----------|------|
| T+1 data lag | FII/DII cash data may arrive next day. Wait until 18:00 IST before marking as missing. |
| PRO/CLIENT availability | Only in F&O segment. No cash market PRO/CLIENT breakdown exists. |
| FII Derivatives data | Separate report from participant OI — download independently. |
| Pre-2016 history | Institutional OI/Volume participant breakdown not available before ~2016. Do not backfill. |
| Gross flows (ADR-006) | Always store BUY + SELL + NET separately. Never store only NET. |

## TRADING CALENDAR EDGE CASES
| Scenario | How Data Behaves |
|----------|-----------------|
| Saturday/Sunday | No bhavcopy — not a missing date |
| NSE national holiday | No bhavcopy — check nse_holidays.csv |
| Market circuit breaker | Partial day — bhavcopy exists (may have low/zero volume) |
| Mahurat trading (Diwali) | 1-hour session — bhavcopy exists, very low volume |
| F&O expiry (last Thu) | Full day — expect higher volume, not anomalous |
| Budget day (Feb 1) | Full day — flag analysis period, do not skip |
| Index rebalancing date | Bhavcopy unaffected — but index constituent files change |

## UPCOMING DATA EXPANSIONS (build order follows critical path)
1. `data/NSE/equity_master/company_fundamentals_master.csv` ← Phase 4 Step 1
2. `data/reference/mapping/industry_master.csv` ← Phase 4 Step 2
3. `data/NSE/results/` ← Phase 4 (financial results)
4. `data/NSE/shareholding/` ← Phase 4 (shareholding patterns)
5. `data/NSE/announcements/` ← Phase 5
6. `data/NSE/corporate_actions/` ← Phase 5
7. `data/NSE/corporate/call_recordings/` ← Phase 6
8. `data/NSE/corporate/transcripts/` ← Phase 6
9. `data/signals/` ← Phase 8 (watchlists, trade candidates)
10. `data/reports/` ← Phase 8+

## BACKUP POLICY (ADR-019)
- Weekly incremental backup: Friday 23:59 IST
- Recovery order: Raw Data → Backup → API Re-download
- Every acquisition engine must support re-download of any missing date range
