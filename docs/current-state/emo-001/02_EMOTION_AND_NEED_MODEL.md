# EMO-001 Emotion and Need Model

The bounded taxonomy distinguishes sadness, disappointment, grief, worry, fear,
uncertainty, frustration, anger, loneliness, vulnerability, affection,
gratitude, excitement, relief, and mixed states. Ambiguous, quoted, fictional,
and metalinguistic emotional language returns `UNKNOWN` with low confidence.

Interaction need is separate from emotion: `JUST_LISTEN`, `ACKNOWLEDGE`,
`GIVE_ADVICE`, and `GIVE_DIRECT_ANSWER` are selected only from explicit or
strong conversational evidence. `I just need to vent` suppresses automatic
solution dumping; an explicit advice question permits advice. This is a
strategy signal for COMM-002, not a response generator.

Clinical diagnoses and fabricated assistant emotions are not produced.
