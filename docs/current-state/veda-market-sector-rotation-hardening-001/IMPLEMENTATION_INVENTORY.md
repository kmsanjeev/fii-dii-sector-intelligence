# Implementation inventory

| Component | Decision | Result |
|---|---|---|
| `engines/participant/sector_rotation_intelligence_engine.py` | EXTEND | authoritative 6C engine now builds bounded constituent return/breadth history and additive contract fields |
| `backend/routers/sectors.py` | EXTEND | `/api/sectors` and detail surface expose structured contract fields without removing legacy fields |
| `tests/test_sector_rotation_contract.py` | CREATE TEST | deterministic return, missing-breadth, persistence and provider-contract coverage |
| VEDA core calculation | REUSE | no sector calculations moved into VEDA; adapter passes provider-owned result through |
| RAG / ML / prediction / EMP | UNCHANGED | no activation or semantic corpus change |

The stale `engines/intelligence/index_intelligence_engine_v2.py` and
`leadership_persistence_engine_v2.py` are not used; repository guidance and the
existing Phase 6C path remain authoritative.
