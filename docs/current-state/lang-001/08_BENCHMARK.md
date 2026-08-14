# Benchmark

`tests/fixtures/veda_lang001_benchmark.json` contains 100 deterministic cases:
English literal/idiomatic pairs, Hindi Devanagari and Roman Hindi, Hinglish,
abbreviation/domain cases, professional jargon, internet slang, metalinguistic
questions, and unknown expressions.

The current deterministic baseline is 54/90 (60.0%) expected resolution labels
for known cases. Unknown-expression fabricated-definition rate is 0/10 (0.0%).
These are implementation baselines, not human or general-world language
accuracy claims; the known-case misses remain follow-up tuning/data work.

LANG-001-R1 corrected nine isolated fixture metadata defects without erasing
this historical baseline. The post-remediation corrected score is 90/90 known
(100%); adversarial and holdout results are recorded in
`docs/current-state/lang-001-r1/`.
