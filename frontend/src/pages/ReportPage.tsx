/**
 * ReportPage — Premium Stock Intelligence Report (v3)
 * Light background, dark text — optimised for print & PDF.
 * All field paths validated against live API response.
 */

import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  api, fetchStockDetail, fetchStockCorpActions, fetchStockAnnouncements,
  type Announcement,
} from '../api/client'

// ── Kundli types (from KundliCard) ────────────────────────────────────────────
interface KPlanet {
  longitude: number; sign: string; degree: number; house: number
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
  current_dasha: { mahadasha: KDashaEntry; antardasha: KDashaEntry; pratyantardasha: KDashaEntry; all_mahadashas: KDashaEntry[] }
  financial_houses: Record<string, KHouseData>
  yogas: KYoga[]
  transits: Record<string, { current_sign: string; natal_sign: string; aspect: string }>
  astro_score: number; astro_action: string
}
interface KGannData {
  square_of_9: { current_degree: number; nearest_angle: string }
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
interface KundliResponse { kundli: KundliData; gann: KGannData | null; interpretation: KInterpretation }

type Bar = { time: string | number; open: number; high: number; low: number; close: number; volume: number }

// ── Fetchers ──────────────────────────────────────────────────────────────────
const fetchOhlcv = (sym: string) =>
  api.get<{ bars: Bar[] }>('/charts/ohlcv', { params: { symbol: sym, timeframe: '1D' } }).then(r => r.data)
const fetchKundli = (sym: string) =>
  api.get<KundliResponse>(`/stocks/${sym}/kundli`).then(r => r.data)

// ── Light-theme design tokens ────────────────────────────────────────────────
// White background / dark text — optimised for print
const L = {
  bg:       '#FFFFFF',
  surf:     '#F8F9FB',
  surf2:    '#EFF2F6',
  border:   '#D0D8E4',
  borderH:  '#B0BECC',
  accent:   '#1A5FBF',    // navy blue
  gold:     '#B8740A',    // dark amber
  red:      '#B91C1C',    // dark red
  green:    '#166534',    // dark green
  teal:     '#0E7490',    // dark teal
  purple:   '#6B21A8',    // dark purple
  orange:   '#C2410C',
  text:     '#0F172A',    // near-black
  sub:      '#334155',    // dark slate
  muted:    '#64748B',    // medium slate
  dim:      '#94A3B8',    // light slate
}

// Toolbar uses dark navy (only visible on screen, not printed)
const TOOLBAR = { bg: '#0F172A', border: '#1E293B', text: '#94A3B8', btnBg: '#1E3A5F', btnText: '#60A5FA' }

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt = {
  pct:  (v: number | null | undefined) => v == null ? '--' : `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`,
  num:  (v: number | null | undefined, dp = 2) => v == null ? '--' : Number(v).toFixed(dp),
  rs:   (v: number | null | undefined, dp = 0) => v == null ? '--' : `₹${Number(v).toFixed(dp)}`,
  cr:   (v: number | null | undefined) => {
    if (v == null) return '--'
    const abs = Math.abs(Number(v)), sign = Number(v) < 0 ? '-' : ''
    if (abs >= 1e5) return `${sign}${(abs / 1e5).toFixed(1)}L Cr`
    if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(1)}K Cr`
    return `${sign}${abs.toFixed(0)} Cr`
  },
  date: (d: string | null | undefined) => d ? String(d).slice(0, 10) : '--',
  safe: (v: unknown) => (v == null || v === '' || (typeof v === 'number' && isNaN(v))) ? '--' : String(v),
}

const scoreColor = (v: number) => v >= 65 ? L.green : v >= 42 ? L.gold : L.red
const sentColor  = (v: number) => v >= 30 ? L.green : v >= 0 ? L.accent : v >= -20 ? L.gold : L.red

// ── Astro / Kundli constants ──────────────────────────────────────────────────
const PLANET_ORDER = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Rahu','Ketu']
const PLANET_ABBR: Record<string,string> = { Sun:'Su', Moon:'Mo', Mercury:'Me', Venus:'Ve', Mars:'Ma', Jupiter:'Ju', Saturn:'Sa', Rahu:'Ra', Ketu:'Ke' }
const DIGNITY_COLOR: Record<string,string> = {
  exalted_exact: L.green, exalted: L.green, moolatrikona: L.teal,
  own_sign: L.accent, friendly: L.sub, neutral: L.muted, enemy: L.gold, debilitated: L.red,
}
const DASHA_COLORS: Record<string,string> = {
  Sun: L.gold, Moon: L.accent, Mars: L.red, Mercury: L.green,
  Jupiter: L.teal, Venus: L.purple, Saturn: L.orange, Rahu: '#7C3AED', Ketu: L.muted,
}
const ZODIAC_FULL = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
const ZODIAC_ABBR = ['Ari','Tau','Gem','Can','Leo','Vir','Lib','Sco','Sag','Cap','Aqu','Pis']
const YOGA_COLOR: Record<string,string> = { BUY: L.green, HOLD: L.accent, CAUTION: L.gold, EXIT: L.orange, AVOID: L.red }
const HOUSE_STRENGTH_COLOR: Record<string,string> = { strong: L.green, 'moderate-strong': L.accent, moderate: L.muted, weak: L.red }
const SIGNAL_COLOR: Record<string,string> = { STRONG_BUY: L.green, BUY: L.green, HOLD: L.accent, CAUTION: L.gold, EXIT: L.orange, AVOID: L.red }
const CA_COLOR: Record<string,string> = { DIVIDEND: L.gold, BONUS: L.green, SPLIT: L.accent, BUYBACK: L.purple, RIGHTS: L.teal }

// ── SVG helpers ───────────────────────────────────────────────────────────────
function svgArc(cx: number, cy: number, r: number, startDeg: number, sweepDeg: number): string {
  const rad = (d: number) => d * Math.PI / 180
  const sx = cx + r * Math.cos(rad(startDeg)), sy = cy + r * Math.sin(rad(startDeg))
  const ed = startDeg + sweepDeg
  const ex = cx + r * Math.cos(rad(ed)), ey = cy + r * Math.sin(rad(ed))
  return `M ${sx.toFixed(2)} ${sy.toFixed(2)} A ${r} ${r} 0 ${sweepDeg > 180 ? 1 : 0} 1 ${ex.toFixed(2)} ${ey.toFixed(2)}`
}

// ── UI Components ─────────────────────────────────────────────────────────────

function SH({ label, accent }: { label: string; accent?: string }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:9, margin:'16px 0 7px', pageBreakAfter:'avoid', breakAfter:'avoid' }}>
      <div style={{ width:3, height:13, background: accent ?? L.accent, borderRadius:2, flexShrink:0 }} />
      <div style={{ fontSize:8.5, fontWeight:800, color:L.muted, letterSpacing:'.16em', textTransform:'uppercase' as const }}>{label}</div>
      <div style={{ flex:1, height:1, background:L.border }} />
    </div>
  )
}

function Chip({ label, color }: { label:string; color:string }) {
  return (
    <span style={{ display:'inline-block', padding:'2px 9px', borderRadius:10, fontSize:9, fontWeight:700, letterSpacing:'.04em', background: color+'1A', border:`1px solid ${color}55`, color }}>
      {label}
    </span>
  )
}

function ArcGauge({ value, max=100, label, size=84, colorOverride }: {
  value: number|null|undefined; max?: number; label: string; size?: number; colorOverride?: string
}) {
  const cx = size/2, cy = Math.round(size*0.58), r = Math.round(size*0.40), sw = size*0.09
  const h = Math.round(size*0.72)
  const bgPath = svgArc(cx, cy, r, 135, 270)
  if (value == null) return (
    <div style={{ textAlign:'center', minWidth:size }}>
      <svg width={size} height={h} viewBox={`0 0 ${size} ${h}`}>
        <path d={bgPath} fill="none" stroke={L.border} strokeWidth={sw} strokeLinecap="round"/>
        <text x={cx} y={cy+4} textAnchor="middle" fill={L.dim} fontSize={size*0.22} fontFamily="monospace">--</text>
      </svg>
      <div style={{ fontSize:7.5, color:L.muted, letterSpacing:'.1em', fontWeight:700, textTransform:'uppercase' as const, marginTop:2 }}>{label}</div>
    </div>
  )
  const pct = Math.min(1, Math.max(0, value/max))
  const sweepDeg = pct*270
  const color = colorOverride ?? scoreColor(pct*100)
  const fgPath = sweepDeg > 0.5 ? svgArc(cx, cy, r, 135, sweepDeg) : null
  return (
    <div style={{ textAlign:'center', pageBreakInside:'avoid', breakInside:'avoid', minWidth:size }}>
      <svg width={size} height={h} viewBox={`0 0 ${size} ${h}`}>
        <path d={bgPath} fill="none" stroke={L.surf2} strokeWidth={sw} strokeLinecap="round"/>
        {fgPath && <path d={fgPath} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"/>}
        <text x={cx} y={cy+4} textAnchor="middle" fill={color} fontSize={size*0.24} fontWeight={800} fontFamily="monospace" style={{ fontVariantNumeric:'tabular-nums' }}>
          {Math.round(value)}
        </text>
      </svg>
      <div style={{ fontSize:7.5, color:L.muted, letterSpacing:'.1em', fontWeight:700, textTransform:'uppercase' as const, marginTop:2, lineHeight:1.3 }}>{label}</div>
    </div>
  )
}

function DivergingGauge({ value, label, size=84 }: { value:number|null|undefined; label:string; size?:number }) {
  if (value == null) return <ArcGauge value={null} label={label} size={size} />
  const mapped = Math.min(100, Math.max(0, (Number(value)+200)/4))
  const color = sentColor(Number(value))
  const cx = size/2, cy = Math.round(size*0.58), r = Math.round(size*0.40), sw = size*0.09
  const h = Math.round(size*0.72)
  const sweepDeg = (mapped/100)*270
  const bgPath = svgArc(cx, cy, r, 135, 270)
  const fgPath = sweepDeg > 0.5 ? svgArc(cx, cy, r, 135, sweepDeg) : null
  const zx = cx + r*Math.cos(270*Math.PI/180), zy = cy + r*Math.sin(270*Math.PI/180)
  return (
    <div style={{ textAlign:'center', pageBreakInside:'avoid', breakInside:'avoid', minWidth:size }}>
      <svg width={size} height={h} viewBox={`0 0 ${size} ${h}`}>
        <path d={bgPath} fill="none" stroke={L.surf2} strokeWidth={sw} strokeLinecap="round"/>
        {fgPath && <path d={fgPath} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"/>}
        <circle cx={zx} cy={zy} r={sw*0.5} fill={L.borderH}/>
        <text x={cx} y={cy+4} textAnchor="middle" fill={color} fontSize={size*0.22} fontWeight={800} fontFamily="monospace" style={{ fontVariantNumeric:'tabular-nums' }}>
          {`${Number(value)>=0?'+':''}${Math.round(Number(value))}`}
        </text>
      </svg>
      <div style={{ fontSize:7.5, color:L.muted, letterSpacing:'.1em', fontWeight:700, textTransform:'uppercase' as const, marginTop:2, lineHeight:1.3 }}>{label}</div>
    </div>
  )
}

function Sparkline({ bars, width=820, height=52 }: { bars:Bar[]|undefined; width?:number; height?:number }) {
  if (!bars || bars.length < 2) return null
  const data = bars.slice(-120)
  const closes = data.map(b => b.close)
  const min = Math.min(...closes), max = Math.max(...closes), range = max-min||1
  const pad = 4
  const pts = closes.map((c,i) => {
    const x = pad+(i/(closes.length-1))*(width-2*pad)
    const y = height-pad-((c-min)/range)*(height-2*pad)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
  const isUp = closes[closes.length-1] >= closes[0]
  const color = isUp ? L.green : L.red
  const fillPts = `${pad},${height-pad} ${pts} ${width-pad},${height-pad}`
  const lx = width-pad, ly = height-pad-((closes[closes.length-1]-min)/range)*(height-2*pad)
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display:'block' }}>
      <defs>
        <linearGradient id="spkG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.18}/>
          <stop offset="100%" stopColor={color} stopOpacity={0.02}/>
        </linearGradient>
      </defs>
      <polygon points={fillPts} fill="url(#spkG)"/>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5}/>
      <circle cx={lx} cy={ly} r={3.5} fill={color}/>
    </svg>
  )
}

function ZodiacWheel({ planets, lagna, size=190 }: { planets:Record<string,KPlanet>|undefined; lagna:KundliData['lagna']|undefined; size?:number }) {
  const cx=size/2, cy=size/2, outerR=size*0.46, ringW=size*0.14, innerR=outerR-ringW, dotR=size*0.046
  const signIdx = (sign:string) => {
    const s = (sign||'').toLowerCase()
    let i = ZODIAC_FULL.findIndex(z=>z.toLowerCase()===s)
    if (i<0) i = ZODIAC_ABBR.findIndex(z=>s.startsWith(z.toLowerCase()))
    return i
  }
  const toAng = (td:number) => (td-90)*Math.PI/180
  if (!planets||!lagna) return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={outerR} fill={L.surf2} stroke={L.border}/>
      <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle" fill={L.muted} fontSize={11}>No data</text>
    </svg>
  )
  const lagnaIdx = signIdx(lagna.sign)
  const lagnaTotal = lagnaIdx>=0 ? lagnaIdx*30+lagna.degree : 0
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display:'block' }}>
      <circle cx={cx} cy={cy} r={outerR} fill={L.surf2} stroke={L.border} strokeWidth={1}/>
      <circle cx={cx} cy={cy} r={innerR} fill={L.bg} stroke={L.border} strokeWidth={1}/>
      {ZODIAC_ABBR.map((abbr,i) => {
        const sa=(i*30-90)*Math.PI/180, ma=((i*30+15)-90)*Math.PI/180
        const x1=cx+outerR*Math.cos(sa), y1=cy+outerR*Math.sin(sa)
        const x2=cx+innerR*Math.cos(sa), y2=cy+innerR*Math.sin(sa)
        const midR2=(outerR+innerR)/2, lx=cx+midR2*Math.cos(ma), ly=cy+midR2*Math.sin(ma)
        return (
          <g key={abbr}>
            <line x1={x2} y1={y2} x2={x1} y2={y1} stroke={L.border} strokeWidth={0.5}/>
            <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" fill={L.muted} fontSize={size*0.045} fontWeight={600} transform={`rotate(${i*30+15},${lx},${ly})`}>{abbr}</text>
          </g>
        )
      })}
      {(() => {
        const ang=toAng(lagnaTotal)
        const ix=cx+innerR*Math.cos(ang), iy=cy+innerR*Math.sin(ang)
        const ox=cx+outerR*Math.cos(ang), oy=cy+outerR*Math.sin(ang)
        return <g><line x1={ix} y1={iy} x2={ox} y2={oy} stroke={L.gold} strokeWidth={2}/><circle cx={ix} cy={iy} r={3.5} fill={L.gold}/></g>
      })()}
      {PLANET_ORDER.map((name,idx) => {
        const p=planets[name]; if(!p) return null
        const si=signIdx(p.sign); if(si<0) return null
        const ang=toAng(si*30+p.degree)
        const pr=innerR*(0.72-(idx%3)*0.18)
        const px=cx+pr*Math.cos(ang), py=cy+pr*Math.sin(ang)
        const color=DIGNITY_COLOR[p.dignity]??L.muted
        return (
          <g key={name}>
            <circle cx={px} cy={py} r={dotR} fill={color+'20'} stroke={color} strokeWidth={1}/>
            <text x={px} y={py} textAnchor="middle" dominantBaseline="middle" fill={color} fontSize={size*0.048} fontWeight={800} fontFamily="monospace">{PLANET_ABBR[name]??name.slice(0,2).toUpperCase()}</text>
          </g>
        )
      })}
      <text x={cx} y={cy-4} textAnchor="middle" fill={L.sub} fontSize={size*0.07} fontWeight={800}>{lagna.sign.slice(0,3).toUpperCase()}</text>
      <text x={cx} y={cy+10} textAnchor="middle" fill={L.muted} fontSize={size*0.046}>{lagna.degree.toFixed(1)}&deg;</text>
    </svg>
  )
}

// ── Print CSS ─────────────────────────────────────────────────────────────────
const PRINT_CSS = `
@page { size: A4 portrait; margin: 10mm 12mm; }
*,*::before,*::after { -webkit-print-color-adjust:exact!important; print-color-adjust:exact!important; color-adjust:exact!important; box-sizing:border-box; }
html,body { margin:0; padding:0; background:#FFFFFF; color:#0F172A; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; font-size:11px; }
.no-print { display:none!important; }
.pb  { page-break-before:always!important; break-before:page!important; }
.pba { page-break-after:always!important; break-after:page!important; }
.pb-avoid { page-break-inside:avoid!important; break-inside:avoid!important; }
table { border-collapse:collapse; width:100%; }
a { color:inherit; text-decoration:none; }
@media screen { body { padding:12px; max-width:900px; margin:0 auto; } }
`

function openPrintWindow(symbol: string) {
  const el = document.getElementById('report-printable')
  if (!el) { window.print(); return }
  const win = window.open('', '_blank', 'width=900,height=1200')
  if (!win) { window.print(); return }
  win.document.write(`<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>${symbol} — Stock Intelligence Report</title><style>${PRINT_CSS}</style></head><body>${el.innerHTML}</body></html>`)
  win.document.close()
  setTimeout(() => { win.focus(); win.print() }, 600)
}

// ── Main component ────────────────────────────────────────────────────────────
export function ReportPage() {
  const { symbol: urlSym } = useParams<{ symbol?:string }>()
  const symbol = (urlSym??'').toUpperCase()

  const { data: detail, isLoading: dLoading } = useQuery({ queryKey:['stock',symbol], queryFn:()=>fetchStockDetail(symbol), enabled:!!symbol, staleTime:5*60_000 })
  const { data: ohlcvData } = useQuery({ queryKey:['ohlcv',symbol], queryFn:()=>fetchOhlcv(symbol), enabled:!!symbol, staleTime:5*60_000 })
  const { data: corpActData } = useQuery({ queryKey:['ca',symbol,12], queryFn:()=>fetchStockCorpActions(symbol,12), enabled:!!symbol, staleTime:10*60_000 })
  const { data: annData } = useQuery({ queryKey:['ann',symbol,10], queryFn:()=>fetchStockAnnouncements(symbol,10), enabled:!!symbol, staleTime:10*60_000 })
  const { data: kundliData, isLoading: kLoading } = useQuery({ queryKey:['kundli',symbol], queryFn:()=>fetchKundli(symbol), enabled:!!symbol, staleTime:60*60_000 })

  // ── Data accessors (validated against live API) ───────────────────────────
  // detail IS the top-level response — NOT nested under detail.detail
  const d    = (detail ?? {}) as Record<string,unknown>
  const fun  = (d.fundamentals  ?? {}) as Record<string,unknown>
  const tec  = (d.technical     ?? {}) as Record<string,unknown>
  const ast  = (d.astro         ?? {}) as Record<string,unknown>
  const mgt  = (d.management    ?? {}) as Record<string,unknown>
  const ml   = (d.ml_scores     ?? {}) as Record<string,unknown>
  const comp = (d.components    ?? {}) as Record<string,unknown>
  const kl   = (d.key_levels    ?? {}) as Record<string,unknown>
  const agm  = (d.agm           ?? {}) as Record<string,unknown>
  const sh   = (d.shareholding  ?? {}) as Record<string,unknown>  // { promoter_pct, fii_pct, dii_pct, public_pct }
  const thesis = (d.structured_thesis ?? {}) as Record<string,unknown>  // { verdict, score, bull_signals, bear_signals }
  // holding_trends is a LIST sorted by quarter; latest = last element
  const htList = Array.isArray(d.holding_trends) ? (d.holding_trends as Record<string,unknown>[]) : []
  const htPrev = htList.length > 1 ? htList[htList.length-2] : null

  const bars = ohlcvData?.bars ?? []
  const kundli = kundliData?.kundli
  const gann   = kundliData?.gann
  const interp = kundliData?.interpretation
  const ca   = corpActData?.actions ?? []
  const anns = ((annData as { announcements?:Announcement[] })?.announcements ?? [])

  // Price
  const lastBar = bars.length > 0 ? bars[bars.length-1] : null
  const prevBar = bars.length > 1 ? bars[bars.length-2] : null
  const price   = lastBar?.close ?? Number(d.close_now ?? 0)
  const chg     = prevBar ? price - prevBar.close : 0
  const chgPct  = prevBar ? (chg/prevBar.close)*100 : 0

  // Delta helpers for shareholding
  const delta = (curr: unknown, prev: unknown) => {
    if (curr == null || prev == null) return null
    return Number(curr) - Number(prev)
  }

  // ── Toolbar ───────────────────────────────────────────────────────────────
  return (
    <div style={{ background: TOOLBAR.bg, minHeight:'100%' }}>
      <div className="no-print" style={{ position:'sticky', top:0, zIndex:100, background:TOOLBAR.bg, borderBottom:`1px solid ${TOOLBAR.border}`, padding:'8px 16px', display:'flex', alignItems:'center', gap:12 }}>
        <Link to={symbol ? `/stocks/${symbol}` : '/stocks'} style={{ color:TOOLBAR.text, fontSize:11, textDecoration:'none' }}>&larr; Back to {symbol||'Stocks'}</Link>
        <div style={{ flex:1 }} />
        {(dLoading||kLoading) && <span style={{ fontSize:11, color:'#94A3B8' }}>Loading{kLoading?' kundli':''}…</span>}
        {(['Print / Download PDF','Download PDF'] as const).map(label => (
          <button key={label} onClick={()=>openPrintWindow(symbol)} disabled={dLoading||kLoading} style={{ display:'flex', alignItems:'center', gap:6, padding:'7px 16px', borderRadius:5, border:`1px solid ${TOOLBAR.btnBg}`, background:TOOLBAR.btnBg, color:TOOLBAR.btnText, cursor:'pointer', fontSize:12, fontWeight:600 }}>
            <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            {label}
          </button>
        ))}
      </div>

      {/* ── Printable content — WHITE background ──────────────────────────── */}
      <div id="report-printable" style={{ background:L.bg, maxWidth:900, margin:'0 auto', padding:'20px 18px 0', color:L.text }}>

        {/* ══ MASTHEAD ══════════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:'20px 22px 16px', marginBottom:14, borderTop:`3px solid ${L.accent}` }}>
          <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:16 }}>
            <div style={{ flex:1 }}>
              <div style={{ fontSize:8, color:L.dim, fontWeight:800, letterSpacing:'.2em', textTransform:'uppercase', marginBottom:5 }}>CAPITAL FLOW INTELLIGENCE PLATFORM</div>
              <div style={{ fontSize:34, fontWeight:900, color:L.text, fontFamily:'monospace', letterSpacing:'.04em', lineHeight:1 }}>{symbol||'--'}</div>
              <div style={{ fontSize:12, color:L.sub, marginTop:3 }}>{fmt.safe(d.sector)} · NSE Equities</div>
              <div style={{ display:'flex', alignItems:'baseline', gap:10, marginTop:8 }}>
                <span style={{ fontSize:26, fontWeight:800, color:L.text, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>
                  {price > 0 ? `₹${price.toFixed(2)}` : '--'}
                </span>
                {chg !== 0 && (
                  <span style={{ fontSize:13, fontWeight:700, color: chg>=0 ? L.green : L.red, fontFamily:'monospace' }}>
                    {chg>=0?'+':''}{chg.toFixed(2)} ({fmt.pct(chgPct)})
                  </span>
                )}
              </div>
              <div style={{ display:'flex', flexWrap:'wrap', gap:5, marginTop:8 }}>
                {Boolean(d.sector) && <Chip label={String(d.sector)} color={L.accent}/>}
                {Boolean(d.label) && <Chip label={String(d.label)} color={scoreColor(Number(d.bull_run_score ?? 50))}/>}
                {Boolean(ast.astro_action) && <Chip label={String(ast.astro_action)} color={SIGNAL_COLOR[String(ast.astro_action)] ?? L.sub}/>}
                {Boolean(tec.trend_signal) && <Chip label={String(tec.trend_signal)} color={L.teal}/>}
              </div>
            </div>
            <div style={{ textAlign:'right', flexShrink:0 }}>
              <div style={{ fontSize:8, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:4 }}>Generated</div>
              <div style={{ fontSize:11, color:L.muted, fontFamily:'monospace' }}>{new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})}</div>
              {lastBar && <div style={{ fontSize:9, color:L.dim, marginTop:5, fontFamily:'monospace' }}>Data: {fmt.date(String(lastBar.time))}</div>}
            </div>
          </div>
          {bars.length > 1 && (
            <div style={{ marginTop:12, borderTop:`1px solid ${L.border}`, paddingTop:10 }}>
              <Sparkline bars={bars} width={820} height={50}/>
            </div>
          )}
        </div>

        {/* ══ SCORE GAUGES ═════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom:14 }}>
          <SH label="Intelligence Scores"/>
          <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:'14px 10px', display:'grid', gridTemplateColumns:'repeat(8,1fr)', gap:6 }}>
            <ArcGauge value={Number(d.bull_run_score)||null}               label="Bull Run" size={84}/>
            <ArcGauge value={Number(comp.price_score)||null}               label="Price Score" size={84}/>
            <ArcGauge value={Number(ml.ml_bull_run_score)||null}           label="ML Bull Run" size={84}/>
            <ArcGauge value={Number(ml.accumulation_score)||null}          label="ML Accumul." size={84}/>
            <ArcGauge value={Number(comp.sector_flow_score)||null}         label="Sector Flow" size={84}/>
            <ArcGauge value={Number(comp.deal_score)||null}                label="Deal Score" size={84}/>
            <ArcGauge value={Number(fun.valuation_score)||null}            label="Valuation" size={84}/>
            <DivergingGauge value={kundli?.astro_score ?? (Number(ast.astro_score)||null)} label="Vedic Astro" size={84}/>
          </div>
        </div>

        {/* ══ INVESTMENT THESIS ════════════════════════════════════════════ */}
        {(Boolean(thesis.verdict) || Boolean(thesis.bull_signals)) && (
          <div className="pb-avoid" style={{ marginBottom:14 }}>
            <SH label="Investment Thesis" accent={L.gold}/>
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:'14px 18px', borderLeft:`4px solid ${scoreColor(Number(d.bull_run_score??50))}` }}>
              <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:10, flexWrap:'wrap' }}>
                {Boolean(thesis.verdict) && <span style={{ fontSize:15, fontWeight:900, letterSpacing:'.06em', color:SIGNAL_COLOR[String(thesis.verdict)]??L.green }}>{String(thesis.verdict)}</span>}
                {d.bull_run_score != null && <span style={{ fontSize:11, color:L.muted }}>Score <strong style={{ color:scoreColor(Number(d.bull_run_score)), fontFamily:'monospace' }}>{Number(d.bull_run_score).toFixed(1)}</strong> / 100</span>}
                {Boolean(thesis.dominant_factor) && <Chip label={String(thesis.dominant_factor)} color={L.teal}/>}
              </div>
              {(() => {
                // bull_signals / bear_signals may arrive as Python repr strings — handle both
                const parseSigs = (raw:unknown):string[] => {
                  if (Array.isArray(raw)) return raw as string[]
                  if (typeof raw === 'string') {
                    try { return JSON.parse(raw.replace(/'/g,'"')) } catch { return raw.split(',').map(s=>s.trim()).filter(Boolean) }
                  }
                  return []
                }
                const bulls = parseSigs(thesis.bull_signals)
                const bears = parseSigs(thesis.bear_signals)
                return (
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
                    <div>{bulls.slice(0,5).map((s,i)=>(
                      <div key={i} style={{ display:'flex', gap:7, marginBottom:4 }}>
                        <span style={{ color:L.green, fontWeight:900, flexShrink:0 }}>+</span>
                        <span style={{ fontSize:10.5, color:L.sub, lineHeight:1.5 }}>{s}</span>
                      </div>
                    ))}</div>
                    <div>{bears.slice(0,4).map((s,i)=>(
                      <div key={i} style={{ display:'flex', gap:7, marginBottom:4 }}>
                        <span style={{ color:L.red, fontWeight:900, flexShrink:0 }}>-</span>
                        <span style={{ fontSize:10.5, color:L.sub, lineHeight:1.5 }}>{s}</span>
                      </div>
                    ))}</div>
                  </div>
                )
              })()}
              {Boolean(thesis.ml_note) && <div style={{ marginTop:8, fontSize:9.5, color:L.muted, borderTop:`1px solid ${L.border}`, paddingTop:7 }}>{String(thesis.ml_note)}</div>}
            </div>
          </div>
        )}

        {/* ══ PRICE HISTORY ════════════════════════════════════════════════ */}
        {bars.length > 0 && (
          <div className="pb" style={{ marginBottom:14 }}>
            <SH label="Price History  (Last 30 Sessions)"/>
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, overflow:'hidden' }}>
              <table>
                <thead>
                  <tr style={{ background:L.surf2, borderBottom:`1px solid ${L.border}` }}>
                    {['Date','Open','High','Low','Close','Volume','Chg%'].map(h=>(
                      <th key={h} style={{ padding:'6px 9px', textAlign: h==='Date'?'left':'right', fontSize:8.5, fontWeight:800, color:L.muted, letterSpacing:'.1em', textTransform:'uppercase' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bars.slice(-30).reverse().map((b,i)=>{
                    const prev = bars[bars.length-30+(30-1-i)-1]
                    const cp = prev ? (b.close-prev.close)/prev.close*100 : 0
                    const up = b.close >= b.open
                    return (
                      <tr key={i} style={{ background: i%2===0?L.bg:L.surf, borderBottom:`1px solid ${L.border}33` }}>
                        <td style={{ padding:'5px 9px', fontSize:9.5, color:L.sub, fontFamily:'monospace' }}>{fmt.date(String(b.time))}</td>
                        <td style={{ padding:'5px 9px', fontSize:9.5, color:L.muted, textAlign:'right', fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{b.open.toFixed(2)}</td>
                        <td style={{ padding:'5px 9px', fontSize:9.5, color:L.green, textAlign:'right', fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{b.high.toFixed(2)}</td>
                        <td style={{ padding:'5px 9px', fontSize:9.5, color:L.red, textAlign:'right', fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{b.low.toFixed(2)}</td>
                        <td style={{ padding:'5px 9px', fontSize:10.5, color: up?L.green:L.red, textAlign:'right', fontFamily:'monospace', fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{b.close.toFixed(2)}</td>
                        <td style={{ padding:'5px 9px', fontSize:9, color:L.muted, textAlign:'right', fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{b.volume>0?(b.volume>=1e6?`${(b.volume/1e6).toFixed(2)}M`:b.volume>=1e3?`${(b.volume/1e3).toFixed(0)}K`:String(b.volume)):'--'}</td>
                        <td style={{ padding:'5px 9px', fontSize:9.5, color: cp>=0?L.green:L.red, textAlign:'right', fontFamily:'monospace', fontWeight:700, fontVariantNumeric:'tabular-nums' }}>{fmt.pct(cp)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ══ TECHNICAL ANALYSIS ═══════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom:14 }}>
          <SH label="Technical Analysis" accent={L.teal}/>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
            {/* Moving averages */}
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
              <div style={{ fontSize:8.5, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:10 }}>Moving Averages</div>
              {([
                { label:'20 DMA',  val:tec.dma_20,  pct:tec.vs_dma_20  },
                { label:'50 DMA',  val:tec.dma_50,  pct:tec.vs_dma_50  },
                { label:'200 DMA', val:tec.dma_200, pct:tec.vs_dma_200 },
              ] as {label:string; val:unknown; pct:unknown}[]).map(({label,val,pct:p})=>{
                if (!val) return null
                const v=Number(val), diff=p!=null?Number(p)*100 : (price>0?(price-v)/v*100:0)
                return (
                  <div key={label} style={{ display:'flex', alignItems:'center', gap:8, marginBottom:7 }}>
                    <span style={{ fontSize:10, color:L.muted, minWidth:54 }}>{label}</span>
                    <span style={{ fontSize:10, color:L.sub, minWidth:60, textAlign:'right', fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>₹{v.toFixed(0)}</span>
                    <span style={{ fontSize:10, fontWeight:700, color:diff>=0?L.green:L.red, minWidth:52, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{diff>=0?'+':''}{diff.toFixed(1)}%</span>
                    <div style={{ flex:1, height:4, background:L.surf2, borderRadius:2 }}>
                      <div style={{ width:`${Math.min(100,Math.abs(diff)/25*100)}%`, height:'100%', background:diff>=0?L.green:L.red, borderRadius:2, opacity:0.7 }}/>
                    </div>
                  </div>
                )
              })}
              <div style={{ marginTop:10, paddingTop:8, borderTop:`1px solid ${L.border}`, display:'flex', gap:8, flexWrap:'wrap' }}>
                {Boolean(tec.trend_signal) && <><span style={{ fontSize:9, color:L.muted }}>Trend:</span><Chip label={String(tec.trend_signal)} color={L.teal}/></>}
                {tec.vol_20d_avg != null && <span style={{ fontSize:9, color:L.muted }}>Avg Vol: <strong style={{ color:L.sub }}>{Number(tec.vol_20d_avg)>=1e6?`${(Number(tec.vol_20d_avg)/1e6).toFixed(2)}M`:Number(tec.vol_20d_avg)>=1e3?`${(Number(tec.vol_20d_avg)/1e3).toFixed(0)}K`:String(tec.vol_20d_avg)}</strong></span>}
              </div>
            </div>

            {/* Key levels */}
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
              <div style={{ fontSize:8.5, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:10 }}>Key Levels (Gann/Pivots)</div>
              {([
                { label:'52W High',     val:tec.high_52w,       color:L.red   },
                { label:'52W Low',      val:tec.low_52w,        color:L.green },
                { label:'Resistance 1', val:kl.conf_res_1,      color:L.red   },
                { label:'Resistance 2', val:kl.conf_res_2,      color:L.red   },
                { label:'Support 1',    val:kl.conf_sup_1,      color:L.green },
                { label:'Support 2',    val:kl.conf_sup_2,      color:L.green },
                { label:'Entry Zone',   val:kl.entry_zone_low != null && kl.entry_zone_high != null ? `₹${Number(kl.entry_zone_low).toFixed(0)} – ₹${Number(kl.entry_zone_high).toFixed(0)}` : null, color:L.accent, asStr:true },
                { label:'Stop Loss',    val:kl.stop_loss,       color:L.red   },
                { label:'Target 1ATR',  val:kl.target_1atr,     color:L.teal  },
                { label:'Target 2ATR',  val:kl.target_2atr,     color:L.teal  },
              ] as {label:string;val:unknown;color:string;asStr?:boolean}[]).filter(r=>r.val!=null).map(({label,val,color,asStr})=>(
                <div key={label} style={{ display:'flex', justifyContent:'space-between', marginBottom:5, alignItems:'center' }}>
                  <span style={{ fontSize:9.5, color:L.muted }}>{label}</span>
                  <span style={{ fontSize:10.5, fontWeight:700, color, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>
                    {asStr ? String(val) : `₹${Number(val).toFixed(2)}`}
                  </span>
                </div>
              ))}
              {Boolean(kl.conf_res_1_tags) && <div style={{ marginTop:6, fontSize:8.5, color:L.dim }}>R1 tags: {String(kl.conf_res_1_tags)}</div>}
              {Boolean(kl.conf_sup_1_tags) && <div style={{ marginTop:2, fontSize:8.5, color:L.dim }}>S1 tags: {String(kl.conf_sup_1_tags)}</div>}
            </div>
          </div>
        </div>

        {/* ══ FUNDAMENTALS ════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom:14 }}>
          <SH label="Company Fundamentals" accent={L.gold}/>
          <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14 }}>
              {([
                { label:'Market Cap',    val: fun.market_cap_cr!=null?fmt.cr(Number(fun.market_cap_cr)):fmt.cr(Number(d.close_now??0)*Number(fun.shares_outstanding_cr??0)), color:L.text  },
                { label:'P/E Ratio',     val: fmt.num(Number(fun.pe_ratio),1),                                                                                                   color:L.sub   },
                { label:'ROE %',         val: fmt.num(Number(fun.roe_pct),2),                                                                                                    color: Number(fun.roe_pct??0)>=15?L.green:L.gold },
                { label:'ROCE %',        val: fmt.num(Number(fun.roce_pct),2),                                                                                                   color: Number(fun.roce_pct??0)>=12?L.green:L.gold },
                { label:'OPM %',         val: fmt.num(Number(fun.opm_pct),2),                                                                                                    color:L.sub   },
                { label:'Book Value/Sh', val: fun.book_value_per_share!=null?`₹${Number(fun.book_value_per_share).toFixed(2)}`:'--',                                        color:L.sub   },
                { label:'Revenue TTM',   val: fmt.cr(Number(fun.revenue_ttm_cr)),                                                                                                color:L.text  },
                { label:'Profit TTM',    val: fmt.cr(Number(fun.profit_ttm_cr)),                                                                                                 color: Number(fun.profit_ttm_cr??0)>=0?L.green:L.red },
                { label:'Sales Growth',  val: fmt.pct(Number(fun.sales_growth_3y_pct)),                                                                                          color: Number(fun.sales_growth_3y_pct??0)>=10?L.green:L.gold },
                { label:'Qtr Rev Grwth', val: fmt.pct(Number(fun.qtr_sales_growth_pct)),                                                                                         color: Number(fun.qtr_sales_growth_pct??0)>=0?L.green:L.red  },
                { label:'Qtr Pft Grwth', val: fmt.pct(Number(fun.qtr_profit_growth_pct)),                                                                                        color: Number(fun.qtr_profit_growth_pct??0)>=0?L.green:L.red  },
                { label:'52W High',      val: tec.high_52w!=null?`₹${Number(tec.high_52w).toFixed(0)}`:'--',                                                               color:L.red   },
                { label:'52W Low',       val: tec.low_52w!=null?`₹${Number(tec.low_52w).toFixed(0)}`:'--',                                                                 color:L.green },
                { label:'From ATH',      val: fmt.pct(Number(fun.down_from_ath_pct)),                                                                                            color: Number(fun.down_from_ath_pct??0)>=0?L.green:L.red },
                { label:'Val. Label',    val: fmt.safe(fun.valuation_label),                                                                                                     color:L.teal  },
                { label:'Valuation Sc.', val: fmt.num(Number(fun.valuation_score),1),                                                                                            color: scoreColor(Number(fun.valuation_score??50)) },
              ] as {label:string;val:string;color:string}[]).map(({label,val,color})=>(
                <div key={label} className="pb-avoid" style={{ pageBreakInside:'avoid', breakInside:'avoid' }}>
                  <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.08em', textTransform:'uppercase', marginBottom:3 }}>{label}</div>
                  <div style={{ fontSize:15, fontWeight:800, color, fontFamily:'monospace', fontVariantNumeric:'tabular-nums', lineHeight:1.2 }}>{val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ══ INSTITUTIONAL INTELLIGENCE ══════════════════════════════════ */}
        <div className="pb-avoid" style={{ marginBottom:14 }}>
          <SH label="Institutional Intelligence" accent={L.purple}/>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
            {/* Shareholding */}
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
              <div style={{ fontSize:8.5, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:10 }}>
                Shareholding Pattern {sh.quarter_end_date ? `(${String(sh.quarter_end_date)})` : ''}
              </div>
              {([
                { label:'Promoter',  val:sh.promoter_pct, prev:htPrev?.promoter_pct, barColor:L.gold   },
                { label:'FII',       val:sh.fii_pct,      prev:htPrev?.fii_pct,      barColor:L.accent },
                { label:'DII',       val:sh.dii_pct,      prev:htPrev?.dii_pct,      barColor:L.teal   },
                { label:'Public',    val:sh.public_pct,   prev:null,                 barColor:L.muted  },
              ] as {label:string;val:unknown;prev:unknown;barColor:string}[]).map(({label,val,prev,barColor})=>{
                if (val==null) return null
                const v=Number(val), d2=delta(val,prev)
                return (
                  <div key={label} style={{ display:'flex', alignItems:'center', gap:8, marginBottom:7 }}>
                    <span style={{ fontSize:9.5, color:L.muted, minWidth:60 }}>{label}</span>
                    <span style={{ fontSize:12, fontWeight:700, color:L.text, fontFamily:'monospace', fontVariantNumeric:'tabular-nums', minWidth:52 }}>{v.toFixed(2)}%</span>
                    {d2!=null && d2!==0 && <span style={{ fontSize:9.5, fontWeight:700, color:d2>0?L.green:L.red, fontFamily:'monospace' }}>{d2>0?'+':''}{d2.toFixed(2)}%</span>}
                    <div style={{ flex:1, height:5, background:L.surf2, borderRadius:2 }}>
                      <div style={{ width:`${Math.min(100,v)}%`, height:'100%', background:barColor, borderRadius:2, opacity:0.7 }}/>
                    </div>
                  </div>
                )
              })}
              {htList.length > 1 && (
                <div style={{ marginTop:10, paddingTop:8, borderTop:`1px solid ${L.border}` }}>
                  <div style={{ fontSize:8, color:L.dim, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:6 }}>QoQ Trend (last {htList.length} quarters)</div>
                  <div style={{ overflowX:'auto' }}>
                    <table style={{ fontSize:9, minWidth:300 }}>
                      <thead>
                        <tr style={{ borderBottom:`1px solid ${L.border}` }}>
                          {['Quarter','Promoter%','FII%','DII%'].map(h=><th key={h} style={{ padding:'3px 8px', textAlign: h==='Quarter'?'left':'right', color:L.dim, fontWeight:700, whiteSpace:'nowrap' }}>{h}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {htList.slice(-4).map((row,i)=>(
                          <tr key={i} style={{ borderBottom:`1px solid ${L.border}22` }}>
                            <td style={{ padding:'3px 8px', color:L.sub }}>{String(row.period??'')}</td>
                            <td style={{ padding:'3px 8px', textAlign:'right', color:L.sub, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{row.promoter_pct!=null?Number(row.promoter_pct).toFixed(2):'--'}</td>
                            <td style={{ padding:'3px 8px', textAlign:'right', color:L.accent, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{row.fii_pct!=null?Number(row.fii_pct).toFixed(2):'--'}</td>
                            <td style={{ padding:'3px 8px', textAlign:'right', color:L.teal, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{row.dii_pct!=null?Number(row.dii_pct).toFixed(2):'--'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Management */}
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
              <div style={{ fontSize:8.5, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:10 }}>Management Intelligence</div>
              {([
                { label:'Holding Signal',  val:mgt.holding_signal,    color:SIGNAL_COLOR[String(mgt.holding_signal??'')]??L.sub },
                { label:'Holding Score',   val:mgt.holding_score!=null?Number(mgt.holding_score).toFixed(1):null, color:scoreColor(Number(mgt.holding_score??50)) },
                { label:'Mgmt Score',      val:mgt.management_score!=null?Number(mgt.management_score).toFixed(1):null, color:scoreColor(Number(mgt.management_score??50)) },
                { label:'Mgmt Label',      val:mgt.management_label,  color:SIGNAL_COLOR[String(mgt.management_label??'')]??L.sub },
                { label:'AI Tone Score',   val:mgt.ai_tone_score!=null?Number(mgt.ai_tone_score).toFixed(1):null, color:sentColor(Number(mgt.ai_tone_score??0)) },
                { label:'Annc. Score',     val:mgt.announcement_score!=null?Number(mgt.announcement_score).toFixed(1):null, color:scoreColor(Number(mgt.announcement_score??50)) },
              ] as {label:string;val:unknown;color:string}[]).filter(r=>r.val!=null).map(({label,val,color})=>(
                <div key={label} style={{ display:'flex', justifyContent:'space-between', marginBottom:7, alignItems:'center' }}>
                  <span style={{ fontSize:9.5, color:L.muted }}>{label}</span>
                  <span style={{ fontSize:11, fontWeight:700, color, fontFamily:'monospace' }}>{fmt.safe(val)}</span>
                </div>
              ))}
              {Boolean(agm.key_decision) && (
                <div style={{ marginTop:10, paddingTop:8, borderTop:`1px solid ${L.border}` }}>
                  <div style={{ fontSize:8, color:L.dim, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:5 }}>Last AGM / Board Decision</div>
                  <div style={{ fontSize:9.5, color:L.sub, lineHeight:1.5 }}>{String(agm.key_decision).slice(0,200)}</div>
                  <div style={{ fontSize:8.5, color:L.dim, marginTop:3 }}>Governance: <strong style={{ color:agm.governance_risk==='LOW'?L.green:L.gold }}>{String(agm.governance_risk??'')}</strong> · Score: {fmt.num(Number(agm.governance_score),0)}/100</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ══ ASTRO SIGNAL ════════════════════════════════════════════════ */}
        {Object.keys(ast).length > 0 && (
          <div className="pb-avoid" style={{ marginBottom:14 }}>
            <SH label="Daily Astro Signal  (Sector Planetary Intelligence)" accent={L.purple}/>
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:'14px 18px' }}>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginBottom:12 }}>
                {([
                  { label:'Primary Planet', val:ast.primary_planet,   color:L.gold   },
                  { label:'Signal',         val:ast.astro_action,      color:SIGNAL_COLOR[String(ast.astro_action??'')]??L.sub },
                  { label:'Score',          val:ast.astro_score!=null?`${Number(ast.astro_score)>=0?'+':''}${Number(ast.astro_score).toFixed(0)}`:'--', color:sentColor(Number(ast.astro_score??0)) },
                  { label:'Planet Sign',    val:ast.planet_sign,       color:L.accent },
                  { label:'Planet State',   val:ast.planet_state,      color:L.sub    },
                  { label:'Retrograde',     val:ast.planet_retrograde!=null?(ast.planet_retrograde?'YES':'NO'):null, color:ast.planet_retrograde?L.red:L.green },
                  { label:'Moon Phase',     val:ast.moon_phase,        color:L.muted  },
                  { label:'Eclipse',        val:ast.eclipse_active!=null?(ast.eclipse_active?'ACTIVE':'None'):null, color:ast.eclipse_active?L.red:L.muted },
                ] as {label:string;val:unknown;color:string}[]).filter(r=>r.val!=null).map(({label,val,color})=>(
                  <div key={label} className="pb-avoid">
                    <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:3 }}>{label}</div>
                    <div style={{ fontSize:13, fontWeight:700, color, fontFamily:'monospace' }}>{fmt.safe(val)}</div>
                  </div>
                ))}
              </div>
              {Boolean(ast.astro_reason) && (
                <div style={{ padding:'10px 14px', background:L.surf2, borderRadius:6, border:`1px solid ${L.border}` }}>
                  <div style={{ fontSize:8, color:L.purple, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:5 }}>Planetary Reasoning</div>
                  <div style={{ fontSize:10.5, color:L.sub, lineHeight:1.6 }}>{String(ast.astro_reason)}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            VEDIC KUNDLI — ALL SECTIONS INLINE
        ══════════════════════════════════════════════════════════════════ */}
        {kundli && (
          <div>
            {/* ── Overview + Zodiac Wheel ───────────────────────────────── */}
            <div className="pb" style={{ marginBottom:14 }}>
              <SH label="Vedic Kundli  — Natal Chart Overview" accent={L.purple}/>
              <div style={{ display:'grid', gridTemplateColumns:'auto 1fr', gap:14, alignItems:'start' }}>
                <div className="pb-avoid" style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:12, textAlign:'center' }}>
                  <ZodiacWheel planets={kundli.planets} lagna={kundli.lagna} size={188}/>
                  <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.12em', textTransform:'uppercase', marginTop:6 }}>Natal Planetary Chart</div>
                  <div style={{ fontSize:8.5, color:L.muted, marginTop:2 }}>IPO: {fmt.date(kundli.entity?.inception_date)}</div>
                </div>
                <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:'14px 16px' }}>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12, marginBottom:14 }}>
                    <div>
                      <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:3 }}>Lagna (Ascendant)</div>
                      <div style={{ fontSize:17, fontWeight:800, color:L.gold, fontFamily:'monospace' }}>{kundli.lagna.sign}</div>
                      <div style={{ fontSize:9.5, color:L.muted }}>{kundli.lagna.degree.toFixed(1)}&deg; · Lord: <span style={{ color:DASHA_COLORS[kundli.lagna.lord]??L.sub }}>{kundli.lagna.lord}</span></div>
                    </div>
                    <div>
                      <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:3 }}>Astro Score</div>
                      <div style={{ fontSize:20, fontWeight:900, color:sentColor(kundli.astro_score), fontFamily:'monospace' }}>{kundli.astro_score>=0?'+':''}{kundli.astro_score.toFixed(0)}</div>
                      <div style={{ fontSize:10, color:SIGNAL_COLOR[kundli.astro_action]??L.sub }}>{kundli.astro_action}</div>
                    </div>
                    <div>
                      <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:3 }}>Entity</div>
                      <div style={{ fontSize:11, fontWeight:700, color:L.text }}>{kundli.entity?.name}</div>
                      <div style={{ fontSize:9.5, color:L.muted }}>{kundli.entity?.inception_date} {kundli.entity?.inception_time}</div>
                    </div>
                  </div>
                  <div style={{ borderTop:`1px solid ${L.border}`, paddingTop:12, marginBottom:12 }}>
                    <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:8 }}>Current Dasha Period</div>
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:8 }}>
                      {[{label:'Mahadasha',dasha:kundli.current_dasha?.mahadasha},{label:'Antardasha',dasha:kundli.current_dasha?.antardasha},{label:'Pratyantar',dasha:kundli.current_dasha?.pratyantardasha}].map(({label,dasha})=>{
                        const d2 = dasha as unknown as KDashaEntry
                        return d2 && (
                        <div key={label} style={{ background:L.surf2, border:`1px solid ${L.border}`, borderRadius:6, padding:'8px 10px' }}>
                          <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:3 }}>{label}</div>
                          <div style={{ fontSize:14, fontWeight:800, color:DASHA_COLORS[d2.planet]??L.sub, fontFamily:'monospace' }}>{d2.planet}</div>
                          <div style={{ fontSize:8, color:L.muted, marginTop:2 }}>until {fmt.date(d2.end_date)}</div>
                        </div>
                      )})}
                    </div>
                  </div>
                  {kundli.yogas?.length > 0 && (
                    <div style={{ borderTop:`1px solid ${L.border}`, paddingTop:10 }}>
                      <div style={{ fontSize:7.5, color:L.dim, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:6 }}>Active Yogas</div>
                      <div style={{ display:'flex', flexWrap:'wrap', gap:5 }}>
                        {kundli.yogas.map((y,i)=>(
                          <span key={i} style={{ padding:'3px 9px', borderRadius:10, fontSize:9, fontWeight:700, background:(YOGA_COLOR[y.signal]??L.muted)+'18', border:`1px solid ${(YOGA_COLOR[y.signal]??L.muted)}44`, color:YOGA_COLOR[y.signal]??L.muted }}>{y.name}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ── Planets Table ─────────────────────────────────────────── */}
            <div className="pb-avoid" style={{ marginBottom:14 }}>
              <SH label="Planetary Positions  — All 9 Planets" accent={L.purple}/>
              <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, overflow:'hidden' }}>
                <table>
                  <thead>
                    <tr style={{ background:L.surf2, borderBottom:`1px solid ${L.border}` }}>
                      {['Planet','Sign','Deg','House','Nakshatra','Pada','Dignity','R'].map(h=>(
                        <th key={h} style={{ padding:'6px 9px', textAlign: h==='Planet'?'left':'right', fontSize:8.5, fontWeight:800, color:L.muted, letterSpacing:'.1em', textTransform:'uppercase' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {PLANET_ORDER.filter(n=>kundli.planets[n]).map((name,i)=>{
                      const p=kundli.planets[name], dc=DIGNITY_COLOR[p.dignity]??L.muted
                      return (
                        <tr key={name} style={{ background: i%2===0?L.bg:L.surf, borderBottom:`1px solid ${L.border}22` }}>
                          <td style={{ padding:'6px 9px', fontWeight:700, color:DASHA_COLORS[name]??L.text, fontSize:11 }}>{name}</td>
                          <td style={{ padding:'6px 9px', color:L.sub, textAlign:'right', fontSize:10 }}>{p.sign}</td>
                          <td style={{ padding:'6px 9px', color:L.muted, textAlign:'right', fontSize:9.5, fontFamily:'monospace' }}>{p.degree.toFixed(1)}&deg;</td>
                          <td style={{ padding:'6px 9px', color:L.sub, textAlign:'right', fontSize:10, fontFamily:'monospace' }}>H{p.house}</td>
                          <td style={{ padding:'6px 9px', color:L.muted, textAlign:'right', fontSize:9 }}>{p.nakshatra}</td>
                          <td style={{ padding:'6px 9px', color:L.dim, textAlign:'right', fontSize:9 }}>{p.pada}</td>
                          <td style={{ padding:'6px 9px', textAlign:'right' }}><span style={{ fontSize:9, fontWeight:700, color:dc }}>{p.dignity.replace(/_/g,' ')}</span></td>
                          <td style={{ padding:'6px 9px', textAlign:'right', fontSize:9.5, color: p.retrograde?L.red:L.dim, fontWeight: p.retrograde?800:400 }}>{p.retrograde?'R':'-'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ── Financial Houses ──────────────────────────────────────── */}
            {kundli.financial_houses && Object.keys(kundli.financial_houses).length > 0 && (
              <div className="pb-avoid" style={{ marginBottom:14 }}>
                <SH label="Financial Houses Analysis" accent={L.purple}/>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
                  {(['2H','5H','8H','10H','11H'] as const).map(hk=>{
                    const h=kundli.financial_houses[hk]; if(!h) return null
                    const sc=HOUSE_STRENGTH_COLOR[h.strength]??L.sub
                    const LABELS:Record<string,string>={'2H':'2nd  — Wealth / Balance Sheet','5H':'5th  — Speculation / R&D','8H':'8th  — Volatility / M&A','10H':'10th  — Mgmt / Reputation','11H':'11th  — Revenue / Profits'}
                    return (
                      <div key={hk} className="pb-avoid" style={{ background:L.surf, border:`1px solid ${L.border}`, borderLeft:`3px solid ${sc}`, borderRadius:8, padding:'10px 14px', pageBreakInside:'avoid', breakInside:'avoid' }}>
                        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:7 }}>
                          <span style={{ fontSize:10, fontWeight:700, color:L.text }}>{LABELS[hk]??hk}</span>
                          <span style={{ fontSize:8.5, fontWeight:700, padding:'2px 8px', borderRadius:8, background:sc+'18', border:`1px solid ${sc}44`, color:sc }}>{h.strength.replace(/-/g,' ')}</span>
                        </div>
                        <div style={{ display:'flex', gap:12, flexWrap:'wrap', marginBottom:4 }}>
                          <span style={{ fontSize:9, color:L.muted }}>Sign: <span style={{ color:L.sub }}>{h.sign}</span></span>
                          <span style={{ fontSize:9, color:L.muted }}>Lord: <span style={{ color:DIGNITY_COLOR[h.lord_dignity]??L.sub, fontWeight:700 }}>{h.lord}</span>{h.lord_house&&<span style={{ color:L.dim }}> in H{h.lord_house}</span>}</span>
                          {h.occupants.length>0&&<span style={{ fontSize:9, color:L.muted }}>Planets: <span style={{ color:L.accent }}>{h.occupants.join(', ')}</span></span>}
                        </div>
                        <div style={{ fontSize:9, color:L.muted, lineHeight:1.5 }}>{h.signification}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* ── Dasha Sequence ────────────────────────────────────────── */}
            {kundli.current_dasha?.all_mahadashas?.length > 0 && (
              <div className="pb-avoid" style={{ marginBottom:14 }}>
                <SH label="Mahadasha Timeline  — Planetary Periods" accent={L.purple}/>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
                  <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, overflow:'hidden' }}>
                    <table>
                      <thead>
                        <tr style={{ background:L.surf2, borderBottom:`1px solid ${L.border}` }}>
                          {['Planet','Start','End',''].map(h=><th key={h} style={{ padding:'5px 9px', textAlign:'left', fontSize:8.5, fontWeight:800, color:L.muted, letterSpacing:'.1em', textTransform:'uppercase' }}>{h}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {kundli.current_dasha.all_mahadashas.slice(0,9).map((m,i)=>{
                          const dc=DASHA_COLORS[m.planet]??L.muted
                          const nowY=new Date().getFullYear(), sY=parseInt(m.start_date?.slice(0,4)??'0'), eY=parseInt(m.end_date?.slice(0,4)??'9999')
                          const active=sY<=nowY&&nowY<=eY
                          return (
                            <tr key={i} style={{ background: active?dc+'12':(i%2===0?L.bg:L.surf), borderBottom:`1px solid ${L.border}22` }}>
                              <td style={{ padding:'5px 9px', fontWeight: active?800:500, color:dc, fontSize:11 }}>{m.planet}{active?' *':''}</td>
                              <td style={{ padding:'5px 9px', fontSize:9.5, color:L.sub, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{m.start_date?.slice(0,7)}</td>
                              <td style={{ padding:'5px 9px', fontSize:9.5, color:L.sub, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>{m.end_date?.slice(0,7)}</td>
                              <td style={{ padding:'5px 9px' }}>{active&&<span style={{ fontSize:8, color:dc, fontWeight:800 }}>ACTIVE</span>}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                  <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
                    <div style={{ fontSize:8, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:8 }}>Dasha Outlook</div>
                    {interp?.dasha_outlook?.slice(0,5).map((o,i)=>(
                      <div key={i} style={{ marginBottom:8, paddingBottom:8, borderBottom: i<4?`1px solid ${L.border}22`:'none' }}>
                        <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                          <span style={{ fontSize:10, fontWeight:700, color:L.text }}>{o.period}</span>
                          <span style={{ fontSize:8.5, color:L.dim, fontFamily:'monospace' }}>{o.start?.slice(0,4)}-{o.end?.slice(0,4)}</span>
                        </div>
                        {o.outlook&&<div style={{ fontSize:9.5, color:L.sub, lineHeight:1.5 }}>{o.outlook}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── Gann ─────────────────────────────────────────────────── */}
            {gann && (
              <div className="pb-avoid" style={{ marginBottom:14 }}>
                <SH label="Gann Analysis  — Square of 9 & Price Levels" accent={L.gold}/>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
                  <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
                    <div style={{ fontSize:8.5, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:10 }}>Key Price Levels</div>
                    <div style={{ display:'flex', gap:10 }}>
                      <div style={{ flex:1 }}>
                        <div style={{ fontSize:8, color:L.red, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:5 }}>Resistance</div>
                        {gann.gann_levels.resistance.slice(0,5).map((r,i)=>(
                          <div key={i} style={{ padding:'4px 9px', borderRadius:4, marginBottom:3, background:L.red+'0C', border:`1px solid ${L.red}33`, color:L.red, fontSize:11, fontWeight:700, textAlign:'right', fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>₹{r.toFixed(2)}</div>
                        ))}
                        {gann.gann_levels.key_r1&&<div style={{ fontSize:8.5, color:L.muted, marginTop:4 }}>Key R1: <strong style={{ color:L.red, fontFamily:'monospace' }}>₹{gann.gann_levels.key_r1.toFixed(2)}</strong></div>}
                      </div>
                      <div style={{ flex:1 }}>
                        <div style={{ fontSize:8, color:L.green, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:5 }}>Support</div>
                        {gann.gann_levels.support.slice(0,5).map((s,i)=>(
                          <div key={i} style={{ padding:'4px 9px', borderRadius:4, marginBottom:3, background:L.green+'0C', border:`1px solid ${L.green}33`, color:L.green, fontSize:11, fontWeight:700, textAlign:'right', fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>₹{s.toFixed(2)}</div>
                        ))}
                        {gann.gann_levels.key_s1&&<div style={{ fontSize:8.5, color:L.muted, marginTop:4 }}>Key S1: <strong style={{ color:L.green, fontFamily:'monospace' }}>₹{gann.gann_levels.key_s1.toFixed(2)}</strong></div>}
                      </div>
                    </div>
                  </div>
                  <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
                    <div style={{ fontSize:8.5, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:10 }}>Square of 9</div>
                    <div style={{ display:'flex', justifyContent:'space-between', marginBottom:4 }}>
                      <span style={{ fontSize:10, color:L.muted }}>Price degree</span>
                      <span style={{ fontSize:11, fontWeight:700, color:L.gold, fontFamily:'monospace' }}>{gann.square_of_9.current_degree.toFixed(1)}&deg;</span>
                    </div>
                    <div style={{ display:'flex', justifyContent:'space-between', marginBottom:14 }}>
                      <span style={{ fontSize:10, color:L.muted }}>Nearest cardinal</span>
                      <span style={{ fontSize:11, fontWeight:700, color:L.accent }}>{gann.square_of_9.nearest_angle}</span>
                    </div>
                    <div style={{ fontSize:8.5, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:8, borderTop:`1px solid ${L.border}`, paddingTop:10 }}>Planetary Price Lines</div>
                    {Object.entries(gann.planetary_lines??{}).slice(0,7).map(([planet,pl])=>(
                      <div key={planet} style={{ display:'flex', justifyContent:'space-between', marginBottom:4, alignItems:'center' }}>
                        <span style={{ fontSize:10, color:DASHA_COLORS[planet]??L.muted }}>{planet}</span>
                        <span style={{ fontSize:9, color:L.dim, fontFamily:'monospace' }}>{pl.longitude.toFixed(1)}&deg;</span>
                        <span style={{ fontSize:11, fontWeight:700, color:L.gold, fontFamily:'monospace', fontVariantNumeric:'tabular-nums' }}>₹{pl.base_price.toFixed(1)}</span>
                      </div>
                    ))}
                    {gann.time_cycles?.fixed_future_dates && Object.keys(gann.time_cycles.fixed_future_dates).length>0 && (
                      <>
                        <div style={{ fontSize:8, color:L.muted, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginTop:10, marginBottom:6, borderTop:`1px solid ${L.border}`, paddingTop:8 }}>Solar Time Cycles</div>
                        <div style={{ display:'flex', flexWrap:'wrap', gap:5 }}>
                          {Object.entries(gann.time_cycles.fixed_future_dates).slice(0,6).map(([lbl,date])=>(
                            <div key={lbl} style={{ padding:'3px 7px', borderRadius:4, background:L.surf2, border:`1px solid ${L.border}` }}>
                              <span style={{ fontSize:8, color:L.dim }}>{lbl} </span>
                              <span style={{ fontSize:8.5, color:L.sub, fontFamily:'monospace' }}>{date}</span>
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ── Interpretation + Narrative ───────────────────────────── */}
            {interp && (interp.bullish_factors?.length>0 || interp.bearish_factors?.length>0 || interp.narrative) && (
              <div className="pb-avoid" style={{ marginBottom:14 }}>
                <SH label="Vedic Interpretation  — Full Analysis" accent={L.purple}/>
                {interp.narrative && (
                  <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderLeft:`4px solid ${L.purple}`, borderRadius:8, padding:'14px 18px', marginBottom:12 }}>
                    <div style={{ display:'flex', gap:12, alignItems:'center', marginBottom:10 }}>
                      <span style={{ fontSize:15, fontWeight:900, letterSpacing:'.06em', color:SIGNAL_COLOR[interp.signal]??L.sub }}>{interp.signal}</span>
                      <span style={{ fontSize:14, fontWeight:800, color:sentColor(interp.astro_score), fontFamily:'monospace' }}>{interp.astro_score>=0?'+':''}{interp.astro_score.toFixed(0)}</span>
                    </div>
                    <div style={{ fontSize:10.5, color:L.sub, lineHeight:1.7 }}>{interp.narrative}</div>
                    {interp.yogas?.length>0 && <div style={{ marginTop:10, paddingTop:8, borderTop:`1px solid ${L.border}`, fontSize:9.5, color:L.muted }}>{interp.yogas.join(' · ')}</div>}
                  </div>
                )}
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
                  <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
                    <div style={{ fontSize:8, color:L.green, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:7 }}>Bullish Planetary Factors</div>
                    {interp.bullish_factors?.map((f,i)=>(
                      <div key={i} style={{ display:'flex', gap:7, marginBottom:5 }}>
                        <span style={{ color:L.green, fontWeight:900, flexShrink:0 }}>+</span>
                        <span style={{ fontSize:10, color:L.sub, lineHeight:1.5 }}>{f}</span>
                      </div>
                    ))}
                  </div>
                  <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, padding:14 }}>
                    {interp.bearish_factors?.length>0 && <>
                      <div style={{ fontSize:8, color:L.red, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:7 }}>Bearish Planetary Factors</div>
                      {interp.bearish_factors?.map((f,i)=>(
                        <div key={i} style={{ display:'flex', gap:7, marginBottom:5 }}>
                          <span style={{ color:L.red, fontWeight:900, flexShrink:0 }}>-</span>
                          <span style={{ fontSize:10, color:L.sub, lineHeight:1.5 }}>{f}</span>
                        </div>
                      ))}
                    </>}
                    <div style={{ marginTop: interp.bearish_factors?.length>0?12:0, padding:'9px 12px', borderRadius:6, background:L.purple+'09', border:`1px solid ${L.purple}22` }}>
                      <div style={{ fontSize:8, color:L.purple, fontWeight:800, letterSpacing:'.1em', textTransform:'uppercase', marginBottom:4 }}>Score Note</div>
                      <div style={{ fontSize:9, color:L.sub, lineHeight:1.6 }}>Kundli score ({kundli.astro_score>=0?'+':''}{kundli.astro_score.toFixed(0)}) = company's natal chart at IPO — fixed. Astro Signal = today's sector planetary reading — dynamic. Both are complementary signals.</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══ CORPORATE ACTIONS ════════════════════════════════════════════ */}
        {ca.length > 0 && (
          <div className="pb-avoid" style={{ marginBottom:14 }}>
            <SH label="Corporate Actions  (Last 12 Months)" accent={L.gold}/>
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, overflow:'hidden' }}>
              <table>
                <thead>
                  <tr style={{ background:L.surf2, borderBottom:`1px solid ${L.border}` }}>
                    {['Ex-Date','Type','Detail','Rec. Date'].map(h=>(
                      <th key={h} style={{ padding:'6px 9px', textAlign:'left', fontSize:8.5, fontWeight:800, color:L.muted, letterSpacing:'.1em', textTransform:'uppercase' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ca.slice(0,20).map((a,i)=>{
                    const color=CA_COLOR[a.action_type]??L.sub
                    const detail2 = a.action_type==='DIVIDEND'&&a.dividend_rs!=null?`₹${a.dividend_rs.toFixed(2)}/sh`
                      : a.action_type==='BONUS'&&a.bonus_ratio!=null?`1:${a.bonus_ratio.toFixed(0)}`
                      : a.action_type==='SPLIT'&&a.split_new_fv!=null?`FV ₹${a.split_new_fv}`
                      : a.subject.slice(0,28)
                    return (
                      <tr key={i} style={{ background: i%2===0?L.bg:L.surf, borderBottom:`1px solid ${L.border}22` }}>
                        <td style={{ padding:'5px 9px', fontSize:9.5, color:L.sub, fontFamily:'monospace' }}>{fmt.date(a.ex_date)}</td>
                        <td style={{ padding:'5px 9px' }}><span style={{ fontSize:8.5, fontWeight:700, padding:'2px 7px', borderRadius:8, background:color+'18', border:`1px solid ${color}44`, color }}>{a.action_type}</span></td>
                        <td style={{ padding:'5px 9px', fontSize:10, color:L.text, fontFamily:'monospace', fontWeight:600 }}>{detail2}</td>
                        <td style={{ padding:'5px 9px', fontSize:9.5, color:L.muted, fontFamily:'monospace' }}>{fmt.date(a.rec_date)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ══ ANNOUNCEMENTS ════════════════════════════════════════════════ */}
        {anns.length > 0 && (
          <div className="pb-avoid" style={{ marginBottom:14 }}>
            <SH label="Recent NSE Announcements" accent={L.teal}/>
            <div style={{ background:L.surf, border:`1px solid ${L.border}`, borderRadius:8, overflow:'hidden' }}>
              {anns.slice(0,10).map((a,i)=>(
                <div key={i} style={{ padding:'9px 14px', borderBottom: i<anns.length-1?`1px solid ${L.border}22`:'none', background: i%2===0?L.bg:L.surf }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:12 }}>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:10.5, fontWeight:600, color:L.text, lineHeight:1.4, marginBottom:2 }}>{a.title}</div>
                      <div style={{ fontSize:8.5, color:L.muted }}>{a.announcement_type??''}</div>
                    </div>
                    <div style={{ fontSize:9, color:L.muted, fontFamily:'monospace', flexShrink:0 }}>{fmt.date(a.date)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══ FOOTER ══════════════════════════════════════════════════════ */}
        <div className="pb-avoid" style={{ borderTop:`1px solid ${L.border}`, padding:'12px 0 20px', marginTop:6, display:'flex', justifyContent:'space-between', alignItems:'flex-end' }}>
          <div>
            <div style={{ fontSize:8.5, fontWeight:800, color:L.dim, letterSpacing:'.16em', textTransform:'uppercase', marginBottom:3 }}>CAPITAL FLOW INTELLIGENCE PLATFORM</div>
            <div style={{ fontSize:8, color:L.dim, maxWidth:580, lineHeight:1.5 }}>
              This report is for informational purposes only and does not constitute financial advice. Past performance is not indicative of future results. Conduct your own due diligence before making any investment decisions.
            </div>
          </div>
          <div style={{ textAlign:'right', flexShrink:0 }}>
            <div style={{ fontSize:9, color:L.dim, fontFamily:'monospace' }}>{symbol} · NSE</div>
            <div style={{ fontSize:8.5, color:L.dim, fontFamily:'monospace', marginTop:2 }}>
              {new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})}
            </div>
          </div>
        </div>

      </div>{/* end #report-printable */}
    </div>
  )
}
