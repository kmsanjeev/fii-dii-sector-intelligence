# VOICE PLATFORM — "VEDA / ADYA"
## Capital Flow Intelligence Platform | Module Design Document
### Phase V (Voice) — Gate-1 Architecture Freeze | 2026-07-10 | Status: PROPOSED

---

# 1. OBJECTIVE

Give the platform a voice assistant persona ("Veda" or "Adya") that:

1. **Wakes on her name** — saying "Veda" or "Adya" activates voice mode
2. **Asks what you want in your preferred language** (Hindi / English / other Indian languages)
3. **Speaks with a sweet, polished female voice** — crystal-clear pronunciation,
   professional, precise, confident tone, minimal lag
4. **Answers in BOTH text and voice** — every voice conversation appears as a
   normal chat (new chat session) with the spoken reply alongside
5. **Records every conversation** for analytics — what is most/least requested,
   feeding future ML personalisation
6. **Costs nothing** — free / open-source components only

---

# 2. TECHNOLOGY SELECTION (RESEARCHED 2026-07-10)

## 2.1 The Voice (Text-to-Speech) — THE CRITICAL REQUIREMENT

**SELECTED: `edge-tts` (Microsoft Edge neural voices via Python, free, no API key)**

| Option | Quality | Indian languages | Cost | Lag | Verdict |
|---|---|---|---|---|---|
| **edge-tts** | Neural, natural, "sweet" female voices | Hindi, Indian English, Tamil, Telugu, Bengali, Marathi, Gujarati + more | FREE, no key | ~0.5-1s to first audio (streams) | **CHOSEN** |
| Browser speechSynthesis | Varies by OS; often robotic | Poor Hindi on most systems | Free | Instant | Rejected: fails the "sweet/polished" bar |
| Piper (local, open source) | Good English; weak Indic | Limited | Free | Fast | Rejected: Indic quality |
| Coqui XTTS | Good but heavy | OK | Free | Needs GPU, slow on this machine | Rejected |
| Sarvam AI Bulbul | Excellent Indic | Best-in-class Indic | Free credits only, then paid | Fast | Backup option if edge-tts ever blocks |

**Voice casting (the persona):**

| Language | Voice ID | Character |
|---|---|---|
| Hindi | `hi-IN-SwaraNeural` | Warm, sweet, clear — the default Hindi Veda |
| Indian English | `en-IN-NeerjaNeural` | Polished, professional, confident — default English Veda |
| Indian English alt | `en-IN-AaravNeural`/new 2026 expressive voices | Microsoft GA'd 11 new Indian voices — we pick the best in testing |
| Tamil | `ta-IN-PallaviNeural` | Optional |
| Telugu | `te-IN-ShrutiNeural` | Optional |
| Bengali | `bn-IN-TanishaaNeural` | Optional |

Tone control: edge-tts supports `rate` and `pitch` adjustment per request — we tune
slightly slower rate (-5%) for precision and neutral pitch for confidence, per voice.

**Honest dependency note:** edge-tts calls Microsoft's Edge TTS service (internet
required). It is unofficial-but-tolerated, actively maintained (v7+ on PyPI, 2026),
and used by thousands of projects. Mitigation if it ever breaks: swap the TTS
provider behind our own `/api/voice/tts` endpoint (one file), fall back to browser
speechSynthesis meanwhile. The abstraction is part of this design.

## 2.2 Hearing (Speech-to-Text)

**SELECTED: Web Speech API (browser) primary + Groq Whisper (server) fallback**

| Option | Accuracy | Hindi/Hinglish | Cost | Lag | Verdict |
|---|---|---|---|---|---|
| **Web Speech API** (Chrome/Edge) | Very good | Good (hi-IN mode) | Free | Real-time streaming | **PRIMARY** — zero install, streams as you speak |
| **Groq Whisper large-v3** | Excellent | Excellent | Free tier (we already have the key) | ~1s per utterance | **FALLBACK** — for Hindi-heavy speech or non-Chrome browsers |
| faster-whisper local | Excellent | Excellent | Free | 3-8s per utterance on this CPU | Rejected as primary: lag violates requirement |
| Vosk local | OK | Mediocre | Free | Fast | Rejected: accuracy |

## 2.3 Wake Word ("Veda" / "Adya")

**Research finding that changed the design:** Picovoice **Porcupine** — the standard
recommendation for custom wake words — **shut its free tier on June 30, 2026**.
Existing free AccessKeys are disabled. It is no longer an option.

**SELECTED: Web Speech API continuous listening + transcript matching**

- The browser keeps a lightweight continuous recognition session open on the Chat
  page (with the auto-restart pattern for Chrome's session timeouts)
- Every interim transcript is checked for "veda" / "adya" / common
  mis-hearings ("vedha", "aadya", "adia", "wada") — fuzzy match list is configurable
- On match: chime + spoken greeting ("Ji, boliye — main sun rahi hoon" / "Yes,
  I'm listening — how can I help?"), then command capture begins
- **Always-available fallback: a mic button (push-to-talk)** — one click starts
  the same flow without the wake word. This is also the path for browsers where
  continuous listening is unreliable (Firefox/iOS)

Honest accuracy note: name-based matching via general STT is ~90-95% reliable in
a quiet room, worse with background noise — not the 97%+ of a dedicated (paid)
wake-word engine. The mic button guarantees the feature always works. If wake-word
quality disappoints, Phase V3 evaluates openWakeWord (open source) with a custom
trained "Veda" model — more setup, fully local, free.

## 2.4 Conversation Recording & Analytics

**SELECTED: append-only parquet log + analytics engine (all local, private)**

- Every turn (voice AND text) appends to `data/chat/conversation_log.parquet`:
  `ts, session_id, mode (voice|text), language, wake_word_used, user_message,
  detected_intent, tools_called, symbols_mentioned, provider_used, reply_chars,
  latency_ms, tts_voice`
- New engine `chat_analytics_engine.py` (daily pipeline stage) aggregates:
  - most/least requested intents (regime, stock scores, kundli, sector...)
  - most-asked symbols/sectors, language split, voice-vs-text share
  - request heatmap by hour/day
  - output: `data/intelligence/chat_analytics.csv` — the demand dataset the
    future ML personalisation layer will train on
- Privacy: everything stays on this machine; raw audio is NOT stored (only
  transcripts), and the log is excluded from git (G-SYS-02)

---

# 3. ARCHITECTURE

```
BROWSER (ChatPage + global VoiceProvider)
 |
 |  [always-on, lightweight]
 |  Web Speech API continuous recognition (lang follows preference)
 |     interim transcripts --> wake-word matcher ("veda"/"adya" + variants)
 |        on match: chime + spoken greeting (pre-cached TTS audio)
 |        --> COMMAND MODE: capture one utterance (final transcript)
 |  [or] Mic button --> COMMAND MODE directly (push-to-talk)
 |
 |  final transcript ------------------------------+
 v                                                 v
POST /api/chat  (existing engine: intent, RAG,   NEW CHAT SESSION
 tools, 7-provider fallback)                     created per voice
 |                                               conversation; both
 |  reply text                                   sides rendered in
 v                                               the normal chat UI
POST /api/voice/tts  {text, lang, voice}
 |  edge-tts --> MP3 stream (chunked)
 v
<audio> element plays as chunks arrive  +  text bubble renders
 |
 v
POST /api/voice/log  (turn metadata) --> data/chat/conversation_log.parquet
                                          |
                          daily pipeline: chat_analytics_engine.py
                                          --> chat_analytics.csv (ML demand data)
```

**New backend router `backend/routers/voice.py`:**

| Endpoint | Purpose |
|---|---|
| `POST /api/voice/tts` | text + language + voice -> streamed MP3 (edge-tts); LRU cache for repeated phrases (greetings answer instantly) |
| `POST /api/voice/stt` | audio blob -> Groq Whisper transcript (fallback path only) |
| `POST /api/voice/log` | append turn metadata to conversation log |
| `GET  /api/voice/voices` | available voices per language for the settings picker |
| `GET  /api/voice/analytics` | aggregated demand stats for a future dashboard card |

**Frontend additions:**

- `VoiceProvider` (context around the app): wake-word listener lifecycle,
  language preference (localStorage `cfip-voice`), voice on/off master switch
- ChatPage: mic button, "listening..." indicator with waveform, speaking
  indicator, auto-play of reply audio, language picker (Hindi / English /
  Hinglish auto-detect / others), voice picker with preview button
- Long replies: TTS speaks a spoken-summary (first ~600 chars or the reply's
  summary block) while full text renders — keeps voice snappy; "read full
  answer" button available

**Reply style for voice:** the chat system prompt gets a voice-mode addendum —
concise spoken-style sentences first, tables/details after (tables are never
read aloud; Veda says "I've put the full table in the chat").

---

# 4. LANGUAGE FLOW

1. User sets preferred language once (settings; default: English-India).
2. Wake greeting and all of Veda's speech use that language's cast voice.
3. STT listens in that language (`hi-IN` recognises Hinglish reasonably well).
4. The LLM is instructed to reply in the user's language. All current
   providers (Groq/Gemini/Mistral/GPT-4o-mini) handle Hindi and Hinglish.
5. Per-conversation override: "Veda, speak in Hindi" switches instantly
   (a lightweight intent the frontend also understands).

---

# 5. LATENCY BUDGET (HONEST NUMBERS)

| Step | Expected |
|---|---|
| Wake word detection | instant-to-1s (streaming interim results) |
| Greeting playback | instant (pre-cached audio) |
| Command STT | real-time (Web Speech streams while you talk) |
| LLM answer | 1-4s (existing chain; Groq fastest) |
| TTS first audio | 0.5-1.5s (edge-tts streams; short sentences start faster) |
| **Voice question -> voice answer starts** | **~2.5-6s typical** |

"Without lagging" is met for the speech itself (streaming, no stutter). The
think-time before an answer is LLM-bound and identical to today's chat; a
spoken "Ek moment..." filler on long tool calls keeps the interaction alive.

---

# 6. IMPLEMENTATION PLAN

### Phase V1 — Core Voice Loop (first build, ~1 session)
- `backend/routers/voice.py`: /tts (edge-tts streaming + cache), /log, /voices
- `edge-tts` package install; voice casting test — pick final Hindi + English voices
- ChatPage: mic button (push-to-talk), language/voice settings, reply audio
  auto-play, text+voice dual response, new-session-per-voice-conversation
- Conversation log parquet + logging of ALL chat turns (voice and text)
- **Result:** click mic, speak in Hindi or English, Veda answers in her voice
  and in the chat, everything recorded

### Phase V2 — Wake Word + Analytics (second build, ~1 session)
- Continuous listener + "Veda"/"Adya" matcher with fuzzy variants + auto-restart
- Spoken greeting flow, chime, listening indicator
- `chat_analytics_engine.py` + pipeline stage + `GET /api/voice/analytics`
- Voice-mode system-prompt addendum (spoken-style answers)
- **Result:** hands-free "Veda... what's the market regime?" end-to-end;
  demand analytics accumulating daily

### Phase V3 — Polish & Resilience (optional, later)
- openWakeWord evaluation for offline, higher-accuracy wake word
- Spoken fillers during long tool calls; barge-in (interrupt Veda by speaking)
- Analytics dashboard card (top requests, language split, voice usage)
- Browser speechSynthesis fallback wiring for edge-tts outages

---

# 7. EXPECTED RESULTS

- Say **"Veda"** (or **"Adya"** — both active) on the Chat page -> chime ->
  *"Ji, boliye"* / *"Yes, I'm listening"* in a sweet, clear female neural voice
- Ask anything the chatbot can do today — stock conviction, regime, sectors,
  kundli — in **Hindi, English or Hinglish**
- Reply arrives as **text in a new chat + spoken audio simultaneously**,
  professional and precise, ~2.5-6s after you stop speaking
- Every conversation logged; after a few weeks `chat_analytics.csv` shows
  exactly what you ask most/least — the training set for ML personalisation
- **Total cost: Rs 0.** No new API keys required (Groq Whisper uses the
  existing key; edge-tts needs none)

# 8. RISKS & LIMITS (STATED PLAINLY)

1. edge-tts is an unofficial free channel to Microsoft's service — it has been
   stable for years but could throttle heavy use; our /tts abstraction + browser
   fallback caps the damage
2. Wake word via STT matching is ~90-95% in quiet rooms, not 97%+; the mic
   button always works; openWakeWord is the V3 upgrade path
3. Web Speech API needs Chrome or Edge (your environment) and internet;
   Firefox/iOS get push-to-talk + server STT only
4. Voice quality of Hinglish (mixed) speech recognition is good, not perfect —
   the chat text box always remains as the precise fallback

---

*Gate-1 document per ADR-012 / phased development protocol. Code begins after approval.*
