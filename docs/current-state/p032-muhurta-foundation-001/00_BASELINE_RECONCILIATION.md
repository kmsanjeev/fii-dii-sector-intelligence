# VEDA-P032-MUHURTA-FOUNDATION-001 — Baseline Reconciliation

Starting commit: `5356d9979ca4607b72c07b5ba1db35b596fe2e37`.

The repository already contained the P032 predecessor foundation surfaces:
`engines/ai/knowledge/muhurta_foundation.py`, the birth-time Panchanga
implementation in `kundli_calculator.py`, MUH-FND-001/MUH-R1 documentation,
and KNOW-MUH-001/002/003 source decisions. The roadmap still labelled P032
not started, so this activity reconciles that stale status as a bounded
foundation extension rather than creating a second Muhurta engine.

Existing reuse decisions:

| Capability | State before | Decision |
| --- | --- | --- |
| Solar day/sunrise | Existing, deterministic NOAA approximation | Reuse |
| Birth Panchanga | Existing five-limb facts | Reuse vocabulary and regression contract |
| Nakshatra boundaries | P016 governed calculation | Reuse boundary convention |
| Event families | Existing request enum and KNOW-MUH claims | Extend with taxonomy metadata only |
| Tara/Chandra Bala | Research candidate, reference not verified | Keep disabled |
| Electional scoring/recommendations | Not implemented | Remain inactive |
| Prashna | Out of scope/missing | Remain not started |

The pre-existing `data/reference/city_coords_cache.csv` working-tree change is
unrelated and is intentionally not included in this activity.
