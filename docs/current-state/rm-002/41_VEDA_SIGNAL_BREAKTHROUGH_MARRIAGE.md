# VEDA-SIGNAL-BREAKTHROUGH-001 â€” Marriage signal

Status: `COMPLETED_WITH_SOURCE_GOVERNABLE_SIGNAL`
Date: 2026-08-16
Parent: `VEDA-RM-002`, `VEDA-EMP-050`

## Decision

The first narrow source-governable event signal is:

`VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001` (`1.0.0`)

It is a research and bounded-pilot contract, not a production prediction
rule. Its event family is `MARRIAGE`; its method is a D1 Vimshottari
Mahadasha lord condition. The source-backed positive condition is that the
Mahadasha lord occupies, aspects, or owns the seventh house. Missing or
insufficient chart facts produce `SIGNAL_INDETERMINATE`.

The deterministic contract hash is:

`b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080`

No EMP-025 outcome, holdout case, chart fit, or model result was used to select
the rule. The marriage sample is currently zero, so the pilot is **not ready**.

## Passage-level basis

The primary passage is Phaladeepika, Chapter 11, marriage verses 13â€“14, in the
available translation. Verse 13 describes marriage during the Dasha of a
planet occupying, aspecting, or owning the seventh house. Verse 14 adds a
stronger-lord and Jupiter-transit refinement. The source is historical and
conditional; it does not establish a universal modern marriage outcome or
day-level event detector.

- [Phaladeepika marriage passage, verses 13â€“14](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/144)
- [Brihat Parashara Hora Shastra translated edition](https://www.iswaryajyotisha.com/pages/library.php?book=Brihat+parspara+hora+sastra), used for corroborating Dasha/Antardasha mechanics and conditional marriage context

The Jupiter transit refinement is retained as a documented optional variant,
not activated in v1. Navamsa refinement is deferred because D9 interpretation
is not source-governed for this pilot. Antardasha is contextual and not a
required positive condition in v1.

## Precision and safety contract

- Exact events are checked only against their recorded date.
- Month events are checked only at month precision.
- Year events are checked only at year precision.
- The signal does not predict spouse quality, permanence, compatibility, or
  inevitability.
- It does not upgrade `PRED-M3_OPERATIONAL_PLUS`, change P031, or activate a
  production predictor.

## Family status after the breakthrough

| Family | Status | Current decision |
|---|---|---|
| Marriage | `SOURCE_GOVERNABLE` | bounded signal contract exists; sample insufficient |
| Progeny | `SOURCE_PARTIAL` | historical/gendered birth passage needs separate governance |
| Education | `SOURCE_PARTIAL` | completion timing remains ungoverned |
| Career commencement | `SOURCE_PARTIAL` | no event-specific source contract |
| Business start | `SOURCE_THIN` | no explicit governed method |
| Relocation | `SOURCE_PARTIAL` | travel/residence sources do not define this event signal |
| Property acquisition | `SOURCE_PARTIAL` | D4 interpretation remains gated |
| Retirement | `SOURCE_THIN` | no governed detector |
| Health event | `SOURCE_PARTIAL / RESTRICTED` | clinical boundary remains active |
| Death | `SOURCE_PARTIAL / HIGH_STAKES` | no activated signal |

The next acquisition priority is independently documented marriage events with
valid birth data. No case is fabricated and no holdout is opened.

## Governance outcome

The public-role result remains frozen as
`NO_SOURCE_GOVERNABLE_PUBLIC_ROLE_SIGNAL`. EMP-050 remains 25/50 eligible,
with 25 chart-ready cases; no prospective predictions, RAG rebuild, Approved
Core promotion, production change, or predictive maturity change occurred.
