# VEDA-CALC-ORACLE-001 — Baseline Reconciliation

Starting HEAD: `688f57179d48701f7a11b7b3844505f0a81cf646` on `main`.

The repository was clean except for the pre-existing, unrelated Barh coordinate row in `data/reference/city_coords_cache.csv`; it is preserved and is not part of this programme. The parent Goldset tag `veda-calc-goldset-001` points to the starting commit. The intermediate commits after the parent were reviewed: pipeline control/progress fixes, dependency/CI repairs, holiday restoration, and data checkpoints are unrelated valid application history, not unexplained calculation drift.

The baseline API snapshot failure is also pre-existing and out of scope. The current application exposes 140 paths/153 operations while the historical P001 fixture expects 129/141. The twelve added empirical intake endpoints descend from the authorized empirical-console change; the snapshot is not changed here.

Raw Astro-Databank files remain ignored and local. No life-event scoring, prediction, ML, PRED-M4, production activation, or RAG change is permitted by this activity.

