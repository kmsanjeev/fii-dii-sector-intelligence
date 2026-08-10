# VEDA-P005 Vimshottari Interpretation Validation

| Rule ID | Source Status | Domain | Current Logic |
| --- | --- | --- | --- |
| `VEDA-P005-DASHA-0001` | `LEGACY_PARTIALLY_SOURCED` | `PERSONAL_REPORT` | kundli_calculator::_dasha_interpretation chooses text by planet themes, dignity, and lagna-specific functional nature. |
| `VEDA-P005-DASHA-0002` | `LEGACY_UNSOURCED` | `PERSONAL_CURRENT_PERIOD` | kundli_interpreter::_combined_dasha_reading combines Mahadasha and Antardasha planet-theme tables with dignity and yogakaraka overrides. |
| `VEDA-P005-DASHA-0003` | `HEURISTIC` | `PERSONAL_LIFE_GUIDE` | kundli_life_guide::_rate_dasha scores upcoming Mahadashas by functional lordship, dignity, house, combustion, and natural benefic/malefic character. |
| `VEDA-P005-DASHA-0004` | `ASTROFINANCE_HYPOTHESIS` | `STOCK_FINANCE` | kundli_interpretator::DASHA_FINANCIAL maps each Mahadasha planet to a finance-market sentence used in bullish/bearish factors and dasha outlook. |
| `VEDA-P005-DASHA-0005` | `SOURCE_VALIDATED` | `PERSONAL_AND_REST_SELECTION` | Current Mahadasha, Antardasha, and Pratyantardasha are surfaced from the deterministic Vimshottari timeline without additional narrative transformation. |

Key distinction:

- P004 validated the deterministic Vimshottari calculation layer.
- P005 shows that the descriptive meaning attached to those periods is still mostly heuristic or legacy-unsourced.
- Only the period-selection baseline currently links through the P002/P003 governed chain.
