# Release-gate design

| Gate | Purpose | Command/path policy | Authority |
|---|---|---|---|
| Fast Core | import, governance, safety and calculation smoke | catalog utility `--mode gate --group CALCULATION` plus selected core tests | supplement |
| Domain Regression | Muhurta, domain and language regressions | explicit catalog groups | supplement |
| Full Deterministic | all repository tests with no external authorization | `py -3.11 -m pytest -q` | authoritative |
| External/Integration | provider/model/API smoke and live access | explicit, bounded, separately reported | never silently merged |

`scripts/veda_engineering_test_suite_performance_rx1_001.py` is the canonical
catalog/runner. A timeout is reported as `TIMEOUT`, not pass. Logical gates do
not replace the full deterministic gate.
