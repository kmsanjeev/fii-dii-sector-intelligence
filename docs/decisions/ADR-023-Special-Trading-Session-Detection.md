# ADR-023 — Special Trading Session Detection (Muhurat / Budget Day)
Status: Accepted
Date: 2026-07-15

## Context

NSE occasionally holds a live trading session on a date that would
otherwise be skipped as a weekend or holiday. `holiday_engine.py`'s
`get_trading_days()` generated candidate dates via
`pd.date_range(freq="B")` (business days only) minus a holiday list --
structurally blind to any weekend session, regardless of whether NSE
actually published a bhavcopy for it. `data/CLAUDE.md`'s own "Trading
Calendar Edge Cases" table already listed "Mahurat trading" and "Budget
day (Feb 1)" as known edge cases, but no code ever implemented handling
for them -- the same "documented but never wired up" pattern found
elsewhere in this codebase this session (e.g. the STRONG_CANDIDATE
taxonomy staleness).

User confirmed via an NSE circular (NSE/CMTR/72349, dated 2026-01-16)
and direct clarification that exactly two recurring patterns exist,
not an open-ended set:

1. **Diwali Muhurat trading** -- an annual tradition (NSE since 1992),
   date varies with the Hindu lunisolar calendar.
2. **Union Budget Day special session** -- fixed to Feb 1 every year;
   NSE began running a live session on it whenever Feb 1 falls on a
   weekend starting 2026 (the Feb 1, 2026 Sunday session was the first).

## Decision

Add special-session detection to `engines/common/holiday_engine.py`,
feeding into the existing `get_trading_days()` output rather than
building a parallel fetch mechanism:

1. **Muhurat -- auto-detected, no maintenance needed.** NSE's own
   current-year holiday calendar (`nselib.trading_holiday_calendar()`)
   marks this date with an asterisk in the Equities holiday description
   (e.g. `"Diwali Laxmi Pujan*"`) even though it's listed as a holiday.
   `_detect_muhurat_from_calendar()` reads this signal every time
   `refresh_special_sessions()` runs. Self-updating for as long as NSE
   keeps this convention; the API only returns the current year, so
   this alone cannot backfill past years (see Backfill below).

2. **Budget Day -- fixed rule.** `_detect_budget_day(year)` flags Feb 1
   whenever it falls on a Saturday or Sunday, gated by
   `BUDGET_DAY_SPECIAL_SESSION_START_YEAR = 2026` (the practice's
   confirmed start year -- not applied retroactively before this, since
   Budget day was the last working day of February pre-2017 and thus
   never needed special weekend handling by construction).

3. **Persistent record**: `data/reference/special_trading_sessions.csv`
   (force-tracked in git despite the blanket `data/**/*.csv` ignore
   rule, same precedent as `nse_holidays.csv`) -- both an audit trail
   and a manual-override safety net if NSE ever announces a third
   pattern that doesn't fit either automated rule.

4. **Wiring**: `get_trading_days()` unions the special-session dates
   (within the requested range) into its normal weekday-minus-holidays
   output. `nse_equity_acquisition_engine.main()` -- already run daily
   via `daily_refresh.py`'s `1A_bhavcopy_equity` stage -- now calls
   `update_nse_holidays()` and `refresh_special_sessions()` at startup
   (both are cheap no-ops once already current for the year). No new
   fetch logic was needed: the existing `validate_archive() ->
   refresh_missing_dates() -> backfill_missing_dates()` pipeline
   automatically picks up any special-session date as "expected" and
   backfills it through the same NSELIB-primary/archive-fallback path
   used for every other date.

## Backfill (one-time)

`trading_holiday_calendar()` only returns the current year, so it
cannot recover past Muhurat dates. Verified 2010-2025 via web search
(cross-checked against known Diwali dates), seeded into
`special_trading_sessions.csv`. Of the dates that actually fell on a
weekend (2013-11-03, 2016-10-30, 2019-10-27, 2020-11-14, 2023-11-12,
2026-02-01 -- weekday Muhurat dates were already covered by normal
acquisition and needed no backfill):

- Downloaded successfully: 2019-10-27, 2020-11-14, 2023-11-12,
  2026-02-01 (the immediately known gap)
- Unavailable at NSE's own archive (`FileNotFoundError`, confirmed not
  a fetch-logic bug since regular weekday data from the same years
  downloads fine via the identical mechanism): 2013-11-03, 2016-10-30

Pre-1995 and pre-2010 Muhurat dates were not pursued -- 1995 is the
bhavcopy archive's start year, and pre-2010 dates lack a reliably
verified source; left as a known gap rather than guessed.

## Consequences

**Positive:**
- Future Muhurat sessions require zero manual maintenance -- detected
  automatically from NSE's own calendar every year.
- Future Budget Day weekend sessions are caught by a one-line fixed rule.
- Reuses the existing, already-tested acquisition pipeline entirely --
  no new fetch/retry/recovery logic to maintain.
- A third, unforeseen special-session type can be added via a single
  row in `special_trading_sessions.csv` without code changes.

**Negative:**
- `get_trading_days()` now depends on a file (`special_trading_sessions.csv`)
  that must itself be kept fresh -- if `refresh_special_sessions()`
  never runs (e.g. the acquisition engine is skipped for a long
  stretch), a new year's Muhurat date could be missed until the next
  run. Mitigated by running on every `main()` invocation (daily).
- Two historical Muhurat dates (2013, 2016) remain unrecoverable from
  NSE's archive.

## Related ADRs

- ADR-004 -- Listing-Date-Aware Processing (holiday_engine.py is used
  by the same acquisition layer this governs)
