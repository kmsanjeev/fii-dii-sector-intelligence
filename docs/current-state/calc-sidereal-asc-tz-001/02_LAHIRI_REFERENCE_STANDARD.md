# Lahiri / Nirayana Reference Standard

## Runtime configuration audited

- Sidereal mode: `SIDM_LAHIRI`.
- Backend policy: explicit `MOSEPH`; unauthorized fallback remains rejected.
- Runtime Ascendant path: Swiss `houses(..., b"W")` followed by explicit ayanamsha subtraction; whole-sign downstream assignment remains unchanged.
- D20 interpretation: not validated and not enabled by this activity.

## IMD bounded comparison

The 2026 IAE Indian Calendar headings provide six “Ayanamsa on 1st” values. The values are within approximately five arcseconds of the Swiss `SIDM_LAHIRI` values at the corresponding fixed UTC dates. The differences are compatible with unresolved publication-time, frame, apparent/geometric and implementation-convention differences; they are not a basis for changing the runtime.

The complete all-body Nirayana regression in `02_NIRAYANA_REGRESSION.json` is explicitly `SAME_ENGINE_REFERENCE_LIMITATION` with `IMD_BOUNDED_AYANAMSHA_ONLY`. It is a deterministic decomposition/regression artifact, not a claim of independent all-body validation.

## Decision

`REFERENCE_STANDARD_PARTIALLY_RESOLVED`. Retain `SIDM_LAHIRI`; do not migrate or change production calculations. A future fully independent all-body Nirayana oracle would require a reference set with matched body, frame, epoch, time-scale and apparent/geometric conventions.
