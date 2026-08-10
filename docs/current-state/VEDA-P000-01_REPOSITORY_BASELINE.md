# VEDA-P000-01 Repository Baseline

Audit baseline captured on: 2026-08-10
Baseline intent: record the pre-audit technical state without changing branches, stashing, resetting, or cleaning

## Git baseline

Pre-documentation repository state:

| Item | Value |
| --- | --- |
| Repository path | `D:\Projects\fii-dii-sector-intelligence` |
| Branch | `main` |
| HEAD commit | `70643c9a2389729b5c73fe84f6ae2d2b7441ea85` |
| Remote | `origin https://github.com/kmsanjeev/fii-dii-sector-intelligence.git` |
| Git tags | none |
| Git status before audit docs | `## main...origin/main` |
| Dirty worktree before docs | no |

Commands executed:

```text
git status --short --branch
git rev-parse HEAD
git branch --show-current
git remote -v
git tag --list
```

## Runtime environment

| Item | Value |
| --- | --- |
| OS shell | PowerShell |
| Python runtime | `Python 3.11.0` |
| Node runtime | `v24.16.0` |
| npm runtime | `11.13.0` |
| FastAPI | `0.138.2` |
| Uvicorn | `0.49.0` |
| pandas | `3.0.3` |
| swisseph | `20230604` |
| openai | `2.44.0` |
| sentence-transformers | `5.6.0` |
| faiss | `1.14.3` |
| xgboost | `3.2.0` |
| lightgbm | `4.6.0` |

Frontend manifest versions:

| Package | Declared version |
| --- | --- |
| React | `^19.2.7` |
| React Router DOM | `^7.18.1` |
| Vite | `^8.1.0` |
| TypeScript | `~6.0.2` |
| Vitest | `^4.1.10` |

## Repository structure observed

Top-level directories materially used by the running platform:

```text
alerts/
backend/
data/
docs/
engines/
fetchers/
frontend/
research/
scripts/
storage/
tests/
utils/
```

Notable control/config roots:

```text
.github/
.vscode/
start.ps1
stop.ps1
main.py
requirements.txt
frontend/package.json
pytest.ini
```

## Application start commands

### Local dev launcher

Observed from `start.ps1`:

```text
Backend:
  py -3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

Frontend:
  npm run dev
```

The launcher probes for importability of `uvicorn`, `fastapi`, `openai`, and optionally `ddgs`.

### Alternative/legacy executable

Observed from `.github/workflows/daily.yml`:

```text
python main.py
```

This is not the live FastAPI app entry point. It is a separate orchestration path used by the GitHub Actions workflow to update data.

## Build, test, and lint commands

### Frontend

```text
npm run build
npm run test -- --run
npm run lint
```

### Python

```text
py -3.11 -m pytest
```

Pytest configuration observed:

- test root: `tests`
- verbose mode enabled
- debug log file: `tests/logs/pytest_debug.log`

## Database and persistence technologies

### Operationally verified

| Layer | Technology |
| --- | --- |
| auth/users/sessions/api keys | SQLite (`data/auth/users.db`) |
| intelligence datasets | CSV / JSON / Parquet files under `data/` |
| reviewed knowledge / chat sessions / uploads | file-backed JSON / JSONL / uploaded binaries under `data/veda` |
| retrieval indexes | BM25 pickle + FAISS index files under `data/intelligence/rag_knowledge` |

### Present in dependencies but not proven as the main operational store

- `duckdb`
- `sqlalchemy`

No evidence was found that the running application uses a central relational business database for market, astrology, or report state.

## Live process state observed during audit

Ports listening during audit:

| Port | Status |
| --- | --- |
| `8001` | backend already running |
| `5173` | frontend already running |

Health checks:

| Probe | Result |
| --- | --- |
| `GET /` | `200` |
| `GET /health` | `200` |
| `GET /openapi.json` | `200` |
| `GET /api/chat/capabilities` | `200` |
| `GET /api/kundli/bulk/status` | `200` |

## Python package/runtime inventory from manifests

Selected package groups in `requirements.txt`:

- FastAPI platform: `fastapi`, `uvicorn`
- AI: `openai`, `ddgs`
- astrology/astronomy: `pyswisseph==2.10.3.2`, `ephem==4.2.1`
- retrieval: `sentence-transformers`, `faiss-cpu`, `rank-bm25`
- ML: `scikit-learn`, `xgboost`, `lightgbm`
- data: `pandas`, `pyarrow`, `duckdb`

## Baseline observations that affect the audit

- the repository was clean before audit-document creation
- the live backend startup path has side effects:
  - initializes auth DB
  - loads datasets
  - starts scheduler
  - validates/warms voice runtime
- because the backend was already live, most runtime verification was performed against the running process instead of restarting services

## Post-audit modification policy

This activity authorizes:

- audit documentation only

This activity does not authorize:

- application code changes
- dependency changes
- schema changes
- runtime behaviour changes
- commits or pushes
