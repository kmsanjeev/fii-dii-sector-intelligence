/**
 * Veda Store — Phase V-UI (global voice assistant)
 *
 * Single source of truth for Veda's chat/voice state, shared between the
 * always-mounted floating widget (VedaWidget, wake word works on every
 * page) and the full /chat page (session history, export, slash palette).
 * Both surfaces read/write the SAME state here -- a message sent from one
 * shows up in the other instantly, and only one wake-word listener ever
 * runs app-wide (owned by VedaWakeController, mounted once in AppShell).
 *
 * This is a faithful extraction of the voice engine that previously lived
 * entirely inside ChatPage.tsx (Phases V1-V3.3, multiple rounds of field
 * fixes for wake-word reliability, barge-in, and staged playback) --
 * behavior and timing constants are unchanged, only the ownership moved
 * from one component's local state to a shared store so it can be
 * global. Zustand's get()/set() pattern also removes the stale-closure
 * risk the original useCallback dependency arrays carried.
 */
import { create } from 'zustand'
import { sendChat, resetChatSession, type ChatResponseData } from '../api/client'

// ─── Types ────────────────────────────────────────────────────────────────────

export type Role = 'user' | 'assistant' | 'system'
export interface Msg { role: Role; content: string; intent?: string; ts: number }

export interface SavedSession {
  id: string
  title: string
  messages: Msg[]
  backendSessionId?: string
  createdAt: number
  updatedAt: number
}

type SpeechRecognitionLike = {
  lang: string; continuous: boolean; interimResults: boolean
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null
  onend: (() => void) | null
  onerror: ((e: { error: string }) => void) | null
  start: () => void; stop: () => void; abort: () => void
}

export function getSpeechRecognition(): SpeechRecognitionLike | null {
  const w = window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike; webkitSpeechRecognition?: new () => SpeechRecognitionLike }
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition
  return Ctor ? new Ctor() : null
}

// ─── Constants ────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'mci_chat_sessions'
const MAX_SESSIONS = 60

export const VOICE_LANGS = [
  { code: 'hi', sttLang: 'hi-IN', label: 'Hindi (Swara)' },
  { code: 'en', sttLang: 'en-IN', label: 'English (Neerja)' },
  { code: 'ta', sttLang: 'ta-IN', label: 'Tamil (Pallavi)' },
  { code: 'te', sttLang: 'te-IN', label: 'Telugu (Shruti)' },
  { code: 'bn', sttLang: 'bn-IN', label: 'Bengali (Tanishaa)' },
]
const VOICE_LANG_KEY = 'cfip-voice-lang'
const WAKE_KEY       = 'cfip-wake'
const FOLLOWUP_KEY   = 'cfip-followup'

function loadVoiceLang(): string {
  try { return localStorage.getItem(VOICE_LANG_KEY) || 'hi' } catch { return 'hi' }
}
function loadWakeEnabled(): boolean {
  try { return localStorage.getItem(WAKE_KEY) !== 'off' } catch { return true }
}
function loadFollowUpEnabled(): boolean {
  try { return localStorage.getItem(FOLLOWUP_KEY) !== 'off' } catch { return true }
}

// Wake words + common mis-hearings; Hindi STT returns Devanagari script.
export const WAKE_WORDS = [
  'veda', 'adya', 'vedha', 'aadya', 'vida', 'vader', 'adia',
  'weda', 'vaida', 'veeda', 'aadia', 'adhya',
  'वेदा', 'वेधा', 'आद्या', 'अद्या', 'वेद', 'विदा',
]
// TTS playback volume: slightly below full so the mic can still hear the
// user's wake word over Veda's own voice from the speakers (barge-in)
const TTS_VOLUME = 0.85

const GREETINGS: Record<string, string> = {
  hi: 'जी, बोलिए। मैं सुन रही हूँ।',
  en: 'Yes, I am listening. How can I help?',
}
const FILLERS: Record<string, string> = {
  hi: 'एक क्षण।',
  en: 'One moment.',
}

// Push-to-talk / wake-command capture timing (V3.2/V3.3 field fixes --
// see module docstring, do not change without re-testing on real devices)
export const INITIAL_WAIT_MS = 8000
export const SILENCE_MS      = 2500
export const MAX_CAPTURE_MS  = 25000

// Hands-free follow-up window (Phase V4): after Veda finishes speaking a
// voice-mode reply, the mic re-opens WITHOUT requiring the wake word again.
// Shorter than INITIAL_WAIT_MS -- the user is already mid-conversation, no
// need to give them as long to decide to speak as the cold-open wake case.
export const FOLLOWUP_WAIT_MS = 6000

// ─── Helpers ──────────────────────────────────────────────────────────────────

// Two-tone "go ahead" earcon for follow-up listening -- synthesized via Web
// Audio (no network round trip, no added latency right after a reply). Kept
// deliberately understated: this replaces a spoken "yes, I'm listening"
// greeting, which would be repeated after every single follow-up turn and
// read as robotic/annoying.
function playFollowUpChime() {
  try {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!Ctx) return
    if (!audioCtx) audioCtx = new Ctx()
    const ctx = audioCtx
    const t0 = ctx.currentTime
    const gain = ctx.createGain()
    gain.gain.setValueAtTime(0, t0)
    gain.gain.linearRampToValueAtTime(0.06, t0 + 0.02)
    gain.gain.linearRampToValueAtTime(0, t0 + 0.22)
    gain.connect(ctx.destination)
    const osc = ctx.createOscillator()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(660, t0)
    osc.frequency.setValueAtTime(880, t0 + 0.09)
    osc.connect(gain)
    osc.start(t0)
    osc.stop(t0 + 0.24)
  } catch {
    // Non-essential UX cue -- never let it interfere with the mic opening.
  }
}

export function genId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function makeWelcome(): Msg {
  return {
    role: 'assistant',
    content: "Hello! I'm your market intelligence chatbot — Ask me anything about markets, sectors, stocks, or flows.",
    ts: Date.now(),
  }
}

export function makeTitle(msgs: Msg[]): string {
  const first = msgs.find(m => m.role === 'user')
  if (!first) return 'New Chat'
  return first.content.length > 50 ? first.content.slice(0, 47) + '...' : first.content
}

function loadSessions(): SavedSession[] {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]') }
  catch { return [] }
}
function saveSessions(list: SavedSession[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_SESSIONS)))
}

function splitForStaging(text: string): [string, string] {
  if (text.length <= 220) return [text, '']
  const head = text.slice(0, 260)
  for (const stop of ['. ', '? ', '! ', '। ']) {
    const i = head.lastIndexOf(stop)
    if (i > 60) return [text.slice(0, i + 1), text.slice(i + 1)]
  }
  return [text, '']
}

// ─── Module-level singletons ────────────────────────────────────────────────
// Imperative Web API handles -- deliberately NOT in Zustand state, since
// there must only ever be ONE of each app-wide (one mic session, one
// audio element), regardless of how many components read the store.

let commandRecog: SpeechRecognitionLike | null = null
let currentAudio: HTMLAudioElement | null = null
let speakGen = 0
let wakeUsed = false
let greetingUrl: string | null = null
let fillerUrl: string | null = null
let audioPrefetchedForLang: string | null = null

// Web Audio analyser for the orb's speaking animation (real amplitude, not
// a canned loop). One AudioContext for the app's lifetime; a fresh
// MediaElementSource per NEW Audio element (speak() never reuses one, and
// the Web Audio spec only allows createMediaElementSource() ONCE per
// element). Analyser is always routed through to ctx.destination --
// skipping that step would silence playback entirely, so this is wrapped
// in try/catch and never allowed to interfere with a.play() itself.
let audioCtx: AudioContext | null = null
let analyserRaf: number | null = null

function attachAnalyser(audioEl: HTMLAudioElement) {
  try {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!Ctx) return
    if (!audioCtx) audioCtx = new Ctx()
    const source = audioCtx.createMediaElementSource(audioEl)
    const analyser = audioCtx.createAnalyser()
    analyser.fftSize = 64
    source.connect(analyser)
    analyser.connect(audioCtx.destination)   // required -- keeps playback audible
    const data = new Uint8Array(analyser.frequencyBinCount)
    if (analyserRaf) cancelAnimationFrame(analyserRaf)
    const tick = () => {
      analyser.getByteFrequencyData(data)
      const avg = data.reduce((a, b) => a + b, 0) / data.length
      useVedaStore.setState({ audioLevel: avg / 255 })
      analyserRaf = requestAnimationFrame(tick)
    }
    tick()
  } catch {
    // Any Web Audio quirk (autoplay policy, browser support) -- fail
    // silently, orb falls back to a non-reactive pulse; TTS playback
    // itself is entirely unaffected since a.play() is called separately.
  }
}

function stopAnalyser() {
  if (analyserRaf) { cancelAnimationFrame(analyserRaf); analyserRaf = null }
  useVedaStore.setState({ audioLevel: 0 })
}

function prefetchAudio(lang: string) {
  if (audioPrefetchedForLang === lang) return
  audioPrefetchedForLang = lang
  const prefetch = (text: string, assign: (url: string) => void) =>
    fetch('/api/voice/tts', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language: lang }),
    })
      .then(r => (r.ok ? r.blob() : null))
      .then(b => { if (b) assign(URL.createObjectURL(b)) })
      .catch(() => { /* best-effort */ })
  prefetch(GREETINGS[lang] ?? GREETINGS.en, u => { greetingUrl = u })
  prefetch(FILLERS[lang] ?? FILLERS.en, u => { fillerUrl = u })
}

// ─── Store ────────────────────────────────────────────────────────────────────

interface VedaState {
  // Sessions
  sessions:   SavedSession[]
  currentId:  string
  messages:   Msg[]
  backendSid: string | undefined

  // Voice settings (persisted)
  voiceLang:      string
  speakReplies:   boolean
  wakeEnabled:    boolean
  followUpEnabled: boolean   // hands-free: keep listening after a voice reply
                              // without requiring the wake word again

  // Live state (shared across every surface)
  listening:      boolean
  speaking:       boolean
  loading:        boolean
  apiError:       string | null
  liveTranscript: string   // interim speech-to-text while listening, shown
                            // as a live preview by whichever surface is open
  audioLevel: number       // 0-1 real TTS playback amplitude, for the orb's
                            // speaking animation (see attachAnalyser)
  followUpListening: boolean  // true while the mic is open in follow-up mode
                               // (no wake word needed) -- lets the UI show a
                               // distinct status from wake-triggered listening

  // Widget UI
  widgetOpen: boolean

  // Voice-born chat tracking (a chat started by voice keeps auto-speaking replies)
  _voiceChats: Set<string>

  // Actions
  setWidgetOpen: (open: boolean) => void
  setVoiceLang: (lang: string) => void
  setSpeakReplies: (v: boolean) => void
  setWakeEnabled: (v: boolean) => void
  setFollowUpEnabled: (v: boolean) => void
  setApiError: (msg: string | null) => void
  handleNewChat: () => Promise<void>
  handleSelectSession: (s: SavedSession) => void
  handleDeleteSession: (id: string) => void
  deleteAllSessions: () => void
  send: (text: string, mode?: 'voice' | 'text', sidOverride?: string | null) => Promise<void>
  sendVoiceCommand: (spoken: string) => void
  speak: (text: string) => Promise<void>
  stopSpeaking: () => void
  startListening: (opts?: { isFollowUp?: boolean }) => void
  markWakeUsed: () => void
}

export const useVedaStore = create<VedaState>((set, get) => ({
  sessions:   loadSessions(),
  currentId:  genId(),
  messages:   [makeWelcome()],
  backendSid: undefined,

  voiceLang:       loadVoiceLang(),
  speakReplies:    true,
  wakeEnabled:     loadWakeEnabled(),
  followUpEnabled: loadFollowUpEnabled(),

  listening: false,
  followUpListening: false,
  speaking:  false,
  loading:   false,
  apiError:  null,
  liveTranscript: '',
  audioLevel: 0,

  widgetOpen: false,
  _voiceChats: new Set(),

  setWidgetOpen: (open) => set({ widgetOpen: open }),

  setVoiceLang: (lang) => {
    set({ voiceLang: lang })
    try { localStorage.setItem(VOICE_LANG_KEY, lang) } catch { /* ignore */ }
    audioPrefetchedForLang = null
    prefetchAudio(lang)
  },

  setSpeakReplies: (v) => set({ speakReplies: v }),

  setWakeEnabled: (v) => {
    set({ wakeEnabled: v })
    try { localStorage.setItem(WAKE_KEY, v ? 'on' : 'off') } catch { /* ignore */ }
  },

  setFollowUpEnabled: (v) => {
    set({ followUpEnabled: v })
    try { localStorage.setItem(FOLLOWUP_KEY, v ? 'on' : 'off') } catch { /* ignore */ }
  },

  setApiError: (msg) => set({ apiError: msg }),

  markWakeUsed: () => { wakeUsed = true },

  handleNewChat: async () => {
    const { backendSid } = get()
    if (backendSid) { try { await resetChatSession(backendSid) } catch { /* ignore */ } }
    set({ currentId: genId(), messages: [makeWelcome()], backendSid: undefined, apiError: null })
  },

  handleSelectSession: (s) => {
    set({ currentId: s.id, messages: s.messages, backendSid: s.backendSessionId, apiError: null })
  },

  handleDeleteSession: (id) => {
    const next = get().sessions.filter(s => s.id !== id)
    saveSessions(next)
    set({ sessions: next })
    if (id === get().currentId) get().handleNewChat()
  },

  deleteAllSessions: () => {
    saveSessions([])
    set({ sessions: [] })
  },

  stopSpeaking: () => {
    speakGen += 1
    currentAudio?.pause()
    try { window.speechSynthesis?.cancel() } catch { /* ignore */ }
    stopAnalyser()
    set({ speaking: false })
  },

  // Resolves only when playback has TRULY finished (or was aborted by a
  // newer speak()/stopSpeaking() call) -- never on "TTS fetch kicked off".
  // Callers that need to react after Veda stops talking (hands-free
  // follow-up listening) depend on this; before this rework the function
  // resolved as soon as playback started, which is too early to chain on.
  speak: (text) => new Promise<void>((resolve) => {
    const gen = ++speakGen
    currentAudio?.pause()
    try { window.speechSynthesis?.cancel() } catch { /* ignore */ }

    const lang = get().voiceLang
    const fetchTtsUrl = async (t: string): Promise<string | null> => {
      try {
        const r = await fetch('/api/voice/tts', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: t, language: lang }),
        })
        if (!r.ok) return null
        return URL.createObjectURL(await r.blob())
      } catch { return null }
    }
    const browserTtsFallback = (t: string) => {
      try {
        const u = new SpeechSynthesisUtterance(t.slice(0, 800))
        u.lang = (VOICE_LANGS.find(l => l.code === lang) ?? VOICE_LANGS[0]).sttLang
        u.onend = () => { set({ speaking: false }); resolve() }
        u.onerror = () => { set({ speaking: false }); resolve() }
        set({ speaking: true })
        window.speechSynthesis.speak(u)
      } catch { set({ speaking: false }); resolve() }
    }

    ;(async () => {
      const [head, tail] = splitForStaging(text)
      const headP = fetchTtsUrl(head)
      const tailP = tail ? fetchTtsUrl(tail) : Promise.resolve(null)

      const headUrl = await headP
      if (gen !== speakGen) { resolve(); return }
      if (!headUrl) { browserTtsFallback(text); return }

      const playUrl = (url: string, onDone: () => void) => {
        const a = new Audio(url)
        a.volume = TTS_VOLUME
        currentAudio = a
        a.onended = onDone
        a.onerror = onDone
        attachAnalyser(a)
        a.play().catch(onDone)
      }
      set({ speaking: true })
      playUrl(headUrl, async () => {
        if (gen !== speakGen) { stopAnalyser(); set({ speaking: false }); resolve(); return }
        const tailUrl = await tailP
        if (gen !== speakGen || !tailUrl) { stopAnalyser(); set({ speaking: false }); resolve(); return }
        playUrl(tailUrl, () => { stopAnalyser(); set({ speaking: false }); resolve() })
      })
    })()
  }),

  send: async (text, mode = 'text', sidOverride) => {
    const trimmed = text.trim()
    const { loading, backendSid, currentId, speakReplies, _voiceChats } = get()
    if (!trimmed || loading) return

    const userMsg: Msg = { role: 'user', content: trimmed, ts: Date.now() }
    set(s => ({ messages: [...s.messages, userMsg], loading: true, apiError: null }))

    const sid = sidOverride !== undefined ? (sidOverride ?? undefined) : backendSid
    const t0 = Date.now()
    let fillerTimer: ReturnType<typeof setTimeout> | null = null
    if (mode === 'voice' && fillerUrl) {
      fillerTimer = setTimeout(() => {
        try { const a = new Audio(fillerUrl as string); a.volume = TTS_VOLUME; currentAudio = a; a.play().catch(() => {}) }
        catch { /* ignore */ }
      }, 2500)
    }
    try {
      const data: ChatResponseData = await sendChat(trimmed, sid, mode)
      if (fillerTimer) { clearTimeout(fillerTimer); fillerTimer = null }
      set(s => ({
        backendSid: data.session_id,
        messages: [...s.messages, { role: 'assistant' as Role, content: data.reply, intent: data.intent, ts: Date.now() }],
      }))
      // logTurn (analytics) -- fire and forget, never break chat
      const wake = wakeUsed
      wakeUsed = false
      fetch('/api/voice/log', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: data.session_id, mode, language: get().voiceLang, wake_word_used: wake,
          user_message: trimmed, intent: data.intent ?? '', reply_chars: data.reply.length,
          latency_ms: Date.now() - t0, tts_voice: mode === 'voice' ? get().voiceLang : '',
          symbols: data.symbols_discussed ?? [],
          flag_reason: data.flag_reason ?? null,
        }),
      }).catch(() => { /* analytics must never break chat */ })

      if (mode === 'voice' || (speakReplies && _voiceChats.has(currentId))) {
        get().speak(data.reply).then(() => {
          // Hands-free follow-up (Phase V4): only chain another listening
          // window for a turn that was ITSELF spoken by voice, and only if
          // nothing else has already claimed the mic/turn in the meantime
          // (a wake-word barge-in mid-reply, a new send() in flight, or the
          // user manually opening the mic) -- those set listening/loading/
          // speaking, and any one of them means this reply's follow-up
          // window is stale and must not fire.
          if (mode !== 'voice') return
          const st = get()
          if (!st.followUpEnabled || !st.wakeEnabled) return
          if (st.listening || st.loading || st.speaking) return
          st.startListening({ isFollowUp: true })
        })
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      const errText = detail ?? 'Connection error. Check that the backend is running.'
      set(s => ({
        apiError: errText,
        messages: [...s.messages, { role: 'assistant' as Role, content: `Sorry, I could not process that. ${errText}`, ts: Date.now() }],
      }))
    } finally {
      if (fillerTimer) clearTimeout(fillerTimer)
      set({ loading: false })

      // Auto-save to localStorage (mirrors the previous per-render effect)
      const st = get()
      if (st.messages.length > 1) {
        const session: SavedSession = {
          id: st.currentId, title: makeTitle(st.messages), messages: st.messages,
          backendSessionId: st.backendSid,
          createdAt: st.sessions.find(s => s.id === st.currentId)?.createdAt ?? Date.now(),
          updatedAt: Date.now(),
        }
        const idx = st.sessions.findIndex(s => s.id === st.currentId)
        const next = idx >= 0 ? st.sessions.map(s => s.id === st.currentId ? session : s) : [session, ...st.sessions]
        saveSessions(next)
        set({ sessions: next })
      }
    }
  },

  sendVoiceCommand: (spoken) => {
    const { messages, currentId, _voiceChats } = get()
    if (messages.length > 1 && !_voiceChats.has(currentId)) {
      const newId = genId()
      _voiceChats.add(newId)
      set({ currentId: newId, messages: [makeWelcome()], backendSid: undefined })
      setTimeout(() => get().send(spoken, 'voice', null), 60)
    } else {
      _voiceChats.add(currentId)
      get().send(spoken, 'voice')
    }
  },

  startListening: (opts) => {
    const isFollowUp = opts?.isFollowUp ?? false
    const { listening, voiceLang } = get()
    if (listening) { commandRecog?.stop(); return }
    const recog = getSpeechRecognition()
    if (!recog) {
      // A follow-up window opening in the background finding no Web Speech
      // support would be a confusing error to surface uninvited -- the user
      // never asked for this listen, so fail silently and just don't open
      // the mic (wake-triggered/manual starts still show the real error).
      if (!isFollowUp) {
        set({ apiError: 'Voice input needs Chrome or Edge (Web Speech API not available)' })
      }
      return
    }
    get().stopSpeaking()
    const langMeta = VOICE_LANGS.find(l => l.code === voiceLang) ?? VOICE_LANGS[0]
    recog.lang = langMeta.sttLang
    recog.continuous = true
    recog.interimResults = true
    commandRecog = recog
    set({ listening: true, liveTranscript: '', followUpListening: isFollowUp })
    if (isFollowUp) playFollowUpChime()

    let finalText = ''
    let heardAnything = false
    let silenceTimer: ReturnType<typeof setTimeout> | null = null
    const armSilence = (ms: number) => {
      if (silenceTimer) clearTimeout(silenceTimer)
      silenceTimer = setTimeout(() => { try { recog.stop() } catch { /* ignore */ } }, ms)
    }
    armSilence(isFollowUp ? FOLLOWUP_WAIT_MS : INITIAL_WAIT_MS)
    const hardCap = setTimeout(() => { try { recog.stop() } catch { /* ignore */ } }, MAX_CAPTURE_MS)

    recog.onresult = (e) => {
      heardAnything = true
      let interim = ''
      finalText = ''
      for (let i = 0; i < e.results.length; i++) {
        const res = e.results[i]
        if (res.isFinal) finalText += res[0].transcript + ' '
        else interim += res[0].transcript
      }
      set({ liveTranscript: (finalText + interim).trim() })
      armSilence(SILENCE_MS)
    }
    recog.onerror = () => { set({ listening: false, followUpListening: false }) }
    recog.onend = () => {
      if (silenceTimer) clearTimeout(silenceTimer)
      clearTimeout(hardCap)
      set({ listening: false, followUpListening: false })
      const spoken = finalText.trim()
      if (!spoken) {
        wakeUsed = false
        // Silence during a follow-up window is the NORMAL end of a
        // hands-free exchange (user is done talking) -- not an error.
        // Only the wake-triggered/manual case, where the user explicitly
        // asked Veda to listen, warrants telling them nothing was heard.
        if (!heardAnything && !isFollowUp) {
          set({ apiError: 'Veda did not hear anything -- say "Veda" and speak within a few seconds, or use the mic button.' })
          setTimeout(() => set({ apiError: null }), 6000)
        }
        return
      }
      set({ liveTranscript: '' })
      get().sendVoiceCommand(spoken)
    }
    try { recog.start() } catch { set({ listening: false, followUpListening: false }) }
  },
}))

// Kick off the greeting/filler prefetch for the initial language immediately
prefetchAudio(useVedaStore.getState().voiceLang)

// ─── Wake-word listener lifecycle (owned by VedaWakeController) ──────────────
// Exported so exactly one component (mounted once in AppShell) can drive
// this -- never call these from more than one place, or two mic sessions
// will fight each other.

let wakeRecog: SpeechRecognitionLike | null = null
let wakeDisposed = true
let wakeStartTimer: ReturnType<typeof setTimeout> | null = null

export function stopWakeListener() {
  wakeDisposed = true
  if (wakeStartTimer) clearTimeout(wakeStartTimer)
  try { wakeRecog?.abort() } catch { /* ignore */ }
  wakeRecog = null
}

export function startWakeListener(onRetry: () => void) {
  const { wakeEnabled, listening, loading, voiceLang } = useVedaStore.getState()
  if (!wakeEnabled || listening || loading) return
  const recog = getSpeechRecognition()
  if (!recog) return

  wakeDisposed = false
  let matched = false
  const langMeta = VOICE_LANGS.find(l => l.code === voiceLang) ?? VOICE_LANGS[0]
  recog.lang = langMeta.sttLang
  recog.continuous = true
  recog.interimResults = true

  const onWake = (fullTranscript: string, matchedWord: string) => {
    matched = true
    try { recog.abort() } catch { /* ignore */ }
    useVedaStore.getState().stopSpeaking()
    wakeUsed = true

    const idx = fullTranscript.toLowerCase().lastIndexOf(matchedWord)
    const trailing = idx >= 0 ? fullTranscript.slice(idx + matchedWord.length) : ''
    const inlineCommand = trailing.replace(/^[,.\s।]+/, '').trim()
    if (inlineCommand.split(/\s+/).filter(Boolean).length >= 2) {
      useVedaStore.getState().sendVoiceCommand(inlineCommand)
      return
    }

    const play = greetingUrl ? new Audio(greetingUrl) : null
    if (play) {
      play.volume = TTS_VOLUME
      useVedaStore.setState({ speaking: true })
      const done = () => { useVedaStore.setState({ speaking: false }); useVedaStore.getState().startListening() }
      play.onended = done
      play.onerror = done
      play.play().catch(done)
    } else {
      useVedaStore.getState().startListening()
    }
  }

  recog.onresult = (e) => {
    let combined = ''
    for (let i = 0; i < e.results.length; i++) combined += (e.results[i][0]?.transcript ?? '') + ' '
    const heardLower = combined.toLowerCase()
    const hit = WAKE_WORDS.find(w => heardLower.includes(w))
    if (hit) onWake(combined, hit)
  }
  recog.onerror = (e) => {
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      useVedaStore.getState().setWakeEnabled(false)
    }
  }
  recog.onend = () => {
    if (!matched && !wakeDisposed) setTimeout(onRetry, 250)
  }

  wakeStartTimer = setTimeout(() => {
    if (wakeDisposed) return
    try { recog.start() } catch {
      if (!wakeDisposed) setTimeout(onRetry, 800)
    }
  }, 350)

  wakeRecog = recog
}
