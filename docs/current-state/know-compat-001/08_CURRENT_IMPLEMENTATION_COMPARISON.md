# Current Implementation Comparison

Compared against `engines/intelligence/p028r1_traditional.py` without editing it.

- Structural framework and 36 maximum: `MATCH` at reference/framework level.
- Varna: `MATERIAL_MISMATCH` risk because the code is symmetric while the inspected practitioner rule is role-directed.
- Tara: `MATERIAL_MISMATCH`; code uses one direction and binary 3/0 while inspected references describe directional/variant scoring.
- Yoni: `MATERIAL_MISMATCH`; code collapses non-identical animals to 2 while the inspected matrix distinguishes relationship classes.
- Graha Maitri: `MATERIAL_MISMATCH`; code uses simplified sets rather than the fuller score table inspected.
- Vashya, Gana, Bhakoot and Nadi: `UNVERIFIED` at source level; current deterministic behavior is not promoted as classical authority.
- 27 Nakshatra and Abhijit exclusion: method-specific policy, not passage-verified.

Engineering remediation required: YES, before any affected executable table can be promoted. This audit intentionally does not patch production code.

