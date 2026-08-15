# Existing-State Audit

## Baseline

- Starting commit: `33296d3629907d374daa2c43fba29b2fc2f7d43a`
- Branch: `main`
- Tracked tree: clean before this activity
- Prior D20 audit tag: `veda-know-d20-001-interpretive-source-validation`

## Existing capability map

| Proposed capability | State | Reuse / decision |
|---|---|---|
| Tithi | EXISTING | Reuse `_compute_panchang`; birth-time only |
| Vara | EXISTING | Reuse local birth date; not an electional day engine |
| Nakshatra | EXISTING | Reuse Moon longitude and existing calculation validation |
| Yoga | EXISTING | Reuse birth-time Panchanga value |
| Karana | EXISTING | Reuse birth-time value and fixed/movable label |
| Sun/Moon longitude | EXISTING | Reuse calculation core |
| Natal Lagna | EXISTING | Reuse only as chart context |
| Sunrise/sunset | MISSING | New astronomical/time-location foundation required |
| Electional date/location query | MISSING | New request contract required |
| Event taxonomy | MISSING | New governed taxonomy required |
| Tarabala / Chandrabala | MISSING | Source and implementation audit required |
| Rahu Kalam/Yamaganda/Gulika | MISSING | Method and local-day boundary governance required |
| Abhijit/Durmuhurta | MISSING | Source/method and sunrise dependency required |
| Event-specific Muhurta rules | MISSING | Classical rule corpus and variant splitting required |
| Electional scoring/selection | MISSING | Must not be inferred from birth Panchanga |
| Prashna | MISSING_FOUNDATION | Separate query-time chart and method foundation required |

The current function `engines/ai/chatbot/tools/kundli_calculator.py::_compute_panchang`
explicitly computes five limbs at birth: Tithi, Nakshatra, Yoga, Karana and
Vara. It does not compute sunrise, sunset, location-specific electional
windows, Bala systems or event selection.
