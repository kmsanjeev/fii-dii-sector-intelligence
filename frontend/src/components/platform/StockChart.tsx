/**
 * StockChart — embedded candlestick + volume chart for the stock detail page.
 * Lightweight-charts v5. No search bar, no signals panel — just the chart.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  createChart, ColorType,
  CandlestickSeries, HistogramSeries,
  type IChartApi, type ISeriesApi,
  type CandlestickData, type HistogramData, type Time,
} from 'lightweight-charts'
import { api } from '../../api/client'

type Timeframe = '1D' | '1W' | '1M'

type Bar = {
  time: string | number
  open: number; high: number; low: number; close: number; volume: number
}

const COLORS = {
  bg: '#0A0D14', border: '#1E2332',
  green: '#22C55E', red: '#EF4444', dim: '#64748B',
}

const DEFAULT_BARS: Record<Timeframe, number> = { '1D': 180, '1W': 52, '1M': 24 }

function toPeriodStart(d: string, tf: Timeframe): string {
  if (tf === '1D') return d
  const dt = new Date(d + 'T00:00:00Z')
  if (tf === '1W') {
    const off = dt.getUTCDay() === 0 ? 6 : dt.getUTCDay() - 1
    dt.setUTCDate(dt.getUTCDate() - off)
  } else {
    dt.setUTCDate(1)
  }
  return dt.toISOString().slice(0, 10)
}

export function StockChart({ symbol }: { symbol: string }) {
  const [tf, setTf] = useState<Timeframe>('1D')
  const chartRef  = useRef<HTMLDivElement>(null)
  const chartApi  = useRef<IChartApi | null>(null)
  const candleRef = useRef<ISeriesApi<'Candlestick', Time> | null>(null)
  const volRef    = useRef<ISeriesApi<'Histogram', Time> | null>(null)
  const barCount  = useRef(0)

  const { data: ohlcv, isLoading, isError } = useQuery({
    queryKey: ['chart-ohlcv', symbol, tf],
    queryFn: () => api.get('/charts/ohlcv', { params: { symbol, timeframe: tf } }).then(r => r.data as { bars: Bar[]; count: number }),
    staleTime: 5 * 60_000,
    retry: 1,
  })

  // Create chart once on mount
  useEffect(() => {
    if (!chartRef.current) return
    const chart = createChart(chartRef.current, {
      autoSize: true,
      attributionLogo: false,
      layout: {
        background: { type: ColorType.Solid, color: COLORS.bg },
        textColor: COLORS.dim, fontSize: 10, fontFamily: 'monospace',
      },
      grid: {
        vertLines: { color: COLORS.border },
        horzLines: { color: COLORS.border },
      },
      crosshair: {
        vertLine: { labelBackgroundColor: COLORS.border },
        horzLine: { labelBackgroundColor: COLORS.border },
      },
      rightPriceScale: { borderColor: COLORS.border },
      timeScale: { borderColor: COLORS.border, timeVisible: false, secondsVisible: false },
      handleScroll: true,
      handleScale: true,
    })

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: COLORS.green, downColor: COLORS.red,
      borderVisible: false, wickUpColor: COLORS.green, wickDownColor: COLORS.red,
    })
    const vol = chart.addSeries(HistogramSeries, { priceScaleId: 'vol' })
    vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })

    chartApi.current  = chart
    candleRef.current = candles
    volRef.current    = vol

    return () => { chart.remove(); chartApi.current = null }
  }, [])

  // Update data when ohlcv or timeframe changes
  useEffect(() => {
    if (!ohlcv?.bars || !candleRef.current || !volRef.current) return
    const bars = ohlcv.bars
    const candles: CandlestickData<Time>[] = bars.map(b => ({
      time: toPeriodStart(String(b.time), tf) as Time,
      open: b.open, high: b.high, low: b.low, close: b.close,
    }))
    const vols: HistogramData<Time>[] = bars.map(b => ({
      time: toPeriodStart(String(b.time), tf) as Time,
      value: b.volume ?? 0,
      color: b.close >= b.open ? COLORS.green + '55' : COLORS.red + '55',
    }))
    candleRef.current.setData(candles)
    volRef.current.setData(vols)
    barCount.current = candles.length
    const show = DEFAULT_BARS[tf]
    if (candles.length > 0 && chartApi.current) {
      chartApi.current.timeScale().setVisibleLogicalRange({
        from: Math.max(0, candles.length - show),
        to: candles.length + 2,
      })
    }
  }, [ohlcv, tf])

  const reset = useCallback(() => {
    if (!chartApi.current) return
    const show = DEFAULT_BARS[tf]
    chartApi.current.timeScale().setVisibleLogicalRange({
      from: Math.max(0, barCount.current - show), to: barCount.current + 2,
    })
  }, [tf])

  const latest = ohlcv?.bars.at(-1)
  const prev   = ohlcv?.bars.at(-2)
  const chg    = latest && prev ? ((latest.close - prev.close) / prev.close) * 100 : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Price */}
        {latest && (
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: '#E2E8F0', fontFamily: 'monospace' }}>
              {latest.close.toFixed(2)}
            </span>
            {chg != null && (
              <span style={{ fontSize: 11, fontWeight: 600, color: chg >= 0 ? COLORS.green : COLORS.red }}>
                {chg >= 0 ? '+' : ''}{chg.toFixed(2)}%
              </span>
            )}
          </div>
        )}

        {/* Timeframe */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
          {(['1D', '1W', '1M'] as Timeframe[]).map(t => (
            <button key={t} onClick={() => setTf(t)} style={{
              padding: '3px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
              border: `1px solid ${tf === t ? COLORS.green : COLORS.border}`,
              background: tf === t ? COLORS.green + '22' : 'transparent',
              color: tf === t ? COLORS.green : COLORS.dim, fontWeight: tf === t ? 700 : 400,
            }}>{t}</button>
          ))}
          <button onClick={reset} style={{
            padding: '3px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
            border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.dim,
            marginLeft: 4,
          }}>Reset</button>
        </div>
      </div>

      {/* Chart */}
      <div style={{
        height: 320, borderRadius: 6, overflow: 'hidden',
        border: `1px solid ${COLORS.border}`, background: COLORS.bg, position: 'relative',
      }}>
        {isLoading && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
            justifyContent: 'center', color: COLORS.dim, fontSize: 11, zIndex: 10,
          }}>
            Loading {symbol} ({tf})...
          </div>
        )}
        {isError && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
            justifyContent: 'center', color: '#EF4444', fontSize: 11, zIndex: 10,
          }}>
            No chart data for {symbol} ({tf})
          </div>
        )}
        <div ref={chartRef} style={{ width: '100%', height: '100%' }} />
      </div>

      {/* OHLC footer */}
      {latest && (
        <div style={{ display: 'flex', gap: 16, fontSize: 10, color: COLORS.dim }}>
          <span>O <span style={{ color: '#E2E8F0' }}>{latest.open.toFixed(2)}</span></span>
          <span>H <span style={{ color: COLORS.green }}>{latest.high.toFixed(2)}</span></span>
          <span>L <span style={{ color: COLORS.red }}>{latest.low.toFixed(2)}</span></span>
          <span>C <span style={{ color: '#E2E8F0' }}>{latest.close.toFixed(2)}</span></span>
          <span>Vol <span style={{ color: '#E2E8F0' }}>{((latest.volume ?? 0) / 1e5).toFixed(1)}L</span></span>
        </div>
      )}
    </div>
  )
}
