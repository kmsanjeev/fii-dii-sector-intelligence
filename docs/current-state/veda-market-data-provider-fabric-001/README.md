# VEDA-MARKET-DATA-PROVIDER-FABRIC-001

Status: `VEDA_MARKET_DATA_PROVIDER_FABRIC_OPERATIONAL_WITH_CONDITIONS`

The FII-DII repository now exposes a broker-agnostic, read-only provider
fabric around the existing `BrokerAdapter` and intraday foundation.  The
fabric owns manifests, capability vocabulary, local connection metadata and
fail-closed resolution.  It does not own provider secrets, authentication
flows, live network calls, order placement or a second market-data engine.

## Scope and ownership

- Existing Dhan, CSV import, local EOD and intraday code remains the data and
  adapter owner.
- `engines/providers/fabric.py` is metadata/policy only.
- Encrypted credentials remain in the existing ignored local broker store.
- `GET /api/broker/providers` exposes manifests and sanitized connection
  metadata; `POST /api/broker/providers/resolve` resolves one capability.
- `ORDER_EXECUTE` is intentionally never resolved as an active capability.
- No RAG, ML, prediction, EMP, Jyotisha or BEBOS files changed.

## Conditions

Dhan remains the only implemented authenticated market-data adapter and its
data entitlement is still a provider/runtime condition. Zerodha/Kite and
HDFC Sky are represented as provider-specific manifests only. Public/community
sources are compatibility or research candidates and are not silent fallback
authority.

Next recommended activity: `VEDA-MARKET-INTRADAY-PROVIDER-ACCESS-VALIDATION-RX1`.
