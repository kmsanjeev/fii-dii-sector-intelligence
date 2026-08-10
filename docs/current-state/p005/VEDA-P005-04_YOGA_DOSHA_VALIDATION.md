# VEDA-P005 Yoga & Dosha Validation

Yogas:

| Name | Surfaces | Source Status | Recommendation | Current Conditions |
| --- | --- | --- | --- | --- |
| Hamsa Yoga | personal | `LEGACY_UNSOURCED` | `KEEP_WITH_CAVEAT` | Jupiter dignified and in H1/H4/H7/H10 |
| Malavya Yoga | personal | `LEGACY_UNSOURCED` | `KEEP_WITH_CAVEAT` | Venus dignified and in H1/H4/H7/H10 |
| Bhadra Yoga | personal | `LEGACY_UNSOURCED` | `KEEP_WITH_CAVEAT` | Mercury dignified and in H1/H4/H7/H10 |
| Ruchaka Yoga | personal | `LEGACY_UNSOURCED` | `KEEP_WITH_CAVEAT` | Mars dignified and in H1/H4/H7/H10 |
| Sasa Yoga | personal | `LEGACY_UNSOURCED` | `KEEP_WITH_CAVEAT` | Saturn dignified and in H1/H4/H7/H10 |
| Gaja Kesari | personal, rest, stock, country | `SOURCE_CANDIDATE_FOUND` | `RESEARCH_FURTHER` | Jupiter in a kendra from Moon; stock path labels conjunction as strong |
| Dhana Yoga | personal, stock, country | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | Personal path uses 2H/11H placement shortcuts; stock path checks both lords in 1/2/5/9/11 |
| Raja Yoga | stock, country, rest_human | `LEGACY_UNSOURCED` | `REWRITE_LATER` | Kendra lord and trikona lord conjunct in same house |
| Viparita Raja | stock, country | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | At least two of the 6H/8H/12H lords occupy 6/8/12 |
| Neecha Bhanga | personal, stock, country | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | Cancellation via debility-sign lord in kendra; stock path also checks Moon-relative kendra pattern |
| Kaal / Kala Sarpa | personal, stock, country | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | All seven classical planets fall inside the Rahu/Ketu arc; personal and stock use different arc tests |
| Kemadruma / Kemdrum | personal, stock, country, rest_human | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | No adjacent-house or adjacent-sign support around the Moon depending on path |
| Parivartana | stock, country | `LEGACY_UNSOURCED` | `KEEP_WITH_CAVEAT` | Two planets occupy each other's own signs |

Doshas:

| Name | Source Status | Recommendation | Current Conditions |
| --- | --- | --- | --- |
| Manglik Dosha | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | Mars in H1/H2/H4/H7/H8/H12 |
| Shani Dosha | `LEGACY_UNSOURCED` | `REWRITE_LATER` | Saturn in H1/H4/H7 plus Moon-relative mild variant |
| Surya Chandal Dosha | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | Sun and Rahu in same house |
| Guru Chandal Dosha | `LEGACY_UNSOURCED` | `RESEARCH_FURTHER` | Jupiter and Rahu in same house |
| Shani-Chandra Yoga | `LEGACY_UNSOURCED` | `KEEP_WITH_CAVEAT` | Moon and Saturn in same house |

Observations:

- Personal and stock paths use different yoga catalogs and different condition logic.
- `Kaal Sarp` versus `Kala Sarpa` is a naming and algorithm divergence, not just spelling.
- No yoga or dosha currently reaches a research-grade, source-linked implementation state.
