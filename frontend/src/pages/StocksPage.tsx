import { useEffect, useRef, useState, useCallback, useMemo, Component, type ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  createChart, ColorType,
  CandlestickSeries, HistogramSeries,
  type IChartApi, type ISeriesApi,
  type CandlestickData, type HistogramData, type Time,
} from 'lightweight-charts'
import { api, fetchAllStocks, type Stock } from '../api/client'

// ─── Design tokens ─────────────────────────────────────────────────────────

const T = {
  bg:        '#07091C',
  bgPanel:   '#0B1120',
  bgCard:    '#0E1628',
  bgActive:  '#0F1D35',
  bgHover:   '#0C1525',
  border:    '#162035',
  borderLit: '#1E3050',
  text:      '#DDE9F8',
  sub:       '#7A9EC0',
  dim:       '#3E5A75',
  green:     '#00D68F',
  red:       '#FF3B5C',
  blue:      '#4088FF',
  amber:     '#FFAD00',
  purple:    '#A855F7',
  teal:      '#0EC9A4',
}

// ─── Chart types ────────────────────────────────────────────────────────────

type Bar = { time: string | number; open: number; high: number; low: number; close: number; volume: number }
type OhlcvResponse = { symbol: string; timeframe: string; bars: Bar[]; count: number; from: string | number | null; to: string | number | null }
type Signal = {
  symbol: string; bull_run_score?: number; label?: string
  price_score?: number; sector_flow_score?: number; deal_score?: number; corporate_score?: number
  market_regime?: string; regime_multiplier?: number; sector?: string; as_of_date?: string
  ml_bull_run_score?: number | null; accumulation_score?: number | null
  rotation_signal?: string; sector_combined?: number
  shp_fii_pct?: number | null; shp_dii_pct?: number | null; shp_promoter_pct?: number | null; shp_quarter?: string
}
type SymbolResult = { SYMBOL: string; COMPANY_NAME: string }
type Timeframe = '5M' | '15M' | '1H' | '1D' | '1W' | '1M' | '3M'
type SortKey = 'bull_run_score' | 'close_now' | 'ret_30d' | 'ret_365d' | 'vol_ratio'
type SortDir = 'asc' | 'desc'

const INTRADAY = new Set<Timeframe>(['5M', '15M', '1H'])
const TF_GROUPS: [Timeframe[], Timeframe[]] = [
  ['5M', '15M', '1H'],
  ['1D', '1W', '1M', '3M'],
]
const DEFAULT_BARS: Record<Timeframe, number> = { '5M': 200, '15M': 200, '1H': 180, '1D': 180, '1W': 52, '1M': 24, '3M': 16 }
const LABELS = ['ALL', 'STRONG_CANDIDATE', 'EMERGING', 'WATCHLIST', 'NEUTRAL', 'AVOID']
const LABEL_COLOR: Record<string, string> = {
  STRONG_CANDIDATE: T.green, EMERGING: T.blue, WATCHLIST: T.amber,
  NEUTRAL: T.dim, AVOID: T.red,
}
const TREND_MAP: Record<string, { color: string; short: string }> = {
  STRONG_UPTREND:    { color: T.green,  short: 'SUP' },
  UPTREND:           { color: T.teal,   short: 'UP'  },
  CONSOLIDATING:     { color: T.amber,  short: 'CON' },
  DOWNTREND:         { color: T.red,    short: 'DWN' },
  INSUFFICIENT_DATA: { color: T.dim,    short: '---' },
}

// ─── API helpers ────────────────────────────────────────────────────────────

const fetchOhlcv = (symbol: string, tf: Timeframe): Promise<OhlcvResponse> =>
  api.get('/charts/ohlcv', { params: { symbol, timeframe: tf } }).then(r => r.data)
const fetchSignals = (symbol: string): Promise<Signal> =>
  api.get('/charts/signals', { params: { symbol } }).then(r => r.data)
const fetchSymbols = (q: string): Promise<{ symbols: SymbolResult[] }> =>
  api.get('/charts/symbols', { params: { q } }).then(r => r.data)

// ─── Helpers ────────────────────────────────────────────────────────────────

function toPeriodStart(dateStr: string, tf: Timeframe): string {
  if (tf === '1D' || INTRADAY.has(tf)) return dateStr
  const d = new Date(dateStr + 'T00:00:00Z')
  if (tf === '1W') {
    const off = d.getUTCDay() === 0 ? 6 : d.getUTCDay() - 1
    d.setUTCDate(d.getUTCDate() - off)
  } else if (tf === '1M') {
    d.setUTCDate(1)
  } else if (tf === '3M') {
    d.setUTCMonth(Math.floor(d.getUTCMonth() / 3) * 3, 1)
  }
  return d.toISOString().slice(0, 10)
}

function fmtBarTime(t: string | number | null | undefined): string {
  if (t == null) return ''
  if (typeof t === 'number') {
    return new Date(t * 1000).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: '2-digit',
      hour: '2-digit', minute: '2-digit',
    })
  }
  return t
}

function scoreColor(v: number | null | undefined): string {
  if (v == null) return T.dim
  return v >= 68 ? T.green : v >= 45 ? T.amber : T.red
}

function pctColor(v: number | null | undefined): string {
  if (v == null) return T.dim
  return v >= 0 ? T.green : T.red
}

function pctStr(v: number | null | undefined): string {
  if (v == null) return '--'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}

// ─── Chart error boundary ───────────────────────────────────────────────────

class ChartBoundary extends Component<{ children: ReactNode }, { err: string | null }> {
  constructor(p: { children: ReactNode }) { super(p); this.state = { err: null } }
  static getDerivedStateFromError(e: unknown) { return { err: e instanceof Error ? e.message : String(e) } }
  render() {
    if (this.state.err) return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 12 }}>
        <span style={{ color: T.red, fontSize: 14, fontWeight: 700 }}>Chart Error</span>
        <span style={{ color: T.sub, fontSize: 11, maxWidth: 360, textAlign: 'center' }}>{this.state.err}</span>
        <button onClick={() => this.setState({ err: null })} style={{ padding: '5px 16px', borderRadius: 4, border: `1px solid ${T.red}`, background: 'transparent', color: T.red, cursor: 'pointer', fontSize: 11 }}>Retry</button>
      </div>
    )
    return this.props.children
  }
}

// ─── Score mini-bar ─────────────────────────────────────────────────────────

function MiniBar({ value, max = 100 }: { value: number | null | undefined; max?: number }) {
  if (value == null) return <span style={{ color: T.dim, fontSize: 10 }}>--</span>
  const pct = Math.min(Math.max(value / max, 0), 1) * 100
  const color = scoreColor(value)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
      <div style={{ width: 36, height: 3, background: T.border, borderRadius: 2, flexShrink: 0 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 10, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>{value.toFixed(0)}</span>
    </div>
  )
}

// ─── Intelligence metric card ────────────────────────────────────────────────

function MetricCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{
      flex: 1, minWidth: 0, background: T.bgCard, border: `1px solid ${T.border}`,
      borderRadius: 6, padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6,
    }}>
      <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.4, color: T.dim, textTransform: 'uppercase' }}>{title}</div>
      {children}
    </div>
  )
}

function ScoreLine({ label, value, max = 100 }: { label: string; value: number | null | undefined; max?: number }) {
  if (value == null) return null
  const pct = Math.min(Math.max(value / max, 0), 1) * 100
  const color = max === 100 ? scoreColor(value) : value >= max * 0.6 ? T.green : value >= max * 0.35 ? T.amber : T.red
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: 9, color: T.sub }}>{label}</span>
        <span style={{ fontSize: 10, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ height: 2, background: T.border, borderRadius: 1 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 1, transition: 'width 0.4s' }} />
      </div>
    </div>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────

export function StocksPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Shared selected symbol
  const [symbol, setSymbol]           = useState((searchParams.get('symbol') || 'RELIANCE').toUpperCase())

  // Chart state
  const [timeframe, setTimeframe]     = useState<Timeframe>('1D')
  const [chartInput, setChartInput]   = useState(symbol)
  const [showDrop, setShowDrop]       = useState(false)
  const [searchQ, setSearchQ]         = useState('')
  const [chartError, setChartError]   = useState<string | null>(null)

  // Chart DOM refs
  const chartRef    = useRef<HTMLDivElement>(null)
  const chartApi    = useRef<IChartApi | null>(null)
  const candleRef   = useRef<ISeriesApi<'Candlestick', Time> | null>(null)
  const volumeRef   = useRef<ISeriesApi<'Histogram', Time> | null>(null)
  const barCountRef = useRef(0)

  // Screener state
  const [page,         setPage]         = useState(1)
  const [labelFilter,  setLabelFilter]  = useState('EMERGING')
  const [listSearch,   setListSearch]   = useState('')
  const [sectorFilter, setSectorFilter] = useState('ALL')
  const [sortKey,      setSortKey]      = useState<SortKey>('bull_run_score')
  const [sortDir,      setSortDir]      = useState<SortDir>('desc')

  // ── Data queries ─────────────────────────────────────────────────────────

  const { data: symbolAC } = useQuery({
    queryKey: ['stocks-sym-ac', searchQ],
    queryFn:  () => fetchSymbols(searchQ),
    enabled:  showDrop && searchQ.length > 0,
    staleTime: 30_000,
  })

  const { data: ohlcv, isLoading: chartLoading, isError: chartIsError, error: chartErrObj } = useQuery({
    queryKey: ['stocks-ohlcv', symbol, timeframe],
    queryFn:  () => fetchOhlcv(symbol, timeframe),
    staleTime: 5 * 60_000,
    retry: 1,
  })

  const { data: signals } = useQuery({
    queryKey: ['stocks-signals', symbol],
    queryFn:  () => fetchSignals(symbol),
    staleTime: 5 * 60_000,
  })

  const { data: stocksData, isLoading: listLoading } = useQuery({
    queryKey: ['stocks-list', page, labelFilter, sectorFilter],
    queryFn:  () => fetchAllStocks(page, 100, labelFilter === 'ALL' ? undefined : labelFilter, sectorFilter === 'ALL' ? undefined : sectorFilter),
    staleTime: 5 * 60_000,
    keepPreviousData: true,
  } as any)

  const stocks: Stock[] = stocksData?.stocks ?? []
  const sectors = useMemo(() => {
    const s = new Set(stocks.map(s => s.sector).filter(Boolean))
    return ['ALL', ...Array.from(s).sort()]
  }, [stocks])

  const displayed = useMemo(() => {
    let rows = stocks
    if (listSearch.trim()) {
      const q = listSearch.trim().toUpperCase()
      rows = rows.filter(s => s.symbol.includes(q) || (s.sector ?? '').toUpperCase().includes(q))
    }
    return [...rows].sort((a, b) => {
      const va = (a as any)[sortKey] ?? (a.price as any)?.[sortKey] ?? -Infinity
      const vb = (b as any)[sortKey] ?? (b.price as any)?.[sortKey] ?? -Infinity
      return sortDir === 'desc' ? vb - va : va - vb
    })
  }, [stocks, listSearch, sortKey, sortDir])

  // ── Chart lifecycle ──────────────────────────────────────────────────────

  useEffect(() => {
    if (!chartRef.current) return
    setChartError(null)
    let chart: IChartApi | null = null
    try {
      chart = createChart(chartRef.current, {
        autoSize: true,
        attributionLogo: false,
        layout: {
          background: { type: ColorType.Solid, color: T.bg },
          textColor: T.sub, fontSize: 10, fontFamily: 'monospace',
        },
        grid: {
          vertLines: { color: T.border },
          horzLines: { color: T.border },
        },
        crosshair: {
          vertLine: { labelBackgroundColor: T.bgCard },
          horzLine: { labelBackgroundColor: T.bgCard },
        },
        rightPriceScale: { borderColor: T.border },
        timeScale: { borderColor: T.border, timeVisible: false, secondsVisible: false },
        handleScroll: true,
        handleScale: true,
      })

      const candles = chart.addSeries(CandlestickSeries, {
        upColor: T.green, downColor: T.red,
        borderVisible: false,
        wickUpColor: T.green, wickDownColor: T.red,
      })
      const volume = chart.addSeries(HistogramSeries, { priceScaleId: 'vol' })
      volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })

      chartApi.current  = chart
      candleRef.current = candles
      volumeRef.current = volume
    } catch (e) {
      setChartError(e instanceof Error ? e.message : String(e))
      chart?.remove()
    }
    return () => {
      chartApi.current?.remove()
      chartApi.current = candleRef.current = volumeRef.current = null
    }
  }, [])

  useEffect(() => {
    chartApi.current?.applyOptions({
      timeScale: { timeVisible: INTRADAY.has(timeframe), secondsVisible: false },
    })
  }, [timeframe])

  useEffect(() => {
    if (!ohlcv || !candleRef.current || !volumeRef.current) return
    try {
      const bars = ohlcv.bars
      const candles: CandlestickData<Time>[] = bars.map(b => ({
        time: (typeof b.time === 'string' ? toPeriodStart(b.time, timeframe) : b.time) as Time,
        open: b.open, high: b.high, low: b.low, close: b.close,
      }))
      const volumes: HistogramData<Time>[] = bars.map(b => ({
        time: (typeof b.time === 'string' ? toPeriodStart(b.time, timeframe) : b.time) as Time,
        value: b.volume ?? 0,
        color: b.close >= b.open ? T.green + '55' : T.red + '55',
      }))
      candleRef.current.setData(candles)
      volumeRef.current.setData(volumes)
      const n = candles.length
      barCountRef.current = n
      if (n > 0 && chartApi.current) {
        chartApi.current.timeScale().setVisibleLogicalRange({
          from: Math.max(0, n - (DEFAULT_BARS[timeframe] ?? 180)),
          to: n + 3,
        })
      }
    } catch (e) { setChartError(e instanceof Error ? e.message : String(e)) }
  }, [ohlcv, timeframe])

  const resetChart = useCallback(() => {
    if (!chartApi.current) return
    chartApi.current.timeScale().setVisibleLogicalRange({
      from: Math.max(0, barCountRef.current - (DEFAULT_BARS[timeframe] ?? 180)),
      to: barCountRef.current + 3,
    })
  }, [timeframe])

  // ── Symbol selection ─────────────────────────────────────────────────────

  const selectSymbol = useCallback((sym: string) => {
    const s = sym.trim().toUpperCase()
    if (!s) return
    setSymbol(s)
    setChartInput(s)
    setShowDrop(false)
    setSearchQ('')
  }, [])

  const handleChartInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value.toUpperCase()
    setChartInput(v)
    setSearchQ(v)
    setShowDrop(true)
  }
  const handleChartInputKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') selectSymbol(chartInput)
    if (e.key === 'Escape') setShowDrop(false)
  }

  const toggleSort = (col: SortKey) => {
    if (sortKey === col) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(col); setSortDir('desc') }
  }

  // ── Derived chart values ─────────────────────────────────────────────────

  const latestBar  = ohlcv?.bars.at(-1)
  const prevBar    = ohlcv?.bars.at(-2)
  const priceChg   = latestBar && prevBar ? ((latestBar.close - prevBar.close) / prevBar.close) * 100 : null
  const isIntraday = INTRADAY.has(timeframe)

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 112px)', gap: 0, background: T.bg }}>

      {/* ── Page header ────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0 10px',
        borderBottom: `1px solid ${T.border}`, flexShrink: 0, flexWrap: 'wrap',
      }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            display: 'flex', alignItems: 'center', gap: 5,
            background: 'none', border: `1px solid ${T.border}`,
            color: T.sub, cursor: 'pointer', padding: '4px 12px',
            borderRadius: 4, fontSize: 11, flexShrink: 0,
          }}
        >
          &larr; Back
        </button>

        <span style={{ fontSize: 13, fontWeight: 800, letterSpacing: 2.5, color: T.text, whiteSpace: 'nowrap' }}>
          STOCKS
        </span>

        <div style={{ width: 1, height: 18, background: T.border, flexShrink: 0 }} />

        {/* List search */}
        <input
          value={listSearch}
          onChange={e => { setListSearch(e.target.value); setPage(1) }}
          placeholder="Filter symbol / sector..."
          style={{
            background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 4,
            color: T.text, padding: '5px 10px', fontSize: 11, outline: 'none', width: 180,
          }}
        />

        {/* Sector filter */}
        <select
          value={sectorFilter}
          onChange={e => { setSectorFilter(e.target.value); setPage(1) }}
          style={{
            background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 4,
            color: sectorFilter === 'ALL' ? T.sub : T.text, padding: '5px 8px', fontSize: 11,
          }}
        >
          {sectors.map(s => <option key={s} value={s}>{s === 'ALL' ? 'All sectors' : s}</option>)}
        </select>

        {/* Sort selector */}
        <div style={{ display: 'flex', gap: 4, marginLeft: 'auto', flexWrap: 'wrap' }}>
          {([
            ['Score', 'bull_run_score'],
            ['LTP',   'close_now'],
            ['30D',   'ret_30d'],
            ['365D',  'ret_365d'],
          ] as [string, SortKey][]).map(([lbl, key]) => (
            <button key={key} onClick={() => toggleSort(key)} style={{
              padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
              border: `1px solid ${sortKey === key ? T.blue : T.border}`,
              background: sortKey === key ? T.blue + '18' : 'transparent',
              color: sortKey === key ? T.blue : T.sub,
              fontWeight: sortKey === key ? 700 : 400,
            }}>
              {lbl}{sortKey === key ? (sortDir === 'desc' ? ' ↓' : ' ↑') : ''}
            </button>
          ))}
        </div>
      </div>

      {/* ── Label filter pills ─────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 4, padding: '7px 0', borderBottom: `1px solid ${T.border}`, flexShrink: 0, flexWrap: 'wrap' }}>
        {LABELS.map(l => {
          const active = labelFilter === l
          const color  = LABEL_COLOR[l] ?? T.sub
          return (
            <button key={l} onClick={() => { setLabelFilter(l); setPage(1) }} style={{
              padding: '3px 10px', borderRadius: 10, fontSize: 9, fontWeight: 700,
              letterSpacing: 0.8, cursor: 'pointer',
              border: `1px solid ${active ? color : T.border}`,
              background: active ? color + '20' : 'transparent',
              color: active ? color : T.dim,
            }}>
              {l === 'ALL' ? 'ALL' : l.replace(/_/g, ' ')}
            </button>
          )
        })}
        <span style={{ marginLeft: 6, fontSize: 10, color: T.dim, alignSelf: 'center' }}>
          {stocksData?.total ?? 0} symbols
        </span>
      </div>

      {/* ── Main split ─────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', gap: 0, overflow: 'hidden', minHeight: 0 }}>

        {/* ── Left: stock screener ─────────────────────────────────────── */}
        <div style={{
          width: 290, flexShrink: 0, display: 'flex', flexDirection: 'column',
          borderRight: `1px solid ${T.border}`, overflow: 'hidden',
        }}>
          {/* Column headers */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 70px 44px 36px',
            padding: '5px 8px 4px', gap: 4,
            borderBottom: `1px solid ${T.border}`,
            fontSize: 8, fontWeight: 700, letterSpacing: 1.2, color: T.dim, textTransform: 'uppercase',
            flexShrink: 0,
          }}>
            <span>Symbol</span>
            <span style={{ textAlign: 'right' }}>Score</span>
            <span style={{ textAlign: 'right' }}>30D</span>
            <span style={{ textAlign: 'center' }}>Trend</span>
          </div>

          {/* Rows */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {listLoading && (
              <div style={{ padding: '32px 12px', textAlign: 'center', color: T.dim, fontSize: 11 }}>
                Loading...
              </div>
            )}
            {displayed.map(s => {
              const isActive = s.symbol === symbol
              const trend    = s.trend_signal ?? (s as any).technical?.trend_signal
              const trendM   = TREND_MAP[trend ?? '']
              const ret30    = s.price?.ret_30d
              const lbl      = LABEL_COLOR[s.label ?? ''] ?? T.dim

              return (
                <div
                  key={s.symbol}
                  onClick={() => selectSymbol(s.symbol)}
                  style={{
                    display: 'grid', gridTemplateColumns: '1fr 70px 44px 36px',
                    padding: '7px 8px', gap: 4, cursor: 'pointer',
                    borderLeft: isActive ? `3px solid ${T.blue}` : '3px solid transparent',
                    background: isActive ? T.bgActive : 'transparent',
                    borderBottom: `1px solid ${T.border}30`,
                    transition: 'background 0.12s',
                    alignItems: 'center',
                  }}
                  onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = T.bgHover }}
                  onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
                >
                  {/* Symbol + sector */}
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <span style={{
                        fontSize: 11, fontWeight: 800, color: isActive ? T.text : '#B8CFE8',
                        fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>{s.symbol}</span>
                      {s.label && (
                        <span style={{
                          fontSize: 7, fontWeight: 700, padding: '1px 4px', borderRadius: 2,
                          background: lbl + '20', color: lbl, border: `1px solid ${lbl}40`,
                          flexShrink: 0,
                        }}>
                          {s.label === 'STRONG_CANDIDATE' ? 'STR' : s.label === 'EMERGING' ? 'EMG' : s.label === 'WATCHLIST' ? 'WCH' : s.label.slice(0, 3)}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 8, color: T.dim, marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {s.sector}
                    </div>
                  </div>

                  {/* Score mini bar */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <MiniBar value={s.bull_run_score} />
                  </div>

                  {/* 30D return */}
                  <div style={{
                    fontSize: 9, fontWeight: 600, textAlign: 'right',
                    color: pctColor(ret30), fontVariantNumeric: 'tabular-nums',
                  }}>
                    {pctStr(ret30)}
                  </div>

                  {/* Trend chip */}
                  <div style={{ textAlign: 'center' }}>
                    {trendM && (
                      <span style={{
                        fontSize: 7, fontWeight: 700, padding: '1px 4px', borderRadius: 2,
                        background: trendM.color + '20', color: trendM.color, border: `1px solid ${trendM.color}40`,
                      }}>{trendM.short}</span>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Pagination */}
            <div style={{ display: 'flex', gap: 6, padding: '10px 8px', justifyContent: 'center', borderTop: `1px solid ${T.border}` }}>
              {page > 1 && (
                <button onClick={() => setPage(p => p - 1)} style={{
                  padding: '3px 10px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  background: T.bgCard, color: T.sub, border: `1px solid ${T.border}`,
                }}>Prev</button>
              )}
              <span style={{ fontSize: 10, color: T.dim, alignSelf: 'center' }}>Pg {page}</span>
              {(stocksData?.stocks?.length ?? 0) === 100 && (
                <button onClick={() => setPage(p => p + 1)} style={{
                  padding: '3px 10px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  background: T.bgCard, color: T.sub, border: `1px solid ${T.border}`,
                }}>Next</button>
              )}
            </div>
          </div>
        </div>

        {/* ── Right: chart + intelligence ────────────────────────────── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>

          {/* Chart toolbar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
            borderBottom: `1px solid ${T.border}`, flexShrink: 0, flexWrap: 'wrap',
          }}>
            {/* Symbol search input */}
            <div style={{ position: 'relative' }}>
              <input
                value={chartInput}
                onChange={handleChartInputChange}
                onKeyDown={handleChartInputKey}
                onFocus={() => { setShowDrop(true); setSearchQ(chartInput) }}
                onBlur={() => setTimeout(() => setShowDrop(false), 150)}
                placeholder="Symbol..."
                style={{
                  background: T.bgCard, border: `1px solid ${T.borderLit}`,
                  color: T.text, padding: '5px 12px', borderRadius: 4,
                  fontSize: 13, fontFamily: 'monospace', fontWeight: 800,
                  width: 130, outline: 'none', letterSpacing: 1,
                }}
              />
              {showDrop && symbolAC?.symbols && symbolAC.symbols.length > 0 && (
                <div style={{
                  position: 'absolute', top: '100%', left: 0, zIndex: 200, marginTop: 2,
                  background: '#0F1828', border: `1px solid ${T.borderLit}`,
                  borderRadius: 4, minWidth: 260, maxHeight: 280, overflowY: 'auto',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
                }}>
                  {symbolAC.symbols.map(s => (
                    <div
                      key={s.SYMBOL}
                      onMouseDown={() => selectSymbol(s.SYMBOL)}
                      style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 11, borderBottom: `1px solid ${T.border}30` }}
                      onMouseEnter={e => (e.currentTarget.style.background = T.bgActive)}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <span style={{ color: T.text, fontWeight: 700, fontFamily: 'monospace' }}>{s.SYMBOL}</span>
                      <span style={{ color: T.sub, marginLeft: 10 }}>{s.COMPANY_NAME}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Price display */}
            {latestBar && (
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontSize: 18, fontWeight: 800, color: T.text, fontFamily: 'monospace', letterSpacing: -0.5, fontVariantNumeric: 'tabular-nums' }}>
                  {latestBar.close.toFixed(2)}
                </span>
                {priceChg != null && (
                  <span style={{ fontSize: 12, fontWeight: 700, color: pctColor(priceChg) }}>
                    {priceChg >= 0 ? '+' : ''}{priceChg.toFixed(2)}%
                  </span>
                )}
                {signals?.label && (
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 10,
                    background: (LABEL_COLOR[signals.label] ?? T.dim) + '22',
                    color: LABEL_COLOR[signals.label] ?? T.dim,
                    border: `1px solid ${(LABEL_COLOR[signals.label] ?? T.dim)}44`,
                    letterSpacing: 0.5,
                  }}>
                    {signals.label.replace(/_/g, ' ')}
                  </span>
                )}
              </div>
            )}

            {/* Timeframe buttons */}
            <div style={{ display: 'flex', gap: 3, marginLeft: 'auto', alignItems: 'center' }}>
              {TF_GROUPS[0].map(tf => (
                <button key={tf} onClick={() => setTimeframe(tf)} style={{
                  padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  border: `1px solid ${timeframe === tf ? T.blue : T.border}`,
                  background: timeframe === tf ? T.blue + '22' : 'transparent',
                  color: timeframe === tf ? T.blue : T.sub,
                  fontWeight: timeframe === tf ? 700 : 400,
                }}>{tf}</button>
              ))}
              <div style={{ width: 1, height: 16, background: T.border, margin: '0 2px' }} />
              {TF_GROUPS[1].map(tf => (
                <button key={tf} onClick={() => setTimeframe(tf)} style={{
                  padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  border: `1px solid ${timeframe === tf ? T.green : T.border}`,
                  background: timeframe === tf ? T.green + '22' : 'transparent',
                  color: timeframe === tf ? T.green : T.sub,
                  fontWeight: timeframe === tf ? 700 : 400,
                }}>{tf}</button>
              ))}
              <button onClick={resetChart} title="Reset view" style={{
                marginLeft: 4, padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                border: `1px solid ${T.border}`, background: 'transparent', color: T.dim,
              }}>Reset</button>
            </div>
          </div>

          {/* Chart container */}
          <ChartBoundary>
            <div style={{ flex: 1, position: 'relative', background: T.bg, minHeight: 0 }}>
              {chartError && (
                <div style={{
                  position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', gap: 8, zIndex: 20, background: T.bg,
                }}>
                  <span style={{ color: T.red, fontSize: 13, fontWeight: 700 }}>Chart Error</span>
                  <span style={{ color: T.sub, fontSize: 10 }}>{chartError}</span>
                  <button onClick={() => { setChartError(null); window.location.reload() }} style={{
                    padding: '4px 14px', borderRadius: 4, border: `1px solid ${T.red}`,
                    background: 'transparent', color: T.red, cursor: 'pointer', fontSize: 10,
                  }}>Reload</button>
                </div>
              )}
              {!chartError && chartLoading && (
                <div style={{
                  position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
                  justifyContent: 'center', color: T.sub, fontSize: 11, zIndex: 10, background: T.bg,
                }}>
                  Loading {symbol} ({timeframe})...
                </div>
              )}
              {!chartError && chartIsError && (
                <div style={{
                  position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', gap: 6, zIndex: 10, background: T.bg,
                }}>
                  <span style={{ color: T.red, fontSize: 12 }}>No data for {symbol} ({timeframe})</span>
                  <span style={{ color: T.sub, fontSize: 10 }}>
                    {isIntraday ? 'Intraday may be unavailable for this symbol' : (chartErrObj as Error)?.message}
                  </span>
                </div>
              )}
              <div ref={chartRef} style={{ width: '100%', height: '100%' }} />
            </div>
          </ChartBoundary>

          {/* OHLCV footer bar */}
          {latestBar && (
            <div style={{
              display: 'flex', gap: 18, padding: '5px 14px',
              fontSize: 10, color: T.sub, flexShrink: 0,
              borderTop: `1px solid ${T.border}`, background: T.bgPanel,
              fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums',
            }}>
              <span>O <span style={{ color: T.text }}>{latestBar.open.toFixed(2)}</span></span>
              <span>H <span style={{ color: T.green }}>{latestBar.high.toFixed(2)}</span></span>
              <span>L <span style={{ color: T.red }}>{latestBar.low.toFixed(2)}</span></span>
              <span>C <span style={{ color: T.text }}>{latestBar.close.toFixed(2)}</span></span>
              <span>Vol <span style={{ color: T.text }}>{((latestBar.volume ?? 0) / 1e6).toFixed(2)}M</span></span>
              {ohlcv && (
                <span style={{ marginLeft: 'auto', color: T.dim }}>
                  {ohlcv.count} bars &nbsp;|&nbsp; {fmtBarTime(ohlcv.from)} — {fmtBarTime(ohlcv.to)}
                </span>
              )}
            </div>
          )}

          {/* ── Intelligence cards ──────────────────────────────────────── */}
          {signals && (
            <div style={{
              display: 'flex', gap: 8, padding: '8px 14px',
              flexShrink: 0, borderTop: `1px solid ${T.border}`,
              background: T.bgPanel,
            }}>

              {/* Bull Run */}
              <MetricCard title="Bull Run">
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{
                    fontSize: 24, fontWeight: 900, color: scoreColor(signals.bull_run_score),
                    fontFamily: 'monospace', lineHeight: 1, fontVariantNumeric: 'tabular-nums',
                  }}>
                    {signals.bull_run_score?.toFixed(0) ?? '--'}
                  </span>
                  {signals.market_regime && (
                    <span style={{ fontSize: 9, color: T.sub }}>{signals.market_regime}</span>
                  )}
                </div>
                <ScoreLine label="Price"   value={signals.price_score} />
                <ScoreLine label="Sector"  value={signals.sector_flow_score} />
                <ScoreLine label="Deals"   value={signals.deal_score} />
                <ScoreLine label="Corp"    value={signals.corporate_score} />
              </MetricCard>

              {/* ML Models */}
              {(signals.ml_bull_run_score != null || signals.accumulation_score != null) && (
                <MetricCard title="ML Models">
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{
                      fontSize: 24, fontWeight: 900, color: scoreColor(signals.ml_bull_run_score),
                      fontFamily: 'monospace', lineHeight: 1, fontVariantNumeric: 'tabular-nums',
                    }}>
                      {signals.ml_bull_run_score?.toFixed(0) ?? '--'}
                    </span>
                    <span style={{ fontSize: 9, color: T.sub }}>bull score</span>
                  </div>
                  <ScoreLine label="Bull Run (LGB+XGB)" value={signals.ml_bull_run_score} />
                  {signals.accumulation_score != null && (
                    <ScoreLine label="Accumulation (XGB)" value={signals.accumulation_score} />
                  )}
                </MetricCard>
              )}

              {/* Sector */}
              {(signals.sector || signals.sector_combined != null || signals.rotation_signal) && (
                <MetricCard title="Sector Signal">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                    {signals.sector && (
                      <span style={{ fontSize: 10, fontWeight: 700, color: T.text }}>{signals.sector}</span>
                    )}
                    {signals.rotation_signal && (
                      <span style={{
                        fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 10,
                        alignSelf: 'flex-start',
                        background: T.blue + '20', color: T.blue, border: `1px solid ${T.blue}40`,
                      }}>
                        {signals.rotation_signal.replace(/_/g, ' ')}
                      </span>
                    )}
                    {signals.sector_combined != null && (
                      <ScoreLine label="Combined" value={signals.sector_combined} max={10} />
                    )}
                    {signals.as_of_date && (
                      <span style={{ fontSize: 8, color: T.dim }}>as of {signals.as_of_date}</span>
                    )}
                  </div>
                </MetricCard>
              )}

              {/* Shareholding */}
              {(signals.shp_fii_pct != null || signals.shp_promoter_pct != null) && (
                <MetricCard title={`Shareholding${signals.shp_quarter ? ` (${signals.shp_quarter})` : ''}`}>
                  {[
                    { label: 'Promoter', value: signals.shp_promoter_pct, color: T.purple },
                    { label: 'FII',      value: signals.shp_fii_pct,      color: T.blue   },
                    { label: 'DII',      value: signals.shp_dii_pct,      color: T.teal   },
                  ].map(({ label, value, color }) => value != null ? (
                    <div key={label}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                        <span style={{ fontSize: 9, color: T.sub }}>{label}</span>
                        <span style={{ fontSize: 10, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>
                          {value.toFixed(2)}%
                        </span>
                      </div>
                      <div style={{ height: 2, background: T.border, borderRadius: 1 }}>
                        <div style={{
                          width: `${Math.min(value, 100)}%`, height: '100%', background: color + '99', borderRadius: 1,
                          transition: 'width 0.4s',
                        }} />
                      </div>
                    </div>
                  ) : null)}
                </MetricCard>
              )}

              {/* Regime */}
              {signals.market_regime && (
                <MetricCard title="Market Regime">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{
                      fontSize: 14, fontWeight: 800, letterSpacing: 0.5, color:
                        signals.market_regime === 'BULLISH' ? T.green :
                        signals.market_regime === 'BEARISH' ? T.red : T.amber,
                    }}>
                      {signals.market_regime}
                    </span>
                    {signals.regime_multiplier != null && (
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                          <span style={{ fontSize: 9, color: T.sub }}>Multiplier</span>
                          <span style={{ fontSize: 10, fontWeight: 700, color: T.text, fontVariantNumeric: 'tabular-nums' }}>
                            ×{signals.regime_multiplier.toFixed(2)}
                          </span>
                        </div>
                        <div style={{ height: 2, background: T.border, borderRadius: 1 }}>
                          <div style={{
                            width: `${signals.regime_multiplier * 60}%`, height: '100%',
                            background: T.amber + '99', borderRadius: 1, transition: 'width 0.4s',
                          }} />
                        </div>
                      </div>
                    )}
                    {signals.as_of_date && (
                      <span style={{ fontSize: 8, color: T.dim }}>as of {signals.as_of_date}</span>
                    )}
                  </div>
                </MetricCard>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
