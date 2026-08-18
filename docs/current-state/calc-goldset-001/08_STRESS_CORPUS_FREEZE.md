# STRESS Corpus Freeze

Machine-readable manifest: `artifacts/08_STRESS_CORPUS_FREEZE.json`.

The stress corpus contains 6,022 calculation-ready ADB inputs and 1,000 outcome-free OGDB inputs, for 7,022 combined candidates. Duplicate identity is not inferred from names; only exact normalized date/time/coordinate duplicates are counted. The corpus is not representative of any population and makes no predictive claim.

The ADB source has 6,036 records. Fourteen are excluded by the calculation input contract: thirteen lack a documentary birthplace and one has a malformed BCE year that cannot be represented by the current engine date contract. Compact DMMSS coordinates and `time_unknown` documentary noon placeholders are parsed deterministically.

