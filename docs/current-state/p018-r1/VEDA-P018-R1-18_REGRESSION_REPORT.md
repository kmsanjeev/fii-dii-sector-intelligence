# Regression Report

- P018-R1 focused tests: `11 passed`
- Inherited governance focused tests: `63 passed`
- Full Python suite: `492 passed, 1 warning`
- Frontend tests: `27 passed`
- Frontend build: `PASS` with the existing large-chunk warning
- Standard smoke wrapper: startup checks exercised; exit was affected by the known Windows temporary-log cleanup defect
- Direct backend/frontend smoke: `PASS`
- RAG rebuild 1: `written={'documents': False, 'metadata': False, 'manifest': False}`
- RAG rebuild 2: `written={'documents': False, 'metadata': False, 'manifest': False}`
- RAG corpus hash: `9754fc5e948405c4510f2340170e47bf4c433f1ac3b83020fe9aa3b02b0a882c`
