# Validation

- FII current provider/foundation/security/API focused suite: `20 passed`.
- FII market/broker regression slice: `39 passed`.
- VEDA platform regression: `96 passed`, with pre-existing deprecation
  warnings.
- FII API smoke: `GET /api/intraday/status` returned `200` with
  `intraday-market-data-1.0`, authenticated profile metadata and
  `ENTITLEMENT_BLOCKED`.
- Official Dhan instrument-master endpoint HEAD: HTTP `200`, approximately
  26.8 MB, no raw content committed.
- Live session validation: `LIVE_SESSION_VALIDATION_PENDING`; the market was
  closed for the bounded run and the inactive Data API entitlement blocked
  live packets.
- FII full regression: `1378 passed`, one pre-existing Starlette/httpx
  deprecation warning. Existing research/network-heavy tests produced their
  normal external-provider traffic and local generated-data changes; those
  files remain outside this release scope.
