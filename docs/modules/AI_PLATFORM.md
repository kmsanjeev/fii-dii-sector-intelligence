# AI PLATFORM
## Capital Flow Intelligence Platform | Updated 2026-06-30

---

# Module Overview

The AI Platform transforms intelligence data into conversational, queryable insights.
Users interact via natural language. Agents access live data via tool calls backed by verified CSVs.

---

# Status: NOT STARTED (Phase 14, after FastAPI + RAG)

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
Agent (Claude API claude-sonnet-4-6)
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

Default: claude-sonnet-4-6 (fast, accurate for structured data)
Deep analysis (ResearchAgent only): claude-opus-4-8
API key: ANTHROPIC_API_KEY from os.getenv() — NEVER hardcoded

System prompt injects:
- Current date + market regime
- Top 3 EMERGING symbols
- Last updated timestamps for all data sources

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
