# VEDA-P005 AstroFinance Validation

| Rule ID | Classification | Current Formula | Empirical Support |
| --- | --- | --- | --- |
| `VEDA-P005-AF-0001` | `MODERN_ASTROLOGY` | Hardcoded sector -> ruling planets mapping in SECTOR_RULERS | NONE_IN_REPOSITORY |
| `VEDA-P005-AF-0002` | `TRADITIONAL_INTERPRETIVE` | Sign-strength scoring: exalted +4, own sign +3, neutral 0, enemy/debilitated negative | NONE_IN_REPOSITORY |
| `VEDA-P005-AF-0003` | `ASTROFINANCE_HYPOTHESIS` | Retrograde penalty, aspect contributions, Moon contribution, eclipse penalty/boost, then action thresholds | NONE_IN_REPOSITORY |
| `VEDA-P005-AF-0004` | `ASTROFINANCE_HYPOTHESIS` | Eclipse type Rahu -> hold/uptrend potential, Ketu -> avoid/downtrend pressure | NONE_IN_REPOSITORY |
| `VEDA-P005-AF-0005` | `INTERNAL_HEURISTIC` | Frontend buildPlainReason restates astro_action into explanatory prose | NOT_APPLICABLE |

Boundary:

- AstroFinance is active and production-wired.
- AstroFinance is not classical natal Jyotisha in the current repository.
- AstroFinance source handling remains modern-only and outside the P002 registry at this point.
