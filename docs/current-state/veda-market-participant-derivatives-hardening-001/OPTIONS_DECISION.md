# Options decision

Decision: `NOT_SUPPORTED` in the governed participant contract.

The provider source exposes option buckets, but the current persisted history
does not retain participant-wise option fields. `index_options.csv` is an
index-level PCR/spot diagnostic file, not participant options positioning.
`fno_intelligence.csv` is symbol-level futures intelligence, not a participant
options source. Neither is merged into the participant contract.

No long/short ratio, option PCR attribution by participant, option flow,
participant gamma, or option-derived prediction is emitted. A future options
programme would require a separate source inventory, persisted schema,
like-for-like dates, method validation and regression corpus.
