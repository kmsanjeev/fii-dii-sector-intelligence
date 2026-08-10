# VEDA-P005-R1 AstroFinance Remediation

Date baseline: `2026-08-10`

## Risk

P005 established that current AstroFinance rules are heuristic or empirical-market experiments, not classical source-validated Jyotisha rules. Despite that, sector outputs still exposed action-oriented wording close to:

- `BUY`
- `HOLD`
- `CAUTION`
- `EXIT`
- `AVOID`

and reason text could read as directive.

## Remediation

R1 introduced a bounded AstroFinance presentation layer:

- user-facing labels now read as bounded heuristic classifications such as `Positive AstroFinance heuristic`;
- raw internal action codes are preserved as `astro_action_code`;
- reasons are rewritten as non-prescriptive heuristic explanations;
- sector payloads now carry `evidence_class=INTERNAL_HEURISTIC` and `source_status=UNVERIFIED`;
- frontend presentation now shows the heuristic boundary note and avoids local reconstruction of prescriptive text.

## Result

AstroFinance remains operational and visible, but it now exposes itself as heuristic research output rather than validated market advice.

Representative regression evidence:

- `tests/test_veda_interpretation_safety_remediation.py::test_astrofinance_tool_returns_bounded_heuristic_payloads`
- `frontend/src/test/AstroSafetyPresentation.test.tsx`

Status: `MITIGATED`
