/**
 * Custom KLineChart indicators for NSE trading.
 * Side-effect import — call once before creating KLineChartPro.
 *
 * Indicators registered:
 *   VWAP        — Volume Weighted Average Price (session-resetting)
 *   Supertrend  — ATR-based trend, bull/bear coloring (7, 3)
 *   HMA         — Hull Moving Average (9)
 *   VOLMain     — Volume bars on main price pane (bottom 20%)
 *   CorpActions — Corporate action markers (D/B/S/R/X triangles)
 *   AlertLines  — User-defined price alert horizontal lines
 */

import { registerIndicator, IndicatorSeries, LineType } from 'klinecharts'
import type { KLineData, Indicator, IndicatorDrawParams } from 'klinecharts'

// ── VWAP ─────────────────────────────────────────────────────────────────────

registerIndicator<{ vwap: number | null }>({
  name: 'VWAP', shortName: 'VWAP',
  series: IndicatorSeries.Price,
  calcParams: [],
  figures: [{ key: 'vwap', title: 'VWAP', type: 'line' }],
  styles: { lines: [{ color: '#7b61ff', size: 2, style: LineType.Solid, dashedValue: [], smooth: false }] },
  calc(dataList: KLineData[]) {
    let cumPV = 0, cumV = 0, lastDay = ''
    return dataList.map(bar => {
      const day = new Date(bar.timestamp).toISOString().slice(0, 10)
      if (day !== lastDay) { cumPV = 0; cumV = 0; lastDay = day }
      const tp = (bar.high + bar.low + bar.close) / 3
      const vol = bar.volume ?? 0
      cumPV += tp * vol; cumV += vol
      return { vwap: cumV > 0 ? cumPV / cumV : null }
    })
  },
})

// ── Supertrend ────────────────────────────────────────────────────────────────

registerIndicator<{ supertrendUp: number | null; supertrendDown: number | null }>({
  name: 'Supertrend', shortName: 'ST',
  series: IndicatorSeries.Price,
  calcParams: [7, 3],
  figures: [
    { key: 'supertrendUp',   title: 'ST Bull', type: 'line' },
    { key: 'supertrendDown', title: 'ST Bear', type: 'line' },
  ],
  styles: {
    lines: [
      { color: '#26a69a', size: 2, style: LineType.Solid, dashedValue: [], smooth: false },
      { color: '#ef5350', size: 2, style: LineType.Solid, dashedValue: [], smooth: false },
    ],
  },
  calc(dataList: KLineData[], indicator: Indicator) {
    const [period, mult] = indicator.calcParams as [number, number]
    type R = { supertrendUp: number | null; supertrendDown: number | null }
    const n = dataList.length
    const EMPTY: R = { supertrendUp: null, supertrendDown: null }
    if (n < period + 1) return dataList.map(() => ({ ...EMPTY }))

    const tr = dataList.map((bar, i) => {
      if (i === 0) return bar.high - bar.low
      const pc = dataList[i - 1].close
      return Math.max(bar.high - bar.low, Math.abs(bar.high - pc), Math.abs(bar.low - pc))
    })
    const atr: number[] = new Array(n).fill(0)
    atr[period - 1] = tr.slice(0, period).reduce((a, b) => a + b, 0) / period
    for (let i = period; i < n; i++) atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    const results: R[] = dataList.map(() => ({ ...EMPTY }))
    const finalUpper: number[] = new Array(n).fill(0)
    const finalLower: number[] = new Array(n).fill(0)

    for (let i = period - 1; i < n; i++) {
      const { high, low, close } = dataList[i]
      const hl2 = (high + low) / 2
      const basicUpper = hl2 + mult * atr[i]
      const basicLower = hl2 - mult * atr[i]
      if (i === period - 1) {
        finalUpper[i] = basicUpper; finalLower[i] = basicLower
        results[i] = { supertrendUp: finalLower[i], supertrendDown: null }
        continue
      }
      const pc = dataList[i - 1].close
      finalUpper[i] = basicUpper < finalUpper[i - 1] || pc > finalUpper[i - 1] ? basicUpper : finalUpper[i - 1]
      finalLower[i] = basicLower > finalLower[i - 1] || pc < finalLower[i - 1] ? basicLower : finalLower[i - 1]
      const wasUp = results[i - 1].supertrendUp !== null
      const isUp = wasUp ? close >= finalLower[i] : close > finalUpper[i]
      results[i] = isUp
        ? { supertrendUp: finalLower[i], supertrendDown: null }
        : { supertrendUp: null, supertrendDown: finalUpper[i] }
    }
    return results
  },
})

// ── HMA — Hull Moving Average ─────────────────────────────────────────────────

registerIndicator<{ hma: number | null }>({
  name: 'HMA', shortName: 'HMA',
  series: IndicatorSeries.Price,
  calcParams: [9],
  figures: [{ key: 'hma', title: 'HMA', type: 'line' }],
  styles: { lines: [{ color: '#f97316', size: 2, style: LineType.Solid, dashedValue: [], smooth: false }] },
  calc(dataList: KLineData[], indicator: Indicator) {
    const [period] = indicator.calcParams as [number]
    return hmaCalc(dataList.map(b => b.close), period).map(v => ({ hma: v }))
  },
})

function wma(values: number[], period: number): (number | null)[] {
  const denom = (period * (period + 1)) / 2
  return values.map((_, i) => {
    if (i < period - 1) return null
    let num = 0
    for (let j = 0; j < period; j++) num += values[i - period + 1 + j] * (j + 1)
    return num / denom
  })
}

function hmaCalc(closes: number[], period: number): (number | null)[] {
  const half = Math.floor(period / 2)
  const sqrtP = Math.round(Math.sqrt(period))
  const wmaFull = wma(closes, period)
  const wmaHalf = wma(closes, half)
  const raw: number[] = wmaFull.map((f, i) => {
    const h = wmaHalf[i]
    if (f === null || h === null) return NaN
    return 2 * h - f
  })
  const firstValid = raw.findIndex(v => !isNaN(v))
  const rawValid = raw.filter(v => !isNaN(v))
  const wmaOfRaw = wma(rawValid, sqrtP)
  const result: (number | null)[] = new Array(closes.length).fill(null)
  wmaOfRaw.forEach((v, j) => { result[firstValid + j] = v })
  return result
}

// ── VOLMain — volume bars on the main price pane ──────────────────────────────

registerIndicator<Record<string, never>>({
  name: 'VOLMain', shortName: 'V',
  series: IndicatorSeries.Price,
  calcParams: [], figures: [],
  calc(dataList: KLineData[]) { return dataList.map(() => ({} as Record<string, never>)) },
  draw(params: IndicatorDrawParams<Record<string, never>>): boolean {
    const { ctx, kLineDataList, visibleRange, bounding, barSpace, xAxis } = params
    const { from, to } = visibleRange
    let maxVol = 0
    for (let i = from; i <= to; i++) {
      const v = kLineDataList[i]?.volume ?? 0
      if (v > maxVol) maxVol = v
    }
    if (!maxVol) return true
    const volZoneH = bounding.height * 0.20
    const bottom = bounding.bottom
    for (let i = from; i <= to; i++) {
      const bar = kLineDataList[i]; if (!bar) continue
      const vol = bar.volume ?? 0; if (!vol) continue
      const h = (vol / maxVol) * volZoneH
      const x = xAxis.convertToPixel(i)
      ctx.fillStyle = bar.close >= bar.open ? 'rgba(38,166,154,0.40)' : 'rgba(239,83,80,0.40)'
      ctx.fillRect(
        Math.round(x - barSpace.halfBar), Math.round(bottom - h),
        Math.max(Math.round(barSpace.bar), 1), Math.max(Math.round(h), 1)
      )
    }
    return true
  },
})

// ── CorpActions — corporate action markers at bar bottom ──────────────────────
// Call setCorpActions() after chart init to populate markers for the current symbol.

const CORP_COLOR: Record<string, string> = {
  DIVIDEND: '#06b6d4',  // cyan
  BONUS:    '#22c55e',  // green
  SPLIT:    '#f97316',  // orange
  RIGHTS:   '#a855f7',  // purple
  BUYBACK:  '#3b82f6',  // blue
}
const CORP_LABEL: Record<string, string> = {
  DIVIDEND: 'D', BONUS: 'B', SPLIT: 'S', RIGHTS: 'R', BUYBACK: 'X',
}

interface CorpMark { ts: number; type: string; label: string; color: string }
let _corpMarks: CorpMark[] = []

export function setCorpActions(actions: Array<{ ex_date: string; action_type: string }>) {
  _corpMarks = actions
    .filter(a => a.ex_date && CORP_LABEL[a.action_type?.toUpperCase()])
    .map(a => {
      const type = a.action_type.toUpperCase()
      return {
        ts:    new Date(a.ex_date + 'T00:00:00Z').getTime(),
        type,
        label: CORP_LABEL[type] ?? '?',
        color: CORP_COLOR[type] ?? '#888',
      }
    })
}

export function clearCorpActions() { _corpMarks = [] }

registerIndicator<Record<string, never>>({
  name: 'CorpActions', shortName: '',
  series: IndicatorSeries.Price,
  calcParams: [], figures: [],
  calc(dataList: KLineData[]) { return dataList.map(() => ({} as Record<string, never>)) },
  draw(params: IndicatorDrawParams<Record<string, never>>): boolean {
    if (!_corpMarks.length) return true
    const { ctx, kLineDataList, visibleRange, bounding, xAxis, barSpace } = params
    const { from, to } = visibleRange

    // Map bar date-strings to bar indices for O(1) lookup
    const dateIdx = new Map<string, number>()
    for (let i = from; i <= to; i++) {
      const bar = kLineDataList[i]
      if (bar) dateIdx.set(new Date(bar.timestamp).toISOString().slice(0, 10), i)
    }

    const bottom = bounding.bottom - 3
    const triH = 8, triW = 6

    for (const mark of _corpMarks) {
      const d = new Date(mark.ts).toISOString().slice(0, 10)
      const idx = dateIdx.get(d)
      if (idx === undefined) continue
      const x = xAxis.convertToPixel(idx)

      // Upward-pointing triangle ▲ sitting at bottom of pane
      ctx.fillStyle = mark.color
      ctx.beginPath()
      ctx.moveTo(x, bottom - triH)     // tip
      ctx.lineTo(x - triW, bottom)     // bottom-left
      ctx.lineTo(x + triW, bottom)     // bottom-right
      ctx.closePath()
      ctx.fill()

      // Letter label inside the triangle (only if bars are wide enough)
      if (barSpace.bar >= 8) {
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 6px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'bottom'
        ctx.fillText(mark.label, x, bottom - 1)
      }
    }
    return true
  },
})

// ── AlertLines — user-defined price alert horizontal lines ────────────────────
// Call setAlertPrices() from outside to set active alert levels.

let _alertPrices: number[] = []

export function setAlertPrices(prices: number[]) { _alertPrices = [...prices] }
export function clearAlertPrices() { _alertPrices = [] }

registerIndicator<Record<string, never>>({
  name: 'AlertLines', shortName: '',
  series: IndicatorSeries.Price,
  calcParams: [], figures: [],
  calc(dataList: KLineData[]) { return dataList.map(() => ({} as Record<string, never>)) },
  draw(params: IndicatorDrawParams<Record<string, never>>): boolean {
    if (!_alertPrices.length) return true
    const { ctx, bounding, yAxis } = params

    for (const price of _alertPrices) {
      const y = yAxis.convertToPixel(price)
      if (y < bounding.top || y > bounding.bottom) continue

      // Dashed orange line
      ctx.save()
      ctx.strokeStyle = '#f97316'
      ctx.lineWidth = 1
      ctx.setLineDash([5, 4])
      ctx.beginPath()
      ctx.moveTo(bounding.left, y)
      ctx.lineTo(bounding.right, y)
      ctx.stroke()

      // Price label on right edge
      const label = `Alert ${price.toFixed(2)}`
      const labelW = ctx.measureText(label).width + 8
      ctx.setLineDash([])
      ctx.fillStyle = '#f97316'
      ctx.fillRect(bounding.right - labelW - 2, y - 8, labelW + 2, 15)
      ctx.fillStyle = '#ffffff'
      ctx.font = '9px monospace'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillText(label, bounding.right - 4, y)
      ctx.restore()
    }
    return true
  },
})
