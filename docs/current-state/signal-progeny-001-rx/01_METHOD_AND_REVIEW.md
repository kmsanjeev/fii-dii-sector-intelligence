# Method, Controls, and Review

The audit uses the Open Gauquelin Database timed-birth download in deterministic
OGID order. Rows without a usable historical timezone, coordinates, place or
minute-level time are excluded before chart construction. This is a mechanics
sample, not an outcome cohort.

The observation interval is fixed at ages 18 through 70, matching
EMP-PROGENY-010. Activation duration is measured as the overlap of the frozen
D1 structural gate and Jupiter Mahadasha/Sun Antardasha intervals with that
window. Negative contract conditions remain blocking; missing required facts
remain indeterminate.

Fixed thresholds were declared before population scoring:

- at least 10%: `NORMAL_PREVALENCE`
- 3% to below 10%: `LOW_PREVALENCE`
- 1% to below 3%: `VERY_LOW_PREVALENCE`
- above 0% and below 1%: `NEAR_ZERO_PREVALENCE`
- exactly 0%: `ZERO_PREVALENCE`

The 1,000-row run produced 999 analyzable subjects. A second deterministic
generation was byte-identical. Focused tests passed: `9 passed`.

No childbirth outcome source was accessed by the audit script. The public OGDB
source describes timed birth records and is available at
https://opengauquelin.org/.
