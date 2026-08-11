# VEDA-P007 Knowledge Gap Engine

P007 generates Jyotisha research missions from the P005 legacy-rule inventory instead of hardcoding a new research backlog.

## Input

- `data/veda/validation/interpretations/p005_legacy_rule_registry.json`

## Output

- `data/research/vedic_astrology_pilot/p007_gap_missions.json`

## Selection Rules

- `LEGACY_UNSOURCED`
- `LEGACY_PARTIALLY_SOURCED`
- `SOURCE_CANDIDATE_FOUND`

## Priority Pattern

- `P1`: foundational dasha, graha/bhava, health/longevity, remedies
- `P2`: yoga, dosha, marriage, career, finance
- `P3`: AstroFinance and exploratory items

The exported sample queue contains `12` machine-readable missions.
