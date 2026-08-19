# API validation

The existing routes remain authoritative:

- `POST /api/muhurta/recommend`
- `POST /api/muhurta/search`

Vehicle accepts the existing candidate/location/P032 request shape with
`activity_id=VEHICLE_CONVEYANCE_COMMENCEMENT`. Consecration uses the same shape
plus a required non-empty `ceremony_subtype`. Window search accepts the same
context field and returns the existing window schema with contract, source,
caution, consultation, capability/access and abstention fields.

OpenAPI exposes `ceremony_subtype` on both request models. Users cannot select a
contract, hash, rule or evaluator; activity IDs resolve to canonical internal
bindings.
