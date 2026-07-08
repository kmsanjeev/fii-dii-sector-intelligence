/**
 * FullChartPage — full-viewport trading chart
 * Route: /fullchart/:symbol   (rendered outside AppShell — no nav bar)
 *
 * Features:
 *   - Candlestick + Volume histogram
 *   - Overlay indicators (toggle): EMA 20/50/200, Bollinger Bands (20,2)
 *   - RSI(14) in a synced sub-pane below (toggle)
 *   - Corporate action markers (D/B/S/R circles)
 *   - Crosshair OHLCV + indicator legend
 *   - All 7 timeframes: 5M / 15M / 1H / 1D / 1W / 1M / 3M
 *   - Time-scale sync between main & RSI charts
 */

import {
  useEffect, useRef, useState, useCallback,
} from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  createChart, ColorType,
  CandlestickSeries, HistogramSeries, LineSeries,
  type IChartApi, type ISeriesApi, type Time,
} from 'lightweight-charts'
import { api, fetchStockCorpActions } from '../api/client'

// ── Types ─────────────────────────────────────────────────────────────────────

type TF = '5M' | '15M' | '1H' | '1D' | '1W' | '1M' | '3M'
type Bar = { time: string | number; open: number; high: number; low: number; close: number; volume: number }
type OhlcvResp = { bars: Bar[]; count: number; from: string | number | null; to: string | number | null }

const INTRADAY   = new Set<TF>(['5M', '15M', '1H'])
const TF_INTRA: TF[] = ['5M', '15M', '1H']
const TF_DAILY: TF[] = ['1D', '1W', '1M', '3M']
const DEFAULT_BARS: Record<TF, number> = { '5M': 200, '15M': 200, '1H': 180, '1D': 180, '1W': 52, '1M': 24, '3M': 16 }

// ── Theme ─────────────────────────────────────────────────────────────────────

const C = {
  bg:     '#0A0D14',
  panel:  '#141720',
  cell:   '#1C2130',
  border: '#1E2332',
  text:   '#E2E8F0',
  sub:    '#64748B',
  dim:    '#374151',
  green:  '#22C55E',
  red:    '#EF4444',
  amber:  '#F59E0B',
  blue:   '#3B82F6',
  purple: '#A78BFA',
  teal:   '#14B8A6',
}

// ── Indicator math ────────────────────────────────────────────────────────────

function calcEma(closes: number[], period: number): (number | null)[] {
  const k = 2 / (period + 1)
  const out: (number | null)[] = new Array(closes.length).fill(null)
  let val: number | null = null
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) continue
    if (val === null) {
      val = closes.slice(0, period).reduce((a, b) => a + b, 0) / period
    } else {
      val = closes[i] * k + val * (1 - k)
    }
    out[i] = +val.toFixed(4)
  }
  return out
}

function calcBB(closes: number[], period = 20, mult = 2) {
  const upper: (number | null)[] = []
  const lower: (number | null)[] = []
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) { upper.push(null); lower.push(null); continue }
    const sl = closes.slice(i - period + 1, i + 1)
    const sma = sl.reduce((a, b) => a + b, 0) / period
    const std = Math.sqrt(sl.reduce((a, b) => a + (b - sma) ** 2, 0) / period)
    upper.push(+(sma + mult * std).toFixed(4))
    lower.push(+(sma - mult * std).toFixed(4))
  }
  return { upper, lower }
}

function calcRSI(closes: number[], period = 14): (number | null)[] {
  const out: (number | null)[] = new Array(closes.length).fill(null)
  if (closes.length < period + 1) return out
  let avgGain = 0, avgLoss = 0
  for (let i = 1; i <= period; i++) {
    const d = closes[i] - closes[i - 1]
    if (d > 0) avgGain += d; else avgLoss += -d
  }
  avgGain /= period; avgLoss /= period
  out[period] = +(100 - 100 / (1 + avgGain / (avgLoss || 1e-10))).toFixed(2)
  for (let i = period + 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1]
    const g = d > 0 ? d : 0
    const l = d < 0 ? -d : 0
    avgGain = (avgGain * (period - 1) + g) / period
    avgLoss = (avgLoss * (period - 1) + l) / period
    out[i] = +(100 - 100 / (1 + avgGain / (avgLoss || 1e-10))).toFixed(2)
  }
  return out
}

// ── Time helper ───────────────────────────────────────────────────────────────

function toPeriodStart(dateStr: string, tf: TF): string {
  if (tf === '1D' || INTRADAY.has(tf)) return dateStr
  const d = new Date(dateStr + 'T00:00:00Z')
  if (tf === '1W') { const o = d.getUTCDay() === 0 ? 6 : d.getUTCDay() - 1; d.setUTCDate(d.getUTCDate() - o) }
  else if (tf === '1M') d.setUTCDate(1)
  else if (tf === '3M') d.setUTCMonth(Math.floor(d.getUTCMonth() / 3) * 3, 1)
  return d.toISOString().slice(0, 10)
}

function fmtNum(v: number | null | undefined, digits = 2): string {
  if (v == null) return '--'
  return v.toLocaleString('en-IN', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}
function fmtVol(v: number | null | undefined): string {
  if (v == null) return '--'
  if (v >= 1e7) return `${(v / 1e7).toFixed(2)}Cr`
  if (v >= 1e5) return `${(v / 1e5).toFixed(2)}L`
  return v.toFixed(0)
}

// ── API ───────────────────────────────────────────────────────────────────────

const fetchOhlcv = (sym: string, tf: TF) =>
  api.get<OhlcvResp>('/charts/ohlcv', { params: { symbol: sym, timeframe: tf } }).then(r => r.data)


// ── Toggle button ─────────────────────────────────────────────────────────────

function TogBtn({ label, active, color, onClick }: { label: string; active: boolean; color: string; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      padding: '4px 10px', borderRadius: 4, fontSize: 10, fontWeight: active ? 700 : 400,
      cursor: 'pointer', border: `1px solid ${active ? color : C.border}`,
      background: active ? color + '22' : 'transparent', color: active ? color : C.sub,
      transition: 'all .15s',
    }}>{label}</button>
  )
}

// ── RSI level line ─────────────────────────────────────────────────────────────

const RSI_LEVELS = [70, 50, 30]

// ── Main component ────────────────────────────────────────────────────────────

export function FullChartPage() {
  const { symbol: sym = '' }       = useParams<{ symbol: string }>()
  const [searchParams]             = useSearchParams()
  const navigate                   = useNavigate()
  const initTf                     = (searchParams.get('tf') as TF) || '1D'

  const [tf,       setTf]          = useState<TF>(initTf)
  const [showE20,  setShowE20]     = useState(true)
  const [showE50,  setShowE50]     = useState(true)
  const [showE200, setShowE200]    = useState(true)
  const [showBB,   setShowBB]      = useState(false)
  const [showRSI,  setShowRSI]     = useState(true)

  // Legend state — updated on crosshair move
  const [legend, setLegend] = useState<{
    o: number; h: number; l: number; c: number; v: number
    e20: number | null; e50: number | null; e200: number | null; rsi: number | null
  } | null>(null)

  // Chart DOM refs
  const mainDiv = useRef<HTMLDivElement>(null)
  const rsiDiv  = useRef<HTMLDivElement>(null)

  // Chart API refs
  const mainChart  = useRef<IChartApi | null>(null)
  const rsiChart   = useRef<IChartApi | null>(null)
  const syncingRef = useRef(false)   // prevent infinite sync loop

  // Series refs
  const sr = useRef<{
    candle?: ISeriesApi<'Candlestick', Time>
    vol?:    ISeriesApi<'Histogram', Time>
    e20?:    ISeriesApi<'Line', Time>
    e50?:    ISeriesApi<'Line', Time>
    e200?:   ISeriesApi<'Line', Time>
    bbU?:    ISeriesApi<'Line', Time>
    bbL?:    ISeriesApi<'Line', Time>
    rsiLine?: ISeriesApi<'Line', Time>
  }>({})

  // Computed indicator arrays — kept in sync with ohlcv
  const indRef = useRef<{
    e20: (number | null)[]; e50: (number | null)[]; e200: (number | null)[]
    bbU: (number | null)[]; bbL: (number | null)[]
    rsi: (number | null)[]
    times: string[]
  }>({ e20: [], e50: [], e200: [], bbU: [], bbL: [], rsi: [], times: [] })

  // ── Data fetching ─────────────────────────────────────────────────────────

  const { data: ohlcv, isLoading } = useQuery({
    queryKey: ['fullchart-ohlcv', sym, tf],
    queryFn: () => fetchOhlcv(sym.toUpperCase(), tf),
    enabled: !!sym,
  })

  const { data: caData } = useQuery({
    queryKey: ['fullchart-ca', sym],
    queryFn: () => fetchStockCorpActions(sym.toUpperCase(), 5),
    enabled: !!sym,
  })

  // ── Chart creation ────────────────────────────────────────────────────────

  useEffect(() => {
    if (!mainDiv.current || !rsiDiv.current) return

    const chartOpts = {
      layout: { background: { type: ColorType.Solid, color: C.bg }, textColor: C.sub, fontSize: 10, fontFamily: 'monospace' },
      grid:   { vertLines: { color: C.border }, horzLines: { color: C.border } },
      crosshair: { vertLine: { labelBackgroundColor: C.cell }, horzLine: { labelBackgroundColor: C.cell } },
      rightPriceScale: { borderColor: C.border },
      handleScroll: true, handleScale: true,
    }

    // ── Main chart ────────────────────────────────────────────────────────
    const mc = createChart(mainDiv.current, {
      ...chartOpts,
      autoSize: true,
      timeScale: { borderColor: C.border, timeVisible: false, secondsVisible: false },
    })

    const candle = mc.addSeries(CandlestickSeries, {
      upColor: C.green, downColor: C.red, borderVisible: false,
      wickUpColor: C.green, wickDownColor: C.red,
    })
    const vol = mc.addSeries(HistogramSeries, { priceScaleId: 'vol' })
    vol.priceScale().applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } })

    const e20  = mc.addSeries(LineSeries, { color: C.blue,   lineWidth: 1, priceLineVisible: false, crosshairMarkerVisible: false, visible: true })
    const e50  = mc.addSeries(LineSeries, { color: C.purple, lineWidth: 1, priceLineVisible: false, crosshairMarkerVisible: false, visible: true })
    const e200 = mc.addSeries(LineSeries, { color: C.amber,  lineWidth: 1, priceLineVisible: false, crosshairMarkerVisible: false, visible: true })
    const bbU  = mc.addSeries(LineSeries, { color: C.teal, lineWidth: 1, lineStyle: 1, priceLineVisible: false, crosshairMarkerVisible: false, visible: false })
    const bbL  = mc.addSeries(LineSeries, { color: C.teal, lineWidth: 1, lineStyle: 1, priceLineVisible: false, crosshairMarkerVisible: false, visible: false })

    sr.current = { candle, vol, e20, e50, e200, bbU, bbL }
    mainChart.current = mc

    // ── RSI chart ─────────────────────────────────────────────────────────
    const rc = createChart(rsiDiv.current, {
      ...chartOpts,
      autoSize: true,
      timeScale: { borderColor: C.border, timeVisible: INTRADAY.has(tf), secondsVisible: false },
      rightPriceScale: { borderColor: C.border, scaleMargins: { top: 0.1, bottom: 0.1 } },
    })

    const rsiLine = rc.addSeries(LineSeries, { color: C.amber, lineWidth: 1, priceLineVisible: false })

    // RSI level reference lines
    for (const lvl of RSI_LEVELS) {
      rsiLine.createPriceLine({
        price: lvl, color: lvl === 50 ? C.dim : lvl === 70 ? C.red + '88' : C.green + '88',
        lineWidth: 1, lineStyle: lvl === 50 ? 2 : 1,
        axisLabelVisible: true, title: lvl === 50 ? '' : String(lvl),
      })
    }

    sr.current.rsiLine = rsiLine
    rsiChart.current = rc

    // ── Time scale sync ───────────────────────────────────────────────────
    mc.timeScale().subscribeVisibleLogicalRangeChange(range => {
      if (syncingRef.current || !range) return
      syncingRef.current = true
      rc.timeScale().setVisibleLogicalRange(range)
      syncingRef.current = false
    })
    rc.timeScale().subscribeVisibleLogicalRangeChange(range => {
      if (syncingRef.current || !range) return
      syncingRef.current = true
      mc.timeScale().setVisibleLogicalRange(range)
      syncingRef.current = false
    })

    // ── Crosshair sync + legend ───────────────────────────────────────────
    mc.subscribeCrosshairMove(param => {
      // sync RSI crosshair
      if (param.time) rc.setCrosshairPosition(0, param.time, rsiLine)
      else rc.clearCrosshairPosition()

      // update legend
      if (!param.time || !param.seriesData) { setLegend(null); return }
      const cd = param.seriesData.get(candle) as { open: number; high: number; low: number; close: number } | undefined
      const vd = param.seriesData.get(vol) as { value: number } | undefined
      if (!cd) return

      const idx = indRef.current.times.indexOf(typeof param.time === 'string' ? param.time : String(param.time))
      setLegend({
        o: cd.open, h: cd.high, l: cd.low, c: cd.close, v: vd?.value ?? 0,
        e20:  idx >= 0 ? indRef.current.e20[idx]  : null,
        e50:  idx >= 0 ? indRef.current.e50[idx]  : null,
        e200: idx >= 0 ? indRef.current.e200[idx] : null,
        rsi:  idx >= 0 ? indRef.current.rsi[idx]  : null,
      })
    })
    rc.subscribeCrosshairMove(param => {
      if (param.time) mc.setCrosshairPosition(0, param.time, candle)
      else mc.clearCrosshairPosition()
    })

    return () => {
      mc.remove(); rc.remove()
      mainChart.current = rsiChart.current = null
      sr.current = {}
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Update timeVisible on RSI chart when TF changes ───────────────────────
  useEffect(() => {
    rsiChart.current?.applyOptions({ timeScale: { timeVisible: INTRADAY.has(tf) } })
    mainChart.current?.applyOptions({ timeScale: { timeVisible: false } })
  }, [tf])

  // ── Feed data to charts when OHLCV loads ─────────────────────────────────

  useEffect(() => {
    const { candle, vol, e20: s20, e50: s50, e200: s200, bbU: sBBU, bbL: sBBL, rsiLine } = sr.current
    if (!candle || !ohlcv?.bars?.length) return

    const bars = ohlcv.bars
    const times = bars.map(b => typeof b.time === 'string' ? toPeriodStart(b.time, tf) : String(b.time))
    const closes = bars.map(b => b.close)

    // Candlestick + Volume
    candle.setData(bars.map((b, i) => ({ time: times[i] as Time, open: b.open, high: b.high, low: b.low, close: b.close })))
    vol?.setData(bars.map((b, i) => ({
      time: times[i] as Time, value: b.volume ?? 0,
      color: b.close >= b.open ? C.green + '55' : C.red + '55',
    })))

    // Compute indicators
    const e20v  = calcEma(closes, 20)
    const e50v  = calcEma(closes, 50)
    const e200v = calcEma(closes, 200)
    const { upper: bbUv, lower: bbLv } = calcBB(closes)
    const rsiV  = calcRSI(closes)

    indRef.current = { e20: e20v, e50: e50v, e200: e200v, bbU: bbUv, bbL: bbLv, rsi: rsiV, times }

    const toSeries = (vals: (number | null)[]) =>
      vals.flatMap((v, i) => v != null ? [{ time: times[i] as Time, value: v }] : [])

    s20?.setData(toSeries(e20v))
    s50?.setData(toSeries(e50v))
    s200?.setData(toSeries(e200v))
    sBBU?.setData(toSeries(bbUv))
    sBBL?.setData(toSeries(bbLv))
    rsiLine?.setData(toSeries(rsiV))

    // Reset visible range
    const n = bars.length
    mainChart.current?.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - DEFAULT_BARS[tf]), to: n + 2 })
  }, [ohlcv, tf])

  // ── Corporate action markers ──────────────────────────────────────────────

  useEffect(() => {
    const { candle } = sr.current
    if (!candle || !caData?.actions?.length) return
    const CA_CFG: Record<string, { color: string; text: string }> = {
      DIVIDEND: { color: C.amber, text: 'D' }, BONUS: { color: C.green, text: 'B' },
      SPLIT: { color: C.blue, text: 'S' },     BUYBACK: { color: C.purple, text: '$' },
      RIGHTS: { color: C.teal, text: 'R' },
    }
    try {
      const markers = caData.actions
        .filter(a => CA_CFG[a.action_type])
        .map(a => {
          const cfg = CA_CFG[a.action_type]
          const label = a.action_type === 'DIVIDEND' && a.dividend_rs != null ? `Div Rs${a.dividend_rs}`
                      : a.action_type === 'BONUS'    && a.bonus_ratio  != null ? `Bonus ${a.bonus_ratio}:1`
                      : a.action_type === 'SPLIT'    && a.split_new_fv != null ? `FV${a.split_new_fv}`
                      : cfg.text
          return { time: a.ex_date.slice(0, 10) as Time, position: 'belowBar' as const, color: cfg.color, shape: 'circle' as const, text: label, size: 0.8 }
        })
        .sort((a, b) => String(a.time).localeCompare(String(b.time)))
      candle.setMarkers(markers)
    } catch { /* cosmetic — ignore */ }
  }, [caData])

  // ── Indicator visibility toggles ──────────────────────────────────────────

  useEffect(() => { sr.current.e20?.applyOptions({ visible: showE20 }) }, [showE20])
  useEffect(() => { sr.current.e50?.applyOptions({ visible: showE50 }) }, [showE50])
  useEffect(() => { sr.current.e200?.applyOptions({ visible: showE200 }) }, [showE200])
  useEffect(() => {
    sr.current.bbU?.applyOptions({ visible: showBB })
    sr.current.bbL?.applyOptions({ visible: showBB })
  }, [showBB])

  const resetView = useCallback(() => {
    const n = ohlcv?.bars?.length ?? 0
    if (n > 0) mainChart.current?.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - DEFAULT_BARS[tf]), to: n + 2 })
  }, [ohlcv, tf])

  // ── RSI color from current value ──────────────────────────────────────────

  const rsiVal = legend?.rsi
  const rsiColor = rsiVal == null ? C.sub : rsiVal >= 70 ? C.red : rsiVal >= 55 ? C.green : rsiVal >= 45 ? C.sub : rsiVal >= 30 ? C.amber : '#FF6060'

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh', background: C.bg, overflow: 'hidden', fontFamily: 'monospace' }}>

      {/* ── Toolbar ──────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px',
        background: C.panel, borderBottom: `1px solid ${C.border}`, flexWrap: 'wrap', flexShrink: 0,
      }}>
        {/* Back */}
        <button onClick={() => navigate(-1)} style={{
          padding: '5px 10px', borderRadius: 4, border: `1px solid ${C.border}`,
          background: 'transparent', color: C.sub, cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
        }}>
          &larr; Back
        </button>

        {/* Symbol */}
        <span style={{ fontSize: 15, fontWeight: 900, color: C.text, letterSpacing: 2, minWidth: 100 }}>{sym.toUpperCase()}</span>

        {/* Divider */}
        <div style={{ width: 1, height: 18, background: C.border }} />

        {/* TF — Intraday */}
        {TF_INTRA.map(t => (
          <button key={t} onClick={() => setTf(t)} style={{
            padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
            border: `1px solid ${tf === t ? C.blue : C.border}`,
            background: tf === t ? C.blue + '22' : 'transparent',
            color: tf === t ? C.blue : C.sub, fontWeight: tf === t ? 700 : 400,
          }}>{t}</button>
        ))}

        <div style={{ width: 1, height: 14, background: C.border }} />

        {/* TF — Daily+ */}
        {TF_DAILY.map(t => (
          <button key={t} onClick={() => setTf(t)} style={{
            padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
            border: `1px solid ${tf === t ? C.green : C.border}`,
            background: tf === t ? C.green + '22' : 'transparent',
            color: tf === t ? C.green : C.sub, fontWeight: tf === t ? 700 : 400,
          }}>{t}</button>
        ))}

        <div style={{ width: 1, height: 14, background: C.border }} />

        {/* Indicator toggles */}
        <TogBtn label="EMA 20"  active={showE20}  color={C.blue}   onClick={() => setShowE20(v  => !v)} />
        <TogBtn label="EMA 50"  active={showE50}  color={C.purple} onClick={() => setShowE50(v  => !v)} />
        <TogBtn label="EMA 200" active={showE200} color={C.amber}  onClick={() => setShowE200(v => !v)} />
        <TogBtn label="BB"      active={showBB}   color={C.teal}   onClick={() => setShowBB(v   => !v)} />
        <TogBtn label="RSI"     active={showRSI}  color={C.amber}  onClick={() => setShowRSI(v  => !v)} />

        <div style={{ width: 1, height: 14, background: C.border }} />
        <button onClick={resetView} style={{ padding: '4px 9px', borderRadius: 4, fontSize: 10, cursor: 'pointer', border: `1px solid ${C.border}`, background: 'transparent', color: C.dim }}>Reset</button>

        {/* Loading indicator */}
        {isLoading && <span style={{ fontSize: 10, color: C.sub, marginLeft: 'auto' }}>Loading {tf}...</span>}
      </div>

      {/* ── Crosshair legend bar ─────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16, padding: '4px 14px',
        background: C.cell, borderBottom: `1px solid ${C.border}`, fontSize: 10, flexShrink: 0,
        fontVariantNumeric: 'tabular-nums', minHeight: 26,
      }}>
        {legend ? (
          <>
            <span>O <span style={{ color: C.text }}>{fmtNum(legend.o)}</span></span>
            <span>H <span style={{ color: C.green }}>{fmtNum(legend.h)}</span></span>
            <span>L <span style={{ color: C.red }}>{fmtNum(legend.l)}</span></span>
            <span>C <span style={{ color: legend.c >= legend.o ? C.green : C.red, fontWeight: 700 }}>{fmtNum(legend.c)}</span></span>
            <span>Vol <span style={{ color: C.text }}>{fmtVol(legend.v)}</span></span>
            <div style={{ width: 1, height: 12, background: C.border }} />
            {showE20  && legend.e20  != null && <span>EMA20 <span style={{ color: C.blue   }}>{fmtNum(legend.e20)}</span></span>}
            {showE50  && legend.e50  != null && <span>EMA50 <span style={{ color: C.purple }}>{fmtNum(legend.e50)}</span></span>}
            {showE200 && legend.e200 != null && <span>EMA200 <span style={{ color: C.amber }}>{fmtNum(legend.e200)}</span></span>}
            {showRSI  && rsiVal != null && (
              <>
                <div style={{ width: 1, height: 12, background: C.border }} />
                <span>RSI <span style={{ color: rsiColor, fontWeight: 700 }}>{fmtNum(rsiVal, 1)}</span>
                  <span style={{ color: rsiColor, marginLeft: 4 }}>{rsiVal >= 70 ? 'OVERBOUGHT' : rsiVal >= 55 ? 'BULLISH' : rsiVal >= 45 ? 'NEUTRAL' : rsiVal >= 30 ? 'BEARISH' : 'OVERSOLD'}</span>
                </span>
              </>
            )}
          </>
        ) : (
          <span style={{ color: C.dim }}>Hover over chart to see OHLCV values</span>
        )}
      </div>

      {/* ── Main chart ───────────────────────────────────────────────────── */}
      <div ref={mainDiv} style={{ flex: 1, minHeight: 0 }} />

      {/* ── RSI pane ─────────────────────────────────────────────────────── */}
      {showRSI && (
        <div style={{ flexShrink: 0, borderTop: `1px solid ${C.border}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '3px 14px', background: C.cell, fontSize: 9, color: C.dim }}>
            <span style={{ fontWeight: 700, letterSpacing: '0.08em' }}>RSI (14)</span>
            <span style={{ color: C.red + 'AA' }}>Overbought &gt;70</span>
            <span style={{ color: C.green + 'AA' }}>Oversold &lt;30</span>
          </div>
          <div ref={rsiDiv} style={{ height: 130 }} />
        </div>
      )}

      {/* ── Status bar ───────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16, padding: '4px 14px',
        background: C.panel, borderTop: `1px solid ${C.border}`, fontSize: 10, color: C.dim, flexShrink: 0,
      }}>
        <span style={{ color: C.sub }}>{sym.toUpperCase()}</span>
        <span>TF: <span style={{ color: C.text }}>{tf}</span></span>
        {ohlcv && <span>{ohlcv.count} bars</span>}
        <span style={{ marginLeft: 'auto' }}>Capital Flow Intelligence Platform</span>
      </div>
    </div>
  )
}
