# VEDA-RM-002 Muhurta Source Expansion

Status: `PASS_WITH_CONDITION`  
Activity: `MUHURTA_SOURCE_EXPANSION`  
Date: 2026-08-16

## Question

Which missing Muhurta source family resolves a documented dependency?

## Bounded finding

The source family is now better specified, but the documented dependency is
not resolved. A stable CiNii bibliographic record identifies a 1928 Sanskrit
edition of *Muhurta Chintamani* with Anupa Misra's *Pramitakshara* commentary,
attributed to Rama Daivajna. A British Library catalogue record independently
identifies a *Muhurta Chintamani* witness with the *Piyush Dhara* commentary.

These records provide acquisition and edition-lineage leads. They do not make
Tarabala or Chandrabala formulas passage-verified: no operative Sanskrit page,
critical apparatus, translation, or reproducible locator was inspected in this
activity. The existing OCR scan therefore remains unusable for formula
extraction, and the new source record is `METADATA_VERIFIED` only.

## Source register delta

| Source | Evidence inspected | Status | Permitted use |
|---|---|---|---|
| *Muhurta Chintamani* with *Pramitakshara* commentary, 1928 | CiNii bibliographic record, identifier BA46170738 | `METADATA_VERIFIED` | Edition acquisition target; no rule extraction |
| *Muhurta Chintamani* with *Piyush Dhara* commentary | British Library catalogue record EAP886/1/26 | Discovery metadata | Witness-lineage lead; no rule extraction |

URLs: [CiNii record](https://ci.nii.ac.jp/ncid/BA46170738); [British Library
catalogue record](https://searcharchives.bl.uk/catalog/040-003690161).

## Decision and trust boundary

- Tarabala and Chandrabala remain `RESEARCH_CANDIDATE` /
  `REFERENCE_NOT_VERIFIED`.
- No Sanskrit quotation, translation, algorithm, scoring, recommendation or
  event suitability rule was added.
- No runtime, RAG, empirical, prospective, Approved Core or predictive state
  changed.
- The new source record is metadata-only and does not authorize promotion.

## Validation

- P002 source registry validator: **PASS** (`11` sources, `13` passages,
  `13` claims, `0` errors, `0` warnings), run with the installed Python 3.11
  executable because the `py -3.11` launcher reported no installed runtime.
- No provider call, empirical case, prospective subject, or prediction was
  created.
- Existing human-validation and inactive Muhurta statuses are preserved.

## Resumable next step

`MUHURTA_EDITION_PASSAGE_AUDIT`: obtain a legally inspectable scan or edition
of the registered *Muhurta Chintamani* witness and verify chapter/page/verse
locators for personal-Bala definitions before considering any claim promotion.
