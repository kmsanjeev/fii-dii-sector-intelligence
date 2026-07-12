# Module Log — Phase V-DATA-3: "Recently Asked" Panel (Chat Personalization, Scoped)

**Date:** 2026-07-13
**Status:** COMPLETE
**Version:** 4.46.0

## User Request

Follow-up to the original data-access audit's flagged concern: "further
look into the concern raised in the Chat to ML part on chat history
nudging alert/screener ordering toward symbols which needs to be scoped
properly."

## Scoping (AskUserQuestion, both recommended options confirmed)

1. Surface: a dedicated "Recently Asked" panel, purely additive -- never
   touches any existing ranked list (not "blend into ranking/scoring",
   explicitly rejected as the same category of mistake as the
   STRONG_CANDIDATE bug just fixed).
2. Timing: build the plumbing now with an honest empty-state, rather than
   defer -- it activates naturally as usage grows, costs nothing to ship
   early.

## Bug found while designing: symbol extraction was Latin-only

Before building, read the actual conversation_log.csv (32 turns) to
ground the design in real data. Found the user has been talking to Veda
almost entirely in Hindi/Devanagari voice, asking about "रिलायंस"
(Reliance) repeatedly -- but the existing symbol-extraction regex in
chat_analytics_engine.py (`[A-Z][A-Z0-9&-]{2,}`) is Latin-script only.
Zero SYMBOL rows existed in chat_analytics.csv despite real, repeated
stock interest in the logs. Building the panel on the broken pipeline
would have shipped a feature that appeared to not work.

## Fix: capture from tool calls, not text

Redesigned around a more robust source of truth: track which symbols the
LLM's TOOL CALLS actually used, since a tool call always resolves to the
Latin NSE symbol regardless of input language.

- chat_engine.py: `self.last_symbols`, populated from any tool call whose
  args include `symbol` (automatic for all 10+ symbol-taking tools).
- chat.py: `ChatResponse.symbols_discussed`.
- voice.py: `LogRequest.symbols`, persisted comma-joined; one-time schema
  migration handles the pre-existing 10-column log file transparently
  (old rows get an empty symbols value, no data loss, no manual step).
- ChatPage.tsx: threads the response's symbols into the `/api/voice/log`
  call.
- chat_analytics_engine.py: prefers the new column, falls back to the old
  regex for historical rows / turns where no symbol tool was called.

## Separate finding, explicitly NOT fixed here

While testing, found the LLM sometimes resolves a Hindi company name to
the WRONG stock ("रिलायंस" answered as CORONA) -- a real chatbot accuracy
issue, likely worse today with the strong providers rate-limited. This is
NOT a capture-pipeline bug (it correctly recorded whatever the tool
actually used) -- flagged as a separate, out-of-scope finding. Would need
a curated Hindi/Indic company-name-to-symbol resolution layer, a
meaningfully different and larger piece of work.

## Built

Dashboard "Recently Asked" card (frontend/src/pages/Dashboard.tsx):
symbol chips with mention count + relative time, linking to stock pages;
two distinct empty states depending on whether any turns vs. any symbol
tool calls have been logged. Reuses the existing /api/voice/analytics
endpoint (its top_symbols field already existed, just fed by broken data)
-- no new backend endpoint needed.

## Verification

- Direct /api/voice/log test: confirmed migration (old rows blank,
  new row populated), confirmed CSV write correctness.
- Direct /api/chat test (English, unambiguous symbol): confirmed
  symbols_discussed captured correctly.
- Re-ran chat_analytics_engine.py: confirmed the symbol flows through
  end-to-end into chat_analytics.csv.
- Dashboard screenshot: confirmed the live chip renders correctly on the
  actual running page, not just in isolation.
- Suite 267/267 green; tsc + vite build clean.
