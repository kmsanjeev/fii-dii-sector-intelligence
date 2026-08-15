# D20 Existing Implementation Audit

| Field | Finding |
|---|---|
| Registry | `engines/ai/knowledge/varga_governance.py` `VARGA_METHODS["D20"]` |
| Current method | `general` |
| Version | No D20-specific version; canonical fallback reports `legacy` |
| Function | `varga_sign(longitude, 20, "general")` |
| Callers | `canonical_varga_fact`; existing P012/P015 Varga surfaces |
| Division | 20 parts of 1°30′ |
| Start logic | Current generic branch: same sign for even zero-based sign index; sign + 6 for odd zero-based index |
| Mapping | Sequential sign mapping from computed start |
| Ascendant/planet handling | Same longitude function; no D20-specific distinction |
| Tests | Generic Varga inventory/determinism; no independent D20 source fixture |
| Fallback | Generic legacy branch |
| Source metadata | P004 validated runtime reproduction; broader formula provenance unresolved |
| Interpretation | `REFERENCE_ONLY` / P031 `NOT_VALIDATED` |

The current code is technically deterministic but is not a documented source-specific Vimshamsha implementation.
