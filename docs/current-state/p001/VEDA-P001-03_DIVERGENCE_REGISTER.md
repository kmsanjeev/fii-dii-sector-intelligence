# VEDA-P001-03 Divergence Register

## Scope

This register captures current known differences between the personal kundli chat path and the REST human kundli path. The purpose is measurement, not convergence. No attempt was made in P001 to make the two paths identical.

## Compared Paths

- `personal_kundli_chat_path` -> `engines/ai/chatbot/tools/kundli_calculator.py::compute_personal_kundli`
- `rest_human_kundli_path` -> `engines/intelligence/kundli_engine.py::KundliEngine.compute_human`

## Divergence Rows

| DIVERGENCE_ID | Case | Field | Output A | Output B | Status | Known Reason |
| --- | --- | --- | --- | --- | --- | --- |
| `MUMBAI_1984-D01` | `mumbai_1984` | `planets_present` | 9 grahas + nodes | 9 grahas + nodes + `Uranus`, `Neptune` | `KNOWN` | REST path exposes additional outer planets |
| `MUMBAI_1984-D02` | `mumbai_1984` | `rahu_dignity` | `friendly` | `exalted` | `KNOWN` | Different node dignity treatment |
| `MUMBAI_1984-D03` | `mumbai_1984` | `yoga_names` | `Sasa Yoga`, `Kemadruma Yoga` | finance-oriented yoga set including `Raja Yoga`, `Kemdrum` | `KNOWN` | Different interpretation layer |
| `MUMBAI_1984-D04` | `mumbai_1984` | `available_varga_surface` | `d9_navamsa`, `d10_dasamsa` | broader divisional chart set including `D1..D60` subset | `KNOWN` | REST path exposes wider divisional surface |
| `MUMBAI_1984-D05` | `mumbai_1984` | `all_antardashas_presence` | `true` | `false` | `KNOWN` | Personal path returns deeper dasha detail |
| `LONDON_2001-D01` | `london_2001` | `planets_present` | 9 grahas + nodes | 9 grahas + nodes + `Uranus`, `Neptune` | `KNOWN` | REST path exposes additional outer planets |
| `LONDON_2001-D02` | `london_2001` | `rahu_dignity` | `exalted` | `neutral` | `KNOWN` | Different node dignity treatment |
| `LONDON_2001-D03` | `london_2001` | `yoga_names` | empty set | includes `Raja Yoga`, `Parivartana` | `KNOWN` | Different interpretation layer |
| `LONDON_2001-D04` | `london_2001` | `available_varga_surface` | `d9_navamsa`, `d10_dasamsa` | broader divisional chart set including `D1..D60` subset | `KNOWN` | REST path exposes wider divisional surface |
| `LONDON_2001-D05` | `london_2001` | `all_antardashas_presence` | `true` | `false` | `KNOWN` | Personal path returns deeper dasha detail |

## Operational Meaning

- The current application contains overlapping kundli engines, not a single unified result surface.
- Both paths are now regression-protected in their current form.
- Any later convergence work belongs to a later phase and must preserve both baselines until an explicit replacement decision is approved.

## Verification

```bash
py -3.11 -m pytest tests/test_veda_astrology_golden.py -q
```
