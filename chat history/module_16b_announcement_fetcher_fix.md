# Session Log: Phase 16B Fix -- AnnouncementFetcher

**Date:** 2026-06-30
**Scope:** Fix announcement_fetcher.py to use correct nselib API

---

## Problem

`announcement_fetcher.py` was calling `nselib.capital_market.shareholding_patterns(symbol=symbol)`
which does NOT exist in nselib. Discovery from prior session confirmed that nselib has:
- `corporate_actions_for_equity(period='6M')` -- bulk, returns 608 rows for all companies

The `run()` method had been partially edited to call `_fetch_bulk()`, but that method body
did not yet exist.

---

## Fix Applied

### Rewrote `engines/management/announcement_fetcher.py`

- Added `_fetch_bulk()`: single call to `corporate_actions_for_equity(period='6M')`
- Added `_parse_bulk(df)`: maps nselib columns to internal schema
  - `recDate` / `exDate` / `caBroadcastDate` -> `date`
  - `subject` -> `_classify(subject)` -> `announcement_type`
  - `series` column preserved for EQ filter
- Fixed date normalization bug: removed premature `[:10]` slice before `_normalize_date()`
  - "27-Apr-2026" was being cut to "27-Apr-202" before the regex could match 4-digit year
  - Fix: pass raw date string directly to `_normalize_date()`, which applies `[:10]` only
    as a final fallback on unrecognized formats
- EQ series filter applied post-parse (G-S-01)
- Atomic write: `.tmp.csv` then `shutil.move()` (G-D-02)

---

## Run Results

```
announcement_fetcher.py:
  527 records, 471 symbols
  DIVIDEND      446
  BONUS          24
  BUYBACK        19
  FUNDRAISE      18
  STOCK_SPLIT    18
  ACQUISITION     2

management_sentiment_engine.py (use_ai=False):
  471 symbols scored
  POSITIVE   435
  NEUTRAL     36
  Output: data/NSE/shareholding/management_sentiment.csv
```

---

## Commit

`da5623f` -- Fix announcement_fetcher.py: add _fetch_bulk() using nselib bulk corporate_actions

---

## Remaining Known Gaps

- `HoldingTrendEngine`: nselib has no shareholding_patterns() method.
  Engine returns STABLE signal for all symbols until an alternative data source is found.
  Options: NSE website scraping, Screener.in API, BSE shareholding feed.
  Current impact: holding_score defaults to 50 (STABLE), so management_score is
  driven almost entirely by announcement_score. Acceptable for now.

- Phase 15 (Financial Results): NSE XBRL endpoint returns 404, yfinance returns
  currentTradingPeriod error for NSE symbols. Both engines handle gracefully.
  Will auto-recover when upstream APIs are restored.
