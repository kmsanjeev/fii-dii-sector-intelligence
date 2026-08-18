# VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001 — Baseline

Date: 2026-08-19
Starting commit: `61eb8d6904a145f5452c508876a96b6f7eec3856`
Branch: `main`
Starting tracked tree: clean
Decision: `CANONICAL_CONTRACT_INCONSISTENT`

The frozen implementation specification is
`docs/current-state/calc-ashtakavarga-normalization-rx2-001/17_CANONICAL_RAW_CONTRACT.json`.
The source-cell witness is
`docs/current-state/calc-source-rx-001/04_ASHTAKAVARGA_SOURCE_RULE_MATRIX.json`.

The contract hash is verified. The source matrix contains 768 complete cells
and its recorded canonical row hash is verified. However, the matrix computes
seven planetary target totals of 49, 49, 39, 54, 54, 52 and 39, summing to
336. The frozen contract requires 337. Adding the matrix's 49-point Lagna row
therefore computes 385, while the contract's optional combined display says
386.

This is the programme's explicit hard-stop condition. No production BAV/SAV
code, source matrix value, schema, consumer, reduction, RAG artifact or
Approved Core state was changed.
