# Module Log — Phase UI-C: Corporate Intelligence Hub

**Date:** 2026-07-12
**Status:** COMPLETE
**Version:** 4.41.0

## User Request

"The whole page seems to be wage [vague]. Check the purpose of this page and
the values being shown -- what do they refer to? If we require the page as
per our model, how can we make it more useful and with what kind of data?
Discuss with me first."

## Discovery

CorporatePage.tsx was two bare tables: institutional_deal_signals.csv
(aggregated 30D per-symbol) and upcoming_catalysts.csv, reading only 2 of
6 available corporate datasets. No filters, no links to stock pages, no
summary. Six corporate datasets exist:
- company_announcements.csv (375,962 rows, live to today)
- announcement_signals.csv (2,405 rows)
- corporate_confidence_scores.csv (1,046 rows)
- event_calendar.csv (33,858 rows -- but max date was 2026-07-04, 8 days
  stale, ZERO future rows despite "upcoming" being the whole point)
- corporate_action_signals.csv (40,744 rows, 1999-2026)
- block_bulk_deals.csv (13,631 rows, live to 2026-07-10)

## User Decisions (AskUserQuestion)

1. Scope: **full hub, all 6 sections** in this phase (not phased further)
2. Event calendar staleness: **fix in this phase**, not deferred
3. Structure: **single scroll**, Dashboard-style card language (not tabs)

## Root cause -- event calendar staleness

corporate_event_calendar_engine.py fetched only from
`last_cached_date+1` to `datetime.now()`. Board meeting announcements are
scheduled ahead of the actual date, so a forward-only-to-today window
means the moment NSE stops backfilling old entries, the "upcoming"
catalysts file has nothing left in it -- it was silently going empty on a
rolling basis. Additionally, 7B was never added to
engines/orchestration/daily_refresh.py's STAGES list (7A and 7C were), so
this had no automated run catching it.

Fix: query window is now `min(catchup, now-7d)` through `now+60d` on every
run, and 7B_event_calendar was added to the pipeline after 7A. Immediate
backfill run: 258 upcoming catalysts populated (was near-zero).

## Root cause -- MF misclassification (found during screenshot QA)

While visually verifying the new Deal Tape section, "QUANT MUTUAL FUND"
rendered with a RETAIL badge. block_bulk_deal_engine.py's MF_KEYWORDS list
enumerates abbreviated brand forms ("QUANT MF", "TATA MF") but NSE deal
records use the full official AMC name ("QUANT MUTUAL FUND"), which never
substring-matched. Fixed with a generic suffix rule: "MUTUAL FUND" is a
SEBI-reserved suffix only registered AMCs may legally use, so any client
name containing it is classified MF regardless of whether the specific
brand is enumerated.

Since `participant` is a derived column (not raw data, so G-D-01 does not
apply), reclassified all 13,631 existing rows in place via a one-off
script rather than a full re-download, then rebuilt
institutional_deal_signals.csv from the corrected file (the engine always
recomputes signals from full history on every run). 61 rows moved from
RETAIL to MF. This also improves the Dashboard Institutional Deals card
and any conviction/signal engine reading inst_net_value_cr, not just this
page.

KNOWN REMAINING GAP: generic-named foreign funds ("THE JUPITER GLOBAL
FUND") still fall through to RETAIL. Unlike "MUTUAL FUND", there is no
safe generic substring for FII names -- would need a curated FPI registry.
Documented, not fixed (out of scope; no safe automatic rule exists).

## Implementation

**Backend** (`backend/routers/corporate.py`): 3 new endpoints --
GET /deal-tape (participant + min_cr filters), GET /upcoming-actions
(ex-date window from corporate_action_signals.csv), GET /summary (8-field
KPI aggregate). `data_loader.py` registered "block_deals" source.

**Frontend** (`frontend/src/pages/CorporatePage.tsx`, full rewrite): KPI
strip, AnnouncementRadar (72h window, type + score filters, links to stock
pages), DealTape (participant filter, client names, direction color),
ActionCalendar (45D ex-date grid, color by action type), ConfidenceLeaderboard
(top 12, bar-normalized, "pts" unit label since it's a raw weighted score
not a percentage), CatalystsPanel (existing data, now linked).

**Engine fixes**: `corporate_event_calendar_engine.py` (forward window),
`daily_refresh.py` (7B stage added), `block_bulk_deal_engine.py` (MF
suffix rule).

## Verification

- tsc --noEmit clean; vite build clean (2.49s)
- All new endpoints live-tested against restarted backend with real data
- Playwright full-page screenshots at each stage caught the MF bug that
  API-only testing would have missed (visual QA surfaced a data quality
  issue, not just a rendering issue)
- Full test suite 267/267 green after data changes
