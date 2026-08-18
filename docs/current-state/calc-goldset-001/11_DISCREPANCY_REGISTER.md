# Discrepancy Register

Machine-readable register: `artifacts/11_DISCREPANCY_REGISTER.json`.

| ID | Component | Classification | State | Decision |
|---|---|---|---|---|
| D001 | Ascendant | `REFERENCE_LIMITATION` | OPEN | Preserve both method descriptions; do not force a sign at the boundary |
| D002 | Ephemeris | `REFERENCE_LIMITATION` | OPEN | Pin explicit ephemeris files in a future standard/remediation phase |
| D003 | Timezone | `TIMEZONE_DIFFERENCE` | OPEN | Preserve caller fixed-offset and source-derived ADB paths separately |

The contained deterministic yoga-order defect was fixed in `engines/intelligence/kundli_engine.py` and covered by `tests/test_veda_calc_goldset_001.py`; it is not left as an open discrepancy.

