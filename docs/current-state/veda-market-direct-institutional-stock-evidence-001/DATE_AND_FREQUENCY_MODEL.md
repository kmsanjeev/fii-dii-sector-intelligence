# Date and frequency model

The contract keeps these concepts separate:

- `source_date`: the date supplied by the local NSE deal report;
- `transaction_date`, `disclosure_date`, `filing_date`, `effective_date` and
  `acquisition_date`: null when the local artifact does not provide that
  distinct field;
- `quarter_end_date`: ownership observation date;
- `submission_date`: filing/submission date;
- `reporting_period`: source period label;
- `as_of`: component-wise dates, never one fabricated universal freshness date.

Deal evidence is daily-disclosed activity when present. Ownership evidence is
quarterly/filing-driven. `institutional_deal_signals.csv` is a rolling derived
summary and retains its own as-of date. Frequency mismatch is explicit in
`data_status.frequency` and `date_fields`.
