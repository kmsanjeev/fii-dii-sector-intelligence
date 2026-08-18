# External Reference Register

Review date: 2026-08-18
Programme: `VEDA-LANG-002-HI-SOURCE-VALIDATION-001`

The external review uses reference classes rather than treating any one web
page as a linguistic approval gate. These sources support the relevant
language, script, terminology, calendrical and transliteration boundaries.
They do not create Jyotisha semantic truth or human presentation approval.

| Ref | Reference class | Authority and use | Accessed |
|---|---|---|---|
| EXT-HI-01 | Government terminology | [Commission for Scientific and Technical Terminology](https://www.cstt.education.gov.in/en): mandate and technical-glossary authority for Hindi/Indian-language terminology. | 2026-08-18 |
| EXT-HI-02 | Government Hindi usage | [Department of Official Language Hindi vocabulary](https://rajbhasha.gov.in/hindi-vocabulary): official Hindi dictionary/glossary catalogue and usage context. | 2026-08-18 |
| EXT-HI-03 | Devanagari/locale standard | [Unicode CLDR scripts and languages](https://unicode.org/cldr/charts/49/supplemental/scripts_and_languages.html): Hindi `hi` and Devanagari `Deva` locale identity. | 2026-08-18 |
| EXT-HI-04 | Panchanga/Jyotisha reference | [IMD Rashtriya Panchang](https://mausam.imd.gov.in/responsive/rashtriyPanchang.php): institutional Panchanga terminology and the boundary between calendrical facts and recommendations. | 2026-08-18 |
| EXT-HI-05 | Scholarly transliteration | [ISO 15919](https://www.iso.org/standard/28333.html): governed Indic-script-to-Latin transliteration reference; used to distinguish diacritic-bearing IAST values from retained ASCII aliases. | 2026-08-18 |

## Accepted conclusions

- The two authorized wording changes are applied exactly.
- `GOVERNANCE.SOURCE_CITATION` remains `स्रोत उद्धरण`; the proposed
  `स्रोत-संदर्भ` replacement is withdrawn.
- Devanagari remains presentation-only and does not alter canonical IDs,
  source IDs, trust zones, numbers, timestamps, or semantic payloads.
- Existing plain-Roman ontology values are retained as legacy aliases. IAST
  values are recorded separately only for the nine graha names where the
  source-governed transliteration metadata is explicit.
- External/source review is not human linguistic review and does not authorize
  production Hindi.
