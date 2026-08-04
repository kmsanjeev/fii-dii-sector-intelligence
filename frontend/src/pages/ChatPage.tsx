/**
 * ChatPage — Phase D v2 -> Phase V-UI (global Veda)
 * Full AI chat UI with persistent history, slash-command palette, and sidebar.
 * POST /api/chat  ->  reply + session_id + intent
 * Persistence: localStorage key "mci_chat_sessions" (up to 60 sessions)
 *
 * Voice/session state now lives in vedaStore (shared with the global
 * VedaWidget in AppShell) -- this page is the "detail view": full session
 * history, export/import/print, slash commands. A message sent here shows
 * up in the floating widget instantly, and vice versa, since both read
 * the same store. The wake-word listener is NOT owned here anymore --
 * see VedaWakeController, mounted once in AppShell so it works app-wide.
 */
import { useState, useRef, useEffect } from 'react'
import {
  useVedaStore, genId, makeTitle, VOICE_LANGS,
  type Msg, type SavedSession,
} from '../store/vedaStore'

// ─── Constants ────────────────────────────────────────────────────────────────

const INTENT_META: Record<string, { label: string; color: string }> = {
  MARKET:    { label: 'MARKET',    color: '#22C55E' },
  SECTOR:    { label: 'SECTOR',    color: '#3B82F6' },
  STOCK:     { label: 'STOCK',     color: '#8B5CF6' },
  CORPORATE: { label: 'CORPORATE', color: '#F59E0B' },
  RESEARCH:  { label: 'RESEARCH',  color: '#64748B' },
  KUNDLI:    { label: 'KUNDLI',    color: '#E879F9' },
  ASTRO:     { label: 'ASTRO',     color: '#FB923C' },
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

// ─── Storage helpers (export/import/print only -- session CRUD lives in the store) ──

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

      {/* Veda demand analytics (Phase V3) */}
      <VedaAnalyticsCard />

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

// ─── Veda demand analytics card (Phase V3) ────────────────────────────────────

type VedaAnalytics = {
  source: string
  summary?: Record<string, number>
  turns?: number
  top_intents?: { key: string; count: number }[] | Record<string, number>
  top_symbols?: { key: string; count: number }[]
  modes?: { key: string; count: number; share_pct: number }[]
}

function VedaAnalyticsCard() {
  const [data, setData] = useState<VedaAnalytics | null>(null)

  useEffect(() => {
    fetch('/api/voice/analytics')
      .then(r => (r.ok ? r.json() : null))
      .then(d => setData(d))
      .catch(() => { /* card is best-effort */ })
  }, [])

  if (!data) return null
  const turns = data.summary?.total_turns ?? data.turns ?? 0
  if (!turns) return null

  const intents: { key: string; count: number }[] = Array.isArray(data.top_intents)
    ? data.top_intents.slice(0, 3)
    : Object.entries(data.top_intents ?? {}).slice(0, 3).map(([k, v]) => ({ key: k, count: v as number }))
  const symbols = (data.top_symbols ?? []).slice(0, 3)
  const voiceMode = Array.isArray(data.modes) ? data.modes.find(m => m.key === 'voice') : undefined

  return (
    <div style={{ padding: '10px 12px', borderTop: '1px solid #1E2332', flexShrink: 0 }}>
      <div style={{ color: '#475569', fontSize: 9, fontWeight: 700, letterSpacing: 1.5, marginBottom: 6 }}>
        VEDA ANALYTICS
      </div>
      <div style={{ fontSize: 9, color: '#64748B', display: 'flex', flexDirection: 'column', gap: 3 }}>
        <span>{turns} turns{voiceMode ? ` · ${voiceMode.share_pct}% by voice` : ''}</span>
        {intents.length > 0 && (
          <span>Top asks: {intents.map(i => `${i.key.toLowerCase().replace(/_/g, ' ')} (${i.count})`).join(', ')}</span>
        )}
        {symbols.length > 0 && (
          <span>Top stocks: {symbols.map(s => s.key).join(', ')}</span>
        )}
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

function ResearchBadge({ research }: { research?: Msg['research'] }) {
  if (!research || (!research.requested && !research.used && !research.error)) return null

  const label = research.used
    ? `Research used${research.provider ? `: ${research.provider}` : ''}${research.source_count ? `, ${research.source_count} source${research.source_count === 1 ? '' : 's'}` : ''}${research.cached ? ', cache' : ''}`
    : research.error
      ? 'Research was requested, but outside lookup was unavailable'
      : 'Research mode checked, but no outside source was added'

  const color = research.used ? '#60A5FA' : research.error ? '#F59E0B' : '#94A3B8'
  const border = research.used ? '#3B82F644' : research.error ? '#F59E0B44' : '#334155'

  return (
    <div style={{
      fontSize: 9,
      color,
      border: `1px solid ${border}`,
      background: '#0D1117',
      borderRadius: 4,
      display: 'inline-block',
      padding: '2px 7px',
      marginBottom: 5,
    }}>
      {label}
    </div>
  )
}

function AttachmentPills({
  attachments,
  onRemove,
  align = 'flex-start',
}: {
  attachments?: Msg['attachments']
  onRemove?: (storageKey?: string | null, name?: string) => void
  align?: 'flex-start' | 'flex-end'
}) {
  if (!attachments || attachments.length === 0) return null
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: align, marginTop: 6 }}>
      {attachments.map((attachment, index) => (
        <div
          key={`${attachment.storage_key ?? attachment.name}-${index}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '3px 8px',
            borderRadius: 999,
            border: `1px solid ${attachment.warning ? '#F59E0B44' : '#334155'}`,
            background: '#0D1117',
            color: attachment.warning ? '#FCD34D' : '#94A3B8',
            fontSize: 10,
            maxWidth: 280,
          }}
          title={attachment.warning || attachment.excerpt || attachment.name}
        >
          <span style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            maxWidth: 220,
          }}>
            {attachment.name}
          </span>
          {onRemove && (
            <button
              onClick={() => onRemove(attachment.storage_key, attachment.name)}
              style={{
                background: 'none',
                border: 'none',
                color: 'inherit',
                cursor: 'pointer',
                fontSize: 11,
                lineHeight: 1,
                padding: 0,
              }}
            >
              x
            </button>
          )}
        </div>
      ))}
    </div>
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
        {!isUser && <ResearchBadge research={msg.research} />}
        <div style={{
          padding: '10px 14px',
          borderRadius: isUser ? '12px 12px 2px 12px' : '2px 12px 12px 12px',
          background: isUser ? '#1E3A5F' : '#141720',
          border: `1px solid ${isUser ? '#1E4A8F' : '#1E2332'}`,
          color: '#E2E8F0', fontSize: 13, lineHeight: 1.65,
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        }}>{msg.content}</div>
        <AttachmentPills attachments={msg.attachments} align={isUser ? 'flex-end' : 'flex-start'} />
        <div style={{ fontSize: 9, color: '#334155', marginTop: 3, display: 'flex', alignItems: 'center', justifyContent: isUser ? 'flex-end' : 'flex-start', gap: 6 }}>
          {new Date(msg.ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          <CopyButton text={msg.content} />
        </div>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function ChatPage() {
  // Shared state (same store the global VedaWidget uses)
  const sessions       = useVedaStore(s => s.sessions)
  const currentId      = useVedaStore(s => s.currentId)
  const messages        = useVedaStore(s => s.messages)
  const backendSid      = useVedaStore(s => s.backendSid)
  const voiceLang       = useVedaStore(s => s.voiceLang)
  const speakReplies    = useVedaStore(s => s.speakReplies)
  const listening        = useVedaStore(s => s.listening)
  const speaking          = useVedaStore(s => s.speaking)
  const loading           = useVedaStore(s => s.loading)
  const wakeEnabled       = useVedaStore(s => s.wakeEnabled)
  const followUpEnabled   = useVedaStore(s => s.followUpEnabled)
  const followUpListening = useVedaStore(s => s.followUpListening)
  const researchMode      = useVedaStore(s => s.researchMode)
  const researchEnabled   = useVedaStore(s => s.researchEnabled)
  const attachmentsEnabled = useVedaStore(s => s.attachmentsEnabled)
  const pendingAttachments = useVedaStore(s => s.pendingAttachments)
  const uploadingAttachment = useVedaStore(s => s.uploadingAttachment)
  const apiError          = useVedaStore(s => s.apiError)
  const liveTranscript    = useVedaStore(s => s.liveTranscript)

  const send               = useVedaStore(s => s.send)
  const startListening     = useVedaStore(s => s.startListening)
  const stopSpeaking       = useVedaStore(s => s.stopSpeaking)
  const setVoiceLang       = useVedaStore(s => s.setVoiceLang)
  const setSpeakReplies    = useVedaStore(s => s.setSpeakReplies)
  const setWakeEnabled     = useVedaStore(s => s.setWakeEnabled)
  const setFollowUpEnabled = useVedaStore(s => s.setFollowUpEnabled)
  const setResearchMode    = useVedaStore(s => s.setResearchMode)
  const setApiError        = useVedaStore(s => s.setApiError)
  const uploadAttachment   = useVedaStore(s => s.uploadAttachment)
  const removePendingAttachment = useVedaStore(s => s.removePendingAttachment)
  const refreshCapabilities = useVedaStore(s => s.refreshCapabilities)
  const handleNewChatStore = useVedaStore(s => s.handleNewChat)
  const handleSelectStore  = useVedaStore(s => s.handleSelectSession)
  const handleDeleteStore  = useVedaStore(s => s.handleDeleteSession)

  // Page-local UI state (each surface, drawer vs full page, owns its own textbox)
  const [input,      setInput]      = useState('')
  const [showSlash,  setShowSlash]  = useState(false)
  const [slashFilter,setSlashFilter]= useState('')

  const bottomRef  = useRef<HTMLDivElement>(null)
  const inputRef   = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Reflect the live transcript into the input box while listening (was
  // setInput() directly inside the recognizer's onresult before this was
  // shared state -- now it flows through the store like everything else).
  useEffect(() => {
    if (listening) setInput(liveTranscript)
  }, [liveTranscript, listening])

  useEffect(() => {
    void refreshCapabilities()
  }, [refreshCapabilities])

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

  // ── New chat / session management (thin wrappers over store actions) ────────
  const handleNewChat = async () => {
    await handleNewChatStore()
    setInput(''); setShowSlash(false)
    setTimeout(() => inputRef.current?.focus(), 80)
  }

  const handleSelectSession = (s: SavedSession) => {
    handleSelectStore(s)
    setInput(''); setShowSlash(false)
    setTimeout(() => inputRef.current?.focus(), 80)
  }

  const handleDeleteSession = (id: string) => { handleDeleteStore(id) }

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
          const next = [imported, ...sessions]
          useVedaStore.setState({ sessions: next })
          try { localStorage.setItem('mci_chat_sessions', JSON.stringify(next.slice(0, 60))) } catch { /* ignore */ }
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
      const text = input
      setInput('')
      send(text)
    }
  }

  const handleSlashSelect = (query: string) => {
    setInput(query)
    setShowSlash(false)
    setSlashFilter('')
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const submitClick = () => {
    const text = input
    setInput('')
    send(text)
  }

  const handleFileSelection = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    for (const file of Array.from(files)) {
      await uploadAttachment(file)
    }
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
              Groq / Llama 3.3 70B &nbsp;+&nbsp; RAG (6 domains) &nbsp;+&nbsp; 23 live tools
              <span style={{ color: researchMode && researchEnabled ? '#60A5FA' : '#64748B' }}>
                {' '}|{' '}
                {researchEnabled
                  ? researchMode
                    ? 'Research mode: ON'
                    : 'Research mode: local-first'
                  : 'Research mode: unavailable'}
              </span>
              {backendSid && <span style={{ color: '#1E2332' }}> &nbsp;|&nbsp; {backendSid.slice(0, 8)}</span>}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Voice controls (Phase V1: Veda) */}
            <select
              value={voiceLang}
              onChange={e => setVoiceLang(e.target.value)}
              title="Veda's language and voice"
              style={{ background: '#0D1117', border: '1px solid #1E2332', borderRadius: 4, color: '#94A3B8', fontSize: 9, padding: '3px 6px', outline: 'none', cursor: 'pointer' }}
            >
              {VOICE_LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
            <button
              onClick={() => setSpeakReplies(!speakReplies)}
              title={speakReplies ? 'Veda speaks replies in voice chats (on)' : 'Voice replies muted'}
              style={{ background: 'transparent', border: `1px solid ${speakReplies ? '#3B82F6' : '#1E2332'}`, borderRadius: 4, color: speakReplies ? '#60A5FA' : '#334155', fontSize: 9, padding: '3px 8px', cursor: 'pointer', fontWeight: 700 }}
            >
              {speakReplies ? 'VOICE ON' : 'MUTED'}
            </button>
            <button
              onClick={() => setWakeEnabled(!wakeEnabled)}
              title={wakeEnabled ? 'Hands-free: say "Veda" or "Adya" from any page (on)' : 'Wake word off -- use the mic button'}
              style={{ background: wakeEnabled ? '#14532D22' : 'transparent', border: `1px solid ${wakeEnabled ? '#22C55E' : '#1E2332'}`, borderRadius: 4, color: wakeEnabled ? '#4ADE80' : '#334155', fontSize: 9, padding: '3px 8px', cursor: 'pointer', fontWeight: 700 }}
            >
              {wakeEnabled ? 'WAKE: VEDA' : 'WAKE OFF'}
            </button>
            <button
              onClick={() => setFollowUpEnabled(!followUpEnabled)}
              title={
                !wakeEnabled ? 'Follow-up needs wake word enabled'
                : followUpEnabled ? 'Hands-free follow-up: mic reopens after each reply, no need to say "Veda" again (on)'
                : 'Follow-up off -- say "Veda" for every question'
              }
              style={{
                background: followUpEnabled && wakeEnabled ? '#1E3A5F' : 'transparent',
                border: `1px solid ${followUpEnabled && wakeEnabled ? '#3B82F6' : '#1E2332'}`,
                borderRadius: 4, color: followUpEnabled && wakeEnabled ? '#60A5FA' : '#334155',
                fontSize: 9, padding: '3px 8px', cursor: 'pointer', fontWeight: 700,
                opacity: wakeEnabled ? 1 : 0.5,
              }}
            >
              {followUpEnabled ? 'FOLLOW-UP: ON' : 'FOLLOW-UP: OFF'}
            </button>
            <button
              onClick={() => setResearchMode(!researchMode)}
              disabled={!researchEnabled}
              title={
                researchEnabled
                  ? researchMode
                    ? 'Research mode on: Veda may check outside sources when local data is weak'
                    : 'Research mode off: Veda stays local-first unless the query auto-needs research'
                  : 'Research mode is not enabled by the backend yet'
              }
              style={{
                background: researchMode && researchEnabled ? '#1E3A5F' : 'transparent',
                border: `1px solid ${researchMode && researchEnabled ? '#3B82F6' : '#1E2332'}`,
                borderRadius: 4,
                color: researchMode && researchEnabled ? '#60A5FA' : '#334155',
                fontSize: 9,
                padding: '3px 8px',
                cursor: researchEnabled ? 'pointer' : 'not-allowed',
                fontWeight: 700,
                opacity: researchEnabled ? 1 : 0.55,
              }}
            >
              {researchMode ? 'RESEARCH: ON' : 'RESEARCH: OFF'}
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

        {/* API error / voice hint banner */}
        {apiError && (apiError.includes('API_KEY') || apiError.includes('not configured')) && (
          <div style={{ margin: '0 20px 8px', padding: '8px 14px', borderRadius: 4, background: '#1c0000', border: '1px solid #EF444444', color: '#EF4444', fontSize: 11, flexShrink: 0 }}>
            API key is not configured — check .env and restart the backend.
          </div>
        )}
        {apiError && apiError.includes('Veda') && (
          <div style={{ margin: '0 20px 8px', padding: '8px 14px', borderRadius: 4, background: '#1a1200', border: '1px solid #F59E0B44', color: '#F59E0B', fontSize: 11, flexShrink: 0 }}>
            {apiError}
          </div>
        )}
        {apiError && !apiError.includes('API_KEY') && !apiError.includes('not configured') && !apiError.includes('Veda') && (
          <div style={{ margin: '0 20px 8px', padding: '8px 14px', borderRadius: 4, background: '#1c0000', border: '1px solid #EF444444', color: '#EF4444', fontSize: 11, flexShrink: 0 }}>
            {apiError}
            <button onClick={() => setApiError(null)} style={{ float: 'right', background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer', fontSize: 12 }}>×</button>
          </div>
        )}

        {/* Input area */}
        <div style={{ padding: '0 20px 14px', flexShrink: 0, borderTop: '1px solid #1E2332', paddingTop: 12 }}>
          <div style={{ position: 'relative' }}>
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
            {showSlash && (
              <SlashPalette
                filter={slashFilter}
                onSelect={handleSlashSelect}
                onClose={() => setShowSlash(false)}
              />
            )}
            {(pendingAttachments.length > 0 || uploadingAttachment) && (
              <div style={{ marginBottom: 10 }}>
                <AttachmentPills attachments={pendingAttachments} onRemove={removePendingAttachment} />
                {uploadingAttachment && (
                  <div style={{ fontSize: 10, color: '#60A5FA', marginTop: 6 }}>
                    Uploading attachment...
                  </div>
                )}
              </div>
            )}
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
              {/* Mic: push-to-talk (Phase V1) */}
              <button
                onClick={() => startListening()}
                disabled={loading}
                title={listening ? (followUpListening ? 'Listening for follow-up... click to stop' : 'Listening... click to stop') : `Speak to Veda (${VOICE_LANGS.find(l => l.code === voiceLang)?.label})`}
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
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={!attachmentsEnabled || loading || uploadingAttachment}
                title={
                  attachmentsEnabled
                    ? 'Attach a PDF, text file, CSV, JSON, or image'
                    : 'Attachments are not enabled by the backend yet'
                }
                style={{
                  width: 42, height: 42, borderRadius: 10, flexShrink: 0,
                  border: `1px solid ${attachmentsEnabled ? '#1E2332' : '#2D3348'}`,
                  background: attachmentsEnabled ? '#0D1117' : 'transparent',
                  color: attachmentsEnabled ? '#94A3B8' : '#334155',
                  cursor: attachmentsEnabled && !loading && !uploadingAttachment ? 'pointer' : 'not-allowed',
                  fontSize: 14,
                }}
              >
                +
              </button>
              <textarea
                ref={inputRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  listening
                    ? (followUpListening ? 'Listening for follow-up... speak now' : 'Listening... speak now')
                    : researchMode && researchEnabled
                      ? 'Ask anything. Veda can also check outside sources when needed.'
                      : attachmentsEnabled
                        ? 'Ask about markets, sectors, stocks, or attach a file... type / for quick questions'
                        : 'Ask about markets, sectors, stocks... or type / for quick questions'
                }
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
                onClick={submitClick}
                disabled={(!input.trim() && pendingAttachments.length === 0) || loading}
                style={{
                  padding: '10px 20px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                  cursor: (input.trim() || pendingAttachments.length > 0) && !loading ? 'pointer' : 'not-allowed',
                  background: (input.trim() || pendingAttachments.length > 0) && !loading ? '#1E3A5F' : '#0D1117',
                  color:  (input.trim() || pendingAttachments.length > 0) && !loading ? '#60A5FA'  : '#334155',
                  border: `1px solid ${(input.trim() || pendingAttachments.length > 0) && !loading ? '#3B82F6' : '#1E2332'}`,
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
