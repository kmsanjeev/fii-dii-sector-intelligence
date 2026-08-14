# Benchmark

`tests/fixtures/veda_lang001_benchmark.json` contains 100 deterministic cases:
English literal/idiomatic pairs, Hindi Devanagari and Roman Hindi, Hinglish,
abbreviation/domain cases, professional jargon, internet slang, metalinguistic
questions, and unknown expressions.

The current deterministic baseline is 54/90 (60.0%) expected resolution labels
for known cases. Unknown-expression fabricated-definition rate is 0/10 (0.0%).
These are implementation baselines, not human or general-world language
accuracy claims; the known-case misses remain follow-up tuning/data work.
