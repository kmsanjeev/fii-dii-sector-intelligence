# COMM-002 Deterministic Benchmark

The frozen adaptation fixture is `tests/fixtures/veda_comm002_adaptation_benchmark.json` with 60 scenarios. It covers all ten conversation types, English/Hindi/Hinglish, explicit style instructions, novice/expert domain presentation, high-stakes restraint, ambiguity, structure, and continuity-related policies.

Acceptance is property-based rather than exact-prose matching. The focused test
passes 60/60 (100%) expected-property checks, 4/4 (100%) explicit-instruction
checks, and 2/2 (100%) high-stakes boundary checks. Human naturalness is not
claimed from this deterministic benchmark.
