# VEDA Roadmap Entry Point

Read this directory before starting any future VEDA work. `VEDA-RM-001-05_FUTURE_PHASE_REGISTRY.md` is the single authoritative future registry; historical roadmaps remain preserved and are classified in `VEDA-RM-001-02_ROADMAP_CONFLICT_AUDIT.md` and `VEDA-RM-001-03_SUPERSESSION_REGISTER.md`.

The implemented baseline is frozen through P026 plus STD-001, STD-002, STD-003, and PRED-001 through PRED-003. P027 is reserved but unassigned. ADM-EMP-001 is implemented/frozen; EMP-001 remains longitudinal.

## Current Status

- RM-001 baseline commit: `1fa05f354a0175637c2b771ab80d3d5763320733`
- RM-001 tag: `veda-rm-001-roadmap-rebaseline`
- Predictive maturity: `PRED-M3_OPERATIONAL_PLUS`
- Empirical status: `VEDA-EMP-001` remains longitudinal; real eligible cases and verified outcomes remain `0`; `PRED-M4` is `INSUFFICIENT_SAMPLE`.
- `VEDA-ADM-EMP-001` is implemented/frozen by its own acceptance record; the next operational step is to supply legitimate governed case data.
- ADM-EMP-001 implementation: `38bd7a03`, tag `veda-adm-emp-001-case-intake-console`.
- STD-003 is implemented/frozen by its current-state acceptance record; COMM-001 is implemented/frozen by `docs/current-state/comm-001/`; LANG-001 and LANG-001-R1 are implemented/frozen by their current-state records; COMM-002 is implemented/frozen by `docs/current-state/comm-002/`; GROUP-001 and LANG-002+ remain planned successor modules.
- STD-003 implementation: `c73261e1`, tag `veda-std-003-conversational-intelligence-standard`.
- COMM-001 implementation: `676f0aca`, tag `veda-comm-001-pragmatic-understanding-engine`.
- LANG-001 implementation: `9d15dcb8` with tag `veda-lang-001-wave1-language-intelligence`.
- LANG-001-R1 resolution hardening: evidence is in `docs/current-state/lang-001-r1/`.
- COMM-002 implementation: evidence is in `docs/current-state/comm-002/`; deterministic adaptation gates pass and Founder blind A/B validation remains pending.
- COMM-002 implementation commit: `f2907971`; release tag: `veda-comm-002-adaptive-response-engine`.

This directory is the VEDA roadmap, status, and cold-start entrypoint. Do not use the historical P000/P013 roadmap files or the governance-audit P027 pathway to infer current scope.
