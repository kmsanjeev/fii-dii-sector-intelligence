# VEDA-P000-05 AI Knowledge Audit

## AI / LLM architecture summary

AI is used in multiple distinct ways:

1. chat orchestration with tool calling and retrieval
2. attachment extraction/vision fallback
3. finance/news/governance summarization
4. optional stock-kundli narrative generation
5. pre-market brief synthesis

Astrology calculation is **not** primarily an LLM task.

## AI provider audit

### Chat engine provider set

Observed in `engines/ai/chatbot/chat_engine.py`:

- Groq
- Gemini
- Mistral
- GitHub Models
- SambaNova
- OpenRouter
- Cerebras
- OpenAI

Characteristics:

- OpenAI-compatible chat completion clients
- per-provider API key env vars
- automatic provider fallback and cooldown handling
- tool calling enabled
- voice-mode token/round reductions

### Shared LLM client provider set

Observed in `engines/common/llm_client.py`:

- Groq
- Cerebras
- Gemini
- Mistral
- GitHub Models
- SambaNova
- OpenRouter
- Together
- OpenAI

Used by:

- announcement summary
- article summary
- news sentiment engine
- concall signal engine
- AGM intelligence engine
- market brief synthesis
- kundli finance narrative

## Prompt inventory

The repository contains many prompt surfaces. This inventory focuses on operational prompts found in executed code.

| PROMPT_ID | File | Purpose | Model path | Inputs | Output | Astrology knowledge embedded | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CHAT-SYS-GREETING` | `engines/ai/chatbot/intent_router.py` | greeting voice/chat behaviour | chat engine providers | user greeting | short conversational reply | none | active |
| `CHAT-SYS-MARKET` | `engines/ai/chatbot/intent_router.py` | market assistant system prompt | chat engine providers | intent + context | tool-driven market answer | no | active |
| `CHAT-SYS-SECTOR` | same | sector research behaviour | chat engine providers | intent + context | sector answer | no | active |
| `CHAT-SYS-STOCK` | same | stock-analysis behaviour | chat engine providers | intent + context | stock answer | no | active |
| `CHAT-SYS-CORPORATE` | same | corporate-intelligence behaviour | chat engine providers | intent + context | corporate answer | no | active |
| `CHAT-SYS-RESEARCH` | same | broad retrieval/research behaviour | chat engine providers | intent + context | synthesis answer | no | active |
| `CHAT-SYS-ASTRO` | same | AstroFinance chat behaviour | chat engine providers | intent + context | market astrology answer | yes, finance rules | active |
| `CHAT-SYS-KUNDLI` | same | personal-kundli behaviour | chat engine providers | DOB/TOB/place or follow-up question | direct tool-first kundli answer | yes | active |
| `KUNDLI-FIN-NARR` | `engines/intelligence/kundli_interpretator.py` | 2-3 sentence stock-kundli narrative | shared LLM client | signal, dasha, yogas, bullish/bearish factors | short finance outlook | yes, finance astrology | active optional |
| `ANNOUNCEMENT-SUMMARY` | `backend/routers/stocks.py` | simplify NSE filing PDF into 3-part summary | shared LLM client | title + extracted text | labelled retail summary | no | active |
| `NEWS-ARTICLE-SUMMARY` | `backend/routers/stocks.py` | simplify scraped article/headline into 3-part summary | shared LLM client | headline + themes + article text | labelled retail summary | no | active |
| `NEWS-SENTIMENT` | `engines/intelligence/news_sentiment_engine.py` | symbol/theme extraction from RSS news | shared LLM client | headline + summary | structured JSON | no | active |
| `CONCALL-SIGNAL` | `engines/intelligence/concall_signal_engine.py` | management tone/capex/guidance extraction | shared LLM client | announcement text | structured JSON | no | active |
| `AGM-GOVERNANCE` | `engines/intelligence/agm_intelligence_engine.py` | governance/dividend/capex extraction | shared LLM client | announcement text | structured JSON | no | active |
| `DMB-SYNTHESIS` | `engines/briefing/dmb_engine.py` | daily market brief synthesis | shared LLM client | deterministic fact sheet | executive summary + intelligence bullets | no | active |
| `ATTACHMENT-VISION` | `engines/ai/attachments/service.py` | PDF/image extraction fallback | vision-capable provider | image/page bytes | extracted context | no | active |

## Chat orchestration audit

### Key behaviours verified

- intent detection is keyword/rule based
- retrieval context can be injected into the system prompt
- attachment context is explicitly marked as source material, not instructions
- outside research is marked temporary unless reviewed and saved
- the chat engine tracks research usage and local evidence metadata

### Kundli-specific behaviour

Critical implementation detail:

- for `KUNDLI` intent, the system prompt says to **always call** `generate_personal_kundli()` first
- if the tool returns `formatted_report`, the chat engine returns it directly with a verbatim bypass
- this means personal astrology reasoning is mostly encoded in deterministic code and templates, not post-hoc LLM improvisation

## Knowledge location map

| Knowledge area | Primary location today |
| --- | --- |
| market/sector/stock intelligence | CSV/JSON datasets under `data/intelligence` |
| platform retrieval corpus | `data/intelligence/rag_knowledge/*.jsonl`, BM25, FAISS |
| reviewed knowledge | `data/veda/knowledge_reviews/*` |
| repo capability knowledge | `data/veda/capability_reviews/*` |
| astrology sign/dignity/nakshatra/dasha tables | hard-coded Python dictionaries/functions |
| personal astrology life readings | `engines/ai/chatbot/tools/kundli_interpreter.py` |
| remedies | `kundli_calculator.py` |
| sector astrology rules | `astro_engine.py` hard-coded mappings |

## Astrology reasoning location audit

| Area | CODE | RULE TABLES | PROMPT | LLM | RAG |
| --- | --- | --- | --- | --- | --- |
| stock kundli calculation | high | high | low | low | none |
| stock finance interpretation | medium | medium | low | low/optional | none |
| personal kundli calculation | high | high | low | low | none |
| personal life reading | high | medium | very low | none for final output path | none |
| AstroFinance sector signals | high | high | none | none | none |

Conclusion:

- astrology reasoning is primarily in **code and hard-coded rule tables**
- RAG does not currently drive astrology interpretation
- LLMs are supplementary on the astrology side, not foundational

## Source-provenance audit

| Knowledge area | Source maturity | Notes |
| --- | --- | --- |
| market intelligence datasets | PARTIALLY_SOURCED | data comes from named exchanges/APIs but source metadata is not always normalized in outputs |
| reviewed knowledge memory | SOURCED at object level | reviewed records keep metadata, but not a research-grade source registry |
| personal astrology rules | UNSOURCED | classical text names appear in report prose, but not as structured verse-level provenance |
| stock-kundli finance rules | UNSOURCED | finance mappings and yoga scores are code tables without source registry |
| remedies | UNSOURCED / lightly described | Lal Kitab tradition referenced in prose, not source-managed |
| AstroFinance sector mappings | UNSOURCED | sector-ruler associations are hard-coded |

## RAG readiness audit

Requested maturity scale:

- `NONE`
- `EXPERIMENTAL`
- `PARTIAL`
- `OPERATIONAL`
- `ADVANCED`

Current assessed maturity: **PARTIAL**

| Capability | Status | Evidence |
| --- | --- | --- |
| document ingestion | yes | document builders and reviewed-memory ingestion |
| chunking | yes | attachment chunking and corpus building |
| embeddings | yes | sentence-transformers + FAISS |
| vector database | partial | FAISS file indexes, not a managed vector DB |
| lexical search | yes | BM25 |
| metadata search | partial | metadata used in unified retrieval/re-ranking |
| citation retrieval | partial | evidence metadata and source cards, but not hard citation discipline everywhere |
| source provenance | partial | platform intelligence metadata exists; astrology provenance weak |
| reranking | partial | RRF + post-rank heuristics |
| Graph RAG | no | not found |
| query rewriting | no clear evidence | not found as a first-class feature |

Why not `OPERATIONAL` overall:

- retrieval is operational for platform knowledge
- provenance/governance are not yet strong enough for research-grade astrology use

## ML readiness audit

Current assessed maturity: **PARTIAL to OPERATIONAL for market intelligence**

| Capability | Status | Evidence |
| --- | --- | --- |
| datasets | yes | feature matrix, scores, forward labels |
| labelled events | yes | forward labels and encoded bull-run labels |
| feature generation | yes | `feature_engineering.py`, `technical_feature_engine.py` |
| trained models | yes | XGBoost/LightGBM model files present |
| evaluation | partial | CV metrics and some efficacy artifacts exist |
| prediction endpoints/artifacts | yes | score CSVs loaded into platform |
| feature store | partial | file-based feature matrix, not a dedicated store |
| astrology ML | no | no evidence found |

## AI / knowledge conclusions

- AI is deeply integrated into the platform, but most heavily outside the core astrology math
- chat/retrieval/review workflows are real, tested, and operational
- personal-kundli output is intentionally protected from LLM paraphrase drift
- the repository does **not** yet implement a research-grade astrology knowledge registry
- future astrology RAG should be treated as new work, not as an already-existing subsystem
