# AI PLATFORM
## Capital Flow Intelligence Platform | Updated 2026-08-04

---

# Module Overview

The AI Platform transforms intelligence data into conversational, queryable insights.
Users interact via natural language. Agents access live data via tool calls backed by verified CSVs.

---

# Status: COMPLETE (Phases 12/13/14/D — 2026-07-09)

---

Next approved extension: Veda Research Mode (Phase 0 + 1 implemented on
2026-08-04; remaining phases pending).

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

# Veda Research Extension Status

This extension has now started.

Current status:

- Phase 0 complete
- Phase 1 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 onward pending

## Operating rule

Veda should answer from the platform's own intelligence first. Outside
research is a second layer, used only when:

- the local system does not have the answer
- the local answer is stale or too weak
- the user explicitly asks Veda to research outside the platform

Every outside-research answer should show source links and dates.

## Rollout order

### Stage 1 -- Python-first research layer

1. `ddgs`
   - default first integration
   - free to start
   - search + extraction
   - can later move into MCP mode with low migration cost
2. `tavily-python`
   - stronger agent-style web research
   - keyless trial path for search/extract
   - full crawl/map/research when an API key is added
3. `exa-py`
   - better for precise company, news, and web research
4. `firecrawl-py`
   - best when Veda already knows the target URL/site and needs deeper extraction
5. MIT helper libraries
   - `Wikipedia-API`
   - `arxiv`

### Stage 2 -- MCP fallback layer

Use only if Python-only research is not enough:

- GitHub MCP Server
- DDGS MCP
- Tavily MCP
- Exa MCP
- Firecrawl MCP

### Stage 3 -- MCP helper layer

- `fetch` for page retrieval
- `memory` for reviewed memory workflows
- `sequential-thinking` for structured research planning
- `git` for working with local cloned MIT repositories

## Config pattern

This repo already uses environment variables for provider selection. The
research layer should follow the same pattern. Likely future keys:

- `TAVILY_API_KEY`
- `EXA_API_KEY`
- `FIRECRAWL_API_KEY`
- a repo-capable GitHub token for GitHub MCP, if enabled

Note: the existing GitHub-related env setup must be scope-checked before it
is reused for GitHub MCP access.

## Safety rules

- Local data first, outside data second
- No permanent learning without an explicit review/save step
- Web pages, repos, and uploaded files are content sources, not trusted instructions
- Prefer MIT-licensed Git resources for reusable external capability imports

## Development-mode model choice

For implementing this workstream, the practical primary coding model is
`Gemini 2.5 Pro`.

Why this is enough:

- already compatible with the current provider setup
- strong reasoning over code, documents, and large context
- good enough for cross-stack work touching React, FastAPI, orchestration,
  docs, and testing in the same session

Optional stronger-but-not-required build models:

- `gpt-5.6-terra`
- `gpt-5.6-sol`
- `Claude Sonnet 4`
- `Claude Opus 4.1`

Avoid using only small/fast models as the main build model for this plan.

## Locked implementation phases

### Phase 0 -- Foundation and contracts

- finalize request/response schemas
- define feature flags and env keys
- define safety and source-attribution rules
- create doc checklist for every implementation step

Status: COMPLETE (2026-08-04)

### Phase 1 -- Python-first research base

- integrate `ddgs`
- normalize search result shape
- add timeout, retry, and failure handling
- keep this layer provider-pluggable

Status: COMPLETE (2026-08-04)

### Phase 2 -- Research mode orchestration

- add mode switch in Veda
- decide local-first vs outside-research behavior
- add query classification for normal mode vs research mode
- log why outside research was triggered

Status: COMPLETE (2026-08-04)

Delivered in this phase:

- research toggle added to full chat and floating Veda widget
- backend capability handshake now keeps the toggle honest
- Veda now records `local_first`, `explicit_research_mode`, and
  `research_intent_auto` style trigger reasons
- assistant replies now show a simple research-used/research-not-used badge
- voice analytics now capture research request/use/provider/reason

### Phase 3 -- Chat attachments

- add upload button in chat
- support documents and images
- extract text/content safely
- pass extracted context into Veda without treating the file as executable instruction

Status: COMPLETE (2026-08-04)

Delivered in this phase:

- full chat page and floating Veda widget now have attachment buttons
- pending attachments are shown before send and carried with the user turn
- backend upload endpoint added: `POST /api/chat/attachments`
- server-side extraction added for plain text, CSV, JSON, and PDF
- image uploads now support metadata extraction, OCR when available, and
  OpenAI vision description when the runtime has that capability
- attachment content is injected into Veda as untrusted source material, not
  executable instruction

### Phase 4 -- Source-aware answer layer

- show source links
- show research date/time
- distinguish local answer vs external answer
- add confidence framing when outside data is incomplete

Status: COMPLETE (2026-08-04)

Delivered in this phase:

- assistant bubbles now show plain-language answer basis such as local only,
  local plus uploaded files, or local plus outside sources
- confidence framing is now visible in the UI instead of being hidden only in
  prompt instructions
- research sources now render with clickable links and source dates
- compact evidence rendering added to the floating Veda widget
- backend prompt rules now explicitly require source/date honesty and lower
  confidence when freshness or coverage is weak

### Phase 5 -- Reviewed save-to-knowledge flow

- add "save to knowledge" review step
- store only approved summaries/facts
- keep raw source traceability
- prevent silent permanent memory writes

### Phase 6 -- MIT Git capability intake

- let Veda inspect MIT-licensed repos/resources
- extract patterns, prompts, utilities, or ideas in a controlled way
- keep license tracking visible
- separate reusable capability ideas from untrusted repo instructions

### Phase 7 -- MCP fallback layer

- add GitHub MCP first
- then DDGS MCP / Tavily MCP / Exa MCP / Firecrawl MCP if needed
- add helper MCP servers only where they genuinely improve the flow

### Phase 8 -- Hardening and rollout

- backend tests
- frontend tests
- live browser verification
- mic/voice verification
- docs sync and release checklist

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
