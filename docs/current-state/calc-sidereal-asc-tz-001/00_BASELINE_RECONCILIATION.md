# VEDA-CALC-SIDEREAL-ASC-TZ-001 — Baseline Reconciliation

## Starting state

- Starting commit: `2342cad7e534435bb5b606d3673f78ad3c91e74a`
- Branch: `main`
- Parent: `VEDA-CALC-ORACLE-001`, `CALC-M5_PARTIAL_EXTERNAL_VALIDATION`
- Unrelated pre-existing work: one valid `barh` row in `data/reference/city_coords_cache.csv`; it remains unstaged.
- Raw Astro-Databank material and local research artifacts remain ignored and uncommitted.
- P015/P015-RX, Goldset, Oracle, D20 calculation gate, D20 interpretation gate, prediction, ML, production, RAG and Approved Core states are preserved.

## Inherited calculation baseline

The parent oracle passed 504/504 JPL Horizons tropical comparisons across 72 fixed timestamps and seven bodies. It also reproduced the frozen Ascendant `houses_ex` reference after explicit Lahiri initialization, while retaining the known runtime `houses()` plus ayanamsha boundary difference. Goldset Silver and Stress results remain the comparison baseline.

The historical OpenAPI snapshot was conclusively stale: the canonical generator reported 140 paths/153 operations while the fixture held 129/141. It was regenerated through `scripts/generate_p001_api_baseline.py`; no endpoint was hand-edited.

## Scope boundary

This activity validates calculation foundations only. It does not validate prediction, life events, feature effects, ML, PRED-M4, production prediction, D20 interpretation, recruitment or participant data.
