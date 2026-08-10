# VEDA-P005-R1 Longevity Remediation

Date baseline: `2026-08-10`

## Risk

P005 identified a P0 risk in the personal kundli longevity section. The runtime surface used deterministic-sounding lifespan language and traditional maraka context without an explicit safety boundary.

## Remediation

R1 preserved the internal traditional analysis path but changed the user-facing output envelope:

- the longevity section remains available as a traditional Jyotisha interpretation surface;
- deterministic lifespan wording was removed;
- explicit safety language now states that the section is not a factual lifespan or death prediction;
- the narrative now emphasizes vitality, resilience, and caution factors rather than age-of-death style certainty.

## Result

Traditional material remains visible for research continuity, but the runtime presentation no longer treats longevity output as reliable factual prediction.

Representative regression evidence:

- `tests/test_veda_interpretation_safety_remediation.py::test_personal_longevity_report_is_bounded_and_non_deterministic`

Status: `MITIGATED`
