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

---

## Session 2026-07-09 — Phase KU-2: Geocoding + Life Guide + Provider Expansion

**Geocoding (fixes Bokaro-not-found):**
- tools/geocoder.py: built-in CITY_COORDS -> learned cache
  (data/reference/city_coords_cache.csv) -> geopy/Nominatim (global, keyless,
  1.1s throttle, India-biased retry, ASCII-sanitized names). Failure degrades
  to manual lat/long path. geopy installed in py -3.11.
- _get_city_coords now calls resolve_city() with builtin dict as tier 1.

**Life Guide (tools/kundli_life_guide.py, appended to formatted_report):**
- Mahadasha favorability scoring: functional lordship for lagna (trikona
  +1.5/lord, trik -1.5, kendra +0.5, 3/11 -0.5) + dignity (+2 exalted /
  -2 debilitated) + occupied house (trik -1) + natural character.
  Labels EXCELLENT >=2.5, GOOD >=1, MIXED >=-1, CHALLENGING below.
- Sade Sati: transit Saturn (computed live via _compute_positions(now) +
  Lahiri ayanamsha) vs natal Moon sign; 12th/1st/2nd = phases 1/2/3;
  4th/8th = dhaiyya. Plain-English notes + do lists.
- Layman summary: outer/inner self, current chapter rating, best window
  (softened wording when best is only MIXED), careful window, top 3 remedies.
- All computed, no LLM, ASCII-only.

**Chatbot provider chain:**
- BUG FIX: Cerebras chat model llama-3.3-70b 404s on free tier (logs proved
  last-resort provider permanently dead) -> gemma-4-31b (confirmed working).
- NEW key-gated providers in chat_engine + llm_client: Mistral
  (mistral-small-latest, 1B tok/mo), GitHub Models (gpt-4o-mini, GitHub PAT),
  SambaNova (Meta-Llama-3.3-70B). Env: MISTRAL_API_KEY, GITHUB_MODELS_TOKEN,
  SAMBANOVA_API_KEY.
- LIVE VERIFIED: forced Groq cooldown -> Gemini rate-limited (real) ->
  OpenRouter rate-limited (real) -> Cerebras answered. Log archaeology found
  two all-providers-exhausted events same day (22:39, 23:50) -- user report
  confirmed; expansion directly addresses it.

---

## Session 2026-07-10 — Phase KU-3: Kundli Depth Rework

User review of a real chart (1979 Nalanda, Libra lagna) found: repetitive
preset sentences (same lord-in-house text in 4 sections), internal
contradiction (Saturn dasha = karmic test vs Life Guide GOOD), truncated
house significations, shallow non-personalised depth.

**Root causes + fixes:**
1. FUNCTIONAL NATURE was missing: for Libra lagna Saturn is YOGAKARAKA
   (kendra+trikona lord). New _functional_nature() + _YOGAKARAKA_BY_LAGNA in
   kundli_calculator; _dasha_interpretation weighs functional role above sign
   dignity; career-timing + combined-dasha readings + Life Guide rating all
   share it -> no more self-contradiction.
2. REPETITION: _lord_sentence per-report dedupe (_EMITTED_LORDS): full text ->
   first-clause essence -> suppressed. Dignity prefixes rotate alternates.
3. TRUNCATION: house significations moved to full-width covers: line.
4. COMBUSTION detection (classical orbs) added to calculator; shows in table
   (C flag), watch-outs, Life Guide scoring, excluded from window advice.
5. HONEST VERDICTS: central _SECTION_META + _section_verdict in interpreter --
   every section ends with Clearly positive / Watch out for naming actual
   chart factors both ways.
6. TIMING WINDOWS: _favourable_windows -- real dasha date ranges for career/
   wealth/marriage from relevant lords+karakas (combust lords excluded).

Verified on both archetypes (yogakaraka chart + plain chart); suite 267/267.
GOTCHA: kundli_calculator imports kundli_interpreter at module load -- any
interpreter->calculator import MUST be lazy (inside function) to avoid a
circular import.

---

## Session 2026-07-11 — Phase V1: Veda Voice Assistant core loop (COMPLETE)

Per gate-1 doc docs/modules/VOICE_PLATFORM.md. Default language: HINDI (user).

**Backend (backend/routers/voice.py):**
- /api/voice/tts: edge-tts streaming; casting hi-IN-SwaraNeural (default),
  en-IN-NeerjaNeural, +ta/te/bn/mr/gu; rate -5%; _spoken_text sanitizer strips
  markdown + drops table lines + caps 900 chars on sentence boundary;
  sha1-keyed in-memory cache (64 entries) -- repeat phrase 3463ms -> 91ms
- /api/voice/log: thread-safe CSV append -> data/chat/conversation_log.csv
  (ts, session, mode, language, wake_word_used, user_message, intent,
  reply_chars, latency_ms, tts_voice). NOTE: doc said parquet; CSV append
  chosen for atomic line-appends without full-file rewrite.
- /voices + /analytics (quick aggregate; full engine = V2)

**Frontend (ChatPage):**
- MIC push-to-talk (Web Speech API; sttLang per language; live transcript
  into input box; red pulse animation)
- Language picker (localStorage cfip-voice-lang, default hi), VOICE ON/MUTED,
  speaking indicator with stop
- send() extended: mode + sidOverride; voice replies auto-speak; voice command
  during a text convo spawns a NEW chat (voiceChatsRef tracks voice-born chats)
- EVERY turn (voice + text) logged via /api/voice/log

**Verified:** both voices generate (first audio 0.8-1.2s); all 4 endpoints
live; sanitizer probes pass; tsc + build clean.
**V2 backlog:** wake word listener, spoken greeting, chat_analytics_engine
pipeline stage, voice-mode system-prompt addendum, provider/tool fields in log.
