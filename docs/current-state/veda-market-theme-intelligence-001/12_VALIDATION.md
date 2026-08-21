# Validation

## Automated validation

- FII focused Theme tests: `5 passed`.
- FII API-contract baseline tests after the governed router addition: `3 passed`.
- FII combined Theme/API regression: `8 passed`.
- FII full suite: `1350 passed, 1 warning` in `554.92s`.
- VEDA platform suite: `83 passed`; only pre-existing Authlib/httpx deprecation
  warnings were emitted.
- New and changed Python modules compile successfully.

## Runtime and determinism

- Real FII HTTP probes returned `200` for health, governed registry, summary,
  bounded detail and stock-membership routes.
- Two standalone snapshot builds produced the identical SHA-256 hash
  `249BA067B42AD4D248A7ADEC937EC8BE2D3863A5C12DFA148B48E86728BB55E5`.
- Cold summary: `19.6436s`; warm summary: `0.0599s`.
- Cold bounded detail: `6.0033s`; warm calls remain below `0.1s`.
- Real VEDA-to-FII Theme query: `SUCCEEDED` in `20.133s`; VEDA uses a
  Theme-only bounded provider timeout of `30s`, while other Market capabilities
  retain the existing timeout.
- Provider calls added: `0`; no RAG rebuild was performed.

The first full-suite run correctly caught a stale API-contract fixture
(`147/160` expected versus `152/165` actual). The fixture and its count
assertions were regenerated as part of this capability change; the rerun is
fully green. The warning is unrelated to Theme logic.
