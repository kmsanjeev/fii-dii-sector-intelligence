/**
 * VedaWidget — Phase V-UI global voice assistant
 *
 * Two pieces, both mounted exactly once in AppShell (so they're alive on
 * every page, not just /chat):
 *
 *   <VedaWakeController />  renders nothing. Owns the wake-word listener
 *   lifecycle (see vedaStore's startWakeListener/stopWakeListener) --
 *   this MUST be the only place that calls those, or two mic sessions
 *   would fight each other.
 *
 *   <VedaWidget />  the top-bar icon + floating drawer. Reads/writes
 *   vedaStore, the same store the full /chat page (ChatPage.tsx) uses --
 *   a message sent from one surface appears in the other instantly.
 */
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useVedaStore, startWakeListener, stopWakeListener,
  VOICE_LANGS, type Msg,
} from '../../store/vedaStore'
import { VedaOrb } from './VedaOrb'

// ─── Wake-word listener controller (mount once) ───────────────────────────────

export function VedaWakeController() {
  const wakeEnabled = useVedaStore(s => s.wakeEnabled)
  const listening   = useVedaStore(s => s.listening)
  const loading     = useVedaStore(s => s.loading)
  const voiceLang   = useVedaStore(s => s.voiceLang)
  const [retryTick, setRetryTick] = useState(0)

  useEffect(() => {
    startWakeListener(() => setRetryTick(n => n + 1))
    return () => stopWakeListener()
  }, [wakeEnabled, listening, loading, voiceLang, retryTick])

  return null
}

// ─── Compact message bubble (drawer only -- ChatPage has its own richer one) ──

function DrawerBubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === 'user'
  if (msg.role === 'system') return null
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 10 }}>
      <div style={{
        maxWidth: '85%', padding: '8px 11px',
        borderRadius: isUser ? '10px 10px 2px 10px' : '2px 10px 10px 10px',
        background: isUser ? '#1E3A5F' : '#141720',
        border: `1px solid ${isUser ? '#1E4A8F' : '#1E2332'}`,
        color: '#E2E8F0', fontSize: 12, lineHeight: 1.55,
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {msg.content}
      </div>
    </div>
  )
}

// ─── Floating icon + drawer ─────────────────────────────────────────────────

export function VedaWidget() {
  const navigate = useNavigate()
  const open          = useVedaStore(s => s.widgetOpen)
  const setOpen        = useVedaStore(s => s.setWidgetOpen)
  const messages       = useVedaStore(s => s.messages)
  const listening      = useVedaStore(s => s.listening)
  const speaking        = useVedaStore(s => s.speaking)
  const loading         = useVedaStore(s => s.loading)
  const liveTranscript  = useVedaStore(s => s.liveTranscript)
  const apiError        = useVedaStore(s => s.apiError)
  const wakeEnabled     = useVedaStore(s => s.wakeEnabled)
  const followUpEnabled = useVedaStore(s => s.followUpEnabled)
  const followUpListening = useVedaStore(s => s.followUpListening)
  const voiceLang       = useVedaStore(s => s.voiceLang)
  const send            = useVedaStore(s => s.send)
  const startListening  = useVedaStore(s => s.startListening)
  const stopSpeaking    = useVedaStore(s => s.stopSpeaking)
  const setWakeEnabled  = useVedaStore(s => s.setWakeEnabled)
  const setFollowUpEnabled = useVedaStore(s => s.setFollowUpEnabled)
  const setVoiceLang    = useVedaStore(s => s.setVoiceLang)

  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const panelRef  = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open, setOpen])

  const statusText = speaking ? 'Speaking...'
    : listening ? (followUpListening ? 'Listening for follow-up...' : 'Listening...')
    : loading ? 'Thinking...'
    : wakeEnabled ? 'Say "Veda" or ask below' : 'Ask below'

  const submit = () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    send(text, 'text')
  }

  return (
    <div style={{ position: 'relative' }} ref={panelRef}>
      <button
        onClick={() => setOpen(!open)}
        title="Veda -- your market voice assistant"
        style={{
          background: open ? '#141720' : 'transparent',
          border: `1px solid ${open ? '#4080FF66' : 'transparent'}`,
          borderRadius: 8, padding: 4, cursor: 'pointer',
          display: 'flex', alignItems: 'center', flexShrink: 0,
        }}
      >
        <VedaOrb size={26} />
      </button>

      {open && (
        <div style={{
          position: 'fixed', top: 52, right: 12, width: 380,
          maxHeight: 'calc(100vh - 76px)', display: 'flex', flexDirection: 'column',
          background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 10,
          boxShadow: '0 12px 48px rgba(0,0,0,0.6)', zIndex: 1000, overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px',
            borderBottom: '1px solid #1E2332', flexShrink: 0, background: '#141720',
          }}>
            <VedaOrb size={30} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700 }}>Veda</div>
              <div style={{ color: '#64748B', fontSize: 10 }}>{statusText}</div>
            </div>
            {speaking && (
              <button onClick={stopSpeaking} title="Stop speaking" style={{
                background: 'transparent', border: '1px solid #2D3348', borderRadius: 4,
                color: '#94A3B8', fontSize: 10, padding: '3px 7px', cursor: 'pointer',
              }}>Stop</button>
            )}
            <button
              onClick={() => setOpen(false)}
              style={{ background: 'none', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer', lineHeight: 1, padding: 0 }}
            >×</button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px', minHeight: 200 }}>
            {messages.map((m, i) => <DrawerBubble key={i} msg={m} />)}
            {liveTranscript && (
              <div style={{ color: '#60A5FA', fontSize: 11, fontStyle: 'italic', padding: '4px 0' }}>
                {liveTranscript}...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {apiError && (
            <div style={{ margin: '0 14px 8px', padding: '6px 10px', borderRadius: 4, background: '#1a1200', border: '1px solid #F59E0B44', color: '#F59E0B', fontSize: 10 }}>
              {apiError}
            </div>
          )}

          {/* Controls */}
          <div style={{ padding: '10px 14px', borderTop: '1px solid #1E2332', flexShrink: 0 }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <button
                onClick={() => startListening()}
                disabled={loading}
                title={listening ? 'Listening... click to stop' : 'Speak to Veda'}
                style={{
                  width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                  border: `2px solid ${listening ? '#EF4444' : '#3B82F6'}`,
                  background: listening ? '#EF444422' : '#0D1117',
                  color: listening ? '#EF4444' : '#60A5FA',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
              >
                {listening ? (
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#EF4444' }} />
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                    <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4M8 22h8" />
                  </svg>
                )}
              </button>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') submit() }}
                placeholder={listening ? 'Listening...' : 'Ask about markets, sectors, stocks...'}
                disabled={loading}
                style={{
                  flex: 1, background: '#0D1117', border: '1px solid #1E2332', borderRadius: 6,
                  color: '#E2E8F0', padding: '0 10px', fontSize: 12, outline: 'none',
                }}
              />
              <button
                onClick={submit}
                disabled={!input.trim() || loading}
                style={{
                  padding: '0 14px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                  cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                  background: input.trim() && !loading ? '#1E3A5F' : '#0D1117',
                  color: input.trim() && !loading ? '#60A5FA' : '#334155',
                  border: `1px solid ${input.trim() && !loading ? '#3B82F6' : '#1E2332'}`,
                }}
              >Send</button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 6 }}>
                <select
                  value={voiceLang}
                  onChange={e => setVoiceLang(e.target.value)}
                  style={{ background: '#0D1117', border: '1px solid #1E2332', borderRadius: 4, color: '#94A3B8', fontSize: 9, padding: '2px 5px', cursor: 'pointer' }}
                >
                  {VOICE_LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
                </select>
                <button
                  onClick={() => setWakeEnabled(!wakeEnabled)}
                  title={wakeEnabled ? 'Wake word on -- say "Veda" from any page' : 'Wake word off'}
                  style={{
                    background: wakeEnabled ? '#14532D22' : 'transparent',
                    border: `1px solid ${wakeEnabled ? '#22C55E' : '#1E2332'}`,
                    borderRadius: 4, color: wakeEnabled ? '#4ADE80' : '#334155',
                    fontSize: 9, fontWeight: 700, padding: '2px 6px', cursor: 'pointer',
                  }}
                >{wakeEnabled ? 'WAKE ON' : 'WAKE OFF'}</button>
                <button
                  onClick={() => setFollowUpEnabled(!followUpEnabled)}
                  title={
                    !wakeEnabled ? 'Follow-up needs wake word enabled'
                    : followUpEnabled ? 'Hands-free follow-up on -- mic reopens after Veda replies, no need to say "Veda" again'
                    : 'Follow-up off -- say "Veda" for every question'
                  }
                  style={{
                    background: followUpEnabled && wakeEnabled ? '#1E3A5F' : 'transparent',
                    border: `1px solid ${followUpEnabled && wakeEnabled ? '#3B82F6' : '#1E2332'}`,
                    borderRadius: 4, color: followUpEnabled && wakeEnabled ? '#60A5FA' : '#334155',
                    fontSize: 9, fontWeight: 700, padding: '2px 6px', cursor: 'pointer',
                    opacity: wakeEnabled ? 1 : 0.5,
                  }}
                >{followUpEnabled ? 'FOLLOW-UP ON' : 'FOLLOW-UP OFF'}</button>
              </div>
              <button
                onClick={() => { setOpen(false); navigate('/chat') }}
                style={{ background: 'none', border: 'none', color: '#3B82F6', fontSize: 10, fontWeight: 600, cursor: 'pointer' }}
              >Full chat →</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
