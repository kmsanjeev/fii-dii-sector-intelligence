# Implementation inventory

| Component | Decision | Result |
|---|---|---|
| `participant_acquisition_engine.py` | REUSE | Existing nselib sources and history files remain authoritative |
| `participant_flow_engine.py` | EXTEND | Adds 1D/3D/10D windows and preserves missing cash evidence |
| `participant_intelligence_engine.py` | EXTEND | Renormalizes available ensemble components; unavailable regime is explicit |
| `backend/routers/participant.py` | EXTEND | Adds additive contract and `/api/participant/institutional` |
| `institutional_contract.py` | WRAP | Pure read/derive layer over existing participant outputs |
| VEDA market adapter | REUSE | Existing adapter accepts additive provider fields and legacy required fields |
| RAG / ML / PRED / EMP | PRESERVE | No semantic or maturity changes |

No raw or generated data files are implementation scope.
