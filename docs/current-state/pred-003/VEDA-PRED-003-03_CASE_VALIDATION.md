# Case Validation

The shared research SQLite database now supports normalized cases with qualitative quality states `HIGH`, `MODERATE`, `LOW`, and `UNVERIFIED`. Empirical eligibility requires `HISTORICAL_VERIFIED` or `PROSPECTIVE_VERIFIED`, moderate/high quality, `VALID` leakage status, and an outcome. Duplicate case families and repeated source families are not counted independently.
