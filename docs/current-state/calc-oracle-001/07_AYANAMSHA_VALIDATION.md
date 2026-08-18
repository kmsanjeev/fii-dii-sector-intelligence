# Ayanamsha validation

The production standard remains Lahiri/Chitrapaksha through Swiss Ephemeris. The oracle does not independently validate Lahiri against a second sidereal implementation. Therefore the status is `INTERNAL_CONFIGURATION_VALIDATED`, not `EXTERNAL_REFERENCE_VALIDATED`.

The oracle explicitly initializes `SIDM_LAHIRI` before calling `houses_ex(..., FLG_SIDEREAL)`. This reproduces the frozen P004 reference values and avoids a process-global sidereal-mode ambiguity.

