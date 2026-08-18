# Full-suite baseline

The parent baseline full suite remains conditionally failing only at the stale `tests/test_api_contract_baseline.py` snapshot. The live generated API contract contains the twelve authorized empirical intake paths added after the fixture was frozen. No calculation-oracle change altered those paths, so the fixture is deliberately not rewritten in this activity.

Focused calculation and VEDA regression suites are the acceptance evidence for this scope. A full-suite rerun is recorded in the final acceptance register with the same out-of-scope stale-fixture classification if it reproduces.

