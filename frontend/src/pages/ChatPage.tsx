/**
 * ChatPage — Phase D
 * Full AI chat UI backed by Phase 14 Claude API chatbot (RAG + tool use).
 * POST /api/chat  →  reply + session_id + intent
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { sendChat, resetChatSession, type ChatResponseData } from '../api/client'

// ─── Types ───────────────────────────────────────────────────────────────────

type Role = 'user' | 'assistant' | 'system'
interface Msg { role: Role; content: string; intent?: string; ts: number }

// ─── Constants ───────────────────────────────────────────────────────────────

const INTENT_META: Record<string, { label: string; color: string }> = {
  MARKET:    { label: 'MARKET',    color: '#22C55E' },
  SECTOR:    { label: 'SECTOR',    color: '#3B82F6' },
  STOCK:     { label: 'STOCK',     color: '#8B5CF6' },
  CORPORATE: { label: 'CORPORATE', color: '#F59E0B' },
  RESEARCH:  { label: 'RESEARCH',  color: '#64748B' },
}

const SUGGESTED = [
  'Which sectors are in early rotation right now?',
  'What is the FII vs DII divergence signal today?',
  'Show me top STRONG_CANDIDATE stocks in BANKING',
  'Explain the PCR signal and what it means',
  'What is the conviction score for RELIANCE?',
  'Which F&O stocks have long buildup today?',
]

const WELCOME: Msg = {
  role: 'assistant',
  content: `Hello! I'm your AI market intelligence assistant — powered by Claude with access to real-time institutional flow data, sector rotation signals, F&O intelligence, and company fundamentals across 2,400+ NSE stocks.\n\nAsk me anything about markets, sectors, stocks, or flows.`,
  ts: Date.now(),
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function IntentBadge({ intent }: { intent?: string }) {
  if (!intent || intent === 'RESEARCH') return null
  const m = INTENT_META[intent] ?? INTENT_META.RESEARCH
  return (
    <span style={{
      fontSize: 8, fontWeight: 700, letterSpacing: 1,
      padding: '1px 6px', borderRadius: 2,
      border: `1px solid ${m.color}55`,
      color: m.color, background: `${m.color}18`,
      marginBottom: 4, display: 'inline-block',
    }}>
      {m.label}
    </span>
  )
}

function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '6px 0' }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: 6, height: 6, borderRadius: '50%', background: '#3B82F6',
          animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
      <style>{`@keyframes pulse { 0%,80%,100%{opacity:.2;transform:scale(.8)} 40%{opacity:1;transform:scale(1)} }`}</style>
    </div>
  )
}

function MessageBubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === 'user'
  const isSystem = msg.role === 'system'

  if (isSystem) {
    return (
      <div style={{ textAlign: 'center', padding: '6px 0' }}>
        <span style={{ color: '#334155', fontSize: 10 }}>{msg.content}</span>
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 12,
    }}>
      {!isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: '50%', background: '#1E2332',
          border: '1px solid #3B82F644', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: 12, marginRight: 8, flexShrink: 0, marginTop: 2,
        }}>
          AI
        </div>
      )}
      <div style={{ maxWidth: '75%' }}>
        {!isUser && <IntentBadge intent={msg.intent} />}
        <div style={{
          padding: '10px 14px',
          borderRadius: isUser ? '12px 12px 2px 12px' : '2px 12px 12px 12px',
          background: isUser ? '#1E3A5F' : '#141720',
          border: `1px solid ${isUser ? '#1E4A8F' : '#1E2332'}`,
          color: '#E2E8F0', fontSize: 13, lineHeight: 1.65,
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        }}>
          {msg.content}
        </div>
        <div style={{ fontSize: 9, color: '#334155', marginTop: 3, textAlign: isUser ? 'right' : 'left' }}>
          {new Date(msg.ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function ChatPage() {
  const [messages, setMessages]     = useState<Msg[]>([WELCOME])
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [sessionId, setSessionId]   = useState<string | undefined>(undefined)
  const [apiError, setApiError]     = useState<string | null>(null)
  const bottomRef                   = useRef<HTMLDivElement>(null)
  const inputRef                    = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Auto-resize textarea
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }, [input])

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userMsg: Msg = { role: 'user', content: trimmed, ts: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setApiError(null)

    try {
      const data: ChatResponseData = await sendChat(trimmed, sessionId)
      setSessionId(data.session_id)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply,
        intent: data.intent,
        ts: Date.now(),
      }])
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      const errText = detail ?? 'Connection error. Check that the backend is running.'
      setApiError(errText)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I couldn't process that request. ${errText}`,
        ts: Date.now(),
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [loading, sessionId])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send(input)
    }
  }

  const handleNewChat = async () => {
    if (sessionId) {
      try { await resetChatSession(sessionId) } catch { /* ignore */ }
    }
    setSessionId(undefined)
    setMessages([WELCOME])
    setInput('')
    setApiError(null)
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const isFirstTurn = messages.length === 1  // only welcome message

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)',
      maxWidth: 820, margin: '0 auto',
    }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        paddingBottom: 12, borderBottom: '1px solid #1E2332', marginBottom: 16,
        flexShrink: 0,
      }}>
        <div>
          <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, margin: 0 }}>
            AI MARKET INTELLIGENCE
          </h1>
          <div style={{ color: '#475569', fontSize: 10, marginTop: 3 }}>
            Claude API + RAG (6 domain indexes) + 11 live data tools &nbsp;|&nbsp; Phase 14
            {sessionId && <span style={{ color: '#334155' }}> &nbsp;|&nbsp; Session: {sessionId}</span>}
          </div>
        </div>
        <button
          onClick={handleNewChat}
          style={{
            padding: '5px 14px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
            background: 'transparent', color: '#64748B',
            border: '1px solid #1E2332',
          }}
        >
          New Chat
        </button>
      </div>

      {/* ── Capability chips ───────────────────────────────────────────────── */}
      {isFirstTurn && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16, flexShrink: 0 }}>
          {Object.entries(INTENT_META).map(([k, v]) => (
            <span key={k} style={{
              fontSize: 9, padding: '2px 8px', borderRadius: 10,
              border: `1px solid ${v.color}44`, color: v.color, background: `${v.color}12`,
              fontWeight: 600, letterSpacing: 0.5,
            }}>
              {v.label}
            </span>
          ))}
          <span style={{ fontSize: 9, color: '#334155', alignSelf: 'center', marginLeft: 4 }}>
            Ask about any of these domains
          </span>
        </div>
      )}

      {/* ── Message thread ─────────────────────────────────────────────────── */}
      <div style={{
        flex: 1, overflowY: 'auto', paddingRight: 4,
        scrollbarWidth: 'thin', scrollbarColor: '#1E2332 transparent',
      }}>
        {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: 12 }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', background: '#1E2332',
              border: '1px solid #3B82F644', display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 12, marginRight: 8, flexShrink: 0,
            }}>AI</div>
            <div style={{
              padding: '10px 14px', borderRadius: '2px 12px 12px 12px',
              background: '#141720', border: '1px solid #1E2332',
            }}>
              <TypingDots />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Suggested prompts (first turn only) ───────────────────────────── */}
      {isFirstTurn && !loading && (
        <div style={{ marginTop: 12, marginBottom: 10, flexShrink: 0 }}>
          <div style={{ color: '#334155', fontSize: 9, letterSpacing: 1, marginBottom: 8 }}>
            TRY ASKING
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {SUGGESTED.map(q => (
              <button
                key={q}
                onClick={() => send(q)}
                style={{
                  padding: '5px 10px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                  background: '#0D1117', color: '#94A3B8',
                  border: '1px solid #1E2332', textAlign: 'left',
                  transition: 'border-color 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = '#3B82F6')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = '#1E2332')}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── API error banner ───────────────────────────────────────────────── */}
      {apiError && (apiError.includes('GROQ_API_KEY') || apiError.includes('not configured')) && (
        <div style={{
          padding: '8px 14px', borderRadius: 4, marginBottom: 8, flexShrink: 0,
          background: '#1c0000', border: '1px solid #EF444444', color: '#EF4444', fontSize: 11,
        }}>
          GROQ_API_KEY is not set in .env — get a free key at console.groq.com then restart the backend.
        </div>
      )}

      {/* ── Input bar ──────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', gap: 10, alignItems: 'flex-end',
        borderTop: '1px solid #1E2332', paddingTop: 12, flexShrink: 0,
      }}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about markets, sectors, stocks, flows… (Enter to send, Shift+Enter for new line)"
          rows={1}
          style={{
            flex: 1, resize: 'none', overflow: 'hidden',
            background: '#0D1117', border: '1px solid #1E2332', borderRadius: 6,
            color: '#E2E8F0', padding: '10px 14px', fontSize: 13,
            outline: 'none', fontFamily: 'inherit', lineHeight: 1.5,
            transition: 'border-color 0.15s',
          }}
          onFocus={e => (e.currentTarget.style.borderColor = '#3B82F6')}
          onBlur={e  => (e.currentTarget.style.borderColor = '#1E2332')}
          disabled={loading}
        />
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          style={{
            padding: '10px 18px', borderRadius: 6, fontSize: 12, fontWeight: 700,
            cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
            background: input.trim() && !loading ? '#1E3A5F' : '#0D1117',
            color: input.trim() && !loading ? '#60A5FA' : '#334155',
            border: `1px solid ${input.trim() && !loading ? '#3B82F6' : '#1E2332'}`,
            transition: 'all 0.15s', whiteSpace: 'nowrap', flexShrink: 0,
          }}
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>

      <div style={{ fontSize: 9, color: '#1E2332', textAlign: 'center', marginTop: 6, flexShrink: 0 }}>
        AI responses are for informational purposes only — not financial advice
      </div>
    </div>
  )
}
