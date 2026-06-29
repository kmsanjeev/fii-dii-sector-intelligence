# ENGINES/FOUNDATION — CLAUDE CONTEXT

## PURPOSE
Foundation engines that build and maintain the static reference datasets the entire platform depends on.
These run infrequently (weekly or on-demand) and their outputs are prerequisites for all other engines.

## ACTIVE ENGINES
| File | Status | Purpose |
|------|--------|---------|
| `nse_constituents_engine_v1.py` | ✅ Active | Download index constituent lists for all 139 NSE indices |

## NSE CONSTITUENTS ENGINE — CURRENT STATE
The engine downloads constituent CSV files for NSE indices.
**Current limitation:** Manual download required for some index files.

**Enhancement needed (Priority 3 on critical path):**
Auto-download all 139 index constituent files using nselib/NSE API.
Target indices:
- Nifty Total Market (broadest universe)
- Nifty 500, Nifty 200, Nifty 100, Nifty 50
- All 29 Sector indices (Nifty IT, Banking, Pharma, etc.)
- All 18 Theme indices (Nifty India Defence, EV, etc.)

Output location: `data/NSE/indices/`
Naming: `<index_name>_constituents.csv`

## PLANNED FOUNDATION ENGINES
```
# Phase 4
nse_equity_master_builder.py      ← Build equity_master.csv from nselib
holiday_master_engine.py          ← Build NSE holiday master (replace utils/trading_calendar.py)

# Phase 5
index_rebalancing_tracker.py      ← Track index constituent changes over time
```

## INDEX UNIVERSE (as of June 2026)
- Total: 139 NSE indices tracked
- Sector indices: 29
- Theme indices: 18
- Broad market: Nifty Total Market, Nifty 500, Nifty 200, Nifty 100, Nifty 50, Nifty Next 50
- All others: Strategy, Factor, Fixed Income indices

Index data location: `data/NSE/indices/`
Reports: `data/NSE/indices/reports/`
Full index list: `data/NSE/indices/reports/all_indices_list.txt`
