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
  createChart, ColorType, CandlestickSeries, HistogramSeries,
  type IChartApi, type ISeriesApi, type CandlestickData,
  type HistogramData, type Time,
} from 'lightweight-charts'
import {
  api, fetchStockDetail, fetchStockAnnouncements,
  type TechnicalIndicators, type FnoData, type Announcement,
} from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { TradeIntelligenceCard } from '../components/platform/TradeIntelligenceCard'

// ─── Palette ──────────────────────────────────────────────────────────────────

const P = {
  bg:      '#07091A',   // page background
  panel:   '#0B1220',   // card background
  cell:    '#0E1628',   // inner cells / deep areas
  border:  '#182A42',   // default border
  litBdr:  '#223A58',   // highlighted border
  text:    '#E8F1FC',   // primary text  — clearly visible
  sub:     '#7BA3C8',   // secondary text — readable
  dim:     '#3E5E80',   // dim labels only (captions, metadata)
  green:   '#00C97A',   // bullish / positive
  red:     '#FF3851',   // bearish / negative
  blue:    '#3B8BFF',   // FII / institutional
  amber:   '#FFAC00',   // neutral / warning
  purple:  '#A855F7',   // ML / AI / promoter
  teal:    '#0EC4A0',   // DII / secondary bull
}

// ─── Shared inline style shortcuts ────────────────────────────────────────────

const LABEL: React.CSSProperties = {
  fontSize: 9, fontWeight: 800, letterSpacing: 1.5,
  textTransform: 'uppercase', color: P.dim,
}

const CARD_HEADER: React.CSSProperties = {
  padding: '8px 14px',
  fontSize: 9, fontWeight: 800, letterSpacing: 1.8,
  textTransform: 'uppercase', color: P.sub,
  borderBottom: `1px solid ${P.border}`,
  background: P.panel,
}

// ─── Chart types & constants ──────────────────────────────────────────────────

type Bar = { time: string | number; open: number; high: number; low: number; close: number; volume: number }
type OhlcvResponse = { bars: Bar[]; count: number; from: string | number | null; to: string | number | null }
type ChartSignal = {
  symbol?: string; sector?: string; label?: string; bull_run_score?: number
  price_score?: number; sector_flow_score?: number; deal_score?: number; corporate_score?: number
  market_regime?: string; regime_multiplier?: number; as_of_date?: string
  ml_bull_run_score?: number | null; accumulation_score?: number | null
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
    <div style={{ background: P.cell, border: `1px solid ${P.border}`, borderRadius: 7, overflow: 'hidden' }}>
      <div style={{ background: hdrBg, padding: '5px 10px', fontSize: 8, fontWeight: 800, letterSpacing: 1.2, color: 'rgba(255,255,255,0.85)', textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ padding: '10px 10px 8px' }}>
        <div style={{ fontSize: 18, fontWeight: 800, fontFamily: 'monospace', color: valColor ?? P.text, lineHeight: 1.1 }}>{value}</div>
        {sub && <div style={{ fontSize: 9, color: P.sub, marginTop: 4 }}>{sub}</div>}
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
      <span style={{ fontSize: 8, color, fontWeight: 700, minWidth: 20 }}>{diff >= 0 ? 'ABV' : 'BLW'}</span>
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

function AnnouncementsSection({ symbol }: { symbol: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['stock-ann', symbol],
    queryFn: () => fetchStockAnnouncements(symbol, 15),
    staleTime: 5 * 60_000,
  })
  if (isLoading) return <SectionCard title="Corporate Announcements"><span style={{ color: P.dim, fontSize: 11 }}>Loading...</span></SectionCard>
  const items: Announcement[] = data?.announcements ?? []
  if (!items.length) return null
  return (
    <SectionCard title={`Corporate Announcements — latest ${items.length} of ${data?.total ?? 0}`} accentColor={P.blue}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {items.map((a, i) => {
          const tc = ANN_CLR[a.announcement_type] ?? P.sub
          const sc = a.signal_score == null ? P.dim : a.signal_score >= 75 ? P.green : a.signal_score >= 50 ? P.amber : P.dim
          return (
            <div key={a.seq_id || i} style={{
              display: 'flex', gap: 10, padding: '8px 4px',
              borderBottom: i < items.length - 1 ? `1px solid ${P.border}30` : 'none',
              alignItems: 'flex-start',
            }}>
              <div style={{ minWidth: 72, flexShrink: 0 }}>
                <div style={{ fontSize: 9, color: P.dim, fontFamily: 'monospace', marginBottom: 3 }}>{a.date.slice(0, 10)}</div>
                {a.signal_score != null && (
                  <span style={{ fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 3, background: sc + '18', color: sc, border: `1px solid ${sc}33` }}>
                    {a.signal_score}
                  </span>
                )}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ marginBottom: 3 }}>
                  <span style={{ fontSize: 8, fontWeight: 700, padding: '1px 6px', borderRadius: 3, background: tc + '18', color: tc, border: `1px solid ${tc}33`, letterSpacing: 0.4 }}>
                    {a.announcement_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <div style={{ fontSize: 10, color: P.text, lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' } as React.CSSProperties}>
                  {a.title || a.desc}
                </div>
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
  const { symbol: urlSym } = useParams<{ symbol?: string }>()
  const navigate = useNavigate()

  const [symbol, setSymbol] = useState(urlSym?.toUpperCase() ?? '')
  const [tf, setTf]         = useState<TF>('1D')
  const [input, setInput]   = useState(urlSym?.toUpperCase() ?? '')
  const [showDrop, setShowDrop] = useState(false)
  const [acQ, setAcQ]       = useState('')
  const [chartErr, setChartErr] = useState<string | null>(null)

  const chartDiv  = useRef<HTMLDivElement>(null)
  const chartApi  = useRef<IChartApi | null>(null)
  const candleRef = useRef<ISeriesApi<'Candlestick', Time> | null>(null)
  const volRef    = useRef<ISeriesApi<'Histogram', Time> | null>(null)
  const barCount  = useRef(0)

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

  // ── Chart lifecycle ───────────────────────────────────────────────────────

  useEffect(() => {
    if (!chartDiv.current) return
    setChartErr(null)
    let chart: IChartApi | null = null
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
      })
      const vol = chart.addSeries(HistogramSeries, { priceScaleId: 'vol' })
      vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
      chartApi.current = chart; candleRef.current = candles; volRef.current = vol
    } catch (e) { setChartErr(e instanceof Error ? e.message : String(e)); chart?.remove() }
    return () => { chartApi.current?.remove(); chartApi.current = candleRef.current = volRef.current = null }
  }, [])

  useEffect(() => {
    chartApi.current?.applyOptions({ timeScale: { timeVisible: INTRADAY.has(tf), secondsVisible: false } })
  }, [tf])

  useEffect(() => {
    if (!ohlcv || !candleRef.current || !volRef.current) return
    try {
      const bars = ohlcv.bars
      const cs: CandlestickData<Time>[] = bars.map(b => ({
        time: (typeof b.time === 'string' ? toPeriodStart(b.time, tf) : b.time) as Time,
        open: b.open, high: b.high, low: b.low, close: b.close,
      }))
      const vs: HistogramData<Time>[] = bars.map(b => ({
        time: (typeof b.time === 'string' ? toPeriodStart(b.time, tf) : b.time) as Time,
        value: b.volume ?? 0,
        color: b.close >= b.open ? P.green + '55' : P.red + '55',
      }))
      candleRef.current.setData(cs); volRef.current.setData(vs)
      barCount.current = cs.length
      if (cs.length > 0 && chartApi.current)
        chartApi.current.timeScale().setVisibleLogicalRange({ from: Math.max(0, cs.length - DEFAULT_BARS[tf]), to: cs.length + 3 })
    } catch (e) { setChartErr(e instanceof Error ? e.message : String(e)) }
  }, [ohlcv, tf])

  const resetChart = useCallback(() => {
    if (!chartApi.current) return
    chartApi.current.timeScale().setVisibleLogicalRange({ from: Math.max(0, barCount.current - DEFAULT_BARS[tf]), to: barCount.current + 3 })
  }, [tf])

  // ── Symbol selection ──────────────────────────────────────────────────────

  const selectSymbol = useCallback((s: string) => {
    const sym = s.trim().toUpperCase(); if (!sym) return
    setSymbol(sym); setInput(sym); setShowDrop(false); setAcQ('')
    navigate(`/stocks/${sym}`, { replace: true })
  }, [navigate])

  // ── Derived values ────────────────────────────────────────────────────────

  const latest   = ohlcv?.bars.at(-1)
  const prev     = ohlcv?.bars.at(-2)
  const priceChg = latest && prev ? ((latest.close - prev.close) / prev.close) * 100 : null
  const close    = detail?.close_now ?? latest?.close ?? 0
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

  // ── No-symbol state ───────────────────────────────────────────────────────

  if (!symbol) return (
    <div style={{ background: P.bg, minHeight: 'calc(100vh - 112px)' }}>
      <div style={{ padding: '10px 0' }}>
        <button onClick={() => navigate(-1)} style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'none', border: `1px solid ${P.border}`, color: P.sub, cursor: 'pointer', padding: '4px 12px', borderRadius: 4, fontSize: 11 }}>
          &larr; Back
        </button>
      </div>
      <SearchPrompt onSelect={selectSymbol} />
    </div>
  )

  // ── Full view ─────────────────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0, background: P.bg }}>

      {/* ── Sticky header: back + search + price ─────────────────────── */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: P.panel, borderBottom: `1px solid ${P.border}`,
        padding: '10px 0', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
      }}>
        <button onClick={() => navigate(-1)} style={{
          display: 'flex', alignItems: 'center', gap: 4, background: 'none',
          border: `1px solid ${P.border}`, color: P.sub, cursor: 'pointer',
          padding: '5px 12px', borderRadius: 4, fontSize: 11, flexShrink: 0,
        }}>&larr; Back</button>

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

        {/* Price + change */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <span style={{ fontSize: 22, fontWeight: 900, color: P.text, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>
            {close > 0 ? `₹${close.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : (latest ? `₹${latest.close.toFixed(2)}` : '—')}
          </span>
          {priceChg != null && (
            <span style={{ fontSize: 13, fontWeight: 700, color: priceChg >= 0 ? P.green : P.red }}>
              {priceChg >= 0 ? '+' : ''}{priceChg.toFixed(2)}%
            </span>
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
            style={{ fontSize: 9, color: P.blue, textDecoration: 'none', border: `1px solid ${P.litBdr}`, padding: '2px 7px', borderRadius: 3 }}>
            NSE ↗
          </a>
        </div>

        {/* Score chips (right-aligned) */}
        <div style={{ display: 'flex', gap: 14, marginLeft: 'auto', alignItems: 'center', flexShrink: 0 }}>
          {detail && <ScoreGauge score={detail.bull_run_score} size={52} />}
          {detail?.ml_scores?.ml_bull_run_score != null && (
            <div style={{ textAlign: 'center' }}>
              <ScoreGauge score={detail.ml_scores.ml_bull_run_score} size={44} />
              <div style={{ fontSize: 8, color: P.dim, marginTop: 2 }}>ML</div>
            </div>
          )}
        </div>
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

          {/* OHLCV footer */}
          {latest && (
            <div style={{ display: 'flex', gap: 20, padding: '7px 14px', fontSize: 10, color: P.sub, background: P.cell, borderTop: `1px solid ${P.border}`, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums', flexWrap: 'wrap' }}>
              <span>O <span style={{ color: P.text }}>{latest.open.toFixed(2)}</span></span>
              <span>H <span style={{ color: P.green }}>{latest.high.toFixed(2)}</span></span>
              <span>L <span style={{ color: P.red }}>{latest.low.toFixed(2)}</span></span>
              <span>C <span style={{ color: P.text }}>{latest.close.toFixed(2)}</span></span>
              <span>Vol <span style={{ color: P.text }}>{((latest.volume ?? 0) / 1e6).toFixed(2)}M</span></span>
              {ohlcv && <span style={{ marginLeft: 'auto', color: P.dim }}>{ohlcv.count} bars | {fmtOhlcTime(ohlcv.from)} — {fmtOhlcTime(ohlcv.to)}</span>}
            </div>
          )}
        </div>

        {/* ── Score + ML strip ──────────────────────────────────────────── */}
        {(detail || sig) && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
            {[
              { label: 'Price Momentum',    value: detail?.components?.price_score       ?? sig?.price_score },
              { label: 'Sector Flow',        value: detail?.components?.sector_flow_score ?? sig?.sector_flow_score },
              { label: 'Block Deals',        value: detail?.components?.deal_score        ?? sig?.deal_score },
              { label: 'Corp Events',        value: detail?.components?.corporate_score   ?? sig?.corporate_score },
              { label: 'ML Bull Run',        value: detail?.ml_scores?.ml_bull_run_score  ?? sig?.ml_bull_run_score },
              { label: 'Accumulation',       value: detail?.ml_scores?.accumulation_score ?? sig?.accumulation_score },
            ].filter(m => m.value != null).map(({ label, value }) => {
              const c = scoreC(value!)
              return (
                <div key={label} style={{ background: P.panel, border: `1px solid ${P.border}`, borderRadius: 7, padding: '10px 14px', borderLeft: `3px solid ${c}` }}>
                  <div style={LABEL}>{label}</div>
                  <div style={{ fontSize: 22, fontWeight: 900, color: c, fontFamily: 'monospace', marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>
                    {value!.toFixed(0)}
                  </div>
                  <div style={{ height: 3, background: P.border, borderRadius: 2, marginTop: 6 }}>
                    <div style={{ width: `${Math.min(value!, 100)}%`, height: '100%', background: c, borderRadius: 2 }} />
                  </div>
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
            {/* ── Analyst insights ──────────────────────────────────── */}
            {insights && insights.length > 0 && (
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
            )}

            {/* ── Fundamentals — Row 1: Financial Size ──────────────── */}
            {Object.keys(fund).length > 0 && (
              <div>
                <div style={CARD_HEADER}>Fundamentals</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginTop: 10 }}>

                  {/* Row 1 — Financial Size */}
                  <FundTile label="Market Cap (₹ Cr)" hdrBg="#1A3A6E" valColor={P.text}
                    value={fund.market_cap_cr != null ? crFmt(+fund.market_cap_cr) : '--'}
                    sub={fund.shares_outstanding_cr != null ? `${(+fund.shares_outstanding_cr).toFixed(1)} Cr shares` : 'estimated'} />
                  <FundTile label="Book Value (₹)" hdrBg="#2D1B4E"
                    valColor={fund.book_value_per_share != null ? P.text : P.sub}
                    value={fund.book_value_per_share != null ? `₹${(+fund.book_value_per_share).toLocaleString('en-IN', {maximumFractionDigits: 0})}` : '---'}
                    sub={fund.total_equity_cr != null ? `Equity ${crFmt(+fund.total_equity_cr)}` : 'balance sheet pending'} />
                  <FundTile label="Sales (₹ Cr)" hdrBg="#1A3A6E" valColor={P.text}
                    value={fund.revenue_ttm_cr != null ? crFmt(+fund.revenue_ttm_cr) : '--'}
                    sub={fund.as_of_date ? `TTM as of ${String(fund.as_of_date).slice(0,7)}` : 'trailing 12M'} />
                  <FundTile label="PAT (₹ Cr)" hdrBg="#2D1B4E"
                    value={fund.profit_ttm_cr != null ? crFmt(+fund.profit_ttm_cr) : '--'}
                    valColor={fund.profit_ttm_cr == null ? P.sub : +fund.profit_ttm_cr >= 0 ? P.text : P.red}
                    sub="profit after tax TTM" />

                  {/* Row 2 — Performance vs History */}
                  <FundTile label="Return over 1Y (%)"
                    hdrBg={detail.price.ret_365d != null && detail.price.ret_365d >= 0 ? '#062014' : '#200606'}
                    value={pct(detail.price.ret_365d)}
                    valColor={detail.price.ret_365d == null ? P.sub : detail.price.ret_365d >= 0 ? P.green : P.red}
                    sub="365-day price return" />
                  <FundTile label="Down from ATH (%)"
                    hdrBg={fund.down_from_ath_pct != null && +fund.down_from_ath_pct >= -15 ? '#062014' : '#1A0D00'}
                    value={fund.down_from_ath_pct != null ? `${(+fund.down_from_ath_pct).toFixed(1)}%` : '--'}
                    valColor={fund.down_from_ath_pct == null ? P.sub : +fund.down_from_ath_pct >= -15 ? P.teal : +fund.down_from_ath_pct >= -40 ? P.amber : P.red}
                    sub={fund.ath_price != null ? `ATH ₹${(+fund.ath_price).toFixed(0)}` : 'all-time high'} />
                  <FundTile label="OPM (%)" hdrBg="#0A1A2E"
                    valColor={fund.opm_pct == null ? P.sub : +fund.opm_pct >= 20 ? P.green : +fund.opm_pct >= 10 ? P.teal : +fund.opm_pct >= 0 ? P.amber : P.red}
                    value={fund.opm_pct != null ? `${(+fund.opm_pct).toFixed(1)}%` : '---'}
                    sub={fund.ebitda_cr_latest != null ? `EBITDA ${crFmt(+fund.ebitda_cr_latest)} qtr` : 'EBITDA data pending'} />
                  <FundTile label={`${fund.qtr_growth_period ?? 'Qtr'} Sales Growth (%)`}
                    hdrBg={fund.qtr_sales_growth_pct != null && +fund.qtr_sales_growth_pct >= 0 ? '#062014' : '#200606'}
                    value={fund.qtr_sales_growth_pct != null ? `${+fund.qtr_sales_growth_pct >= 0 ? '+' : ''}${(+fund.qtr_sales_growth_pct).toFixed(1)}%` : '--'}
                    valColor={fund.qtr_sales_growth_pct == null ? P.sub : +fund.qtr_sales_growth_pct >= 10 ? P.green : +fund.qtr_sales_growth_pct >= 0 ? P.teal : P.red}
                    sub="vs prior period revenue" />

                  {/* Row 3 — Profitability & Returns */}
                  <FundTile label={`${fund.qtr_growth_period ?? 'Qtr'} Profit Growth (%)`}
                    hdrBg={fund.qtr_profit_growth_pct != null && +fund.qtr_profit_growth_pct >= 0 ? '#062014' : '#200606'}
                    value={fund.qtr_profit_growth_pct != null ? `${+fund.qtr_profit_growth_pct >= 0 ? '+' : ''}${(+fund.qtr_profit_growth_pct).toFixed(1)}%` : '--'}
                    valColor={fund.qtr_profit_growth_pct == null ? P.sub : +fund.qtr_profit_growth_pct >= 10 ? P.green : +fund.qtr_profit_growth_pct >= 0 ? P.teal : P.red}
                    sub="vs prior period PAT" />
                  <FundTile label="ROCE (%)" hdrBg="#0A1A2E"
                    valColor={fund.roce_pct == null ? P.sub : +fund.roce_pct >= 20 ? P.green : +fund.roce_pct >= 12 ? P.teal : +fund.roce_pct >= 0 ? P.amber : P.red}
                    value={fund.roce_pct != null ? `${(+fund.roce_pct).toFixed(1)}%` : '---'}
                    sub={fund.capital_employed_cr != null ? `CE ${crFmt(+fund.capital_employed_cr)}` : 'capital employed pending'} />
                  <FundTile label="ROE (%)" hdrBg="#0A2A1F"
                    value={fund.roe_pct != null ? `${(+fund.roe_pct).toFixed(1)}%` : '--'}
                    valColor={fund.roe_pct == null ? P.sub : +fund.roe_pct >= 20 ? P.green : +fund.roe_pct >= 12 ? P.teal : P.red}
                    sub="return on equity" />
                  <FundTile
                    label={`Sales Growth ${fund.sales_growth_years != null ? `${(+fund.sales_growth_years).toFixed(0)}Y` : '3Y'} (%)`}
                    hdrBg={fund.sales_growth_3y_pct != null && +fund.sales_growth_3y_pct >= 0 ? '#062014' : '#200606'}
                    valColor={fund.sales_growth_3y_pct == null ? P.sub : +fund.sales_growth_3y_pct >= 15 ? P.green : +fund.sales_growth_3y_pct >= 5 ? P.teal : +fund.sales_growth_3y_pct >= 0 ? P.amber : P.red}
                    value={fund.sales_growth_3y_pct != null ? `${+fund.sales_growth_3y_pct >= 0 ? '+' : ''}${(+fund.sales_growth_3y_pct).toFixed(1)}%` : '---'}
                    sub={fund.sales_growth_years != null ? `${(+fund.sales_growth_years).toFixed(1)}Y revenue CAGR` : 'needs 4+ quarters'} />
                </div>

                {/* Row 4 — Valuation & Technical */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 10, marginTop: 10 }}>
                  <FundTile label="P/E Ratio" hdrBg="#2A1800"
                    value={fund.pe_ratio != null ? `${(+fund.pe_ratio).toFixed(1)}x` : '--'}
                    valColor={fund.pe_ratio == null ? P.sub : +fund.pe_ratio < 15 ? P.green : +fund.pe_ratio > 40 ? P.red : P.amber}
                    sub="price to earnings" />
                  <FundTile label="vs 200 DMA" hdrBg={t?.vs_dma_200 != null && t.vs_dma_200 >= 0 ? '#062014' : '#200606'}
                    value={t?.vs_dma_200 != null ? `${t.vs_dma_200 >= 0 ? '+' : ''}${t.vs_dma_200.toFixed(1)}%` : '--'}
                    valColor={t?.vs_dma_200 == null ? P.sub : t.vs_dma_200 >= 5 ? P.green : t.vs_dma_200 >= 0 ? P.teal : P.red}
                    sub="long-term trend" />
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
                  <FundTile label="Valuation"
                    hdrBg={fund.valuation_label === 'CHEAP_QUALITY' ? '#052E16' : fund.valuation_label === 'FAIR_VALUE' ? '#0C1A3A' : fund.valuation_label === 'EXPENSIVE' ? '#2D0A0A' : '#1A1228'}
                    value={<span style={{ fontSize: 13 }}>{String(fund.valuation_label ?? 'N/A').replace(/_/g, ' ')}</span>}
                    valColor={fund.valuation_label === 'CHEAP_QUALITY' ? P.green : fund.valuation_label === 'FAIR_VALUE' ? P.blue : fund.valuation_label === 'EXPENSIVE' ? P.red : P.amber}
                    sub={fund.valuation_score != null ? `score ${(+fund.valuation_score).toFixed(0)}/100` : ''} />
                </div>
              </div>
            )}

            {/* ── Two-column intelligence grid ───────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>

              {/* LEFT */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

                {/* Technicals */}
                {t && (
                  <SectionCard title="Technical Indicators" accentColor={trendColor}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                      <Chip label={t.trend_signal?.replace(/_/g, ' ') ?? 'N/A'} color={trendColor} size={11} />
                      {t.vol_20d_avg != null && <span style={{ color: P.sub, fontSize: 10 }}>Avg Vol {(t.vol_20d_avg / 1e5).toFixed(1)}L shares/day</span>}
                    </div>
                    {t.high_52w != null && t.low_52w != null && (
                      <div style={{ marginBottom: 14 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: P.dim, marginBottom: 5 }}>
                          <span>52W Low ₹{t.low_52w.toFixed(0)}</span>
                          <span>52W High ₹{t.high_52w.toFixed(0)}</span>
                        </div>
                        <div style={{ height: 6, background: '#1A2740', borderRadius: 3, position: 'relative' }}>
                          {(() => {
                            const pos = (close - t.low_52w!) / (t.high_52w! - t.low_52w!) * 100
                            return (
                              <>
                                <div style={{ width: `${pos}%`, height: '100%', background: `linear-gradient(to right, ${P.border}, ${P.green}55)`, borderRadius: 3 }} />
                                <div style={{ position: 'absolute', top: -4, left: `${pos}%`, width: 14, height: 14, borderRadius: '50%', background: pos >= 80 ? P.green : pos >= 40 ? P.amber : P.red, transform: 'translateX(-50%)', border: `2px solid ${P.bg}`, boxShadow: `0 0 8px ${pos >= 80 ? P.green : pos >= 40 ? P.amber : P.red}88` }} />
                              </>
                            )
                          })()}
                        </div>
                      </div>
                    )}
                    <DMARow label="20 DMA"  dma={t.dma_20}  close={close} color={P.blue} />
                    <DMARow label="50 DMA"  dma={t.dma_50}  close={close} color="#A78BFA" />
                    <DMARow label="200 DMA" dma={t.dma_200} close={close} color={P.amber} />
                    {t.as_of_date && <div style={{ fontSize: 9, color: P.dim, marginTop: 8 }}>as of {t.as_of_date}</div>}
                  </SectionCard>
                )}

                {/* Concall signal */}
                {Object.keys(concall).length > 0 && concall.sentiment && (
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
                )}

                {/* AGM signal */}
                {Object.keys(agm).length > 0 && agm.governance_risk && (
                  <SectionCard title={`Governance Signal${agm.date ? ` (${agm.date})` : ''}`}
                    accentColor={String(agm.governance_risk) === 'LOW' ? P.green : String(agm.governance_risk) === 'HIGH' ? P.red : P.amber}>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 10 }}>
                      {[
                        { label: 'Risk',        value: String(agm.governance_risk), color: String(agm.governance_risk) === 'LOW' ? P.green : P.red },
                        { label: 'Dividend',    value: String(agm.dividend_signal ?? ''), color: P.green, hide: String(agm.dividend_signal) === 'NONE' },
                        { label: 'Mgmt Change', value: 'CHANGE', color: P.amber, hide: String(agm.management_change) !== 'YES' },
                        { label: 'Capex',       value: 'CONFIRMED', color: P.teal, hide: String(agm.capex_confirm) !== 'YES' },
                      ].filter(({ hide }) => !hide).map(({ label, value, color }) => value && (
                        <div key={label}>
                          <div style={LABEL}>{label}</div>
                          <div style={{ marginTop: 5 }}><Chip label={value} color={color} size={11} /></div>
                        </div>
                      ))}
                    </div>
                    {agm.key_decision && (
                      <div style={{ fontSize: 11, color: P.text, background: P.cell, padding: '8px 12px', borderRadius: 6, border: `1px solid ${P.border}`, lineHeight: 1.55 }}>
                        {String(agm.key_decision)}
                      </div>
                    )}
                  </SectionCard>
                )}

                {/* News signal */}
                {Object.keys(news).length > 0 && news.news_count_7d != null && +news.news_count_7d > 0 && (
                  <SectionCard title="Recent News Signal" accentColor={P.blue}>
                    <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                      {[
                        { label: 'Articles (7D)', value: String(news.news_count_7d), color: P.text },
                        { label: 'Sentiment',     value: String(news.sentiment_label ?? ''), color: String(news.sentiment_label) === 'BULLISH' ? P.green : String(news.sentiment_label) === 'BEARISH' ? P.red : P.amber },
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
                      <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        <span style={{ ...LABEL, alignSelf: 'center' }}>Themes:</span>
                        {String(news.top_theme).split(',').map(th => (
                          <Chip key={th.trim()} label={th.trim()} color={P.blue} size={9} />
                        ))}
                      </div>
                    )}
                  </SectionCard>
                )}

                {/* F&O */}
                {f && f.oi_signal && (
                  <SectionCard title="Futures & Options" accentColor={f.oi_signal.includes('LONG') ? P.green : P.red}>
                    {(() => {
                      const OI_MAP: Record<string, string> = { LONG_BUILDUP: P.green, SHORT_BUILDUP: P.red, LONG_UNWINDING: P.amber, SHORT_COVERING: P.teal }
                      const OI_TEXT: Record<string, string> = { LONG_BUILDUP: 'Big traders buying fresh — bullish', SHORT_BUILDUP: 'Traders betting on fall — bearish', LONG_UNWINDING: 'Buyers exiting — weakening', SHORT_COVERING: 'Bears buying back — potential reversal' }
                      const c = OI_MAP[f.oi_signal] ?? P.sub
                      return (
                        <>
                          <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 10 }}>
                            <div><div style={LABEL}>Signal</div><div style={{ marginTop: 5 }}><Chip label={f.oi_signal.replace(/_/g, ' ')} color={c} size={11} /></div></div>
                            {f.futures_oi != null && <div><div style={LABEL}>Open Interest</div><div style={{ fontSize: 16, fontWeight: 800, color: P.text, marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{(f.futures_oi / 1e6).toFixed(2)}M</div></div>}
                            {f.oi_1d != null && <div><div style={LABEL}>1D Change</div><div style={{ fontSize: 16, fontWeight: 800, color: f.oi_1d >= 0 ? P.green : P.red, marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{f.oi_1d >= 0 ? '+' : ''}{f.oi_1d.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div></div>}
                            {f.oi_5d != null && <div><div style={LABEL}>5D Change</div><div style={{ fontSize: 16, fontWeight: 800, color: f.oi_5d >= 0 ? P.green : P.red, marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>{f.oi_5d >= 0 ? '+' : ''}{f.oi_5d.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div></div>}
                          </div>
                          {OI_TEXT[f.oi_signal] && <div style={{ fontSize: 11, color: c, background: c + '12', border: `1px solid ${c}33`, padding: '7px 10px', borderRadius: 5 }}>{OI_TEXT[f.oi_signal]}</div>}
                        </>
                      )
                    })()}
                  </SectionCard>
                )}
              </div>

              {/* RIGHT */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

                {/* Score breakdown */}
                <SectionCard title="Bull Run Score Breakdown">
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                    {[
                      { label: 'Price Momentum', value: detail.components.price_score,       sub: '30% weight' },
                      { label: 'Sector Flow',    value: detail.components.sector_flow_score, sub: '25% weight' },
                      { label: 'Block Deals',    value: detail.components.deal_score,        sub: '25% weight' },
                      { label: 'Corp Events',    value: detail.components.corporate_score,   sub: '20% weight' },
                    ].map(({ label, value, sub }) => {
                      const c = scoreC(value)
                      return (
                        <div key={label} style={{ background: P.cell, border: `1px solid ${P.border}`, borderRadius: 6, padding: '10px 12px' }}>
                          <div style={{ fontSize: 22, fontWeight: 900, color: c, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{value.toFixed(0)}</div>
                          <div style={{ height: 3, background: P.border, borderRadius: 2, margin: '6px 0' }}>
                            <div style={{ width: `${value}%`, height: '100%', background: c, borderRadius: 2 }} />
                          </div>
                          <div style={{ color: P.sub, fontSize: 9 }}>{label}</div>
                          <div style={{ color: P.dim, fontSize: 8 }}>{sub}</div>
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

                {/* Holding trends */}
                {trends.length > 0 && (
                  <SectionCard title="Shareholding Trends (QoQ)" accentColor={P.purple}>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
                        <thead>
                          <tr>
                            {['Period', 'Promoter', 'FII', 'DII', 'Signal'].map(h => (
                              <th key={h} style={{ padding: '4px 8px', textAlign: h === 'Period' ? 'left' : 'right', color: P.dim, fontSize: 8, fontWeight: 700, letterSpacing: 1, borderBottom: `1px solid ${P.border}` }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {trends.map((r, i) => {
                            const sig_ = String(r.conviction_signal ?? '')
                            const sc = sig_.includes('ACCUMULATION') ? P.green : sig_.includes('DISTRIBUTION') ? P.red : P.dim
                            return (
                              <tr key={i} style={{ borderBottom: `1px solid ${P.border}20` }}>
                                <td style={{ padding: '5px 8px', color: P.sub, fontFamily: 'monospace', fontSize: 10 }}>{String(r.period ?? '')}</td>
                                {(['promoter_pct', 'fii_pct', 'dii_pct'] as const).map(k => {
                                  const dk = k + '_delta'
                                  const val = r[k]; const delta = r[dk]
                                  return (
                                    <td key={k} style={{ padding: '5px 8px', textAlign: 'right', color: P.text, fontVariantNumeric: 'tabular-nums' }}>
                                      {val != null ? `${(+val).toFixed(2)}%` : '--'}
                                      {delta != null && <span style={{ color: +delta >= 0 ? P.green : P.red, marginLeft: 4, fontSize: 9 }}>{+delta >= 0 ? '+' : ''}{(+delta).toFixed(2)}</span>}
                                    </td>
                                  )
                                })}
                                <td style={{ padding: '5px 8px', textAlign: 'right' }}>
                                  {sig_ && <span style={{ fontSize: 8, fontWeight: 700, color: sc, padding: '1px 5px', background: sc + '18', border: `1px solid ${sc}33`, borderRadius: 3 }}>{sig_.replace(/_/g, ' ')}</span>}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </SectionCard>
                )}

                {/* Deal signals */}
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

                {/* Management score */}
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

                {/* Consensus */}
                {Object.keys(consensus).length > 0 && consensus.consensus_action && (
                  <SectionCard title="Multi-Signal Consensus" accentColor={String(consensus.consensus_action) === 'BUY' ? P.green : String(consensus.consensus_action) === 'SELL' ? P.red : P.amber}>
                    <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
                      {[
                        { label: 'Action',    value: String(consensus.consensus_action ?? ''),  color: String(consensus.consensus_action) === 'BUY' ? P.green : String(consensus.consensus_action) === 'SELL' ? P.red : P.amber },
                        { label: 'Confidence',value: String(consensus.confidence ?? ''),        color: P.blue },
                        { label: 'Signals In',value: String(consensus.signals_in ?? ''),        color: P.text },
                      ].map(({ label, value, color }) => value && (
                        <div key={label}>
                          <div style={LABEL}>{label}</div>
                          <div style={{ fontSize: 16, fontWeight: 800, color, marginTop: 4 }}>{value.replace(/_/g, ' ')}</div>
                        </div>
                      ))}
                    </div>
                  </SectionCard>
                )}

                {/* Sector link */}
                <Link to={`/sectors/${detail.sector}`} style={{
                  display: 'block', textAlign: 'center', padding: '12px 0',
                  color: P.blue, fontSize: 12, textDecoration: 'none',
                  border: `1px solid ${P.litBdr}`, borderRadius: 8, background: P.cell,
                  fontWeight: 700, letterSpacing: 0.5,
                }}>
                  View {detail.sector} Sector Intelligence &rarr;
                </Link>
              </div>
            </div>

            {/* ── Trade Intelligence (full width) ────────────────────── */}
            <TradeIntelligenceCard data={detail!} />

            {/* ── Announcements (full width) ─────────────────────────── */}
            <AnnouncementsSection symbol={symbol} />

          </>
        )}
      </div>
    </div>
  )
}
