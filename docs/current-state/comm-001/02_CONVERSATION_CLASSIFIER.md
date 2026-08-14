# Conversation Classifier

The STD-003 ten-type taxonomy remains compatible and now supports `UNKNOWN`,
`MIXED`, and explicit transition metadata. Primary and secondary types are
retained separately. Confidence is emitted with every classification.

The deterministic benchmark contains 50 initial type examples, five per type,
plus language, idiom, slang, sarcasm, and ambiguity cases. The authored initial
set classifies 50/50 in the current configuration.
