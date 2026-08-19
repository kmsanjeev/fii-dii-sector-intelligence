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
import {
  deleteAllChatSavedSessions,
  deleteChatSavedSession,
  sendChat,
  resetChatSession,
  fetchChatCapabilities,
  fetchChatSavedSessions,
  upsertChatSavedSession,
  uploadChatAttachment,
  type ChatKnowledgeSaved,
  type ChatCapabilities,
  type ChatAttachmentStub,
  type ChatLocalEvidenceMeta,
  type ChatResponseData,
  type ChatResearchMeta,
} from '../api/client'

// ─── Types ────────────────────────────────────────────────────────────────────

export type Role = 'user' | 'assistant' | 'system'
export interface Msg {
  role: Role
  content: string
  intent?: string
  ts: number
  research?: ChatResearchMeta
  localEvidence?: ChatLocalEvidenceMeta
  attachments?: ChatAttachmentStub[]
  knowledge?: ChatKnowledgeSaved
}

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
const DEFAULT_ATTACHMENT_ACCEPT = 'application/pdf,text/*,application/json,image/*'
const RESEARCH_DISABLED_ERROR = 'Research mode is not enabled by the backend yet.'
const RESEARCH_NOT_READY_ERROR = 'Research mode is enabled, but no live research provider is available right now.'

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
const RESEARCH_MODE_KEY = 'cfip-research-mode'

function loadVoiceLang(): string {
  try { return localStorage.getItem(VOICE_LANG_KEY) || 'hi' } catch { return 'hi' }
}
function loadWakeEnabled(): boolean {
  try { return localStorage.getItem(WAKE_KEY) !== 'off' } catch { return true }
}
function loadFollowUpEnabled(): boolean {
  try { return localStorage.getItem(FOLLOWUP_KEY) !== 'off' } catch { return true }
}
function loadResearchMode(): boolean {
  try { return localStorage.getItem(RESEARCH_MODE_KEY) === 'on' } catch { return false }
}

function buildAttachmentAccept(prefixes: string[]): string {
  if (!prefixes.length) return DEFAULT_ATTACHMENT_ACCEPT
  return prefixes.map(prefix => (
    prefix.endsWith('/') ? `${prefix}*` : prefix
  )).join(',')
}

function isResearchRuntimeReady(caps: ChatCapabilities): boolean {
  return Boolean(caps.research_enabled && caps.research_runtime_ready)
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
    content: "Hello! I'm Veda, your conversational assistant. Ask me anything, or explore markets, Jyotish, research, and other specialist capabilities.",
    ts: Date.now(),
  }
}

export function makeTitle(msgs: Msg[]): string {
  const first = msgs.find(m => m.role === 'user')
  if (!first) return 'New Chat'
  return first.content.length > 50 ? first.content.slice(0, 47) + '...' : first.content
}

function loadSessions(): SavedSession[] {
  try { return sortSessions(JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')) }
  catch { return [] }
}
function saveSessions(list: SavedSession[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sortSessions(list)))
}

function sortSessions(list: SavedSession[]): SavedSession[] {
  return [...list]
    .sort((a, b) => (
      (b.updatedAt ?? 0) - (a.updatedAt ?? 0) ||
      (b.createdAt ?? 0) - (a.createdAt ?? 0)
    ))
    .slice(0, MAX_SESSIONS)
}

function upsertSessionInList(list: SavedSession[], session: SavedSession): SavedSession[] {
  return sortSessions([session, ...list.filter(existing => existing.id !== session.id)])
}

function mergeSavedSessions(
  localSessions: SavedSession[],
  remoteSessions: SavedSession[],
): { merged: SavedSession[]; pendingUpload: SavedSession[] } {
  const merged = new Map<string, SavedSession>()
  const pendingUpload: SavedSession[] = []

  for (const session of remoteSessions) {
    merged.set(session.id, session)
  }
  for (const localSession of localSessions) {
    const remoteSession = merged.get(localSession.id)
    if (!remoteSession || (localSession.updatedAt ?? 0) > (remoteSession.updatedAt ?? 0)) {
      merged.set(localSession.id, localSession)
      pendingUpload.push(localSession)
    }
  }

  return {
    merged: sortSessions(Array.from(merged.values())),
    pendingUpload: sortSessions(pendingUpload),
  }
}

function syncSessionToBackend(session: SavedSession): void {
  void upsertChatSavedSession(session).catch(() => { /* best-effort */ })
}

function syncDeleteSessionFromBackend(sessionId: string): void {
  void deleteChatSavedSession(sessionId).catch(() => { /* best-effort */ })
}

function syncDeleteAllSessionsFromBackend(): void {
  void deleteAllChatSavedSessions().catch(() => { /* best-effort */ })
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
let sessionsHydrated = false
let sessionsHydrationPromise: Promise<void> | null = null

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
  researchMode: boolean
  researchEnabled: boolean
  researchProviderAvailable: boolean
  researchRuntimeReady: boolean
  attachmentsEnabled: boolean
  saveToKnowledgeEnabled: boolean
  mitRepoIntakeEnabled: boolean
  mcpEnabled: boolean
  voiceEnabled: boolean
  capabilityStates: NonNullable<ChatCapabilities['capability_states']>
  mcpServerNames: string[]
  supportedAttachmentMimePrefixes: string[]
  attachmentAccept: string
  pendingAttachments: ChatAttachmentStub[]
  uploadingAttachment: boolean

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
  setResearchMode: (v: boolean) => void
  setApiError: (msg: string | null) => void
  uploadAttachment: (file: File) => Promise<void>
  removePendingAttachment: (storageKey?: string | null, name?: string) => void
  clearPendingAttachments: () => void
  markKnowledgeSaved: (messageTs: number, saved: ChatKnowledgeSaved) => void
  hydrateSavedSessions: () => Promise<void>
  refreshCapabilities: () => Promise<void>
  importSession: (session: SavedSession) => void
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
  researchMode:    loadResearchMode(),
  researchEnabled: true,
  researchProviderAvailable: false,
  researchRuntimeReady: false,
  attachmentsEnabled: false,
  saveToKnowledgeEnabled: false,
  mitRepoIntakeEnabled: false,
  mcpEnabled: false,
  // Optimistic until the backend capability snapshot arrives; a disabled
  // backend still rejects TTS/chat execution and refreshCapabilities replaces
  // this with the effective policy state.
  voiceEnabled: true,
  capabilityStates: [],
  mcpServerNames: [],
  supportedAttachmentMimePrefixes: [],
  attachmentAccept: DEFAULT_ATTACHMENT_ACCEPT,
  pendingAttachments: [],
  uploadingAttachment: false,

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

  setResearchMode: (v) => {
    if (v && !get().researchEnabled) {
      set({ apiError: RESEARCH_DISABLED_ERROR })
      return
    }
    if (v && !get().researchRuntimeReady) {
      set({ apiError: RESEARCH_NOT_READY_ERROR })
      return
    }
    set({ researchMode: v })
    try { localStorage.setItem(RESEARCH_MODE_KEY, v ? 'on' : 'off') } catch { /* ignore */ }
  },

  setApiError: (msg) => set({ apiError: msg }),

  uploadAttachment: async (file) => {
    if (!get().attachmentsEnabled) {
      set({ apiError: 'Attachments are not enabled by the backend yet.' })
      return
    }
    set({ uploadingAttachment: true, apiError: null })
    try {
      const uploaded = await uploadChatAttachment(file)
      set(s => ({
        pendingAttachments: [...s.pendingAttachments, uploaded],
      }))
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      set({ apiError: detail ?? 'Attachment upload failed. Please try again.' })
    } finally {
      set({ uploadingAttachment: false })
    }
  },

  removePendingAttachment: (storageKey, name) => {
    set(s => ({
      pendingAttachments: s.pendingAttachments.filter(att => {
        if (storageKey && att.storage_key) return att.storage_key !== storageKey
        return att.name !== name
      }),
    }))
  },

  clearPendingAttachments: () => set({ pendingAttachments: [] }),

  markKnowledgeSaved: (messageTs, saved) => {
    let updatedSession: SavedSession | null = null
    set(state => {
      const nextMessages = state.messages.map(message => (
        message.ts === messageTs ? { ...message, knowledge: saved } : message
      ))
      let nextSessions = state.sessions
      const idx = state.sessions.findIndex(session => session.id === state.currentId)
      if (idx >= 0) {
        updatedSession = {
          ...state.sessions[idx],
          messages: nextMessages,
          updatedAt: Date.now(),
        }
        nextSessions = upsertSessionInList(state.sessions, updatedSession)
        saveSessions(nextSessions)
      }
      return {
        messages: nextMessages,
        sessions: nextSessions,
      }
    })
    if (updatedSession) syncSessionToBackend(updatedSession)
  },

  hydrateSavedSessions: async () => {
    if (sessionsHydrated) return
    if (sessionsHydrationPromise) {
      await sessionsHydrationPromise
      return
    }

    sessionsHydrationPromise = (async () => {
      try {
        const localSessions = loadSessions()
        const remotePayload = await fetchChatSavedSessions()
        const { merged, pendingUpload } = mergeSavedSessions(localSessions, remotePayload.sessions ?? [])
        saveSessions(merged)
        set({ sessions: merged })
        for (const session of pendingUpload) {
          await upsertChatSavedSession(session)
        }
        sessionsHydrated = true
      } catch {
        // Best-effort. Local history remains usable if the backend is unavailable.
      } finally {
        sessionsHydrationPromise = null
      }
    })()

    await sessionsHydrationPromise
  },

  refreshCapabilities: async () => {
    try {
      const caps: ChatCapabilities = await fetchChatCapabilities()
      const researchRuntimeReady = isResearchRuntimeReady(caps)
      const next: Partial<VedaState> = {
        researchEnabled: caps.research_enabled,
        researchProviderAvailable: caps.research_provider_available,
        researchRuntimeReady,
        attachmentsEnabled: caps.attachments_enabled,
        saveToKnowledgeEnabled: caps.save_to_knowledge_enabled,
        mitRepoIntakeEnabled: caps.mit_repo_intake_enabled,
        mcpEnabled: caps.mcp_enabled,
        voiceEnabled: caps.voice_enabled ?? true,
        capabilityStates: caps.capability_states ?? [],
        mcpServerNames: caps.mcp_server_names,
        supportedAttachmentMimePrefixes: caps.supported_attachment_mime_prefixes,
        attachmentAccept: buildAttachmentAccept(caps.supported_attachment_mime_prefixes),
      }
      if ((!caps.research_enabled || !researchRuntimeReady) && get().researchMode) {
        next.researchMode = false
        try { localStorage.setItem(RESEARCH_MODE_KEY, 'off') } catch { /* ignore */ }
      }
      set(next)
    } catch {
      // Best-effort. The UI keeps the last known local state if the backend
      // is unavailable during page load.
    }
    await get().hydrateSavedSessions()
  },

  markWakeUsed: () => { wakeUsed = true },

  handleNewChat: async () => {
    const { backendSid } = get()
    if (backendSid) { try { await resetChatSession(backendSid) } catch { /* ignore */ } }
    set({
      currentId: genId(),
      messages: [makeWelcome()],
      backendSid: undefined,
      apiError: null,
      pendingAttachments: [],
      uploadingAttachment: false,
    })
  },

  handleSelectSession: (s) => {
    set({
      currentId: s.id,
      messages: s.messages,
      backendSid: s.backendSessionId,
      apiError: null,
      pendingAttachments: [],
      uploadingAttachment: false,
    })
  },

  importSession: (session) => {
    const next = upsertSessionInList(get().sessions, session)
    saveSessions(next)
    set({ sessions: next })
    syncSessionToBackend(session)
  },

  handleDeleteSession: (id) => {
    const next = get().sessions.filter(s => s.id !== id)
    saveSessions(next)
    set({ sessions: next })
    syncDeleteSessionFromBackend(id)
    if (id === get().currentId) get().handleNewChat()
  },

  deleteAllSessions: () => {
    saveSessions([])
    set({ sessions: [], pendingAttachments: [], uploadingAttachment: false })
    syncDeleteAllSessionsFromBackend()
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
    if (!get().voiceEnabled) { set({ apiError: 'Voice capability is disabled by administrator configuration.' }); resolve(); return }
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
        // Prefer a female voice to match Veda's persona; the primary edge-tts path
        // uses a named female neural voice -- the browser fallback should too.
        // Wrapped in its own try/catch: a getVoices() failure must never suppress speech.
        try {
          const voices = window.speechSynthesis.getVoices()
          if (voices.length > 0) {
            const prefix = u.lang
            const femaleInLang = voices.find(
              v => v.lang.startsWith(prefix) &&
                   (v.name + v.voiceURI).toLowerCase().includes('female'),
            )
            const langMatch   = voices.find(v => v.lang.startsWith(prefix))
            const anyFemale   = voices.find(
              v => (v.name + v.voiceURI).toLowerCase().includes('female'),
            )
            u.voice = femaleInLang ?? langMatch ?? anyFemale ?? null
          }
        } catch {
          // getVoices() unavailable or threw — leave u.voice = null (browser default)
        }
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
    const { loading, backendSid, currentId, speakReplies, _voiceChats, researchMode, pendingAttachments } = get()
    const hasAttachments = pendingAttachments.length > 0
    if (mode === 'voice' && !get().voiceEnabled) {
      set({ apiError: 'Voice capability is disabled by administrator configuration.' })
      return
    }
    const finalPrompt = trimmed || (hasAttachments ? 'Please study the attached file(s) and help me with them.' : '')
    if (!finalPrompt || loading) return

    const userMsg: Msg = {
      role: 'user',
      content: finalPrompt,
      ts: Date.now(),
      attachments: hasAttachments ? pendingAttachments : undefined,
    }
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
      const data: ChatResponseData = await sendChat(finalPrompt, sid, mode, {
        research_mode: researchMode,
        attachments: pendingAttachments,
      })
      if (fillerTimer) { clearTimeout(fillerTimer); fillerTimer = null }
      set(s => ({
        backendSid: data.session_id,
        pendingAttachments: [],
        messages: [...s.messages, {
          role: 'assistant' as Role,
          content: data.reply,
          intent: data.intent,
          ts: Date.now(),
          research: data.research,
          localEvidence: data.local_evidence,
        }],
      }))
      // logTurn (analytics) -- fire and forget, never break chat
      const wake = wakeUsed
      wakeUsed = false
      fetch('/api/voice/log', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: data.session_id, mode, language: get().voiceLang, wake_word_used: wake,
          user_message: finalPrompt, intent: data.intent ?? '', reply_chars: data.reply.length,
          latency_ms: Date.now() - t0, tts_voice: mode === 'voice' ? get().voiceLang : '',
          symbols: data.symbols_discussed ?? [],
          flag_reason: data.flag_reason ?? null,
          research_requested: data.research?.requested ?? researchMode,
          research_used: data.research?.used ?? false,
          research_provider: data.research?.provider ?? '',
          research_reason: data.research?.reason ?? null,
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
        const next = upsertSessionInList(st.sessions, session)
        saveSessions(next)
        set({ sessions: next })
        syncSessionToBackend(session)
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
    const { listening, voiceLang, voiceEnabled } = get()
    if (listening) { commandRecog?.stop(); return }
    if (!voiceEnabled) {
      if (!isFollowUp) set({ apiError: 'Voice capability is disabled by administrator configuration.' })
      return
    }
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
    recog.onerror = (ev) => {
      const errCode = (ev as { error?: string }).error ?? 'unknown'
      console.warn('[Veda] Speech recognition error:', errCode)
      set({ listening: false, followUpListening: false })
      if (errCode === 'not-allowed' || errCode === 'service-not-allowed') {
        set({ apiError: 'Microphone access denied. Please allow microphone permission in your browser and try again.' })
        setTimeout(() => set({ apiError: null }), 8000)
      } else if (errCode === 'no-speech') {
        // Silence — onend will handle the "did not hear" message
      } else if (errCode !== 'aborted') {
        set({ apiError: `Voice recognition error: ${errCode}. Try again or use the mic button.` })
        setTimeout(() => set({ apiError: null }), 6000)
      }
    }
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
    try { recog.start() } catch (e) {
      console.warn('[Veda] Speech recognition start() failed:', e)
      set({ listening: false, followUpListening: false })
      if (!isFollowUp) {
        set({ apiError: 'Could not start voice recognition. Ensure microphone permission is granted and you are using Chrome or Edge.' })
        setTimeout(() => set({ apiError: null }), 8000)
      }
    }
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
  const { wakeEnabled, listening, loading, voiceLang, voiceEnabled } = useVedaStore.getState()
  if (!voiceEnabled) return
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
