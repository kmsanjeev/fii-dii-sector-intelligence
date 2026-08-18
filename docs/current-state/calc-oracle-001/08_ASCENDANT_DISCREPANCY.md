# Ascendant discrepancy and decision

The independent GMST/mean-obliquity formula agrees with Swiss tropical `houses()` within 0.01° for both frozen boundary cases. After explicit Lahiri initialization, the `houses_ex` values reproduce the parent reference exactly:

| Case | Frozen/reference sidereal Ascendant | Runtime `houses()` minus ayanamsha | Result |
|---|---:|---:|---|
| VEDA-FIX-CALC-000005 | 179.9959072113° | 180.0000608135° | known boundary sign flip |
| VEDA-FIX-CALC-000006 | 149.9988035456° | 150.0024586365° | known boundary sign flip |

Root cause of the earlier oracle mismatch: the standalone comparison did not set the process-global Lahiri sidereal mode. That is repaired in the oracle only. The remaining approximately 0.004° runtime/reference difference is the already-registered numerical boundary behavior between the runtime’s `houses()` plus ayanamsha subtraction and the sidereal `houses_ex` reference. No production output correction is accepted by this programme.

Decision: `REFERENCE_REPRODUCED_RUNTIME_BOUNDARY_REMAINS`; this is not a calculation defect.

