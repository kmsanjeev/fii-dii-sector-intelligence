# Certainty, Negation, and Source Preservation

The foundation carries structured governance fields unchanged and includes
English safety messages for qualified interpretation, research-only content,
not-validated content, inactive Muhurta recommendations, and the absence of a
predictive claim.

`validate_epistemic_preservation()` is intentionally conservative. It rejects
a rendered string that drops required phrases such as `may indicate`,
`research-only`, `not validated`, `not authorized`, `not proven`, or `no
predictive claim`. It is a regression guard, not a general translation-quality
metric.

Free-text interpretation is not machine translated. `render_interpretation()`
keeps canonical text in English until a reviewed locale translation exists and
attaches source metadata unchanged.
