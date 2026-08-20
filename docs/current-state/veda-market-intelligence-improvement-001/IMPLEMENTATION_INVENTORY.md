# Implementation inventory

## FII-DII

- `backend/services/data_loader.py`: dataset date detection, freshness state,
  provenance, update timestamp and limitations.
- `backend/routers/market.py`: nullable numeric values and `data_status` on
  regime/context; metadata on freshness endpoint.
- `backend/routers/participant.py`: nullable flow values and `data_status`.
- `backend/routers/sectors.py`: nullable FPI values and `data_status`.
- `backend/routers/corporate.py`: unavailable corporate signals remain
  explicit and carry `data_status`.
- `backend/routers/stocks.py`: nullable formal stock signal fields and
  `data_status`.
- `tests/test_market_freshness_contract.py`: deterministic freshness,
  scheduled-date, unavailable-optional and missing-number coverage.

## VEDA

- `platform/app/providers/market_intelligence.py`: validates and propagates
  the normalized `data_status` contract while retaining predecessor fields.
- `platform/tests/test_market_provider.py` and
  `platform/tests/test_public_foundation.py`: updated contract fixtures and
  assertions.

## Explicitly unchanged

The FII scheduler, Telegram/reporting paths, legacy bridge, RAG artifacts,
prediction/ML code, identity/entitlement controls and BEBOS were not changed.
