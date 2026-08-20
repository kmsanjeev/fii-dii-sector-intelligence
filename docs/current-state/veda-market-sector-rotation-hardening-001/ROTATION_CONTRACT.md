# Sector rotation contract 1.1

`GET /api/sectors` remains the only formal sector surface. The response is an
additive evolution of the prior contract and retains `rotation_signal`,
`combined_score`, participant fields and FPI fields.

Each sector now additionally carries:

- `performance`: 1D/3D/5D/10D/20D sector, benchmark and relative returns;
- `breadth`: positive percentage, expected/usable constituents and coverage;
- `leadership`: relative-strength rank, score, state and persistence evidence;
- `rotation`: state, 5D rank change and acceleration state;
- `date_alignment`: sector/benchmark/institutional/FPI dates and alignment;
- `institutional_context`: governed scope and limitations;
- `evidence_quality`: evidence completeness, not predictive confidence;
- `facts`, `signals`, `interpretation`, `leaders`, `laggards`, `limitations`;
- `contract_version: sector-rotation-1.1`.

The legacy `FII_flow_score` and related fields are retained for compatibility,
but the response explicitly states `MARKET_LEVEL_CONTEXT_ONLY`. They must not
be interpreted as direct sector-specific FII/DII attribution.
