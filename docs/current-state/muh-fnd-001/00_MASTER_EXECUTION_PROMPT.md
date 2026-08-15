# VEDA-MUH-FND-001 — Master Execution Prompt

## Mission

Audit the Panchanga and electional-astrology foundations required before any
Muhurta capability is authorized. This is a knowledge-governance and readiness
activity, not a Muhurta implementation.

## Hard boundaries

- Preserve P031, P015-RX2, KNOW-SPIRIT-001 and all prior frozen states.
- Keep P032, Muhurta implementation, Prashna, LANG-002+ and D20 remediation
  unstarted unless separately authorized.
- Do not add an electional scorer, date selector, auspiciousness recommender,
  query-time chart workflow, or Prashna rules.
- Do not create a Panchanga-specific RAG store or new trust zone.
- Preserve EMP-001 as `ACTIVE_LONGITUDINAL`, predictive maturity as
  `PRED-M3_OPERATIONAL_PLUS`, and COMM-002/GROUP-001 human validation as
  `PENDING`.

## Required audit

1. Verify branch, commit, tags, clean tracked tree and ignored local files.
2. Inspect existing Panchanga, Lagna, longitude, timezone and location code,
   tests, knowledge registry, roadmap and prior readiness records.
3. Reconstruct exactly what exists: Tithi, Vara, Nakshatra, Yoga, Karana,
   Moon/Sun longitude and natal Lagna.
4. Audit missing electional dependencies: sunrise/sunset, local civil-time
   handling, event taxonomy, event-specific rules, Tarabala, Chandrabala,
   Rahu Kalam, Yamaganda, Gulika/Mandi, Abhijit, Durmuhurta, weekday and
   boundary handling, and evidence/provenance propagation.
5. Inspect classical and traditional Muhurta material. Verify actual passages
   where possible; retain `REFERENCE_NOT_VERIFIED` when exact provenance is not
   available. Never manufacture Sanskrit, verse numbers or translations.
6. Separate classical rules, traditional/commentarial variants, practitioner
   methods, modern conventions and platform safety logic.
7. Compare the audit with the current runtime without changing production
   behavior.
8. Decide readiness as `READY`, `PARTIAL` or `MISSING_FOUNDATION` for each
   dependency and record the next authorization boundary.
9. Run focused governance/runtime checks, independently review the result,
   synchronize current governance, selectively stage, commit, push and tag if
   acceptance permits.

## Acceptance outcome

The expected outcome is `PASS_WITH_CONDITION`: birth-time Panchanga facts are
available, while electional Muhurta remains `PARTIAL` until source-governed
event rules and astronomical/time-location dependencies are separately built
and validated. Prashna remains `MISSING_FOUNDATION`. No production capability
is activated by this audit.
