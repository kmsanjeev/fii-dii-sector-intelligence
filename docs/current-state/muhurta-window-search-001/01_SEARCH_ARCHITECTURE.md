# Search architecture

`POST /api/muhurta/search` validates a bounded timezone-aware range, discovers only recommendation-relevant P032 transitions, calls the canonical P032 fact layer at a deterministic representative instant, delegates the candidate to RX1, and then performs categorical presentation.

The layers are intentionally separate:

1. `muhurta_transition_source.py` reuses the canonical Kundli/Swiss Ephemeris Sun/Moon position path and existing P032 boundary conventions.
2. `muhurta_foundation.build_candidate_windows` performs interval splitting.
3. `muhurta_recommendation_engine_rx1.recommend` remains the only rule/abstention/source-gap/caution authority.
4. `muhurta_window_search.search` merges only complete semantic equivalents and presents primary/equivalent/alternative windows.

The default search range is 7 days and the hard maximum is 31 days. The result includes performance telemetry, but semantic result comparison excludes wall-clock telemetry. Search never uses a numeric score, hidden weights, or personal birth data.
