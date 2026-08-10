# VEDA-P005-R1 Stock Finance Remediation

Date baseline: `2026-08-10`

## Risk

P005 identified a P0 risk in stock-kundli finance presentation. User-facing stock interpretation surfaces exposed action labels such as:

- `STRONG_BUY`
- `BUY`
- `HOLD`
- `CAUTION`
- `EXIT`
- `AVOID`

Those labels were derived from unsourced legacy astrology heuristics and were presented too close to validated financial instruction.

## Remediation

R1 preserved the underlying internal heuristic scoring while changing the user-facing envelope:

- `interpretation.signal` now uses bounded labels such as `Strong positive astrology heuristic`;
- the raw legacy code is preserved as `signal_code`;
- remediated payloads now include `evidence_class`, `source_status`, `interpretation_type`, `high_stakes`, `actionability`, `output_classification`, and `boundary_note`;
- chart-level `astro_action` text is similarly bounded while preserving the raw code as `astro_action_code`.

## Result

The stock-kundli path still exposes the analytical signal, but it no longer presents that signal as validated trading or investment advice.

Representative regression evidence:

- `tests/test_veda_interpretation_safety_remediation.py::test_stock_kundli_route_returns_bounded_finance_labels`
- `tests/test_veda_interpretation_validation.py::test_p005_summary_captures_interpretation_baseline`

Status: `MITIGATED`
