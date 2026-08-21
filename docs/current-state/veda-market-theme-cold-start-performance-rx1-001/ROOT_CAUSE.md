# Root cause

Primary cause: `REQUEST_TIME_FULL_HISTORY_PRICE_LOAD`.

The first Theme summary iterated through 15 Themes and loaded 2,106 full
per-symbol price histories from the stock-history Parquet cache. The largest
required return window is only 20 trading sessions, but the request read the
entire available `date`/`close` history for every member file.

Secondary causes:

- `FIRST_REQUEST_INDEX_BUILD`: membership indexes were reconstructed from CSV
  inputs on process start because no validated runtime membership artifact was
  consumed.
- `REQUEST_TIME_DYNAMIC_PROJECTION_BUILD`: no persisted bounded price
  projection existed, so every process paid the price-file cost once.

Ruled out by trace:

- no request-time snapshot rebuild existed before the RX; there was no usable
  snapshot artifact at the predecessor baseline;
- no recursive repository-wide price discovery;
- no per-member Stock Intelligence service calls;
- no Corporate, Fundamental, or institutional per-member calls;
- no FII self-HTTP;
- no global recursive Theme-detail computation;
- registry parsing and benchmark loading were not material causes.
