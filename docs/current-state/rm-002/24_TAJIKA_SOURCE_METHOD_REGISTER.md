# VEDA-RM-002 Tajika Source-Method Register

Status: `PASS_WITH_CONDITION` / calculation remains blocked  
Activity: `TAJIKA_FOUNDATION`  
Date: 2026-08-16

## Question

Does the repository now have a citable annual-method witness that can support
the missing Tajika calculation contract?

## Finding

Yes, a suitable scholarly witness is now registered as `VEDA-SRC-000012`:
Martin Gansten's 2020 parallel Sanskrit-English critical edition of
Balabhadra Daivajna's *Hayanaratna*. The Lund University bibliographic record
identifies the Brill edition, DOI, ISBNs, publication year and 1044-page
scope. The open-access chapter catalogue exposes the relevant chapter
boundaries. This is a source-method register, not formula approval.

| Required contract area | Witness locator | Current status | Permitted conclusion |
|---|---|---|---|
| Annual-return chart construction | Chapter 1, *Fundamentals of Astrology and the Annual Revolution*, pp. 77-160 | `LOCATOR_VERIFIED` | Candidate source for return construction; exact convention still requires passage audit |
| Tajika aspects and dignities | Chapter 2, *Aspects and Dignities*, pp. 161-250 | `LOCATOR_VERIFIED` | Candidate source for aspect geometry/dignity definitions; no algorithm enabled |
| Tajika configurations | Chapter 3, *The Sixteen Configurations*, pp. 251-354 | `LOCATOR_VERIFIED` | Candidate source for named configurations; no yoga claim promoted |
| Sahamas | Chapter 4, *The Sahamas*, pp. 355-422 | `LOCATOR_VERIFIED` | Candidate source for lot definitions; no formula extracted |
| Annual lord | Chapter 5, *The Ruler of the Year and Related Matters*, pp. 423-556 | `LOCATOR_VERIFIED` | Candidate source for annual-lord method; selection convention remains unresolved |
| Muntha | Chapter 1 and Chapter 5; exact passage locator pending | `SOURCE_SCOPE_IDENTIFIED` | Named dependency retained; no progression formula inferred |

## Governance decision

This closes the missing-edition discovery dependency but does not close the
calculation dependency. The edition is `METADATA_VERIFIED`, not
`PASSAGE_VERIFIED`; the repository must not infer formulas from chapter titles,
secondary summaries, or search snippets. No runtime, prediction, empirical
case, prospective subject, Approved Core rule, or RAG promotion is authorized.

The existing Hayanaratna travel evidence remains method-scoped and is not
silently broadened into a universal natal or settlement rule. The annual
forecasting trust chain remains:

`source -> inspectable passage -> normalized contract -> deterministic fixture -> expert review -> gated research use`

## Validation

- `scripts/validate_p002_astrology_registry.py`: expected to validate 12 source records with no registry errors.
- Source identity and chapter boundaries were checked against the Lund University record and open-access JSTOR catalogue.
- Brill PDF fetch returned HTTP 403 in this environment; no inaccessible text was represented as extracted evidence.
- No Sanskrit quotation, formula, calculation fixture, empirical record, prospective record, or production behavior was created.

## Resumable next step

`TAJIKA_PASSAGE_AUDIT`: inspect the legally accessible chapter witnesses and
register passage-level records for annual-return construction, Muntha, annual
lord, Tajika aspects, and Sahamas. Preserve school variance and keep all
unverified items blocked.
