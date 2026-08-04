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
import { MessageEvidence } from './MessageEvidence'
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

function DrawerBubble({ msg, previous }: { msg: Msg; previous?: Msg }) {
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
        {msg.attachments && msg.attachments.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
            {msg.attachments.map((attachment, index) => (
              <div
                key={`${attachment.storage_key ?? attachment.name}-${index}`}
                style={{
                  padding: '2px 7px',
                  borderRadius: 999,
                  border: `1px solid ${attachment.warning ? '#F59E0B44' : '#334155'}`,
                  background: '#0D1117',
                  color: attachment.warning ? '#FCD34D' : '#94A3B8',
                  fontSize: 9,
                  maxWidth: 220,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={attachment.warning || attachment.excerpt || attachment.name}
              >
                {attachment.name}
              </div>
            ))}
          </div>
        )}
        {!isUser && <MessageEvidence msg={msg} previous={previous} compact />}
      </div>
    </div>
  )
}

function DrawerPendingAttachments({
  attachments,
  onRemove,
}: {
  attachments?: Msg['attachments']
  onRemove: (storageKey?: string | null, name?: string) => void
}) {
  if (!attachments || attachments.length === 0) return null
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
      {attachments.map((attachment, index) => (
        <div
          key={`${attachment.storage_key ?? attachment.name}-${index}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '2px 7px',
            borderRadius: 999,
            border: `1px solid ${attachment.warning ? '#F59E0B44' : '#334155'}`,
            background: '#0D1117',
            color: attachment.warning ? '#FCD34D' : '#94A3B8',
            fontSize: 9,
            maxWidth: 260,
          }}
          title={attachment.warning || attachment.excerpt || attachment.name}
        >
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 190 }}>
            {attachment.name}
          </span>
          <button
            onClick={() => onRemove(attachment.storage_key, attachment.name)}
            style={{
              background: 'none',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              fontSize: 10,
              lineHeight: 1,
              padding: 0,
            }}
          >
            x
          </button>
        </div>
      ))}
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
  const researchMode    = useVedaStore(s => s.researchMode)
  const researchEnabled = useVedaStore(s => s.researchEnabled)
  const attachmentsEnabled = useVedaStore(s => s.attachmentsEnabled)
  const pendingAttachments = useVedaStore(s => s.pendingAttachments)
  const uploadingAttachment = useVedaStore(s => s.uploadingAttachment)
  const send            = useVedaStore(s => s.send)
  const startListening  = useVedaStore(s => s.startListening)
  const stopSpeaking    = useVedaStore(s => s.stopSpeaking)
  const setWakeEnabled  = useVedaStore(s => s.setWakeEnabled)
  const setFollowUpEnabled = useVedaStore(s => s.setFollowUpEnabled)
  const setVoiceLang    = useVedaStore(s => s.setVoiceLang)
  const setResearchMode = useVedaStore(s => s.setResearchMode)
  const uploadAttachment = useVedaStore(s => s.uploadAttachment)
  const removePendingAttachment = useVedaStore(s => s.removePendingAttachment)
  const refreshCapabilities = useVedaStore(s => s.refreshCapabilities)

  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const panelRef  = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  useEffect(() => {
    if (!open) return
    void refreshCapabilities()
  }, [open, refreshCapabilities])

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
    : loading ? (researchMode && researchEnabled ? 'Researching...' : 'Thinking...')
    : researchMode && researchEnabled ? 'Research mode is on'
    : wakeEnabled ? 'Say "Veda" or ask below' : 'Ask below'

  const submit = () => {
    const text = input.trim()
    if ((!text && pendingAttachments.length === 0) || loading) return
    setInput('')
    send(text, 'text')
  }

  const handleFileSelection = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    for (const file of Array.from(files)) {
      await uploadAttachment(file)
    }
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
            {messages.map((m, i) => <DrawerBubble key={i} msg={m} previous={i > 0 ? messages[i - 1] : undefined} />)}
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
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.md,.csv,.json,.png,.jpg,.jpeg,.webp,.gif,.bmp"
              style={{ display: 'none' }}
              onChange={async e => {
                await handleFileSelection(e.target.files)
                e.currentTarget.value = ''
              }}
            />
            {(pendingAttachments.length > 0 || uploadingAttachment) && (
              <>
                <DrawerPendingAttachments
                  attachments={pendingAttachments}
                  onRemove={removePendingAttachment}
                />
                {uploadingAttachment && (
                  <div style={{ fontSize: 10, color: '#60A5FA', marginBottom: 8 }}>
                    Uploading attachment...
                  </div>
                )}
              </>
            )}
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
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={!attachmentsEnabled || loading || uploadingAttachment}
                title={
                  attachmentsEnabled
                    ? 'Attach a PDF, text file, CSV, JSON, or image'
                    : 'Attachments are not enabled by the backend yet'
                }
                style={{
                  width: 34, height: 34, borderRadius: 8, flexShrink: 0,
                  border: `1px solid ${attachmentsEnabled ? '#1E2332' : '#2D3348'}`,
                  background: attachmentsEnabled ? '#0D1117' : 'transparent',
                  color: attachmentsEnabled ? '#94A3B8' : '#334155',
                  cursor: attachmentsEnabled && !loading && !uploadingAttachment ? 'pointer' : 'not-allowed',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14,
                }}
              >
                +
              </button>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') submit() }}
                placeholder={
                  listening
                    ? 'Listening...'
                    : researchMode && researchEnabled
                      ? 'Ask anything. Veda can check outside sources too.'
                      : attachmentsEnabled
                        ? 'Ask or attach a file...'
                        : 'Ask about markets, sectors, stocks...'
                }
                disabled={loading}
                style={{
                  flex: 1, background: '#0D1117', border: '1px solid #1E2332', borderRadius: 6,
                  color: '#E2E8F0', padding: '0 10px', fontSize: 12, outline: 'none',
                }}
              />
              <button
                onClick={submit}
                disabled={(!input.trim() && pendingAttachments.length === 0) || loading}
                style={{
                  padding: '0 14px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                  cursor: (input.trim() || pendingAttachments.length > 0) && !loading ? 'pointer' : 'not-allowed',
                  background: (input.trim() || pendingAttachments.length > 0) && !loading ? '#1E3A5F' : '#0D1117',
                  color: (input.trim() || pendingAttachments.length > 0) && !loading ? '#60A5FA' : '#334155',
                  border: `1px solid ${(input.trim() || pendingAttachments.length > 0) && !loading ? '#3B82F6' : '#1E2332'}`,
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
                <button
                  onClick={() => setResearchMode(!researchMode)}
                  disabled={!researchEnabled}
                  title={
                    researchEnabled
                      ? researchMode
                        ? 'Research mode on: Veda may check outside sources when local data is weak'
                        : 'Research mode off: Veda stays local-first unless a research query needs more'
                      : 'Research mode is not enabled by the backend yet'
                  }
                  style={{
                    background: researchMode && researchEnabled ? '#1E3A5F' : 'transparent',
                    border: `1px solid ${researchMode && researchEnabled ? '#3B82F6' : '#1E2332'}`,
                    borderRadius: 4, color: researchMode && researchEnabled ? '#60A5FA' : '#334155',
                    fontSize: 9, fontWeight: 700, padding: '2px 6px', cursor: researchEnabled ? 'pointer' : 'not-allowed',
                    opacity: researchEnabled ? 1 : 0.55,
                  }}
                >{researchMode ? 'RESEARCH ON' : 'RESEARCH OFF'}</button>
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
