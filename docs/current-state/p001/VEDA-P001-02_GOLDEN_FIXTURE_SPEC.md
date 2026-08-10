# VEDA-P001-02 Golden Fixture Specification

## Purpose

These fixtures freeze current deterministic astrology behavior. They do **not** certify classical correctness. They certify current application output so later phases can detect unintended changes.

## Fixture Inventory

| Fixture Class | Count | Source Path |
| --- | --- | --- |
| Personal kundli | `4` | `tests/fixtures/veda_p001/astrology_golden.json` |
| REST human kundli | `2` | `tests/fixtures/veda_p001/astrology_golden.json` |
| Stock kundli | `3` | `tests/fixtures/veda_p001/astrology_golden.json` |
| Country kundli | `2` | `tests/fixtures/veda_p001/astrology_golden.json` |
| Personal/REST divergence rows | `10` | `tests/fixtures/veda_p001/divergence_register.json` |

## Covered Cases

### Personal kundli

| ID | Input Focus |
| --- | --- |
| `personal_mumbai_1984_morning` | India, morning birth, Libra lagna case |
| `personal_london_2001_late_night` | non-India, UTC timezone, late-night boundary |
| `personal_sydney_2000_boundary_midnight` | southern hemisphere, near-midnight case |
| `personal_newyork_1969_evening` | historical pre-1970 case, western hemisphere |

### REST human kundli

| ID | Input Focus |
| --- | --- |
| `rest_human_mumbai_1984_morning` | direct comparison with personal path |
| `rest_human_london_2001_late_night` | direct comparison with personal path |

### Stock kundli

| ID | Source |
| --- | --- |
| `stock_reliance` | cached stock kundli corpus |
| `stock_tcs` | cached stock kundli corpus |
| `stock_hdfcbank` | cached stock kundli corpus |

### Country kundli

| ID | Notes |
| --- | --- |
| `country_india` | stable country chart path |
| `country_usa` | stable country chart path |

## Frozen Fields

The golden files snapshot deterministic fields only:

- Julian date
- ayanamsha
- lagna sign, degree, full longitude, lord
- planet longitudes
- sign placements
- house placements
- nakshatra, pada, nakshatra lord
- dignity
- retrograde status
- combust flag on personal path
- selected dasha blocks
- available varga/divisional chart surface
- D9 and D10 mappings
- yoga names
- dosha names
- astro score and astro action

Volatile natural-language report text is intentionally excluded.

## Tolerance Policy

| Output Type | Tolerance |
| --- | --- |
| `julian_date` | `0.0002` |
| `ayanamsha` | `0.0002` |
| `longitude` / `full_longitude` | `0.001` |
| `degree` | `0.01` |
| `astro_score` | `0.1` |

## Execution

Generate fixtures:

```bash
py -3.11 scripts/generate_p001_astrology_fixtures.py
```

Validate fixtures:

```bash
py -3.11 -m pytest tests/test_veda_astrology_golden.py -q
```

## Cache Behavior Coverage

`tests/test_veda_astrology_golden.py` also verifies that `/api/stocks/RELIANCE/kundli` uses the cached stock kundli artifact rather than forcing a live recomputation for a known cached symbol.
