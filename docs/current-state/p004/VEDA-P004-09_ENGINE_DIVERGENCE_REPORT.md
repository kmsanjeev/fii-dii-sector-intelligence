# VEDA-P004 Engine Divergence Report

| Divergence ID | Field | Category | Status | Reason |
| --- | --- | --- | --- | --- |
| `VEDA-DIV-CALC-000001` | `nakshatra_name_normalization` | `FORMAT_ONLY` | `KNOWN` | Personal path uses fuller canonical Nakshatra labels while REST keeps abbreviated labels for some entries. |
| `VEDA-DIV-CALC-000002` | `planets_present` | `EXPECTED_DOMAIN_DIFFERENCE` | `KNOWN` | REST path exposes Uranus and Neptune while personal path keeps to 9 grahas plus nodes. |
| `VEDA-DIV-CALC-000003` | `available_vargas` | `EXPECTED_DOMAIN_DIFFERENCE` | `KNOWN` | Personal path only surfaces D9 and D10, while REST exposes a broader divisional chart set. |
| `VEDA-DIV-CALC-000004` | `antardasha_surface` | `LEGACY_IMPLEMENTATION` | `KNOWN` | Personal path keeps a deeper current Mahadasha breakdown than the REST path. |
| `VEDA-DIV-CALC-000005` | `utc_normalization` | `EXPECTED_DOMAIN_DIFFERENCE` | `KNOWN` | Current path relies on a fixed or hardcoded offset instead of a zone-history-aware conversion. |
| `VEDA-DIV-CALC-000006` | `utc_normalization` | `TIMEZONE_DIFFERENCE` | `LIKELY_DEFECT` | Current path relies on a fixed or hardcoded offset instead of a zone-history-aware conversion. |
| `VEDA-DIV-CALC-000007` | `utc_normalization` | `TIMEZONE_DIFFERENCE` | `LIKELY_DEFECT` | Current path relies on a fixed or hardcoded offset instead of a zone-history-aware conversion. |
| `VEDA-DIV-CALC-000008` | `utc_normalization` | `TIMEZONE_DIFFERENCE` | `LIKELY_DEFECT` | Current path relies on a fixed or hardcoded offset instead of a zone-history-aware conversion. |
| `VEDA-DIV-CALC-000009` | `utc_normalization` | `EXPECTED_DOMAIN_DIFFERENCE` | `KNOWN` | Current path relies on a fixed or hardcoded offset instead of a zone-history-aware conversion. |
| `VEDA-DIV-CALC-000010` | `utc_normalization` | `EXPECTED_DOMAIN_DIFFERENCE` | `KNOWN` | Current path relies on a fixed or hardcoded offset instead of a zone-history-aware conversion. |
| `VEDA-DIV-CALC-000011` | `lagna_sign_boundary` | `PRECISION_DIFFERENCE` | `UNKNOWN` | The two sidereal Ascendant derivations differ by roughly 0.004° and cross a sign boundary on this sampled chart. |

Interpretation:

- Several divergences remain expected surface differences rather than outright calculation defects.
- Timezone-derived stock/country divergences are materially different and have been promoted into the issue register.
