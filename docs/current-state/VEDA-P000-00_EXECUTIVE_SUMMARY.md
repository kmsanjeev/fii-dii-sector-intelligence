# VEDA-P000-00 Executive Summary

Audit date: 2026-08-10
Repository audited: `D:\Projects\fii-dii-sector-intelligence`
Audit mode: read-only inspection of repository and live runtime

## What VEDA is today

VEDA is not a pure astrology application.

As of 2026-08-10, the repository and live runtime show a broader **Capital Flow Intelligence Platform** with an embedded **VEDA** research/chat layer and embedded astrology features:

- institutional market-intelligence platform for Indian equities
- React frontend + FastAPI backend
- large file-based intelligence pipeline under `data/`
- VEDA chat/research subsystem with local retrieval, attachment handling, reviewed memory, and external web research
- two active astrology surfaces:
  - stock/country/human REST kundli + Gann endpoints
  - richer personal-kundli toolchain inside chat

The backend root response is `{"name":"Capital Flow Intelligence Platform","version":"1.0.0"}`. The authoritative application identity in code is therefore broader than the astrology label.

## Does the existing application genuinely run

Yes, with conditions.

Runtime evidence observed on 2026-08-10:

- frontend dev server responded on `http://127.0.0.1:5173`
- backend responded on `http://127.0.0.1:8001`
- `GET /health` returned `200` with `datasets_loaded: 41` and `datasets_total: 43`
- `GET /openapi.json` returned a live FastAPI schema with `137` mounted endpoints
- kundli bulk status returned `2053` generated stock kundli JSON files

Validation status:

- frontend build: passes
- frontend tests: pass (`16/16`)
- frontend lint: passes with warnings
- Python tests: mostly pass but not clean (`331` passed, `8` failed, `339` total)

## Current-state headline findings

### Major capabilities already working

- market, sector, stock, corporate, portfolio, risk, research, broker, execution, backtest, themes, voice, auth/admin, and chat surfaces are all mounted in the live backend
- stock kundli, country kundli, human kundli, Gann analysis, and bulk kundli cache are operational
- AstroFinance sector signal layer is present and connected to frontend stock/thematic reporting
- local hybrid retrieval exists with persisted BM25 and FAISS indexes and a live "research runtime ready" status
- ML scoring exists with persisted models, feature matrix artifacts, and daily inference wiring

### Astrology foundations that are relatively trustworthy

These are implemented in executed code, not only documentation:

- Swiss Ephemeris via `pyswisseph`
- sidereal mode explicitly set to Lahiri
- deterministic planetary longitude calculation
- Lagna calculation
- whole-sign style house assignment downstream of Lagna sign
- Vimshottari dasha in both stock and personal flows
- persistent stock-kundli generation for thousands of symbols

### Capabilities that are partial, duplicated, or fragile

- astrology exists in **multiple partially overlapping engines**
  - `engines/intelligence/kundli_engine.py`
  - `engines/ai/chatbot/tools/kundli_calculator.py`
  - `engines/intelligence/astro_engine.py`
- personal astrology coverage is richer in chat than in REST
- stock astrology is finance-specific, not a general Jyotisha platform
- timezone handling in the stock kundli engine uses fixed UTC-offset maps rather than timezone database logic
- the stock transit classifier uses angular aspect labels like conjunction, square, trine, opposition, not a full classical transit framework

### Capabilities that exist mainly in docs or intent, not proved complete in code

- research-governed source registry for astrology rules
- machine-readable classical source provenance
- RAG over a structured Jyotisha corpus
- ML for astrology outcomes
- research-grade validation datasets for kundli predictions
- broad classical modules such as Shadbala, Ashtakavarga, Jaimini, Muhurta, compatibility, and multiple dasha families

## Deterministic vs LLM-generated behaviour

| Area | Primary mode today |
| --- | --- |
| stock/country/human kundli math | deterministic code |
| personal-kundli report body | deterministic formatted text generated from code |
| stock financial-kundli narrative | optional LLM add-on |
| chat orchestration | LLM + tool calling |
| announcement/news/concall/AGM summaries | LLM |
| retrieval context | deterministic local retrieval |
| AstroFinance sector scoring | deterministic code |

Important distinction:

- **personal-kundli chat responses are not primarily freeform LLM reasoning**
- the chat engine is explicitly instructed to call `generate_personal_kundli()` first and return the tool's `formatted_report` verbatim when available

## RAG and ML readiness

### RAG

Current maturity: **PARTIAL to OPERATIONAL**

Evidence:

- document builders
- BM25 indexers
- FAISS indexers
- unified retriever
- reviewed knowledge store
- attachment ingestion
- live chat capability flag reporting research runtime ready

Constraints:

- the current RAG corpus is primarily market/platform intelligence, not a sourced Jyotisha knowledge base
- source provenance for astrology is weak

### ML

Current maturity: **PARTIAL to OPERATIONAL for market scoring, not astrology**

Evidence:

- feature engineering code
- label generation
- accumulation model
- bull-run model
- forward-return model
- persisted trained models under `data/intelligence/ml_features/models`
- live ML score artifacts loaded by the platform

Constraints:

- no astrology ML pipeline
- no evidence of labelled kundli outcome datasets

## Most fragile areas

- checked-in secrets in `.env`
- auth disabled by default
- default bootstrap admin password when auth is enabled without proper env vars
- durable storage of chat sessions, uploaded files, and voice conversation logs
- duplicate astrology logic across REST and chat paths
- scheduled background work starts with the backend and can mutate local data outside the audit
- Python test drift concentrated in the chat engine suite

## Components that should be preserved

- Swiss-Ephemeris-based calculation core
- cached stock kundli generation pipeline
- existing bulk kundli JSON corpus and CSV summaries
- frontend stock report/kundli integration
- unified retrieval and knowledge review workflow
- file-based intelligence pipeline and scheduler wiring until governed replacements exist

## What should be built next

The evidence supports **PRESERVE -> VALIDATE -> EXTEND**, not rewrite.

Immediate next programme after VEDA-P000 should be:

1. baseline governance and regression protection
2. source and knowledge governance for astrology
3. validation of existing calculation foundations before new astrology expansion
4. validation of the current interpretation/reporting layers
5. only then targeted expansion into additional classical modules, sourced RAG, or ML

## Executive verdict

Recommended audit verdict: **PASS WITH CONDITIONS**

Reason:

- the running system can be mapped with high confidence
- the live application is operational
- the astrology and AI surfaces are sufficiently understood to authorize a governed next phase
- but security, provenance, duplicated astrology logic, and test drift must be explicitly controlled before risky modifications
