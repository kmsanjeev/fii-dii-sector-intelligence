# Date and Lifecycle Model

The contract carries separate fields where available:

- `announcement_date`: date of disclosed announcement;
- `effective_date`: event/ex/effective date or source-reported calendar date;
- `record_date`: corporate-action record date;
- `completion_date`: deliberately null unless a governed completion field is
  available; this activity does not infer it;
- `result_period_end`: reporting period end, linked to fundamentals;
- provider freshness: retrieval/update state from `data_loader`, not an event
  date.

Lifecycle states are `ANNOUNCED`, `SCHEDULED`, `UNKNOWN` and `NOT_AVAILABLE`.
Past calendar/action dates are not upgraded to `COMPLETED`; this avoids
turning a schedule or stale row into an outcome.

ISO/year-first values are parsed year-first. Legacy local date values are
parsed day-first only when they are not year-first. Years outside 1900..2100
are treated as invalid rather than allowed to crash or distort freshness.

Freshness remains source-conditioned. The live audit observed announcements
and corporate actions at EOD freshness, a stale event calendar, and unknown
quarterly-results freshness because the source has no usable single date
column. The aggregate `data_status` therefore remains `UNKNOWN` with these
limitations visible.
