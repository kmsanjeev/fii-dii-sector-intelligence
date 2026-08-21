# Validation

- Real Dhan authentication/profile: pass.
- Dhan Data API entitlement: blocked (`Deactive`, `NA`).
- Instrument master: pass, exact identities obtained in memory.
- Historical equity/futures/OI: blocked.
- Quote: blocked.
- Option chain/Greeks: blocked.
- WebSocket: pending because market was closed and entitlement inactive.
- Normalization, quality, aggregation, storage and idempotency: deterministic
  regression-only; prior fixture tests pass.
- No-broker EOD path: pass.
- FII focused provider/foundation/security/API suite: `20 passed`.
- FII market/broker regression slice: `39 passed`.
- FII full repository suite: `1,378 passed`, one pre-existing Starlette/httpx
  deprecation warning.
- VEDA platform suite: `96 passed`, two pre-existing Authlib/httpx
  deprecation warnings.
- Python compilation: pass.
- Real HTTP boundary: FII status/provider-resolution and VEDA provider-fabric,
  readiness and intraday query checks passed; VEDA propagated the FII
  entitlement-blocked state without exposing secrets.
- yfinance fallback: prohibited and unused.
- nselib/nsepython promotion: none.
- Orders/trading: none.

The authoritative result is operational with conditions, not full live-data
acceptance.
