# Corrective classification policy

`ctimetype` is retained as `TIME_SYSTEM_TIMEZONE_HANDLING_NOT_BIRTH_TIME_PRECISION`.

Explicit provider accuracy is preserved exactly. A canonical VEDA precision label is assigned only from `itimeacc`; absent accuracy remains `UNKNOWN`. `time_unknown=yes/1` excludes the record from confirmatory birth-time candidacy even when a placeholder clock value is present.

Potential Tier A uses structured source codes 1, 2, 4, 51, and 52. Potential Tier B uses 5 and 53. Untimed codes 56–58 are retained as structured candidates but cannot qualify a time-accuracy candidate. Conflict, rectification, absent accuracy, unsupported source notes, and unknown source classes remain exclusion or adjudication states. Rodden rating is metadata only and is never an automatic VEDA tier.

The deterministic candidate count is an engineering pre-adjudication count, not a human-certified tier: 114 potential-A and 6 potential-B records. A bounded 30-record automated review queue is emitted for later human/source adjudication; it does not authorize astrology or event scoring.
