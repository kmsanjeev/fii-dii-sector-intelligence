/**
 * ChatPage — Phase D v2
 * Full AI chat UI with persistent history, slash-command palette, and sidebar.
 * POST /api/chat  ->  reply + session_id + intent
 * Persistence: localStorage key "mci_chat_sessions" (up to 60 sessions)
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { sendChat, resetChatSession, type ChatResponseData } from '../api/client'

// ─── Types ────────────────────────────────────────────────────────────────────

type Role = 'user' | 'assistant' | 'system'
interface Msg { role: Role; content: string; intent?: string; ts: number }

interface SavedSession {
  id: string
  title: string
  messages: Msg[]
  backendSessionId?: string
  createdAt: number
  updatedAt: number
}

// ─── Constants ────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'mci_chat_sessions'
const MAX_SESSIONS = 60

const INTENT_META: Record<string, { label: string; color: string }> = {
  MARKET:    { label: 'MARKET',    color: '#22C55E' },
  SECTOR:    { label: 'SECTOR',    color: '#3B82F6' },
  STOCK:     { label: 'STOCK',     color: '#8B5CF6' },
  CORPORATE: { label: 'CORPORATE', color: '#F59E0B' },
  RESEARCH:  { label: 'RESEARCH',  color: '#64748B' },
  KUNDLI:    { label: 'KUNDLI',    color: '#E879F9' },
  ASTRO:     { label: 'ASTRO',     color: '#FB923C' },
}

function makeWelcome(): Msg {
  return {
    role: 'assistant',
    content: "Hello! I'm your market intelligence chatbot — Ask me anything about markets, sectors, stocks, or flows.",
    ts: Date.now(),
  }
}

// ─── Slash Commands ───────────────────────────────────────────────────────────

interface SlashCmd { label: string; query: string }
interface SlashCat { key: string; icon: string; category: string; cmds: SlashCmd[] }

const SLASH: SlashCat[] = [
  {
    key: 'market', icon: 'M', category: 'Market Overview',
    cmds: [
      { label: 'FII vs DII divergence today',   query: 'What is the FII vs DII divergence signal today?' },
      { label: 'Current market regime',          query: 'What is the current market regime and its implications?' },
      { label: 'Smart money flow direction',     query: 'Where is smart money flowing right now?' },
      { label: 'PCR signal & interpretation',    query: 'Explain the current Put Call Ratio signal and market implications.' },
      { label: 'Overall institutional sentiment',query: 'What is the overall institutional market sentiment today?' },
    ],
  },
  {
    key: 'gainers', icon: '+', category: 'Top Gainers',
    cmds: [
      { label: 'Top gaining stocks',       query: 'Show me top gaining stocks with high momentum scores.' },
      { label: 'Top gaining sectors',      query: 'Which sectors have the highest gains and rotation score?' },
      { label: 'FII-driven gainers',       query: 'Which stocks are gaining with FII accumulation support?' },
      { label: 'Breakout conviction stocks', query: 'Show stocks breaking out with high conviction scores.' },
    ],
  },
  {
    key: 'losers', icon: '-', category: 'Top Losers',
    cmds: [
      { label: 'Top declining stocks',    query: 'Show me stocks with the largest recent price decline.' },
      { label: 'FII distribution stocks', query: 'Which stocks show FII distribution (selling) patterns?' },
      { label: 'Weakest sectors',         query: 'Which sectors are lagging or seeing outflows?' },
      { label: 'MARKDOWN / Bear phase',   query: 'Show stocks in MARKDOWN or confirmed bear phase status.' },
    ],
  },
  {
    key: '52h', icon: '^', category: '52-Week High',
    cmds: [
      { label: 'Near 52W high (within 5%)',  query: 'Which stocks are within 5% of their 52-week high?' },
      { label: 'Fresh 52W high breakouts',   query: 'Show stocks that just made a new 52-week high.' },
      { label: 'Strong above 200 DMA',       query: 'Show stocks trading well above their 200-day moving average.' },
    ],
  },
  {
    key: '52l', icon: 'v', category: '52-Week Low',
    cmds: [
      { label: 'Near 52W low (reversal watch)', query: 'Which stocks near 52-week low could be reversal candidates?' },
      { label: 'Bouncing from lows',            query: 'Show stocks bouncing from 52-week lows with increasing volume.' },
      { label: 'Below 200 DMA',                 query: 'Which stocks are significantly below their 200-day moving average?' },
    ],
  },
  {
    key: 'bullrun', icon: 'B', category: 'Bull Run / Emerging',
    cmds: [
      { label: 'BULL_RUN status stocks',        query: 'Show me all stocks currently in BULL_RUN status.' },
      { label: 'EMERGING stocks',               query: 'Show EMERGING stocks with high accumulation and ML scores.' },
      { label: 'Highest conviction scores',     query: 'Which stocks have the highest trade conviction scores right now?' },
      { label: 'FII accumulation + bull run',   query: 'Show stocks with both FII accumulation and BULL_RUN label.' },
    ],
  },
  {
    key: 'bear', icon: 'D', category: 'Bear Phase',
    cmds: [
      { label: 'Bear phase confirmed stocks',   query: 'Which stocks are in confirmed bear phase or downtrend?' },
      { label: 'FII selling pressure',          query: 'Show stocks under sustained FII selling pressure.' },
      { label: 'Avoid list — weak technicals',  query: 'Which stocks should be avoided due to weak technicals and outflows?' },
    ],
  },
  {
    key: 'fundamentals', icon: 'F', category: 'Fundamentals',
    cmds: [
      { label: 'Best ROE stocks (>20%)',       query: 'Which stocks have Return on Equity above 20%?' },
      { label: 'Low P/E value plays',          query: 'Show undervalued stocks with P/E below sector average.' },
      { label: 'High operating margin (OPM%)', query: 'Which stocks have the highest operating profit margin?' },
      { label: 'Revenue growth CAGR leaders',  query: 'Show stocks with the strongest 3-year revenue growth CAGR.' },
      { label: 'ROCE champions',               query: 'Which stocks have the highest Return on Capital Employed?' },
      { label: 'Near book value',              query: 'Show stocks trading near or below book value.' },
    ],
  },
  {
    key: 'sectors', icon: 'S', category: 'Sector Rotation',
    cmds: [
      { label: 'Early rotation sectors',       query: 'Which sectors are in early rotation with FII entry signals?' },
      { label: 'Rank all sectors by score',    query: 'Rank all sectors by combined flow score today.' },
      { label: 'Strongest FII sector inflows', query: 'Which sectors are seeing the strongest FII inflows?' },
      { label: 'Rotation signal — what to buy',query: 'What is the current rotation signal and which sector to enter?' },
    ],
  },
  {
    key: 'fno', icon: 'O', category: 'F&O Intelligence',
    cmds: [
      { label: 'Long buildup stocks',           query: 'Which F&O stocks show long buildup — rising OI with rising price?' },
      { label: 'Short covering candidates',     query: 'Show F&O stocks showing short covering pattern.' },
      { label: 'Short buildup (bearish signal)', query: 'Which stocks show short buildup — bearish signal?' },
      { label: 'Highest OI change today',       query: 'Show stocks with the highest open interest change today.' },
      { label: 'Put Call Ratio deep dive',      query: 'What is the current PCR and how to interpret it for market direction?' },
    ],
  },
  {
    key: 'institutional', icon: 'I', category: 'Institutional Activity',
    cmds: [
      { label: 'Recent block & bulk deals',     query: 'Show recent large block and bulk deals by institutions.' },
      { label: 'FII consistent buying',         query: 'Which stocks has FII been consistently buying recently?' },
      { label: 'DII net buyers',                query: 'Show stocks where DII is a strong net buyer recently.' },
      { label: 'Promoter stake increase',       query: 'Which companies have seen promoter stake increase recently?' },
    ],
  },
  {
    key: 'kundli', icon: 'K', category: 'Personal Kundli',
    cmds: [
      { label: 'Generate my Kundli',           query: 'Generate my personal Kundli — DOB: DD-MM-YYYY, Time: HH:MM, Place: City' },
      { label: 'Current Dasha reading',         query: 'What is my current Dasha period and what does it mean for my life?' },
      { label: 'Career & wealth reading',       query: 'Give me a detailed career and wealth reading from my birth chart.' },
      { label: 'Love & marriage reading',       query: 'Read my love life and marriage prospects from my natal chart.' },
    ],
  },
]

// ─── Storage helpers ──────────────────────────────────────────────────────────

function genId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function makeTitle(msgs: Msg[]): string {
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

function exportSession(s: SavedSession): void {
  const blob = new Blob([JSON.stringify(s, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `chat_${s.title.slice(0, 24).replace(/\W+/g, '_')}_${new Date(s.createdAt).toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function printSession(s: SavedSession): void {
  const win = window.open('', '_blank')
  if (!win) return
  const rows = s.messages
    .filter(m => m.role !== 'system')
    .map(m => `<div style="margin-bottom:14px">
      <div style="font-size:10px;color:#666;margin-bottom:4px">${m.role.toUpperCase()} &nbsp; ${new Date(m.ts).toLocaleString('en-IN')}</div>
      <pre style="white-space:pre-wrap;font-size:12px;margin:0;padding:10px;background:${m.role === 'user' ? '#e8f0fe' : '#f5f5f5'};border-radius:4px;font-family:Arial,sans-serif">${m.content.replace(/</g, '&lt;')}</pre>
    </div><hr style="border:1px solid #eee;margin:14px 0">`).join('')
  win.document.write(`<!DOCTYPE html><html><head><title>${s.title}</title>
    <style>body{font-family:Arial,sans-serif;padding:28px;max-width:780px;margin:0 auto;font-size:13px}</style>
    </head><body>
    <h2 style="font-size:15px;margin-bottom:4px;font-weight:700">${s.title}</h2>
    <div style="font-size:10px;color:#888;margin-bottom:20px">${new Date(s.createdAt).toLocaleString('en-IN')} &nbsp;|&nbsp; ${s.messages.filter(m => m.role === 'user').length} questions</div>
    <hr style="border:1px solid #ccc;margin-bottom:20px">${rows}</body></html>`)
  win.document.close()
  setTimeout(() => win.print(), 300)
}

// ─── Slash Command Palette ────────────────────────────────────────────────────

function SlashPalette({ filter, onSelect, onClose }: {
  filter: string
  onSelect: (q: string) => void
  onClose: () => void
}) {
  const [hov, setHov] = useState('')
  const q = filter.trim().toLowerCase()

  const flat = SLASH.flatMap(cat =>
    cat.cmds.map(c => ({ ...c, cat: cat.category, icon: cat.icon, key: cat.key }))
  )
  const filtered = q ? flat.filter(c =>
    c.label.toLowerCase().includes(q) || c.cat.toLowerCase().includes(q)
  ) : null

  return (
    <div style={{
      position: 'absolute', bottom: '100%', left: 0, right: 0, marginBottom: 6, zIndex: 200,
      background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 8,
      maxHeight: 360, overflowY: 'auto', boxShadow: '0 -8px 40px rgba(0,0,0,0.7)',
    }}>
      <div style={{
        padding: '7px 12px', borderBottom: '1px solid #1E2332',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        position: 'sticky', top: 0, background: '#0A0D14', zIndex: 1,
      }}>
        <span style={{ fontSize: 9, color: '#475569', letterSpacing: 1 }}>
          QUICK QUESTIONS &nbsp;·&nbsp; type to filter
        </span>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#475569', cursor: 'pointer', fontSize: 14, lineHeight: 1, padding: '0 2px' }}>
          ×
        </button>
      </div>

      {filtered !== null ? (
        filtered.length === 0
          ? <div style={{ padding: '16px', color: '#475569', fontSize: 12, textAlign: 'center' }}>No results for "{filter}"</div>
          : filtered.map(c => {
              const key = c.key + c.label
              return (
                <div key={key}
                  onClick={() => onSelect(c.query)}
                  onMouseEnter={() => setHov(key)}
                  onMouseLeave={() => setHov('')}
                  style={{
                    padding: '7px 16px', cursor: 'pointer', fontSize: 12,
                    background: hov === key ? '#1E2332' : 'transparent',
                    color: hov === key ? '#E2E8F0' : '#94A3B8',
                    display: 'flex', alignItems: 'baseline', gap: 10,
                  }}>
                  <span style={{ fontSize: 9, color: '#475569', flexShrink: 0 }}>{c.icon} {c.cat}</span>
                  <span>{c.label}</span>
                </div>
              )
            })
      ) : (
        SLASH.map(cat => (
          <div key={cat.key}>
            <div style={{ padding: '8px 12px 3px', fontSize: 9, color: '#3B82F6', letterSpacing: 1, fontWeight: 700 }}>
              {cat.icon} &nbsp;{cat.category.toUpperCase()}
            </div>
            {cat.cmds.map(cmd => {
              const key = cat.key + cmd.label
              return (
                <div key={key}
                  onClick={() => onSelect(cmd.query)}
                  onMouseEnter={() => setHov(key)}
                  onMouseLeave={() => setHov('')}
                  style={{
                    padding: '5px 20px 5px 28px', cursor: 'pointer', fontSize: 12,
                    background: hov === key ? '#1E2332' : 'transparent',
                    color: hov === key ? '#E2E8F0' : '#94A3B8',
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}>
                  <span style={{ opacity: 0.3, fontSize: 9, flexShrink: 0 }}>&gt;</span>
                  {cmd.label}
                </div>
              )
            })}
          </div>
        ))
      )}
    </div>
  )
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

function Sidebar({
  sessions, currentId, onSelect, onNew, onDelete, onExport, onImport, onPrint, hasChat,
}: {
  sessions: SavedSession[]
  currentId: string
  onSelect: (s: SavedSession) => void
  onNew: () => void
  onDelete: (id: string) => void
  onExport: () => void
  onImport: (f: File) => void
  onPrint: () => void
  hasChat: boolean
}) {
  const [hov, setHov] = useState('')
  const importRef = useRef<HTMLInputElement>(null)
  const SBTN = {
    base: {
      padding: '6px 10px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
      background: 'transparent', border: '1px solid #1E2332', textAlign: 'left' as const,
      display: 'flex', alignItems: 'center', gap: 7, width: '100%',
    },
    active: { color: '#64748B' },
    disabled: { color: '#334155', cursor: 'not-allowed' as const },
  }

  return (
    <div style={{
      width: 252, flexShrink: 0, borderRight: '1px solid #1E2332',
      display: 'flex', flexDirection: 'column', background: '#06080F', overflowY: 'hidden',
    }}>
      {/* New Chat */}
      <div style={{ padding: '12px 12px 8px', flexShrink: 0 }}>
        <button onClick={onNew} style={{
          width: '100%', padding: '9px 14px', borderRadius: 6,
          background: '#1E3A5F', border: '1px solid #2563EB55',
          color: '#93C5FD', fontSize: 12, cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600,
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
          New Chat
        </button>
      </div>

      <div style={{ padding: '4px 12px 6px' }}>
        <span style={{ fontSize: 9, color: '#334155', letterSpacing: 1 }}>SAVED CHATS</span>
      </div>

      {/* Sessions list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px', scrollbarWidth: 'thin', scrollbarColor: '#1E2332 transparent' }}>
        {sessions.length === 0 && (
          <div style={{ color: '#334155', fontSize: 11, padding: '20px 8px', textAlign: 'center' }}>
            No saved chats yet.<br />
            <span style={{ fontSize: 10, opacity: 0.7 }}>Chats auto-save after<br />your first message.</span>
          </div>
        )}
        {sessions.map(s => (
          <div key={s.id}
            onClick={() => onSelect(s)}
            onMouseEnter={() => setHov(s.id)}
            onMouseLeave={() => setHov('')}
            style={{
              padding: '8px 10px', borderRadius: 6, cursor: 'pointer', marginBottom: 2,
              background: s.id === currentId ? '#131A2E' : hov === s.id ? '#0D1117' : 'transparent',
              border: `1px solid ${s.id === currentId ? '#1E4A8F' : 'transparent'}`,
              display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 6,
              transition: 'background 0.1s',
            }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 11, lineHeight: 1.4,
                color: s.id === currentId ? '#BFDBFE' : '#94A3B8',
                fontWeight: s.id === currentId ? 600 : 400,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>{s.title}</div>
              <div style={{ fontSize: 9, color: '#334155', marginTop: 2 }}>
                {new Date(s.updatedAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                &nbsp;·&nbsp;{s.messages.filter(m => m.role === 'user').length}Q
              </div>
            </div>
            {hov === s.id && (
              <button
                onClick={e => { e.stopPropagation(); onDelete(s.id) }}
                title="Delete chat"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#EF4444', padding: '2px', borderRadius: 3, flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6M14 11v6" /><path d="M9 6V4h6v2" />
                </svg>
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Bottom actions */}
      <div style={{ padding: '8px 12px 14px', borderTop: '1px solid #1E2332', display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0 }}>
        <button onClick={onExport} disabled={!hasChat} style={{ ...SBTN.base, ...(hasChat ? SBTN.active : SBTN.disabled) }}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
          Export current chat
        </button>
        <button onClick={() => importRef.current?.click()} style={{ ...SBTN.base, ...SBTN.active }}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
          Import chat
        </button>
        <button onClick={onPrint} disabled={!hasChat} style={{ ...SBTN.base, ...(hasChat ? SBTN.active : SBTN.disabled) }}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9" /><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" /><rect x="6" y="14" width="12" height="8" /></svg>
          Print chat
        </button>
        <input ref={importRef} type="file" accept=".json" style={{ display: 'none' }}
          onChange={e => { const f = e.target.files?.[0]; if (f) onImport(f); e.target.value = '' }} />
      </div>
    </div>
  )
}

// ─── Message components ───────────────────────────────────────────────────────

function IntentBadge({ intent }: { intent?: string }) {
  if (!intent || intent === 'RESEARCH') return null
  const m = INTENT_META[intent]
  if (!m) return null
  return (
    <span style={{
      fontSize: 8, fontWeight: 700, letterSpacing: 1,
      padding: '1px 6px', borderRadius: 2,
      border: `1px solid ${m.color}55`, color: m.color, background: `${m.color}18`,
      marginBottom: 4, display: 'inline-block',
    }}>{m.label}</span>
  )
}

function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '6px 0' }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: '#3B82F6', animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }} />
      ))}
      <style>{`@keyframes pulse{0%,80%,100%{opacity:.2;transform:scale(.8)}40%{opacity:1;transform:scale(1)}}`}</style>
    </div>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500) })}
      title={copied ? 'Copied!' : 'Copy'}
      style={{
        background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px',
        borderRadius: 3, display: 'inline-flex', alignItems: 'center', gap: 3,
        color: copied ? '#22C55E' : '#475569', fontSize: 9, verticalAlign: 'middle', transition: 'color 0.2s',
      }}>
      {copied
        ? <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
        : <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></svg>
      }
      {copied ? 'Copied!' : ''}
    </button>
  )
}

function MessageBubble({ msg }: { msg: Msg }) {
  const isUser   = msg.role === 'user'
  const isSystem = msg.role === 'system'
  if (isSystem) return (
    <div style={{ textAlign: 'center', padding: '6px 0' }}>
      <span style={{ color: '#334155', fontSize: 10 }}>{msg.content}</span>
    </div>
  )
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 14 }}>
      {!isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: '50%', background: '#1E2332',
          border: '1px solid #3B82F644', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: 11, marginRight: 8, flexShrink: 0, marginTop: 2, color: '#60A5FA',
        }}>AI</div>
      )}
      <div style={{ maxWidth: '78%' }}>
        {!isUser && <IntentBadge intent={msg.intent} />}
        <div style={{
          padding: '10px 14px',
          borderRadius: isUser ? '12px 12px 2px 12px' : '2px 12px 12px 12px',
          background: isUser ? '#1E3A5F' : '#141720',
          border: `1px solid ${isUser ? '#1E4A8F' : '#1E2332'}`,
          color: '#E2E8F0', fontSize: 13, lineHeight: 1.65,
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        }}>{msg.content}</div>
        <div style={{ fontSize: 9, color: '#334155', marginTop: 3, display: 'flex', alignItems: 'center', justifyContent: isUser ? 'flex-end' : 'flex-start', gap: 6 }}>
          {new Date(msg.ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          <CopyButton text={msg.content} />
        </div>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

// ── Voice support (Phase V1: Veda) ────────────────────────────────────────────

const VOICE_LANGS = [
  { code: 'hi', sttLang: 'hi-IN', label: 'Hindi (Swara)' },
  { code: 'en', sttLang: 'en-IN', label: 'English (Neerja)' },
  { code: 'ta', sttLang: 'ta-IN', label: 'Tamil (Pallavi)' },
  { code: 'te', sttLang: 'te-IN', label: 'Telugu (Shruti)' },
  { code: 'bn', sttLang: 'bn-IN', label: 'Bengali (Tanishaa)' },
]
const VOICE_LANG_KEY = 'cfip-voice-lang'
const WAKE_KEY       = 'cfip-wake'

function loadVoiceLang(): string {
  try { return localStorage.getItem(VOICE_LANG_KEY) || 'hi' } catch { return 'hi' }
}
function loadWakeEnabled(): boolean {
  try { return localStorage.getItem(WAKE_KEY) !== 'off' } catch { return true }
}

// Wake words + common mis-hearings; Hindi STT returns Devanagari script
const WAKE_WORDS = [
  'veda', 'adya', 'vedha', 'aadya', 'vida', 'vader', 'adia',
  'वेदा', 'वेधा', 'आद्या', 'अद्या', 'वेद',
]

const GREETINGS: Record<string, string> = {
  hi: 'जी, बोलिए। मैं सुन रही हूँ।',
  en: 'Yes, I am listening. How can I help?',
}

type SpeechRecognitionLike = {
  lang: string; continuous: boolean; interimResults: boolean
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null
  onend: (() => void) | null
  onerror: ((e: { error: string }) => void) | null
  start: () => void; stop: () => void; abort: () => void
}

function getSpeechRecognition(): SpeechRecognitionLike | null {
  const w = window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike; webkitSpeechRecognition?: new () => SpeechRecognitionLike }
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition
  return Ctor ? new Ctor() : null
}

export function ChatPage() {
  // Session state
  const [sessions,   setSessions]   = useState<SavedSession[]>(() => loadSessions())
  const [currentId,  setCurrentId]  = useState<string>(() => genId())
  const [messages,   setMessages]   = useState<Msg[]>(() => [makeWelcome()])
  const [backendSid, setBackendSid] = useState<string | undefined>(undefined)

  // UI state
  const [input,      setInput]      = useState('')
  const [loading,    setLoading]    = useState(false)
  const [apiError,   setApiError]   = useState<string | null>(null)
  const [showSlash,  setShowSlash]  = useState(false)
  const [slashFilter,setSlashFilter]= useState('')

  // Voice state (Phase V1 + V2)
  const [voiceLang,    setVoiceLang]    = useState<string>(() => loadVoiceLang())
  const [speakReplies, setSpeakReplies] = useState(true)
  const [listening,    setListening]    = useState(false)
  const [speaking,     setSpeaking]     = useState(false)
  const [wakeEnabled,  setWakeEnabled]  = useState<boolean>(() => loadWakeEnabled())
  const [wakeRetry,    setWakeRetry]    = useState(0)     // bumps to restart the wake listener

  const bottomRef  = useRef<HTMLDivElement>(null)
  const inputRef   = useRef<HTMLTextAreaElement>(null)
  const recogRef   = useRef<SpeechRecognitionLike | null>(null)
  const audioRef   = useRef<HTMLAudioElement | null>(null)
  const voiceChatsRef = useRef<Set<string>>(new Set())   // chats born from voice
  const wakeUsedRef   = useRef(false)                    // next turn was wake-initiated
  const greetingRef   = useRef<string | null>(null)      // pre-fetched greeting audio URL

  // Pre-fetch Veda's greeting so wake response is instant (Phase V2)
  useEffect(() => {
    let cancelled = false
    const text = GREETINGS[voiceLang] ?? GREETINGS.en
    fetch('/api/voice/tts', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language: voiceLang }),
    })
      .then(r => (r.ok ? r.blob() : null))
      .then(b => { if (b && !cancelled) greetingRef.current = URL.createObjectURL(b) })
      .catch(() => { /* greeting is best-effort */ })
    return () => { cancelled = true }
  }, [voiceLang])

  // ── Auto-scroll ─────────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ── Auto-resize textarea ────────────────────────────────────────────────────
  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }, [input])

  // ── Auto-save to localStorage ────────────────────────────────────────────────
  useEffect(() => {
    if (messages.length <= 1) return   // don't save welcome-only sessions
    const session: SavedSession = {
      id:               currentId,
      title:            makeTitle(messages),
      messages,
      backendSessionId: backendSid,
      createdAt:        sessions.find(s => s.id === currentId)?.createdAt ?? Date.now(),
      updatedAt:        Date.now(),
    }
    setSessions(prev => {
      const idx = prev.findIndex(s => s.id === currentId)
      const next = idx >= 0
        ? prev.map(s => s.id === currentId ? session : s)
        : [session, ...prev]
      saveSessions(next)
      return next
    })
  }, [messages])  // eslint-disable-line react-hooks/exhaustive-deps

  // ── New chat ─────────────────────────────────────────────────────────────────
  const handleNewChat = useCallback(async () => {
    if (backendSid) { try { await resetChatSession(backendSid) } catch { /* ignore */ } }
    setCurrentId(genId())
    setMessages([makeWelcome()])
    setBackendSid(undefined)
    setInput('')
    setApiError(null)
    setShowSlash(false)
    setTimeout(() => inputRef.current?.focus(), 80)
  }, [backendSid])

  // ── Load existing session ────────────────────────────────────────────────────
  const handleSelectSession = useCallback((s: SavedSession) => {
    setCurrentId(s.id)
    setMessages(s.messages)
    setBackendSid(s.backendSessionId)
    setInput('')
    setApiError(null)
    setShowSlash(false)
    setTimeout(() => inputRef.current?.focus(), 80)
  }, [])

  // ── Delete session ───────────────────────────────────────────────────────────
  const handleDeleteSession = useCallback((id: string) => {
    setSessions(prev => { const next = prev.filter(s => s.id !== id); saveSessions(next); return next })
    if (id === currentId) handleNewChat()
  }, [currentId, handleNewChat])

  // ── Export / Import / Print ──────────────────────────────────────────────────
  const currentSession = sessions.find(s => s.id === currentId) ?? null
  const hasChat = messages.length > 1

  const handleExport = () => {
    const s: SavedSession = currentSession ?? {
      id: currentId, title: makeTitle(messages), messages,
      backendSessionId: backendSid, createdAt: Date.now(), updatedAt: Date.now(),
    }
    exportSession(s)
  }

  const handleImport = (file: File) => {
    const reader = new FileReader()
    reader.onload = e => {
      try {
        const s = JSON.parse(e.target?.result as string) as SavedSession
        if (s.messages && Array.isArray(s.messages)) {
          const imported: SavedSession = {
            ...s, id: genId(),
            title: s.title ? `(imported) ${s.title}` : 'Imported Chat',
            updatedAt: Date.now(),
          }
          setSessions(prev => { const next = [imported, ...prev]; saveSessions(next); return next })
          handleSelectSession(imported)
        }
      } catch { /* invalid file */ }
    }
    reader.readAsText(file)
  }

  const handlePrint = () => {
    const s: SavedSession = currentSession ?? {
      id: currentId, title: makeTitle(messages), messages,
      backendSessionId: backendSid, createdAt: Date.now(), updatedAt: Date.now(),
    }
    printSession(s)
  }

  // ── Voice: speak a reply via Veda's TTS (edge-tts on the backend) ────────────
  const speak = useCallback(async (text: string) => {
    try {
      audioRef.current?.pause()
      const r = await fetch('/api/voice/tts', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: voiceLang }),
      })
      if (!r.ok) return
      const blob = await r.blob()
      const audio = new Audio(URL.createObjectURL(blob))
      audioRef.current = audio
      setSpeaking(true)
      audio.onended = () => setSpeaking(false)
      audio.onerror = () => setSpeaking(false)
      await audio.play()
    } catch { setSpeaking(false) }
  }, [voiceLang])

  const stopSpeaking = useCallback(() => {
    audioRef.current?.pause()
    setSpeaking(false)
  }, [])

  // ── Conversation analytics log (every turn, voice AND text) ─────────────────
  const logTurn = useCallback((sid: string, mode: 'voice' | 'text', userMessage: string,
                               intent: string, replyChars: number, latencyMs: number) => {
    const wake = wakeUsedRef.current
    wakeUsedRef.current = false
    fetch('/api/voice/log', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sid, mode, language: voiceLang, wake_word_used: wake,
        user_message: userMessage, intent, reply_chars: replyChars,
        latency_ms: latencyMs, tts_voice: mode === 'voice' ? voiceLang : '',
      }),
    }).catch(() => { /* analytics must never break chat */ })
  }, [voiceLang])

  // ── Send message ─────────────────────────────────────────────────────────────
  // sidOverride: pass null to force a fresh backend session (voice-new-chat flow)
  const send = useCallback(async (text: string, mode: 'voice' | 'text' = 'text',
                                  sidOverride?: string | null) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userMsg: Msg = { role: 'user', content: trimmed, ts: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setShowSlash(false)
    setLoading(true)
    setApiError(null)

    const sid = sidOverride !== undefined ? (sidOverride ?? undefined) : backendSid
    const t0 = Date.now()
    try {
      const data: ChatResponseData = await sendChat(trimmed, sid, mode)
      setBackendSid(data.session_id)
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply, intent: data.intent, ts: Date.now() }])
      logTurn(data.session_id, mode, trimmed, data.intent ?? '', data.reply.length, Date.now() - t0)
      if (mode === 'voice' || (speakReplies && voiceChatsRef.current.has(currentId))) {
        speak(data.reply)
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      const errText = detail ?? 'Connection error. Check that the backend is running.'
      setApiError(errText)
      setMessages(prev => [...prev, { role: 'assistant', content: `Sorry, I could not process that. ${errText}`, ts: Date.now() }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [loading, backendSid, speak, logTurn, speakReplies, currentId])

  // ── Voice: push-to-talk capture ──────────────────────────────────────────────
  const startListening = useCallback(() => {
    if (listening) { recogRef.current?.stop(); return }
    const recog = getSpeechRecognition()
    if (!recog) {
      setApiError('Voice input needs Chrome or Edge (Web Speech API not available)')
      return
    }
    stopSpeaking()
    const langMeta = VOICE_LANGS.find(l => l.code === voiceLang) ?? VOICE_LANGS[0]
    recog.lang = langMeta.sttLang
    recog.continuous = false
    recog.interimResults = true
    recogRef.current = recog
    setListening(true)

    let finalText = ''
    recog.onresult = (e) => {
      let interim = ''
      for (let i = 0; i < e.results.length; i++) {
        const res = e.results[i]
        if (res.isFinal) finalText += res[0].transcript
        else interim += res[0].transcript
      }
      setInput(finalText || interim)   // live transcript in the input box
    }
    recog.onerror = () => { setListening(false) }
    recog.onend = () => {
      setListening(false)
      const spoken = finalText.trim()
      if (!spoken) return
      // Voice conversations are recorded in their own chat: if the current
      // chat is a text conversation with history, start a fresh one first.
      if (messages.length > 1 && !voiceChatsRef.current.has(currentId)) {
        const newId = genId()
        voiceChatsRef.current.add(newId)
        setCurrentId(newId)
        setMessages([makeWelcome()])
        setBackendSid(undefined)
        setTimeout(() => send(spoken, 'voice', null), 60)
      } else {
        voiceChatsRef.current.add(currentId)
        send(spoken, 'voice')
      }
    }
    try { recog.start() } catch { setListening(false) }
  }, [listening, voiceLang, messages.length, currentId, send, stopSpeaking])

  // ── Voice: hands-free wake word "Veda" / "Adya" (Phase V2) ──────────────────
  // A lightweight continuous recognition session runs whenever the page is
  // otherwise idle. On hearing a wake word it plays the pre-cached greeting
  // and opens command capture. Chrome ends continuous sessions periodically;
  // onend bumps wakeRetry to restart (auto-restart pattern).
  useEffect(() => {
    if (!wakeEnabled || listening || loading || speaking) return
    const recog = getSpeechRecognition()
    if (!recog) return

    let matched = false
    let disposed = false
    const langMeta = VOICE_LANGS.find(l => l.code === voiceLang) ?? VOICE_LANGS[0]
    recog.lang = langMeta.sttLang
    recog.continuous = true
    recog.interimResults = true

    const onWake = () => {
      matched = true
      try { recog.abort() } catch { /* ignore */ }
      wakeUsedRef.current = true
      const play = greetingRef.current ? new Audio(greetingRef.current) : null
      if (play) {
        setSpeaking(true)
        play.onended = () => { setSpeaking(false); startListening() }
        play.onerror = () => { setSpeaking(false); startListening() }
        play.play().catch(() => { setSpeaking(false); startListening() })
      } else {
        startListening()
      }
    }

    recog.onresult = (e) => {
      // Only inspect the newest result to avoid re-matching old transcript
      const last = e.results[e.results.length - 1]
      if (!last) return
      const heard = (last[0]?.transcript ?? '').toLowerCase()
      if (WAKE_WORDS.some(w => heard.includes(w))) onWake()
    }
    recog.onerror = (e) => {
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
        setWakeEnabled(false)
        try { localStorage.setItem(WAKE_KEY, 'off') } catch { /* ignore */ }
      }
    }
    recog.onend = () => {
      // Chrome times continuous sessions out -- restart unless we woke or unmounted
      if (!matched && !disposed) setTimeout(() => setWakeRetry(n => n + 1), 500)
    }
    try { recog.start() } catch { /* mic busy -- retry on next state change */ }

    return () => { disposed = true; try { recog.abort() } catch { /* ignore */ } }
  }, [wakeEnabled, listening, loading, speaking, voiceLang, wakeRetry, startListening])

  // ── Input handling ────────────────────────────────────────────────────────────
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value
    setInput(val)
    if (val.startsWith('/')) {
      setShowSlash(true)
      setSlashFilter(val.slice(1))
    } else {
      setShowSlash(false)
      setSlashFilter('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Escape' && showSlash) { setShowSlash(false); return }
    if (e.key === 'Enter' && !e.shiftKey && !showSlash) {
      e.preventDefault()
      send(input)
    }
  }

  const handleSlashSelect = (query: string) => {
    setInput(query)
    setShowSlash(false)
    setSlashFilter('')
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  // ── Render ────────────────────────────────────────────────────────────────────
  return (
    <div style={{
      display: 'flex',
      margin: '-16px',            // break out of AppShell p-4 padding
      height: 'calc(100% + 32px)',
      overflow: 'hidden',
      background: '#0A0D14',
    }}>

      {/* ── Sidebar ────────────────────────────────────────────────────────── */}
      <Sidebar
        sessions={sessions}
        currentId={currentId}
        onSelect={handleSelectSession}
        onNew={handleNewChat}
        onDelete={handleDeleteSession}
        onExport={handleExport}
        onImport={handleImport}
        onPrint={handlePrint}
        hasChat={hasChat}
      />

      {/* ── Main chat area ──────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>

        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 20px', borderBottom: '1px solid #1E2332', flexShrink: 0, background: '#0A0D14',
        }}>
          <div>
            <div style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700 }}>
              {makeTitle(messages) === 'New Chat' ? 'MARKET CHATBOT' : makeTitle(messages)}
            </div>
            <div style={{ color: '#334155', fontSize: 9, marginTop: 2 }}>
              Groq / Llama 3.3 70B &nbsp;+&nbsp; RAG (6 domains) &nbsp;+&nbsp; 11 live tools
              {backendSid && <span style={{ color: '#1E2332' }}> &nbsp;|&nbsp; {backendSid.slice(0, 8)}</span>}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Voice controls (Phase V1: Veda) */}
            <select
              value={voiceLang}
              onChange={e => { setVoiceLang(e.target.value); try { localStorage.setItem(VOICE_LANG_KEY, e.target.value) } catch { /* ignore */ } }}
              title="Veda's language and voice"
              style={{ background: '#0D1117', border: '1px solid #1E2332', borderRadius: 4, color: '#94A3B8', fontSize: 9, padding: '3px 6px', outline: 'none', cursor: 'pointer' }}
            >
              {VOICE_LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
            <button
              onClick={() => setSpeakReplies(v => !v)}
              title={speakReplies ? 'Veda speaks replies in voice chats (on)' : 'Voice replies muted'}
              style={{ background: 'transparent', border: `1px solid ${speakReplies ? '#3B82F6' : '#1E2332'}`, borderRadius: 4, color: speakReplies ? '#60A5FA' : '#334155', fontSize: 9, padding: '3px 8px', cursor: 'pointer', fontWeight: 700 }}
            >
              {speakReplies ? 'VOICE ON' : 'MUTED'}
            </button>
            <button
              onClick={() => {
                const next = !wakeEnabled
                setWakeEnabled(next)
                try { localStorage.setItem(WAKE_KEY, next ? 'on' : 'off') } catch { /* ignore */ }
              }}
              title={wakeEnabled ? 'Hands-free: say "Veda" or "Adya" to activate (on)' : 'Wake word off -- use the mic button'}
              style={{ background: wakeEnabled ? '#14532D22' : 'transparent', border: `1px solid ${wakeEnabled ? '#22C55E' : '#1E2332'}`, borderRadius: 4, color: wakeEnabled ? '#4ADE80' : '#334155', fontSize: 9, padding: '3px 8px', cursor: 'pointer', fontWeight: 700 }}
            >
              {wakeEnabled ? 'WAKE: VEDA' : 'WAKE OFF'}
            </button>
            {speaking && (
              <button onClick={stopSpeaking} style={{ background: '#1E3A5F', border: '1px solid #3B82F6', borderRadius: 4, color: '#60A5FA', fontSize: 9, padding: '3px 8px', cursor: 'pointer', fontWeight: 700 }}>
                Veda speaking... stop
              </button>
            )}
            <span style={{ fontSize: 9, color: '#334155' }}>Type / for quick questions</span>
            {Object.entries(INTENT_META).slice(0, 5).map(([k, v]) => (
              <span key={k} style={{ fontSize: 8, padding: '1px 5px', borderRadius: 2, border: `1px solid ${v.color}33`, color: v.color, fontWeight: 700, letterSpacing: 0.5 }}>{v.label}</span>
            ))}
          </div>
        </div>

        {/* Message thread */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: '16px 20px',
          scrollbarWidth: 'thin', scrollbarColor: '#1E2332 transparent',
        }}>
          {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
          {loading && (
            <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: 12 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#1E2332', border: '1px solid #3B82F644', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, marginRight: 8, flexShrink: 0, color: '#60A5FA' }}>AI</div>
              <div style={{ padding: '10px 14px', borderRadius: '2px 12px 12px 12px', background: '#141720', border: '1px solid #1E2332' }}>
                <TypingDots />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* API error banner */}
        {apiError && (apiError.includes('API_KEY') || apiError.includes('not configured')) && (
          <div style={{ margin: '0 20px 8px', padding: '8px 14px', borderRadius: 4, background: '#1c0000', border: '1px solid #EF444444', color: '#EF4444', fontSize: 11, flexShrink: 0 }}>
            API key is not configured — check .env and restart the backend.
          </div>
        )}

        {/* Input area */}
        <div style={{ padding: '0 20px 14px', flexShrink: 0, borderTop: '1px solid #1E2332', paddingTop: 12 }}>
          <div style={{ position: 'relative' }}>
            {showSlash && (
              <SlashPalette
                filter={slashFilter}
                onSelect={handleSlashSelect}
                onClose={() => setShowSlash(false)}
              />
            )}
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
              {/* Mic: push-to-talk (Phase V1) */}
              <button
                onClick={startListening}
                disabled={loading}
                title={listening ? 'Listening... click to stop' : `Speak to Veda (${VOICE_LANGS.find(l => l.code === voiceLang)?.label})`}
                style={{
                  width: 42, height: 42, borderRadius: '50%', flexShrink: 0,
                  border: `2px solid ${listening ? '#EF4444' : '#3B82F6'}`,
                  background: listening ? '#EF444422' : '#0D1117',
                  color: listening ? '#EF4444' : '#60A5FA',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: listening ? 16 : 9, fontWeight: 700,
                  animation: listening ? 'pulse 1.2s infinite' : 'none',
                }}
              >
                {listening ? '●' : 'MIC'}
              </button>
              <style>{'@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5);} 50% { box-shadow: 0 0 0 8px rgba(239,68,68,0);} }'}</style>
              <textarea
                ref={inputRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={listening ? 'Listening... speak now' : 'Ask about markets, sectors, stocks… or type / for quick questions'}
                rows={1}
                style={{
                  flex: 1, resize: 'none', overflow: 'hidden',
                  background: '#0D1117', border: '1px solid #1E2332', borderRadius: 6,
                  color: '#E2E8F0', padding: '10px 14px', fontSize: 13,
                  outline: 'none', fontFamily: 'inherit', lineHeight: 1.5,
                  transition: 'border-color 0.15s',
                }}
                onFocus={e  => (e.currentTarget.style.borderColor = '#3B82F6')}
                onBlur={e   => (e.currentTarget.style.borderColor = '#1E2332')}
                disabled={loading}
              />
              <button
                onClick={() => send(input)}
                disabled={!input.trim() || loading}
                style={{
                  padding: '10px 20px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                  cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                  background: input.trim() && !loading ? '#1E3A5F' : '#0D1117',
                  color:  input.trim() && !loading ? '#60A5FA'  : '#334155',
                  border: `1px solid ${input.trim() && !loading ? '#3B82F6' : '#1E2332'}`,
                  transition: 'all 0.15s', whiteSpace: 'nowrap', flexShrink: 0,
                }}>
                {loading ? '...' : 'Send'}
              </button>
            </div>
          </div>
          <div style={{ fontSize: 9, color: '#1E2332', textAlign: 'center', marginTop: 6 }}>
            AI responses are for informational purposes only — not financial advice
          </div>
        </div>
      </div>
    </div>
  )
}
