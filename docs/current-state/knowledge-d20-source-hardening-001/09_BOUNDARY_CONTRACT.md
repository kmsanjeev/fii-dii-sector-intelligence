# Boundary Contract

The source does not specify software floating-point boundary semantics. VEDA's existing implementation contract is retained for diagnostic comparison:

- normalized longitude domain: `[0, 360)`;
- each sign occupies `[0°, 30°)`;
- each D20 division occupies a lower-inclusive, upper-exclusive interval;
- division index uses exact Decimal floor at 1.5° increments;
- 30° hands off to the next sign;
- 29°59'… remains in the twentieth division;
- no special D20 boundary engine is introduced.

These are deterministic implementation semantics, not newly promoted classical claims.
