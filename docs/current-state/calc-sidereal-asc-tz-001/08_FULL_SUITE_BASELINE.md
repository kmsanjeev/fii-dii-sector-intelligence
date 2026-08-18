# Full-suite and Regression Validation

The canonical OpenAPI contract snapshot was regenerated using `scripts/generate_p001_api_baseline.py` because the live application’s 140 paths/153 operations were conclusively newer than the historical 129/141 fixture. The twelve authorized empirical routes are represented by the canonical generator; no manual fixture edit was used.

Required validation results are recorded after execution in this file and in the final acceptance register. A timeout is never reported as a pass. Parent Goldset, Silver, Stress and Oracle artifacts remain immutable comparison baselines.

Validation history:

- An initial quiet `py -3.11 -m pytest -q` run reached its 900-second execution limit. This is recorded as a timeout, not a pass.
- A verbose `--maxfail=1` run reached 365 passed tests before finding stale P013 exported capability artifacts. The current P013 exporter was run; it wrote 30 canonical files and `validate_exported_bundle` returned `is_valid=True`. The drift was a generated-baseline mismatch: the current Muhurta foundation has 148 dependency edges and explicit date/location/timezone/sunrise/sunset facts, while the older export had 145 edges and transit/lagna placeholders.
- The next verbose run reached 539 passed tests before finding stale ignored P005 interpretation artifacts. The current yoga output was checked across five independent Python hash-seed processes and was identical. The P005 exporter was rerun and its validator returned `is_valid=True`; no production interpretation logic was changed.
- Focused cross-programme regression after both repairs: `50 passed in 9.13s`.
- Final full suite: `956 passed, 1 warning in 732.68s (0:12:12)`, exit code 0. The warning is the existing Starlette/httpx deprecation warning; it did not fail the suite.

The generated P013 artifacts and unified RAG snapshots are included only where their canonical current-state output changed. Ignored P005 validation artifacts remain local and are not promoted into the repository. Parent Goldset rerun remained `Silver 109/109`, `Stress 7022/7022`; Gold remains `23/25` with the two governed unresolved cases.
