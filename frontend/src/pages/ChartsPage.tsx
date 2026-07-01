import { useEffect, useRef, useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  createChart,
  ColorType,
  CandlestickSeries,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type HistogramData,
  type Time,
} from 'lightweight-charts'
import { api } from '../api/client'

// ── Types ─────────────────────────────────────────────────────────────────────

type Bar = {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

type OhlcvResponse = {
  symbol: string
  period: string
  bars: Bar[]
  count: number
  from: string | null
  to: string | null
}

type Signal = {
  symbol: string
  bull_run_score?: number
  label?: string
  price_score?: number
  sector_flow_score?: number
  deal_score?: number
  corporate_score?: number
  market_regime?: string
  regime_multiplier?: number
  sector?: string
  as_of_date?: string
  ml_bull_run_score?: number | null
  accumulation_score?: number | null
  rotation_signal?: string
  sector_combined?: number
  shp_fii_pct?: number | null
  shp_dii_pct?: number | null
  shp_promoter_pct?: number | null
  shp_quarter?: string
}

type SymbolResult = { SYMBOL: string; COMPANY_NAME: string }

// ── Constants ─────────────────────────────────────────────────────────────────

const PERIODS = ['1M', '3M', '6M', '1Y', '3Y', '5Y'] as const
type Period = typeof PERIODS[number]

const COLORS = {
  bg:       '#0A0D14',
  panel:    '#141720',
  border:   '#1E2332',
  text:     '#94A3B8',
  textDim:  '#64748B',
  green:    '#22C55E',
  red:      '#EF4444',
  amber:    '#F59E0B',
  blue:     '#3B82F6',
}

const LABEL_COLOR: Record<string, string> = {
  STRONG_CANDIDATE: '#22C55E',
  EMERGING:         '#3B82F6',
  WATCHLIST:        '#F59E0B',
  NEUTRAL:          '#64748B',
  AVOID:            '#EF4444',
}

const ROTATION_COLOR: Record<string, string> = {
  EARLY_ROTATION: '#22C55E',
  LEADING:        '#3B82F6',
  MOMENTUM:       '#F59E0B',
  EMERGING:       '#94A3B8',
  LAGGING:        '#64748B',
  DECLINING:      '#EF4444',
}

// ── API helpers ───────────────────────────────────────────────────────────────

const fetchOhlcv = (symbol: string, period: Period): Promise<OhlcvResponse> =>
  api.get('/charts/ohlcv', { params: { symbol, period } }).then(r => r.data)

const fetchSignals = (symbol: string): Promise<Signal> =>
  api.get('/charts/signals', { params: { symbol } }).then(r => r.data)

const fetchSymbols = (q: string): Promise<{ symbols: SymbolResult[] }> =>
  api.get('/charts/symbols', { params: { q } }).then(r => r.data)

// ── Score bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ label, value, max = 100 }: { label: string; value: number | undefined | null; max?: number }) {
  if (value == null) return null
  const pct = Math.min(Math.max(value / max, 0), 1) * 100
  const color = value >= 70 ? COLORS.green : value >= 40 ? COLORS.amber : COLORS.red
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: 10, color: COLORS.textDim }}>{label}</span>
        <span style={{ fontSize: 11, color, fontWeight: 600 }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ height: 3, backgroundColor: COLORS.border, borderRadius: 2 }}>
        <div style={{ width: `${pct}%`, height: '100%', backgroundColor: color, borderRadius: 2, transition: 'width 0.3s' }} />
      </div>
    </div>
  )
}

function Pill({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      fontSize: 9, fontWeight: 700, letterSpacing: '0.08em',
      padding: '2px 8px', borderRadius: 10,
      backgroundColor: color + '22', color, border: `1px solid ${color}55`,
    }}>
      {label}
    </span>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function ChartsPage() {
  const [symbol, setSymbol]       = useState('RELIANCE')
  const [inputVal, setInputVal]   = useState('RELIANCE')
  const [period, setPeriod]       = useState<Period>('1Y')
  const [showDropdown, setShowDropdown] = useState(false)
  const [searchQ, setSearchQ]     = useState('')

  const chartRef   = useRef<HTMLDivElement>(null)
  const chartApi   = useRef<IChartApi | null>(null)
  const candleRef  = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeRef  = useRef<ISeriesApi<'Histogram'> | null>(null)

  // Symbol autocomplete
  const { data: symbolData } = useQuery({
    queryKey: ['chart-symbols', searchQ],
    queryFn: () => fetchSymbols(searchQ),
    enabled: showDropdown && searchQ.length > 0,
    staleTime: 30_000,
  })

  // OHLCV data
  const { data: ohlcv, isLoading, isError, error } = useQuery({
    queryKey: ['chart-ohlcv', symbol, period],
    queryFn: () => fetchOhlcv(symbol, period),
    staleTime: 5 * 60_000,
    retry: 1,
  })

  // Intelligence signals
  const { data: signals } = useQuery({
    queryKey: ['chart-signals', symbol],
    queryFn: () => fetchSignals(symbol),
    staleTime: 5 * 60_000,
  })

  // Create chart once
  useEffect(() => {
    if (!chartRef.current) return

    const chart = createChart(chartRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: COLORS.bg },
        textColor: COLORS.text,
        fontSize: 11,
        fontFamily: 'monospace',
      },
      grid: {
        vertLines: { color: COLORS.border },
        horzLines: { color: COLORS.border },
      },
      crosshair: { vertLine: { labelBackgroundColor: '#1E2332' }, horzLine: { labelBackgroundColor: '#1E2332' } },
      rightPriceScale: { borderColor: COLORS.border },
      timeScale: {
        borderColor: COLORS.border,
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: true,
      handleScale: true,
    })

    const candles = chart.addSeries(CandlestickSeries, {
      upColor:       COLORS.green,
      downColor:     COLORS.red,
      borderVisible: false,
      wickUpColor:   COLORS.green,
      wickDownColor: COLORS.red,
    })

    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'vol',
    } as Parameters<typeof chart.addSeries<'Histogram'>>[1])

    chart.priceScale('vol').applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    })

    chartApi.current  = chart
    candleRef.current = candles as unknown as ISeriesApi<'Candlestick'>
    volumeRef.current = volume as unknown as ISeriesApi<'Histogram'>

    const ro = new ResizeObserver(() => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth })
    })
    ro.observe(chartRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
      chartApi.current  = null
      candleRef.current = null
      volumeRef.current = null
    }
  }, [])

  // Update data when ohlcv changes
  useEffect(() => {
    if (!ohlcv || !candleRef.current || !volumeRef.current) return

    const bars = ohlcv.bars

    const candles: CandlestickData<Time>[] = bars.map(b => ({
      time:  b.time as Time,
      open:  b.open,
      high:  b.high,
      low:   b.low,
      close: b.close,
    }))

    const volumes: HistogramData<Time>[] = bars.map(b => ({
      time:  b.time as Time,
      value: b.volume,
      color: b.close >= b.open ? COLORS.green + '66' : COLORS.red + '66',
    }))

    candleRef.current.setData(candles)
    volumeRef.current.setData(volumes)
    chartApi.current?.timeScale().fitContent()
  }, [ohlcv])

  const handleSymbolSelect = useCallback((sym: string) => {
    setSymbol(sym)
    setInputVal(sym)
    setShowDropdown(false)
    setSearchQ('')
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value.toUpperCase()
    setInputVal(v)
    setSearchQ(v)
    setShowDropdown(true)
  }

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const v = inputVal.trim().toUpperCase()
      if (v) handleSymbolSelect(v)
    }
    if (e.key === 'Escape') setShowDropdown(false)
  }

  const latestBar = ohlcv?.bars.at(-1)
  const prevBar   = ohlcv?.bars.at(-2)
  const priceChange = latestBar && prevBar ? ((latestBar.close - prevBar.close) / prevBar.close) * 100 : null

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 120px)' }}>

      {/* ── Left: chart area ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0 }}>

        {/* Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>

          {/* Symbol search */}
          <div style={{ position: 'relative' }}>
            <input
              value={inputVal}
              onChange={handleInputChange}
              onKeyDown={handleInputKeyDown}
              onFocus={() => { setShowDropdown(true); setSearchQ(inputVal) }}
              onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
              placeholder="Symbol..."
              style={{
                backgroundColor: COLORS.panel, border: `1px solid ${COLORS.border}`,
                color: '#E2E8F0', padding: '6px 12px', borderRadius: 4,
                fontSize: 13, fontFamily: 'monospace', fontWeight: 700,
                width: 140, outline: 'none',
              }}
            />
            {showDropdown && symbolData?.symbols && symbolData.symbols.length > 0 && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, zIndex: 100, marginTop: 2,
                backgroundColor: '#1A1F2E', border: `1px solid ${COLORS.border}`,
                borderRadius: 4, minWidth: 240, maxHeight: 280, overflowY: 'auto',
              }}>
                {symbolData.symbols.map(s => (
                  <div
                    key={s.SYMBOL}
                    onMouseDown={() => handleSymbolSelect(s.SYMBOL)}
                    style={{
                      padding: '7px 12px', cursor: 'pointer', fontSize: 11,
                      borderBottom: `1px solid ${COLORS.border}30`,
                    }}
                    onMouseEnter={e => (e.currentTarget.style.backgroundColor = COLORS.border)}
                    onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <span style={{ color: '#E2E8F0', fontWeight: 700 }}>{s.SYMBOL}</span>
                    <span style={{ color: COLORS.textDim, marginLeft: 8 }}>{s.COMPANY_NAME}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Price display */}
          {latestBar && (
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontSize: 20, fontWeight: 700, color: '#E2E8F0', fontFamily: 'monospace' }}>
                {latestBar.close.toFixed(2)}
              </span>
              {priceChange != null && (
                <span style={{ fontSize: 12, color: priceChange >= 0 ? COLORS.green : COLORS.red, fontWeight: 600 }}>
                  {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                </span>
              )}
            </div>
          )}

          {/* Period selector */}
          <div style={{ display: 'flex', gap: 4, marginLeft: 'auto' }}>
            {PERIODS.map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                style={{
                  padding: '4px 10px', borderRadius: 4, fontSize: 11, cursor: 'pointer',
                  border: `1px solid ${period === p ? COLORS.green : COLORS.border}`,
                  backgroundColor: period === p ? COLORS.green + '22' : 'transparent',
                  color: period === p ? COLORS.green : COLORS.textDim,
                  fontWeight: period === p ? 700 : 400,
                }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Chart container */}
        <div
          style={{
            flex: 1, borderRadius: 6, overflow: 'hidden',
            border: `1px solid ${COLORS.border}`,
            backgroundColor: COLORS.bg,
            position: 'relative', minHeight: 300,
          }}
        >
          {isLoading && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
              justifyContent: 'center', color: COLORS.textDim, zIndex: 10, backgroundColor: COLORS.bg,
            }}>
              Loading {symbol}...
            </div>
          )}
          {isError && (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 8, zIndex: 10, backgroundColor: COLORS.bg,
            }}>
              <span style={{ color: COLORS.red, fontSize: 13 }}>
                Failed to load {symbol}
              </span>
              <span style={{ color: COLORS.textDim, fontSize: 11 }}>
                {(error as Error)?.message ?? 'NSE API error — try again'}
              </span>
            </div>
          )}
          <div ref={chartRef} style={{ width: '100%', height: '100%' }} />
        </div>

        {/* Bar info footer */}
        {latestBar && (
          <div style={{ display: 'flex', gap: 20, fontSize: 11, color: COLORS.textDim }}>
            <span>O <span style={{ color: '#E2E8F0' }}>{latestBar.open.toFixed(2)}</span></span>
            <span>H <span style={{ color: COLORS.green }}>{latestBar.high.toFixed(2)}</span></span>
            <span>L <span style={{ color: COLORS.red }}>{latestBar.low.toFixed(2)}</span></span>
            <span>C <span style={{ color: '#E2E8F0' }}>{latestBar.close.toFixed(2)}</span></span>
            <span>Vol <span style={{ color: '#E2E8F0' }}>{(latestBar.volume / 1e6).toFixed(2)}M</span></span>
            {ohlcv && <span style={{ marginLeft: 'auto' }}>{ohlcv.count} bars | {ohlcv.from} to {ohlcv.to}</span>}
          </div>
        )}
      </div>

      {/* ── Right: Intelligence panel ── */}
      <div style={{
        width: 220, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10, overflowY: 'auto',
      }}>

        {/* Symbol header */}
        <div style={{ padding: '12px 14px', backgroundColor: COLORS.panel, borderRadius: 6, border: `1px solid ${COLORS.border}` }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#E2E8F0', fontFamily: 'monospace' }}>{symbol}</div>
          {signals?.sector && <div style={{ fontSize: 10, color: COLORS.textDim, marginTop: 2 }}>{signals.sector}</div>}
          <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
            {signals?.label && <Pill label={signals.label} color={LABEL_COLOR[signals.label] ?? COLORS.textDim} />}
            {signals?.rotation_signal && <Pill label={signals.rotation_signal} color={ROTATION_COLOR[signals.rotation_signal] ?? COLORS.textDim} />}
          </div>
        </div>

        {/* Bull Run Scores */}
        {signals && (
          <div style={{ padding: '12px 14px', backgroundColor: COLORS.panel, borderRadius: 6, border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: COLORS.textDim, marginBottom: 10 }}>BULL RUN SCORES</div>
            <ScoreBar label="Overall Score"    value={signals.bull_run_score} />
            <ScoreBar label="Price Momentum"   value={signals.price_score} />
            <ScoreBar label="Sector Flow"      value={signals.sector_flow_score} />
            <ScoreBar label="Institutional"    value={signals.deal_score} />
            <ScoreBar label="Corporate Events" value={signals.corporate_score} />
            {signals.as_of_date && (
              <div style={{ fontSize: 9, color: COLORS.textDim, marginTop: 8 }}>as of {signals.as_of_date}</div>
            )}
          </div>
        )}

        {/* ML Scores */}
        {signals && (signals.ml_bull_run_score != null || signals.accumulation_score != null) && (
          <div style={{ padding: '12px 14px', backgroundColor: COLORS.panel, borderRadius: 6, border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: COLORS.textDim, marginBottom: 10 }}>ML SCORES</div>
            <ScoreBar label="Bull Run (ML)"    value={signals.ml_bull_run_score} />
            <ScoreBar label="Accumulation"     value={signals.accumulation_score} />
          </div>
        )}

        {/* Sector Signal */}
        {signals?.sector_combined != null && (
          <div style={{ padding: '12px 14px', backgroundColor: COLORS.panel, borderRadius: 6, border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: COLORS.textDim, marginBottom: 10 }}>SECTOR SIGNAL</div>
            <ScoreBar label="Sector Combined"  value={signals.sector_combined} max={10} />
            {signals.rotation_signal && (
              <div style={{ fontSize: 10, color: ROTATION_COLOR[signals.rotation_signal] ?? COLORS.textDim, marginTop: 6 }}>
                {signals.rotation_signal}
              </div>
            )}
          </div>
        )}

        {/* Shareholding */}
        {signals && (signals.shp_fii_pct != null || signals.shp_promoter_pct != null) && (
          <div style={{ padding: '12px 14px', backgroundColor: COLORS.panel, borderRadius: 6, border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: COLORS.textDim, marginBottom: 10 }}>
              SHAREHOLDING {signals.shp_quarter && `(${signals.shp_quarter})`}
            </div>
            {[
              { label: 'Promoter', value: signals.shp_promoter_pct },
              { label: 'FII',      value: signals.shp_fii_pct },
              { label: 'DII',      value: signals.shp_dii_pct },
            ].map(({ label, value }) => value != null ? (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                <span style={{ fontSize: 10, color: COLORS.textDim }}>{label}</span>
                <span style={{ fontSize: 11, color: '#E2E8F0', fontWeight: 600 }}>{value.toFixed(2)}%</span>
              </div>
            ) : null)}
          </div>
        )}

        {/* Regime */}
        {signals?.market_regime && (
          <div style={{ padding: '12px 14px', backgroundColor: COLORS.panel, borderRadius: 6, border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: COLORS.textDim, marginBottom: 6 }}>MARKET REGIME</div>
            <div style={{ fontSize: 11, color: '#E2E8F0' }}>{signals.market_regime}</div>
            {signals.regime_multiplier != null && (
              <div style={{ fontSize: 10, color: COLORS.textDim, marginTop: 4 }}>
                Multiplier: x{signals.regime_multiplier.toFixed(2)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
