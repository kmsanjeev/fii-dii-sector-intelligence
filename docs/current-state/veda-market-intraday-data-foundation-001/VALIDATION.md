# Validation

- FII Intraday focused tests: `7 passed` after preserving the exact Dhan
  provider instrument type (`FUTIDX`/`OPTIDX`) in the identity contract.
- FII API-contract plus Intraday focused tests: `10 passed`.
- VEDA market provider plus Intraday capability tests: `30 passed`.
- VEDA repository regression: `93 passed`, `2` pre-existing deprecation
  warnings, with `PYTHONPATH=platform`.
- FII API smoke: `GET /api/intraday/status` returned `200` with
  `intraday-market-data-1.0` and `CREDENTIALS_UNAVAILABLE`.
- Official Dhan instrument-master endpoint HEAD: HTTP `200`, approximately
  26.8 MB, no raw content committed.
- Live session validation: `LIVE_SESSION_VALIDATION_PENDING`; no provider
  token exists and no live packet was fabricated.
- FII full regression was attempted: `1369 passed`, `1 failed` at the initial
  snapshot assertion because the additive routes required the API baseline to
  move from 158/171 to 162/175. The baseline generator, count assertion and
  affected tests were then rerun successfully; the failure was not a runtime
  or intraday behavior failure. Existing research/network-heavy tests produced
  their normal external-provider traffic and local generated-data changes;
  those files remain outside this release scope.
