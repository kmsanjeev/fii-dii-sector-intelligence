# Validation

Passed:

- focused Theme tests: 7 passed;
- focused FII API baseline tests: 3 passed;
- FII full suite: 1,352 passed, 1 warning;
- VEDA Theme/provider/routing regression: passed;
- VEDA platform suite: 83 passed, pre-existing deprecation warnings only;
- Ruff, format, mypy, and compileall;
- direct FII HTTP probes;
- real VEDA → FII Theme HTTP query;
- natural Theme query routing;
- valid artifact load without CSV/Parquet reads;
- controlled price-manifest invalidation;
- many-to-many and missing-data boundary tests;
- two deterministic snapshot builds.

Current canonical builder stdout hash, run 1 and run 2:

`61c4517397436b923b8801fea4d335e3edd2ab1b64cac04346ea922f77592da1`

The predecessor recorded hash was generated against an earlier evidence
state. Running the exact predecessor service and the optimized service
against the same current evidence produced identical canonical Theme JSON.

No RAG rebuild was performed.
