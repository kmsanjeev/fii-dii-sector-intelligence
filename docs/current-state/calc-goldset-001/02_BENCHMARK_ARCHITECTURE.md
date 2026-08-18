# Benchmark Architecture

The benchmark is layered so calculation evidence cannot be confused with predictive validity.

1. **GOLD_C diagnostic reference layer** — existing P004 fixtures and a direct pyswisseph reference path. It verifies reproducible agreement and boundary behavior, but is not independent oracle evidence.
2. **SILVER high-quality input layer** — the currently adjudicated ADB Tier A/B records. These are source-qualified inputs, not truth labels for calculated planetary output.
3. **STRESS layer** — all calculation-ready local ADB records combined with the 1,000-chart outcome-free OGDB population. It tests scale, failure handling and deterministic output, not population representativeness.
4. **User benchmark pathway** — accepts DOB/TOB/POB records with precision, source and documentary-status metadata. It does not require life events and never automatically promotes a user case to GOLD.

All layers use the same current runtime entry point. The benchmark does not create a second astrology engine, score features, join outcomes, train models, or activate prediction.

