# Validation

Focused tests:

- `tests/test_stock_institutional_evidence.py`: contract, identity review,
  ownership date separation, heuristic classification and market-context
  boundary;
- existing stock and cross-layer contract tests.

Live provider-local probes covered a symbol with deal and ownership evidence,
symbols with both ownership and disclosed activity, and the no-stock-evidence
path after data-loader startup. The live contract retained the two direct-flow
decision gates and did not emit a daily FII/DII stock claim.

Full validation completed:

- FII full suite: `1322 passed, 1 warning` in `701.37s`;
- VEDA platform regression suite: `76 passed, 2 warnings`;
- FII focused suite: `9 passed`;
- Ruff and compile validation: passed;
- real HTTP: `/api/stocks/PAYTM` and `/api/market/intelligence/cross-layer?mode=STOCK_CONFIRMATION&symbol=PAYTM` returned `200` and exposed the nested evidence contract;
- no raw provider data was added by this activity.

The activity is complete with conditions: the direct daily stock-level and
direct sector-level FII/DII source gates remain explicitly ungoverned.
