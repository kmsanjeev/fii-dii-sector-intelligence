# VEDA-EMP-MARRIAGE-010 — First ten marriage cases

Status: `PILOT_BLOCKED_CONTROLS_PENDING`  
Date: 2026-08-16  
Parent: `VEDA-SIGNAL-BREAKTHROUGH-001`

## Frozen signal

`VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001`, version `1.0.0`, remains frozen with
hash `b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080`.
The pilot used only the D1 seventh-house relationship and Vimshottari
Mahadasha lord. Jupiter transit and Antardasha were not added.

## Acquisition result

Ten distinct subjects were selected from the existing timed OGDB population.
Selection used birth quality, identity, event provenance, date precision,
coordinates and historical timezone usability only. No chart feature was used
for selection. All ten produced deterministic D1 chart snapshots after the
case ledger was frozen.

| Metric | Result |
|---|---:|
| candidates screened | 10 |
| birth-first | 10 |
| event-first | 0 |
| identity verified | 10 |
| marriage events | 10 |
| exact-day | 5 |
| month | 0 |
| year | 5 |
| primary sources | 0 |
| strong referenced | 6 |
| single referenced | 4 |
| chart-ready | 10 |
| Indian candidates / eligible | 0 / 0 |

The four single-reference cases remain eligible-with-conditions and should be
upgraded before any replication claim. Public biographies and referenced
material were used as event evidence; astrology websites were not used as
event evidence. The birth feed is the [OGDB timed-data download](https://opengauquelin.org/download/ogdb-time.csv.zip).

Event-source examples include [Brigitte Bardot](https://en.wikipedia.org/wiki/Brigitte_Bardot),
[Arthur Ashe](https://en.wikipedia.org/wiki/Arthur_Ashe),
[Buzz Aldrin](https://en.wikipedia.org/wiki/Buzz_Aldrin),
[Herb Alpert](https://en.wikipedia.org/wiki/Herb_Alpert),
[Charles Aznavour](https://en.wikipedia.org/wiki/Charles_Aznavour),
[James Arness](https://en.wikipedia.org/wiki/James_Arness),
[Don Ameche](https://en.wikipedia.org/wiki/Don_Ameche),
[Gaston Bachelard](https://en.wikipedia.org/wiki/Gaston_Bachelard),
[Raymond Barre](https://www.memoiresdeguerre.com/article-barre-raymond-111999106.html),
and [Konrad Adenauer’s institutional biography](https://www.kas.de/en/single-title/-/content/konrad-adenauer-lebensgeschichte-in-daten).

## Freeze and split

The deterministic split is Design: 4, Validation: 3, Holdout: 3. No subject
has multiple marriages in this pilot. Each frozen case contains a case hash,
birth record, coordinate/timezone inputs, event record, signal identity/hash,
engine revision, chart snapshot and evaluation lock.

Holdout outcomes remain masked. Controls were constructed before scoring as two
matched subject windows per case, excluding known marriage years. Shuffled,
permutation and random-time controls are prepared but not scored in this
activity.

## Pilot state

The ten-case pilot is **blocked pending independent control scoring/review**.
The visible event-side signal rate is recorded in the machine artifact, but no
event-minus-control difference is reported. The result state is
`INSUFFICIENT_SAMPLE`; ten cases are a sanity pilot only and do not establish
predictive validity.

No holdout was unsealed, no signal doctrine was changed, and no production
prediction or confidence calibration was performed.

## Governance preserved

- EMP-025 remains sealed and unchanged.
- EMP-050 general corpus remains 25/50.
- Public-role signal remains `PUBLIC_ROLE_SIGNAL_UNGOVERNABLE` and frozen.
- PRED-M4 remains `INSUFFICIENT_SAMPLE`.
- Approved Core and RAG are unchanged.
- Prospective personal marriage prediction remains `RESEARCH_RESTRICTED`.

Next automatic action: finalize independent matched-control scoring/review,
then continue toward `VEDA-EMP-MARRIAGE-025` while maintaining general EMP-050
diversity.
