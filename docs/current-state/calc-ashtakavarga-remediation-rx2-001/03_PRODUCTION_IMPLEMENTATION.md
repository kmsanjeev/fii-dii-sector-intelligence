# Production implementation

The existing `engines/ai/knowledge/shadbala_engine.py` now defaults to `ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2` and binds contract `084E19B2D61880066A503E1CED38810CA9D51962354A9520DD2E5E5946279A62`. The explicit table is in `engines/ai/knowledge/ashtakavarga_contract_v2.py`; it is a source-contract table, not a parallel calculation engine. The old target-shared implementation remains available only through explicit legacy methods.
