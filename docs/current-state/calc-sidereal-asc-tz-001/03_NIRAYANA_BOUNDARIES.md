# Nirayana, Rashi, Nakshatra and Pada Validation

The harness evaluates 32 fixed dates across 1850–2026 and seven bodies, producing 224 deterministic tropical → Lahiri ayanamsha → Nirayana rows. Rashi, Nakshatra and Pada labels are derived with explicit equal divisions:

- Rashi: 12 × 30°.
- Nakshatra: 27 × 13°20′.
- Pada: 108 × 3°20′.
- Lower endpoint inclusive; upper endpoint exclusive; 360° wraps to 0°.

Boundary tests cover all 12 Rashi, 27 Nakshatra and 108 Pada boundaries at ±0.1°, ±0.01°, ±0.005° and ±0.001°. The exact boundary convention is encoded in the harness and tested; it is not inferred from rounded display output.

This validates deterministic classification and boundary behavior. It does not promote an interpretation, D20 use, or an external all-body sidereal oracle.
