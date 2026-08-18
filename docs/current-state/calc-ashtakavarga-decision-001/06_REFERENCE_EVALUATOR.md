# Independent Reference Evaluator

`scripts/veda_calc_ashtakavarga_decision_001.py` loads the existing governed source matrix JSON and independently implements only: (1) target-to-contributor relative sign indexing, (2) source bindu lookup, (3) contributor-sign placement, and (4) seven-target SAV summation. It does not import `BAV_CONTRIBUTIONS`, `calculate_bav`, or `calculate_sav` for reference evaluation. Production functions are imported only in the comparison path.

The evaluator uses synthetic deterministic charts only. No personal birth data or predictive outcome is used.
