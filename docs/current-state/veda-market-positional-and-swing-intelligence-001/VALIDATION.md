# Validation

- FII focused suite: 19 passed.
- VEDA focused Market/provider suite: 44 passed.
- FII full repository suite: 1,364 passed, 1 existing deprecation warning, in
  566.63 seconds. Existing research-heavy tests regenerated live RAG
  artifacts; those generated files are outside this release.
- VEDA full platform suite: 90 passed, with existing deprecation warnings only.
- FII changed-file Ruff and compile checks: passed.
- VEDA changed-file Ruff and compile checks: passed.
- Live FII TestClient probes: detail SWING/POSITIONAL, Theme-absent symbol,
  both bounded screens returned HTTP 200; unknown symbol returned HTTP 404.
- Deterministic contract version and horizon validation passed.
- No RAG rebuild, ML, prediction, EMP, Jyotish or BEBOS behavior changed.
