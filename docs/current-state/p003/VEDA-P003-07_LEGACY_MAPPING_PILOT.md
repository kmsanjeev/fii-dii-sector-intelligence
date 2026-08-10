# VEDA-P003-07 Legacy Mapping Pilot

## Pilot Scope

P003 mapped a deliberately small legacy sample:

- Vimshottari Dasha runtime
- Graha dignity runtime
- one existing yoga: Gaja Kesari

## Mapping Records

| Mapping ID | Legacy Location | Target Rule(s) | Status | Match |
| --- | --- | --- | --- | --- |
| `VEDA-LMP-000001` | `engines/intelligence/kundli_engine.py::_vimshottari_dasha` | `VEDA-RUL-DASHA-000001`, `VEDA-RUL-DASHA-000002` | `MAPPED_TO_SCHEMA` | `PARTIAL` |
| `VEDA-LMP-000002` | `engines/intelligence/kundli_engine.py::_dignity` | `VEDA-RUL-DIGNITY-000001` | `MAPPED_TO_SCHEMA` | `PARTIAL` |
| `VEDA-LMP-000003` | `engines/intelligence/kundli_engine.py::_detect_yogas` | `VEDA-RUL-YOGA-000001` | `MAPPED_TO_SCHEMA` | `EXACT` |

## Why Partial Exists

- Vimshottari runtime does not yet emit governed provenance IDs or coexistence metadata
- the dignity pilot represents only one branch of the runtime dignity table
- yoga provenance is not yet source-governed in P002

## Production Migration Status

- production rules migrated to the new schema: `0`
- production runtime switched to schema-driven evaluation: `0`

This is intentional.

P003 proves representability, not migration.
