# AI PLATFORM
## Capital Flow Intelligence Platform | Updated 2026-08-04

---

# Module Overview

The AI Platform transforms intelligence data into conversational, queryable insights.
Users interact via natural language. Agents access live data via tool calls backed by verified CSVs.

---

# Status: COMPLETE (Phases 12/13/14/D — 2026-07-09)

---

Latest approved extension: Veda Research Mode rollout completed through Phase 8
on 2026-08-04, with follow-up hardening continuing where needed.

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
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 complete
- Phase 6 complete
- Phase 7 complete
- Phase 8 implementation complete

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
- scanned PDFs now attempt rendered-page fallback through the same OCR/vision
  pipeline when embedded PDF text is missing
- local Python OCR now uses `rapidocr_onnxruntime` first, so scanned pages can
  be read without depending only on a machine-wide `tesseract` install
- when cloud vision is unavailable, Veda now adds a lightweight layout note so
  mixed pages can still be recognized as text-plus-diagram pages
- attachment content is injected into Veda as untrusted source material, not
  executable instruction

Current limitation:

- scanned documents still need a working OCR or vision runtime to become
  readable; the new local OCR path solves many cases, but visual meaning is
  still richer when cloud vision is available
- saved chat history now syncs to backend storage under
  `data/veda/chat_sessions` while keeping browser caching for fast UI loads
- saved-history ownership is user-aware: browser client id when auth is off,
  authenticated user id when auth is on

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

Status: COMPLETE (2026-08-04)

Delivered in this phase:

- assistant answers in both chat surfaces now expose a review-before-save step
- the user can edit the title, summary, facts, tags, and optional review note
  before approval
- nothing is written into durable Veda memory until that explicit approval
  happens
- approved records keep raw question/answer trace plus file and research source
  references
- when a reviewed save includes readable attachments, Veda now stores the full
  extracted file text in searchable document chunks, not only the short
  reviewed note
- before a reviewed save is approved, Veda now checks whether the same readable
  file or a very strong same-topic memory already exists
- when that overlap is found, the review step recommends `discard` or `save
  anyway` and waits for explicit user confirmation
- exact duplicate file checks now use readable extracted content, not file
  names, so renamed copies of the same book are still caught
- approved reviewed memory is immediately searchable by Veda through a
  lightweight reviewed-knowledge overlay, without silently changing the core
  indexed knowledge base
- local launch now prefers a Python runtime that already has `ddgs`, reducing
  false "research unavailable" startup states in development
- local launch now checks only `LISTENING` sockets for backend startup, which
  avoids false "already running" messages caused by dead `TIME_WAIT` ports
- backend startup dependencies now explicitly include `apscheduler` in
  `requirements.txt`, matching the scheduler import already used at runtime
- chat-provider failover now cools down bad providers after auth, connection,
  and stale-model failures instead of retrying them every turn
- long-session prompt assembly now bounds stored history, individual message
  size, and final tool-result size before remote model calls
- live Veda chat and research mode were re-verified on 2026-08-04 after
  relaunch with real network access

### Phase 6 -- MIT Git capability intake

- let Veda inspect MIT-licensed repos/resources
- extract patterns, prompts, utilities, or ideas in a controlled way
- keep license tracking visible
- separate reusable capability ideas from untrusted repo instructions

Status: COMPLETE (2026-08-04)

Delivered in this phase:

- full chat page and floating Veda widget now expose a simple "MIT Repo"
  study flow
- Phase 6 works on local cloned repo paths in this runtime; remote GitHub
  acquisition still belongs to Phase 7
- backend now rejects non-MIT repos at intake time and keeps the detected
  license path/excerpt visible in the review step
- candidate repo files are reduced to a controlled short list of prompts,
  workflows, docs, and small utility files instead of blindly trusting repo
  content
- approved MIT repo notes are saved separately from normal answer-review
  memory and become reusable Veda context only after explicit approval
- chat-engine context assembly now includes these approved MIT repo
  capability notes alongside reviewed knowledge and normal RAG context

### Phase 7 -- MCP fallback layer

- add GitHub MCP first
- then DDGS MCP / Tavily MCP / Exa MCP / Firecrawl MCP if needed
- add helper MCP servers only where they genuinely improve the flow

Status: COMPLETE (2026-08-04)

Delivered in this phase:

- Python-first research still stays the default path, but Veda can now fall
  back to MCP research servers when the primary provider cannot answer
- a lightweight MCP stdio client was added so Veda can initialize a server,
  list tools, call search-like tools, and normalize the returned results
- MCP server usage is config-driven through `VEDA_MCP_SERVER_CONFIG`,
  `VEDA_MCP_SERVER_ORDER`, and related timeout/result-limit settings
- backend chat capabilities now report whether MCP fallback is actually
  available at runtime and which server names are currently configured
- fallback results flow through the same evidence system, so the UI still shows
  provider names, links, and dates instead of hiding the source change

### Phase 8 -- Hardening and rollout

- backend tests
- frontend tests
- live browser verification
- mic/voice verification
- docs sync and release checklist

Status: IMPLEMENTATION COMPLETE (2026-08-04)

Delivered in this phase:

- the research service now falls back to MCP even when the primary research
  provider is unavailable, not only when it returns empty results
- chat API coverage was expanded with focused tests for capability reporting,
  config fallback, and attachment gating
- the backend/frontend capability contract now exposes live research readiness,
  so Veda can show when research exists as a feature but is not usable in the
  current runtime
- the shared Veda store now keeps attachment accept rules in sync with backend
  capabilities instead of hardcoding them separately in each chat surface
- research-mode tooltips in both chat surfaces now reflect when MCP fallback is
  ready in the runtime
- a real React test stack is now wired in with Vitest + Testing Library
- focused Veda React tests now cover research readiness, research fallback
  evidence, and the main chat surfaces
- a rollout checklist was added at
  `docs/governance/VEDA_PHASE8_ROLLOUT.md`
- live HTTP smoke was completed against the running local frontend/backend on
  2026-08-04

Important note:

- the separate detailed browser + microphone acceptance round is intentionally
  left to the later human QA pass requested for this project
- browser UI QA has now passed through Selenium on 2026-08-04

### Phase 9 -- P020 governance foundation

- build shadow-only career, education, and wealth synthesis governance
- preserve fact, rule, signal, and conflict separation
- keep runtime activation unchanged

Status: COMPLETE (2026-08-14)
- the remaining open live QA scope is microphone capture and spoken-audio
  behavior

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
