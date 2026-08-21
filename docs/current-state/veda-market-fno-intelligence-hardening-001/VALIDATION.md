# Validation record

Focused FII F&O and integration tests: PASS. Focused VEDA market-provider and F&O capability tests: PASS. FII full suite: 1,359 passed initially; the only failure was the expected API baseline snapshot after adding four governed F&O operations. The baseline was regenerated and the affected 3-test contract suite then passed. VEDA platform full suite: PASS (all collected tests passed; two dependency deprecation warnings).

Live source checks: 6,452 files; latest 2026-08-19; current schema instrument counts include `STO`, `IDO`, `STF`, `IDF`; representative legacy schemas use `FUTIDX`, `FUTSTK`, `OPTIDX`, `OPTSTK`. The live output produced 214 selected futures records, separate stock/index PCR, explicit source status, and no participant-option attribution.

Real HTTP validation passed for FII F&O routes and the VEDA provider query. Deterministic direct-service hashes matched across repeated builds: `2b6f562d15ca447732c0701c1ef2ec6ec3edee80257149f17f9c4ef61573279f`. Cold construction was 16.840 seconds and five warm samples ranged from 0.097 to 0.193 seconds. Ruff passed for the new F&O service, routes, engine and tests; unrelated pre-existing lint findings remain in legacy files. Git scope validation and final acceptance are recorded separately.
