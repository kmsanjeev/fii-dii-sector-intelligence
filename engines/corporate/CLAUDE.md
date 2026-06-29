# ENGINES/CORPORATE — CLAUDE CONTEXT

## PURPOSE
Corporate Intelligence Layer — Phase 7 per ADR-020.
Tracks institutional conviction at the stock level via block/bulk deals,
upcoming catalysts via the event calendar, and corporate confidence signals
via classified corporate actions.

## BUILD SEQUENCE

| Phase | Engine | Status |
|-------|--------|--------|
| 7A | block_bulk_deal_engine.py | ✅ Done |
| 7B | corporate_event_calendar_engine.py | ✅ Done |
| 7C | corporate_action_intelligence_engine.py | ✅ Done |

## DATA SOURCES (nselib.capital_market)

| Function | Data | Granularity |
|----------|------|-------------|
| `block_deals_data(period='1M')` | Block deals: qty ≥ 5L shares or ≥ 5Cr value | Daily |
| `bulk_deal_data(period='1M')` | Bulk deals: qty ≥ 0.5% of equity | Daily |
| `event_calendar_for_equity(from_date, to_date)` | Board meetings, results, AGM dates | Per announcement |
| `corporate_actions_for_equity(period='6M')` | Dividends, bonus, splits, buybacks | Per action |

## DATA FILES

| File | Path | Description |
|------|------|-------------|
| block_bulk_deals.csv | `data/intelligence/` | Raw block/bulk deal history (incremental) |
| institutional_deal_signals.csv | `data/intelligence/` | Per-symbol 30D net institutional flow |
| event_calendar.csv | `data/intelligence/` | Board meeting + results history |
| upcoming_catalysts.csv | `data/intelligence/` | Next 60D events sorted by flow+catalyst priority |
| corporate_action_signals.csv | `data/intelligence/` | Classified corporate actions 1999-2026 |
| corporate_confidence_scores.csv | `data/intelligence/` | Per-symbol rolling 12M corporate confidence |

## PARTICIPANT CLASSIFICATION (block/bulk deals)
Client names are mapped to participant categories by keyword matching:
- FII: Goldman Sachs, Morgan Stanley, Barclays, Nomura, UBS, Citibank, JP Morgan, Deutsche, BNP, HSBC, Societe
- MF/DII: HDFC MF, ICICI Prudential, SBI MF, Nippon, UTI, Kotak MF, Axis MF, DSP, Franklin, Mirae, Motilal
- INSURANCE: LIC, HDFC Life, SBI Life, Bajaj Allianz, Max Life, ICICI Lombard
- PROMOTER: detected by name matching with company/promoter disclosures (heuristic)
- RETAIL: residual

## CORPORATE ACTION TYPES + CONFIDENCE WEIGHTS
| Type | Confidence Weight | Signal |
|------|-------------------|--------|
| BUYBACK | +3 | Management very confident — buying own stock |
| BONUS | +2 | Management confident — rewarding shareholders |
| SPLIT | +1 | Management expects retail interest |
| DIVIDEND | +0.5 | Distributing cash, may limit capex |
| RIGHTS | -0.5 | Dilution — management needs capital |
| MERGER | 0 | Neutral — outcome depends on deal |
| AGM/EGM | 0 | Routine |

## KEY GUARDRAILS
- G-A-01: 1s rate limit between API calls
- G-A-02: 3 retries with exponential backoff
- G-A-03: Failed items → recovery queue
- G-D-02: Atomic writes (.tmp → shutil.move)
- G-D-03: No empty DataFrame writes
- G-S-01: EQ series filter on all corporate action data
