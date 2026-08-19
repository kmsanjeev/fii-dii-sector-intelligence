# VEDA-ENGINEERING-TEST-SUITE-PERFORMANCE-RX1-001 — Baseline

Baseline was captured on 2026-08-19 from commit
`68a3698c92a651eee174737304d66852e64f57b8` on `main`.

| Item | Observation |
|---|---|
| Python | 3.11.9 |
| pytest | 9.1.1 |
| Plugins | `anyio-4.14.0` only |
| Test files | 199 before this activity |
| Collected tests | 1,266 |
| Collection | 8.48s |
| CPU | 4 logical processors |
| Memory | 15.9 GB visible; approximately 2.5 GB free during audit |
| Workspace payload | 53,404 files / approximately 21.2 GB outside excluded VCS/build directories |
| Test-specific environment | None observed |

The first authoritative full run exceeded the 900-second diagnostic bound at
approximately 95%, with the last visible path entering RAG/FAISS model work.
The command wrapper left its own pytest child alive; only those confirmed
children were terminated. The unrelated broker MCP process was not touched.

No production astrology, prediction, ML, PRED-M4, RAG semantics, EMP-001,
Approved Core, or Muhurta behavior was changed.
