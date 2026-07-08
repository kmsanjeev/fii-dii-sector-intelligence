/**
 * Custom KLineChart indicators for NSE trading.
 * Import this module once (side-effect import) before creating KLineChartPro.
 * Each registerIndicator() call adds the indicator to Pro's built-in picker.
 *
 * Indicators added:
 *   VWAP        — Volume Weighted Average Price (resets per session)
 *   Supertrend  — ATR-based trend with bull/bear coloring (default 7,3)
 *   HMA         — Hull Moving Average, smoother than EMA (default 9)
 */

import { registerIndicator, IndicatorSeries } from 'klinecharts'
import type { KLineData, Indicator } from 'klinecharts'

// ── VWAP ─────────────────────────────────────────────────────────────────────
// Resets at each UTC date boundary (≈ NSE session start for daily charts).
// For intraday (5M/15M/1H), this gives the correct intraday VWAP per session.

registerIndicator<{ vwap: number | null }>({
  name:      'VWAP',
  shortName: 'VWAP',
  series:    IndicatorSeries.Price,
  calcParams: [],
  figures: [
    { key: 'vwap', title: 'VWAP', type: 'line' },
  ],
  styles: {
    lines: [{ color: '#7b61ff', size: 2 }],
  },
  calc(dataList: KLineData[]) {
    let cumPV = 0, cumV = 0, lastDay = ''
    return dataList.map(bar => {
      // Detect new session by date change in UTC timestamp
      const day = new Date(bar.timestamp).toISOString().slice(0, 10)
      if (day !== lastDay) { cumPV = 0; cumV = 0; lastDay = day }
      const tp  = (bar.high + bar.low + bar.close) / 3
      const vol = bar.volume ?? 0
      cumPV += tp * vol
      cumV  += vol
      return { vwap: cumV > 0 ? cumPV / cumV : null }
    })
  },
})

// ── Supertrend ────────────────────────────────────────────────────────────────
// Uses Wilder's ATR. Two figures: supertrendUp (teal, bullish line below price)
// and supertrendDown (red, bearish line above price). Null in the inactive state
// so the chart draws them as separate coloured segments.

registerIndicator<{ supertrendUp: number | null; supertrendDown: number | null }>({
  name:      'Supertrend',
  shortName: 'ST',
  series:    IndicatorSeries.Price,
  calcParams: [7, 3],
  figures: [
    { key: 'supertrendUp',   title: 'ST Bull', type: 'line' },
    { key: 'supertrendDown', title: 'ST Bear', type: 'line' },
  ],
  styles: {
    lines: [
      { color: '#26a69a', size: 2 },  // bull — teal
      { color: '#ef5350', size: 2 },  // bear — red
    ],
  },
  calc(dataList: KLineData[], indicator: Indicator) {
    const [period, mult] = indicator.calcParams as [number, number]
    type R = { supertrendUp: number | null; supertrendDown: number | null }
    const n = dataList.length
    const EMPTY: R = { supertrendUp: null, supertrendDown: null }

    if (n < period + 1) return dataList.map(() => ({ ...EMPTY }))

    // True Range
    const tr = dataList.map((bar, i) => {
      if (i === 0) return bar.high - bar.low
      const pc = dataList[i - 1].close
      return Math.max(bar.high - bar.low, Math.abs(bar.high - pc), Math.abs(bar.low - pc))
    })

    // Wilder's ATR
    const atr: number[] = new Array(n).fill(0)
    atr[period - 1] = tr.slice(0, period).reduce((a, b) => a + b, 0) / period
    for (let i = period; i < n; i++) atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    const results: R[]     = dataList.map(() => ({ ...EMPTY }))
    const finalUpper: number[] = new Array(n).fill(0)
    const finalLower: number[] = new Array(n).fill(0)

    for (let i = period - 1; i < n; i++) {
      const { high, low, close } = dataList[i]
      const hl2       = (high + low) / 2
      const basicUpper = hl2 + mult * atr[i]
      const basicLower = hl2 - mult * atr[i]

      if (i === period - 1) {
        finalUpper[i] = basicUpper
        finalLower[i] = basicLower
        results[i]    = { supertrendUp: finalLower[i], supertrendDown: null } // assume uptrend at start
        continue
      }

      const pc = dataList[i - 1].close
      // Tighten bands only — never widen them mid-trend
      finalUpper[i] = basicUpper < finalUpper[i - 1] || pc > finalUpper[i - 1] ? basicUpper : finalUpper[i - 1]
      finalLower[i] = basicLower > finalLower[i - 1] || pc < finalLower[i - 1] ? basicLower : finalLower[i - 1]

      // Direction flip logic
      const wasUp = results[i - 1].supertrendUp !== null
      const isUp  = wasUp
        ? close >= finalLower[i]   // stay up unless close breaks below support
        : close >  finalUpper[i]   // flip to up only when close clears resistance

      results[i] = isUp
        ? { supertrendUp: finalLower[i], supertrendDown: null }
        : { supertrendUp: null, supertrendDown: finalUpper[i] }
    }

    return results
  },
})

// ── HMA — Hull Moving Average ─────────────────────────────────────────────────
// HMA(n) = WMA(sqrt(n),  2·WMA(n/2) − WMA(n))
// Dramatically reduces MA lag while staying smooth. Default period 9.

registerIndicator<{ hma: number | null }>({
  name:      'HMA',
  shortName: 'HMA',
  series:    IndicatorSeries.Price,
  calcParams: [9],
  figures: [
    { key: 'hma', title: 'HMA', type: 'line' },
  ],
  styles: {
    lines: [{ color: '#f97316', size: 2 }],
  },
  calc(dataList: KLineData[], indicator: Indicator) {
    const [period] = indicator.calcParams as [number]
    const closes   = dataList.map(b => b.close)
    const hmaVals  = hma(closes, period)
    return hmaVals.map(v => ({ hma: v }))
  },
})

// ── WMA + HMA helpers ─────────────────────────────────────────────────────────

function wma(values: number[], period: number): (number | null)[] {
  const denom = (period * (period + 1)) / 2
  return values.map((_, i) => {
    if (i < period - 1) return null
    let num = 0
    for (let j = 0; j < period; j++) num += values[i - period + 1 + j] * (j + 1)
    return num / denom
  })
}

function hma(closes: number[], period: number): (number | null)[] {
  const half  = Math.floor(period / 2)
  const sqrtP = Math.round(Math.sqrt(period))

  const wmaFull = wma(closes, period)
  const wmaHalf = wma(closes, half)

  // Raw = 2·WMA(half) − WMA(full)
  const raw: number[] = wmaFull.map((f, i) => {
    const h = wmaHalf[i]
    if (f === null || h === null) return NaN
    return 2 * h - f
  })

  // WMA of raw (sqrtP period), aligned back to original indices
  const firstValid = raw.findIndex(v => !isNaN(v))
  const rawValid   = raw.filter(v => !isNaN(v))
  const wmaOfRaw   = wma(rawValid, sqrtP)

  const result: (number | null)[] = new Array(closes.length).fill(null)
  wmaOfRaw.forEach((v, j) => { result[firstValid + j] = v })
  return result
}
