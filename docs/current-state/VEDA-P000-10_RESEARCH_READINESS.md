# VEDA-P000-10 Research Readiness

## Knowledge-location map

| Knowledge Area | Current Location | Form | State |
| --- | --- | --- | --- |
| stock/country kundli rules | `engines/intelligence/kundli_engine.py` | Python functions + hardcoded tables | active, unsourced |
| personal-kundli rules | `engines/ai/chatbot/tools/kundli_calculator.py`, `kundli_interpreter.py`, `kundli_life_guide.py` | Python functions + narrative templates | active, unsourced |
| financial astrology heuristics | `engines/intelligence/kundli_engine.py`, `astro_engine.py`, `kundli_interpretator.py` | Python scoring logic + prompt | active, unsourced |
| Nakshatra metadata | `kundli_engine.py` and personal calculator | Python dictionaries | active, partial |
| Yoga / dosha conditions | stock and personal kundli code paths | Python conditionals | active, partial |
| Dasha logic | stock and personal kundli code paths | Python calculation functions | active, partial |
| Gann logic | `engines/intelligence/gann_engine.py` | Python calculation functions | active, unsourced |
| reviewed knowledge memory | `data/veda/knowledge_reviews/*` | JSON review records + approved notes | active |
| repo capability memory | `data/veda/capability_reviews/*` | JSON review records + approved notes | active |
| retrieval corpus | `data/intelligence/rag_knowledge/*` | text docs + BM25/FAISS artifacts | active, market/platform-focused |
| prompts | `engines/ai/chatbot/intent_router.py`, backend routers, intelligence engines | inline strings | active, duplicated |

## Source provenance audit

Classification scale:

- `SOURCED`
- `PARTIALLY_SOURCED`
- `UNSOURCED`
- `UNKNOWN`

| Knowledge Area | Classification | Evidence |
| --- | --- | --- |
| ephemeris / astronomical dependency | PARTIALLY_SOURCED | computational dependency is explicit (`swisseph`), but classical/authoritative source linkage is not recorded |
| Graha interpretation rules | UNSOURCED | hardcoded logic without verse/authority metadata |
| Rashi dignity/lordship tables | UNSOURCED | hardcoded tables, no source registry |
| Bhava interpretations | UNSOURCED | narrative/rule logic exists but without provenance |
| Nakshatra interpretations | UNSOURCED | partial metadata exists, no source attribution |
| Dasha interpretation | UNSOURCED | calculation present, source-linked interpretive layer absent |
| Yoga / dosha detection | UNSOURCED | conditions implemented without chapter/verse metadata |
| remedies | UNSOURCED | Lal Kitab-style remedies present without provenance or validation notes |
| AstroFinance mappings | UNSOURCED | sector-ruler mappings and scoring logic are hardcoded |
| reviewed knowledge memory | PARTIALLY_SOURCED | review metadata exists, but not a formal astrology authority schema |

## RAG readiness audit

Current maturity: `PARTIAL`

### Evidence present today

- document builders
- unified BM25 indexer
- unified FAISS indexer
- unified retriever
- reviewed-memory save/approve workflow
- durable corpus artifacts under `data/intelligence/rag_knowledge/`
- live runtime readiness flag in `/api/chat/capabilities`

### Missing for research-grade astrology RAG

- curated Jyotisha corpus
- source IDs and passage IDs
- author/work/chapter/verse metadata
- contradiction-aware retrieval policy
- citation-grade answer enforcement
- provenance-aware reranking
- explicit separation of source text, translation, commentary, and internal notes

### RAG verdict

The repo already contains a reusable retrieval substrate, but not an astrology-ready knowledge base.

Recommended future posture:

- reuse the current retrieval infrastructure
- do not claim astrology RAG exists yet
- add source governance before adding embeddings

## ML readiness audit

Current maturity:

- market intelligence ML: `PARTIAL` to `OPERATIONAL`
- astrology ML: `NONE`

### Evidence present today

- feature engineering
- label generation
- persisted market models
- inference scoring
- daily pipeline integration

### Missing for astrology ML

- labelled horoscope outcomes
- feature schema for chart factors
- outcome definitions and data-governance policy
- benchmark datasets
- evaluation framework
- ethical/safety boundaries

### ML verdict

The project is ML-capable in platform terms, but not astrology-ML-ready.

## Research-to-engineering boundary audit

Target lifecycle requested by programme:

```text
SOURCE
  -> RESEARCH
  -> CROSS-VALIDATION
  -> APPROVED KNOWLEDGE
  -> MACHINE-READABLE RULE
  -> IMPLEMENTATION
  -> TEST
  -> VALIDATION
  -> RELEASE
```

### What the current repo already supports

- review-and-approve workflow concepts
- durable storage for reviewed knowledge
- retrieval substrate
- modular code locations where rules can later be externalized
- existing docs/governance folders that can host source registries and acceptance records

### What is missing

- authoritative astrology source registry
- machine-readable rule schema
- explicit approval states for knowledge before implementation
- regression fixture library for astrology outputs
- clear separation between deterministic rules and LLM-generated language

### Boundary verdict

The architecture can support the requested lifecycle, but only after governance layers are added.

## Development gates

| Gate | Meaning | What should satisfy it in VEDA |
| --- | --- | --- |
| Gate A | Research Approved | source artifact recorded with authority metadata and review sign-off |
| Gate B | Architecture Approved | chosen module boundary and data contract documented |
| Gate C | Code Complete | implementation done in the authorized module set only |
| Gate D | Technical Validation | tests, build, lint, and runtime smoke checks pass |
| Gate E | Knowledge Validation | implementation checked against approved source notes |
| Gate F | Regression Validation | existing kundli/API/frontend outputs remain within accepted baseline |
| Gate G | Release Approved | final audit of risk, docs, and deployment readiness complete |

## Regression protection strategy

| Protection | Why Needed Before Risky Change | Current State |
| --- | --- | --- |
| stock kundli golden fixtures | protect existing 2053-symbol corpus behaviour | missing |
| personal-kundli golden fixtures | protect formatted report and life-domain outputs | missing |
| API contract tests for kundli/chat/auth/data routes | protect route consumers and auth mode behaviour | partial |
| bulk artifact snapshots | protect scheduled-pipeline outputs | partial |
| frontend report/chat snapshots | protect visible VEDA surfaces | partial |
| timezone and ephemeris fixture tests | protect foundational chart math | missing |
| secure secret handling and backup policy | protect credentials and local state | weak |
| chat-engine regression tests aligned to current behaviour | repair the current failing suite concentration | partial |

## Recommended Claude + Codex development model

### Claude

- research interpretation
- architecture and governance decisions
- cross-module design
- evidence review and acceptance gating

### Codex

- targeted implementation inside approved modules
- fixture generation
- contract tests
- mechanical refactors only when explicitly authorized
- focused bug fixes after gate approval

### Final review

- compare implementation against approved sources
- verify no regression against preserved baselines
- confirm module scope and docs were updated

## Research readiness conclusion

VEDA does not yet have a research-grade astrology knowledge layer.

It does already have:

- a working runtime
- a working review pattern
- a working retrieval substrate
- working deterministic chart calculation

That makes it suitable for a governed research programme, but not for uncontrolled feature expansion.
