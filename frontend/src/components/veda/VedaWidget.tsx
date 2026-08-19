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
import {
  approveKnowledgeDraft,
  approveRepoCapabilityDraft,
  createKnowledgeDraft,
  createRepoCapabilityDraft,
  discardKnowledgeDraft,
  type ChatKnowledgeDraft,
  type ChatRepoCapabilityDraft,
} from '../../api/client'
import { KnowledgeReviewPanel, type KnowledgeReviewPayload } from './KnowledgeReviewPanel'
import {
  RepoCapabilityReviewPanel,
  type RepoCapabilityApprovePayload,
  type RepoCapabilityScanPayload,
} from './RepoCapabilityReviewPanel'
import { MessageEvidence } from './MessageEvidence'
import { VedaOrb } from './VedaOrb'

// ─── Wake-word listener controller (mount once) ───────────────────────────────

export function VedaWakeController() {
  const wakeEnabled = useVedaStore(s => s.wakeEnabled)
  const listening   = useVedaStore(s => s.listening)
  const loading     = useVedaStore(s => s.loading)
  const voiceEnabled = useVedaStore(s => s.voiceEnabled)
  const voiceLang   = useVedaStore(s => s.voiceLang)
  const [retryTick, setRetryTick] = useState(0)

  useEffect(() => {
    startWakeListener(() => setRetryTick(n => n + 1))
    return () => stopWakeListener()
  }, [wakeEnabled, listening, loading, voiceLang, voiceEnabled, retryTick])

  return null
}

// ─── Compact message bubble (drawer only -- ChatPage has its own richer one) ──

function DrawerBubble({
  msg,
  previous,
  saveToKnowledgeEnabled,
  reviewLoading,
  onReviewSave,
}: {
  msg: Msg
  previous?: Msg
  saveToKnowledgeEnabled?: boolean
  reviewLoading?: boolean
  onReviewSave?: (msg: Msg, previous?: Msg) => void
}) {
  const isUser = msg.role === 'user'
  const canReviewSave = !isUser && saveToKnowledgeEnabled && previous?.role === 'user' && Boolean(msg.intent || msg.research) && !msg.knowledge
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
        {canReviewSave && (
          <div style={{ marginTop: 6 }}>
            <button
              onClick={() => onReviewSave?.(msg, previous)}
              disabled={reviewLoading}
              style={{
                background: reviewLoading ? 'transparent' : '#0D1117',
                border: '1px solid #334155',
                color: reviewLoading ? '#64748B' : '#94A3B8',
                borderRadius: 999,
                padding: '3px 7px',
                fontSize: 9,
                cursor: reviewLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {reviewLoading ? 'Preparing review...' : 'Review to save'}
            </button>
          </div>
        )}
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
  const researchRuntimeReady = useVedaStore(s => s.researchRuntimeReady)
  const attachmentsEnabled = useVedaStore(s => s.attachmentsEnabled)
  const saveToKnowledgeEnabled = useVedaStore(s => s.saveToKnowledgeEnabled)
  const mitRepoIntakeEnabled = useVedaStore(s => s.mitRepoIntakeEnabled)
  const mcpEnabled = useVedaStore(s => s.mcpEnabled)
  const voiceEnabled = useVedaStore(s => s.voiceEnabled)
  const mcpServerNames = useVedaStore(s => s.mcpServerNames)
  const attachmentAccept = useVedaStore(s => s.attachmentAccept)
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
  const markKnowledgeSaved = useVedaStore(s => s.markKnowledgeSaved)
  const refreshCapabilities = useVedaStore(s => s.refreshCapabilities)
  const backendSid = useVedaStore(s => s.backendSid)
  const canUseResearch = researchEnabled && researchRuntimeReady

  const [input, setInput] = useState('')
  const [reviewDraft, setReviewDraft] = useState<ChatKnowledgeDraft | null>(null)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewMessageTs, setReviewMessageTs] = useState<number | null>(null)
  const [reviewLoading, setReviewLoading] = useState(false)
  const [reviewSubmitting, setReviewSubmitting] = useState(false)
  const [reviewError, setReviewError] = useState<string | null>(null)
  const [repoDraft, setRepoDraft] = useState<ChatRepoCapabilityDraft | null>(null)
  const [repoReviewOpen, setRepoReviewOpen] = useState(false)
  const [repoLoading, setRepoLoading] = useState(false)
  const [repoSubmitting, setRepoSubmitting] = useState(false)
  const [repoError, setRepoError] = useState<string | null>(null)
  const [repoNotice, setRepoNotice] = useState<string | null>(null)
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
    : loading ? (researchMode && canUseResearch ? 'Researching...' : 'Thinking...')
    : researchMode && canUseResearch ? 'Research mode is on'
    : researchEnabled && !researchRuntimeReady ? 'Research is temporarily unavailable'
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

  const closeKnowledgeReview = (force = false) => {
    if (reviewSubmitting && !force) return
    setReviewOpen(false)
    setReviewDraft(null)
    setReviewMessageTs(null)
    setReviewLoading(false)
    setReviewError(null)
  }

  const openKnowledgeReview = async (answerMsg: Msg, previous?: Msg) => {
    if (!saveToKnowledgeEnabled || previous?.role !== 'user' || answerMsg.knowledge?.status === 'approved') return
    setReviewOpen(true)
    setReviewDraft(null)
    setReviewMessageTs(answerMsg.ts)
    setReviewLoading(true)
    setReviewError(null)
    try {
      const draft = await createKnowledgeDraft({
        question: previous.content,
        answer: answerMsg.content,
        intent: answerMsg.intent,
        session_id: backendSid,
        research: answerMsg.research,
        attachments: previous.attachments,
      })
      setReviewDraft(draft)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setReviewError(detail ?? 'Could not prepare the review draft.')
    } finally {
      setReviewLoading(false)
    }
  }

  const approveKnowledgeReview = async (payload: KnowledgeReviewPayload) => {
    if (!reviewDraft || reviewMessageTs == null) return
    setReviewSubmitting(true)
    setReviewError(null)
    try {
      const saved = await approveKnowledgeDraft(reviewDraft.draft_id, payload)
      markKnowledgeSaved(reviewMessageTs, saved)
      closeKnowledgeReview(true)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setReviewError(detail ?? 'Could not save this reviewed knowledge.')
    } finally {
      setReviewSubmitting(false)
    }
  }

  const discardKnowledgeReview = async (draftId: string) => {
    setReviewSubmitting(true)
    setReviewError(null)
    try {
      await discardKnowledgeDraft(draftId)
      closeKnowledgeReview(true)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setReviewError(detail ?? 'Could not discard this review draft.')
    } finally {
      setReviewSubmitting(false)
    }
  }

  const closeRepoReview = (force = false) => {
    if (repoSubmitting && !force) return
    setRepoReviewOpen(false)
    setRepoDraft(null)
    setRepoLoading(false)
    setRepoError(null)
  }

  const scanRepoCapability = async (payload: RepoCapabilityScanPayload) => {
    setRepoReviewOpen(true)
    setRepoDraft(null)
    setRepoLoading(true)
    setRepoError(null)
    setRepoNotice(null)
    try {
      const draft = await createRepoCapabilityDraft(payload)
      setRepoDraft(draft)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setRepoError(detail ?? 'Could not study this repo yet.')
    } finally {
      setRepoLoading(false)
    }
  }

  const approveRepoCapability = async (payload: RepoCapabilityApprovePayload) => {
    if (!repoDraft) return
    setRepoSubmitting(true)
    setRepoError(null)
    try {
      const saved = await approveRepoCapabilityDraft(repoDraft.draft_id, payload)
      setRepoNotice(saved.duplicate
        ? `This MIT repo note was already saved: ${saved.title}`
        : `MIT repo note saved for Veda: ${saved.title}`)
      closeRepoReview(true)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setRepoError(detail ?? 'Could not save this MIT repo note.')
    } finally {
      setRepoSubmitting(false)
    }
  }

  return (
    <div style={{ position: 'relative' }} ref={panelRef}>
      <button
        onClick={() => setOpen(!open)}
        title="Veda -- your conversational assistant"
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
              onClick={() => { setRepoReviewOpen(true); setRepoError(null); setRepoNotice(null) }}
              disabled={!mitRepoIntakeEnabled || loading}
              title={
                mitRepoIntakeEnabled
                  ? 'Study a local MIT repo and save approved capability notes'
                  : 'MIT repo study is not enabled by the backend yet'
              }
              style={{
                background: repoReviewOpen && mitRepoIntakeEnabled ? '#1F2937' : 'transparent',
                border: `1px solid ${repoReviewOpen && mitRepoIntakeEnabled ? '#60A5FA' : '#2D3348'}`,
                borderRadius: 4,
                color: repoReviewOpen && mitRepoIntakeEnabled ? '#BFDBFE' : '#64748B',
                fontSize: 9,
                padding: '3px 7px',
                cursor: mitRepoIntakeEnabled && !loading ? 'pointer' : 'not-allowed',
                opacity: mitRepoIntakeEnabled ? 1 : 0.55,
              }}
            >
              MIT Repo
            </button>
            <button
              onClick={() => setOpen(false)}
              style={{ background: 'none', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer', lineHeight: 1, padding: 0 }}
            >×</button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px', minHeight: 200 }}>
            {messages.map((m, i) => (
              <DrawerBubble
                key={i}
                msg={m}
                previous={i > 0 ? messages[i - 1] : undefined}
                saveToKnowledgeEnabled={saveToKnowledgeEnabled}
                reviewLoading={reviewLoading && reviewMessageTs === m.ts}
                onReviewSave={openKnowledgeReview}
              />
            ))}
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
          {repoNotice && (
            <div style={{ margin: '0 14px 8px', padding: '6px 10px', borderRadius: 4, background: '#0F1E30', border: '1px solid #1D4ED8', color: '#BFDBFE', fontSize: 10 }}>
              {repoNotice}
            </div>
          )}

          {/* Controls */}
          <div style={{ padding: '10px 14px', borderTop: '1px solid #1E2332', flexShrink: 0 }}>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={attachmentAccept}
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
                disabled={!voiceEnabled || loading}
                title={!voiceEnabled ? 'Voice is disabled by administrator configuration' : (listening ? 'Listening... click to stop' : 'Speak to Veda')}
                style={{
                  width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                  border: `2px solid ${listening ? '#EF4444' : '#3B82F6'}`,
                  background: listening ? '#EF444422' : '#0D1117',
                  color: listening ? '#EF4444' : '#60A5FA',
                  cursor: !voiceEnabled || loading ? 'not-allowed' : 'pointer',
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
                    : researchMode && canUseResearch
                      ? 'Ask anything. Veda can check outside sources too.'
                      : researchEnabled && !researchRuntimeReady
                        ? 'Research is temporarily unavailable right now.'
                      : attachmentsEnabled
                        ? 'Ask or attach a file...'
                        : 'Ask anything, or explore Veda capabilities...'
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
                  disabled={!canUseResearch}
                  title={
                    !researchEnabled
                      ? 'Research mode is not enabled by the backend yet'
                      : !researchRuntimeReady
                        ? 'Research mode is enabled, but no live research provider is available right now.'
                      : researchEnabled
                      ? researchMode
                        ? `Research mode on: Veda may check outside sources when local data is weak${mcpEnabled ? ` and can fall back to MCP (${mcpServerNames.join(', ') || 'configured servers'}) if needed` : ''}`
                        : `Research mode off: Veda stays local-first unless a research query needs more${mcpEnabled ? '. MCP fallback is ready if research is triggered.' : ''}`
                      : 'Research mode is not enabled by the backend yet'
                  }
                  style={{
                    background: researchMode && canUseResearch ? '#1E3A5F' : 'transparent',
                    border: `1px solid ${researchMode && canUseResearch ? '#3B82F6' : '#1E2332'}`,
                    borderRadius: 4, color: researchMode && canUseResearch ? '#60A5FA' : researchEnabled && !researchRuntimeReady ? '#F59E0B' : '#334155',
                    fontSize: 9, fontWeight: 700, padding: '2px 6px', cursor: canUseResearch ? 'pointer' : 'not-allowed',
                    opacity: canUseResearch ? 1 : 0.65,
                  }}
                >{!researchEnabled
                  ? 'RESEARCH OFF'
                  : !researchRuntimeReady
                    ? 'RESEARCH UNAVAILABLE'
                    : researchMode
                      ? 'RESEARCH ON'
                      : 'RESEARCH OFF'}</button>
              </div>
              <button
                onClick={() => { setOpen(false); navigate('/chat') }}
                style={{ background: 'none', border: 'none', color: '#3B82F6', fontSize: 10, fontWeight: 600, cursor: 'pointer' }}
              >Full chat -&gt;</button>
            </div>
          </div>
        </div>
      )}
      <KnowledgeReviewPanel
        open={reviewOpen}
        draft={reviewDraft}
        loading={reviewLoading}
        submitting={reviewSubmitting}
        error={reviewError}
        onClose={closeKnowledgeReview}
        onApprove={approveKnowledgeReview}
        onDiscard={discardKnowledgeReview}
      />
      <RepoCapabilityReviewPanel
        open={repoReviewOpen}
        draft={repoDraft}
        loading={repoLoading}
        submitting={repoSubmitting}
        error={repoError}
        onClose={closeRepoReview}
        onScan={scanRepoCapability}
        onApprove={approveRepoCapability}
      />
    </div>
  )
}
