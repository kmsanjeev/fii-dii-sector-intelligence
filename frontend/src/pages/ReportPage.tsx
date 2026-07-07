/**
 * ReportPage — Premium Stock Intelligence Report (v2)
 * Route: /report/:symbol
 *
 * Full redesign: SVG arc gauges, SVG sparkline, SVG zodiac wheel,
 * all Kundli tabs rendered inline (no tabs), professional print layout.
 */

import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  api, fetchStockDetail, fetchStockCorpActions, fetchStockAnnouncements,
  type Announcement, type CorpAction,
} from '../api/client'

// ── Types ─────────────────────────────────────────────────────────────────────

type Bar = { time: string | number; open: number; high: number; low: number; close: number; volume: number }
type OhlcvResponse = { bars: Bar[] }

interface KPlanet {
  longitude: number; sign: string; sign_num: number; degree: number; house: number
  nakshatra: string; pada: number; nakshatra_lord: string; dignity: string; retrograde: boolean
}
interface KDashaEntry { planet: string; start_date: string; end_date: string }
interface KHouseData {
  sign: string; lord: string; lord_house: number | null; lord_dignity: string
  occupants: string[]; strength: string; signification: string
}
interface KYoga { name: string; effect: string; score: number; signal: string }
interface KundliData {
  entity: { type: string; name: string; inception_date: string; inception_time: string }
  lagna: { sign: string; degree: number; lord: string; full_longitude: number }
  planets: Record<string, KPlanet>
  current_dasha: {
    mahadasha: KDashaEntry; antardasha: KDashaEntry; pratyantardasha: KDashaEntry
    all_mahadashas: KDashaEntry[]
  }
  financial_houses: Record<string, KHouseData>
  yogas: KYoga[]
  transits: Record<string, { current_sign: string; natal_sign: string; aspect: string }>
  astro_score: number; astro_action: string; computed_date: string
}
interface KGannData {
  square_of_9: {
    current_degree: number; nearest_angle: string
    levels: Record<string, { angle: number; resistances: number[]; supports: number[]; is_nearest: boolean }>
  }
  gann_levels: { resistance: number[]; support: number[]; key_r1: number | null; key_s1: number | null }
  time_cycles: { current_sun_degree: number; fixed_future_dates: Record<string, string> }
  planetary_lines: Record<string, { longitude: number; base_price: number }>
}
interface KInterpretation {
  signal: string; astro_score: number
  bullish_factors: string[]; bearish_factors: string[]
  dasha_outlook: Array<{ period: string; start: string; end: string; outlook: string }>
  narrative: string; yogas: string[]
}
interface KundliResponse {
  symbol: string; exchange: string
  kundli: KundliData; gann: KGannData | null; interpretation: KInterpretation
}

// ── Fetchers ──────────────────────────────────────────────────────────────────

const fetchOhlcv = (sym: string) =>
  api.get<OhlcvResponse>('/charts/ohlcv', { params: { symbol: sym, timeframe: '1D' } }).then(r => r.data)

const fetchKundli = (sym: string) =>
  api.get<KundliResponse>(`/stocks/${sym}/kundli`).then(r => r.data)

// ── Design tokens ─────────────────────────────────────────────────────────────

const C = {
  bg:      '#07101F',
  surf:    '#0C1829',
  surf2:   '#101E30',
  border:  '#1A2E47',
  borderH: '#243E5E',
  accent:  '#1B6BF5',
  gold:    '#D4991A',
  red:     '#CC3333',
  green:   '#0F9E6E',
  teal:    '#0BB8A3',
  purple:  '#8B6BF5',
  orange:  '#F97316',
  text:    '#D2E3F4',
  sub:     '#86A8C8',
  muted:   '#526A80',
  dim:     '#2E4660',
}

// ── Format helpers ────────────────────────────────────────────────────────────

const fmt = {
  pct:  (v: number | null | undefined) => v == null ? '--' : `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`,
  num:  (v: number | null | undefined, dp = 2) => v == null ? '--' : v.toFixed(dp),
  rs:   (v: number | null | undefined, dp = 0) => v == null ? '--' : `₹${v.toFixed(dp)}`,
  cr:   (v: number | null | undefined) => {
    if (v == null) return '--'
    const abs = Math.abs(v)
    const sign = v < 0 ? '-' : ''
    if (abs >= 1e5) return `${sign}${(abs / 1e5).toFixed(1)}L Cr`
    if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(1)}K Cr`
    return `${sign}${abs.toFixed(0)} Cr`
  },
  date: (d: string | null | undefined) => d ? String(d).slice(0, 10) : '--',
}

const scoreColor = (v: number) => v >= 65 ? C.green : v >= 42 ? C.gold : C.red
const sentColor  = (v: number) => v >= 30 ? C.green : v >= 0 ? C.accent : v >= -20 ? C.gold : C.red

const PLANET_ORDER = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu']
const PLANET_ABBR: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
  Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}
const DIGNITY_COLOR: Record<string, string> = {
  exalted_exact: C.green, exalted: C.green, moolatrikona: C.teal,
  own_sign: C.accent, friendly: C.sub, neutral: C.muted, enemy: C.gold, debilitated: C.red,
}
const DASHA_COLOR: Record<string, string> = {
  Sun: C.gold, Moon: C.accent, Mars: C.red, Mercury: C.green,
  Jupiter: C.teal, Venus: C.purple, Saturn: C.orange,
  Rahu: '#E879F9', Ketu: C.muted,
}
const ZODIAC_FULL = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
const ZODIAC_ABBR = ['Ari','Tau','Gem','Can','Leo','Vir','Lib','Sco','Sag','Cap','Aqu','Pis']

const YOGA_COLOR: Record<string, string> = {
  BUY: C.green, HOLD: C.accent, CAUTION: C.gold, EXIT: C.orange, AVOID: C.red,
}
const HOUSE_STRENGTH_COLOR: Record<string, string> = {
  strong: C.green, 'moderate-strong': C.accent, moderate: C.sub, weak: C.red,
}
const SIGNAL_COLOR: Record<string, string> = {
  STRONG_BUY: C.green, BUY: C.green, HOLD: C.accent, CAUTION: C.gold, EXIT: C.orange, AVOID: C.red,
}
const CA_CFG: Record<string, { color: string }> = {
  DIVIDEND: { color: C.gold }, BONUS: { color: C.green }, SPLIT: { color: C.accent },
  BUYBACK: { color: C.purple }, RIGHTS: { color: C.teal },
}

// ── SVG helpers ───────────────────────────────────────────────────────────────

function svgArcPath(cx: number, cy: number, r: number, startDeg: number, sweepDeg: number): string {
  const rad = (d: number) => d * Math.PI / 180
  const sx = cx + r * Math.cos(rad(startDeg))
  const sy = cy + r * Math.sin(rad(startDeg))
  const endDeg = startDeg + sweepDeg
  const ex = cx + r * Math.cos(rad(endDeg))
  const ey = cy + r * Math.sin(rad(endDeg))
  const la = sweepDeg > 180 ? 1 : 0
  return `M ${sx.toFixed(2)} ${sy.toFixed(2)} A ${r} ${r} 0 ${la} 1 ${ex.toFixed(2)} ${ey.toFixed(2)}`
}

// ── Reusable components ───────────────────────────────────────────────────────

function SH({ label, accent }: { label: string; accent?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 9, margin: '16px 0 7px', pageBreakAfter: 'avoid', breakAfter: 'avoid' }}>
      <div style={{ width: 3, height: 13, background: accent ?? C.accent, borderRadius: 2, flexShrink: 0 }} />
      <div style={{ fontSize: 8.5, fontWeight: 800, color: C.muted, letterSpacing: '.16em', textTransform: 'uppercase' as const }}>{label}</div>
      <div style={{ flex: 1, height: 1, background: C.border }} />
    </div>
  )
}

function Chip({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 9px', borderRadius: 10,
      fontSize: 9, fontWeight: 700, letterSpacing: '.05em',
      background: color + '1A', border: `1px solid ${color}44`, color,
    }}>{label}</span>
  )
}

function ArcGauge({ value, max = 100, label, size = 72, colorOverride }: {
  value: number | null | undefined; max?: number; label: string; size?: number; colorOverride?: string
}) {
  if (value == null) return (
    <div style={{ textAlign: 'center', minWidth: size }}>
      <svg width={size} height={Math.round(size * 0.72)} viewBox={`0 0 ${size} ${Math.round(size * 0.72)}`}>
        <path d={svgArcPath(size/2, Math.round(size*.58), Math.round(size*.40), 135, 270)} fill="none" stroke={C.border} strokeWidth={size * 0.09} strokeLinecap="round" />
        <text x={size/2} y={Math.round(size*.62)} textAnchor="middle" fill={C.dim} fontSize={size * 0.22}>--</text>
      </svg>
      <div style={{ fontSize: 7.5, color: C.dim, letterSpacing: '.1em', fontWeight: 700, textTransform: 'uppercase' as const, marginTop: 2 }}>{label}</div>
    </div>
  )
  const cx = size / 2
  const cy = Math.round(size * 0.58)
  const r  = Math.round(size * 0.40)
  const sw = size * 0.09
  const pct = Math.min(1, Math.max(0, value / max))
  const sweepDeg = pct * 270
  const color = colorOverride ?? scoreColor(pct * 100)
  const fgPath = sweepDeg > 0.5 ? svgArcPath(cx, cy, r, 135, sweepDeg) : null
  const h = Math.round(size * 0.72)
  return (
    <div style={{ textAlign: 'center', pageBreakInside: 'avoid', breakInside: 'avoid', minWidth: size }}>
      <svg width={size} height={h} viewBox={`0 0 ${size} ${h}`}>
        <path d={svgArcPath(cx, cy, r, 135, 270)} fill="none" stroke={C.border} strokeWidth={sw} strokeLinecap="round" />
        {fgPath && <path d={fgPath} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" />}
        <text x={cx} y={cy + 4} textAnchor="middle" fill={color}
          fontSize={size * 0.24} fontWeight={800} fontFamily="monospace"
          style={{ fontVariantNumeric: 'tabular-nums' }}>
          {Math.round(value)}
        </text>
      </svg>
      <div style={{ fontSize: 7.5, color: C.muted, letterSpacing: '.1em', fontWeight: 700, textTransform: 'uppercase' as const, marginTop: 2, lineHeight: 1.3 }}>{label}</div>
    </div>
  )
}

function DivergingGauge({ value, label, size = 72 }: { value: number | null | undefined; label: string; size?: number }) {
  if (value == null) return <ArcGauge value={null} label={label} size={size} />
  // Map -200..+200 → 0..100 for gauge display, show real value as text
  const mapped = Math.min(100, Math.max(0, (value + 200) / 4))
  const color = sentColor(value)
  const displayStr = `${value >= 0 ? '+' : ''}${Math.round(value)}`
  const cx = size / 2
  const cy = Math.round(size * 0.58)
  const r  = Math.round(size * 0.40)
  const sw = size * 0.09
  const sweepDeg = (mapped / 100) * 270
  const fgPath = sweepDeg > 0.5 ? svgArcPath(cx, cy, r, 135, sweepDeg) : null
  const h = Math.round(size * 0.72)
  // center tick at 50% (= 0 point)
  const zeroAngle = (135 + 135) * Math.PI / 180  // 270° = top
  const zx = cx + r * Math.cos(zeroAngle), zy = cy + r * Math.sin(zeroAngle)
  return (
    <div style={{ textAlign: 'center', pageBreakInside: 'avoid', breakInside: 'avoid', minWidth: size }}>
      <svg width={size} height={h} viewBox={`0 0 ${size} ${h}`}>
        <path d={svgArcPath(cx, cy, r, 135, 270)} fill="none" stroke={C.border} strokeWidth={sw} strokeLinecap="round" />
        {fgPath && <path d={fgPath} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" />}
        <circle cx={zx} cy={zy} r={sw * 0.5} fill={C.dim} />
        <text x={cx} y={cy + 4} textAnchor="middle" fill={color}
          fontSize={size * 0.22} fontWeight={800} fontFamily="monospace"
          style={{ fontVariantNumeric: 'tabular-nums' }}>
          {displayStr}
        </text>
      </svg>
      <div style={{ fontSize: 7.5, color: C.muted, letterSpacing: '.1em', fontWeight: 700, textTransform: 'uppercase' as const, marginTop: 2, lineHeight: 1.3 }}>{label}</div>
    </div>
  )
}

function ScoreBar({ value, max = 100, color }: { value: number; max?: number; color?: string }) {
  const fill = Math.min(100, Math.max(0, value / max * 100))
  const c = color ?? scoreColor(value / max * 100)
  return (
    <div style={{ height: 3, background: C.border, borderRadius: 2, marginTop: 3 }}>
      <div style={{ width: `${fill}%`, height: '100%', background: c, borderRadius: 2 }} />
    </div>
  )
}

function Sparkline({ bars, width = 360, height = 52 }: { bars: Bar[] | undefined; width?: number; height?: number }) {
  if (!bars || bars.length < 2) return (
    <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <span style={{ fontSize: 10, color: C.dim }}>No price data</span>
    </div>
  )
  const data = bars.slice(-120)
  const closes = data.map(b => b.close)
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const range = max - min || 1
  const pad = 4
  const pts = closes.map((c, i) => {
    const x = pad + (i / (closes.length - 1)) * (width - 2 * pad)
    const y = height - pad - ((c - min) / range) * (height - 2 * pad)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
  const isUp = closes[closes.length - 1] >= closes[0]
  const color = isUp ? C.green : C.red
  const fillPts = `${pad},${height - pad} ${pts} ${width - pad},${height - pad}`
  const lastX = (width - pad)
  const lastY = height - pad - ((closes[closes.length - 1] - min) / range) * (height - 2 * pad)
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
      <defs>
        <linearGradient id="spkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.28} />
          <stop offset="100%" stopColor={color} stopOpacity={0.02} />
        </linearGradient>
      </defs>
      <polygon points={fillPts} fill="url(#spkGrad)" />
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} />
      <circle cx={lastX} cy={lastY} r={3.5} fill={color} />
    </svg>
  )
}

function ZodiacWheel({ planets, lagna, size = 190 }: {
  planets: Record<string, KPlanet> | undefined
  lagna: KundliData['lagna'] | undefined
  size?: number
}) {
  const cx = size / 2, cy = size / 2
  const outerR = size * 0.46
  const ringW  = size * 0.14
  const innerR = outerR - ringW
  const dotR   = size * 0.048

  const signIdx = (sign: string) => {
    if (!sign) return -1
    const s = sign.toLowerCase()
    let idx = ZODIAC_FULL.findIndex(z => z.toLowerCase() === s)
    if (idx < 0) idx = ZODIAC_ABBR.findIndex(z => s.startsWith(z.toLowerCase()))
    return idx
  }

  const toAngle = (totalDeg: number) => (totalDeg - 90) * Math.PI / 180

  if (!planets || !lagna) {
    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cy} r={outerR} fill={C.surf2} stroke={C.border} />
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle" fill={C.muted} fontSize={11}>No data</text>
      </svg>
    )
  }

  const lagnaIdx = signIdx(lagna.sign)
  const lagnaTotal = lagnaIdx >= 0 ? lagnaIdx * 30 + lagna.degree : 0

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: 'block' }}>
      {/* Outer zodiac ring */}
      <circle cx={cx} cy={cy} r={outerR} fill={C.surf2} stroke={C.border} strokeWidth={1} />
      {/* Inner chart area */}
      <circle cx={cx} cy={cy} r={innerR} fill={C.surf} stroke={C.border} strokeWidth={1} />

      {/* 12 zodiac sign segments */}
      {ZODIAC_ABBR.map((abbr, i) => {
        const startAng = (i * 30 - 90) * Math.PI / 180
        const endAng   = ((i + 1) * 30 - 90) * Math.PI / 180
        const midAng   = ((i * 30 + 15) - 90) * Math.PI / 180
        const x1 = cx + outerR * Math.cos(startAng), y1 = cy + outerR * Math.sin(startAng)
        const x2 = cx + innerR * Math.cos(startAng), y2 = cy + innerR * Math.sin(startAng)
        const midR2 = (outerR + innerR) / 2
        const lx = cx + midR2 * Math.cos(midAng), ly = cy + midR2 * Math.sin(midAng)
        return (
          <g key={abbr}>
            <line x1={x2} y1={y2} x2={x1} y2={y1} stroke={C.border} strokeWidth={0.5} />
            <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
              fill={C.dim} fontSize={size * 0.046} fontWeight={600}
              transform={`rotate(${i * 30 + 15}, ${lx}, ${ly})`}
            >{abbr}</text>
          </g>
        )
      })}

      {/* Lagna marker */}
      {(() => {
        const ang = toAngle(lagnaTotal)
        const ix = cx + innerR * Math.cos(ang), iy = cy + innerR * Math.sin(ang)
        const ox = cx + outerR * Math.cos(ang), oy = cy + outerR * Math.sin(ang)
        return (
          <g>
            <line x1={ix} y1={iy} x2={ox} y2={oy} stroke={C.gold} strokeWidth={2} />
            <circle cx={ix} cy={iy} r={3.5} fill={C.gold} />
          </g>
        )
      })()}

      {/* Planets — placed at their degree within the inner circle */}
      {PLANET_ORDER.map((name, idx) => {
        const p = planets[name]
        if (!p) return null
        const si = signIdx(p.sign)
        if (si < 0) return null
        const totalDeg = si * 30 + p.degree
        const ang = toAngle(totalDeg)
        // Stagger planet radii slightly to reduce overlap
        const pr = innerR * (0.72 - (idx % 3) * 0.18)
        const px = cx + pr * Math.cos(ang)
        const py = cy + pr * Math.sin(ang)
        const color = DIGNITY_COLOR[p.dignity] ?? C.muted
        return (
          <g key={name}>
            <circle cx={px} cy={py} r={dotR} fill={color + '28'} stroke={color} strokeWidth={1} />
            <text x={px} y={py} textAnchor="middle" dominantBaseline="middle"
              fill={color} fontSize={size * 0.05} fontWeight={800} fontFamily="monospace">
              {PLANET_ABBR[name] ?? name.slice(0, 2).toUpperCase()}
            </text>
          </g>
        )
      })}

      {/* Center */}
      <text x={cx} y={cy - 4} textAnchor="middle" fill={C.sub} fontSize={size * 0.07} fontWeight={800}>
        {lagna.sign.slice(0, 3).toUpperCase()}
      </text>
      <text x={cx} y={cy + 9} textAnchor="middle" fill={C.muted} fontSize={size * 0.046}>
        {lagna.degree.toFixed(1)}&deg;
      </text>
    </svg>
  )
}

// ── Print CSS ─────────────────────────────────────────────────────────────────

const PRINT_CSS = `
@page { size: A4 portrait; margin: 10mm 12mm; }
*, *::before, *::after {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  color-adjust: exact !important;
  box-sizing: border-box;
}
html, body {
  margin: 0; padding: 0;
  background: #07101F;
  color: #D2E3F4;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 11px;
  -webkit-font-smoothing: antialiased;
}
.no-print { display: none !important; }
.pb { page-break-before: always !important; break-before: page !important; }
.pb-avoid { page-break-inside: avoid !important; break-inside: avoid !important; }
table { border-collapse: collapse; width: 100%; }
a { color: inherit; text-decoration: none; }
@media screen { body { padding: 12px; max-width: 900px; margin: 0 auto; } }
`

// ── handlePrint ───────────────────────────────────────────────────────────────

function openPrintWindow(symbol: string) {
  const el = document.getElementById('report-printable')
  if (!el) { window.print(); return }
  const win = window.open('', '_blank', 'width=900,height=1200')
  if (!win) { window.print(); return }
  win.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${symbol} — Stock Intelligence Report</title>
<style>${PRINT_CSS}</style>
</head>
<body>${el.innerHTML}</body>
</html>`)
  win.document.close()
  setTimeout(() => { win.focus(); win.print() }, 600)
}

// ── Main component ────────────────────────────────────────────────────────────

export function ReportPage() {
  const { symbol: urlSym } = useParams<{ symbol?: string }>()
  const symbol = (urlSym ?? '').toUpperCase()

  const { data: detail, isLoading: dLoading } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockDetail(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })
  const { data: ohlcvData } = useQuery({
    queryKey: ['ohlcv', symbol],
    queryFn: () => fetchOhlcv(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })
  const { data: corpActData } = useQuery({
    queryKey: ['ca', symbol, 12],
    queryFn: () => fetchStockCorpActions(symbol, 12),
    enabled: !!symbol,
    staleTime: 10 * 60_000,
  })
  const { data: annData } = useQuery({
    queryKey: ['ann', symbol, 10],
    queryFn: () => fetchStockAnnouncements(symbol, 10),
    enabled: !!symbol,
    staleTime: 10 * 60_000,
  })
  const { data: kundliData, isLoading: kLoading } = useQuery({
    queryKey: ['kundli', symbol],
    queryFn: () => fetchKundli(symbol),
    enabled: !!symbol,
    staleTime: 60 * 60_000,
  })

  const isLoading = dLoading || kLoading

  // Convenience accessors
  const d   = (detail?.detail ?? {}) as Record<string, unknown>
  const ast = (d.astro ?? {}) as Record<string, unknown>
  const fun = (d.fundamentals ?? {}) as Record<string, unknown>
  const tec = (d.technical ?? {}) as Record<string, unknown>
  const fno = (d.fno ?? {}) as Record<string, unknown>
  const mgt = (d.management ?? {}) as Record<string, unknown>
  const ht  = (d.holding_trends ?? {}) as Record<string, unknown>
  const ml  = (d.ml_scores ?? {}) as Record<string, unknown>
  const br  = (d.bull_run ?? {}) as Record<string, unknown>
  const pm  = (d.price_momentum ?? {}) as Record<string, unknown>
  const tc  = (d.trade_conviction ?? {}) as Record<string, unknown>
  const kev = (d.upcoming_events ?? []) as unknown[]
  const kl  = (d.key_levels ?? {}) as Record<string, unknown>
  const cc  = (d.concall ?? {}) as Record<string, unknown>
  const thesis = (d.structured_thesis ?? {}) as Record<string, unknown>
  const consensus = (d.consensus ?? {}) as Record<string, unknown>

  const bars    = ohlcvData?.bars ?? []
  const kundli  = kundliData?.kundli
  const gann    = kundliData?.gann
  const interp  = kundliData?.interpretation
  const ca      = (corpActData?.actions ?? []) as CorpAction[]
  const anns    = ((annData as { announcements?: Announcement[] })?.announcements ?? []) as Announcement[]

  // Price info
  const lastBar = bars.length > 0 ? bars[bars.length - 1] : null
  const prevBar = bars.length > 1 ? bars[bars.length - 2] : null
  const price   = lastBar?.close ?? (detail?.close_price ?? 0)
  const chg     = prevBar ? price - prevBar.close : 0
  const chgPct  = prevBar ? (chg / prevBar.close) * 100 : 0

  // ── Toolbar ────────────────────────────────────────────────────────────────
  return (
    <div style={{ background: C.bg, minHeight: '100%' }}>
      {/* Sticky toolbar — excluded from print */}
      <div className="no-print" style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: '#0A1220', borderBottom: `1px solid ${C.border}`,
        padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <Link to={symbol ? `/stocks/${symbol}` : '/stocks'}
          style={{ color: C.muted, fontSize: 11, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
          &larr; Back to {symbol || 'Stocks'}
        </Link>
        <div style={{ flex: 1 }} />
        {isLoading && <span style={{ fontSize: 11, color: C.muted }}>Loading data...</span>}
        {kLoading && <span style={{ fontSize: 11, color: C.purple }}>Loading Kundli...</span>}
        <button
          onClick={() => openPrintWindow(symbol)}
          disabled={isLoading}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 16px', borderRadius: 5, border: `1px solid ${C.accent}44`,
            background: C.accent + '18', color: C.accent, cursor: 'pointer', fontSize: 12, fontWeight: 600,
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>
          </svg>
          Print / Download PDF
        </button>
        <button
          onClick={() => openPrintWindow(symbol)}
          disabled={isLoading}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 16px', borderRadius: 5, border: `1px solid ${C.green}44`,
            background: C.green + '18', color: C.green, cursor: 'pointer', fontSize: 12, fontWeight: 600,
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
          </svg>
          Download PDF
        </button>
      </div>

      {/* ── Printable content ──────────────────────────────────────────────── */}
      <div id="report-printable" style={{ maxWidth: 900, margin: '0 auto', padding: '20px 16px 0' }}>

        {/* ══ MASTHEAD ═══════════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{
          background: C.surf, border: `1px solid ${C.border}`,
          borderRadius: 8, padding: '20px 24px 18px', marginBottom: 16,
          borderTop: `3px solid ${C.accent}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
            <div style={{ flex: 1 }}>
              {/* Platform label */}
              <div style={{ fontSize: 8, color: C.dim, fontWeight: 800, letterSpacing: '.2em', textTransform: 'uppercase', marginBottom: 6 }}>
                CAPITAL FLOW INTELLIGENCE PLATFORM
              </div>
              {/* Symbol */}
              <div style={{ fontSize: 36, fontWeight: 900, color: C.text, fontFamily: 'monospace', letterSpacing: '.04em', lineHeight: 1 }}>
                {symbol || '--'}
              </div>
              {/* Company name */}
              <div style={{ fontSize: 13, color: C.sub, marginTop: 4, fontWeight: 500 }}>
                {String(detail?.company_name ?? detail?.symbol_name ?? symbol ?? '')}
              </div>
              {/* Price row */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 10 }}>
                <span style={{ fontSize: 26, fontWeight: 800, color: C.text, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>
                  &#8377;{price > 0 ? price.toFixed(2) : '--'}
                </span>
                {chg !== 0 && (
                  <span style={{ fontSize: 14, fontWeight: 700, color: chg >= 0 ? C.green : C.red, fontFamily: 'monospace' }}>
                    {chg >= 0 ? '+' : ''}{chg.toFixed(2)} ({fmt.pct(chgPct)})
                  </span>
                )}
              </div>
              {/* Tags row */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                {detail?.sector && <Chip label={String(detail.sector)} color={C.accent} />}
                {!!br?.label && <Chip label={String(br.label)} color={scoreColor(Number(br?.probability_score ?? 50))} />}
                {!!(ast?.astro_action ?? ast?.signal) && (
                  <Chip label={String(ast?.astro_action ?? ast?.signal ?? '')} color={SIGNAL_COLOR[String(ast?.astro_action ?? ast?.signal ?? '')] ?? C.sub} />
                )}
                {!!tec?.trend_signal && <Chip label={String(tec.trend_signal)} color={C.teal} />}
                {!!fno?.oi_signal && <Chip label={`F&O: ${String(fno.oi_signal)}`} color={C.purple} />}
              </div>
            </div>
            {/* Date stamp */}
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: 8, color: C.dim, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 4 }}>Report Generated</div>
              <div style={{ fontSize: 11, color: C.muted, fontFamily: 'monospace' }}>
                {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
              </div>
              <div style={{ fontSize: 8, color: C.dim, marginTop: 8, letterSpacing: '.1em' }}>NSE EQUITIES</div>
              <div style={{ fontSize: 9, color: C.muted, marginTop: 2 }}>
                {lastBar ? `Data: ${fmt.date(String(lastBar.time))}` : ''}
              </div>
            </div>
          </div>

          {/* Sparkline */}
          {bars.length > 1 && (
            <div style={{ marginTop: 14, borderTop: `1px solid ${C.border}`, paddingTop: 12 }}>
              <Sparkline bars={bars} width={840} height={52} />
            </div>
          )}
        </div>

        {/* ══ SCORE GAUGES ═══════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom: 16 }}>
          <SH label="Intelligence Scores" />
          <div style={{
            background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8,
            padding: '16px 12px',
            display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: 8,
          }}>
            <ArcGauge value={Number(tc?.conviction_score ?? null) || null} label="Conviction" size={88} />
            <ArcGauge value={Number(ml?.bull_run_score ?? null) || null} label="ML Bull Run" size={88} />
            <ArcGauge value={Number(ml?.accumulation_score ?? null) || null} label="ML Accumul." size={88} />
            <ArcGauge value={Number(br?.probability_score ?? null) || null} label="Bull Run Prob" size={88} />
            <ArcGauge value={Number(pm?.price_score ?? null) || null} label="Price Momentum" size={88} />
            <ArcGauge
              value={Number(detail?.smart_money_score ?? (d?.participant_flow as Record<string,unknown>)?.smart_money_score ?? null) || null}
              label="Smart Money" size={88}
            />
            <ArcGauge value={Number(tec?.technical_score ?? null) || null} label="Technical" size={88} />
            <DivergingGauge value={kundli?.astro_score ?? Number(ast?.astro_score ?? null) || null} label="Vedic Astro" size={88} />
          </div>
        </div>

        {/* ══ INVESTMENT THESIS ══════════════════════════════════════════════ */}
        {(thesis?.verdict || thesis?.bull_signals || tc?.action) && (
          <div className="pb-avoid" style={{ marginBottom: 16 }}>
            <SH label="Investment Thesis" accent={C.gold} />
            <div style={{
              background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: '16px 18px',
              borderLeft: `4px solid ${scoreColor(Number(tc?.conviction_score ?? 50))}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
                {tc?.action && (
                  <span style={{
                    fontSize: 16, fontWeight: 900, letterSpacing: '.06em',
                    color: SIGNAL_COLOR[String(tc?.action)] ?? C.green,
                  }}>{String(tc?.action)}</span>
                )}
                {tc?.conviction_score != null && (
                  <span style={{ fontSize: 12, color: C.muted }}>
                    Score <strong style={{ color: scoreColor(Number(tc?.conviction_score)), fontFamily: 'monospace' }}>
                      {Number(tc?.conviction_score).toFixed(1)}
                    </strong> / 100
                  </span>
                )}
                {consensus?.analyst_rating && (
                  <Chip label={`Consensus: ${String(consensus?.analyst_rating)}`} color={C.teal} />
                )}
              </div>

              {/* Bull signals */}
              {Array.isArray(thesis?.bull_signals) && (thesis?.bull_signals as string[]).length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  {(thesis?.bull_signals as string[]).slice(0, 5).map((s, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'flex-start' }}>
                      <span style={{ color: C.green, fontWeight: 900, flexShrink: 0, marginTop: 1 }}>+</span>
                      <span style={{ fontSize: 11, color: C.sub, lineHeight: 1.5 }}>{s}</span>
                    </div>
                  ))}
                </div>
              )}
              {/* Bear signals */}
              {Array.isArray(thesis?.bear_signals) && (thesis?.bear_signals as string[]).length > 0 && (
                <div>
                  {(thesis?.bear_signals as string[]).slice(0, 3).map((s, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'flex-start' }}>
                      <span style={{ color: C.red, fontWeight: 900, flexShrink: 0, marginTop: 1 }}>-</span>
                      <span style={{ fontSize: 11, color: C.sub, lineHeight: 1.5 }}>{s}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* ML insight */}
              {ml?.bull_run_score != null && (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: `1px solid ${C.border}`, fontSize: 10, color: C.muted }}>
                  ML Models: Bull Run {Number(ml?.bull_run_score).toFixed(1)} | Accumulation {Number(ml?.accumulation_score ?? 0).toFixed(1)} | Combined {Number(ml?.combined_score ?? 0).toFixed(1)}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ══ PRICE HISTORY TABLE ════════════════════════════════════════════ */}
        {bars.length > 0 && (
          <div className="pb" style={{ marginBottom: 16 }}>
            <SH label="Price History  (Last 30 Sessions)" />
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
              <table>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Chg%'].map(h => (
                      <th key={h} style={{ padding: '7px 10px', textAlign: h === 'Date' ? 'left' : 'right', fontSize: 9, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bars.slice(-30).reverse().map((b, i) => {
                    const prev = bars[bars.length - 30 + (30 - 1 - i) - 1]
                    const chgP = prev ? (b.close - prev.close) / prev.close * 100 : 0
                    const up = b.close >= b.open
                    return (
                      <tr key={i} style={{ background: i % 2 === 0 ? C.surf : C.surf2, borderBottom: `1px solid ${C.border}22` }}>
                        <td style={{ padding: '5px 10px', fontSize: 10, color: C.sub, fontFamily: 'monospace' }}>{fmt.date(String(b.time))}</td>
                        <td style={{ padding: '5px 10px', fontSize: 10, color: C.muted, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{b.open.toFixed(2)}</td>
                        <td style={{ padding: '5px 10px', fontSize: 10, color: C.green, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{b.high.toFixed(2)}</td>
                        <td style={{ padding: '5px 10px', fontSize: 10, color: C.red, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{b.low.toFixed(2)}</td>
                        <td style={{ padding: '5px 10px', fontSize: 11, color: up ? C.green : C.red, textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{b.close.toFixed(2)}</td>
                        <td style={{ padding: '5px 10px', fontSize: 9, color: C.muted, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{b.volume > 0 ? (b.volume >= 1e6 ? `${(b.volume / 1e6).toFixed(2)}M` : (b.volume >= 1e3 ? `${(b.volume / 1e3).toFixed(0)}K` : String(b.volume))) : '--'}</td>
                        <td style={{ padding: '5px 10px', fontSize: 10, color: chgP >= 0 ? C.green : C.red, textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{fmt.pct(chgP)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ══ TECHNICAL ANALYSIS ═════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom: 16 }}>
          <SH label="Technical Analysis" accent={C.teal} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {/* Moving averages */}
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 9, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 10 }}>Moving Averages</div>
              {[
                { label: '20 DMA', val: tec?.dma_20 },
                { label: '50 DMA', val: tec?.dma_50 },
                { label: '200 DMA', val: tec?.dma_200 },
              ].map(({ label, val }) => {
                if (!val) return null
                const v = Number(val)
                const diff = price > 0 ? (price - v) / v * 100 : 0
                return (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 10, color: C.muted, minWidth: 52 }}>{label}</span>
                    <span style={{ fontSize: 10, color: C.sub, minWidth: 64, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>&#8377;{v.toFixed(0)}</span>
                    <span style={{ fontSize: 10, fontWeight: 700, color: diff >= 0 ? C.green : C.red, minWidth: 52, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>
                      {diff >= 0 ? '+' : ''}{diff.toFixed(1)}%
                    </span>
                    <ScoreBar value={Math.min(20, Math.abs(diff))} max={20} color={diff >= 0 ? C.green : C.red} />
                  </div>
                )
              })}
              {tec?.trend_signal && (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: `1px solid ${C.border}` }}>
                  <span style={{ fontSize: 9, color: C.muted }}>Trend: </span>
                  <Chip label={String(tec?.trend_signal)} color={C.teal} />
                </div>
              )}
            </div>

            {/* Key levels + indicators */}
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 9, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 10 }}>52-Week Range & Levels</div>
              {[
                { label: '52W High', val: tec?.week_52_high ?? tec?.high_52w, color: C.red },
                { label: '52W Low',  val: tec?.week_52_low  ?? tec?.low_52w,  color: C.green },
                { label: 'Supp. 1',  val: kl?.support_1,  color: C.green },
                { label: 'Supp. 2',  val: kl?.support_2,  color: C.green },
                { label: 'Resist. 1', val: kl?.resistance_1, color: C.red },
                { label: 'Resist. 2', val: kl?.resistance_2, color: C.red },
              ].filter(r => r.val != null).map(({ label, val, color }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, alignItems: 'center' }}>
                  <span style={{ fontSize: 10, color: C.muted }}>{label}</span>
                  <span style={{ fontSize: 11, fontWeight: 700, color, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>&#8377;{Number(val).toFixed(2)}</span>
                </div>
              ))}
              {fno?.oi_signal && (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: `1px solid ${C.border}` }}>
                  <span style={{ fontSize: 9, color: C.muted }}>F&O Signal: </span>
                  <Chip label={String(fno?.oi_signal)} color={C.purple} />
                  {fno?.futures_oi && <span style={{ fontSize: 9, color: C.muted, marginLeft: 8 }}>OI: {fmt.cr(Number(fno?.futures_oi))}</span>}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ══ FUNDAMENTALS ═══════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom: 16 }}>
          <SH label="Company Fundamentals" accent={C.gold} />
          <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Market Cap',      val: fmt.cr(Number(fun?.market_cap_cr ?? detail?.market_cap_cr)),         color: C.text },
                { label: 'P/E Ratio',       val: fmt.num(Number(fun?.pe_ratio ?? fun?.pe)),                            color: C.sub },
                { label: 'P/B Ratio',       val: fmt.num(Number(fun?.pb_ratio ?? fun?.pb)),                            color: C.sub },
                { label: 'EPS',             val: fmt.rs(Number(fun?.eps), 2),                                          color: C.gold },
                { label: 'Book Value/Sh',   val: fmt.rs(Number(fun?.book_value_per_share ?? fun?.book_value), 2),      color: C.sub },
                { label: 'Revenue',         val: fmt.cr(Number(fun?.revenue_cr ?? fun?.revenue_ttm)),                  color: C.text },
                { label: 'Net Profit',      val: fmt.cr(Number(fun?.net_profit_cr ?? fun?.profit_ttm)),                color: Number(fun?.net_profit_cr ?? fun?.profit_ttm ?? 0) >= 0 ? C.green : C.red },
                { label: 'ROE %',           val: fmt.num(Number(fun?.roe_pct ?? fun?.roe)),                            color: Number(fun?.roe_pct ?? fun?.roe ?? 0) >= 15 ? C.green : C.gold },
                { label: 'ROCE %',          val: fmt.num(Number(fun?.roce_pct ?? fun?.roce)),                          color: Number(fun?.roce_pct ?? fun?.roce ?? 0) >= 12 ? C.green : C.gold },
                { label: 'OPM %',           val: fmt.num(Number(fun?.opm_pct ?? fun?.ebitda_margin)),                 color: C.sub },
                { label: 'D/E Ratio',       val: fmt.num(Number(fun?.debt_equity ?? fun?.de_ratio)),                  color: Number(fun?.debt_equity ?? fun?.de_ratio ?? 0) < 1 ? C.green : C.red },
                { label: 'Sales Growth',    val: fmt.pct(Number(fun?.sales_growth_cagr ?? fun?.revenue_growth)),       color: Number(fun?.sales_growth_cagr ?? 0) >= 10 ? C.green : C.gold },
                { label: 'Face Value',      val: fmt.rs(Number(fun?.face_value ?? detail?.face_value), 2),            color: C.muted },
                { label: 'Div. Yield %',    val: fmt.num(Number(fun?.dividend_yield_pct ?? fun?.dividend_yield)),      color: C.gold },
                { label: 'Val. Label',      val: String(fun?.valuation_label ?? '--'),                                 color: C.teal },
                { label: 'Sector P/E',      val: fmt.num(Number((d?.sector_peer_valuation as Record<string,unknown>)?.sector_pe)), color: C.muted },
              ].map(({ label, val, color }) => (
                <div key={label} className="pb-avoid" style={{ pageBreakInside: 'avoid', breakInside: 'avoid' }}>
                  <div style={{ fontSize: 8, color: C.muted, letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 3 }}>{label}</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums', lineHeight: 1.2 }}>{val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ══ INSTITUTIONAL INTELLIGENCE ═════════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom: 16 }}>
          <SH label="Institutional Intelligence" accent={C.purple} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {/* Shareholding trends */}
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 9, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 10 }}>Shareholding Pattern</div>
              {[
                { label: 'Promoter %',  val: ht?.promoter_pct ?? fun?.promoter_holding,   delta: ht?.promoter_delta_qoq },
                { label: 'FII %',       val: ht?.fii_pct      ?? fun?.fii_holding,         delta: ht?.fii_delta_qoq },
                { label: 'DII %',       val: ht?.dii_pct      ?? fun?.dii_holding,         delta: ht?.dii_delta_qoq },
                { label: 'Public %',    val: ht?.public_pct   ?? fun?.public_holding,      delta: null },
              ].map(({ label, val, delta }) => (
                val != null ? (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 10, color: C.muted, minWidth: 72 }}>{label}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: C.text, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums', minWidth: 52 }}>
                      {Number(val).toFixed(2)}%
                    </span>
                    {delta != null && Number(delta) !== 0 && (
                      <span style={{ fontSize: 10, fontWeight: 700, color: Number(delta) > 0 ? C.green : C.red, fontFamily: 'monospace' }}>
                        {Number(delta) > 0 ? '+' : ''}{Number(delta).toFixed(2)}%
                      </span>
                    )}
                    <div style={{ flex: 1, height: 3, background: C.border, borderRadius: 2 }}>
                      <div style={{ width: `${Math.min(100, Number(val))}%`, height: '100%', background: label === 'FII %' ? C.accent : label === 'Promoter %' ? C.gold : label === 'DII %' ? C.teal : C.dim, borderRadius: 2 }} />
                    </div>
                  </div>
                ) : null
              ))}
            </div>

            {/* Management sentiment + governance */}
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 9, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 10 }}>Management & Governance</div>
              {[
                { label: 'Mgmt Sentiment',  val: mgt?.sentiment_label ?? mgt?.tone_label },
                { label: 'Mgmt Score',      val: mgt?.sentiment_score != null ? Number(mgt?.sentiment_score).toFixed(1) : null },
                { label: 'Promoter Pledge', val: mgt?.promoter_pledge_pct != null ? `${Number(mgt?.promoter_pledge_pct).toFixed(1)}%` : null },
                { label: 'Concall Tone',    val: cc?.tone_label ?? cc?.sentiment },
                { label: 'Analyst Target',  val: consensus?.target_price != null ? fmt.rs(Number(consensus?.target_price)) : null },
                { label: 'Upside',          val: consensus?.upside_pct != null ? fmt.pct(Number(consensus?.upside_pct)) : null },
              ].filter(r => r.val != null).map(({ label, val }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'center' }}>
                  <span style={{ fontSize: 10, color: C.muted }}>{label}</span>
                  <span style={{ fontSize: 11, fontWeight: 700, color: C.sub, fontFamily: 'monospace' }}>{String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ══ UPCOMING EVENTS ════════════════════════════════════════════════ */}
        {kev.length > 0 && (
          <div className="pb-avoid" style={{ marginBottom: 16 }}>
            <SH label="Upcoming Catalysts & Events" accent={C.teal} />
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {(kev as Record<string, unknown>[]).slice(0, 8).map((ev, i) => (
                  <div key={i} className="pb-avoid" style={{
                    background: C.surf2, border: `1px solid ${C.border}`, borderRadius: 6,
                    padding: '8px 12px', pageBreakInside: 'avoid', breakInside: 'avoid',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, color: C.text }}>{String(ev?.event_type ?? ev?.type ?? '')}</span>
                      <span style={{ fontSize: 9, color: C.muted, fontFamily: 'monospace' }}>{fmt.date(String(ev?.event_date ?? ev?.date ?? ''))}</span>
                    </div>
                    {ev?.catalyst_score != null && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 9, color: C.muted }}>Catalyst Score:</span>
                        <span style={{ fontSize: 10, fontWeight: 700, color: scoreColor(Number(ev?.catalyst_score)), fontFamily: 'monospace' }}>{Number(ev?.catalyst_score).toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ══ ASTRO SIGNAL ═══════════════════════════════════════════════════ */}
        {Object.keys(ast).length > 0 && (
          <div className="pb-avoid" style={{ marginBottom: 16 }}>
            <SH label="Daily Astro Signal  (Sector Planetary Intelligence)" accent={C.purple} />
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: '14px 18px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 14 }}>
                {[
                  { label: 'Ruling Planet',     val: ast?.ruling_planet ?? ast?.planet,      color: C.gold },
                  { label: 'Astro Signal',      val: ast?.signal ?? ast?.astro_signal,        color: SIGNAL_COLOR[String(ast?.signal ?? '')] ?? C.sub },
                  { label: 'Score',             val: ast?.astro_score != null ? `${Number(ast?.astro_score) >= 0 ? '+' : ''}${Number(ast?.astro_score).toFixed(0)}` : '--', color: sentColor(Number(ast?.astro_score ?? 0)) },
                  { label: 'Moon Sign',         val: ast?.moon_sign ?? ast?.current_moon,    color: C.accent },
                  { label: 'Moon Phase',        val: ast?.moon_phase,                         color: C.sub },
                  { label: 'Nakshatra',         val: ast?.nakshatra ?? ast?.moon_nakshatra,   color: C.muted },
                  { label: 'Jupiter Transit',   val: ast?.jupiter_transit ?? ast?.jupiter_sign, color: C.teal },
                  { label: 'Saturn Transit',    val: ast?.saturn_transit ?? ast?.saturn_sign, color: C.muted },
                  { label: 'Sector Context',    val: ast?.sector_context ?? ast?.context,    color: C.sub },
                ].filter(r => r.val).map(({ label, val, color }) => (
                  <div key={label} className="pb-avoid">
                    <div style={{ fontSize: 8, color: C.dim, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 3 }}>{label}</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color, fontFamily: 'monospace' }}>{String(val ?? '--')}</div>
                  </div>
                ))}
              </div>
              {ast?.bull_signals && Array.isArray(ast?.bull_signals) && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <div style={{ fontSize: 8, color: C.green, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 6 }}>Bullish Planetary Factors</div>
                    {(ast?.bull_signals as string[]).map((s, i) => (
                      <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 4 }}>
                        <span style={{ color: C.green, fontWeight: 900, flexShrink: 0 }}>+</span>
                        <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.5 }}>{s}</span>
                      </div>
                    ))}
                  </div>
                  {Array.isArray(ast?.bear_signals) && (ast?.bear_signals as string[]).length > 0 && (
                    <div>
                      <div style={{ fontSize: 8, color: C.red, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 6 }}>Bearish Planetary Factors</div>
                      {(ast?.bear_signals as string[]).map((s, i) => (
                        <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 4 }}>
                          <span style={{ color: C.red, fontWeight: 900, flexShrink: 0 }}>-</span>
                          <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.5 }}>{s}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════ */}
        {/* VEDIC KUNDLI — ALL SECTIONS INLINE                               */}
        {/* ══════════════════════════════════════════════════════════════════ */}
        {kundli && (
          <div>
            {/* ── Kundli: Overview ───────────────────────────────────────── */}
            <div className="pb" style={{ marginBottom: 16 }}>
              <SH label="Vedic Kundli  — Natal Chart Overview" accent={C.purple} />
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 16, alignItems: 'start' }}>
                {/* Zodiac wheel */}
                <div className="pb-avoid" style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 12 }}>
                  <ZodiacWheel planets={kundli.planets} lagna={kundli.lagna} size={190} />
                  <div style={{ textAlign: 'center', marginTop: 8 }}>
                    <div style={{ fontSize: 8, color: C.dim, letterSpacing: '.12em', textTransform: 'uppercase' }}>Natal Planetary Chart</div>
                    <div style={{ fontSize: 9, color: C.muted, marginTop: 3 }}>IPO: {fmt.date(kundli.entity?.inception_date)}</div>
                  </div>
                </div>

                {/* Overview details */}
                <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: '14px 16px' }}>
                  {/* Lagna */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 14 }}>
                    <div>
                      <div style={{ fontSize: 8, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 3 }}>Lagna (Ascendant)</div>
                      <div style={{ fontSize: 16, fontWeight: 800, color: C.gold, fontFamily: 'monospace' }}>{kundli.lagna.sign}</div>
                      <div style={{ fontSize: 10, color: C.muted }}>{kundli.lagna.degree.toFixed(1)}&deg; &middot; Lord: <span style={{ color: DASHA_COLOR[kundli.lagna.lord] ?? C.sub }}>{kundli.lagna.lord}</span></div>
                    </div>
                    <div>
                      <div style={{ fontSize: 8, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 3 }}>Astro Score</div>
                      <div style={{ fontSize: 20, fontWeight: 900, color: sentColor(kundli.astro_score), fontFamily: 'monospace' }}>
                        {kundli.astro_score >= 0 ? '+' : ''}{kundli.astro_score.toFixed(0)}
                      </div>
                      <div style={{ fontSize: 10, color: SIGNAL_COLOR[kundli.astro_action] ?? C.sub }}>{kundli.astro_action}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 8, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 3 }}>Entity</div>
                      <div style={{ fontSize: 12, fontWeight: 700, color: C.text }}>{kundli.entity?.name}</div>
                      <div style={{ fontSize: 10, color: C.muted }}>{kundli.entity?.inception_date} {kundli.entity?.inception_time}</div>
                    </div>
                  </div>

                  {/* Dasha */}
                  <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 12, marginBottom: 12 }}>
                    <div style={{ fontSize: 8, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 8 }}>Current Dasha Period</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                      {[
                        { label: 'Mahadasha', d: kundli.current_dasha?.mahadasha },
                        { label: 'Antardasha', d: kundli.current_dasha?.antardasha },
                        { label: 'Pratyantardasha', d: kundli.current_dasha?.pratyantardasha },
                      ].map(({ label, d }) => d && (
                        <div key={label} style={{ background: C.surf2, border: `1px solid ${C.border}`, borderRadius: 6, padding: '8px 10px' }}>
                          <div style={{ fontSize: 8, color: C.dim, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 4 }}>{label}</div>
                          <div style={{ fontSize: 14, fontWeight: 800, color: DASHA_COLOR[d.planet] ?? C.sub, fontFamily: 'monospace' }}>{d.planet}</div>
                          <div style={{ fontSize: 8.5, color: C.muted, marginTop: 2 }}>until {fmt.date(d.end_date)}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Yogas */}
                  {kundli.yogas?.length > 0 && (
                    <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>
                      <div style={{ fontSize: 8, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 6 }}>Active Yogas</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                        {kundli.yogas.map((y, i) => (
                          <span key={i} style={{
                            padding: '3px 9px', borderRadius: 10,
                            fontSize: 9, fontWeight: 700, letterSpacing: '.04em',
                            background: (YOGA_COLOR[y.signal] ?? C.muted) + '1A',
                            border: `1px solid ${(YOGA_COLOR[y.signal] ?? C.muted)}44`,
                            color: YOGA_COLOR[y.signal] ?? C.muted,
                          }}>{y.name}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ── Kundli: Planets Table ──────────────────────────────────── */}
            <div className="pb-avoid" style={{ marginBottom: 16 }}>
              <SH label="Planetary Positions  — All 9 Planets" accent={C.purple} />
              <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
                <table>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                      {['Planet', 'Sign', 'Deg', 'House', 'Nakshatra', 'Pada', 'Dignity', 'R'].map(h => (
                        <th key={h} style={{ padding: '7px 10px', textAlign: h === 'Planet' ? 'left' : 'right', fontSize: 8.5, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {PLANET_ORDER.filter(n => kundli.planets[n]).map((name, i) => {
                      const p = kundli.planets[name]
                      const dc = DIGNITY_COLOR[p.dignity] ?? C.muted
                      return (
                        <tr key={name} style={{ background: i % 2 === 0 ? C.surf : C.surf2, borderBottom: `1px solid ${C.border}22` }}>
                          <td style={{ padding: '7px 10px', fontWeight: 700, color: DASHA_COLOR[name] ?? C.text, fontSize: 11 }}>{name}</td>
                          <td style={{ padding: '7px 10px', color: C.sub, textAlign: 'right', fontSize: 10 }}>
                            {p.sign}
                          </td>
                          <td style={{ padding: '7px 10px', color: C.muted, textAlign: 'right', fontSize: 10, fontFamily: 'monospace' }}>{p.degree.toFixed(1)}&deg;</td>
                          <td style={{ padding: '7px 10px', color: C.sub, textAlign: 'right', fontSize: 10, fontFamily: 'monospace' }}>H{p.house}</td>
                          <td style={{ padding: '7px 10px', color: C.muted, textAlign: 'right', fontSize: 9.5 }}>{p.nakshatra}</td>
                          <td style={{ padding: '7px 10px', color: C.dim, textAlign: 'right', fontSize: 9 }}>{p.pada}</td>
                          <td style={{ padding: '7px 10px', textAlign: 'right' }}>
                            <span style={{ fontSize: 9, fontWeight: 700, color: dc }}>
                              {p.dignity.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td style={{ padding: '7px 10px', textAlign: 'right', fontSize: 9.5, color: p.retrograde ? C.orange : C.dim, fontWeight: p.retrograde ? 800 : 400 }}>
                            {p.retrograde ? 'R' : '-'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ── Kundli: Financial Houses ───────────────────────────────── */}
            {kundli.financial_houses && Object.keys(kundli.financial_houses).length > 0 && (
              <div className="pb-avoid" style={{ marginBottom: 16 }}>
                <SH label="Financial Houses Analysis" accent={C.purple} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  {(['2H', '5H', '8H', '10H', '11H'] as const).map(hk => {
                    const h = kundli.financial_houses[hk]
                    if (!h) return null
                    const sc = HOUSE_STRENGTH_COLOR[h.strength] ?? C.sub
                    const HOUSE_LABELS: Record<string, string> = {
                      '2H': '2nd House — Wealth / Balance Sheet',
                      '5H': '5th House — Speculation / R&D',
                      '8H': '8th House — Volatility / M&A Events',
                      '10H': '10th House — Management / Reputation',
                      '11H': '11th House — Revenue / Profits',
                    }
                    return (
                      <div key={hk} className="pb-avoid" style={{
                        background: C.surf, border: `1px solid ${C.border}`,
                        borderLeft: `3px solid ${sc}`,
                        borderRadius: 8, padding: '10px 14px',
                        pageBreakInside: 'avoid', breakInside: 'avoid',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <span style={{ fontSize: 10, fontWeight: 700, color: C.text }}>{HOUSE_LABELS[hk] ?? hk}</span>
                          <span style={{ fontSize: 8.5, fontWeight: 700, padding: '2px 8px', borderRadius: 8, background: sc + '1A', border: `1px solid ${sc}44`, color: sc }}>
                            {h.strength.replace(/-/g, ' ')}
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 4 }}>
                          <span style={{ fontSize: 9.5, color: C.muted }}>Sign: <span style={{ color: C.sub }}>{h.sign}</span></span>
                          <span style={{ fontSize: 9.5, color: C.muted }}>Lord: <span style={{ color: DIGNITY_COLOR[h.lord_dignity] ?? C.sub, fontWeight: 700 }}>{h.lord}</span>
                            {h.lord_house && <span style={{ color: C.dim }}> in H{h.lord_house}</span>}
                          </span>
                          {h.occupants.length > 0 && (
                            <span style={{ fontSize: 9.5, color: C.muted }}>Planets: <span style={{ color: C.accent }}>{h.occupants.join(', ')}</span></span>
                          )}
                        </div>
                        <div style={{ fontSize: 9.5, color: C.muted, lineHeight: 1.5 }}>{h.signification}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* ── Kundli: Dasha Sequence ─────────────────────────────────── */}
            {kundli.current_dasha?.all_mahadashas?.length > 0 && (
              <div className="pb-avoid" style={{ marginBottom: 16 }}>
                <SH label="Mahadasha Timeline  — Planetary Periods" accent={C.purple} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {/* Mahadasha table */}
                  <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
                    <table>
                      <thead>
                        <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                          {['Planet', 'Start', 'End', ''].map(h => (
                            <th key={h} style={{ padding: '6px 10px', textAlign: 'left', fontSize: 8.5, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {kundli.current_dasha.all_mahadashas.slice(0, 9).map((m, i) => {
                          const dc = DASHA_COLOR[m.planet] ?? C.muted
                          const nowYear = new Date().getFullYear()
                          const sYear = parseInt(m.start_date?.slice(0, 4) ?? '0')
                          const eYear = parseInt(m.end_date?.slice(0, 4) ?? '9999')
                          const active = sYear <= nowYear && nowYear <= eYear
                          return (
                            <tr key={i} style={{ background: active ? dc + '0C' : (i % 2 === 0 ? C.surf : C.surf2), borderBottom: `1px solid ${C.border}22` }}>
                              <td style={{ padding: '6px 10px', fontWeight: active ? 800 : 500, color: dc, fontSize: 11 }}>
                                {m.planet}{active ? ' *' : ''}
                              </td>
                              <td style={{ padding: '6px 10px', fontSize: 9.5, color: C.sub, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{m.start_date?.slice(0, 7)}</td>
                              <td style={{ padding: '6px 10px', fontSize: 9.5, color: C.sub, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>{m.end_date?.slice(0, 7)}</td>
                              <td style={{ padding: '6px 10px' }}>{active && <span style={{ fontSize: 8, color: dc, fontWeight: 800 }}>ACTIVE</span>}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Dasha outlook */}
                  <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
                    <div style={{ fontSize: 8.5, color: C.muted, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 10 }}>Dasha Outlook</div>
                    {interp?.dasha_outlook?.slice(0, 5).map((o, i) => (
                      <div key={i} style={{ marginBottom: 8, paddingBottom: 8, borderBottom: i < 4 ? `1px solid ${C.border}22` : 'none' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                          <span style={{ fontSize: 10, fontWeight: 700, color: C.text }}>{o.period}</span>
                          <span style={{ fontSize: 9, color: C.dim, fontFamily: 'monospace' }}>{o.start?.slice(0, 4)}-{o.end?.slice(0, 4)}</span>
                        </div>
                        {o.outlook && (
                          <div style={{ fontSize: 9.5, color: C.sub, lineHeight: 1.5 }}>{o.outlook}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── Kundli: Gann Square of 9 ──────────────────────────────── */}
            {gann && (
              <div className="pb-avoid" style={{ marginBottom: 16 }}>
                <SH label="Gann Analysis  — Square of 9 & Price Levels" accent={C.gold} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {/* Price levels */}
                  <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
                    <div style={{ fontSize: 8.5, color: C.muted, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 12 }}>Key Price Levels</div>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 8, color: C.red, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 6 }}>Resistance</div>
                        {gann.gann_levels.resistance.slice(0, 6).map((r, i) => (
                          <div key={i} style={{
                            padding: '5px 10px', borderRadius: 4, marginBottom: 4,
                            background: C.red + '0E', border: `1px solid ${C.red}33`,
                            color: C.red, fontSize: 11, fontWeight: 700,
                            textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums',
                          }}>&#8377;{r.toFixed(2)}</div>
                        ))}
                        {gann.gann_levels.key_r1 && (
                          <div style={{ fontSize: 9, color: C.muted, marginTop: 4 }}>Key R1: <strong style={{ color: C.red, fontFamily: 'monospace' }}>&#8377;{gann.gann_levels.key_r1.toFixed(2)}</strong></div>
                        )}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 8, color: C.green, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 6 }}>Support</div>
                        {gann.gann_levels.support.slice(0, 6).map((s, i) => (
                          <div key={i} style={{
                            padding: '5px 10px', borderRadius: 4, marginBottom: 4,
                            background: C.green + '0E', border: `1px solid ${C.green}33`,
                            color: C.green, fontSize: 11, fontWeight: 700,
                            textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums',
                          }}>&#8377;{s.toFixed(2)}</div>
                        ))}
                        {gann.gann_levels.key_s1 && (
                          <div style={{ fontSize: 9, color: C.muted, marginTop: 4 }}>Key S1: <strong style={{ color: C.green, fontFamily: 'monospace' }}>&#8377;{gann.gann_levels.key_s1.toFixed(2)}</strong></div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Sq of 9 + Planetary lines */}
                  <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
                    <div style={{ fontSize: 8.5, color: C.muted, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 10 }}>Square of 9</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, color: C.muted }}>Price degree</span>
                      <span style={{ fontSize: 11, fontWeight: 700, color: C.gold, fontFamily: 'monospace' }}>{gann.square_of_9.current_degree.toFixed(1)}&deg;</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                      <span style={{ fontSize: 10, color: C.muted }}>Nearest cardinal</span>
                      <span style={{ fontSize: 11, fontWeight: 700, color: C.accent }}>{gann.square_of_9.nearest_angle}</span>
                    </div>

                    <div style={{ fontSize: 8.5, color: C.muted, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 8, borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>Planetary Price Lines</div>
                    {Object.entries(gann.planetary_lines ?? {}).slice(0, 7).map(([planet, pl]) => (
                      <div key={planet} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
                        <span style={{ fontSize: 10, color: DASHA_COLOR[planet] ?? C.muted }}>{planet}</span>
                        <span style={{ fontSize: 9.5, color: C.dim, fontFamily: 'monospace' }}>{pl.longitude.toFixed(1)}&deg;</span>
                        <span style={{ fontSize: 11, fontWeight: 700, color: C.gold, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>&#8377;{pl.base_price.toFixed(1)}</span>
                      </div>
                    ))}

                    {/* Time cycles */}
                    {gann.time_cycles?.fixed_future_dates && Object.keys(gann.time_cycles.fixed_future_dates).length > 0 && (
                      <>
                        <div style={{ fontSize: 8.5, color: C.muted, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 8, borderTop: `1px solid ${C.border}`, paddingTop: 10, marginTop: 8 }}>Solar Time Cycles</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {Object.entries(gann.time_cycles.fixed_future_dates).slice(0, 6).map(([label, date]) => (
                            <div key={label} style={{ padding: '4px 8px', borderRadius: 4, background: C.surf2, border: `1px solid ${C.border}` }}>
                              <span style={{ fontSize: 8, color: C.dim }}>{label} </span>
                              <span style={{ fontSize: 9, color: C.sub, fontFamily: 'monospace' }}>{date}</span>
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ── Kundli: Bullish / Bearish factors ─────────────────────── */}
            {interp && (interp.bullish_factors?.length > 0 || interp.bearish_factors?.length > 0) && (
              <div className="pb-avoid" style={{ marginBottom: 16 }}>
                <SH label="Vedic Interpretation  — Planetary Factors" accent={C.purple} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
                    <div style={{ fontSize: 8, color: C.green, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 8 }}>Bullish Planetary Factors</div>
                    {interp.bullish_factors?.map((f, i) => (
                      <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'flex-start' }}>
                        <span style={{ color: C.green, fontWeight: 900, flexShrink: 0, marginTop: 1 }}>+</span>
                        <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.5 }}>{f}</span>
                      </div>
                    ))}
                  </div>
                  <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
                    {interp.bearish_factors?.length > 0 && (
                      <>
                        <div style={{ fontSize: 8, color: C.red, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 8 }}>Bearish Planetary Factors</div>
                        {interp.bearish_factors?.map((f, i) => (
                          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'flex-start' }}>
                            <span style={{ color: C.red, fontWeight: 900, flexShrink: 0, marginTop: 1 }}>-</span>
                            <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.5 }}>{f}</span>
                          </div>
                        ))}
                      </>
                    )}
                    {/* Context box */}
                    <div style={{ marginTop: interp.bearish_factors?.length > 0 ? 12 : 0, padding: '10px 12px', borderRadius: 6, background: C.purple + '09', border: `1px solid ${C.purple}22` }}>
                      <div style={{ fontSize: 8, color: C.purple, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 5 }}>Score Interpretation Note</div>
                      <div style={{ fontSize: 9.5, color: C.sub, lineHeight: 1.6 }}>
                        The Kundli score ({kundli.astro_score >= 0 ? '+' : ''}{kundli.astro_score.toFixed(0)}) reflects the company's natal chart at IPO — a fixed reading unique to this entity. The Astro Signal score reflects today's planetary movements for the sector — a dynamic daily reading. Both are valid and complementary signals.
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ── Kundli: Narrative ─────────────────────────────────────── */}
            {interp?.narrative && (
              <div className="pb-avoid" style={{ marginBottom: 16 }}>
                <SH label="Vedic Narrative Analysis" accent={C.purple} />
                <div style={{
                  background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8,
                  borderLeft: `4px solid ${C.purple}`,
                  padding: '14px 18px',
                }}>
                  {/* Signal header */}
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
                    <span style={{ fontSize: 18, fontWeight: 900, letterSpacing: '.06em', color: SIGNAL_COLOR[interp.signal] ?? C.sub }}>{interp.signal}</span>
                    <span style={{ fontSize: 14, fontWeight: 800, color: sentColor(interp.astro_score), fontFamily: 'monospace' }}>
                      {interp.astro_score >= 0 ? '+' : ''}{interp.astro_score.toFixed(0)}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: C.sub, lineHeight: 1.7 }}>{interp.narrative}</div>

                  {/* Yogas summary */}
                  {interp.yogas?.length > 0 && (
                    <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
                      <div style={{ fontSize: 8, color: C.muted, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 6 }}>Yogas Summary</div>
                      <div style={{ fontSize: 10, color: C.sub, lineHeight: 1.6 }}>{interp.yogas.join(' · ')}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── Kundli: Transits (current planetary positions) ─────────── */}
            {kundli.transits && Object.keys(kundli.transits).length > 0 && (
              <div className="pb-avoid" style={{ marginBottom: 16 }}>
                <SH label="Current Planet Transits vs Natal Chart" accent={C.purple} />
                <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
                  <table>
                    <thead>
                      <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                        {['Planet', 'Natal Sign', 'Current Sign', 'Aspect'].map(h => (
                          <th key={h} style={{ padding: '6px 10px', textAlign: 'left', fontSize: 8.5, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(kundli.transits).slice(0, 9).map(([planet, t], i) => (
                        <tr key={planet} style={{ background: i % 2 === 0 ? C.surf : C.surf2, borderBottom: `1px solid ${C.border}22` }}>
                          <td style={{ padding: '6px 10px', fontWeight: 700, color: DASHA_COLOR[planet] ?? C.text, fontSize: 10.5 }}>{planet}</td>
                          <td style={{ padding: '6px 10px', color: C.muted, fontSize: 10 }}>{t.natal_sign}</td>
                          <td style={{ padding: '6px 10px', color: C.sub, fontSize: 10 }}>{t.current_sign}</td>
                          <td style={{ padding: '6px 10px', fontSize: 9.5 }}>
                            <span style={{
                              color: t.aspect?.toLowerCase().includes('favorable') || t.aspect?.toLowerCase().includes('positive') ? C.green
                                   : t.aspect?.toLowerCase().includes('unfavorable') || t.aspect?.toLowerCase().includes('negative') ? C.red : C.muted,
                            }}>{t.aspect ?? '--'}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══ CORPORATE ACTIONS ══════════════════════════════════════════════ */}
        {ca.length > 0 && (
          <div className="pb-avoid" style={{ marginBottom: 16 }}>
            <SH label="Corporate Actions  (Last 12 Months)" accent={C.gold} />
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
              <table>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {['Ex-Date', 'Type', 'Detail', 'Rec. Date'].map(h => (
                      <th key={h} style={{ padding: '6px 10px', textAlign: 'left', fontSize: 8.5, fontWeight: 800, color: C.muted, letterSpacing: '.1em', textTransform: 'uppercase' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ca.slice(0, 20).map((a, i) => {
                    const cfg = CA_CFG[a.action_type] ?? { color: C.sub }
                    const detail2 = a.action_type === 'DIVIDEND' && a.dividend_rs != null
                      ? `₹${a.dividend_rs.toFixed(2)}/sh`
                      : a.action_type === 'BONUS' && a.bonus_ratio != null
                      ? `1:${a.bonus_ratio.toFixed(0)}`
                      : a.action_type === 'SPLIT' && a.split_new_fv != null
                      ? `FV ₹${a.split_new_fv}`
                      : a.subject.slice(0, 28)
                    return (
                      <tr key={i} style={{ background: i % 2 === 0 ? C.surf : C.surf2, borderBottom: `1px solid ${C.border}22` }}>
                        <td style={{ padding: '6px 10px', fontSize: 10, color: C.sub, fontFamily: 'monospace' }}>{fmt.date(a.ex_date)}</td>
                        <td style={{ padding: '6px 10px' }}>
                          <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 8, background: cfg.color + '18', border: `1px solid ${cfg.color}44`, color: cfg.color }}>{a.action_type}</span>
                        </td>
                        <td style={{ padding: '6px 10px', fontSize: 10, color: C.text, fontFamily: 'monospace', fontWeight: 600 }}>{detail2}</td>
                        <td style={{ padding: '6px 10px', fontSize: 10, color: C.muted, fontFamily: 'monospace' }}>{fmt.date(a.rec_date)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ══ ANNOUNCEMENTS ══════════════════════════════════════════════════ */}
        {anns.length > 0 && (
          <div className="pb-avoid" style={{ marginBottom: 16 }}>
            <SH label="Recent NSE Announcements" accent={C.teal} />
            <div style={{ background: C.surf, border: `1px solid ${C.border}`, borderRadius: 8, overflow: 'hidden' }}>
              {anns.slice(0, 10).map((a, i) => (
                <div key={i} style={{
                  padding: '10px 14px', borderBottom: i < anns.length - 1 ? `1px solid ${C.border}22` : 'none',
                  background: i % 2 === 0 ? C.surf : C.surf2,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: C.text, lineHeight: 1.4, marginBottom: 3 }}>{a.title}</div>
                      <div style={{ fontSize: 9, color: C.muted }}>{a.announcement_type ?? ''}</div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontSize: 9.5, color: C.muted, fontFamily: 'monospace' }}>{fmt.date(a.date)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══ FOOTER ═════════════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{
          borderTop: `1px solid ${C.border}`,
          padding: '14px 0 20px', marginTop: 8,
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
        }}>
          <div>
            <div style={{ fontSize: 9, fontWeight: 800, color: C.dim, letterSpacing: '.16em', textTransform: 'uppercase', marginBottom: 4 }}>CAPITAL FLOW INTELLIGENCE PLATFORM</div>
            <div style={{ fontSize: 8.5, color: C.dim, maxWidth: 600, lineHeight: 1.5 }}>
              This report is generated for informational purposes only and does not constitute financial advice. Past performance is not indicative of future results. Always conduct your own due diligence before making investment decisions.
            </div>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 9, color: C.dim, fontFamily: 'monospace' }}>{symbol} · NSE</div>
            <div style={{ fontSize: 8.5, color: C.dim, fontFamily: 'monospace', marginTop: 2 }}>
              {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
            </div>
          </div>
        </div>

      </div>{/* end #report-printable */}
    </div>
  )
}
