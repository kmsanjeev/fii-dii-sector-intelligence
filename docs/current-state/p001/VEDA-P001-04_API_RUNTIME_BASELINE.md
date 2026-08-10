# VEDA-P001-04 API / Frontend / Runtime Baseline

## Backend Contract Snapshot

- OpenAPI path count: `125`
- OpenAPI operation count: `137`
- Contract fixture: `tests/fixtures/veda_p001/api_contract_baseline.json`
- Generator: `scripts/generate_p001_api_baseline.py`
- Snapshot test: `tests/test_api_contract_baseline.py`

### Critical Endpoint Baseline

| Method | Path | Auth Requirement | Verification |
| --- | --- | --- | --- |
| `GET` | `/health` | `PUBLIC` | smoke + contract fixture |
| `POST` | `/api/auth/login` | `PUBLIC` | contract fixture |
| `GET` | `/api/auth/config` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | smoke |
| `GET` | `/api/chat/capabilities` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | smoke + contract fixture |
| `POST` | `/api/chat` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | contract fixture |
| `GET` | `/api/stocks/{symbol}/kundli` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | golden test + contract fixture |
| `POST` | `/api/kundli/human` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | smoke + contract fixture |
| `GET` | `/api/research/universe/stats` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | smoke + contract fixture |
| `GET` | `/api/broker/status` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | smoke + contract fixture |
| `GET` | `/api/pipeline/status` | `AUTH_MIDDLEWARE` in production / local loopback allowed when auth off | smoke + contract fixture |

## Frontend Contract Baseline

### Route Baseline Tests

File: `frontend/src/test/AppRouteBaseline.test.tsx`

Protected routes:

- `/chat`
- `/settings`
- `/report/:symbol`
- `/fullchart/:symbol`
- `/participant` -> redirect to dashboard

### Existing Frontend Evidence Retained

The pre-existing Veda frontend surface tests remain part of the baseline:

- `frontend/src/test/VedaSurfaces.test.tsx`
- `frontend/src/test/vedaStore.test.ts`
- `frontend/src/test/MessageEvidence.test.tsx`
- `frontend/src/test/KnowledgeReviewPanel.test.tsx`

## Runtime Smoke Procedure

Runner:

```bash
py -3.11 scripts/run_p001_smoke.py
```

Checks executed:

- backend startup
- `/health`
- `/api/auth/config`
- `/api/chat/capabilities`
- `/api/research/universe/stats`
- `/api/kundli/human`
- `/api/pipeline/status`
- `/api/broker/status`
- frontend startup via Vite root response

### Latest Smoke Result

| Check | Result | Notes |
| --- | --- | --- |
| backend startup and health | `PASS` | `41 / 43` datasets loaded |
| authentication configuration | `PASS` | local auth-disabled mode surfaced explicitly |
| chat capability | `PASS` | runtime research capability returned |
| retrieval capability | `PASS` | research universe stats returned structured keys |
| kundli calculation | `PASS` | lagna `Libra`, planet count `11` on REST human path |
| pipeline status | `PASS` | runtime state returned |
| broker status | `PASS` | disconnected state returned cleanly |
| frontend startup | `PASS` | Vite root served `200` |

## Validation Commands

```bash
py -3.11 -m pytest tests/test_api_contract_baseline.py -q
py -3.11 -m pytest tests/test_veda_astrology_golden.py -q
npm run test
npm run build
py -3.11 scripts/run_p001_smoke.py
```
