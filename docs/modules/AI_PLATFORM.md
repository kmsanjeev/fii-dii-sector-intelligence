# AI PLATFORM
## Capital Flow Intelligence Platform | Updated 2026-07-09

---

# Module Overview

The AI Platform transforms intelligence data into conversational, queryable insights.
Users interact via natural language. Agents access live data via tool calls backed by verified CSVs.

---

# Status: COMPLETE (Phases 12/13/14/D — 2026-07-09)

---

# Vision

Answer these questions from live data, not training data:
- "Where is FII putting money this week?"
- "Which stocks are in EARLY_ROTATION sectors?"
- "Why is ADANIENSOL on the watchlist?"
- "What changed in the market today?"

---

# Architecture

```
User Query
    |
Intent Router (classify: market / sector / stock / corporate / research)
    |
RAG Retrieval (hybrid FAISS + BM25, 5-10 context chunks)
    |
Agent (Groq llama-3.3-70b-versatile via llm_client.py multi-provider fallback)
    |
Tool Calls (live data: get_regime, get_sector_flow, get_stock_score, etc.)
    |
Grounded Response with citations
```

---

# 5 Specialized Agents

| Agent | Purpose | Primary Tools |
|-------|---------|---------------|
| MarketAgent | Regime, participant flows, macro | get_market_regime, get_participant_intel |
| SectorAgent | Rotation signals, sector flows | get_sector_flows, get_sector_history |
| StockAgent | Bull run scores, entry points | get_stock_score, get_watchlist |
| CorporateAgent | Deal signals, event calendar | get_deals, get_upcoming_events |
| ResearchAgent | Deep cross-layer analysis (Opus 4.8) | all tools |

---

# Tool Registry

```python
get_market_regime()              -> regime, scores, date
get_sector_flows(sector=None)    -> rotation signals, FII flow scores
get_stock_score(symbol)          -> bull run components + label
get_watchlist(label="EMERGING")  -> sorted watchlist
get_deals(symbol, min_cr=50)     -> institutional deal signals
get_upcoming_events(days=30)     -> catalyst calendar
```

---

# LLM Configuration

**Primary:** Groq `llama-3.3-70b-versatile` (free tier, 100k tokens/day)
**Fallback chain:** Groq → Cerebras → Gemini → OpenRouter (via `engines/common/llm_client.py`)
**Anthropic API:** retained for Phase 16 management sentiment only — NOT used for chatbot
API keys: `GROQ_API_KEY` (chatbot), `ANTHROPIC_API_KEY` (sentiment) — from os.getenv() — NEVER hardcoded

System prompt injects:
- Current date + market regime
- Top 3 EMERGING symbols
- Last updated timestamps for all data sources

Implementation notes:
- Tool calling format: Groq/OpenAI function calling (converted from Anthropic format at module load)
- `parallel_tool_calls=False` to prevent Llama XML-style function call bug
- `MAX_TOOL_ROUNDS=3` (conserve 100k/day free tier budget)
- 429 rate limit caught → user-readable message returned
- `tool_use_failed` 400 error → fallback to clean prompt with tool results only

---

# Build Phases

Phase 14A: Intent router + tool registry + MarketAgent + SectorAgent
Phase 14B: StockAgent + CorporateAgent
Phase 14C: ResearchAgent (Opus) + conversation memory
Phase 14D: WebSocket integration (FastAPI /ws/chat)
Phase 14E: GUI-9 React chat UI

---

# Dependencies

- Phase 10 (FastAPI Backend) — tool data endpoints
- Phase 13 (RAG Knowledge Base) — context retrieval
- ANTHROPIC_API_KEY environment variable

---

# Directory

engines/ai/chatbot/
  intent_router.py
  chat_engine.py
  agents/
  tools/
  memory/

---

# Packages

anthropic (Claude API SDK)
