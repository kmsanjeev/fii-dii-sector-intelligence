# API validation

The existing Muhurta router now exposes:

- `POST /api/muhurta/recommend` — unchanged RX1 single-candidate endpoint.
- `POST /api/muhurta/search` — bounded transition-aware range search.

Search accepts `activity_id`, `location`, `start_datetime`, `end_datetime`, optional daily bounds, `max_results`, optional formal activity scope, and controlled transition/fact fixtures for deterministic validation. It does not accept DOB, TOB, POB or personal Bala inputs. The OpenAPI path was verified after router registration. No frontend or separate Muhurta application was created.
