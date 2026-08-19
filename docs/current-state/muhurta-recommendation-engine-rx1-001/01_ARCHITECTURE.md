# Architecture

The RX1 production boundary is `engines/ai/knowledge/muhurta_recommendation_engine_rx1.py`, exposed through the existing FastAPI application at `POST /api/muhurta/recommend`.

The path is:

1. Load and hash-verify the immutable RX2 V4 contract.
2. Validate candidate datetime and location.
3. Reuse P032 Panchanga facts, or calculate them with the existing P032 function when both supplied sidereal longitudes are present.
4. Reuse `adapt_p032_facts` to expose stable evaluator factors.
5. Validate and evaluate only declarative machine-ready predicates.
6. Preserve source-partial rules as disclosed nonblocking gaps.
7. Classify one candidate categorically; no window search, score, ranking, or hidden weight.
8. Emit caution, consultation guidance, contract metadata, and source trace.

Unsupported activities return a governed `ABSTAIN` result. Malformed input or a contract/runtime failure is an `ENGINE_ERROR` at the API boundary and is not disguised as a recommendation.
