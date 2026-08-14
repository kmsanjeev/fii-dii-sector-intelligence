# Group Benchmark

`tests/fixtures/veda_group001_benchmark.json` contains 50 deterministic scenarios and `veda_group001_transitions.json` contains 15 topic transition sequences. Coverage includes direct and non-direct address, reply-to, attribution, quoted speech, pronoun ambiguity, topic ownership/shift, agreement, conflict, consensus, per-speaker Hindi/Hinglish, Jyotisha parent/child subject separation, participation, and position changes.

Focused acceptance asserts explicit transport identity and reply-to are preserved exactly, direct VEDA addressing responds, participant-directed turns are observed, and the benchmark minimums are met. Human group quality is not inferred from deterministic fixtures.
