# VEDA-P000-07 Test, Security, and Runtime Audit

## Runtime verification

Live probes executed on 2026-08-10:

| Check | Result |
| --- | --- |
| backend root `GET /` | `200` |
| backend health `GET /health` | `200` |
| OpenAPI `GET /openapi.json` | `200` |
| chat capabilities `GET /api/chat/capabilities` | `200` |
| stock kundli `GET /api/stocks/RELIANCE/kundli` | `200` |
| country kundli `GET /api/kundli/country/India` | `200` |
| human kundli `POST /api/kundli/human` | `200` |
| frontend root `GET http://127.0.0.1:5173/` | `200` |
| frontend report route `GET /report/RELIANCE` | `200` |
| frontend chat route `GET /chat` | `200` |

Operational runtime notes:

- backend and frontend were already running before audit probes
- backend startup path has side effects and was not needlessly restarted
- scheduler and background refresh wiring are active once backend is up

## Validation command results

| Command | Result |
| --- | --- |
| `py -3.11 -m pytest` | fails overall |
| `npm run test -- --run` | passes |
| `npm run build` | passes |
| `npm run lint` | passes with warnings |

### Python test result

Observed summary:

- total: `339`
- passed: `331`
- failed: `8`
- skipped: `0` observed
- warnings: `1` deprecation warning group observed

All observed failures were in `tests/test_veda_chat_engine.py`.

#### Failing test details

| Test | Failure theme |
| --- | --- |
| `test_chat_engine_attachment_prompt_explains_reviewed_save_flow` | mocked `_run_turn` signature drift after `voice_mode` keyword addition |
| `test_chat_engine_cools_down_provider_after_auth_failure` | same signature drift |
| `test_chat_engine_bounds_history_and_message_size` | expected `_bounded_history()` no longer exists |
| `test_chat_engine_prefers_unified_retrieval` | expected context string not present |
| `test_chat_engine_shadow_mode_compares_unified_and_legacy` | expected context string not present |
| `test_chat_engine_shadow_mode_can_keep_legacy_primary` | expected legacy context string not present |
| `test_chat_engine_tracks_local_evidence_and_instructs_ml_separation` | mocked `_run_turn` signature drift |
| `test_chat_engine_marks_research_as_temporary_and_flags_memory_conflict` | expected conflict note not present in context |

Interpretation:

- Python suite is broadly healthy
- the failing area is concentrated in chat-engine behaviour/tests
- the failures look like **test drift vs current chat implementation**, not a platform-wide collapse

### Frontend test result

Observed summary:

- test files: `4 passed`
- tests: `16 passed`

### Frontend build result

Observed summary:

- TypeScript build passed
- Vite production build passed
- generated main JS bundle was large (`~1.84 MB` minified, `~509.75 kB` gzip) and triggered chunk-size warnings

### Frontend lint result

Observed summary:

- no hard lint failure
- warnings only, including:
  - React hook dependency warnings
  - unused catch parameter
  - unused expression warning

## Security audit

### Findings

| Severity | Finding | Evidence |
| --- | --- | --- |
| CRITICAL | real secrets are stored in `.env` inside the repository workspace | `.env` contains live-looking Telegram and multi-provider API credentials |
| HIGH | auth is disabled by default in current runtime | `/api/auth/config` returned `enabled: false` |
| HIGH | high-risk operational endpoints are therefore effectively open locally | auth middleware bypasses all routes when auth is disabled; data/pipeline/broker/admin surfaces are mounted |
| HIGH | default admin bootstrap password exists if auth is enabled without env overrides | `ADMIN_PASSWORD` defaults to `admin123` in `backend/auth/store.py` |
| HIGH | broker credentials are stored in plaintext JSON on disk | `engines/broker/sync_engine.py` writes `data/portfolio/broker_auth.json` with `client_id` and `access_token` |
| MEDIUM | user conversations and potential birth details are stored durably on disk | `data/veda/chat_sessions/*`, `data/chat/conversation_log.csv`, voice log path in `backend/routers/voice.py` |
| MEDIUM | uploaded user documents are stored durably on disk | `data/veda/uploads/*` |
| MEDIUM | local retrieval indexes are loaded via pickle | `bm25_indexer.py` / `unified_bm25_indexer.py` use `pickle.load` on local files |
| MEDIUM | backend startup launches scheduler and data loaders automatically | `backend/main.py` startup hook |
| LOW | voice configuration comments and actual rate values diverge | `backend/routers/voice.py` comment vs `VOICES["en"]["rate"]` |

### Positive controls observed

| Control | Evidence |
| --- | --- |
| password hashing | PBKDF2-HMAC-SHA256 with per-user salt |
| session and API-key verification | middleware and store helpers present |
| SQL parameterization | SQLite queries use parameters |
| CORS scope | localhost-only origins configured in backend |
| attachment prompt hardening | attachment context explicitly framed as source material, not instructions |

### Security interpretation

The biggest risks are operational/governance issues, not classic SQL-injection findings:

- secret handling
- disabled auth posture
- plaintext credential persistence
- durable PII/conversation storage
- powerful automation endpoints exposed when auth is off

## Runtime and operational fragility

| Area | Risk |
| --- | --- |
| backend startup | initializes DB, starts scheduler, warms voice runtime |
| daily refresh pipeline | spawns subprocesses and writes many data artifacts |
| retrieval stack | depends on local index artifacts and embedding runtime |
| chat engine | complex multi-provider/tool/retrieval state; current failing tests concentrated here |
| duplicated astrology stacks | behaviour may diverge silently across REST vs chat |

## Overall validation conclusion

- the repository is operational enough to audit and extend
- frontend quality gates are in good shape
- Python gates are mostly green but not fully clean
- security and runtime governance issues are material and must be handled before risky change phases
