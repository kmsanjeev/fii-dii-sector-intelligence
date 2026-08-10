# VEDA-P005 Domain Validation

| Domain | Status | Source Coverage | Varga Use | Dasha Use | Transit Use | Confidence | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAREER | `FUNCTIONAL_UNSOURCED` | NONE | D10 displayed but not actually interpreted in personal runtime | Yes | Stock path only | LOW | `SOURCE_AND_MIGRATE` |
| FINANCE | `HEURISTIC` | NONE | No active varga confirmation | Yes | Stock path yes | LOW | `RESEARCH_FURTHER` |
| MARRIAGE | `FUNCTIONAL_UNSOURCED` | NONE | D9 displayed but not applied inside the marriage section | Timing mention only | No | LOW | `SOURCE_AND_MIGRATE` |
| CHILDREN | `FUNCTIONAL_UNSOURCED` | NONE | No D7 usage | Timing mention only | No | LOW | `SOURCE_AND_MIGRATE` |
| HEALTH | `FUNCTIONAL_UNSOURCED` | NONE | No | Indirect | No | LOW | `REWRITE_AFTER_RESEARCH` |
| LONGEVITY | `HEURISTIC` | NONE | No | Maraka warning only | No | VERY_LOW | `REWRITE_AFTER_RESEARCH` |
| REMEDIES | `HEURISTIC` | NONE | No | No | No | VERY_LOW | `RESEARCH_FURTHER` |
| EDUCATION | `FUNCTIONAL_UNSOURCED` | NONE | No D24 usage | No | No | LOW | `SOURCE_AND_MIGRATE` |
| HOME_AND_FAMILY | `FUNCTIONAL_UNSOURCED` | NONE | No | No | No | LOW | `SOURCE_AND_MIGRATE` |
| SIBLINGS_AND_COURAGE | `FUNCTIONAL_UNSOURCED` | NONE | No | No | No | LOW | `SOURCE_AND_MIGRATE` |
| FATHER_AND_FORTUNE | `FUNCTIONAL_UNSOURCED` | NONE | No | No | No | LOW | `SOURCE_AND_MIGRATE` |
| SPIRITUALITY | `FUNCTIONAL_UNSOURCED` | NONE | No | Indirect | Sade Sati note in life guide only | LOW | `SOURCE_AND_MIGRATE` |
| ASTROFINANCE | `HEURISTIC` | MODERN_ONLY | Not applicable | No | Yes | LOW | `KEEP_AS_ASTROFINANCE_EXPERIMENT` |

Interpretation:

- Marriage, finance, and career are implemented, but they remain unsourced at rule level.
- Health, longevity, and remedies are active and require tighter future governance because of the stakes.
- Education, home/family, siblings, father/fortune, and spirituality are present as deterministic prose sections rather than governed rule sets.
