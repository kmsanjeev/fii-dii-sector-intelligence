# Modules 13-16 -- RAG, Chatbot, Financial Results, Management Intelligence
## Phases 13-16 Complete | 2026-06-30

---

## Phase 13 -- RAG Knowledge Base

engines/ai/knowledge/
  __init__.py
  document_builder.py   <- Phase 13A: 1091 text docs from intelligence CSVs
  bm25_indexer.py       <- Phase 13B: BM25Okapi sparse keyword index
  faiss_indexer.py      <- Phase 13C: sentence-transformers dense, 6 domain indexes
  retriever.py          <- Phase 13D: RRF hybrid fusion (BM25 + FAISS)
  index_updater.py      <- Phase 13E: daily rebuild pipeline

### Packages Installed

sentence-transformers==5.6.0
faiss-cpu==1.14.3
rank-bm25==0.2.2

### Document Builder (Phase 13A)

Converts 6 intelligence CSVs to 1091 structured text documents:
  - 1 MARKET document (regime, FII/DII scores)
  - 29 SECTOR documents (rotation signal, flow scores, top stocks)
  - 500 STOCK documents (top EMERGING + STRONG_CANDIDATE + WATCHLIST by score)
  - N DEAL documents (institutional deal signals)
  - 200 CORPORATE documents (top by confidence_score_12m)

### BM25 Indexer (Phase 13B)

BM25Okapi over all 1091 docs. Output: bm25_index.pkl
Tokenizer: lowercase, re.findall('[a-z0-9_]+') -- keeps EARLY_ROTATION intact.
Query tested: 'FII buying EARLY_ROTATION sector' -> top: sector_media (EARLY_ROTATION)

### FAISS Indexer (Phase 13C)

Model: all-MiniLM-L6-v2 (sentence-transformers)
6 indexes: ALL, MARKET, SECTOR, STOCK, DEAL, CORPORATE
Flat index for n < nlist*40 (avoids IVF clustering warnings on small collections)
Output: data/intelligence/rag_knowledge/faiss/*.index + *_ids.json

### Hybrid Retriever (Phase 13D)

RRF(k=60) fuses BM25 + FAISS rankings by doc_id
Domain auto-detection from keyword matching
Methods: retrieve(query, domain=None), retrieve_by_domain(query, domain, top_k)

### Index Updater (Phase 13E)

Orchestrates: DocumentBuilder -> BM25Indexer -> FAISSIndexer
Smoke test: retrieve 'What is the market regime today?' -> market_regime, sector_aviation, sector_amc

---

## Phase 14 -- AI Chatbot

engines/ai/chatbot/
  __init__.py
  intent_router.py      <- Phase 14B: keyword intent detection
  chat_engine.py        <- Phase 14C: Claude API multi-turn + RAG + tool use
  agents/__init__.py
  tools/__init__.py
  tools/data_tools.py   <- Phase 14A: 11 data access functions
  tools/tool_registry.py <- Phase 14A: Anthropic API tool schemas

backend/routers/chat.py <- Phase 14D: POST /api/chat, in-memory sessions

### Security Guardrail

ANTHROPIC_API_KEY always from os.getenv() -- never hardcoded.
ChatEngine raises EnvironmentError at init if key not set.

### Intent Router

5 intents: MARKET, SECTOR, STOCK, CORPORATE, RESEARCH
Keyword scoring: 0-3+ matches -> confidence 0.3-1.0
Domain-specific system prompts injected per intent

### Tool Registry (11 tools)

get_market_regime, get_participant_history,
get_all_sectors, get_sector_detail, get_sectors_by_signal,
get_top_stocks, get_stock_detail, get_stocks_by_sector,
get_institutional_deals, get_top_corporate_confidence, get_corporate_catalysts

### Chat Engine

Model: claude-sonnet-4-6
Max tool rounds: 5 (prevent infinite loops)
RAG context: top 3 docs injected in system prompt
Session history: maintained in ChatEngine.history list

### Tests

- EnvironmentError raised correctly on missing API key
- Intent router tested on 5 queries: correct domain detection for MARKET, SECTOR, CORPORATE
- Tool data_tools.py: get_market_regime() = NEUTRAL, FII=10.91
- get_top_stocks('EMERGING') = [ADANIENSOL, ADANIENT, GMRAIRPORT, ...]
- Chat router routes: ['/chat', '/chat/session/{session_id}'] confirmed

---

## Phase 15 -- Financial Results + Valuation Engine

engines/fundamentals/
  financial_results_engine.py  <- bulk nselib + yfinance fallback
  valuation_engine.py          <- P/E + ROE + growth scoring

### Financial Results Engine (Phase 15A)

Primary: nselib financial_results_for_equity (bulk, date-range)
  - Fetches all companies for 4 quarters: Q1-Q4 FY2026
  - NSE XBRL archive endpoint intermittently returns 404 (known issue)
Fallback: yfinance per-symbol quarterly_income_stmt
Output: data/NSE/results/quarterly_results.csv
Symbols: 2123 EQ-series (from equity_master.csv)

### Valuation Engine (Phase 15B)

Reads quarterly_results.csv, computes:
  - TTM revenue and profit (sum of last 4 quarters)
  - YoY growth (requires 8+ quarters)
  - P/E ratio (latest_close / eps_ttm)
  - ROE proxy (profit_ttm / revenue_ttm)
  - Composite valuation_score (0-100)
  - Labels: CHEAP_QUALITY, FAIR_VALUE, MODERATE, EXPENSIVE_OR_WEAK

Weights: P/E score 40% + ROE score 40% + growth score 20%
Output: data/NSE/results/valuation_scores.csv

---

## Phase 16 -- Management Intelligence

engines/management/
  __init__.py
  holding_trend_engine.py         <- QoQ stake change signals
  announcement_fetcher.py         <- board meeting classification
  management_sentiment_engine.py  <- composite score + optional Claude AI tone

### Holding Trend Engine (Phase 16A)

Data source: nselib shareholding_patterns() per symbol
7 conviction signals:
  STRONG_PROMOTER_FII_BUY (promoter +1%+ AND fii +0.5%+)
  FII_DII_ACCUMULATION (both +0.5%+)
  STRONG_PROMOTER_BUY (promoter +1%+)
  FII_ACCUMULATION (fii +0.5%+)
  DII_ACCUMULATION (dii +0.5%+)
  FII_DII_DIVERGENCE (FII buying + DII selling)
  PROMOTER_SELLING (promoter -1%+)
  STABLE (no significant change)

### Announcement Fetcher (Phase 16B)

nselib board_meeting_detail() or corporate_actions() per symbol
8 announcement types: DIVIDEND, BUYBACK, BONUS, STOCK_SPLIT, AGM_EGM,
                       BOARD_MEETING, ACQUISITION, FUNDRAISE

### Management Sentiment Engine (Phase 16C)

Rule-based score (use_ai=False or no API key):
  management_score = 0.6 * holding_score + 0.4 * announcement_score
AI-enhanced score (ANTHROPIC_API_KEY set):
  management_score = 0.4 * holding_score + 0.25 * announcement_score + 0.35 * ai_tone_score
  Model: claude-haiku-4-5-20251001 for cost efficiency
  Processes top 50 symbols only (budget constraint)

Labels: HIGH_CONVICTION (>=75), POSITIVE (>=55), NEUTRAL (>=35), WEAK (<35)

---

## Session Errors and Fixes

1. NSE XBRL endpoint 404:
   - nselib financial_results_for_equity uses nsearchives.nseindia.com/corporate/xbrl/
   - Returns 404 intermittently (not a code bug, infrastructure issue)
   - Fix: engine handles gracefully, logs warning, returns False without crash

2. FAISS IVF clustering warnings:
   - "WARNING clustering N points to 64 centroids: please provide at least 2496 training points"
   - Fix: only use IVF when n >= nlist*40, use flat index for smaller collections

3. Config attribute typo:
   - financial_results_engine.py used cfg.NSE_EQUITY_MASTER_DIR (doesn't exist)
   - Fix: changed to cfg.EQUITY_MASTER_DIR

4. CORS methods:
   - backend/main.py only allowed GET method
   - Fix: added POST, DELETE for chat endpoints
