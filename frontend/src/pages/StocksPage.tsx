/**
 * StocksPage — unified stock intelligence dashboard
 * Routes: /stocks (search prompt) | /stocks/:symbol (full view)
 *
 * Combines ChartsPage (full 7-TF candlestick chart) and StockDetailPage
 * (all fundamentals, intelligence, announcements) into one scrolling page.
 * No separate pages. No duplication.
 */

import {
  useEffect, useRef, useState, useCallback,
  Component, type ReactNode,
} from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  createChart, ColorType, CandlestickSeries,
  type IChartApi, type ISeriesApi, type CandlestickData, type Time,
} from 'lightweight-charts'
import {
  api, fetchStockDetail, fetchStockAnnouncements, fetchStockCorpActions,
  fetchAnnouncementSummary, fetchNewsArticleSummary,
  type TechnicalIndicators, type FnoData, type Announcement, type CorpAction, type NewsArticle,
} from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { TradeIntelligenceCard } from '../components/platform/TradeIntelligenceCard'
import { AstroSignalCard, type AstroSignal } from '../components/platform/AstroSignalCard'
import { KundliCard } from '../components/platform/KundliCard'
import { T, FS, FW, CARD_HDR, FIELD_LBL } from '../styles/tokens'
import { useMobile } from '../hooks/useMobile'

// ─── Page-local palette (aliases to shared tokens + chart-specific) ───────────

const P = {
  bg:      T.bg,
  panel:   T.panel,
  cell:    T.cell,
  border:  T.border,
  litBdr:  T.borderHi,
  text:    T.text,
  sub:     T.textSub,
  dim:     T.muted,
  green:   T.green,
  red:     T.red,
  blue:    T.blue,
  amber:   T.amber,
  purple:  T.purple,
  teal:    T.teal,
}

// ─── Shared inline style shortcuts (use token sizes) ─────────────────────────

const LABEL: React.CSSProperties = {
  ...FIELD_LBL,
}

const CARD_HEADER: React.CSSProperties = {
  ...CARD_HDR,
}

// ─── Chart types & constants ──────────────────────────────────────────────────

type Bar = { time: string | number; open: number; high: number; low: number; close: number; volume: number }
type OhlcvResponse = { bars: Bar[]; count: number; from: string | number | null; to: string | number | null }
type ChartSignal = {
  symbol?: string; sector?: string; label?: string; bull_run_score?: number
  price_score?: number; sector_flow_score?: number; deal_score?: number; corporate_score?: number
  market_regime?: string; regime_multiplier?: number; as_of_date?: string
  ml_bull_run_score?: number | null; accumulation_score?: number | null
  forward_return_score?: number | null
  rotation_signal?: string; sector_combined?: number
  shp_fii_pct?: number | null; shp_dii_pct?: number | null
  shp_promoter_pct?: number | null; shp_quarter?: string
}
type SymbolHit = { SYMBOL: string; COMPANY_NAME: string }

type TF = '5M' | '15M' | '1H' | '1D' | '1W' | '1M' | '3M'
const INTRADAY = new Set<TF>(['5M', '15M', '1H'])
const TF_DAILY: TF[] = ['1D', '1W', '1M', '3M']
const TF_INTRA: TF[] = ['5M', '15M', '1H']
const DEFAULT_BARS: Record<TF, number> = { '5M': 200, '15M': 200, '1H': 180, '1D': 180, '1W': 52, '1M': 24, '3M': 16 }


// ─── API helpers ─────────────────────────────────────────────────────────────

const fetchOhlcv   = (sym: string, tf: TF) =>
  api.get<OhlcvResponse>('/charts/ohlcv', { params: { symbol: sym, timeframe: tf } }).then(r => r.data)
const fetchCSignal = (sym: string) =>
  api.get<ChartSignal>('/charts/signals', { params: { symbol: sym } }).then(r => r.data)
const fetchAC      = (q: string) =>
  api.get<{ symbols: SymbolHit[] }>('/charts/symbols', { params: { q } }).then(r => r.data)

// ─── Pure helpers ─────────────────────────────────────────────────────────────

function toPeriodStart(dateStr: string, tf: TF): string {
  if (tf === '1D' || INTRADAY.has(tf)) return dateStr
  const d = new Date(dateStr + 'T00:00:00Z')
  if (tf === '1W') { const o = d.getUTCDay() === 0 ? 6 : d.getUTCDay() - 1; d.setUTCDate(d.getUTCDate() - o) }
  else if (tf === '1M') d.setUTCDate(1)
  else if (tf === '3M') d.setUTCMonth(Math.floor(d.getUTCMonth() / 3) * 3, 1)
  return d.toISOString().slice(0, 10)
}

function crFmt(v: number): string {
  if (v >= 1e5) return `${(v / 1e5).toFixed(1)}L Cr`
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K Cr`
  return `${v.toFixed(0)} Cr`
}

function pct(v: number | null | undefined): string {
  if (v == null) return '--'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}

function scoreC(v: number | null | undefined): string {
  if (v == null) return P.dim
  return v >= 65 ? P.green : v >= 42 ? P.amber : P.red
}

function fmtOhlcTime(t: string | number | null | undefined): string {
  if (t == null) return ''
  if (typeof t === 'number')
    return new Date(t * 1000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: '2-digit', hour: '2-digit', minute: '2-digit' })
  return t
}

// ─── Small reusable components ────────────────────────────────────────────────

function SectionCard({ title, accentColor, children }: { title: string; accentColor?: string; children: ReactNode }) {
  return (
    <div style={{
      background: P.panel, borderRadius: 8, overflow: 'hidden',
      border: `1px solid ${P.border}`,
      borderTop: accentColor ? `3px solid ${accentColor}` : `1px solid ${P.border}`,
    }}>
      <div style={CARD_HEADER}>{title}</div>
      <div style={{ padding: 14 }}>{children}</div>
    </div>
  )
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '10px 0 2px' }}>
      <div style={{ fontSize: 9, fontWeight: 800, color: P.dim, letterSpacing: '0.12em', flexShrink: 0 }}>{label}</div>
      <div style={{ flex: 1, height: 1, background: P.border }} />
    </div>
  )
}

function ScoreBar({ label, value, max = 100, color }: { label: string; value: number | null | undefined; max?: number; color?: string }) {
  if (value == null) return null
  const fill = Math.min(Math.max(value / max, 0), 1) * 100
  const c = color ?? scoreC(max === 100 ? value : value / max * 100)
  return (
    <div style={{ marginBottom: 7 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: 10, color: P.sub }}>{label}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: c, fontVariantNumeric: 'tabular-nums' }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ height: 3, background: '#1A2D44', borderRadius: 2 }}>
        <div style={{ width: `${fill}%`, height: '100%', background: c, borderRadius: 2, transition: 'width .4s' }} />
      </div>
    </div>
  )
}

function Chip({ label, color, size = 10 }: { label: string; color: string; size?: number }) {
  return (
    <span style={{
      fontSize: size - 1, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
      background: color + '20', color, border: `1px solid ${color}40`, letterSpacing: 0.4,
    }}>{label}</span>
  )
}

// ─── Chart error boundary ─────────────────────────────────────────────────────

class ChartBoundary extends Component<{ children: ReactNode }, { err: string | null }> {
  constructor(p: { children: ReactNode }) { super(p); this.state = { err: null } }
  static getDerivedStateFromError(e: unknown) { return { err: e instanceof Error ? e.message : String(e) } }
  render() {
    if (this.state.err) return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 12, color: P.red }}>
        <span style={{ fontWeight: 700 }}>Chart Error</span>
        <span style={{ color: P.sub, fontSize: 11 }}>{this.state.err}</span>
        <button onClick={() => this.setState({ err: null })} style={{ padding: '4px 14px', border: `1px solid ${P.red}`, background: 'transparent', color: P.red, cursor: 'pointer', borderRadius: 4 }}>Retry</button>
      </div>
    )
    return this.props.children
  }
}

// ─── Search prompt (no symbol state) ─────────────────────────────────────────

function SearchPrompt({ onSelect }: { onSelect: (s: string) => void }) {
  const [q, setQ] = useState('')
  const [show, setShow] = useState(false)
  const { data } = useQuery({
    queryKey: ['stocks-ac-prompt', q],
    queryFn: () => fetchAC(q),
    enabled: show && q.length > 0,
    staleTime: 30_000,
  })

  const QUICK = ['RELIANCE', 'HDFCBANK', 'TATASTEEL', 'INFY', 'ICICIBANK', 'WIPRO', 'LT', 'SBIN']

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 160px)', gap: 24 }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 28, fontWeight: 900, color: P.text, letterSpacing: 2, marginBottom: 6 }}>STOCK INTELLIGENCE</div>
        <div style={{ fontSize: 13, color: P.sub }}>Search any NSE symbol to view its full intelligence dashboard</div>
      </div>

      <div style={{ position: 'relative', width: 380 }}>
        <input
          autoFocus
          value={q}
          onChange={e => { setQ(e.target.value.toUpperCase()); setShow(true) }}
          onKeyDown={e => { if (e.key === 'Enter' && q.trim()) onSelect(q.trim()); if (e.key === 'Escape') setShow(false) }}
          onFocus={() => setShow(true)}
          onBlur={() => setTimeout(() => setShow(false), 160)}
          placeholder="Type a symbol e.g. RELIANCE..."
          style={{
            width: '100%', boxSizing: 'border-box',
            background: P.panel, border: `2px solid ${P.litBdr}`, borderRadius: 8,
            color: P.text, padding: '14px 18px', fontSize: 18,
            fontFamily: 'monospace', fontWeight: 700, outline: 'none',
            boxShadow: `0 0 0 4px ${P.blue}18`,
          }}
        />
        {show && data?.symbols && data.symbols.length > 0 && (
          <div style={{
            position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 200,
            background: '#0D1A2E', border: `1px solid ${P.litBdr}`, borderRadius: 6,
            marginTop: 4, maxHeight: 320, overflowY: 'auto',
            boxShadow: '0 12px 40px rgba(0,0,0,0.7)',
          }}>
            {data.symbols.map(s => (
              <div key={s.SYMBOL} onMouseDown={() => onSelect(s.SYMBOL)}
                style={{ padding: '10px 16px', cursor: 'pointer', borderBottom: `1px solid ${P.border}30`, display: 'flex', gap: 12, alignItems: 'baseline' }}
                onMouseEnter={e => (e.currentTarget.style.background = P.cell)}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                <span style={{ color: P.text, fontWeight: 800, fontFamily: 'monospace', fontSize: 13 }}>{s.SYMBOL}</span>
                <span style={{ color: P.sub, fontSize: 11 }}>{s.COMPANY_NAME}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 420 }}>
        <span style={{ fontSize: 10, color: P.dim, alignSelf: 'center' }}>Quick:</span>
        {QUICK.map(s => (
          <button key={s} onClick={() => onSelect(s)} style={{
            padding: '4px 12px', borderRadius: 6, fontSize: 11, fontWeight: 700,
            background: P.cell, border: `1px solid ${P.border}`,
            color: P.sub, cursor: 'pointer', fontFamily: 'monospace',
          }}>{s}</button>
        ))}
      </div>
    </div>
  )
}

// ─── Fundamentals tile grid ───────────────────────────────────────────────────

function FundTile({ label, value, sub, hdrBg, valColor }: {
  label: string; value: ReactNode; sub?: string; hdrBg: string; valColor?: string
}) {
  return (
    <div style={{ background: P.cell, border: `1px solid ${P.border}`, borderRadius: 8, overflow: 'hidden' }}>
      <div style={{ background: hdrBg, padding: '6px 11px', fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1.1, color: 'rgba(255,255,255,0.92)', textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ padding: '11px 11px 9px' }}>
        <div style={{ fontSize: FS['2xl'], fontWeight: FW.black, fontFamily: 'monospace', color: valColor ?? P.text, lineHeight: 1.1 }}>{value}</div>
        {sub && <div style={{ fontSize: FS.label, color: T.muted, marginTop: 5 }}>{sub}</div>}
      </div>
    </div>
  )
}

// ─── DMA row (technicals) ─────────────────────────────────────────────────────

function DMARow({ label, dma, close, color }: { label: string; dma: number | null; close: number; color: string }) {
  if (dma == null) return null
  const diff = (close - dma) / dma * 100
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 7 }}>
      <span style={{ color: P.dim, fontSize: 10, minWidth: 50 }}>{label}</span>
      <span style={{ color: P.sub, fontSize: 10, minWidth: 60, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        &#8377;{dma.toFixed(0)}
      </span>
      <span style={{ fontSize: 10, fontWeight: 700, minWidth: 48, color: diff >= 0 ? P.green : P.red, fontVariantNumeric: 'tabular-nums' }}>
        {diff >= 0 ? '+' : ''}{diff.toFixed(1)}%
      </span>
      <div style={{ flex: 1, height: 3, background: P.border, borderRadius: 2, maxWidth: 80 }}>
        <div style={{ width: `${Math.min(100, Math.abs(diff) / 20 * 100)}%`, height: '100%', background: color, opacity: diff >= 0 ? 1 : 0.4, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 10, color, fontWeight: 700, minWidth: 20 }}>{diff >= 0 ? 'ABV' : 'BLW'}</span>
    </div>
  )
}

// ─── Corporate Action color config ───────────────────────────────────────────

const CA_CFG: Record<string, { color: string; bg: string; label: string; marker: string }> = {
  DIVIDEND: { color: P.amber,  bg: '#F5A52414', label: 'Dividend',   marker: 'D' },
  BONUS:    { color: P.green,  bg: '#22D35E14', label: 'Bonus Issue',marker: 'B' },
  SPLIT:    { color: P.blue,   bg: '#4080FF14', label: 'Split',      marker: 'S' },
  BUYBACK:  { color: P.purple, bg: '#A855F714', label: 'Buyback',    marker: '$' },
  RIGHTS:   { color: P.teal,   bg: '#0EC4A014', label: 'Rights',     marker: 'R' },
}
function caDisplay(a: CorpAction): string {
  if (a.action_type === 'DIVIDEND' && a.dividend_rs != null) return `₹${a.dividend_rs.toFixed(2)}`
  if (a.action_type === 'BONUS'    && a.bonus_ratio  != null) return `1 : ${a.bonus_ratio.toFixed(0)}`
  if (a.action_type === 'SPLIT'    && a.split_new_fv != null) return `FV ₹${a.split_new_fv}`
  if (a.action_type === 'BUYBACK')                             return 'Offer'
  if (a.action_type === 'RIGHTS')                              return 'Rights'
  return a.subject.slice(0, 12)
}
function caUnit(a: CorpAction): string {
  if (a.action_type === 'DIVIDEND') return 'per share'
  if (a.action_type === 'BONUS')    return 'bonus per share held'
  if (a.action_type === 'SPLIT')    return 'new face value'
  if (a.action_type === 'BUYBACK')  return 'buyback scheme'
  if (a.action_type === 'RIGHTS')   return 'rights issue'
  return ''
}

function CorporateActionsSection({ symbol }: { symbol: string }) {
  const { data } = useQuery({
    queryKey: ['stock-ca', symbol],
    queryFn:  () => fetchStockCorpActions(symbol, 5),
    staleTime: 10 * 60_000,
  })
  const actions = data?.actions ?? []
  if (!actions.length) return null

  const summary = data?.summary ?? {}
  const chips = (['DIVIDEND','BONUS','SPLIT','BUYBACK','RIGHTS'] as const)
    .filter(k => (summary[k] ?? 0) > 0)
    .map(k => ({ k, count: summary[k] as number, cfg: CA_CFG[k] }))

  return (
    <div style={{ background: P.panel, border: `1px solid ${P.border}`, borderRadius: 10, overflow: 'hidden' }}>
      {/* header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', ...CARD_HEADER }}>
        <span>Corporate Actions</span>
        <div style={{ display: 'flex', gap: 6 }}>
          {chips.map(({ k, count, cfg }) => (
            <span key={k} style={{ fontSize: FS.caption, fontWeight: FW.bold, padding: '2px 8px', borderRadius: 10, background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}40` }}>
              {count} {cfg.label}{count > 1 ? 's' : ''}
            </span>
          ))}
        </div>
      </div>
      {/* horizontal scrollable rail */}
      <div style={{ display: 'flex', gap: 10, padding: '12px 14px', overflowX: 'auto', scrollbarWidth: 'thin' } as React.CSSProperties}>
        {actions.map((a, i) => {
          const cfg = CA_CFG[a.action_type] ?? { color: P.sub, bg: P.cell, label: a.action_type, marker: '?' }
          return (
            <div key={i} style={{ flexShrink: 0, width: 138, background: T.cell, border: `1px solid ${T.border}`, borderRadius: 8, overflow: 'hidden' }}>
              {/* colored type header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 10px', background: cfg.bg, fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1, textTransform: 'uppercase', color: cfg.color }}>
                <span style={{ width: 18, height: 18, borderRadius: '50%', background: cfg.color + '30', color: cfg.color, fontSize: 9, fontWeight: 900, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {cfg.marker}
                </span>
                {cfg.label}
              </div>
              {/* body */}
              <div style={{ padding: '9px 10px 8px' }}>
                <div style={{ fontSize: FS['2xl'], fontWeight: FW.black, fontFamily: 'monospace', color: cfg.color, lineHeight: 1, marginBottom: 3 }}>
                  {caDisplay(a)}
                </div>
                <div style={{ fontSize: FS.caption, color: T.muted, marginBottom: 6 }}>{caUnit(a)}</div>
                <div style={{ fontSize: 9, color: T.dim, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 1 }}>Ex-Date</div>
                <div style={{ fontSize: FS.caption, color: T.dim, fontFamily: 'monospace' }}>
                  {new Date(a.ex_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── AI summary renderer ──────────────────────────────────────────────────────

function AISummaryBody({ text, accentColor }: { text: string; accentColor: string }) {
  const LABELS = ['What happened:', 'What this means for the company:', 'Why you should care:']
  const parts = text.split(/\*\*(.+?)\*\*/)
  // parts alternates: [pre, label, body, label, body, ...]
  const sections: { label: string; body: string }[] = []
  for (let i = 1; i < parts.length - 1; i += 2) {
    const raw = parts[i].replace(/:$/, '').trim()
    const label = LABELS.find(l => l.toLowerCase().startsWith(raw.toLowerCase())) ?? raw + ':'
    sections.push({ label, body: (parts[i + 1] ?? '').trim() })
  }
  if (!sections.length) {
    return <div style={{ fontSize: 12, lineHeight: 1.55 }}>{text}</div>
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {sections.map(({ label, body }) => (
        <div key={label}>
          <span style={{ fontWeight: 700, color: accentColor, fontSize: 11 }}>{label} </span>
          <span style={{ fontSize: 12, lineHeight: 1.55 }}>{body}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Announcement timeline ────────────────────────────────────────────────────

const ANN_CLR: Record<string, string> = {
  BOARD_OUTCOME: '#A855F7', MANAGEMENT_CHANGE: P.red, ACQUISITION: P.amber,
  FUNDRAISE: P.blue, DIVIDEND: P.green, ORDER_WIN: P.green,
  DISTRESS: P.red, RESULT_UPDATE: P.teal, ANALYST_MEET: P.blue,
  REGULATORY: P.amber, CREDIT_RATING: P.amber, ESOP: P.sub,
  PRESS_RELEASE: P.dim, OTHER: P.dim,
}

function AnnRow({ a, i, last }: { a: Announcement; i: number; last: boolean }) {
  const [summary, setSummary]   = useState<string | null>(null)
  const [loading, setLoading]   = useState(false)
  const [error,   setError]     = useState<string | null>(null)
  const [open,    setOpen]      = useState(false)

  const tc = ANN_CLR[a.announcement_type] ?? P.sub
  const sc = a.signal_score == null ? T.dim : a.signal_score >= 75 ? P.green : a.signal_score >= 50 ? P.amber : T.dim

  const handleSummarise = async () => {
    if (summary) { setOpen(o => !o); return }
    setOpen(true)
    setLoading(true)
    setError(null)
    try {
      const res = await fetchAnnouncementSummary(a.pdf_url!, a.seq_id, a.title || a.desc)
      setSummary(res.summary)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })
        ?.response?.data?.detail ?? (e as { message?: string })?.message ?? 'Failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div key={a.seq_id || i} style={{
      padding: '9px 4px',
      borderBottom: !last ? `1px solid ${P.border}` : 'none',
    }}>
      {/* ── top row ── */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        {/* date + score */}
        <div style={{ minWidth: 76, flexShrink: 0 }}>
          <div style={{ fontSize: FS.label, color: T.muted, fontFamily: 'monospace', marginBottom: 4 }}>{a.date.slice(0, 10)}</div>
          {a.signal_score != null && (
            <span style={{ fontSize: FS.caption, fontWeight: FW.bold, padding: '1px 6px', borderRadius: 3, background: sc + '18', color: sc, border: `1px solid ${sc}33` }}>
              {a.signal_score}
            </span>
          )}
        </div>
        {/* type + title */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ marginBottom: 4 }}>
            <span style={{ fontSize: FS.caption, fontWeight: FW.bold, padding: '2px 7px', borderRadius: 3, background: tc + '18', color: tc, border: `1px solid ${tc}33`, letterSpacing: 0.3 }}>
              {a.announcement_type.replace(/_/g, ' ')}
            </span>
          </div>
          <div style={{ fontSize: FS.body, color: P.text, lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' } as React.CSSProperties}>
            {a.title || a.desc}
          </div>
        </div>
        {/* actions */}
        <div style={{ flexShrink: 0, alignSelf: 'center', display: 'flex', gap: 6 }}>
          {/* AI summary button — only when PDF available */}
          {a.pdf_url && (
            <button
              onClick={handleSummarise}
              title={summary ? (open ? 'Hide summary' : 'Show summary') : 'Read PDF & summarise'}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '4px 8px', borderRadius: 4, cursor: 'pointer',
                border: `1px solid ${P.amber}50`,
                background: open ? P.amber + '22' : P.amber + '10',
                color: P.amber, fontSize: 10, fontWeight: 700,
              }}
            >
              {loading
                ? <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
                : <span>AI</span>
              }
            </button>
          )}
          {/* PDF download */}
          {a.pdf_url && (
            <a href={a.pdf_url} target="_blank" rel="noopener noreferrer"
              style={{ display: 'flex', alignItems: 'center', padding: '5px 8px', borderRadius: 4, background: P.blue + '18', color: P.blue, border: `1px solid ${P.blue}40`, textDecoration: 'none' }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </a>
          )}
        </div>
      </div>

      {/* ── AI summary panel ── */}
      {open && (
        <div style={{
          marginTop: 8, marginLeft: 86,
          padding: '10px 12px', borderRadius: 6,
          background: P.amber + '0C', border: `1px solid ${P.amber}28`,
          fontSize: FS.body, color: P.text, lineHeight: 1.55,
        }}>
          {loading && <span style={{ color: P.dim }}>Reading PDF and generating analysis...</span>}
          {error   && <span style={{ color: P.red }}>Error: {error}</span>}
          {summary && !loading && <AISummaryBody text={summary} accentColor={P.amber} />}
        </div>
      )}
    </div>
  )
}

function AnnouncementsSection({ symbol }: { symbol: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['stock-ann', symbol],
    queryFn: () => fetchStockAnnouncements(symbol, 20),
    staleTime: 5 * 60_000,
  })
  if (isLoading) return <SectionCard title="Corporate Announcements"><span style={{ color: P.dim, fontSize: 11 }}>Loading...</span></SectionCard>
  const items: Announcement[] = data?.announcements ?? []
  if (!items.length) return null
  return (
    <SectionCard title={`Corporate Announcements — latest ${items.length} of ${data?.total ?? 0}`} accentColor={P.blue}>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {items.map((a, i) => (
          <AnnRow key={a.seq_id || i} a={a} i={i} last={i === items.length - 1} />
        ))}
      </div>
    </SectionCard>
  )
}

// ─── Governance Signal card ───────────────────────────────────────────────────

function GovernanceCard({ agm }: { agm: Record<string, string | number | null> }) {
  const [summary, setSummary] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const [open,    setOpen]    = useState(false)

  const risk = String(agm.governance_risk ?? '')
  const riskColor = risk === 'LOW' ? P.green : risk === 'HIGH' ? P.red : P.amber
  const pdfUrl  = agm.pdf_url  ? String(agm.pdf_url)  : null
  const seqId   = agm.seq_id   ? String(agm.seq_id)   : ''
  const keyDec  = agm.key_decision ? String(agm.key_decision) : ''

  const handleSummarise = async () => {
    if (!pdfUrl) return
    if (summary) { setOpen(o => !o); return }
    setOpen(true); setLoading(true); setError(null)
    try {
      const res = await fetchAnnouncementSummary(pdfUrl, seqId, keyDec)
      setSummary(res.summary)
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? 'Failed')
    } finally { setLoading(false) }
  }

  return (
    <SectionCard title={`Governance Signal${agm.date ? ` (${agm.date})` : ''}`} accentColor={riskColor}>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 10, alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
            {[
              { label: 'Risk',        value: risk, color: riskColor },
              { label: 'Dividend',    value: String(agm.dividend_signal ?? ''), color: P.green,  hide: String(agm.dividend_signal) === 'NONE' },
              { label: 'Mgmt Change', value: 'CHANGE',    color: P.amber, hide: String(agm.management_change) !== 'YES' },
              { label: 'Capex',       value: 'CONFIRMED', color: P.teal,  hide: String(agm.capex_confirm) !== 'YES' },
            ].filter(({ hide }) => !hide).map(({ label, value, color }) => value && (
              <div key={label}>
                <div style={LABEL}>{label}</div>
                <div style={{ marginTop: 5 }}><Chip label={value} color={color} size={11} /></div>
              </div>
            ))}
          </div>
          {keyDec && (
            <div style={{ fontSize: 11, color: P.text, background: P.cell, padding: '8px 12px', borderRadius: 6, border: `1px solid ${P.border}`, lineHeight: 1.55 }}>
              {keyDec}
            </div>
          )}
        </div>
        {/* Action buttons */}
        {pdfUrl && (
          <div style={{ display: 'flex', gap: 6, flexShrink: 0, alignSelf: 'flex-start', marginTop: 2 }}>
            <button onClick={handleSummarise} style={{ display: 'flex', alignItems: 'center', gap: 3, padding: '4px 9px', borderRadius: 4, cursor: 'pointer', border: `1px solid ${P.amber}50`, background: open ? P.amber + '22' : P.amber + '10', color: P.amber, fontSize: 10, fontWeight: 700 }}>
              {loading ? <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span> : 'AI'}
            </button>
            <a href={pdfUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', padding: '5px 8px', borderRadius: 4, background: P.blue + '18', color: P.blue, border: `1px solid ${P.blue}40`, textDecoration: 'none' }}>
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </a>
          </div>
        )}
      </div>
      {open && (
        <div style={{ padding: '10px 12px', borderRadius: 6, background: P.amber + '0C', border: `1px solid ${P.amber}28` }}>
          {loading && <span style={{ color: P.dim, fontSize: 11 }}>Reading PDF and generating analysis...</span>}
          {error   && <span style={{ color: P.red,  fontSize: 11 }}>Error: {error}</span>}
          {summary && !loading && <AISummaryBody text={summary} accentColor={P.amber} />}
        </div>
      )}
    </SectionCard>
  )
}

// ─── News article row ─────────────────────────────────────────────────────────

function NewsArticleRow({ art, last }: { art: NewsArticle; last: boolean }) {
  const [summary, setSummary] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const [open,    setOpen]    = useState(false)

  const sentColor = art.sentiment === 'BULLISH' ? P.green : art.sentiment === 'BEARISH' ? P.red : P.amber

  const handleSummarise = async () => {
    if (summary) { setOpen(o => !o); return }
    setOpen(true); setLoading(true); setError(null)
    try {
      const res = await fetchNewsArticleSummary(art.link, art.article_id, art.headline, art.themes)
      setSummary(res.summary)
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? 'Failed')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ padding: '9px 4px', borderBottom: !last ? `1px solid ${P.border}` : 'none' }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        {/* date + sentiment */}
        <div style={{ minWidth: 72, flexShrink: 0 }}>
          <div style={{ fontSize: 10, color: T.muted, fontFamily: 'monospace', marginBottom: 3 }}>{art.date}</div>
          <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 3, background: sentColor + '18', color: sentColor, border: `1px solid ${sentColor}33` }}>{art.sentiment || 'NEUTRAL'}</span>
        </div>
        {/* headline + source */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 11, color: P.text, lineHeight: 1.4, marginBottom: 3 }}>{art.headline}</div>
          <div style={{ fontSize: 10, color: P.dim }}>{art.source.replace(/_/g, ' ')}</div>
        </div>
        {/* buttons */}
        <div style={{ flexShrink: 0, display: 'flex', gap: 5, alignSelf: 'center' }}>
          <button onClick={handleSummarise} style={{ display: 'flex', alignItems: 'center', gap: 3, padding: '3px 7px', borderRadius: 3, cursor: 'pointer', border: `1px solid ${P.amber}50`, background: open ? P.amber + '22' : P.amber + '10', color: P.amber, fontSize: 10, fontWeight: 700 }}>
            {loading ? <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span> : 'AI'}
          </button>
          <a href={art.link} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', padding: '4px 7px', borderRadius: 3, background: P.blue + '18', color: P.blue, border: `1px solid ${P.blue}40`, textDecoration: 'none' }}>
            <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </a>
        </div>
      </div>
      {open && (
        <div style={{ marginTop: 8, marginLeft: 82, padding: '10px 12px', borderRadius: 6, background: P.amber + '0C', border: `1px solid ${P.amber}28` }}>
          {loading && <span style={{ color: P.dim, fontSize: 11 }}>Fetching article and generating analysis...</span>}
          {error   && <span style={{ color: P.red,  fontSize: 11 }}>Error: {error}</span>}
          {summary && !loading && <AISummaryBody text={summary} accentColor={P.amber} />}
        </div>
      )}
    </div>
  )
}

// ─── News signal card ─────────────────────────────────────────────────────────

function NewsCard({ news }: { news: Record<string, string | number | null | unknown[]> }) {
  const articles = (news.recent_articles ?? []) as NewsArticle[]
  const sentLabel = String(news.sentiment_label ?? '')
  const sentColor = sentLabel === 'BULLISH' ? P.green : sentLabel === 'BEARISH' ? P.red : P.amber

  return (
    <SectionCard title="Recent News Signal" accentColor={P.blue}>
      {/* stats row */}
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: articles.length ? 12 : 0 }}>
        {[
          { label: 'Articles (7D)', value: String(news.news_count_7d), color: P.text },
          { label: 'Sentiment',     value: sentLabel, color: sentColor },
          { label: 'Bullish',       value: String(news.bullish_count ?? 0), color: P.green },
          { label: 'Bearish',       value: String(news.bearish_count ?? 0), color: P.red },
        ].map(({ label, value, color }) => (
          <div key={label}>
            <div style={LABEL}>{label}</div>
            <div style={{ fontSize: 16, fontWeight: 800, color, marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{value || '--'}</div>
          </div>
        ))}
      </div>
      {news.top_theme && (
        <div style={{ marginBottom: articles.length ? 12 : 0, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ ...LABEL, alignSelf: 'center' }}>Themes:</span>
          {String(news.top_theme).split(',').map(th => (
            <Chip key={th.trim()} label={th.trim()} color={P.blue} size={9} />
          ))}
        </div>
      )}
      {/* article list */}
      {articles.length > 0 && (
        <div style={{ borderTop: `1px solid ${P.border}`, paddingTop: 8 }}>
          {articles.map((art, i) => (
            <NewsArticleRow key={art.article_id || i} art={art} last={i === articles.length - 1} />
          ))}
        </div>
      )}
    </SectionCard>
  )
}

// ─── Participant Caution Banner ───────────────────────────────────────────────

const PARTICIPANT_CFG: Record<string, { color: string; label: string; icon: string }> = {
  FII:         { color: '#4FC3F7', label: 'FII',         icon: 'F' },
  DII:         { color: '#81C784', label: 'DII',         icon: 'D' },
  SMART_MONEY: { color: '#CE93D8', label: 'SMART MONEY', icon: 'S' },
  MIXED:       { color: '#FFD54F', label: 'MIXED',       icon: 'M' },
  RETAIL:      { color: '#FF8A65', label: 'RETAIL',      icon: 'R' },
  NONE:        { color: '#607D8B', label: 'NONE',        icon: '?' },
}

function ParticipantCautionBanner({ label, drivingParticipant }: {
  label: string
  drivingParticipant: string
}) {
  const dp = drivingParticipant?.toUpperCase() || 'NONE'
  const cfg = PARTICIPANT_CFG[dp] ?? PARTICIPANT_CFG['NONE']
  const isRisky = (label === 'BULL_RUN' || label === 'EMERGING') && (dp === 'RETAIL' || dp === 'NONE')
  const isAccumPhase = label === 'ACCUMULATION'
  const isInstitutional = dp === 'FII' || dp === 'DII' || dp === 'SMART_MONEY'

  if (dp === 'MIXED' && !isAccumPhase) return null  // mixed signal — no strong message

  const borderColor  = isRisky ? '#FF8A65' : isAccumPhase ? '#9575CD' : isInstitutional ? cfg.color : P.border
  const bgColor      = isRisky ? '#FF8A6508' : isAccumPhase ? '#9575CD08' : isInstitutional ? cfg.color + '08' : 'transparent'
  const accentColor  = isRisky ? '#FF8A65' : isAccumPhase ? '#9575CD' : cfg.color

  return (
    <div style={{
      background: bgColor,
      border: `1px solid ${borderColor}44`,
      borderLeft: `3px solid ${accentColor}`,
      borderRadius: 6, padding: '10px 14px',
      display: 'flex', alignItems: 'flex-start', gap: 12,
    }}>
      {/* Participant badge */}
      <div style={{
        width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
        background: cfg.color + '22', border: `1px solid ${cfg.color}55`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 11, fontWeight: 900, color: cfg.color, fontFamily: 'monospace',
      }}>{cfg.icon}</div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: accentColor, letterSpacing: 0.8 }}>
            {isRisky ? 'DISTRIBUTION RISK' : isAccumPhase ? 'WYCKOFF ACCUMULATION' : isInstitutional ? 'INSTITUTIONAL BACKING' : 'PARTICIPANT SIGNAL'}
          </span>
          <span style={{
            fontSize: 9, fontWeight: 700, padding: '1px 7px', borderRadius: 8,
            background: cfg.color + '18', color: cfg.color, border: `1px solid ${cfg.color}44`,
            letterSpacing: 0.5,
          }}>{cfg.label} DRIVEN</span>
        </div>
        <div style={{ fontSize: 11, color: isRisky ? '#FFCCBC' : isAccumPhase ? '#CE93D8' : P.sub, lineHeight: 1.55 }}>
          {isAccumPhase && isInstitutional && (
            `Wyckoff Accumulation Phase: ${cfg.label} is quietly building a position in this sector while the stock remains in a base. Price has not yet moved — this is the "boring" phase before breakout. Patient entry; wait for volume expansion confirming the move.`
          )}
          {isAccumPhase && !isInstitutional && dp === 'RETAIL' && (
            'Stock is in base-building phase with sector institutional flow near neutral. No strong institutional accumulation detected yet — watch for volume expansion and sector rotation signals before entry.'
          )}
          {isRisky && dp === 'RETAIL' && (
            'FII and DII are not accumulating in this sector. This move is driven by retail momentum — characteristic of the Wyckoff Distribution phase. Smart money may be quietly exiting while retail FOMO drives prices higher. Exercise position sizing caution.'
          )}
          {isRisky && dp === 'NONE' && (
            'No institutional participant is driving this sector. Price appreciation lacks institutional conviction — high reversal risk if retail sentiment shifts.'
          )}
          {!isRisky && !isAccumPhase && dp === 'FII' && (
            'Foreign Institutional Investors are accumulating in this sector. FII-backed moves tend to have stronger follow-through and lower reversal risk.'
          )}
          {!isRisky && !isAccumPhase && dp === 'DII' && (
            'Domestic Institutional Investors (MFs, Insurance) are accumulating. DII flows indicate domestic conviction and provide structural price support.'
          )}
          {!isRisky && !isAccumPhase && dp === 'SMART_MONEY' && (
            'Professional / Smart Money participants are the dominant buyers in this sector. Institutional conviction is high.'
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Investment Thesis Card ───────────────────────────────────────────────────

type Thesis = NonNullable<import('../api/client').Stock['structured_thesis']>

function InvestmentThesisCard({ thesis, drivingParticipant }: {
  thesis: Thesis
  drivingParticipant?: string
}) {
  const VERDICT_CFG: Record<string, { color: string; label: string }> = {
    BULL_RUN:     { color: P.green,  label: 'BULL RUN'     },
    EMERGING:     { color: P.teal,   label: 'EMERGING'     },
    WATCHLIST:    { color: P.blue,   label: 'WATCHLIST'    },
    NEUTRAL:      { color: P.amber,  label: 'NEUTRAL'      },
    ACCUMULATION: { color: '#9575CD', label: 'ACCUMULATION' },
    MARKDOWN:     { color: P.red,    label: 'MARKDOWN'     },
  }
  const cfg     = VERDICT_CFG[thesis.verdict] ?? { color: P.sub, label: thesis.verdict }
  const confClr = thesis.confidence === 'HIGH' ? P.green : thesis.confidence === 'MEDIUM' ? P.amber : P.red

  const dp    = drivingParticipant?.toUpperCase() || 'NONE'
  const dpCfg = PARTICIPANT_CFG[dp] ?? PARTICIPANT_CFG['NONE']

  return (
    <div style={{
      background: '#090F1E', border: `1px solid ${cfg.color}44`,
      borderLeft: `4px solid ${cfg.color}`, borderRadius: 8, padding: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
        <div style={{
          background: cfg.color + '22', border: `1px solid ${cfg.color}55`,
          borderRadius: 6, padding: '5px 14px',
          fontSize: 13, fontWeight: 900, color: cfg.color, letterSpacing: 1.5,
        }}>{cfg.label}</div>
        <div style={{ fontSize: 20, fontWeight: 900, color: cfg.color, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>
          {thesis.score.toFixed(0)}<span style={{ fontSize: 11, fontWeight: 400, color: P.dim }}>/100</span>
        </div>
        <span style={{ fontSize: 9, fontWeight: 700, color: confClr, background: confClr + '18', border: `1px solid ${confClr}44`, borderRadius: 3, padding: '2px 7px', letterSpacing: 0.5 }}>
          {thesis.confidence} CONFIDENCE
        </span>
        {/* Participant driver chip */}
        {dp && dp !== 'NONE' && (
          <span style={{
            fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 8,
            background: dpCfg.color + '18', color: dpCfg.color, border: `1px solid ${dpCfg.color}44`,
            letterSpacing: 0.5,
          }}>
            {dpCfg.label}
          </span>
        )}
        <div style={{ marginLeft: 'auto', fontSize: 9, color: P.dim, letterSpacing: 0.8 }}>INVESTMENT THESIS</div>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: (thesis.conflict_note || thesis.dominant_factor) ? 12 : 0 }}>
        {thesis.bull_signals.map(s => (
          <span key={s} style={{ fontSize: 10, fontWeight: 700, padding: '3px 9px', borderRadius: 10, background: P.green + '18', color: P.green, border: `1px solid ${P.green}44` }}>
            + {s}
          </span>
        ))}
        {thesis.bear_signals.map(s => (
          <span key={s} style={{ fontSize: 10, fontWeight: 700, padding: '3px 9px', borderRadius: 10, background: P.red + '18', color: P.red, border: `1px solid ${P.red}44` }}>
            - {s}
          </span>
        ))}
        {thesis.bull_signals.length === 0 && thesis.bear_signals.length === 0 && (
          <span style={{ fontSize: 10, color: P.dim }}>Insufficient signal data for chip analysis</span>
        )}
      </div>

      {thesis.conflict_note && (
        <div style={{ fontSize: 11, color: P.amber, background: P.amber + '0C', border: `1px solid ${P.amber}28`, borderRadius: 5, padding: '8px 12px', marginBottom: 8, lineHeight: 1.55 }}>
          {thesis.conflict_note}
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {thesis.dominant_factor && (
          <div style={{ fontSize: 10, color: P.sub }}>
            <span style={{ color: P.dim, marginRight: 4 }}>Driver:</span>{thesis.dominant_factor}
          </div>
        )}
        {thesis.ml_note && (
          <div style={{ fontSize: 10, color: P.dim }}>
            <span style={{ color: P.purple, marginRight: 4 }}>ML:</span>{thesis.ml_note}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Key Levels Card ──────────────────────────────────────────────────────────

type KeyLevels = NonNullable<import('../api/client').Stock['key_levels']>

function KeyLevelsCard({ kl, close }: { kl: KeyLevels; close: number }) {
  const fmt = (v: number | null) =>
    v != null ? `₹${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '--'
  const pctFrom = (v: number | null) => {
    if (v == null || close <= 0) return ''
    const p = (v - close) / close * 100
    return `${p >= 0 ? '+' : ''}${p.toFixed(1)}%`
  }

  const lo  = kl.conf_sup_1 ?? (close - (kl.atr_14 ?? 0) * 3)
  const hi  = kl.conf_res_1 ?? (close + (kl.atr_14 ?? 0) * 3)
  const pos = (lo < hi) ? Math.max(0, Math.min(100, (close - lo) / (hi - lo) * 100)) : 50

  function TagRow({ tags, color }: { tags: string; color: string }) {
    if (!tags) return null
    return (
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
        {tags.split('|').map(t => t.trim()).filter(Boolean).map(t => (
          <span key={t} style={{ fontSize: 8, fontWeight: 700, padding: '1px 6px', borderRadius: 8, background: color + '18', color, border: `1px solid ${color}33`, letterSpacing: 0.3 }}>
            {t}
          </span>
        ))}
      </div>
    )
  }

  return (
    <SectionCard title="Key Support & Resistance Levels" accentColor={P.teal}>
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: P.dim, marginBottom: 5 }}>
          <span>S1 {fmt(kl.conf_sup_1)}</span>
          <span style={{ color: P.text, fontWeight: 700 }}>Now {fmt(close)}</span>
          <span>R1 {fmt(kl.conf_res_1)}</span>
        </div>
        <div style={{ height: 6, background: '#1A2740', borderRadius: 3, position: 'relative' }}>
          <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(to right, ${P.red}44, ${P.border}, ${P.green}44)`, borderRadius: 3 }} />
          {kl.entry_zone_low != null && kl.entry_zone_high != null && lo < hi && (
            <div style={{
              position: 'absolute',
              left: `${Math.max(0, (kl.entry_zone_low - lo) / (hi - lo) * 100)}%`,
              right: `${Math.max(0, 100 - (kl.entry_zone_high - lo) / (hi - lo) * 100)}%`,
              height: '100%', background: P.teal + '55', borderRadius: 3,
            }} />
          )}
          <div style={{ position: 'absolute', top: -4, left: `${pos}%`, width: 14, height: 14, borderRadius: '50%', background: pos >= 70 ? P.green : pos >= 30 ? P.amber : P.red, transform: 'translateX(-50%)', border: `2px solid ${P.bg}`, boxShadow: `0 0 6px ${pos >= 70 ? P.green : pos >= 30 ? P.amber : P.red}88` }} />
        </div>
      </div>

      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 9, color: P.dim, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>Resistance</div>
        {[
          { price: kl.conf_res_1, score: kl.conf_res_1_score, tags: kl.conf_res_1_tags, rank: 'R1' },
          { price: kl.conf_res_2, score: kl.conf_res_2_score, tags: kl.conf_res_2_tags, rank: 'R2' },
        ].filter(l => l.price != null).map(l => (
          <div key={l.rank} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: 9, fontWeight: 800, color: P.red, background: P.red + '18', border: `1px solid ${P.red}33`, borderRadius: 3, padding: '1px 6px', flexShrink: 0 }}>{l.rank}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: P.red, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{fmt(l.price)}</span>
                <span style={{ fontSize: 10, color: P.dim }}>{pctFrom(l.price)}</span>
                {l.score != null && <span style={{ fontSize: 9, color: P.amber, marginLeft: 'auto' }}>confluence {l.score}</span>}
              </div>
              <TagRow tags={l.tags ?? ''} color={P.red} />
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 9, color: P.dim, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>Support</div>
        {[
          { price: kl.conf_sup_1, score: kl.conf_sup_1_score, tags: kl.conf_sup_1_tags, rank: 'S1' },
          { price: kl.conf_sup_2, score: kl.conf_sup_2_score, tags: kl.conf_sup_2_tags, rank: 'S2' },
        ].filter(l => l.price != null).map(l => (
          <div key={l.rank} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: 9, fontWeight: 800, color: P.green, background: P.green + '18', border: `1px solid ${P.green}33`, borderRadius: 3, padding: '1px 6px', flexShrink: 0 }}>{l.rank}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: P.green, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{fmt(l.price)}</span>
                <span style={{ fontSize: 10, color: P.dim }}>{pctFrom(l.price)}</span>
                {l.score != null && <span style={{ fontSize: 9, color: P.amber, marginLeft: 'auto' }}>confluence {l.score}</span>}
              </div>
              <TagRow tags={l.tags ?? ''} color={P.green} />
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: P.cell, border: `1px solid ${P.border}`, borderRadius: 6, padding: '9px 12px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        {[
          { label: 'Entry Zone',  value: kl.entry_zone_low != null && kl.entry_zone_high != null ? `${fmt(kl.entry_zone_low)}–${fmt(kl.entry_zone_high)}` : '--', color: P.teal },
          { label: 'Stop Loss',   value: fmt(kl.stop_loss),   color: P.red   },
          { label: 'ATR (14D)',   value: kl.atr_14 != null ? `₹${kl.atr_14.toFixed(1)}` : '--', color: P.sub },
        ].map(({ label, value, color }) => (
          <div key={label}>
            <div style={{ fontSize: 10, color: P.dim, letterSpacing: 0.5, marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 11, fontWeight: 800, color, fontFamily: 'monospace' }}>{value}</div>
          </div>
        ))}
      </div>
      {kl.as_of_date && (
        <div style={{ fontSize: 9, color: P.dim, marginTop: 8 }}>
          Fib + Pivot + Volume Profile + Swing confluence · as of {kl.as_of_date}
        </div>
      )}
    </SectionCard>
  )
}

// ─── Valuation Context Card ───────────────────────────────────────────────────

type PeerVal = NonNullable<import('../api/client').Stock['sector_peer_valuation']>

function ValuationContextCard({ fundamentals, peers }: {
  fundamentals: Record<string, number | string | null>
  peers: PeerVal
}) {
  const metrics = [
    { label: 'P/E Ratio', stock: fundamentals.pe_ratio,  peer: peers.sector_pe,   unit: 'x', good: 'low'  },
    { label: 'ROE (%)',   stock: fundamentals.roe_pct,   peer: peers.sector_roe,  unit: '%', good: 'high' },
    { label: 'ROCE (%)',  stock: fundamentals.roce_pct,  peer: peers.sector_roce, unit: '%', good: 'high' },
  ].filter(m => m.stock != null || m.peer != null)

  if (!metrics.length) return null

  return (
    <SectionCard title={`Valuation vs ${peers.sector ?? 'Sector'} Median (${peers.peer_count ?? 0} peers)`} accentColor={P.purple}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {metrics.map(({ label, stock, peer, unit, good }) => {
          const sv = stock != null ? +stock : null
          const pv = peer  != null ? +peer  : null
          const vsStr = sv != null && pv != null
            ? (good === 'low'
                ? (sv < pv * 0.85 ? 'cheaper than sector' : sv > pv * 1.2 ? 'more expensive' : 'in-line')
                : (sv > pv * 1.1  ? 'better than sector'  : sv < pv * 0.8 ? 'below sector'  : 'in-line'))
            : ''
          const vsClr = (vsStr === 'cheaper than sector' || vsStr === 'better than sector') ? P.green
            : (vsStr === 'more expensive' || vsStr === 'below sector') ? P.red : P.amber
          const barMax = Math.max(sv ?? 0, pv ?? 0, 5) * 1.15
          return (
            <div key={label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                <span style={{ fontSize: 10, color: P.sub }}>{label}</span>
                {vsStr && <span style={{ fontSize: 9, fontWeight: 700, color: vsClr }}>{vsStr}</span>}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {sv != null && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 9, color: P.dim, minWidth: 34 }}>Stock</span>
                    <div style={{ flex: 1, height: 8, background: P.border, borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, sv / barMax * 100)}%`, height: '100%', background: P.blue, borderRadius: 4 }} />
                    </div>
                    <span style={{ fontSize: 10, fontWeight: 800, color: P.blue, fontVariantNumeric: 'tabular-nums', minWidth: 38, textAlign: 'right' }}>{sv.toFixed(1)}{unit}</span>
                  </div>
                )}
                {pv != null && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 9, color: P.dim, minWidth: 34 }}>Sector</span>
                    <div style={{ flex: 1, height: 8, background: P.border, borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, pv / barMax * 100)}%`, height: '100%', background: P.dim, borderRadius: 4 }} />
                    </div>
                    <span style={{ fontSize: 10, fontWeight: 800, color: P.dim, fontVariantNumeric: 'tabular-nums', minWidth: 38, textAlign: 'right' }}>{pv.toFixed(1)}{unit}</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </SectionCard>
  )
}

// ─── Upcoming Catalysts Card ──────────────────────────────────────────────────

function UpcomingCatalystsCard({ events }: { events: Array<{ event_date: string; purpose_type: string; bm_desc: string }> }) {
  if (!events.length) return null
  const TYPE_CLR: Record<string, string> = {
    RESULTS: P.green, DIVIDEND: P.amber, AGM: P.purple,
    EGM: P.blue, BUYBACK: P.teal, OTHER: P.dim,
  }

  return (
    <SectionCard title={`Upcoming Catalysts — next 90 days (${events.length})`} accentColor={P.amber}>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {events.map((ev, i) => {
          const clr = TYPE_CLR[ev.purpose_type] ?? P.sub
          const daysFrom = Math.round((new Date(ev.event_date).getTime() - Date.now()) / 86400000)
          return (
            <div key={i} style={{ display: 'flex', gap: 10, padding: '9px 0', borderBottom: i < events.length - 1 ? `1px solid ${P.border}` : 'none', alignItems: 'flex-start' }}>
              <div style={{ minWidth: 60, flexShrink: 0 }}>
                <div style={{ fontSize: 11, fontWeight: 800, color: P.text, fontFamily: 'monospace' }}>{ev.event_date.slice(5)}</div>
                <div style={{ fontSize: 9, color: daysFrom <= 14 ? P.amber : P.dim }}>in {daysFrom}d</div>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ marginBottom: 4 }}>
                  <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 8, background: clr + '18', color: clr, border: `1px solid ${clr}33`, letterSpacing: 0.3 }}>
                    {ev.purpose_type.replace(/_/g, ' ')}
                  </span>
                </div>
                {ev.bm_desc && ev.bm_desc.length > 4 && (
                  <div style={{ fontSize: 10, color: P.sub, lineHeight: 1.45, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' } as React.CSSProperties}>
                    {ev.bm_desc.replace(/=+/g, '').trim()}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </SectionCard>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function StocksPage() {
  const isMobile = useMobile()
  const { symbol: urlSym } = useParams<{ symbol?: string }>()
  const navigate = useNavigate()

  const [symbol, setSymbol] = useState(urlSym?.toUpperCase() ?? '')
  const [tf, setTf]         = useState<TF>('1D')
  const [input, setInput]   = useState(urlSym?.toUpperCase() ?? '')
  const [showDrop, setShowDrop] = useState(false)
  const [acQ, setAcQ]       = useState('')
  const [chartErr, setChartErr] = useState<string | null>(null)
  const [chartKey, setChartKey] = useState(0)   // increments each time chart is (re)created
  const [snapFlash, setSnapFlash] = useState(false)
  const [hoverBar, setHoverBar] = useState<{ time: Time; open: number; high: number; low: number; close: number; volume: number } | null>(null)

  const chartDiv  = useRef<HTMLDivElement>(null)
  const chartApi  = useRef<IChartApi | null>(null)
  const candleRef = useRef<ISeriesApi<'Candlestick', Time> | null>(null)
  const barCount  = useRef(0)
  // Volume is shown only in the OHLCV footer, not as a chart pane -- this
  // map (time -> volume) feeds the footer's hover lookup without needing a
  // rendered HistogramSeries.
  const volumeByTime = useRef<Map<Time, number>>(new Map())
  // Render-phase snapshot refs — updated every render so chart init can read
  // the current ohlcv/tf WITHOUT waiting for the data effect to fire again.
  // This is the correct fix for StrictMode's double-invoke blank chart bug.
  const latestOhlcvRef = useRef<OhlcvResponse | undefined>(undefined)
  const latestTfRef    = useRef<TF>('1D')

  // Sync when navigating from Watchlist (/stocks/:symbol)
  useEffect(() => {
    const s = urlSym?.toUpperCase() ?? ''
    setSymbol(s); setInput(s)
  }, [urlSym])

  // ── Data queries ─────────────────────────────────────────────────────────

  const { data: acData } = useQuery({
    queryKey: ['stocks-ac', acQ],
    queryFn: () => fetchAC(acQ),
    enabled: showDrop && acQ.length > 0,
    staleTime: 30_000,
  })

  const { data: ohlcv, isLoading: chartLoading, isError: chartFailed, error: chartErrObj } = useQuery({
    queryKey: ['stocks-ohlcv', symbol, tf],
    queryFn: () => fetchOhlcv(symbol, tf),
    enabled: !!symbol,
    staleTime: 5 * 60_000, retry: 1,
  })

  const { data: sig } = useQuery({
    queryKey: ['stocks-sig', symbol],
    queryFn: () => fetchCSignal(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockDetail(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })

  const { data: corpActions } = useQuery({
    queryKey: ['stock-ca', symbol],
    queryFn: () => fetchStockCorpActions(symbol, 5),
    enabled: !!symbol,
    staleTime: 10 * 60_000,
  })

  // ── Chart lifecycle ───────────────────────────────────────────────────────

  // Chart init re-runs when symbol changes.
  // React Router v6 reuses this component instance when navigating from /stocks
  // (no symbol) to /stocks/:symbol, so [] would only run once with chartDiv=null.
  // Adding symbol as a dep ensures chart is created the moment the full view mounts.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!chartDiv.current || !symbol) return
    setChartErr(null)
    let chart: IChartApi | null = null
    try {
      chart = createChart(chartDiv.current, {
        autoSize: true,
        layout: { background: { type: ColorType.Solid, color: P.bg }, textColor: P.sub, fontSize: 10, fontFamily: 'monospace' },
        grid: { vertLines: { color: P.border }, horzLines: { color: P.border } },
        crosshair: { vertLine: { labelBackgroundColor: P.cell }, horzLine: { labelBackgroundColor: P.cell } },
        rightPriceScale: { borderColor: P.border },
        timeScale: { borderColor: P.border, timeVisible: false, secondsVisible: false },
        handleScroll: true, handleScale: true,
      })
      const candles = chart.addSeries(CandlestickSeries, {
        upColor: P.green, downColor: P.red, borderVisible: false, wickUpColor: P.green, wickDownColor: P.red,
        // lightweight-charts draws a permanent dashed line at the last close
        // by default (priceLineVisible: true) -- it never moves with the
        // cursor and was being mistaken for a frozen crosshair. The actual
        // crosshair (which does track the cursor) is a separate, built-in
        // feature that renders regardless of this setting.
        priceLineVisible: false,
      })
      chartApi.current = chart; candleRef.current = candles
      setChartKey(k => k + 1)

      // Drive the OHLCV footer from whatever bar is under the cursor,
      // instead of it always showing the latest bar regardless of hover.
      // Volume comes from volumeByTime (no rendered volume series).
      chart.subscribeCrosshairMove(param => {
        if (!param.time) { setHoverBar(null); return }
        const cs = param.seriesData.get(candles) as CandlestickData<Time> | undefined
        if (!cs) { setHoverBar(null); return }
        setHoverBar({
          time: param.time as Time,
          open: cs.open, high: cs.high, low: cs.low, close: cs.close,
          volume: volumeByTime.current.get(param.time as Time) ?? 0,
        })
      })

      // Apply data immediately if already in cache — this is the critical path.
      // The data effect [ohlcv, tf, chartKey] may not re-fire if the deps haven't
      // changed (StrictMode recreates the chart but ohlcv/tf are the same object).
      // Reading latestOhlcvRef (set synchronously during render) is always current.
      const snap = latestOhlcvRef.current
      if (snap?.bars?.length) {
        const tfNow = latestTfRef.current
        const cs = snap.bars.map(b => ({
          time: (typeof b.time === 'string' ? toPeriodStart(b.time, tfNow) : b.time) as Time,
          open: b.open, high: b.high, low: b.low, close: b.close,
        }))
        candles.setData(cs)
        volumeByTime.current = new Map(cs.map((c, i) => [c.time, snap.bars[i].volume ?? 0]))
        barCount.current = cs.length
        if (cs.length > 0) chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, cs.length - DEFAULT_BARS[tfNow]), to: cs.length + 3 })
      }
    } catch (e) { setChartErr(e instanceof Error ? e.message : String(e)); chart?.remove() }
    return () => { chartApi.current?.remove(); chartApi.current = candleRef.current = null }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol])

  useEffect(() => {
    chartApi.current?.applyOptions({ timeScale: { timeVisible: INTRADAY.has(tf), secondsVisible: false } })
  }, [tf])

  useEffect(() => {
    if (!ohlcv || !candleRef.current) return
    try {
      const bars = ohlcv.bars
      const cs: CandlestickData<Time>[] = bars.map(b => ({
        time: (typeof b.time === 'string' ? toPeriodStart(b.time, tf) : b.time) as Time,
        open: b.open, high: b.high, low: b.low, close: b.close,
      }))
      candleRef.current.setData(cs)
      volumeByTime.current = new Map(cs.map((c, i) => [c.time, bars[i].volume ?? 0]))
      barCount.current = cs.length
      if (cs.length > 0 && chartApi.current)
        chartApi.current.timeScale().setVisibleLogicalRange({ from: Math.max(0, cs.length - DEFAULT_BARS[tf]), to: cs.length + 3 })
    } catch (e) { setChartErr(e instanceof Error ? e.message : String(e)) }
  }, [ohlcv, tf, chartKey])

  // ── Corporate action markers on chart ─────────────────────────────────────
  // Renders colored circles below candle bars at the ex-date of each CA event.
  useEffect(() => {
    if (!candleRef.current || !corpActions?.actions?.length) return
    const CA_MARKER_CFG: Record<string, { color: string; text: string }> = {
      DIVIDEND: { color: P.amber,  text: 'D' },
      BONUS:    { color: P.green,  text: 'B' },
      SPLIT:    { color: P.blue,   text: 'S' },
      BUYBACK:  { color: P.purple, text: '$' },
      RIGHTS:   { color: P.teal,   text: 'R' },
    }
    try {
      const markers = corpActions.actions
        .filter(a => CA_MARKER_CFG[a.action_type])
        .map(a => {
          const cfg = CA_MARKER_CFG[a.action_type]
          // For daily/weekly TF, ex_date maps directly to a 'YYYY-MM-DD' time
          const dateStr = a.ex_date.slice(0, 10)
          const label = a.action_type === 'DIVIDEND' && a.dividend_rs != null
            ? `Div ₹${a.dividend_rs}`
            : a.action_type === 'BONUS' && a.bonus_ratio != null
            ? `Bonus ${a.bonus_ratio}:1`
            : a.action_type === 'SPLIT' && a.split_new_fv != null
            ? `Split FV ${a.split_new_fv}`
            : cfg.text
          return {
            time:     dateStr as Time,
            position: 'belowBar' as const,
            color:    cfg.color,
            shape:    'circle' as const,
            text:     label,
            size:     0.8,
          }
        })
        .sort((a, b) => String(a.time).localeCompare(String(b.time)))
      candleRef.current.setMarkers(markers)
    } catch { /* markers are cosmetic — ignore failures */ }
  }, [corpActions, chartKey])

  const resetChart = useCallback(() => {
    if (!chartApi.current) return
    chartApi.current.timeScale().setVisibleLogicalRange({ from: Math.max(0, barCount.current - DEFAULT_BARS[tf]), to: barCount.current + 3 })
  }, [tf])

  const takeSnapshot = useCallback(() => {
    if (!chartApi.current || !symbol) return
    try {
      const canvas = chartApi.current.takeScreenshot()
      const a = document.createElement('a')
      a.href = canvas.toDataURL('image/png')
      a.download = `${symbol.toUpperCase()}-${tf}-${new Date().toISOString().slice(0, 10)}.png`
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      setSnapFlash(true); setTimeout(() => setSnapFlash(false), 800)
    } catch { /* ignore -- chart not ready */ }
  }, [symbol, tf])

  // ── Symbol selection ──────────────────────────────────────────────────────

  const selectSymbol = useCallback((s: string) => {
    const sym = s.trim().toUpperCase(); if (!sym) return
    setSymbol(sym); setInput(sym); setShowDrop(false); setAcQ('')
    navigate(`/stocks/${sym}`, { replace: true })
  }, [navigate])

  // ── Derived values ────────────────────────────────────────────────────────

  const latest        = ohlcv?.bars.at(-1)
  const prev          = ohlcv?.bars.at(-2)
  const priceChg      = latest && prev ? ((latest.close - prev.close) / prev.close) * 100 : null
  const priceChgAbs   = latest && prev ? latest.close - prev.close : null
  // Fall back to API-provided 1D change when OHLCV not loaded yet
  const chg1dPct  = priceChg ?? (detail?.price?.change_1d_pct ?? null)
  const chg1dAbs  = priceChgAbs ?? (detail?.price?.change_1d_abs ?? null)
  const close     = detail?.close_now ?? latest?.close ?? 0
  const t        = detail?.technical as TechnicalIndicators | undefined
  const f        = detail?.fno as FnoData | undefined
  const fund     = (detail?.fundamentals ?? {}) as Record<string, number | string | null>
  const shp      = (detail?.shareholding ?? {}) as Record<string, number | string | null>
  type KV = Record<string, string | number | null>
  const trends   = Array.isArray(detail?.holding_trends) ? detail!.holding_trends as KV[] : []
  const mgmt     = (detail?.management ?? {}) as KV
  const concall  = (detail?.concall ?? {}) as KV
  const agm      = (detail?.agm ?? {}) as KV
  const news     = (detail?.news ?? {}) as KV
  const consensus = (detail?.consensus ?? {}) as KV
  const insights  = detail?.analyst_insights as string[] | undefined

  const trendColor = t?.trend_signal === 'STRONG_UPTREND' ? P.green
    : t?.trend_signal === 'UPTREND' ? P.teal
    : t?.trend_signal === 'CONSOLIDATING' ? P.amber
    : t?.trend_signal ? P.red : P.dim

  // Update render-phase snapshot refs every render (before any early return)
  // so the chart init effect always has the latest ohlcv/tf values.
  latestOhlcvRef.current = ohlcv
  latestTfRef.current    = tf

  // ── No-symbol state ───────────────────────────────────────────────────────

  if (!symbol) return (
    <div style={{ background: P.bg, minHeight: '100%' }}>
      <SearchPrompt onSelect={selectSymbol} />
    </div>
  )

  // ── Full view ─────────────────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0, background: P.bg }}>

      {/* ── Stock header: search + price ─────────────────────────────── */}
      <div style={{
        background: P.panel, borderBottom: `1px solid ${P.border}`,
        padding: '10px 0', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
      }}>
        {/* Symbol search */}
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <input
            value={input}
            onChange={e => { setInput(e.target.value.toUpperCase()); setAcQ(e.target.value.toUpperCase()); setShowDrop(true) }}
            onKeyDown={e => { if (e.key === 'Enter') selectSymbol(input); if (e.key === 'Escape') setShowDrop(false) }}
            onFocus={() => { setShowDrop(true); setAcQ(input) }}
            onBlur={() => setTimeout(() => setShowDrop(false), 160)}
            style={{
              background: P.cell, border: `1px solid ${P.litBdr}`, borderRadius: 5,
              color: P.text, padding: '6px 12px', fontSize: 14, fontFamily: 'monospace',
              fontWeight: 800, width: 140, outline: 'none', letterSpacing: 1,
            }}
          />
          {showDrop && acData?.symbols && acData.symbols.length > 0 && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, zIndex: 300, marginTop: 3,
              background: '#0D1A2E', border: `1px solid ${P.litBdr}`, borderRadius: 6,
              minWidth: 280, maxHeight: 300, overflowY: 'auto',
              boxShadow: '0 12px 40px rgba(0,0,0,.8)',
            }}>
              {acData.symbols.map(s => (
                <div key={s.SYMBOL} onMouseDown={() => selectSymbol(s.SYMBOL)}
                  style={{ padding: '8px 14px', cursor: 'pointer', borderBottom: `1px solid ${P.border}30`, display: 'flex', gap: 10, alignItems: 'baseline' }}
                  onMouseEnter={e => (e.currentTarget.style.background = P.cell)}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <span style={{ color: P.text, fontWeight: 800, fontFamily: 'monospace' }}>{s.SYMBOL}</span>
                  <span style={{ color: P.sub, fontSize: 11 }}>{s.COMPANY_NAME}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Price + 1D change */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 22, fontWeight: 900, color: P.text, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>
            {close > 0 ? `₹${close.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : (latest ? `₹${latest.close.toFixed(2)}` : '—')}
          </span>
          {chg1dPct != null && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <span style={{ fontSize: 13, fontWeight: 800, color: chg1dPct >= 0 ? P.green : P.red, lineHeight: 1.1 }}>
                {chg1dPct >= 0 ? '▲' : '▼'} {chg1dPct >= 0 ? '+' : ''}{chg1dPct.toFixed(2)}%
              </span>
              {chg1dAbs != null && (
                <span style={{ fontSize: 10, color: chg1dPct >= 0 ? P.green : P.red, fontFamily: 'monospace', lineHeight: 1 }}>
                  {chg1dAbs >= 0 ? '+' : ''}&#x20B9;{Math.abs(chg1dAbs).toFixed(2)} 1D
                </span>
              )}
            </div>
          )}
          {detail?.price?.ret_30d != null && (
            <span style={{ fontSize: 11, color: P.sub }}>
              30D: <span style={{ fontWeight: 700, color: detail.price.ret_30d >= 0 ? P.green : P.red }}>{pct(detail.price.ret_30d)}</span>
            </span>
          )}
        </div>

        {/* Badges */}
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {detail?.sector && <span style={{ fontSize: 11, color: P.sub }}>{detail.sector}</span>}
          {detail?.label && <CapFlowBadge label={detail.label} />}
          {t?.trend_signal && t.trend_signal !== 'INSUFFICIENT_DATA' && (
            <Chip label={t.trend_signal.replace(/_/g, ' ')} color={trendColor} />
          )}
          {f?.oi_signal && (
            <Chip label={`F&O: ${f.oi_signal.replace(/_/g, ' ')}`} color={f.oi_signal.includes('LONG') ? P.green : P.red} />
          )}
          <a href={`https://www.nseindia.com/get-quotes/equity?symbol=${symbol}`} target="_blank" rel="noopener noreferrer"
            style={{ fontSize: 10, color: P.blue, textDecoration: 'none', border: `1px solid ${P.litBdr}`, padding: '2px 7px', borderRadius: 3 }}>
            NSE
          </a>
        </div>

        {/* Score chips — 8-score panel matching the printed report */}
        {detail && (
          <div style={{ display: 'flex', gap: 8, marginLeft: 'auto', alignItems: 'flex-start', flexShrink: 0, flexWrap: 'wrap' }}>
            {([
              { label: 'Bull Run',    value: detail.bull_run_score,                                        signed: false },
              { label: 'Price',       value: detail.components?.price_score,                               signed: false },
              { label: 'ML Bull',     value: detail.ml_scores?.ml_bull_run_score,                          signed: false },
              { label: 'ML Accum.',   value: detail.ml_scores?.accumulation_score,                         signed: false },
              { label: 'Sector Flow', value: detail.components?.sector_flow_score,                         signed: false },
              { label: 'Deal',        value: detail.components?.deal_score,                                signed: false },
              { label: 'Valuation',   value: detail.fundamentals?.valuation_score != null ? Number(detail.fundamentals.valuation_score) : undefined, signed: false },
              { label: 'Astro',       value: detail.astro?.astro_score,                                    signed: true  },
            ] as { label: string; value: number | null | undefined; signed: boolean }[])
              .filter(s => s.value != null)
              .map(({ label, value, signed }) => {
                const displayVal = signed
                  ? Math.max(0, Math.min(100, ((value as number) + 100) / 2))
                  : value as number
                return (
                  <div key={label} style={{ textAlign: 'center', minWidth: 52 }}>
                    <ScoreGauge score={displayVal} size={52} />
                    <div style={{ fontSize: 10, color: P.sub, marginTop: 3, fontWeight: 600 }}>{label}</div>
                  </div>
                )
              })
            }
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, paddingTop: 16 }}>

        {/* ── Full-width chart ─────────────────────────────────────────── */}
        <div style={{ background: P.panel, border: `1px solid ${P.border}`, borderRadius: 8, overflow: 'hidden' }}>

          {/* Chart toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: `1px solid ${P.border}`, flexWrap: 'wrap' }}>
            <span style={{ ...LABEL, marginRight: 4 }}>Chart</span>
            <div style={{ display: 'flex', gap: 3 }}>
              {TF_INTRA.map(t_ => (
                <button key={t_} onClick={() => setTf(t_)} style={{
                  padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  border: `1px solid ${tf === t_ ? P.blue : P.border}`,
                  background: tf === t_ ? P.blue + '22' : 'transparent',
                  color: tf === t_ ? P.blue : P.sub, fontWeight: tf === t_ ? 700 : 400,
                }}>{t_}</button>
              ))}
            </div>
            <div style={{ width: 1, height: 16, background: P.border }} />
            <div style={{ display: 'flex', gap: 3 }}>
              {TF_DAILY.map(t_ => (
                <button key={t_} onClick={() => setTf(t_)} style={{
                  padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  border: `1px solid ${tf === t_ ? P.green : P.border}`,
                  background: tf === t_ ? P.green + '22' : 'transparent',
                  color: tf === t_ ? P.green : P.sub, fontWeight: tf === t_ ? 700 : 400,
                }}>{t_}</button>
              ))}
            </div>
            <button onClick={resetChart} style={{ padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer', border: `1px solid ${P.border}`, background: 'transparent', color: P.dim, marginLeft: 4 }}>
              Reset
            </button>
            <button
              onClick={takeSnapshot}
              disabled={!symbol}
              title="Save chart as PNG"
              style={{
                padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: symbol ? 'pointer' : 'not-allowed',
                border: `1px solid ${snapFlash ? P.green : P.border}`,
                background: snapFlash ? P.green + '22' : 'transparent',
                color: snapFlash ? P.green : P.dim, fontWeight: snapFlash ? 700 : 400,
              }}
            >
              {snapFlash ? 'Saved!' : 'Snapshot'}
            </button>
            {symbol && (
              <button
                onClick={() => navigate(`/fullchart/${symbol}?tf=${tf}`)}
                title="Open full-page chart"
                style={{
                  marginLeft: 'auto', padding: '4px 10px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  border: `1px solid ${P.blue}`, background: P.blue + '18', color: P.blue,
                  fontWeight: 600, letterSpacing: '0.04em',
                }}
              >
                [+] Full Chart
              </button>
            )}
          </div>

          {/* Chart canvas */}
          <ChartBoundary>
            <div style={{ position: 'relative', height: 400, background: P.bg }}>
              {chartErr && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, zIndex: 20 }}>
                  <span style={{ color: P.red, fontWeight: 700 }}>Chart Error</span>
                  <span style={{ color: P.sub, fontSize: 11 }}>{chartErr}</span>
                  <button onClick={() => { setChartErr(null); window.location.reload() }} style={{ padding: '4px 14px', border: `1px solid ${P.red}`, background: 'transparent', color: P.red, cursor: 'pointer', borderRadius: 4, fontSize: 10 }}>Reload</button>
                </div>
              )}
              {!chartErr && chartLoading && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: P.sub, fontSize: 12, zIndex: 10 }}>
                  Loading {symbol} ({tf})...
                </div>
              )}
              {!chartErr && chartFailed && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6, zIndex: 10 }}>
                  <span style={{ color: P.red, fontSize: 12 }}>No chart data for {symbol} ({tf})</span>
                  <span style={{ color: P.sub, fontSize: 10 }}>{INTRADAY.has(tf) ? 'Intraday may be unavailable for this symbol' : (chartErrObj as Error)?.message ?? ''}</span>
                </div>
              )}
              <div ref={chartDiv} style={{ width: '100%', height: '100%' }} />
            </div>
          </ChartBoundary>

          {/* OHLCV footer -- shows the hovered candle when the cursor is over
              the chart, falls back to the latest bar otherwise */}
          {(hoverBar ?? latest) && (() => {
            const b = hoverBar ?? latest!
            return (
              <div style={{ display: 'flex', gap: 20, padding: '7px 14px', fontSize: 10, color: P.sub, background: P.cell, borderTop: `1px solid ${P.border}`, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums', flexWrap: 'wrap', alignItems: 'center' }}>
                {hoverBar && <span style={{ color: P.blue, fontWeight: 700 }}>{fmtOhlcTime(hoverBar.time as string | number)}</span>}
                <span>O <span style={{ color: P.text }}>{b.open.toFixed(2)}</span></span>
                <span>H <span style={{ color: P.green }}>{b.high.toFixed(2)}</span></span>
                <span>L <span style={{ color: P.red }}>{b.low.toFixed(2)}</span></span>
                <span>C <span style={{ color: P.text }}>{b.close.toFixed(2)}</span></span>
                <span>Vol <span style={{ color: P.text }}>{((b.volume ?? 0) / 1e6).toFixed(2)}M</span></span>
                {ohlcv && <span style={{ marginLeft: 'auto', color: P.dim }}>{ohlcv.count} bars | {fmtOhlcTime(ohlcv.from)} — {fmtOhlcTime(ohlcv.to)}</span>}
              </div>
            )
          })()}
        </div>

        {/* ── Score + ML strip ──────────────────────────────────────────── */}
        {(detail || sig) && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
            {[
              { label: 'Price Momentum',    value: detail?.components?.price_score           ?? sig?.price_score },
              { label: 'ATH Proximity',     value: detail?.components?.ath_proximity_score  ?? detail?.ath_proximity_score },
              { label: 'Sector Flow',        value: detail?.components?.sector_flow_score   ?? sig?.sector_flow_score },
              { label: 'Block Deals',        value: detail?.components?.deal_score          ?? sig?.deal_score },
              { label: 'Corp Events',        value: detail?.components?.corporate_score     ?? sig?.corporate_score },
              { label: 'ML Bull Run',        value: detail?.ml_scores?.ml_bull_run_score  ?? sig?.ml_bull_run_score,  isFwd: false },
              { label: 'Accumulation',       value: detail?.ml_scores?.accumulation_score ?? sig?.accumulation_score, isFwd: false },
              { label: 'Fwd Return (45D)',   value: detail?.ml_scores?.forward_return_score ?? sig?.forward_return_score, isFwd: true },
            ].filter(m => m.value != null).map(({ label, value, isFwd }) => {
              const c = isFwd ? P.amber : scoreC(value!)
              return (
                <div key={label} style={{ background: P.panel, border: `1px solid ${isFwd ? P.amber + '55' : P.border}`, borderRadius: 7, padding: '10px 14px', borderLeft: `3px solid ${c}` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={LABEL}>{label}</div>
                    {isFwd && (
                      <span style={{ fontSize: 8, fontWeight: 700, color: P.amber, background: P.amber + '18', border: `1px solid ${P.amber}44`, borderRadius: 3, padding: '1px 4px', letterSpacing: '0.04em' }}>
                        REALIZED
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 900, color: c, fontFamily: 'monospace', marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>
                    {value!.toFixed(0)}
                  </div>
                  <div style={{ height: 3, background: P.border, borderRadius: 2, marginTop: 6 }}>
                    <div style={{ width: `${Math.min(value!, 100)}%`, height: '100%', background: c, borderRadius: 2 }} />
                  </div>
                  {isFwd && (
                    <div style={{ fontSize: 9, color: P.dim, marginTop: 4 }}>
                      P(+15% in 45 sessions) · AUC 0.63
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Loading shimmer for detail */}
        {detailLoading && (
          <div style={{ color: P.sub, textAlign: 'center', padding: 24, fontSize: 12 }}>
            Loading intelligence for {symbol}...
          </div>
        )}

        {detail && (
          <>
            {/* ══ THESIS & CONVICTION ══════════════════════════════════════════ */}
            <SectionDivider label="THESIS & CONVICTION" />

            {detail.structured_thesis && (
              <InvestmentThesisCard
                thesis={detail.structured_thesis}
                drivingParticipant={detail.driving_participant}
              />
            )}

            {/* Participant caution — only shown when signal is meaningful */}
            {detail.driving_participant && (
              <ParticipantCautionBanner
                label={detail.label}
                drivingParticipant={detail.driving_participant}
              />
            )}

            {/* Analyst Insights + Score Breakdown: 2-col when insights exist, full-width 4-tile row otherwise */}
            {insights && insights.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.4fr 1fr', gap: 14, alignItems: 'start' }}>
                <div style={{ background: '#090F1E', border: `1px solid ${P.litBdr}`, borderLeft: `4px solid ${P.blue}`, borderRadius: 8, padding: 16 }}>
                  <div style={{ ...LABEL, color: P.blue, marginBottom: 12 }}>Analyst Insights — Plain English</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {insights.map((txt, i) => (
                      <div key={i} style={{ display: 'flex', gap: 10, background: P.cell, border: `1px solid ${P.border}`, borderRadius: 6, padding: '9px 12px' }}>
                        <div style={{ width: 22, height: 22, borderRadius: '50%', background: '#1E3A5F', color: P.blue, fontSize: 10, fontWeight: 800, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{i + 1}</div>
                        <div style={{ color: P.text, fontSize: 12, lineHeight: 1.55 }}>{txt}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <SectionCard title="Bull Run Score Breakdown">
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                    {[
                      { label: 'Price Momentum', value: detail.components.price_score,                            sub: '25% weight' },
                      { label: 'ATH Proximity',  value: detail.components.ath_proximity_score ?? detail.ath_proximity_score ?? 0, sub: '20% weight' },
                      { label: 'Sector Flow',    value: detail.components.sector_flow_score,                      sub: '20% weight' },
                      { label: 'Block Deals',    value: detail.components.deal_score,                             sub: '20% weight' },
                      { label: 'Corp Events',    value: detail.components.corporate_score,                        sub: '15% weight' },
                    ].map(({ label, value, sub }) => {
                      const c = scoreC(value)
                      return (
                        <div key={label} style={{ background: P.cell, border: `1px solid ${P.border}`, borderRadius: 6, padding: '10px 12px' }}>
                          <div style={{ fontSize: 22, fontWeight: 900, color: c, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{value.toFixed(0)}</div>
                          <div style={{ height: 3, background: P.border, borderRadius: 2, margin: '6px 0' }}>
                            <div style={{ width: `${value}%`, height: '100%', background: c, borderRadius: 2 }} />
                          </div>
                          <div style={{ color: P.sub, fontSize: 10, fontWeight: 600 }}>{label}</div>
                          <div style={{ color: P.dim, fontSize: 10 }}>{sub}</div>
                        </div>
                      )
                    })}
                  </div>
                  <div style={{ background: P.cell, borderRadius: 5, border: `1px solid ${P.border}`, padding: '7px 10px', display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 10 }}>
                    <span style={{ color: P.sub }}>Regime: <span style={{ color: P.text, fontWeight: 700 }}>{detail.market_regime}</span></span>
                    <span style={{ color: P.dim }}>|</span>
                    <span style={{ color: P.sub }}>Multiplier: <span style={{ color: P.text, fontWeight: 700 }}>×{detail.regime_multiplier.toFixed(2)}</span></span>
                    <span style={{ color: P.dim }}>|</span>
                    <span style={{ color: P.dim }}>as of {detail.as_of_date}</span>
                  </div>
                </SectionCard>
              </div>
            ) : (
              <SectionCard title="Bull Run Score Breakdown">
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(5, 1fr)', gap: 10, marginBottom: 12 }}>
                  {[
                    { label: 'Price Momentum', value: detail.components.price_score,                            sub: '25% weight' },
                    { label: 'ATH Proximity',  value: detail.components.ath_proximity_score ?? detail.ath_proximity_score ?? 0, sub: '20% weight' },
                    { label: 'Sector Flow',    value: detail.components.sector_flow_score,                      sub: '20% weight' },
                    { label: 'Block Deals',    value: detail.components.deal_score,                             sub: '20% weight' },
                    { label: 'Corp Events',    value: detail.components.corporate_score,                        sub: '15% weight' },
                  ].map(({ label, value, sub }) => {
                    const c = scoreC(value)
                    return (
                      <div key={label} style={{ background: P.cell, border: `1px solid ${P.border}`, borderRadius: 6, padding: '10px 12px' }}>
                        <div style={{ fontSize: 22, fontWeight: 900, color: c, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{value.toFixed(0)}</div>
                        <div style={{ height: 3, background: P.border, borderRadius: 2, margin: '6px 0' }}>
                          <div style={{ width: `${value}%`, height: '100%', background: c, borderRadius: 2 }} />
                        </div>
                        <div style={{ color: P.sub, fontSize: 10, fontWeight: 600 }}>{label}</div>
                        <div style={{ color: P.dim, fontSize: 10 }}>{sub}</div>
                      </div>
                    )
                  })}
                </div>
                <div style={{ background: P.cell, borderRadius: 5, border: `1px solid ${P.border}`, padding: '7px 10px', display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 10 }}>
                  <span style={{ color: P.sub }}>Regime: <span style={{ color: P.text, fontWeight: 700 }}>{detail.market_regime}</span></span>
                  <span style={{ color: P.dim }}>|</span>
                  <span style={{ color: P.sub }}>Multiplier: <span style={{ color: P.text, fontWeight: 700 }}>×{detail.regime_multiplier.toFixed(2)}</span></span>
                  <span style={{ color: P.dim }}>|</span>
                  <span style={{ color: P.dim }}>as of {detail.as_of_date}</span>
                </div>
              </SectionCard>
            )}

            {/* ══ PRICE & TECHNICALS ══════════════════════════════════════════ */}
            <SectionDivider label="PRICE & TECHNICALS" />

            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'start' }}>
              {t && (
                <div style={{ flex: '2 1 400px', minWidth: 340 }}>
                  <SectionCard title="Technical Indicators" accentColor={trendColor}>

                    {/* ── Header: trend chip + vol ── */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                        <Chip label={t.trend_signal?.replace(/_/g, ' ') ?? 'N/A'} color={trendColor} size={11} />
                        {t.adx_strength && (
                          <Chip
                            label={t.adx != null ? `ADX ${t.adx.toFixed(0)} ${t.adx_strength.replace(/_/g, ' ')}` : t.adx_strength.replace(/_/g, ' ')}
                            color={t.adx_strength === 'STRONG_TREND' ? P.green : t.adx_strength === 'MODERATE_TREND' ? P.amber : P.dim}
                            size={10}
                          />
                        )}
                      </div>
                      {t.vol_20d_avg != null && <span style={{ color: P.sub, fontSize: 10 }}>Avg Vol {(t.vol_20d_avg / 1e5).toFixed(1)}L/day</span>}
                    </div>

                    {/* ── 52W Range slider ── */}
                    {t.high_52w != null && t.low_52w != null && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: P.dim, marginBottom: 5 }}>
                          <span>52W Low ₹{t.low_52w.toFixed(0)}</span>
                          <span>52W High ₹{t.high_52w.toFixed(0)}</span>
                        </div>
                        <div style={{ height: 6, background: '#1A2740', borderRadius: 3, position: 'relative' }}>
                          {(() => {
                            const pos = Math.max(0, Math.min(100, (close - t.low_52w!) / (t.high_52w! - t.low_52w!) * 100))
                            const dotC = pos >= 80 ? P.green : pos >= 40 ? P.amber : P.red
                            return (
                              <>
                                <div style={{ width: `${pos}%`, height: '100%', background: `linear-gradient(to right, ${P.border}, ${dotC}55)`, borderRadius: 3 }} />
                                <div style={{ position: 'absolute', top: -4, left: `${pos}%`, width: 14, height: 14, borderRadius: '50%', background: dotC, transform: 'translateX(-50%)', border: `2px solid ${P.bg}`, boxShadow: `0 0 8px ${dotC}88` }} />
                              </>
                            )
                          })()}
                        </div>
                      </div>
                    )}

                    {/* ── DMA rows ── */}
                    <DMARow label="20 DMA"  dma={t.dma_20}  close={close} color={P.blue} />
                    <DMARow label="50 DMA"  dma={t.dma_50}  close={close} color="#A78BFA" />
                    <DMARow label="200 DMA" dma={t.dma_200} close={close} color={P.amber} />

                    {/* ── Momentum grid ── */}
                    <SectionDivider label="MOMENTUM" />
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 4 }}>

                      {/* RSI */}
                      {t.rsi != null && (() => {
                        const rsiC = t.rsi >= 70 ? P.red : t.rsi >= 55 ? P.green : t.rsi >= 45 ? P.sub : t.rsi >= 30 ? P.amber : '#FF6060'
                        return (
                          <div style={{ background: P.cell, borderRadius: 6, padding: '8px 10px', border: `1px solid ${P.border}` }}>
                            <div style={{ fontSize: 10, color: P.dim, fontWeight: 700, letterSpacing: '0.08em' }}>RSI (14)</div>
                            <div style={{ fontSize: 20, fontWeight: 800, color: rsiC, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{t.rsi.toFixed(1)}</div>
                            <div style={{ fontSize: 10, color: rsiC, marginTop: 1 }}>{t.rsi_signal.replace(/_/g, ' ')}</div>
                            <div style={{ marginTop: 5, height: 3, background: '#1A2740', borderRadius: 2 }}>
                              <div style={{ width: `${t.rsi}%`, height: '100%', background: rsiC, borderRadius: 2 }} />
                            </div>
                          </div>
                        )
                      })()}

                      {/* MACD */}
                      {t.macd_line != null && (() => {
                        const macdC = t.macd_cross?.includes('BULLISH') ? P.green : t.macd_cross?.includes('BEARISH') ? P.red : P.sub
                        const isCross = t.macd_cross === 'BULLISH_CROSS' || t.macd_cross === 'BEARISH_CROSS'
                        return (
                          <div style={{ background: P.cell, borderRadius: 6, padding: '8px 10px', border: `1px solid ${isCross ? macdC + '55' : P.border}` }}>
                            <div style={{ fontSize: 10, color: P.dim, fontWeight: 700, letterSpacing: '0.08em' }}>MACD</div>
                            <div style={{ fontSize: 14, fontWeight: 800, color: macdC, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>
                              {t.macd_hist != null ? `${t.macd_hist >= 0 ? '+' : ''}${t.macd_hist.toFixed(2)}` : '--'}
                            </div>
                            <div style={{ fontSize: 10, color: macdC, marginTop: 1 }}>
                              {isCross ? t.macd_cross!.replace(/_/g, ' ') : (t.macd_hist != null && t.macd_hist >= 0 ? 'Histogram +' : 'Histogram -')}
                            </div>
                            <div style={{ fontSize: 9, color: P.dim, marginTop: 2 }}>
                              L {t.macd_line.toFixed(1)} | S {t.macd_signal?.toFixed(1) ?? '--'}
                            </div>
                          </div>
                        )
                      })()}

                      {/* Bollinger Bands */}
                      {t.bb_pct != null && (() => {
                        const bbC = t.bb_signal === 'NEAR_UPPER' ? P.red : t.bb_signal === 'NEAR_LOWER' ? P.green : t.bb_signal === 'SQUEEZE' ? P.amber : P.sub
                        return (
                          <div style={{ background: P.cell, borderRadius: 6, padding: '8px 10px', border: `1px solid ${t.bb_squeeze ? P.amber + '66' : P.border}` }}>
                            <div style={{ fontSize: 10, color: P.dim, fontWeight: 700, letterSpacing: '0.08em' }}>BB %B{t.bb_squeeze ? ' SQUEEZE' : ''}</div>
                            <div style={{ fontSize: 20, fontWeight: 800, color: bbC, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{t.bb_pct.toFixed(0)}%</div>
                            <div style={{ fontSize: 10, color: bbC, marginTop: 1 }}>{t.bb_signal.replace(/_/g, ' ')}</div>
                            <div style={{ marginTop: 5, height: 3, background: '#1A2740', borderRadius: 2 }}>
                              <div style={{ width: `${Math.min(100, Math.max(0, t.bb_pct))}%`, height: '100%', background: bbC, borderRadius: 2 }} />
                            </div>
                          </div>
                        )
                      })()}
                    </div>

                    {/* ── Volatility + Volume row ── */}
                    <SectionDivider label="VOLATILITY & VOLUME" />
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 4 }}>

                      {/* ATR */}
                      {t.atr_14 != null && (
                        <div style={{ background: P.cell, borderRadius: 6, padding: '8px 10px', border: `1px solid ${P.border}` }}>
                          <div style={{ fontSize: 10, color: P.dim, fontWeight: 700, letterSpacing: '0.08em' }}>ATR (14)</div>
                          <div style={{ fontSize: 16, fontWeight: 800, color: P.text, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>₹{t.atr_14.toFixed(1)}</div>
                          <div style={{ fontSize: 10, color: P.sub, marginTop: 1 }}>{t.atr_pct != null ? `${t.atr_pct.toFixed(2)}% of price` : 'daily range'}</div>
                        </div>
                      )}

                      {/* OBV */}
                      {t.obv_signal && (
                        <div style={{ background: P.cell, borderRadius: 6, padding: '8px 10px', border: `1px solid ${P.border}` }}>
                          <div style={{ fontSize: 10, color: P.dim, fontWeight: 700, letterSpacing: '0.08em' }}>OBV FLOW</div>
                          <div style={{ fontSize: 13, fontWeight: 800, color: t.obv_signal === 'ACCUMULATING' ? P.green : P.red, marginTop: 5 }}>
                            {t.obv_signal === 'ACCUMULATING' ? 'ACCUMULATING' : 'DISTRIBUTING'}
                          </div>
                          <div style={{ fontSize: 10, color: P.sub, marginTop: 1 }}>volume direction 20D</div>
                        </div>
                      )}

                      {/* ADX +DI / -DI */}
                      {t.adx != null && t.adx_plus_di != null && (
                        <div style={{ background: P.cell, borderRadius: 6, padding: '8px 10px', border: `1px solid ${P.border}` }}>
                          <div style={{ fontSize: 10, color: P.dim, fontWeight: 700, letterSpacing: '0.08em' }}>ADX / DI</div>
                          <div style={{ fontSize: 16, fontWeight: 800, color: P.text, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{t.adx.toFixed(1)}</div>
                          <div style={{ display: 'flex', gap: 8, marginTop: 2 }}>
                            <span style={{ fontSize: 10, color: P.green }}>+DI {t.adx_plus_di.toFixed(1)}</span>
                            <span style={{ fontSize: 10, color: P.red }}>-DI {t.adx_minus_di?.toFixed(1) ?? '--'}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {t.as_of_date && <div style={{ fontSize: 10, color: P.dim, marginTop: 10 }}>as of {t.as_of_date}</div>}
                  </SectionCard>
                </div>
              )}

              {/* Key Levels + F&O stacked on the right */}
              <div style={{ flex: '1 1 260px', minWidth: 240, display: 'flex', flexDirection: 'column', gap: 14 }}>
                {detail.key_levels && detail.key_levels.conf_res_1 != null && (
                  <KeyLevelsCard kl={detail.key_levels} close={close} />
                )}

                {f && f.oi_signal && (
                  <SectionCard title="Futures & Options" accentColor={f.oi_signal.includes('LONG') ? P.green : P.red}>
                    {(() => {
                      const OI_MAP: Record<string, string> = { LONG_BUILDUP: P.green, SHORT_BUILDUP: P.red, LONG_UNWINDING: P.amber, SHORT_COVERING: P.teal }
                      const OI_TEXT: Record<string, string> = { LONG_BUILDUP: 'Big traders buying fresh — bullish', SHORT_BUILDUP: 'Traders betting on fall — bearish', LONG_UNWINDING: 'Buyers exiting — weakening', SHORT_COVERING: 'Bears buying back — potential reversal' }
                      const c = OI_MAP[f.oi_signal] ?? P.sub
                      return (
                        <>
                          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
                            <div><div style={LABEL}>Signal</div><div style={{ marginTop: 5 }}><Chip label={f.oi_signal.replace(/_/g, ' ')} color={c} size={11} /></div></div>
                            {f.futures_oi != null && <div><div style={LABEL}>Open Interest</div><div style={{ fontSize: 15, fontWeight: 800, color: P.text, marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{(f.futures_oi / 1e6).toFixed(2)}M</div></div>}
                            {f.oi_1d != null && <div><div style={LABEL}>1D OI Chg</div><div style={{ fontSize: 15, fontWeight: 800, color: f.oi_1d >= 0 ? P.green : P.red, marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{f.oi_1d >= 0 ? '+' : ''}{f.oi_1d.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div></div>}
                            {f.oi_5d != null && <div><div style={LABEL}>5D OI Chg</div><div style={{ fontSize: 15, fontWeight: 800, color: f.oi_5d >= 0 ? P.green : P.red, marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{f.oi_5d >= 0 ? '+' : ''}{f.oi_5d.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div></div>}
                          </div>
                          {OI_TEXT[f.oi_signal] && <div style={{ fontSize: 11, color: c, background: c + '12', border: `1px solid ${c}33`, padding: '7px 10px', borderRadius: 5 }}>{OI_TEXT[f.oi_signal]}</div>}
                        </>
                      )
                    })()}
                  </SectionCard>
                )}
              </div>
            </div>

            {/* ══ FUNDAMENTALS & VALUATION ════════════════════════════════════ */}
            <SectionDivider label="FUNDAMENTALS & VALUATION" />

            {Object.keys(fund).length > 0 && (
              <div>
                <div style={CARD_HEADER}>Fundamentals</div>
                {fund._sector_note === 'BANKING_XBRL_PENDING' && (
                  <div style={{
                    margin: '8px 0', padding: '8px 12px', borderRadius: 4,
                    background: '#0A1828', border: '1px solid #1E3A5A',
                    fontSize: 11, color: '#64748B', display: 'flex', alignItems: 'center', gap: 8,
                  }}>
                    <span style={{ color: '#3B82F6', fontWeight: 700 }}>i</span>
                    Banking sector: P&amp;L reported under IndAS Banking taxonomy (NIM, NII, GNPA).
                    Standard P&amp;L metrics (Revenue, PAT, P/E) are not yet parsed — Phase 15 XBRL update pending.
                    Market cap, shareholding and technical data below are accurate.
                  </div>
                )}
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(3, 1fr)' : 'repeat(6, 1fr)', gap: 10, marginTop: 10 }}>

                  {/* Row 1 — Valuation & Quality Ratios */}
                  <FundTile label="Market Cap (₹ Cr)" hdrBg="#1A3A6E" valColor={P.text}
                    value={fund.market_cap_cr != null ? crFmt(+fund.market_cap_cr) : '--'}
                    sub={fund.shares_outstanding_cr != null ? `${(+fund.shares_outstanding_cr).toFixed(1)} Cr shares` : 'estimated'} />
                  <FundTile label="P/E Ratio" hdrBg="#2A1800"
                    value={fund.pe_ratio != null ? `${(+fund.pe_ratio).toFixed(1)}x` : '--'}
                    valColor={fund.pe_ratio == null ? P.sub : +fund.pe_ratio < 15 ? P.green : +fund.pe_ratio > 40 ? P.red : P.amber}
                    sub="price to earnings" />
                  <FundTile label="Book Value (₹)" hdrBg="#2D1B4E"
                    valColor={fund.book_value_per_share != null ? P.text : P.sub}
                    value={fund.book_value_per_share != null ? `₹${(+fund.book_value_per_share).toLocaleString('en-IN', {maximumFractionDigits: 0})}` : '---'}
                    sub={fund.total_equity_cr != null ? `Equity ${crFmt(+fund.total_equity_cr)}` : 'balance sheet pending'} />
                  <FundTile label="Valuation"
                    hdrBg={fund.valuation_label === 'CHEAP_QUALITY' ? '#052E16' : fund.valuation_label === 'FAIR_VALUE' ? '#0C1A3A' : fund.valuation_label === 'EXPENSIVE' ? '#2D0A0A' : '#1A1228'}
                    value={<span style={{ fontSize: FS.md }}>{String(fund.valuation_label ?? 'N/A').replace(/_/g, ' ')}</span>}
                    valColor={fund.valuation_label === 'CHEAP_QUALITY' ? P.green : fund.valuation_label === 'FAIR_VALUE' ? P.blue : fund.valuation_label === 'EXPENSIVE' ? P.red : P.amber}
                    sub={fund.valuation_score != null ? `score ${(+fund.valuation_score).toFixed(0)}/100` : ''} />
                  <FundTile label="ROE (%)" hdrBg="#0A2A1F"
                    value={fund.roe_pct != null ? `${(+fund.roe_pct).toFixed(1)}%` : '--'}
                    valColor={fund.roe_pct == null ? P.sub : +fund.roe_pct >= 20 ? P.green : +fund.roe_pct >= 12 ? P.teal : P.red}
                    sub="return on equity" />
                  <FundTile label="ROCE (%)" hdrBg="#0A1A2E"
                    valColor={fund.roce_pct == null ? P.sub : +fund.roce_pct >= 20 ? P.green : +fund.roce_pct >= 12 ? P.teal : +fund.roce_pct >= 0 ? P.amber : P.red}
                    value={fund.roce_pct != null ? `${(+fund.roce_pct).toFixed(1)}%` : '---'}
                    sub={fund.capital_employed_cr != null ? `CE ${crFmt(+fund.capital_employed_cr)}` : 'capital employed pending'} />

                  {/* Row 2 — Income Statement & Quarterly Growth */}
                  <FundTile label="Sales (₹ Cr)" hdrBg="#1A3A6E" valColor={P.text}
                    value={fund.revenue_ttm_cr != null ? crFmt(+fund.revenue_ttm_cr) : '--'}
                    sub={fund.as_of_date ? `TTM as of ${String(fund.as_of_date).slice(0,7)}` : 'trailing 12M'} />
                  <FundTile label="PAT (₹ Cr)" hdrBg="#2D1B4E"
                    value={fund.profit_ttm_cr != null ? crFmt(+fund.profit_ttm_cr) : '--'}
                    valColor={fund.profit_ttm_cr == null ? P.sub : +fund.profit_ttm_cr >= 0 ? P.text : P.red}
                    sub="profit after tax TTM" />
                  <FundTile label="OPM (%)" hdrBg="#0A1A2E"
                    valColor={fund.opm_pct == null ? P.sub : +fund.opm_pct >= 20 ? P.green : +fund.opm_pct >= 10 ? P.teal : +fund.opm_pct >= 0 ? P.amber : P.red}
                    value={fund.opm_pct != null ? `${(+fund.opm_pct).toFixed(1)}%` : '---'}
                    sub={fund.ebitda_cr_latest != null ? `EBITDA ${crFmt(+fund.ebitda_cr_latest)} qtr` : 'EBITDA data pending'} />
                  <FundTile label={`${fund.qtr_growth_period ?? 'Qtr'} Sales Growth (%)`}
                    hdrBg={fund.qtr_sales_growth_pct != null && +fund.qtr_sales_growth_pct >= 0 ? '#062014' : '#200606'}
                    value={fund.qtr_sales_growth_pct != null ? `${+fund.qtr_sales_growth_pct >= 0 ? '+' : ''}${(+fund.qtr_sales_growth_pct).toFixed(1)}%` : '--'}
                    valColor={fund.qtr_sales_growth_pct == null ? P.sub : +fund.qtr_sales_growth_pct >= 10 ? P.green : +fund.qtr_sales_growth_pct >= 0 ? P.teal : P.red}
                    sub="vs prior period revenue" />
                  <FundTile label={`${fund.qtr_growth_period ?? 'Qtr'} Profit Growth (%)`}
                    hdrBg={fund.qtr_profit_growth_pct != null && +fund.qtr_profit_growth_pct >= 0 ? '#062014' : '#200606'}
                    value={fund.qtr_profit_growth_pct != null ? `${+fund.qtr_profit_growth_pct >= 0 ? '+' : ''}${(+fund.qtr_profit_growth_pct).toFixed(1)}%` : '--'}
                    valColor={fund.qtr_profit_growth_pct == null ? P.sub : +fund.qtr_profit_growth_pct >= 10 ? P.green : +fund.qtr_profit_growth_pct >= 0 ? P.teal : P.red}
                    sub="vs prior period PAT" />
                  <FundTile
                    label={`Sales Growth ${fund.sales_growth_years != null ? `${(+fund.sales_growth_years).toFixed(0)}Y` : '3Y'} (%)`}
                    hdrBg={fund.sales_growth_3y_pct != null && +fund.sales_growth_3y_pct >= 0 ? '#062014' : '#200606'}
                    valColor={fund.sales_growth_3y_pct == null ? P.sub : +fund.sales_growth_3y_pct >= 15 ? P.green : +fund.sales_growth_3y_pct >= 5 ? P.teal : +fund.sales_growth_3y_pct >= 0 ? P.amber : P.red}
                    value={fund.sales_growth_3y_pct != null ? `${+fund.sales_growth_3y_pct >= 0 ? '+' : ''}${(+fund.sales_growth_3y_pct).toFixed(1)}%` : '---'}
                    sub={fund.sales_growth_years != null ? `${(+fund.sales_growth_years).toFixed(1)}Y revenue CAGR` : 'needs 4+ quarters'} />

                  {/* Row 3 — Price Position & Ownership */}
                  <FundTile label="Return over 1Y (%)"
                    hdrBg={detail.price.ret_365d != null && detail.price.ret_365d >= 0 ? '#062014' : '#200606'}
                    value={pct(detail.price.ret_365d)}
                    valColor={detail.price.ret_365d == null ? P.sub : detail.price.ret_365d >= 0 ? P.green : P.red}
                    sub="365-day price return" />
                  <FundTile label="vs 200 DMA" hdrBg={t?.vs_dma_200 != null && t.vs_dma_200 >= 0 ? '#062014' : '#200606'}
                    value={t?.vs_dma_200 != null ? `${t.vs_dma_200 >= 0 ? '+' : ''}${t.vs_dma_200.toFixed(1)}%` : '--'}
                    valColor={t?.vs_dma_200 == null ? P.sub : t.vs_dma_200 >= 5 ? P.green : t.vs_dma_200 >= 0 ? P.teal : P.red}
                    sub="long-term trend" />
                  <FundTile label="Down from 52W High (%)"
                    hdrBg={fund.down_from_ath_pct != null && +fund.down_from_ath_pct >= -15 ? '#062014' : '#1A0D00'}
                    value={fund.down_from_ath_pct != null ? `${(+fund.down_from_ath_pct).toFixed(1)}%` : '--'}
                    valColor={fund.down_from_ath_pct == null ? P.sub : +fund.down_from_ath_pct >= -15 ? P.teal : +fund.down_from_ath_pct >= -40 ? P.amber : P.red}
                    sub={fund.high_52w != null ? `52W High ₹${(+fund.high_52w).toFixed(0)}` : fund.ath_price != null ? `52W High ₹${(+fund.ath_price).toFixed(0)}` : '52-week high'} />
                  <FundTile label="Vol Ratio" hdrBg="#0A1C2E"
                    value={detail.price.vol_ratio != null ? `${(+detail.price.vol_ratio).toFixed(1)}x` : '--'}
                    valColor={detail.price.vol_ratio == null ? P.sub : +detail.price.vol_ratio >= 1.5 ? P.green : +detail.price.vol_ratio >= 1 ? P.blue : P.sub}
                    sub="vs 90D avg volume" />
                  <FundTile label="Promoter %" hdrBg="#1E0D3A"
                    value={shp.promoter_pct != null ? `${(+shp.promoter_pct).toFixed(1)}%` : '--'}
                    valColor={shp.promoter_pct == null ? P.sub : +shp.promoter_pct >= 65 ? P.green : +shp.promoter_pct >= 50 ? P.teal : P.amber}
                    sub="promoter holding" />
                  <FundTile label="FII %" hdrBg="#0A2014"
                    value={shp.fii_pct != null ? `${(+shp.fii_pct).toFixed(1)}%` : '--'}
                    valColor={shp.fii_pct == null ? P.sub : +shp.fii_pct >= 10 ? P.blue : P.sub}
                    sub="foreign institutional" />
                </div>
              </div>
            )}

            {detail.sector_peer_valuation && Object.keys(detail.sector_peer_valuation).length > 0 && (
              <ValuationContextCard fundamentals={fund} peers={detail.sector_peer_valuation} />
            )}

            {/* ══ INSTITUTIONAL POSITIONING ════════════════════════════════════ */}
            <SectionDivider label="INSTITUTIONAL POSITIONING" />

            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'start' }}>
              {/* LEFT: Shareholding Trends — only rendered when data exists */}
              {trends.length > 0 && (
                <div style={{ flex: '1 1 300px', minWidth: 280 }}>
                  <SectionCard title="Shareholding Trends (QoQ)" accentColor={P.purple}>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
                        <thead>
                          <tr>
                            {['Period', 'Promoter', 'FII', 'DII', 'Signal'].map(h => (
                              <th key={h} style={{ padding: '4px 8px', textAlign: h === 'Period' ? 'left' : 'right', color: P.dim, fontSize: 10, fontWeight: 700, letterSpacing: 1, borderBottom: `1px solid ${P.border}` }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {trends.map((r, i) => {
                            const sig_ = String(r.conviction_signal ?? '')
                            const sc = sig_.includes('ACCUMULATION') ? P.green
                                     : sig_.includes('SELLING') || sig_.includes('DISTRIBUTION') ? P.red
                                     : sig_.includes('DIVERGENCE') ? P.amber
                                     : P.dim
                            // Detect data gap: consecutive periods should differ by 1 FY quarter
                            const fyIdx = (p: string) => { const m = p.match(/Q(\d)FY(\d+)/); return m ? +m[2]*4 + +m[1] : 0 }
                            const prevPeriod = i > 0 ? String(trends[i-1]?.period ?? '') : ''
                            const showGap = i > 0 && (fyIdx(String(r.period ?? '')) - fyIdx(prevPeriod)) > 1
                            return (
                              <>
                              {showGap && (
                                <tr key={`gap-${i}`}>
                                  <td colSpan={5} style={{ padding: '3px 8px', fontSize: 10, color: P.dim, fontStyle: 'italic', borderBottom: `1px dashed ${P.border}`, textAlign: 'center' }}>
                                    data unavailable for intermediate quarters
                                  </td>
                                </tr>
                              )}
                              <tr key={i} style={{ borderBottom: `1px solid ${P.border}20` }}>
                                <td style={{ padding: '5px 8px', color: P.sub, fontFamily: 'monospace', fontSize: 10 }}>{String(r.period ?? '')}</td>
                                {(['promoter_pct', 'fii_pct', 'dii_pct'] as const).map(k => {
                                  const dk = k + '_delta'
                                  const val = r[k]; const delta = r[dk]
                                  return (
                                    <td key={k} style={{ padding: '5px 8px', textAlign: 'right', color: P.text, fontVariantNumeric: 'tabular-nums' }}>
                                      {val != null ? `${(+val).toFixed(2)}%` : '--'}
                                      {delta != null && <span style={{ color: +delta >= 0 ? P.green : P.red, marginLeft: 4, fontSize: 10 }}>{+delta >= 0 ? '+' : ''}{(+delta).toFixed(2)}</span>}
                                    </td>
                                  )
                                })}
                                <td style={{ padding: '5px 8px', textAlign: 'right' }}>
                                  {sig_ && <span style={{ fontSize: 10, fontWeight: 700, color: sc, padding: '2px 6px', background: sc + '18', border: `1px solid ${sc}33`, borderRadius: 3 }}>{sig_.replace(/_/g, ' ')}</span>}
                                </td>
                              </tr>
                              </>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </SectionCard>
                </div>
              )}

              {/* RIGHT: Block Deals + Management + Consensus */}
              <div style={{ flex: '1 1 280px', minWidth: 260, display: 'flex', flexDirection: 'column', gap: 14 }}>
                {detail.deal_signals && Object.keys(detail.deal_signals).length > 0 && (() => {
                  const d = detail.deal_signals as Record<string, string | number | null>
                  if (!d.deal_signal) return null
                  const dc = String(d.deal_signal).includes('BULL') ? P.green : String(d.deal_signal).includes('BEAR') ? P.red : P.sub
                  return (
                    <SectionCard title="Institutional Block Deals" accentColor={dc}>
                      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 10 }}>
                        {[
                          { label: 'Signal', value: String(d.deal_signal).replace(/_/g, ' '), color: dc },
                          { label: 'Total Deals', value: String(d.total_deals ?? '--'), color: P.text },
                          { label: 'Inst Net (Cr)', value: d.inst_net_value_cr != null ? crFmt(+d.inst_net_value_cr!) : '--', color: +d.inst_net_value_cr! >= 0 ? P.green : P.red },
                        ].map(({ label, value, color }) => (
                          <div key={label}>
                            <div style={LABEL}>{label}</div>
                            <div style={{ fontSize: 15, fontWeight: 800, color, marginTop: 4 }}>{value}</div>
                          </div>
                        ))}
                      </div>
                      {d.last_deal_date && <div style={{ fontSize: 9, color: P.dim }}>last deal: {String(d.last_deal_date)} | window: {d.window_days}D</div>}
                    </SectionCard>
                  )
                })()}
                {Object.keys(mgmt).length > 0 && mgmt.management_score != null && (
                  <SectionCard title="Management Intelligence" accentColor={+mgmt.management_score! >= 65 ? P.green : +mgmt.management_score! >= 45 ? P.amber : P.red}>
                    <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 10 }}>
                      <div>
                        <div style={LABEL}>Overall Score</div>
                        <div style={{ fontSize: 24, fontWeight: 900, color: scoreC(+mgmt.management_score!), fontFamily: 'monospace', marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{(+mgmt.management_score!).toFixed(0)}</div>
                      </div>
                      {mgmt.management_label && (
                        <div style={{ alignSelf: 'flex-end', paddingBottom: 4 }}>
                          <Chip label={String(mgmt.management_label)} color={String(mgmt.management_label) === 'POSITIVE' ? P.green : String(mgmt.management_label) === 'NEGATIVE' ? P.red : P.amber} size={11} />
                        </div>
                      )}
                    </div>
                    <ScoreBar label="Holding Signal" value={mgmt.holding_score != null ? +mgmt.holding_score : null} />
                    <ScoreBar label="Announcements"  value={mgmt.announcement_score != null ? +mgmt.announcement_score : null} />
                  </SectionCard>
                )}
                {Object.keys(consensus).length > 0 && consensus.consensus_action && (
                  <SectionCard title="Multi-Signal Consensus" accentColor={String(consensus.consensus_action) === 'BUY' ? P.green : String(consensus.consensus_action) === 'SELL' ? P.red : P.amber}>
                    <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
                      {[
                        { label: 'Action',     value: String(consensus.consensus_action ?? ''),  color: String(consensus.consensus_action) === 'BUY' ? P.green : String(consensus.consensus_action) === 'SELL' ? P.red : P.amber },
                        { label: 'Confidence', value: String(consensus.confidence ?? ''),        color: P.blue },
                        { label: 'Signals In', value: String(consensus.signals_in ?? ''),        color: P.text },
                      ].map(({ label, value, color }) => value && (
                        <div key={label}>
                          <div style={LABEL}>{label}</div>
                          <div style={{ fontSize: 16, fontWeight: 800, color, marginTop: 4 }}>{value.replace(/_/g, ' ')}</div>
                        </div>
                      ))}
                    </div>
                  </SectionCard>
                )}
              </div>
            </div>

            {/* ══ EVENTS & CATALYSTS ══════════════════════════════════════════ */}
            <SectionDivider label="EVENTS & CATALYSTS" />

            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'start' }}>
              {detail.upcoming_events && detail.upcoming_events.length > 0 && (
                <div style={{ flex: '1 1 300px' }}>
                  <UpcomingCatalystsCard events={detail.upcoming_events} />
                </div>
              )}
              {Object.keys(concall).length > 0 && concall.sentiment && (
                <div style={{ flex: '1 1 280px' }}>
                  <SectionCard title="Concall Intelligence" accentColor={String(concall.sentiment) === 'BULLISH' ? P.green : String(concall.sentiment) === 'BEARISH' ? P.red : P.amber}>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 10 }}>
                      {[
                        { label: 'Sentiment', value: String(concall.sentiment ?? ''), color: String(concall.sentiment) === 'BULLISH' ? P.green : String(concall.sentiment) === 'BEARISH' ? P.red : P.amber },
                        { label: 'Guidance',  value: String(concall.guidance_direction ?? ''), color: P.blue },
                        { label: 'Capex',     value: String(concall.capex_signal ?? ''), color: String(concall.capex_signal) === 'YES' ? P.teal : P.dim },
                      ].map(({ label, value, color }) => value && value !== 'undefined' && (
                        <div key={label}>
                          <div style={LABEL}>{label}</div>
                          <Chip label={value.replace(/_/g, ' ')} color={color} size={11} />
                        </div>
                      ))}
                    </div>
                    {concall.key_statement && (
                      <div style={{ fontSize: 11, color: P.text, background: P.cell, padding: '8px 12px', borderRadius: 6, border: `1px solid ${P.border}`, lineHeight: 1.55 }}>
                        "{String(concall.key_statement)}"
                      </div>
                    )}
                    {concall.concall_score != null && <ScoreBar label="Concall Score" value={+concall.concall_score} />}
                  </SectionCard>
                </div>
              )}
              {Object.keys(agm).length > 0 && agm.governance_risk && (
                <div style={{ flex: '1 1 280px' }}>
                  <GovernanceCard agm={agm} />
                </div>
              )}
              {Object.keys(news).length > 0 && news.news_count_7d != null && +news.news_count_7d > 0 && (
                <div style={{ flex: '1 1 280px' }}>
                  <NewsCard news={news} />
                </div>
              )}
            </div>

            {/* ══ ASTRO SIGNAL ═════════════════════════════════════════════════ */}
            {detail.astro && detail.astro.astro_action && (
              <>
                <SectionDivider label="ASTRO SIGNAL" />
                <AstroSignalCard astro={detail.astro as AstroSignal} />
              </>
            )}

            {/* ══ VEDIC KUNDLI + GANN ══════════════════════════════════════════ */}
            <SectionDivider label="VEDIC KUNDLI + GANN" />
            <KundliCard symbol={symbol} />

            {/* ══ CORPORATE ════════════════════════════════════════════════════ */}
            <SectionDivider label="CORPORATE" />

            <TradeIntelligenceCard data={detail!} />
            <CorporateActionsSection symbol={symbol} />
            <AnnouncementsSection symbol={symbol} />

            <div style={{ display: 'flex', gap: 10 }}>
              <Link to={`/sectors/${detail.sector}`} style={{
                flex: 1, display: 'block', textAlign: 'center', padding: '12px 0',
                color: P.blue, fontSize: 12, textDecoration: 'none',
                border: `1px solid ${P.litBdr}`, borderRadius: 8, background: P.cell,
                fontWeight: 700, letterSpacing: 0.5,
              }}>
                View {detail.sector} Sector Intelligence &rarr;
              </Link>
              <Link to={`/report/${symbol}`} style={{
                flexShrink: 0, display: 'flex', alignItems: 'center', gap: 7,
                padding: '12px 20px', textAlign: 'center',
                color: P.green, fontSize: 12, textDecoration: 'none',
                border: `1px solid ${P.green}55`, borderRadius: 8, background: P.green + '0E',
                fontWeight: 700, letterSpacing: 0.5,
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
                Generate Report / PDF
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
