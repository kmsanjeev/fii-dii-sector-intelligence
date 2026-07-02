# ML / AI / Chatbot Architecture
# Capital Flow Intelligence Platform

**Status:** Approved — FULLY IMPLEMENTED  
**Date:** 2026-06-29 | **Last updated:** 2026-07-02  
**ADR:** ADR-021 (ML Intelligence Layer), ADR-022 (RAG Knowledge Base), ADR-023 (Chatbot)

---

## Implementation Status (2026-07-02)

| Layer | Status | Notes |
|-------|--------|-------|
| ML Intelligence (Phase 12) | COMPLETE | XGBoost+LightGBM, 24 features, 4 outputs, 2441 symbols |
| RAG Knowledge Base (Phase 13) | COMPLETE | FAISS+BM25, 6 domain indexes, hybrid RRF retrieval |
| Chatbot Engine (Phase 14) | COMPLETE | Groq llama-3.3-70b-versatile (free tier), 11 tools, /api/chat |
| Chat UI (Phase D) | COMPLETE | ChatPage.tsx — 355 lines, session-aware, 6 suggested prompts |

## LLM Backend Change (2026-07-02)

**Original design:** Anthropic claude-sonnet-4-6 (paid API)  
**Current implementation:** Groq `llama-3.3-70b-versatile` (free tier, 100k tokens/day)  
**Reason:** Development cost elimination; Anthropic API retained for Phase 16 management sentiment only.

Tool calling format conversion at module load:
```python
# Anthropic format (tool_registry.py) -> Groq/OpenAI format (chat_engine.py)
GROQ_TOOLS = [{"type":"function","function":{"name":t["name"],"description":t["description"],
               "parameters":t.get("input_schema",{})}} for t in TOOLS]
```

Known Groq/Llama tool calling quirks and mitigations:
- Llama 3.3 occasionally generates XML-style function calls → `parallel_tool_calls=False` prevents this
- `tool_use_failed` 400 error → caught; final answer generated from clean prompt with tool results only
- 429 rate limit (100k tokens/day free tier) → caught; user-readable message returned
- `MAX_TOOL_ROUNDS=3` (was 5) to conserve token budget

---

---

## 1. Overview

Three new layers are added to the platform intelligence stack:

```
RAW DATA (NSE bhavcopy, FII/DII flows, fundamentals)
    ↓
INTELLIGENCE ENGINES  (existing phases 1–8)
    ↓
ML INTELLIGENCE LAYER  ← NEW: prediction + scoring models
    ↓
AI KNOWLEDGE BASE      ← NEW: RAG over all intelligence outputs
    ↓
AI AGENT LAYER         ← ENHANCED: Claude API + tool use
    ↓
CHATBOT INTERFACE      ← NEW: conversational access layer
    ↓
REACT GUI / API
```

---

## 2. Module 14 — ML Intelligence Layer

### Purpose
Replace heuristic scoring with trained ML models. Every engine currently producing a score (accumulation, sector, bull run) gets an ML counterpart that learns from historical validated outcomes.

### Models & Engines

#### 2.1 Accumulation Detection Model
**File:** `engines/ml/accumulation_model.py`  
**Algorithm:** XGBoost classifier + LightGBM ensemble  
**Predicts:** Probability stock is in active accumulation over next 20 sessions  

**Features:**
```python
ACCUMULATION_FEATURES = [
    # Price-volume
    "volume_ratio_20d",        # today's vol / 20d avg vol
    "delivery_pct",            # delivery % (high = conviction)
    "delivery_pct_ma10",       # 10-day avg delivery
    "close_vs_vwap",           # close relative to VWAP
    "range_pct",               # (High - Low) / Close — contraction = accumulation

    # Institutional flows
    "fii_net_5d",              # FII net ₹Cr last 5 sessions
    "dii_net_5d",              # DII net ₹Cr last 5 sessions
    "fii_buy_ratio_5d",        # FII BUY / (BUY+SELL)
    "pro_net_5d",              # PRO (smart money) net

    # Price action
    "rsi_14",                  # momentum
    "close_vs_52w_high_pct",   # position in 52-week range
    "ema20_slope",             # trend direction
    "higher_lows_5d",          # boolean: 5 consecutive higher lows

    # Relative strength
    "rs_vs_nifty50_20d",       # stock return vs NIFTY 50
    "rs_vs_sector_20d",        # stock return vs sector

    # OI (post-2016)
    "oi_change_pct",           # F&O OI change
    "pcr",                     # Put-Call Ratio
]

TARGET = "price_up_10pct_in_20d"  # binary: 1 if price rises ≥10% within 20 sessions
```

**Training:**
- Universe: All NSE EQ stocks 2016–2023 (OI available)
- Train: 2016–2021 | Validate: 2022 | Test: 2023
- Class imbalance: SMOTE oversampling (accumulation events ~15%)
- Output: `accumulation_probability` ∈ [0, 1]
- Threshold ≥ 0.65 → "Accumulating" label

---

#### 2.2 Sector Rotation Prediction Model
**File:** `engines/ml/sector_rotation_model.py`  
**Algorithm:** LightGBM multi-class  
**Predicts:** Which of 29 sectors leads the market in next 20 trading sessions  

**Features per sector:**
```python
SECTOR_ROTATION_FEATURES = [
    "fii_net_cr_10d",           # FII ₹Cr into sector
    "dii_net_cr_10d",
    "rs_vs_nifty_20d",          # relative strength
    "sector_breadth_pct",       # % of sector stocks advancing
    "sector_volume_ratio",      # sector volume / 30d avg
    "momentum_score_20d",
    "leadership_count",         # # of stocks making 52w highs
    "sector_delivery_pct",      # avg delivery % across sector
    "fii_buy_ratio_10d",
    "macro_correlation",        # sector sensitivity to USD/bond yields/crude
]
```

---

#### 2.3 Bull Run Probability Model
**File:** `engines/ml/bull_run_model.py`  
**Algorithm:** Ensemble (XGBoost + LightGBM + Logistic Regression) with soft voting  
**Predicts:** Probability a stock enters a sustained bull run (≥30% in ≤60 sessions)

**Multi-source features:**
```python
BULL_RUN_FEATURES = [
    # Technical
    "price_vs_200ema",         # above 200 EMA
    "ema_stack",               # 20 > 50 > 200 EMA
    "atr_contraction",         # ATR shrinking (coiling)
    "volume_dry_up",           # volume below avg (base formation)

    # Accumulation signals
    "accumulation_prob",       # output from Model 2.1
    "consecutive_accumulation_weeks",

    # Institutional
    "fii_net_quarter",         # FII net last quarter
    "promoter_holding_change", # QoQ promoter holding delta
    "dii_entry_detected",      # DII first appeared in shareholding

    # Fundamental
    "revenue_growth_yoy",
    "pat_growth_yoy",
    "roe",
    "debt_to_equity",
    "sector_tailwind",         # sector rotation model output

    # Index
    "in_nifty500",             # index membership
    "index_rebalance_expected",
]
```

---

#### 2.4 Anomaly Detection Model
**File:** `engines/ml/anomaly_detector.py`  
**Algorithm:** Isolation Forest + Statistical Z-Score  
**Purpose:** Flag unusual institutional flow events for review  

**Detects:**
- Sudden FII inflow spike (> 3σ from 90-day mean)
- Unusual PRO activity (smart money divergence)
- Volume anomaly on a quiet sector (pre-announcement trading)
- Delivery % spike without price movement
- OI buildup without FII support

---

#### 2.5 Company Classification Model
**File:** `engines/ml/classification_model.py`  
**Algorithm:** NLP (sentence-transformers) + cosine similarity to sector taxonomy  
**Purpose:** Auto-classify companies into 29 sectors and 18 themes using business description  

**Approach:**
```python
# 1. Embed company's business description using sentence-transformers
company_embedding = embedder.encode(company_description)

# 2. Embed each sector/theme description
sector_embeddings = {s: embedder.encode(SECTOR_DESCRIPTIONS[s]) for s in SECTORS}

# 3. Cosine similarity → top 3 sector candidates
scores = cosine_similarity(company_embedding, sector_embeddings)

# 4. Confidence = top-1 score; below 0.70 → manual review queue
# 5. Manual override CSV always applied last (G-C-02)
```

This directly fixes the classification coverage gap (37% → 95%+) and the ADANIPORTS → AEROSPACE bug.

---

#### 2.6 Feature Engineering Pipeline
**File:** `engines/ml/feature_engineering.py`  
**Purpose:** Shared feature computation for all ML models  

```python
class FeatureEngineer:
    def compute_all(self, symbol: str, as_of_date: str) -> pd.Series:
        price_features = self._price_features(symbol, as_of_date)
        flow_features = self._flow_features(symbol, as_of_date)
        fundamental_features = self._fundamental_features(symbol, as_of_date)
        sector_features = self._sector_features(symbol, as_of_date)
        return pd.concat([price_features, flow_features,
                          fundamental_features, sector_features])
```

**Storage:** `data/intelligence/ml_features/` (date-partitioned Parquet)

---

### Model Registry & Versioning
**File:** `engines/ml/model_registry.py`  
**Storage:** `data/intelligence/ml_models/`  

```
data/intelligence/ml_models/
├── accumulation/
│   ├── v1_2024_xgboost.pkl
│   └── v1_2024_lightgbm.pkl
├── sector_rotation/
│   └── v1_2024_lgbm.pkl
├── bull_run/
│   └── v1_2024_ensemble.pkl
└── classification/
    └── v1_2024_sentence_transformer.pkl
```

---

## 3. Module 15 — AI Knowledge Base (RAG)

### Purpose
Index all platform intelligence outputs into a searchable vector store so AI agents can retrieve verified, platform-specific context before generating answers — not hallucinate from training data.

### Architecture

```
Intelligence Outputs (CSV/JSON)
    ↓
Chunker + Embedder (sentence-transformers)
    ↓
FAISS Vector Index
    ↓
Retriever (Hybrid: Dense + BM25 keyword)
    ↓
Context Assembly
    ↓
Claude API Prompt
```

### Directory: `engines/ai/knowledge/`

```
engines/ai/knowledge/
├── indexer.py           ← builds/updates FAISS index
├── embedder.py          ← sentence-transformers wrapper
├── retriever.py         ← hybrid search (dense + keyword)
├── context_builder.py   ← assembles prompt context from retrieved chunks
├── chunker.py           ← splits intelligence outputs into retrievable chunks
└── schemas.py           ← document schemas for each intelligence type
```

### Indexed Documents

| Source | Update Frequency | Chunk Strategy |
|--------|-----------------|----------------|
| Daily institutional flow summary | Daily | One chunk per day per participant |
| Sector heatmap + scores | Daily | One chunk per sector |
| Theme scores | Daily | One chunk per theme |
| Stock accumulation scores | Daily | One chunk per stock |
| Quarterly financial results | Quarterly | One chunk per company per quarter |
| Corporate actions log | Event-driven | One chunk per event |
| Research reports | As generated | Split by paragraph |
| Market regime history | Daily | Rolling 90-day window |

### FAISS Index Structure
```python
# Separate indexes by domain
INDEXES = {
    "market":        FAISSIndex("data/intelligence/rag/market.faiss"),
    "sectors":       FAISSIndex("data/intelligence/rag/sectors.faiss"),
    "themes":        FAISSIndex("data/intelligence/rag/themes.faiss"),
    "stocks":        FAISSIndex("data/intelligence/rag/stocks.faiss"),
    "fundamentals":  FAISSIndex("data/intelligence/rag/fundamentals.faiss"),
    "research":      FAISSIndex("data/intelligence/rag/research.faiss"),
}
```

### Retrieval Strategy
```python
def retrieve(query: str, domain: str, top_k: int = 8) -> list[Chunk]:
    # 1. Dense retrieval: semantic similarity via FAISS
    dense_hits = indexes[domain].search(embed(query), k=top_k * 2)
    # 2. Keyword retrieval: BM25 over same corpus
    keyword_hits = bm25[domain].search(query, k=top_k)
    # 3. Reciprocal Rank Fusion: merge and re-rank
    return rrf_merge(dense_hits, keyword_hits, k=top_k)
```

---

## 4. Module 16 — Chatbot / Conversational AI

### Architecture

```
User Input (text)
    ↓
Intent Router            ← classifies which agent + domain
    ↓
Tool Resolver            ← decides if live data lookup needed
    ↓
Knowledge Retriever      ← pulls RAG context (Module 15)
    ↓
Claude API (Sonnet 4.6)  ← generates response with context + tools
    ↓
Response Formatter       ← adds charts, tables, links inline
    ↓
WebSocket / REST
    ↓
React Chat UI
```

### Directory: `engines/ai/chatbot/`

```
engines/ai/chatbot/
├── router.py                ← intent → agent mapping
├── memory.py                ← session + long-term memory
├── tools.py                 ← live data tool registry
├── formatter.py             ← response + inline visual data
├── agents/
│   ├── market_agent.py      ← Agent 01: market analysis
│   ├── sector_agent.py      ← Agent 02: sector rotation
│   ├── theme_agent.py       ← Agent 03: theme rotation
│   ├── stock_agent.py       ← Agent 04: stock analysis
│   ├── portfolio_agent.py   ← Agent 05: portfolio review
│   ├── research_agent.py    ← Agent 06: research Q&A
│   └── dev_cto_agent.py     ← Agent 07: development guidance
└── session.py               ← WebSocket session management
```

### LLM: Claude API
**Model:** `claude-sonnet-4-6` (default) / `claude-opus-4-8` (deep analysis)  
**API key:** `os.getenv("ANTHROPIC_API_KEY")` — never hardcoded  

```python
# engines/ai/chatbot/agents/base_agent.py
import anthropic

class BaseAgent:
    def __init__(self, agent_name: str, system_prompt: str):
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        self.model = "claude-sonnet-4-6"
        self.system_prompt = system_prompt
        self.max_tokens = 2048

    def respond(self, user_message: str, context: str, tools: list) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=f"{self.system_prompt}\n\nPLATFORM CONTEXT:\n{context}",
            messages=[{"role": "user", "content": user_message}],
            tools=tools,
        )
        return response.content[0].text
```

### Intent Router

```python
# router.py
INTENT_MAP = {
    # Market
    r"market|regime|risk.on|risk.off|breadth|index": "market_agent",
    # Sector
    r"sector|rotation|BANKING|IT|FMCG|which sector": "sector_agent",
    # Theme
    r"theme|EV|PSU|infra|emerging|narrative": "theme_agent",
    # Stock
    r"stock|[A-Z]{3,10}|accumulation|distribution|why.*moving": "stock_agent",
    # Portfolio
    r"portfolio|my holdings|exposure|risk|allocation": "portfolio_agent",
    # Research
    r"research|investment thesis|why buy|why sell|compare": "research_agent",
}

def route(user_input: str) -> str:
    for pattern, agent in INTENT_MAP.items():
        if re.search(pattern, user_input, re.IGNORECASE):
            return agent
    return "market_agent"  # default
```

### Tool Registry (live data access)

```python
# tools.py — Claude API tool use spec
TOOLS = [
    {
        "name": "get_sector_flows",
        "description": "Get latest FII/DII/PRO/CLIENT flow for a specific sector",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector": {"type": "string"},
                "days": {"type": "integer", "default": 30}
            }
        }
    },
    {
        "name": "get_stock_score",
        "description": "Get current accumulation and bull run probability scores for a stock",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}}
        }
    },
    {
        "name": "get_top_sectors",
        "description": "Get top N sectors by current capital flow score",
        "input_schema": {
            "type": "object",
            "properties": {"n": {"type": "integer", "default": 5}}
        }
    },
    {
        "name": "get_market_regime",
        "description": "Get current market regime and last 5 regime changes",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "search_research",
        "description": "Search the research knowledge base for investment context",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}}
        }
    },
]
```

### Conversation Memory

```python
# memory.py
class ConversationMemory:
    def __init__(self, session_id: str, max_turns: int = 20):
        self.session_id = session_id
        self.short_term = []         # last N turns (in-session)
        self.long_term_key = f"user_prefs_{session_id}"  # persisted to JSON

    def add_turn(self, role: str, content: str):
        self.short_term.append({"role": role, "content": content})
        if len(self.short_term) > self.max_turns * 2:
            # Summarize oldest half before dropping
            self.short_term = self._summarize_and_trim()

    def get_history(self) -> list[dict]:
        return self.short_term
```

### WebSocket API Endpoint

```python
# api/routers/chatbot.py
from fastapi import WebSocket

@router.websocket("/ws/chat/{session_id}")
async def chat_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    memory = ConversationMemory(session_id)
    while True:
        user_msg = await websocket.receive_text()
        agent_name = router.route(user_msg)
        agent = agent_registry[agent_name]
        context = retriever.retrieve(user_msg, domain=agent.domain)
        response = agent.respond(user_msg, context, tools=TOOLS)
        memory.add_turn("user", user_msg)
        memory.add_turn("assistant", response)
        await websocket.send_json({
            "type": "message",
            "agent": agent_name,
            "content": response,
            "sources": context.sources,  # which intelligence outputs were used
        })
```

### Example Chatbot Interactions

```
User:  "Which sectors are seeing FII accumulation this week?"
AI:    "Based on the last 5 sessions (as of 2026-06-27), FII inflows are concentrated in:
        1. BANKING (+₹3,240 Cr) — largest FII buy since March 2026
        2. IT (+₹1,890 Cr) — reversal from 2-week selling
        3. PHARMA (+₹920 Cr) — steady accumulation for 3rd week
        Capital is rotating away from METALS (-₹1,200 Cr) and REALTY (-₹640 Cr)."

User:  "Why is RELIANCE moving up?"
AI:    "RELIANCE shows:
        • Accumulation probability: 78% (XGBoost model, last updated 2026-06-27)
        • FII net buy: +₹430 Cr last 10 sessions
        • Delivery %: 68% (above sector avg 52%)
        • Bull run probability: 71%
        Possible catalyst: Jio subscriber additions Q1FY26 beat expectations
        (from corporate announcements, 2026-06-20). No Q2 results yet."

User:  "Review my portfolio: RELIANCE×100, HDFCBANK×200, TCS×50"
AI:    "Your portfolio analysis:
        Sector exposure: Financial Services 42%, IT 25%, Oil & Gas 33%
        Risk alert: Heavy financial sector concentration (42% vs NIFTY 18%)
        Strongest holding: TCS — accumulation prob 82%, sector momentum positive
        Watch: HDFCBANK — DII selling last 5 sessions despite FII buying"
```

---

## 5. Integration with Existing Platform

### Updated Layer Stack

```
Layer 1  Foundation (bhavcopy, equity master)            ✅ Complete
Layer 2  Classification (sector, theme mapping)          🟡 70%
Layer 3  Price Intelligence (OHLCV, delivery)            🟡 In progress
Layer 4  Institutional Intelligence (FII/DII/PRO/CLIENT) ✅ Complete
Layer 5  Sector + Theme Intelligence                     🟡 45%
Layer 6  Fundamental Intelligence                        🔴 0% (Phase 4A)
Layer 7  Corporate Intelligence                          ⚪ Blocked
Layer 8  ML Intelligence Layer                           🔴 0% (NEW - needs L6)
Layer 9  AI Knowledge Base (RAG)                         🔴 0% (NEW - needs L8)
Layer 10 Chatbot / Conversational AI                     🔴 0% (NEW - needs L9)
```

### Data Flow: New ML/AI Paths

```
engines/fundamentals/ → company_fundamentals_master.csv
                     → engines/ml/feature_engineering.py
                     → engines/ml/accumulation_model.py  → data/intelligence/scores/
                     → engines/ml/bull_run_model.py      → data/intelligence/scores/

engines/intelligence/ → sector scores, theme scores
                     → engines/ai/knowledge/indexer.py   → data/intelligence/rag/
                     → engines/ai/chatbot/agents/        → WebSocket → React GUI
```

---

## 6. Required Dependencies (add to requirements.txt)

```
# AI / LLM
anthropic>=0.25.0          # Claude API

# ML
scikit-learn>=1.5.0        # already present
xgboost>=2.1.0             # already present
lightgbm>=4.5.0            # already present
imbalanced-learn>=0.12.0   # SMOTE for class imbalance
optuna>=3.6.0              # hyperparameter tuning

# Embeddings + RAG
sentence-transformers>=3.0.0  # already present
faiss-cpu>=1.8.0              # already present
rank-bm25>=0.2.2              # BM25 keyword retrieval

# API
websockets>=12.0           # already via FastAPI
```

---

## 7. New Data Paths

```
data/intelligence/
├── scores/
│   ├── accumulation/          ← ML accumulation scores (daily, per symbol)
│   ├── bull_run/              ← Bull run probability (daily, per symbol)
│   └── sector_rotation/       ← Sector rotation predictions
├── ml_features/               ← Pre-computed feature sets (Parquet, date-partitioned)
├── ml_models/                 ← Trained model artifacts (.pkl)
│   ├── accumulation/
│   ├── sector_rotation/
│   ├── bull_run/
│   └── classification/
└── rag/                       ← FAISS indexes + metadata
    ├── market.faiss
    ├── sectors.faiss
    ├── themes.faiss
    ├── stocks.faiss
    ├── fundamentals.faiss
    └── research.faiss
```

---

## 8. Build Phases for ML/AI/Chatbot

| Phase | Deliverable | Depends On |
|-------|------------|------------|
| ML-1 | Feature engineering pipeline | Phase 4A (fundamentals) |
| ML-2 | Accumulation detection model | ML-1 |
| ML-3 | Company classification model (NLP) | ML-1 |
| ML-4 | Sector rotation prediction model | ML-1, Phase 6 |
| ML-5 | Bull run probability model (ensemble) | ML-2, ML-4 |
| ML-6 | Anomaly detection model | ML-1 |
| RAG-1 | FAISS indexer + embedder | Phase 3 outputs |
| RAG-2 | Hybrid retriever (dense + BM25) | RAG-1 |
| RAG-3 | Context builder + prompt assembly | RAG-2 |
| CB-1 | Intent router + base agent | RAG-3 |
| CB-2 | All 7 specialized agents | CB-1 |
| CB-3 | Tool registry (live data access) | CB-2 + API layer |
| CB-4 | Conversation memory | CB-2 |
| CB-5 | WebSocket session management | CB-3, CB-4 |
| CB-6 | React chat UI integration | CB-5, GUI-8 |

**Earliest ML-1 start:** After Phase 4A (Company Fundamentals Master Engine)  
**Earliest RAG-1 start:** After Phase 3B outputs exist (✅ now possible)  
**Earliest CB-1 start:** After RAG-3 + any 3 intelligence engines producing outputs
