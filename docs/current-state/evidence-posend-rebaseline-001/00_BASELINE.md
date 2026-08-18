# VEDA-EVIDENCE-POSEND-REBASELINE-001 - Baseline

## Scope

This is a feature-blind, astrology-blind, ML-free redesign of the existing
`POSITION_END` evidence lane. It audits outcome definition, precision,
provenance, independence, risk intervals, holdout protection and future study
design. No chart, Dasha, transit, Varga or feature value was calculated.

Starting commit: `2211e1cfe64fd10e89df7a204d9d67ecf1fac5fe`.

The authoritative inputs were:

- `emp-posend-acq-001/02_COHORT_FREEZE.json`
- `emp-posend-acq-001/03_CONTROL_FREEZE.json`
- `emp-feature-003/02_FEATURE_FAMILY_REGISTRY.json`
- `evidence-rebaseline-001/03_POWER_SENSITIVITY.json`
- the current roadmap rebaseline and master-state records.

The cohort contains 20 independently selected birth-first subjects and 20
primary events. The existing 14/6 validation/holdout split is retained exactly.
All dates are recorded as YEAR precision. The feature-family hash is retained
as metadata only: `da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297`.

## Existing-state reconciliation

The acquisition record says one `RETIREMENT` event per subject, but the event
labels describe professional career ends. That is not equivalent to a formal
effective role-end date. The redesigned governed subtype is therefore
`CAREER_END_INFERRED` until documentary evidence supports a narrower event
definition.

The event source mix is 2 Tier A, 7 Tier B and 11 Tier C under the inherited
evidence standard. Eighteen records resolve to the same Wikipedia upstream
dependence cluster; the two remaining records use institutional sources. This
is a provenance/generalizability warning, not a claim that the raw N is 3.

The earlier acquisition and evidence documents are historical records and are
not rewritten. Their premature `EMP-FEATURE-003-R1` handoff is superseded for
current work by this redesign decision.

## Bounded source-resolution pass

The Baseball Hall of Fame page for Hank Aaron was checked: it reports team
career ranges through 1976, but no effective day or month for career cessation.
The French Football Federation page for Claude Abbes was checked: it lists
club activity through June 1967, while the acquired record labels 1962 as a
professional-career end. This is an unresolved event-definition conflict, not
a license to substitute an easier date.

The remaining 18 pages are secondary/structured biography references. They were
not treated as independent precision upgrades. The bounded stop rule therefore
closes recovery with 0 day upgrades, 0 month upgrades, 20 unchanged YEAR
records and 1 unresolved event-definition conflict.

## Governance result

The current cohort is useful for exploratory feasibility and acquisition
architecture only. It is not a confirmatory exact-day corpus. No raw provider
data, feature outputs, activation records or control dates were created or
committed.
