# Acceptance register

| Gate | Result | Evidence |
|---|---|---|
| Existing engines/data reused | PASS | Implementation inventory |
| F&O and cash kept separate | PASS | Data inventory and contract |
| 1D/3D/5D/10D/20D windows explicit | PASS | Metric contract and tests |
| Missing values are not zero | PASS | Flow engine change and tests |
| Persistence/acceleration/reversal exposed | PASS | Contract helper and tests |
| Divergence retained | PASS | Existing intelligence plus contract |
| Options boundary explicit | PASS_WITH_CONDITION | Current participant source has no governed options contract |
| Cash-vs-derivatives boundary explicit | PASS_WITH_CONDITION | Units/normalization not established |
| Freshness/evidence quality separated | PASS | Contract and data loader metadata |
| Backward-compatible latest endpoint | PASS | Focused route test |
| No ML/PRED/EMP/RAG/data migration | PASS | Scope review |
| Full FII regressions | PASS | 1,306 passed; one initial stale API snapshot was corrected and the full rerun passed |
| VEDA provider suite and static checks | PASS | 72 tests, Ruff, format, mypy and compileall passed |
| Live HTTP/provider validation | PASS | FII and VEDA institutional-flow path returned HTTP 200/SUCCEEDED |
| Performance validation | PASS_WITH_CONDITION | Local-only benchmark; no production SLA inferred |
| Deterministic contract rebuild | PASS | Two canonical rebuilds produced the same SHA-256 |

Final pre-Git status: `PASS_WITH_CONDITION`; options and cash-vs-derivatives
comparability remain explicitly unsupported, and the working tree contains
pre-existing generated/data changes that must remain unstaged.
