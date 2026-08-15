# VEDA-RM-002 Method Comparison — Muhurta Event Input

Status: `PASS_WITH_CONDITION`  
Activity: `METHOD_COMPARISON`  
Date: 2026-08-16

## Question

Which two legitimate Muhurta methods produce the better-governed result for a
shared comparison input after the new edition metadata was registered?

## Compared methods

| Method | Evidence status | Permitted result |
|---|---|---|
| Scoped classical event-action families | `VALIDATED_KNOWLEDGE`, event-scoped | Qualitative action-class evidence for the relevant nakshatra, tithi or karana; no universal score or recommendation |
| Personal Tarabala/Chandrabala route | `RESEARCH_CANDIDATE`, `REFERENCE_NOT_VERIFIED` | No executable result; retain as a named research variant pending passage and formula verification |

The second method is represented by the *Muhurta Chintamani* lineage lead
registered as `VEDA-SRC-000011` (1928 *Pramitakshara* commentary edition).
The catalogue record verifies bibliographic identity only; it does not expose
an inspectable operative passage or formula.

## Shared deterministic input

Both methods were evaluated against the same labeled input contract: a
Muhurta request for `2026-08-15`, Mumbai (`19.0760, 72.8777`),
`Asia/Kolkata`, event family `MARRIAGE`. This is a deterministic calculation
fixture, not an empirical case, prospective subject, outcome, or prediction.

## Result

The methods cannot be compared numerically without inventing the personal-Bala
formula. The scoped classical route has admissible source-governed semantics;
the personal-Bala route returns `NOT_IMPLEMENTED` / `REFERENCE_NOT_VERIFIED`.
Therefore no agreement rate, suitability score, event window, or
recommendation is reported.

## Decision

The scoped classical event-action family is the better-governed method for this
shared input because its evidence is passage-scoped and its interpretation is
explicitly bounded. Tarabala and Chandrabala remain named research variants,
not fallback methods and not interchangeable inputs. The new edition metadata
does not authorize formula extraction, runtime activation, Approved Core
promotion, or predictive use.

## Validation and trust boundary

- P002 source registry validator: `PASS` (`11` sources, `13` passages,
  `13` claims, `0` errors, `0` warnings).
- Focused Muhurta/governance tests: `12 passed`.
- No Sanskrit quotation, formula, implementation, empirical record,
  prospective record, or production behavior changed.
- Human-validation statuses and inactive electional output are preserved.

## Resumable next step

`MUHURTA_EDITION_PASSAGE_AUDIT`: obtain a legally inspectable witness and
verify chapter/page/verse locators for the personal-Bala definitions before
attempting a numerical method comparison.
