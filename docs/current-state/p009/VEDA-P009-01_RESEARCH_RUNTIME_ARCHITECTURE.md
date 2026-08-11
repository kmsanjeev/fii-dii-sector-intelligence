# Research Runtime Architecture

P009 introduces `engines/ai/research/platform/runtime.py` as the backend-owned worker wrapper around the existing `ResearchPlatformService`.

Runtime responsibilities:
- poll due schedules;
- acquire a persisted worker lease;
- honor platform pause and kill-switch controls;
- execute due research runs;
- update runtime state and release the lease;
- remain independent of the Admin UI.

Startup integration:
- `backend/main.py` starts the research runtime only when `VEDA_RESEARCH_RUNTIME_ENABLED=true`;
- shutdown stops both the legacy refresh scheduler and the research runtime.

Persistence:
- SQLite-backed runtime state is stored in `research_runtime_state`;
- provider runtime state is stored in `research_provider_state`;
- digests are stored in `research_digests`.
