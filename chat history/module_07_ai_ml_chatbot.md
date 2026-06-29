# Chat History — Module 07/14/15/16: AI Platform + ML + Chatbot

> **Append-only. Add new entries at the bottom. Never overwrite.**
> Covers: AI Platform (M07), ML Intelligence (M14), RAG Knowledge Base (M15), Chatbot (M16)

---

## Session: 2026-06-29 — ML/AI/Chatbot Architecture Design

### Context
User requested: "Kindly add Machine learning, AI & chatbot in the project and update the roadmap & necessary md files accordingly and share the final roadmap once prepared."

### Decisions Made

**LLM Selection:** Claude API `claude-sonnet-4-6` as default, `claude-opus-4-8` for deep analysis.  
API key read from `os.getenv("ANTHROPIC_API_KEY")` — never hardcoded.

**ML Stack (Module 14):**
- XGBoost + LightGBM ensemble for accumulation detection (target: price_up_10pct_in_20d)
- LightGBM multi-class for sector rotation prediction (29 sectors)
- Isolation Forest for anomaly detection in institutional flows
- sentence-transformers (cosine similarity) for company classification — fixes the ADANIPORTS→AEROSPACE bug and the 37% classification coverage gap
- All in `engines/ml/`; features stored as Parquet in `data/intelligence/ml_features/`

**RAG Stack (Module 15):**
- 6 FAISS indexes by domain (market, sectors, themes, stocks, fundamentals, research)
- Hybrid retrieval: Dense (sentence-transformers) + BM25 (rank-bm25) via Reciprocal Rank Fusion
- RAG-1 can begin immediately (Phase 3B outputs available); full indexing unblocks after Phase 4A
- Engines in `engines/ai/knowledge/`

**Chatbot Stack (Module 16):**
- 7 specialized agents (Market, Sector, Theme, Stock, Portfolio, Research, Dev CTO)
- Intent router: regex pattern matching → agent dispatch
- Tool registry: Claude API tool use spec for live data (sector flows, stock scores, regime)
- Conversation memory: short-term (last 20 turns, auto-summarize) + long-term (JSON preferences)
- WebSocket endpoint: `/ws/chat/{session_id}` via FastAPI
- React UI: GUI-9 in the GUI plan
- Engines in `engines/ai/chatbot/`

### Files Created / Modified
| File | Action |
|------|--------|
| `docs/architecture/ML_AI_CHATBOT_ARCHITECTURE.md` | Created — 8-section full spec |
| `docs/governance/MODULE_REGISTRY.md` | Added Modules 14, 15, 16; updated overall % to 22% |
| `docs/governance/CHANGELOG.md` | Added v2.3 |
| `memory/project_fii_dii.md` | Updated with ML/AI/Chatbot section |
| `chat history/module_07_ai_ml_chatbot.md` | Created (this file) |

### Build Phases Defined

**ML (Module 14):** ML-1 → ML-6 (depends on Phase 4A)  
**RAG (Module 15):** RAG-1 → RAG-3 (RAG-1 can start now)  
**Chatbot (Module 16):** CB-1 → CB-6 (depends on RAG-3 + any 3 intelligence engines)

### Key Dependencies
- ML-1 cannot start until Phase 4A (Company Fundamentals Master Engine) is complete
- RAG-1 CAN start now — Phase 3B outputs exist
- CB-1 can start after RAG-3 + any 3 intelligence engine outputs

### Next Actions for This Module
1. After Phase 4A → begin ML-1 (feature engineering pipeline)
2. Parallel track: begin RAG-1 (FAISS indexer for existing intelligence outputs)
3. CB-1 intent router can be built as a stub for early testing with mock agent responses

---
