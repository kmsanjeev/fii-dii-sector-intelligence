# Implementation inventory

| Component | Action | Result |
|---|---|---|
| `participant_acquisition_engine.py` | Reused | Existing NSE source functions and aggregate-futures formula retained |
| `participant_flow_engine.py` | Reused | Existing daily and rolling OI-change derivation retained |
| `participant_intelligence_engine.py` | Reused | Existing scores/regime/divergences retained |
| `institutional_contract.py` | Extended | Minor contract metadata, level/change semantics, persistence directions, same-basis divergence, date alignment |
| `backend/routers/participant.py` | Reused | Existing `/latest` and `/institutional` endpoints retained |
| VEDA market adapter | Reused | Provider output remains pass-through; no market calculation in VEDA |

No new retriever, database, prediction path, ML path, astrology path or
participant engine was created. The source options fields are documented but
not promoted into production output.
