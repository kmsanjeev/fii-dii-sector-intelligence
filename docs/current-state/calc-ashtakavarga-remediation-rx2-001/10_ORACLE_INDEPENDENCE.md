# Oracle independence

The reference evaluator in `scripts/veda_calc_ashtakavarga_remediation_rx2_001.py` loads the governed 768-cell JSON matrix and computes relative positions independently. It does not import the production table or production BAV/SAV functions for expected values. Production is imported only for comparison. External numerical oracle status remains `UNAVAILABLE`; this establishes source-contract conformance only.
