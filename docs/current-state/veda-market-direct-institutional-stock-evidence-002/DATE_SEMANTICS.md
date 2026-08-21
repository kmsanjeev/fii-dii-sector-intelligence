# Date semantics

The contract preserves component dates rather than collapsing them into one
freshness date:

- disclosed deals: `source_date` is the date in the local NSE daily report;
  the local extract does not separately expose transaction and disclosure
  dates, so it is explicitly `DATE_SEMANTICS_LIMITED`;
- ownership: `quarter_end_date` and `submission_date` remain separate;
- derived signals: `as_of_date` and source record IDs are retained;
- reserved fields include exchange publication, reporting-period, filing,
  effective, acquisition and retrieval dates and remain null when unavailable.

No quarter-end ownership snapshot is presented as daily activity and no deal
report date is silently presented as a settlement or execution timestamp.
