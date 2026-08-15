# FII-DII SECTOR INTELLIGENCE PLATFORM
# MASTER PROJECT STATE
# Version 4.73.0 | 2026-08-14

---

# PROJECT MISSION

Build India's most advanced institutional-grade market intelligence platform capable of
identifying capital flow (Participant -> Sector -> Theme -> Stock) before broad market recognition.

Core cascade:
  FII/DII/PRO/CLIENT -> Sector Attribution -> Corporate Signals -> Stock Scoring -> Alert/Chatbot/Execution

This project is NOT a screener. It IS a decision intelligence platform.

---

# CURRENT PLATFORM STATE (2026-08-04)

## VEDA CURRENT JYOTISHA STATE (2026-08-15)

- P027 Advanced Synthesis & Multi-Chart Reasoning is implemented/frozen; it reuses the existing Jyotisha runtime and preserves chart/evidence authority.
- P028 Compatibility & Relationship Synthesis is implemented/frozen; it reuses P024/P027 contracts, preserves chart identity, and does not fabricate traditional match scores.
- P028-R1 Traditional Compatibility Methods is implemented/frozen as a research-candidate, versioned Ashtakoota foundation; VEDA-KNOW-COMPAT-001 completed source validation with partial framework validation only. Executable Kuta tables remain research candidates, Manglik cancellation remains deferred, and no Approved Core compatibility promotion occurred.
- P029 Property, Residence & Real-Estate Synthesis is implemented/frozen as a governed domain layer over existing D1/property facts, P022 wealth context, P027 synthesis, Dasha and Transit. D4 is explicitly not validated; P030 remains not started.
- VEDA-KNOW-PROP-001 completed the property/D4 source audit with `PASS_WITH_CONDITION`; D4 calculation is available with conditions but its current generic method does not match the inspected source-referenced 1/4/7/10 method. `P015-RX_REQUIRED` is recorded; P029-R1 and P030 remain not started.
- P015-RX remediated D4 calculation to `D4_CHATURTHAMSHA_1_4_7_10_V1` with calculation status validated and interpretation status not validated. P029 remains D1-first and does not use D4 interpretively; P029-R1 and P030 remain not started.
- COMM-002 and GROUP-001 human validation remain pending. EMO-001 is implemented/frozen.
- EMP-001 remains active longitudinal with insufficient sample; LANG-002+ remains planned.
- Historical P027 reservation is preserved; current assignment is governed by `docs/current-state/p027/`.

**ALL 25 CORE PHASES + A/B/C/D/FPI/KU/AF/CH/TI/SH/UI-S COMPLETE. Full investment operating system is live.**

Frontend build health on 2026-08-04:
- Full `frontend` production build passes again with `npm.cmd run build`
- Old TypeScript drift in charting, watchlist, report, and stock-detail pages
  has been cleaned up
- One narrow local build-mode workaround remains in `StockDetailPage.tsx` for a
  TS JSX inference edge case; runtime behavior is unchanged

Latest Veda memory follow-up on 2026-08-04:
- approved reviewed saves now keep both the edited knowledge note and the full
  readable attachment text as searchable document memory
- Veda can now recall approved book/document content later instead of only
  recalling a short reviewed note about that file
- when the same topic or same readable file is uploaded again, Veda now checks
  saved memory first, recommends whether to save or discard, and asks the user
  to confirm the final action
- reviewed-memory decisions are now smarter:
  - `discard` for near-duplicate readable files or strongly repeated notes
  - `merge` for same-topic drafts that add new value to an older saved memory
  - `save` when the draft is still different enough to stand on its own
- `start.ps1` now prefers a backend Python runtime that already has `ddgs`, so
  research mode does not come up disabled just because the wrong interpreter
  started first
- `start.ps1` now checks for `LISTENING` sockets only, so a dead `TIME_WAIT`
  backend port is no longer mistaken for a running API
- `requirements.txt` now explicitly includes `apscheduler`, which the backend
  already uses during startup for scheduled refresh jobs
- Veda chat now clamps oversized session history and tool-result context before
  sending prompts to remote models, preventing the older prompt-too-large
  failure pattern from recurring in long sessions
- Veda now cools down bad providers after auth, connection, or stale-model
  failures instead of retrying them every turn and delaying the answer path
- approved reviewed memory and approved MIT capability notes now refresh the
  unified durable corpus and unified BM25 index immediately after a real save
  or merge, so newly approved knowledge becomes searchable right away
- save-time unified FAISS rebuild is now off by default, which keeps the review
  flow fast while the normal full index refresh path remains responsible for
  the heavier semantic rebuild

Latest Jyotish programme audit on 2026-08-05:

- a dedicated repo-vs-programme audit was added to:
  `docs/governance/VEDA_JYOTISH_ML_RAG_AUDIT_2026-08-05.md`
- audit conclusion:
  - Veda's platform foundation is strong enough to host a serious Jyotish programme
  - the Jyotish-specific scholarly layer is still incomplete
- already reusable in the current repo:
  - attachment reading
  - OCR/image fallback
  - reviewed durable memory
  - unified BM25 + FAISS retrieval
  - evidence/provenance UI
  - deterministic astro/kundli calculation core
- major missing layers before this can become a true source-grounded Jyotish system:
  - programme charter and epistemic governance
  - validated source register and authority rubric
  - Sanskrit corpus engineering and passage IDs
  - source-layer separation for text / translation / commentary / modern interpretation
  - contradiction-aware citation-first Jyotish RAG
  - Jyotish-specific annotation, benchmarking, and red-team evaluation
- important correction from the audit:
  - Veda should be treated as the orchestration/governance layer above ML and RAG, not as a thin frontend over them
- important product-positioning note:
  - the repo should not promise autonomous "accurate prediction in all aspects"
  - the safe target is accurate calculation, accurate source retrieval, accurate citation, and controlled testing of predictive hypotheses

Latest P020 governance follow-up on 2026-08-14:
- a shadow-only career / education / wealth synthesis bundle is now present
- D10 is reused as a governed supporting fact, not a deterministic outcome
- finance remains high-stakes and inactive at the synthesis layer
- runtime activation was not changed

Latest P021 governance follow-up on 2026-08-14:
- career / profession validation now sits on top of the existing kundli data
- the exported profile set contains 12,096 rows across 2,016 symbols
- canonical rows remain separate from shadow-synthesized alternatives
- the admin dashboard now surfaces summary metrics without changing runtime prediction semantics

Project root: `D:\Projects\fii-dii-sector-intelligence`

## Intelligence Cascade: COMPLETE
```
Layer 1: Participant Intelligence  (5A/5B/5C)  LIVE through 2026-07-01
Layer 2: Sector Rotation           (6A/6B/6C)  LIVE through 2026-07-01
Layer 3: Corporate Intelligence    (7A/7B/7C)  LIVE through 2026-07-01
Layer 4: Stock Scoring             (8A/8B)     LIVE through 2026-07-01
Layer 5: Technical + F&O           (A)         LIVE through 2026-07-01
Layer 6: Trade Conviction          (C)         LIVE through 2026-07-01
```

## Market Snapshot (as of 2026-07-01)
- Market Regime: NEUTRAL (x0.90 multiplier)
- Smart Money Score: -4.7 | FII conviction: 40%
- Bull run watchlist: 225 EMERGING symbols
- Sector EARLY_ROTATION: MEDIA
- Trade conviction scores: 2406 symbols

---

# PHASE COMPLETION STATUS

## Foundation + Data Layer (COMPLETE)
| Phase | Engine | Output | Status |
|-------|--------|--------|--------|
| 1 | Foundation | equity_master.csv, 7813 bhavcopy files | COMPLETE |
| 2 | Classification V4 | company_classification_v4.csv (2123 symbols, 99.5%) | COMPLETE |
| 3 | Index Intelligence | 139 indices, index_momentum.csv | COMPLETE |
| 3B | Guardrails + Tests | guardrails.py, 400+ tests | COMPLETE |
| 4A | Fundamentals Master | company_fundamentals_master.csv (2123 symbols) | COMPLETE |
| 4B | Industry Master | industry_master.csv (183 industries) | COMPLETE |
| 4C | Classification V4 final | 99.53% sector coverage | COMPLETE |
| 4D | NSE Constituents | index_membership.csv (30 indices, 506 symbols) | COMPLETE |

## Intelligence Layer (COMPLETE)
| Phase | Engine | Output | Rows | Status |
|-------|--------|--------|------|--------|
| 5A | Participant Acquisition | institutional_positioning_history.csv | 2581 | COMPLETE |
| 5B | Participant Flow Engine | participant_flow_scores.csv | 2581 | COMPLETE |
| 5C | Participant Intelligence | participant_intelligence.csv | 2581 | COMPLETE |
| 6A | Sector Capital Flow | sector_capital_flows.csv | 74269 | COMPLETE |
| 6B | Sector Flow Scores | sector_flow_scores.csv | 74269 | COMPLETE |
| 6C | Sector Rotation Intel | sector_rotation_intelligence.csv | 29 | COMPLETE |
| 7A | Block/Bulk Deals | institutional_deal_signals.csv | 361 | COMPLETE |
| 7B | Event Calendar | event_calendar.csv + upcoming_catalysts.csv | 33839 | COMPLETE |
| 7C | Corporate Actions | corporate_confidence_scores.csv | 1111 | COMPLETE |
| 8A | Price Momentum | price_momentum.csv | 2441 | COMPLETE |
| 8B | Bull Run Probability | bull_run_probability.csv + watchlist (225) | 2441 | COMPLETE |

## Application Layer (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| 9  | Alert System (Telegram)    | alerts/               | COMPLETE — 10 alert types, APScheduler, cooldown + per-type caps |
| 10 | FastAPI Backend            | backend/              | COMPLETE — 20 endpoints, port 8001, WebSocket live ticker |
| 11 | React GUI                  | frontend/             | COMPLETE — 15 pages, KLineChart Pro OHLCV, IST timestamps, inline styles |
| 12 | ML Intelligence Layer      | engines/ml/           | COMPLETE — XGBoost+LightGBM, 24 features, 4 model outputs |
| 13 | RAG Knowledge Base         | engines/ai/knowledge/ | COMPLETE — FAISS+BM25, 6 domain indexes, hybrid RRF retrieval |
| 14 | Chatbot (multi-provider LLM) | engines/ai/chatbot/ | COMPLETE — Groq llama-3.3-70b (primary), multi-provider fallback via llm_client.py, 11 tools, /api/chat |
| 15 | Financial Results + SHP    | engines/fundamentals/ | COMPLETE — 4181 XBRL rows, 76170 shareholding rows (8 quarters, XBRL fraction-scale fixed) |
| 16 | Management Intelligence    | engines/management/   | COMPLETE — holding trends, announcements, sentiment |

## Generation 4 — Investment Operating System (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| 17 | Symbol Change History       | engines/foundation/    | COMPLETE — 1038 renames |
| 18 | Corporate Announcements     | engines/corporate/     | COMPLETE — NSE XBRL fetcher |
| 19 | Daily Intelligence Refresh  | engines/orchestration/ | COMPLETE — APScheduler 18:00 IST |
| 20 | Portfolio Engine            | engines/portfolio/     | COMPLETE — transactions, P&L, allocation |
| 21 | Backtesting Framework       | engines/backtest/      | COMPLETE — 3 strategies, 5 horizons |
| 22 | Broker Adapter (R/O)        | engines/broker/        | COMPLETE — Dhan + CSV adapters |
| 23 | Research Platform           | engines/research/      | COMPLETE — screener, comparator, notes |
| 24 | Execution Platform          | engines/execution/     | COMPLETE — risk engine, paper/live orders |
| 25 | Commercial Platform         | backend/auth/          | COMPLETE — auth off by default |

## Generation 5 — Trade Intelligence Layer (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| A | Technical + F&O Intelligence | engines/intelligence/ | COMPLETE — tech_indicators (2718), fno_intel (211), market_context.json |
| B | Trade Intelligence Card      | frontend/components/  | COMPLETE — 7-factor WHY BUY panel, _enrich_bulk() in stocks.py |
| C | Trade Conviction Alerts      | engines/intelligence/ | COMPLETE — trade_conviction_scores (2406), P9/P10 alerts |
| D | Chat Page (Full UI)          | frontend/pages/       | COMPLETE — 355-line ChatPage.tsx, 6 suggested prompts, session chat |

## Generation 6 — Extended Intelligence (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| FPI | FPI Sector Ownership Engine  | engines/fpi/          | COMPLETE — 8690 rows, sector_fpi_fortnightly.csv, 3-factor rotation |
| KU  | Kundli + Gann Engine         | engines/astro/        | COMPLETE — kundli_engine.py, gann_engine.py |
| AF  | AstroFinance Engine          | engines/intelligence/ | COMPLETE — astro_signals.csv (209 rows), planetary intelligence layer |
| CH  | KLineChart Pro Chart         | frontend/src/         | COMPLETE — klinecharts v9.8.12, customIndicators.ts (VOLMain/VWAP/Supertrend/HMA) |
| TI  | Technical Indicators Upgrade | engines/intelligence/ | COMPLETE — RSI/MACD/ATR/BB/OBV/ADX added, technical_indicators.csv (2718 rows) |
| SH  | Shareholding Fix + 8-score panel | frontend/src/     | COMPLETE — XBRL fraction-scale fixed, 8-score panel in StockDetail |
| UI-S | Sectors + Social Pulse UI   | frontend/src/         | COMPLETE — Sectors page + Social Pulse component |

## Generation 7 — Voice + Portfolio Ops (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| V1-V3 | Veda Voice Assistant (base) | backend/routers/voice.py | COMPLETE — edge-tts, wake word, staged playback |
| V4  | Hands-free follow-up mode    | frontend/src/store/vedaStore.ts | COMPLETE — mic reopens after Veda speaks, no repeat wake word |
| V5  | Customer-support voice persona | chat_engine.py, intent_router.py, voice.py | COMPLETE — confirm-before-detail, warm greetings |
| V6  | Voice stability fixes (2026-08-09) | start.ps1, voice.py, vedaStore.ts | COMPLETE — non-blocking startup, py -3.11 probe, English Neerja rate fix |
| RF-1 | Research foundation commit (2026-08-10) | engines/ai/, frontend/veda/, tests/ | COMPLETE — 7 commits: 71 files, ~14,500 lines. Kiro AI additions committed category-wise |
| WL-1 | Watchlist Decision Metrics  | engines/watchlist/     | COMPLETE — RVOL, RS vs NIFTY, 5D delivery |
| DMB-1 | Daily Market Brief         | engines/briefing/      | COMPLETE — 08:45 IST auto-brief, Telegram digest |
| UI-D | Dashboard Consolidation     | frontend/src/pages/Dashboard.tsx | COMPLETE — Participant page merged into Dashboard |
| PF-1 | Portfolio CSV Import        | engines/portfolio/, backend/routers/portfolio.py | COMPLETE — bulk import + downloadable template |

Not yet verified live (flagged, not blocking): hands-free follow-up loop and voice
persona pacing need an actual browser/mic session — see Task #25 in the session
tracker (wake word from non-chat pages, drawer/page state sync, orb animation).

---

# VEDA CURRENT CONVERSATIONAL STATUS (2026-08-15)

- EMO-001 is implemented/frozen in `docs/current-state/emo-001/`.
- COMM-002 and GROUP-001 remain technically validated with human validation pending.
- LANG-002+ remains planned; P027 remains reserved/unassigned.
- EMP-001 remains active longitudinal; predictive and empirical systems are unchanged.

# VEDA WORKSTREAM STATUS (HISTORICAL PHASE 8 RECORD)

> This section preserves the historical 2026-08-04 Veda platform rollout record.
> It is not the current VEDA roadmap. The authoritative current roadmap and
> future phase registry are maintained at:
> `docs/roadmap/veda/README.md` and
> `docs/roadmap/veda/VEDA-RM-001-05_FUTURE_PHASE_REGISTRY.md`.
> RM-001 freezes the implemented Veda baseline through P026 plus STD-001,
> STD-002, STD-003, COMM-001, LANG-001, COMM-002, GROUP-001, and PRED-001 through PRED-003; P027 is reserved and
> unassigned.

As of 2026-08-04, the approved Veda upgrade path is complete through Phase 8
for implementation, automated verification, and rollout documentation:

| Track | Goal | Status |
|-------|------|--------|
| VR-1 | Research mode foundation | PHASE 0 + 1 + 2 COMPLETE -- contracts, `ddgs` provider, local-first decision layer, chat/widget research controls, research audit metadata |
| VR-2 | Chat attachments (documents/images) | PHASE 3 COMPLETE -- upload UI, safe extraction, image vision fallback, and attachment-aware prompting live |
| VR-3 | Source-aware answer layer | PHASE 4 COMPLETE -- answer basis, confidence framing, source links, and research dates visible in chat |
| VR-4 | Save-to-knowledge review flow | PHASE 5 COMPLETE -- review draft, approve-to-save, traceability, reviewed note memory, and approved attachment document memory live |
| VR-5 | MIT repo capability intake | PHASE 6 COMPLETE -- local MIT repo study, license check, approval-before-save, and reusable capability memory live |
| VR-6 | External research connectors | PHASE 7 COMPLETE -- Python-first research remains primary, MCP fallback connectors are now available when the primary path is insufficient |
| VR-7 | Hardening, tests, and rollout | PHASE 8 COMPLETE -- MCP fallback now covers provider-unavailable cases, research-runtime readiness is exposed honestly to React, focused React tests are live, browser UI QA passed on 2026-08-04, and microphone/voice QA remains separately pending |

Latest Veda follow-up on 2026-08-04:

- saved chat history now mirrors to backend storage under `data/veda/chat_sessions`
- browser caching is still kept for fast sidebar/session loading
- auth-off mode separates saved history by browser client id
- auth-on mode separates saved history by authenticated user id
- approved reviewed saves now also store readable attachment text as document
  memory under `data/intelligence/rag_knowledge/veda_reviewed_documents.jsonl`
- reviewed-save drafts now detect duplicate readable files and strong same-topic
  overlap before saving
- the review modal now recommends `discard` versus `save anyway` and lets the
  user confirm the decision instead of silently re-saving similar memory
- duplicate readable-file detection now uses extracted content instead of the
  upload filename, so the same book saved under a different name is still
  recognized correctly
- Veda live chat was re-verified on 2026-08-04 after relaunch with a real
  network-enabled backend: normal chat replies and research-mode replies both
  returned successfully again
- unified ML-RAG-Veda follow-up started on 2026-08-04 with a shared durable
  knowledge contract in `engines/ai/knowledge/contracts.py`
- Phase 0 added normalizers for platform RAG docs, reviewed memory, attachment
  memory, and MIT repo capability notes without changing live retrieval yet
- Phase 0 contract coverage was validated with focused tests across all current
  durable source families plus existing reviewed-memory and MIT capability flows
- Phase 1 now emits a combined durable side corpus through
  `engines/ai/knowledge/unified_corpus_builder.py` with manifest and metadata
  outputs, while current production retrieval still stays unchanged
- Phase 1 corpus generation and duplicate reporting were validated with focused
  tests on 2026-08-04 without changing the production chat path
- Phase 2 now adds unified BM25 + FAISS indexes over the combined durable
  corpus and makes chat prefer one ranked local evidence path with automatic
  fallback to the old split retrieval route
- Phase 2 unified retrieval was validated with focused retriever, chat, corpus,
  contract, reviewed-memory, and MIT capability tests on 2026-08-04
- approved saves and approved MIT capability notes now trigger immediate
  unified corpus + BM25 refresh through runtime sync, so Veda no longer has to
  wait for the next scheduled rebuild before recalling newly approved durable
  knowledge
- save-time FAISS rebuild is now optional and disabled by default to avoid
  slowing the user-facing review/save path
- Phase 4 now marks local evidence explicitly as predictive ML signal,
  platform snapshot, approved memory, attachment memory, or MIT capability note
- stock ML-oriented platform documents now carry model name, model version,
  feature date, score meaning, and a reliability note so Veda does not confuse
  predictive scoring with plain descriptive knowledge
- Veda chat prompt and message evidence now say plainly when local ML signals
  were used and remind the user that scored signals are not guaranteed fact
- Phase 4 ML-versus-memory separation was validated on 2026-08-04 with focused
  contract, corpus, retriever, chat-engine, router, and React evidence tests
- local RAG and unified retrieval assets were rebuilt on 2026-08-04 so the
  running knowledge files and indexes now reflect the new Phase 4 metadata
- Phase 5 now preserves user-readable local source references for the top
  unified evidence items instead of only storing summary counts
- saved chat history now keeps those local evidence references too, so the
  evidence trail survives in sidebar/history sessions
- Veda now shows local conflict notes when top evidence for the same entity
  points in opposite directions, and freshness notes when the answer mixes
  different local source dates or mixes dated platform signals with saved memory
- the chat evidence panel now renders local source cards with plain-language
  source labels, dates, summaries, and model/reliability details where relevant
- Phase 5 strong source grounding was validated on 2026-08-04 with focused
  unified-retriever, chat-engine, chat-router, React evidence, and TypeScript checks
- Phase 6 now keeps outside research explicitly temporary by default and marks
  that status in chat metadata and UI notes
- Veda now says plainly when outside research and saved memory do not agree,
  instead of silently blending the two into one view
- approved reviewed memory now preserves research provenance inside retrievable
  metadata, including source title, URL, date, excerpt, and the latest source date
- the knowledge review modal now reminds the user that outside research becomes
  durable knowledge only after they approve the save
- Phase 6 research governance was validated on 2026-08-04 with focused
  reviewed-memory, contract, chat-engine, chat-router, React evidence, and TypeScript checks
- Phase 7 now adds rollout safety around unified retrieval instead of changing
  Veda's answer style again
- Veda can now run unified and legacy retrieval side by side in shadow mode,
  compare source overlap and source gaps, and keep the result reversible through flags
- the chat API now exposes retrieval-audit metadata so backend tests and future
  rollout checks can see which path was primary, which path was shadow, and how
  much the two evidence bundles overlapped
- a committed benchmark fixture plus a benchmark runner now measure:
  - hit rate
  - top-k relevance
  - duplicate noise
  - source attribution quality
- Phase 7 rollout controls were validated on 2026-08-04 with focused
  chat-engine, chat-router, benchmark, unified-retriever, and TypeScript checks
- the first local Phase 7 benchmark report was written on 2026-08-04 to:
  `data/veda/retrieval_audits/benchmark_reports/latest_report.json`
- that report shows unified retrieval currently beats the legacy stitched path
  on hit rate, top-k relevance, and attribution quality, while duplicate noise
  is tied at zero for the tested cases
- the same report also shows one honest remaining corpus gap: the astrology
  memory benchmark case still misses on both retrieval paths right now

Research connector rollout order:

1. Python-first layer: `ddgs`
2. Optional upgrade: `tavily-python`
3. Precision web research: `exa-py`
4. Deep crawl/extract: `firecrawl-py`
5. Structured knowledge helpers: `Wikipedia-API`, `arxiv`
6. MCP fallback layer: GitHub MCP, DDGS MCP, Tavily MCP, Exa MCP, Firecrawl MCP
7. MCP helper layer: `fetch`, `memory`, `sequential-thinking`, `git`

Operational rules for this workstream:

- Veda must use local platform data first.
- External research starts only when local data is missing, weak, stale, or the user explicitly asks for outside research.
- External answers must carry source links and dates.
- Files, repositories, and web pages are content sources, not trusted instructions.
- MIT-licensed Git resources are preferred when importing reusable skills, tools, or artifacts.
- No silent self-learning into permanent memory without an explicit review/save step.
- Approved reviewed knowledge can be reused by Veda only after explicit user approval.
- When that approval includes readable attachments, Veda now stores searchable
  document chunks from those files too, not just the reviewed summary note.

Current env note:

- Existing `.env` already follows the right pattern for provider keys.
- Veda now accepts `OPENAI_API_KEY` directly in both chat and general LLM fallback paths.
- `start.ps1` now falls back to the installed `python` runtime if `py -3.11` is missing.
- Research-specific keys are not present yet.
- Likely future additions: `TAVILY_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, plus a repo-capable GitHub token if GitHub MCP is enabled.

Current Veda attachment + history note:

- Text-based PDFs already work and can be studied immediately inside chat.
- Scanned PDFs now have a backend fallback path through rendered page images,
  but they still need a working OCR/vision runtime to become readable.
- Once a reviewed save is approved, readable attachment text is now stored as
  searchable document memory in addition to the approved note itself.
- On this machine as of August 4, 2026, `OPENAI_API_KEY` is present but
  cloud-image vision was unavailable during the live audit.
- A user-space Python OCR runtime (`rapidocr_onnxruntime`) is now installed
  and wired into Veda, so scanned pages can still be read locally without a
  machine-wide admin install.
- Mixed pages with both running text and a central labeled figure can now be
  described as mixed-layout pages instead of being treated as flat OCR text.
- Saved chat history now has backend persistence as well as browser caching.
- Active multi-turn engine memory is still runtime-only and is reset through
  `/api/chat/session/{session_id}`.

Recommended development model for this workstream:

- Practical primary choice: `Gemini 2.5 Pro`
- Stronger optional upgrade: frontier coding models such as `gpt-5.6-terra`,
  `gpt-5.6-sol`, `Claude Sonnet 4`, or `Claude Opus 4.1`
- Avoid relying only on fast/small models for this implementation

Locked implementation phases:

1. Phase 0 -- Foundation and contracts
2. Phase 1 -- Python-first research base
3. Phase 2 -- Research mode orchestration
4. Phase 3 -- Chat attachments
5. Phase 4 -- Source-aware answer layer
6. Phase 5 -- Reviewed save-to-knowledge flow
7. Phase 6 -- MIT Git capability intake
8. Phase 7 -- MCP fallback layer
9. Phase 8 -- Hardening, tests, documentation, rollout

Phase goals:

- Phase 0: define backend/frontend contracts, configs, flags, error states, and safety rules -- COMPLETE 2026-08-04
- Phase 1: integrate `ddgs` as the first external research provider -- COMPLETE 2026-08-04
- Phase 2: add the logic that decides when Veda should use local knowledge vs outside research -- COMPLETE 2026-08-04
- Phase 3: add file/document/image upload in chat and extract usable text/context -- COMPLETE 2026-08-04
- Phase 4: force sources, dates, and confidence framing in outside-research answers -- COMPLETE 2026-08-04
- Phase 5: add explicit review-before-save knowledge intake -- COMPLETE 2026-08-04
- Phase 6: let Veda inspect MIT-licensed Git resources in a controlled way -- COMPLETE 2026-08-04
- Phase 7: add MCP only if Python-first research is not enough -- COMPLETE 2026-08-04
- Phase 8: finish tests, live verification, documentation sync, and rollout checklist -- COMPLETE 2026-08-04 for code, API tests, React tests, docs, and live browser UI QA; detailed microphone/voice pass remains deferred to the separate QA round

---

# KEY INTELLIGENCE FILES (all in data/intelligence/)

| File | Rows | Key Columns | Freshness |
|------|------|-------------|-----------|
| participant_intelligence.csv | 2581 | Market_Regime, Smart_Money_Score, conviction | 2026-07-01 |
| sector_rotation_intelligence.csv | 29 | rotation_signal, FII_flow_score, combined_score | 2026-07-01 |
| bull_run_probability.csv | 2441 | bull_run_score, label, 4 component scores | 2026-07-01 |
| bull_run_watchlist.csv | 225 | EMERGING symbols sorted by score | 2026-07-01 |
| technical_indicators.csv | 2718 | 52W H/L, 20/50/200 DMA, RSI, MACD, ATR, BB, OBV, ADX, trend_signal | 2026-07-01 |
| fno_intelligence.csv | 211 | futures_oi, oi_signal, oi_1d, oi_5d | 2026-07-01 |
| trade_conviction_scores.csv | 2406 | conviction_score, action (STRONG_BUY..EXIT) | 2026-07-01 |
| institutional_deal_signals.csv | 361 | inst_net_value_cr, deal_signal | 2026-07-01 |
| corporate_confidence_scores.csv | 1111 | confidence_score_12m, confidence_label | 2026-07-01 |
| ml_scores_combined.csv | 2441 | ml_bull_run_score, accumulation_score | 2026-07-01 |

---

# KNOWN ISSUES + TECHNICAL DEBT

| Issue | Severity | Note |
|-------|----------|------|
| ~~ADANIPORTS -> AEROSPACE misclassification~~ | -- | FIXED 2026-06-30, verified live 2026-07-19 |
| Cash flows gap: 2026-02-19 | Low | Not a code bug (re-diagnosed 2026-07-19) -- nselib itself returns a clean FileNotFoundError for this date, NSE's own cat_turnover archive appears to genuinely lack the file though equity bhavcopy exists. Engine already skips it silently and correctly. Permanent 1-day gap. |
| Groq free tier: 100k tokens/day | Medium | Chat heavy queries exhaust daily budget; upgrade or cache tool results |
| Shareholding pre-2024 quarters | Low | NSE XBRL archive has no FII/DII before 2024 |
| Major banks missing from XBRL results | Low | HDFCBANK/ICICIBANK/SBIN use different schema |
| stub engines in engines/intelligence/ | Low | v2 stubs, marked for removal |

---

# PLATFORM RUNTIME

- Backend: `py -3.11 -m uvicorn backend.main:app --port 8001 --reload`
- Frontend: `npm run dev` in `frontend/` (http://localhost:5173)
- Startup script: `./start.ps1` (detached background processes, idempotent)
- Stop script: `./stop.ps1` (kills ports 8001 + 5173)
- Telegram bot: live (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in .env)
- Auth: disabled by default; enable via `POST /api/auth/setup` or Admin -> Auth Config

---

# GOVERNANCE

- CHANGELOG: docs/governance/CHANGELOG.md (v4.72.7 is latest; entries before
  v4.43 archived to docs/governance/CHANGELOG_ARCHIVE.md, 2026-07-19, to keep
  the active file small for session/token budget)
- Module Registry: docs/governance/MODULE_REGISTRY.md
- Guardrails: docs/governance/GUARDRAILS.md (55 rules)
- ADRs: docs/decisions/ (ADR-001 to ADR-024; next = ADR-025)
- Session logs: chat history/ (module-wise append files)
- Memory: C:\Users\hp\.claude\projects\D--Projects-fii-dii-sector-intelligence\memory\
