# VEDA-MUHURTA-ENGINE-ACTIVITY-EXPANSION-T1-001 - Baseline

Starting commit: `596e2d393940c5d27381fc71a1affe200a6aa18e`

The existing RX1 general recommendation engine and transition-aware window
search were operational for Business and Education. The T1 predecessor
contracts were present but inactive. Personal Bala remained diagnostic only;
P032 calculation, RAG, prediction, ML and Approved Core were outside scope.

The implementation reuses the same RX1 engine, P032 factor adapter, declarative
predicate evaluator, transition source and FastAPI routes. No parallel engine
or search subsystem was created.
