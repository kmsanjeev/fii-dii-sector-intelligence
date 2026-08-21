# Valuation semantics

PE and PB are ratios. They do not by themselves establish cheapness,
expensiveness, undervaluation or a fair value. The legacy valuation label and
composite score remain compatibility fields but are marked as legacy derived
output and are not promoted as authoritative valuation conclusions.

The existing `roe_pct` semantic defect is recorded and isolated: it contains a
net-margin-like value in the legacy file, so the new contract reports
`LEGACY_COLUMN_IS_NET_MARGIN_NOT_ROE` and does not claim ROE.
