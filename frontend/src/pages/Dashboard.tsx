/**
 * Dashboard — Professional infographic redesign
 * Design system: high-contrast text, rich navy card palette, visual data encoding
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  fetchMarketContext, fetchParticipantLatest, fetchParticipantHistory, fetchSectors,
  fetchCatalysts, fetchDeals, fetchNews, fetchSocialPulse, fetchVoiceAnalytics,
  type MarketContext, type ParticipantLatest, type Sector, type NewsItem,
  type SocialPulseHandle,
} from '../api/client'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Legend, BarChart, Bar, ReferenceLine,
} from 'recharts'
import { T, FS, FW } from '../styles/tokens'
import { useMobile }    from '../hooks/useMobile'

// ─── Page palette (aliases from shared design tokens) ─────────────────────────
// Text hierarchy  : h1 > text > textSub > muted  (never dim for readable text)

const C = {
  bg:       T.bg,
  bgInner:  T.cell,
  border:   `1px solid ${T.border}`,
  borderH:  T.borderHi,
  h1:       T.h1,
  primary:  T.text,
  secondary:T.textSub,
  muted:    T.muted,
  dim:      T.dim,
  bull:     T.green,
  bear:     T.red,
  neutral:  T.amber,
  fii:      T.fii,
  dii:      T.dii,
  pro:      T.pro,
  client:   T.client,
  blue:     T.blue,
} as const

const CARD: React.CSSProperties = {
  background: C.bg, border: C.border, borderRadius: 10,
}
const LABEL: React.CSSProperties = {
  color: C.secondary, fontSize: FS.label, fontWeight: FW.bold, letterSpacing: 1.5, textTransform: 'uppercase',
}
const VAL: React.CSSProperties = {
  color: C.h1, fontWeight: FW.heavy, fontFamily: 'monospace',
}

const signed = (n: number | null | undefined, d = 1) =>
  n == null ? '--' : `${n >= 0 ? '+' : ''}${n.toFixed(d)}`

function _relTimeShort(iso: string | null | undefined): string {
  if (!iso) return ''
  const then = new Date(iso.replace(' ', 'T') + 'Z').getTime()
  if (Number.isNaN(then)) return ''
  const diffMin = Math.max(0, Math.floor((Date.now() - then) / 60000))
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffMin < 1440) return `${Math.floor(diffMin / 60)}h ago`
  return `${Math.floor(diffMin / 1440)}d ago`
}

// ─── Recently Asked (Phase V-DATA-3) ──────────────────────────────────────────
// Purely additive: surfaces what you've been asking Veda about. Never reorders
// or influences any ranked list (Conviction Screener, Watchlist, ML scores) --
// what you're curious about is not evidence of what the data says is good.
// Language-agnostic by construction (captured from actual tool calls in
// chat_engine.py, not a text regex), so Hindi voice queries count too.

function RecentlyAskedCard() {
  const { data } = useQuery({
    queryKey: ['voice-analytics-dashboard'],
    queryFn: fetchVoiceAnalytics,
    refetchInterval: 300_000,
    staleTime: 120_000,
  })

  const symbols = (data?.top_symbols ?? []).slice(0, 10)
  const totalTurns = data?.summary?.total_turns ?? 0

  return (
    <div style={{ ...CARD, padding: '16px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: symbols.length ? 12 : 4 }}>
        <div style={LABEL}>RECENTLY ASKED <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(what you've been researching with Veda)</span></div>
        <Link to="/chat" style={{ color: C.blue, fontSize: 11, textDecoration: 'none', fontWeight: 600 }}>Ask Veda →</Link>
      </div>
      {symbols.length === 0 ? (
        <div style={{ color: C.muted, fontSize: 11, padding: '4px 0 2px' }}>
          {totalTurns > 0
            ? "No specific stocks identified yet -- ask Veda about a symbol by name to build this up."
            : "Not enough chat history yet -- ask Veda about a stock to build this up."}
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {symbols.map(s => (
            <Link key={s.key} to={`/stocks/${s.key}`} style={{ textDecoration: 'none' }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 7,
                background: C.bgInner, border: `1px solid ${T.border}`, borderRadius: 6,
                padding: '6px 10px', transition: 'border-color 0.15s',
              }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = `${C.blue}66`)}
                onMouseLeave={e => (e.currentTarget.style.borderColor = T.border)}
              >
                <span style={{ color: C.h1, fontSize: 12, fontWeight: 700 }}>{s.key}</span>
                <span style={{ color: C.blue, fontSize: 10, fontWeight: 700 }}>×{s.count}</span>
                {s.last_seen && <span style={{ color: C.dim, fontSize: 9 }}>{_relTimeShort(s.last_seen)}</span>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Command Strip ────────────────────────────────────────────────────────────

function CommandStrip({ ctx, part, isMobile }: { ctx: MarketContext; part: ParticipantLatest | undefined; isMobile: boolean }) {
  const rgColor = ctx.regime === 'BULL' ? C.bull : ctx.regime === 'BEAR' ? C.bear : C.neutral
  const pcrColor = ctx.pcr_signal === 'BULLISH' ? C.bull : ctx.pcr_signal === 'BEARISH' ? C.bear : C.neutral
  const smColor  = (ctx.smart_money_score ?? 0) >= 0 ? C.bull : C.bear

  const cells = [
    {
      label: 'MARKET REGIME',
      content: (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            padding: '4px 14px', borderRadius: 6, fontWeight: 800, fontSize: 15,
            background: `${rgColor}20`, color: rgColor, border: `1px solid ${rgColor}55`,
            letterSpacing: 1,
          }}>{ctx.regime}</div>
        </div>
      ),
    },
    {
      label: 'SMART MONEY',
      content: (
        <div>
          <span style={{ ...VAL, fontSize: 22, color: smColor }}>
            {signed(ctx.smart_money_score)}
          </span>
          <span style={{ color: C.muted, fontSize: 10, marginLeft: 4 }}>z-score</span>
        </div>
      ),
    },
    {
      label: 'PUT/CALL RATIO',
      content: (
        <div>
          <span style={{ ...VAL, fontSize: 22, color: pcrColor }}>{ctx.pcr?.toFixed(2) ?? '--'}</span>
          <div style={{ color: pcrColor, fontSize: 10, fontWeight: 700, marginTop: 2 }}>{ctx.pcr_signal}</div>
        </div>
      ),
    },
    {
      label: 'FII CONVICTION',
      content: part && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: C.secondary, fontSize: 10 }}>FII</span>
            <span style={{ color: C.fii, fontWeight: 700, fontSize: 12 }}>{part.FII_conviction.toFixed(0)}%</span>
          </div>
          <div style={{ height: 5, background: C.bgInner, borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${part.FII_conviction}%`, background: C.fii, borderRadius: 3 }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: C.secondary, fontSize: 10 }}>DII</span>
            <span style={{ color: C.dii, fontWeight: 700, fontSize: 12 }}>{part.DII_conviction.toFixed(0)}%</span>
          </div>
          <div style={{ height: 5, background: C.bgInner, borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${part.DII_conviction}%`, background: C.dii, borderRadius: 3 }} />
          </div>
        </div>
      ),
    },
    {
      label: 'UNIVERSE BREADTH',
      content: ctx.breadth && (
        <div style={{ display: 'flex', gap: 12 }}>
          {([
            { k: 'bull_run',     l: 'BULL',  col: C.bull    },
            { k: 'emerging',     l: 'EMRG',  col: '#10B981' },
            { k: 'accumulation', l: 'ACCUM', col: '#9575CD' },
            { k: 'markdown',     l: 'DOWN',  col: C.bear    },
          ] as const).map(({ k, l, col }) => (
            <Link key={k} to={`/watchlist?label=${k.toUpperCase()}`}
              title={`Open the full ${k.replace('_', ' ')} list`}
              style={{ textAlign: 'center', textDecoration: 'none', cursor: 'pointer' }}>
              <div style={{ color: col, fontSize: 18, fontWeight: 800, lineHeight: 1 }}>
                {ctx.breadth![k as keyof typeof ctx.breadth]}
              </div>
              <div style={{ color: C.muted, fontSize: 9, marginTop: 3 }}>{l}</div>
            </Link>
          ))}
        </div>
      ),
    },
    {
      label: 'FII/DII DIVERGENCE',
      content: part && (
        <div>
          <div style={{ ...VAL, fontSize: 22, color: (part.FII_DII_Divergence ?? 0) >= 0 ? C.bull : C.bear }}>
            {signed(part.FII_DII_Divergence)}
          </div>
          <div style={{ color: C.muted, fontSize: 10, marginTop: 2 }}>
            Smart/Retail: <span style={{ color: (part.Smart_Retail_Divergence ?? 0) >= 0 ? C.bull : C.bear, fontWeight: 700 }}>
              {signed(part.Smart_Retail_Divergence)}
            </span>
          </div>
        </div>
      ),
    },
  ]

  return (
    <div style={{
      ...CARD,
      display: 'grid',
      gridTemplateColumns: isMobile ? '1fr 1fr' : 'auto 1fr 1fr 1.4fr 1.6fr 1fr',
      gap: 0,
      overflow: 'hidden',
    }}>
      {cells.map((cell, i) => (
        <div key={i} style={{
          padding: isMobile ? '10px 12px' : '14px 20px',
          borderRight: isMobile
            ? (i % 2 === 0 ? C.border : 'none')
            : (i < cells.length - 1 ? C.border : 'none'),
          borderBottom: isMobile && i < cells.length - 2 ? C.border : 'none',
        }}>
          <div style={{ ...LABEL, marginBottom: 8 }}>{cell.label}</div>
          {cell.content}
        </div>
      ))}
    </div>
  )
}

// ─── SVG Regime Speedometer ───────────────────────────────────────────────────

function RegimeDial({ score, regime }: { score: number; regime: string }) {
  const cx = 120, cy = 105, R = 80, Rn = 65
  const clamped = Math.max(-100, Math.min(100, score))
  const ratio   = (clamped + 100) / 200
  const theta   = Math.PI - ratio * Math.PI
  const nx = cx + Rn * Math.cos(theta)
  const ny = cy - Rn * Math.sin(theta)

  const pt = (t: number, r = R) => {
    const a = Math.PI - t * Math.PI
    return { x: cx + r * Math.cos(a), y: cy - r * Math.sin(a) }
  }

  // Needle tip glow coordinates (shorter)
  const tipX = cx + (Rn + 8) * Math.cos(theta)
  const tipY = cy - (Rn + 8) * Math.sin(theta)

  const segs = [
    { from: 0,   to: 1/3, color: C.bear,    stops: ['#F44B4B', '#FF8A8A'] },
    { from: 1/3, to: 2/3, color: C.neutral, stops: ['#F5A524', '#FFD280'] },
    { from: 2/3, to: 1,   color: C.bull,    stops: ['#22D35E', '#70FF9A'] },
  ]

  const rgColor = regime === 'BULL' ? C.bull : regime === 'BEAR' ? C.bear : C.neutral

  return (
    <div style={{ ...CARD, padding: '20px', display: 'flex', flexDirection: 'column' }}>
      <div style={LABEL}>REGIME METER</div>
      <svg viewBox="0 0 240 130" width="100%" style={{ display: 'block', margin: '8px auto 0', maxWidth: 300 }}>
        <defs>
          {segs.map(({ from, stops }, i) => (
            <linearGradient key={i} id={`gr${i}`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={stops[0]} />
              <stop offset="100%" stopColor={stops[1]} />
            </linearGradient>
          ))}
          <filter id="glow">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {/* Track */}
        {(() => { const s = pt(0); const e = pt(1)
          return <path d={`M${s.x},${s.y} A${R},${R} 0 0,1 ${e.x},${e.y}`}
            stroke="#1A2540" strokeWidth="18" fill="none" strokeLinecap="round" /> })()}

        {/* Colored arc segments */}
        {segs.map(({ from, to, color }, i) => {
          const s = pt(from); const e = pt(to)
          return <path key={i} d={`M${s.x},${s.y} A${R},${R} 0 0,1 ${e.x},${e.y}`}
            stroke={color} strokeWidth="14" fill="none" strokeLinecap="round" opacity="0.85" />
        })}

        {/* Glow dot at needle tip */}
        <circle cx={tipX} cy={tipY} r="5" fill={rgColor} filter="url(#glow)" opacity="0.9" />

        {/* Needle */}
        <line x1={cx} y1={cy} x2={nx} y2={ny}
          stroke={rgColor} strokeWidth="2.5" strokeLinecap="round" filter="url(#glow)" />
        <circle cx={cx} cy={cy} r="6" fill="#0E1420" stroke={rgColor} strokeWidth="2.5" />

        {/* Zone labels */}
        <text x="20" y="122" fill={C.bear}    fontSize="9" textAnchor="middle" fontFamily="monospace" fontWeight="700">BEAR</text>
        <text x={cx} y="122" fill={C.neutral} fontSize="9" textAnchor="middle" fontFamily="monospace" fontWeight="700">NEUTRAL</text>
        <text x="220" y="122" fill={C.bull}   fontSize="9" textAnchor="middle" fontFamily="monospace" fontWeight="700">BULL</text>

        {/* Score + regime */}
        <text x={cx} y="78" fill={rgColor} fontSize="22" fontWeight="800" textAnchor="middle" fontFamily="monospace">
          {clamped >= 0 ? '+' : ''}{clamped.toFixed(1)}
        </text>
        <text x={cx} y="94" fill={C.secondary} fontSize="10" textAnchor="middle" fontFamily="monospace" fontWeight="600">
          {regime} REGIME
        </text>
      </svg>
    </div>
  )
}

// ─── SVG Breadth Donut ────────────────────────────────────────────────────────

function BreadthDonut({ breadth }: { breadth: MarketContext['breadth'] | undefined }) {
  if (!breadth) return null

  const total = Object.values(breadth).reduce((a, b) => a + b, 0)
  const R = 44, cx = 65, cy = 65, SW = 22
  const circ = 2 * Math.PI * R

  const SEG_DEFS = [
    { key: 'bull_run',     label: 'BULL RUN',     color: '#22D35E', bg: '#052E14' },
    { key: 'emerging',     label: 'EMERGING',     color: '#0EC4A0', bg: '#023323' },
    { key: 'watchlist',    label: 'WATCHLIST',    color: '#4080FF', bg: '#0A1A3A' },
    { key: 'neutral',      label: 'NEUTRAL',      color: '#94A3B8', bg: '#161E2E' },
    { key: 'accumulation', label: 'ACCUMULATION', color: '#A78BFA', bg: '#1A0A2E' },
    { key: 'markdown',     label: 'MARKDOWN',     color: '#F44B4B', bg: '#2A0A0A' },
  ] as const

  // Pre-compute each segment's fraction and cumulative start position
  const segments = SEG_DEFS.map((def, i) => {
    const count = (breadth as Record<string, number>)[def.key] ?? 0
    const pct   = total > 0 ? count / total : 0
    const cumStart = SEG_DEFS.slice(0, i).reduce((s, d) => {
      return s + ((breadth as Record<string, number>)[d.key] ?? 0) / total
    }, 0)
    return { ...def, count, pct, cumStart }
  })

  return (
    <div style={{ ...CARD, padding: '20px', display: 'flex', flexDirection: 'column' }}>
      <div style={LABEL}>UNIVERSE BREADTH</div>
      <div style={{ display: 'flex', gap: 20, marginTop: 12, alignItems: 'center', flex: 1 }}>
        <svg viewBox="0 0 130 130" width={150} height={150} style={{ flexShrink: 0 }}>
          {/* Background track */}
          <circle cx={cx} cy={cy} r={R} fill="none"
            stroke="#1E2D44" strokeWidth={SW}
          />
          {segments.map(({ key, color, pct, cumStart }) => {
            if (pct < 0.001) return null
            // Gap between segments (only for non-tiny segments)
            const gap    = pct > 0.015 ? 2 : 0
            const dash   = Math.max(0.5, circ * pct - gap)
            // Correct SVG donut formula:
            // dashOffset = circ * (1 + pct - cumStart)
            // This places the start of the dash at the cumStart position of the circle.
            const dashOffset = circ * (1 + pct - cumStart)
            return (
              <circle key={key} cx={cx} cy={cy} r={R} fill="none"
                stroke={color} strokeWidth={SW}
                strokeDasharray={`${dash} ${circ}`}
                strokeDashoffset={dashOffset}
                transform={`rotate(-90 ${cx} ${cy})`}
                strokeLinecap="butt"
              />
            )
          })}
          {/* Center label */}
          <text x={cx} y={cy - 7} textAnchor="middle" fill={C.h1}
            fontSize="20" fontWeight="800" fontFamily="monospace">{total.toLocaleString()}</text>
          <text x={cx} y={cy + 8} textAnchor="middle" fill={C.muted}
            fontSize="9" fontFamily="monospace">STOCKS</text>
        </svg>

        {/* Legend — each segment links to the full list on the Watchlist page */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6, justifyContent: 'space-evenly', alignSelf: 'stretch' }}>
          {segments.map(({ key, label, color, bg, count, pct }) => {
            const pctStr = (pct * 100).toFixed(0)
            return (
              <Link key={key} to={`/watchlist?label=${key.toUpperCase()}`}
                title={`Open all ${count} ${label} stocks`}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  background: bg, borderRadius: 5, padding: '4px 8px',
                  textDecoration: 'none', border: '1px solid transparent',
                  transition: 'border-color 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = color + '66')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'transparent')}
              >
                <div style={{ width: 8, height: 8, borderRadius: 2, background: color, flexShrink: 0 }} />
                <span style={{ color: C.secondary, fontSize: 10, flex: 1, fontWeight: 600 }}>{label}</span>
                <span style={{ color, fontSize: 12, fontWeight: 800, fontFamily: 'monospace' }}>{count}</span>
                <span style={{ color: C.muted, fontSize: 9, minWidth: 26, textAlign: 'right' }}>{pctStr}%</span>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ─── Conviction + Cash Panel ──────────────────────────────────────────────────

function ConvictionPanel({ part, cash }: { part: ParticipantLatest; cash: MarketContext['cash_flows'] }) {
  const convBars = [
    { label: 'FII / FPI',  value: part.FII_conviction, color: C.fii, track: '#0A1A2E' },
    { label: 'DII / MF',   value: part.DII_conviction, color: C.dii, track: '#130D2A' },
  ]
  const flowBars = cash ? [
    { label: 'FPI/FII',    value: cash.fpi_5d_cr,       color: cash.fpi_5d_cr >= 0 ? C.bull : C.bear },
    { label: 'MF/DII',     value: cash.mf_5d_cr,        color: cash.mf_5d_cr >= 0 ? C.dii : C.bear },
    { label: 'Insurance',  value: cash.insurance_5d_cr,  color: cash.insurance_5d_cr >= 0 ? '#7C4DFF' : C.bear },
  ] : []
  const flowBars20 = cash ? [
    { label: 'FPI/FII',    value: cash.fpi_20d_cr,      color: cash.fpi_20d_cr >= 0 ? C.bull : C.bear },
    { label: 'MF/DII',     value: cash.mf_20d_cr,       color: cash.mf_20d_cr >= 0 ? C.dii : C.bear },
  ] : []
  const maxAbs   = Math.max(...flowBars.map(f => Math.abs(f.value)), 1000)
  const maxAbs20 = Math.max(...flowBars20.map(f => Math.abs(f.value)), 1000)

  return (
    <div style={{ ...CARD, padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={LABEL}>CONVICTION & CASH FLOWS</div>

      {convBars.map(({ label, value, color, track }) => (
        <div key={label}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ color: C.secondary, fontSize: 11, fontWeight: 600 }}>{label}</span>
            <span style={{ color, fontWeight: 800, fontSize: 15 }}>{value.toFixed(0)}%</span>
          </div>
          <div style={{ height: 10, background: track, borderRadius: 5, overflow: 'hidden', position: 'relative' }}>
            <div style={{
              height: '100%', width: `${Math.min(100, value)}%`,
              background: `linear-gradient(90deg, ${color}55, ${color})`,
              borderRadius: 5, transition: 'width 1.2s cubic-bezier(.4,0,.2,1)',
            }} />
            {/* 50% tick mark */}
            <div style={{ position: 'absolute', left: '50%', top: 0, height: '100%', width: 1, background: '#FFFFFF18' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3 }}>
            <span style={{ color: C.dim, fontSize: 9 }}>0%</span>
            <span style={{ color: C.dim, fontSize: 9 }}>50%</span>
            <span style={{ color: C.dim, fontSize: 9 }}>100%</span>
          </div>
        </div>
      ))}

      {/* 5D + 20D Net Cash Flows */}
      {([
        { title: '5-DAY NET CASH FLOWS',  bars: flowBars,   max: maxAbs   },
        { title: '20-DAY NET CASH FLOWS', bars: flowBars20, max: maxAbs20 },
      ]).map(({ title, bars, max }) => bars.length > 0 && (
        <div key={title} style={{ borderTop: `1px solid #1E2D44`, paddingTop: 12 }}>
          <div style={{ ...LABEL, marginBottom: 10 }}>{title}</div>
          {bars.map(({ label, value, color }) => {
            const pct = Math.min(100, Math.abs(value) / max * 100)
            return (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ color: C.secondary, fontSize: 10, fontWeight: 600, minWidth: 56 }}>{label}</span>
                <div style={{ flex: 1, height: 6, background: C.bgInner, borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3 }} />
                </div>
                <span style={{ color, fontSize: 10, fontWeight: 700, minWidth: 80, textAlign: 'right' }}>
                  {value >= 0 ? '+' : ''}{value.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr
                </span>
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

// ─── Participant Flow Bars ─────────────────────────────────────────────────────

function FlowBars({ flows, part, isMobile }: {
  flows: { FII: number; DII: number; PRO: number; CLIENT: number }
  part:  ParticipantLatest
  isMobile: boolean
}) {
  const fnoRows = [
    { key: 'FII',    score: flows.FII,    color: C.fii,    conv: part.FII_conviction, label: 'FII / FPI',  sub: 'Foreign Institutional' },
    { key: 'DII',    score: flows.DII,    color: C.dii,    conv: part.DII_conviction, label: 'DII / MF',   sub: 'Domestic Institutional' },
    { key: 'PRO',    score: flows.PRO,    color: C.pro,    conv: null,                label: 'PRO',         sub: 'Proprietary Desks' },
    { key: 'CLIENT', score: flows.CLIENT, color: C.client, conv: null,                label: 'CLIENT',      sub: 'Retail / HNI' },
  ]
  const cashRows = [
    { key: 'FPI',    score: part.FPI_flow_score,       color: C.fii,    conv: null, label: 'FPI',       sub: 'FII cash segment' },
    { key: 'MF',     score: part.MF_flow_score,        color: C.dii,    conv: null, label: 'MF',        sub: 'Mutual Funds' },
    { key: 'INS',    score: part.INSURANCE_flow_score, color: '#7C4DFF', conv: null, label: 'INSURANCE', sub: 'Insurance cos' },
    { key: 'RETAIL', score: part.RETAIL_flow_score,    color: C.client, conv: null, label: 'RETAIL',    sub: 'Retail cash' },
  ].filter(r => r.score != null && !Number.isNaN(r.score))
  const rows = [...fnoRows, ...cashRows]
  const maxAbs = Math.max(...rows.map(r => Math.abs(r.score)), 10)

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={LABEL}>PARTICIPANT FLOWS  <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(z-score, rolling)</span></div>
        <span style={{ color: C.dim, fontSize: 9, fontWeight: 600, letterSpacing: 0.5 }}>F&amp;O + CASH</span>
      </div>

      {rows.map(({ key, score, color, conv, label, sub }, ri) => {
        const pct = (Math.abs(score) / maxAbs) * 50  // max 50% of half-width
        const pos = score >= 0
        return (
          <div key={key} style={{
            display: 'grid', gridTemplateColumns: isMobile ? '80px 1fr 65px' : '130px 1fr 80px',
            alignItems: 'center', gap: isMobile ? 8 : 12, marginBottom: 14,
            ...(ri === fnoRows.length ? { borderTop: '1px solid #1E2D44', paddingTop: 14 } : {}),
          }}>
            {/* Label */}
            <div>
              <div style={{ color: C.primary, fontSize: 12, fontWeight: 700 }}>{label}</div>
              {!isMobile && <div style={{ color: C.muted, fontSize: 9 }}>{sub}</div>}
            </div>

            {/* Bidirectional bar */}
            <div style={{ position: 'relative', height: 24, background: C.bgInner, borderRadius: 6, overflow: 'hidden' }}>
              {/* Center line */}
              <div style={{ position: 'absolute', left: '50%', top: 0, height: '100%', width: 1, background: '#FFFFFF15', zIndex: 2 }} />
              {/* Main fill */}
              <div style={{
                position: 'absolute',
                [pos ? 'left' : 'right']: '50%',
                width: `${pct}%`,
                height: '100%',
                background: `linear-gradient(${pos ? '90deg' : '270deg'}, ${color}30, ${color}90)`,
                borderRadius: pos ? '0 4px 4px 0' : '4px 0 0 4px',
              }} />
              {/* Conviction overlay (brighter inner stripe) */}
              {conv != null && (
                <div style={{
                  position: 'absolute',
                  [pos ? 'left' : 'right']: '50%',
                  width: `${Math.min(conv / 2 * (pct / 50), pct)}%`,
                  top: '30%', height: '40%',
                  background: color,
                  borderRadius: 2,
                  opacity: 0.9,
                }} />
              )}
              {/* Score label inside bar */}
              <div style={{
                position: 'absolute',
                [pos ? 'left' : 'right']: `calc(50% + ${pct}% + 4px)`,
                top: '50%', transform: 'translateY(-50%)',
                color: C.dim, fontSize: 9, whiteSpace: 'nowrap',
                display: pct < 15 ? 'block' : 'none',
              }}>
                {score >= 0 ? '+' : ''}{score.toFixed(1)}
              </div>
            </div>

            {/* Value + conviction */}
            <div style={{ textAlign: 'right' }}>
              <div style={{ color, fontSize: 15, fontWeight: 800, fontFamily: 'monospace' }}>
                {score >= 0 ? '+' : ''}{score.toFixed(1)}
              </div>
              {conv != null && (
                <div style={{ color: C.muted, fontSize: 9 }}>{conv.toFixed(0)}% conv</div>
              )}
            </div>
          </div>
        )
      })}

      {/* Scale footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', paddingLeft: isMobile ? 88 : 142, paddingTop: 2 }}>
        <span style={{ color: C.dim, fontSize: 9 }}>— {maxAbs.toFixed(0)}</span>
        <span style={{ color: C.dim, fontSize: 9 }}>0</span>
        <span style={{ color: C.dim, fontSize: 9 }}>+{maxAbs.toFixed(0)}</span>
      </div>
    </div>
  )
}

// ─── Flow Interpretation (rescued from Participant page) ─────────────────────

function FlowInterpretation({ part }: { part: ParticipantLatest }) {
  const fii = part.FII_flow_score
  const dii = part.DII_flow_score
  const smart = part.Smart_Money_Score
  const retail = part.RETAIL_flow_score
  const divergence = part.FII_DII_Divergence

  const lines: { text: string; color: string }[] = []

  if (fii > 1 && dii > 1)
    lines.push({ text: 'FII + DII both accumulating — broad institutional conviction. Historically precedes sustained rally.', color: C.bull })
  else if (fii > 1 && dii < -1)
    lines.push({ text: 'FII buying while DII selling — foreign led rally. DII caution is a mild headwind; watch for confirmation.', color: C.neutral })
  else if (fii < -1 && dii > 1)
    lines.push({ text: 'FII exiting while DII absorbing — DII acting as last buyer. Typical pre-consolidation setup. Not a buy signal.', color: C.neutral })
  else if (fii < -1 && dii < -1)
    lines.push({ text: 'FII + DII both reducing — institutional distribution. High risk of further downside. Reduce exposure.', color: C.bear })
  else
    lines.push({ text: 'Flows are within normal range — no strong directional signal from institutional participants.', color: C.muted })

  if (Math.abs(divergence) > 2)
    lines.push({
      text: `FII/DII divergence at ${Math.abs(divergence).toFixed(1)}σ — extreme divergence. ${divergence < 0 ? 'FII pressure dominant; short-term weakness likely.' : 'DII pressure; possible base forming.'}`,
      color: '#8B5CF6',
    })

  if (smart > 1 && (retail ?? 0) < -1)
    lines.push({ text: 'Smart money buying while retail exits — classic accumulation pattern. Bullish for 15–45 days.', color: C.bull })
  if (smart < -1 && (retail ?? 0) > 1)
    lines.push({ text: 'Smart money selling into retail buying — distribution. High reversal risk.', color: C.bear })

  return (
    <div style={{ ...CARD, padding: '20px', display: 'flex', flexDirection: 'column', flex: 1 }}>
      <div style={{ ...LABEL, marginBottom: 14 }}>FLOW INTERPRETATION</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {lines.map((l, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
            <span style={{ color: l.color, flexShrink: 0, fontSize: 10, marginTop: 2 }}>&#9679;</span>
            <span style={{ color: l.color, fontSize: 12, lineHeight: 1.55 }}>{l.text}</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 'auto', paddingTop: 14, color: C.dim, fontSize: 9 }}>
        Data date: {part.date} &middot; z-scores vs 60D window
      </div>
    </div>
  )
}

// ─── Participant History (rescued from Participant page) ─────────────────────

const PERIOD_OPTIONS = [
  { label: '30D',  days: 30  },
  { label: '90D',  days: 90  },
  { label: '180D', days: 180 },
  { label: '1Y',   days: 252 },
]

function ParticipantHistory({ isMobile }: { isMobile: boolean }) {
  const [period, setPeriod] = useState(90)
  const { data: history } = useQuery({
    queryKey: ['participant-history', 252],
    queryFn:  () => fetchParticipantHistory(252),
    refetchInterval: 300_000,
  })

  const chartData = (history?.rows ?? []).slice(-period)
  if (chartData.length === 0) return null
  const hasCash = chartData[0] && 'FPI_flow_5D' in chartData[0]

  return (
    <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'column', gap: 14, height: '100%' }}>
      {/* FII vs DII flow score history */}
      <div style={{ ...CARD, padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', minHeight: 240 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={LABEL}>FII vs DII FLOW SCORE</div>
          <div style={{ display: 'flex', gap: 6 }}>
            {PERIOD_OPTIONS.map(o => (
              <button
                key={o.label} onClick={() => setPeriod(o.days)}
                style={{
                  padding: '3px 10px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                  border: `1px solid ${period === o.days ? C.bull : '#1E2D44'}`,
                  background: 'transparent', color: period === o.days ? C.bull : C.muted,
                }}
              >{o.label}</button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height="100%" minHeight={170}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="dash-fii" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#22C55E" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="dash-dii" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748B' }} tickLine={false} axisLine={false} interval={Math.floor(period / 6)} />
            <YAxis tick={{ fontSize: 9, fill: '#64748B' }} tickLine={false} axisLine={false} />
            <ReferenceLine y={0} stroke="#1E2D44" strokeDasharray="3 3" />
            <Tooltip contentStyle={{ backgroundColor: '#141720', border: '1px solid #1E2332', fontSize: 11 }} labelStyle={{ color: '#64748B' }} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Area type="monotone" dataKey="FII_flow_score" name="FII (F&O)" stroke="#22C55E" fill="url(#dash-fii)" strokeWidth={1.5} dot={false} />
            <Area type="monotone" dataKey="DII_flow_score" name="DII (F&O)" stroke="#3B82F6" fill="url(#dash-dii)" strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* FPI vs MF rolling cash flows */}
      {hasCash && (
        <div style={{ ...CARD, padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', minHeight: 240 }}>
          <div style={{ ...LABEL, marginBottom: 12 }}>FPI vs MF CASH (5D ROLLING, Cr)</div>
          <ResponsiveContainer width="100%" height="100%" minHeight={170}>
            <BarChart data={chartData.slice(-60)} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748B' }} tickLine={false} axisLine={false} interval={9} />
              <YAxis tick={{ fontSize: 9, fill: '#64748B' }} tickLine={false} axisLine={false} />
              <ReferenceLine y={0} stroke="#334155" />
              <Tooltip contentStyle={{ backgroundColor: '#141720', border: '1px solid #1E2332', fontSize: 11 }} labelStyle={{ color: '#64748B' }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="FPI_flow_5D" name="FPI (FII Cash)" fill="#22C55E" opacity={0.8} />
              <Bar dataKey="MF_flow_5D"  name="MF (DII Cash)"  fill="#3B82F6" opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

// ─── Sector Heatmap ───────────────────────────────────────────────────────────

const SIG: Record<string, { bg: string; glow: string; badge: string; text: string }> = {
  STRONG_ACCUMULATION: { bg: '#061A0E', glow: '#22D35E40', badge: '#0A3320', text: C.bull },
  EARLY_ROTATION:      { bg: '#041A10', glow: '#10B98140', badge: '#083320', text: '#10B981' },
  PRICE_LED:           { bg: '#040E22', glow: '#3BAEF040', badge: '#071830', text: C.fii },
  NEUTRAL:             { bg: '#0E1420', glow: 'transparent', badge: '#131B2E', text: '#64748B' },
  DISTRIBUTION:        { bg: '#1A0408', glow: '#F44B4B30', badge: '#2A0608', text: C.bear },
}

const SECTORS_VISIBLE = 10   // 5 cols x 2 rows before expanding

function SectorHeatmap({ sectors, isMobile }: { sectors: Sector[]; isMobile: boolean }) {
  const [expanded, setExpanded] = useState(false)

  // Strongest cross-sectional rotation candidates first; nulls last
  const sorted = [...sectors].sort((a, b) =>
    (b.relative_score ?? -Infinity) - (a.relative_score ?? -Infinity))
  const visible = expanded ? sorted : sorted.slice(0, SECTORS_VISIBLE)

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div style={LABEL}>SECTOR CAPITAL ROTATION  <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(top {expanded ? sectors.length : Math.min(SECTORS_VISIBLE, sectors.length)} of {sectors.length} by relative score)</span></div>
        <Link to="/sectors" style={{ color: C.blue, fontSize: 11, textDecoration: 'none', fontWeight: 600 }}>Full View →</Link>
      </div>

      {/* Signal legend */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 14, flexWrap: 'wrap' }}>
        {Object.entries(SIG).map(([sig, st]) => (
          <div key={sig} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: st.text, opacity: 0.9 }} />
            <span style={{ color: C.muted, fontSize: 9, fontWeight: 600 }}>{sig.replace(/_/g, ' ')}</span>
          </div>
        ))}
      </div>

      {/* Grid — 5 cols desktop / 2 cols mobile */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(5, 1fr)', gap: 6 }}>
        {visible.map(s => {
          const st  = SIG[s.rotation_signal] ?? SIG['NEUTRAL']
          const rel = s.relative_score   // cross-sectional ±100
          const z   = s.combined_score   // z-score vs 252D baseline
          const relColor = rel != null ? (rel >= 0 ? C.bull : C.bear) : C.muted
          const zColor   = z   != null ? (z   >= 0 ? C.bull : C.bear) : C.muted
          return (
            <Link key={s.sector} to={`/sectors/${s.sector}`} style={{ textDecoration: 'none' }}>
              <div style={{
                background: st.bg,
                border: `1px solid ${st.text}33`,
                boxShadow: st.glow !== 'transparent' ? `0 0 12px ${st.glow}` : 'none',
                borderRadius: 7, padding: '10px 12px',
                transition: 'all 0.18s', cursor: 'pointer',
              }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = `${st.text}88`; e.currentTarget.style.transform = 'translateY(-1px)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = `${st.text}33`; e.currentTarget.style.transform = 'none' }}
              >
                {/* Sector name */}
                <div style={{ color: C.h1, fontSize: FS.body, fontWeight: FW.heavy, marginBottom: 7 }}>
                  {s.sector.replace(/_/g, ' ')}
                </div>

                {/* Two scores side by side */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 7 }}>
                  {/* Relative Rank */}
                  <div style={{
                    flex: 1, background: '#ffffff08', borderRadius: 5, padding: '5px 7px',
                    borderLeft: `2px solid ${relColor}`,
                  }}>
                    <div style={{ color: relColor, fontSize: FS.lg, fontWeight: FW.black, fontFamily: 'monospace', lineHeight: 1 }}>
                      {rel != null ? (rel >= 0 ? '+' : '') + rel.toFixed(0) : '--'}
                    </div>
                    <div style={{ color: C.muted, fontSize: FS.caption, fontWeight: FW.bold, letterSpacing: 0.8, marginTop: 3 }}>
                      RELATIVE
                    </div>
                  </div>

                  {/* Z-Score */}
                  <div style={{
                    flex: 1, background: '#ffffff08', borderRadius: 5, padding: '5px 7px',
                    borderLeft: `2px solid ${zColor}55`,
                  }}>
                    <div style={{ color: zColor, fontSize: FS.lg, fontWeight: FW.black, fontFamily: 'monospace', lineHeight: 1 }}>
                      {z != null ? (z >= 0 ? '+' : '') + z.toFixed(1) : '--'}
                    </div>
                    <div style={{ color: C.muted, fontSize: FS.caption, fontWeight: FW.bold, letterSpacing: 0.8, marginTop: 3 }}>
                      Z-SCORE
                    </div>
                  </div>
                </div>

                {/* Signal badge */}
                <div style={{
                  display: 'inline-block',
                  background: st.badge, color: st.text,
                  fontSize: FS.caption, fontWeight: FW.bold,
                  padding: '2px 7px', borderRadius: 3, letterSpacing: 0.6,
                }}>
                  {s.rotation_signal.replace(/_/g, ' ')}
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      {/* Expand / collapse */}
      {sectors.length > SECTORS_VISIBLE && (
        <div style={{ textAlign: 'center', marginTop: 12 }}>
          <button onClick={() => setExpanded(v => !v)} style={{
            background: 'transparent', border: `1px solid #1E2D44`, borderRadius: 5,
            color: C.blue, fontSize: 10, fontWeight: 700, padding: '5px 18px',
            cursor: 'pointer', letterSpacing: 0.5,
          }}>
            {expanded ? 'SHOW TOP 10' : `SHOW ALL ${sectors.length} SECTORS`}
          </button>
        </div>
      )}
    </div>
  )
}

// ─── Catalysts + Institutional Deals row ─────────────────────────────────────

function CatalystsCard({ catalysts }: {
  catalysts: { catalysts: Record<string, unknown>[]; count: number } | undefined
}) {
  const rows = (catalysts?.catalysts ?? []).slice(0, 8)
  return (
    <div style={{ ...CARD, padding: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={LABEL}>UPCOMING CATALYSTS</div>
        <Link to="/corporate" style={{ color: C.blue, fontSize: 10, textDecoration: 'none', fontWeight: 600 }}>All →</Link>
      </div>
      {rows.length === 0 && (
        <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '12px 0' }}>No upcoming events</div>
      )}
      {rows.map((c, i) => {
        const cat = c as Record<string, unknown>
        const symbol  = String(cat.symbol ?? '')
        const dateStr = String(cat.event_date ?? '')
        const score   = Number(cat.catalyst_score ?? NaN)
        return (
          <Link key={i} to={`/stocks/${symbol}`} style={{ textDecoration: 'none' }}>
            <div style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: `1px solid #1E2D44`, alignItems: 'center' }}
              onMouseEnter={e => (e.currentTarget.style.paddingLeft = '4px')}
              onMouseLeave={e => (e.currentTarget.style.paddingLeft = '0')}
            >
              <div style={{
                flexShrink: 0, background: '#1A1508', border: '1px solid #F5A52455',
                borderRadius: 5, padding: '4px 7px', textAlign: 'center', minWidth: 34,
              }}>
                <div style={{ color: C.neutral, fontSize: 11, fontWeight: 800, lineHeight: 1 }}>{dateStr.slice(8)}</div>
                <div style={{ color: C.muted, fontSize: 8, marginTop: 1 }}>{dateStr.slice(5, 7)}</div>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: C.primary, fontSize: 12, fontWeight: 700 }}>{symbol}</div>
                <div style={{ color: C.muted, fontSize: 9, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {String(cat.purpose_type ?? cat.purpose ?? '').replace(/_/g, ' ')}
                </div>
              </div>
              {Number.isFinite(score) && (
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ color: C.neutral, fontSize: 12, fontWeight: 800, fontFamily: 'monospace' }}>{score.toFixed(0)}</div>
                  <div style={{ color: C.dim, fontSize: 8 }}>CATALYST</div>
                </div>
              )}
            </div>
          </Link>
        )
      })}
    </div>
  )
}

function DealsCard({ deals }: {
  deals: { deals: Record<string, unknown>[]; count: number } | undefined
}) {
  const rows = (deals?.deals ?? []).slice(0, 8)
  return (
    <div style={{ ...CARD, padding: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={LABEL}>INSTITUTIONAL DEALS <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(30D net)</span></div>
        <Link to="/corporate" style={{ color: C.blue, fontSize: 10, textDecoration: 'none', fontWeight: 600 }}>All →</Link>
      </div>
      {rows.length === 0 && (
        <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '12px 0' }}>No significant deals</div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', columnGap: 28 }}>
      {rows.map((d, i) => {
        const deal   = d as Record<string, unknown>
        const symbol = String(deal.symbol ?? '')
        const cr     = Number(deal.inst_net_value_cr ?? 0)
        const signal = String(deal.deal_signal ?? '')
        const accum  = signal.includes('ACCUMULATION')
        const sigColor = accum ? C.bull : signal.includes('DISTRIBUTION') ? C.bear : C.muted
        return (
          <Link key={i} to={`/stocks/${symbol}`} style={{ textDecoration: 'none' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 0', borderBottom: `1px solid #1E2D44` }}
              onMouseEnter={e => (e.currentTarget.style.paddingLeft = '4px')}
              onMouseLeave={e => (e.currentTarget.style.paddingLeft = '0')}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: C.primary, fontSize: 12, fontWeight: 700 }}>{symbol}</span>
                  {signal && (
                    <span style={{
                      fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                      background: `${sigColor}18`, color: sigColor, border: `1px solid ${sigColor}44`,
                      whiteSpace: 'nowrap',
                    }}>{signal.replace('INSTITUTIONAL_', '').replace(/_/g, ' ')}</span>
                  )}
                </div>
                <div style={{ color: C.muted, fontSize: 9, marginTop: 2 }}>
                  {String(deal.inst_deals ?? '')} inst deals &middot; dominant: {String(deal.dominant_participant ?? '--')}
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{ color: cr >= 0 ? C.bull : C.bear, fontSize: 12, fontWeight: 800, fontFamily: 'monospace' }}>
                  {cr >= 0 ? '+' : ''}{cr.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr
                </div>
                <div style={{ color: C.dim, fontSize: 9 }}>last {String(deal.last_deal_date ?? '').slice(5)}</div>
              </div>
            </div>
          </Link>
        )
      })}
      </div>
    </div>
  )
}

// ─── Social Pulse Ticker ─────────────────────────────────────────────────────

const CAT_ACCENT: Record<string, string> = {
  INDIA_GOVT:      '#10B981',   // emerald  — Indian ministers
  INDIA_REGULATOR: '#3B82F6',   // blue     — SEBI / RBI
  G20_LEADER:      '#F59E0B',   // amber    — G20 heads of state
  MULTILATERAL:    '#6366F1',   // indigo   — IMF / World Bank
  GEOPOLITICAL:    '#EF4444',   // red      — NATO / conflict
}

const CAT_LABEL: Record<string, string> = {
  INDIA_GOVT:      'INDIA GOVT',
  INDIA_REGULATOR: 'REGULATOR',
  G20_LEADER:      'G20 LEADER',
  MULTILATERAL:    'MULTILATERAL',
  GEOPOLITICAL:    'GEOPOLITICAL',
}

const SENT_DOT: Record<string, string> = {
  POSITIVE: '#22D35E',
  NEGATIVE: '#F44B4B',
  NEUTRAL:  '#64748B',
}

function HandleCard({ h }: { h: SocialPulseHandle }) {
  const accent   = CAT_ACCENT[h.category] ?? '#64748B'
  const catLabel = CAT_LABEL[h.category] ?? h.category

  return (
    <div style={{
      flexShrink: 0,
      width: 260,
      height: 210,
      background: C.bg,
      border: `1px solid ${accent}28`,
      borderLeft: `3px solid ${accent}`,
      borderRadius: 8,
      padding: '11px 13px',
      display: 'flex',
      flexDirection: 'column',
      gap: 7,
      boxSizing: 'border-box',
    }}>
      {/* Header: avatar + name + X badge + category */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{
          flexShrink: 0,
          width: 34, height: 34, borderRadius: 6,
          background: `${accent}18`,
          border: `1px solid ${accent}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: accent, fontSize: 8, fontWeight: 900, letterSpacing: 0.2,
          textAlign: 'center', lineHeight: 1.1,
        }}>{h.avatar}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            color: C.h1, fontSize: 11, fontWeight: 800,
            overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis',
          }}>{h.display_name}</div>
          <div style={{ display: 'flex', gap: 5, marginTop: 2, alignItems: 'center' }}>
            {/* X (Twitter) icon marker */}
            <span style={{
              fontSize: 7, fontWeight: 900, color: '#fff',
              background: '#000', borderRadius: 3, padding: '1px 3px', lineHeight: 1.4,
            }}>X</span>
            <span style={{ color: accent, fontSize: 8, fontWeight: 700 }}>{h.handle}</span>
          </div>
        </div>
        <span style={{
          flexShrink: 0,
          fontSize: 7, fontWeight: 800, padding: '2px 5px', borderRadius: 3,
          background: `${accent}14`, color: accent, border: `1px solid ${accent}3A`,
          letterSpacing: 0.4, whiteSpace: 'nowrap',
        }}>{catLabel}</span>
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: `${accent}1A` }} />

      {/* Tweet list */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {h.items.slice(0, 3).map((it, i) => (
          <a
            key={i}
            href={it.url || undefined}
            target={it.url ? '_blank' : undefined}
            rel="noopener noreferrer"
            style={{ textDecoration: 'none', display: 'flex', gap: 6, alignItems: 'flex-start' }}
          >
            {/* Impact + sentiment dot */}
            <div style={{
              flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
              marginTop: 2,
            }}>
              <div style={{
                width: 5, height: 5, borderRadius: '50%',
                background: SENT_DOT[it.sentiment] ?? '#64748B',
              }} />
              {it.impact_score >= 3 && (
                <div style={{
                  width: 5, height: 3, borderRadius: 1,
                  background: it.sentiment === 'NEGATIVE' ? '#EF4444' : '#10B981',
                  opacity: 0.7,
                }} />
              )}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                color: it.url ? C.primary : C.secondary,
                fontSize: 10, lineHeight: 1.38,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}>{it.title}</div>
              <div style={{ color: C.dim, fontSize: 8, marginTop: 1 }}>{it.published_rel} ago</div>
            </div>
          </a>
        ))}
        {h.items.length === 0 && (
          <div style={{ color: C.dim, fontSize: 10, marginTop: 6, fontStyle: 'italic' }}>
            No market-impacting tweets
          </div>
        )}
      </div>
    </div>
  )
}

function SocialPulse() {
  const [paused, setPaused] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['social-pulse'],
    queryFn:  fetchSocialPulse,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 5 * 60 * 1000,
  })

  const handles = (data?.handles ?? []).filter(h => h.item_count > 0)
  // Duplicate for seamless loop — need at least enough to fill viewport twice
  const track   = handles.length > 0 ? [...handles, ...handles, ...handles] : []
  const duration = Math.max(40, handles.length * 7)  // seconds

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <style>{`
        @keyframes pulse-scroll {
          0%   { transform: translateX(0) }
          100% { transform: translateX(calc(-100% / 3)) }
        }
        .pulse-track {
          animation: pulse-scroll ${duration}s linear infinite;
          will-change: transform;
        }
        .pulse-track.paused { animation-play-state: paused; }
      `}</style>

      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={LABEL}>X INTELLIGENCE TICKER</div>
          {/* Live dot */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{
              width: 6, height: 6, borderRadius: 3,
              background: '#22D35E',
              boxShadow: '0 0 6px #22D35E',
              animation: 'none',
            }} />
            <span style={{ color: '#22D35E', fontSize: 9, fontWeight: 700 }}>LIVE</span>
          </div>
          {data && (
            <span style={{ color: C.dim, fontSize: 9 }}>
              {data.active}/{data.total} sources
            </span>
          )}
        </div>
        <button
          onClick={() => setPaused(v => !v)}
          style={{
            background: 'transparent', border: `1px solid #1E2D44`,
            borderRadius: 5, color: paused ? C.bull : C.muted,
            fontSize: 9, fontWeight: 700, padding: '3px 10px', cursor: 'pointer',
          }}
        >{paused ? 'RESUME' : 'PAUSE'}</button>
      </div>

      {/* Scrolling track — pauses on hover */}
      <div
        style={{ overflow: 'hidden', position: 'relative' }}
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        {/* Fade edges */}
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0, width: 40,
          background: `linear-gradient(90deg, ${C.bg}, transparent)`,
          zIndex: 2, pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', right: 0, top: 0, bottom: 0, width: 40,
          background: `linear-gradient(270deg, ${C.bg}, transparent)`,
          zIndex: 2, pointerEvents: 'none',
        }} />

        {isLoading ? (
          <div style={{ display: 'flex', gap: 8 }}>
            {[...Array(5)].map((_, i) => (
              <div key={i} style={{
                flexShrink: 0, width: 230, height: 188,
                background: C.bg, border: `1px solid #1E2D44`, borderRadius: 8,
                opacity: 0.5,
              }} />
            ))}
          </div>
        ) : (
          <div
            className={`pulse-track${paused ? ' paused' : ''}`}
            style={{ display: 'flex', gap: 8, width: 'max-content' }}
          >
            {track.map((h, i) => (
              <HandleCard key={`${h.handle}-${i}`} h={h} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── News Section ─────────────────────────────────────────────────────────────

const SENT_STYLE: Record<string, React.CSSProperties> = {
  POSITIVE: { background: '#061A0E', color: '#22D35E', border: '1px solid #22D35E44' },
  NEGATIVE: { background: '#1A0408', color: '#F44B4B', border: '1px solid #F44B4B44' },
  NEUTRAL:  { background: '#0E1420', color: '#64748B', border: '1px solid #1E2D44'   },
}
const CAT_COLOR: Record<string, string> = {
  EQUITIES:    '#3BAEF0',
  MACRO:       '#F5A524',
  COMMODITIES: '#C668E8',
  FOREX:       '#22D35E',
  FLOWS:       '#60A5FA',
  EARNINGS:    '#FB923C',
  IPO:         '#E879F9',
  CRYPTO:      '#FACC15',
  OTHER:       '#64748B',
}

function _relTime(ts: number): string {
  const diff = Math.floor(Date.now() / 1000) - ts
  if (diff < 60)   return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400)return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

const ALL_CATS = ['ALL', 'EQUITIES', 'MACRO', 'FLOWS', 'EARNINGS', 'COMMODITIES', 'FOREX', 'IPO', 'OTHER']

function NewsCard({ item }: { item: NewsItem }) {
  const catColor = CAT_COLOR[item.category] ?? '#64748B'
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{ textDecoration: 'none', display: 'block' }}
    >
      <div style={{
        ...CARD,
        padding: '14px',
        display: 'flex', flexDirection: 'column', gap: 8,
        transition: 'all 0.18s', height: '100%', boxSizing: 'border-box',
      }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = '#2D4A6B'; e.currentTarget.style.boxShadow = '0 4px 16px #0008'; e.currentTarget.style.transform = 'translateY(-1px)' }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = '#1E2D44'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none' }}
      >
        {/* Top meta row */}
        <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{
            fontSize: 8, fontWeight: 700, padding: '2px 5px', borderRadius: 3,
            background: '#0A1628', color: C.blue, border: `1px solid ${C.blue}44`,
            textTransform: 'uppercase', letterSpacing: 0.5, whiteSpace: 'nowrap',
          }}>{item.source}</span>
          <span style={{
            fontSize: 8, fontWeight: 700, padding: '2px 5px', borderRadius: 3,
            background: item.region === 'INDIA' ? '#0A1A08' : '#040E22',
            color: item.region === 'INDIA' ? '#22D35E' : '#3BAEF0',
            border: `1px solid ${item.region === 'INDIA' ? '#22D35E' : '#3BAEF0'}44`,
          }}>{item.region}</span>
          <span style={{
            fontSize: 8, fontWeight: 700, padding: '2px 5px', borderRadius: 3,
            background: `${catColor}14`, color: catColor, border: `1px solid ${catColor}44`,
          }}>{item.category}</span>
        </div>

        {/* Headline */}
        <div style={{
          color: C.h1, fontSize: 12, fontWeight: 700, lineHeight: 1.45,
          display: '-webkit-box',
          WebkitLineClamp: 3,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          flex: 1,
        }}>{item.title}</div>

        {/* Bottom row: sentiment + time + link icon */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{
            fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 3,
            ...SENT_STYLE[item.sentiment],
          }}>{item.sentiment}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ color: C.dim, fontSize: 9 }}>{_relTime(item.published_ts)}</span>
            <svg width="10" height="10" viewBox="0 0 12 12" fill="none" style={{ opacity: 0.4 }}>
              <path d="M5 2H2a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V7M8 1h3m0 0v3m0-3L5.5 6.5" stroke={C.muted} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>
      </div>
    </a>
  )
}

function NewsSection() {
  const [cat, setCat]         = useState('ALL')
  const [region, setRegion]   = useState<'ALL'|'INDIA'|'GLOBAL'>('ALL')
  const [showAll, setShowAll] = useState(false)

  const { data, isLoading, refetch, dataUpdatedAt } = useQuery({
    queryKey: ['news'],
    queryFn:  fetchNews,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 5 * 60 * 1000,
  })

  const items = data?.items ?? []
  const filtered = items.filter(it =>
    (cat === 'ALL'    || it.category === cat) &&
    (region === 'ALL' || it.region === region),
  )
  const displayed = showAll ? filtered : filtered.slice(0, 12)

  const cacheAge = data?.cached_at
    ? Math.round((Date.now() / 1000 - data.cached_at) / 60)
    : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={LABEL}>MARKET NEWS &amp; INTELLIGENCE</div>
          {cacheAge !== null && (
            <span style={{ color: C.dim, fontSize: 9 }}>
              cached {cacheAge}m ago
            </span>
          )}
        </div>
        <button
          onClick={() => refetch()}
          style={{
            background: 'transparent', border: `1px solid #1E2D44`, borderRadius: 5,
            color: C.blue, fontSize: 10, fontWeight: 600, padding: '4px 10px',
            cursor: 'pointer',
          }}
        >Refresh</button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Region */}
        {(['ALL', 'INDIA', 'GLOBAL'] as const).map(r => (
          <button key={r} onClick={() => setRegion(r)} style={{
            background: region === r ? '#1E3A5F' : 'transparent',
            border: `1px solid ${region === r ? '#3BAEF0' : '#1E2D44'}`,
            borderRadius: 4, color: region === r ? C.blue : C.muted,
            fontSize: 9, fontWeight: 700, padding: '3px 8px', cursor: 'pointer',
            letterSpacing: 0.5,
          }}>{r}</button>
        ))}
        <div style={{ width: 1, height: 14, background: '#1E2D44', margin: '0 2px' }} />
        {/* Category */}
        {ALL_CATS.map(c => (
          <button key={c} onClick={() => setCat(c)} style={{
            background: cat === c ? `${CAT_COLOR[c] ?? '#3BAEF0'}22` : 'transparent',
            border: `1px solid ${cat === c ? (CAT_COLOR[c] ?? '#3BAEF0') + '66' : '#1E2D44'}`,
            borderRadius: 4,
            color: cat === c ? (CAT_COLOR[c] ?? C.blue) : C.muted,
            fontSize: 9, fontWeight: 700, padding: '3px 8px', cursor: 'pointer',
            letterSpacing: 0.3,
          }}>{c}</button>
        ))}
      </div>

      {/* Grid */}
      {isLoading ? (
        <div style={{ ...CARD, padding: 32, textAlign: 'center', color: C.dim, fontSize: 12 }}>
          Fetching news from global sources...
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ ...CARD, padding: 32, textAlign: 'center', color: C.dim, fontSize: 12 }}>
          No news items available for the selected filter.
        </div>
      ) : (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: 8,
          }}>
            {displayed.map((it, i) => <NewsCard key={`${it.url}-${i}`} item={it} />)}
          </div>
          {filtered.length > 12 && (
            <div style={{ textAlign: 'center' }}>
              <button onClick={() => setShowAll(v => !v)} style={{
                background: 'transparent', border: `1px solid #1E2D44`, borderRadius: 5,
                color: C.blue, fontSize: 11, fontWeight: 600, padding: '6px 20px', cursor: 'pointer',
              }}>
                {showAll ? 'Show less' : `Show all ${filtered.length} articles`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export function Dashboard() {
  const isMobile = useMobile()

  const { data: ctx }       = useQuery({ queryKey: ['market-context'],    queryFn: fetchMarketContext,    refetchInterval: 300_000 })
  const { data: part }      = useQuery({ queryKey: ['participant-latest'], queryFn: fetchParticipantLatest, refetchInterval: 300_000 })
  const { data: sectors }   = useQuery({ queryKey: ['sectors'],            queryFn: fetchSectors,           refetchInterval: 300_000 })
  const { data: catalysts } = useQuery({ queryKey: ['catalysts'],          queryFn: fetchCatalysts,         refetchInterval: 600_000 })
  const { data: deals }     = useQuery({ queryKey: ['deals-dash'],         queryFn: () => fetchDeals(10, 8), refetchInterval: 600_000 })

  const allSectors = sectors?.sectors ?? []
  const flows      = ctx?.flow_scores

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* Row 1: Command Strip */}
      {ctx && <CommandStrip ctx={ctx} part={part} isMobile={isMobile} />}

      {/* Row 1B: Recently Asked (Phase V-DATA-3) -- purely additive, never
          reorders any ranked list */}
      <RecentlyAskedCard />

      {/* Row 2: Regime + interpretation stack | Breadth | Conviction & Cash */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 14, alignItems: 'stretch' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {ctx ? <RegimeDial score={ctx.smart_money_score ?? 0} regime={ctx.regime} /> : (
            <div style={{ ...CARD, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: C.dim }}>Loading…</span>
            </div>
          )}
          {part && <FlowInterpretation part={part} />}
        </div>
        <BreadthDonut breadth={ctx?.breadth} />
        {part && ctx ? <ConvictionPanel part={part} cash={ctx.cash_flows} /> : (
          <div style={{ ...CARD, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: C.dim }}>Loading…</span>
          </div>
        )}
      </div>

      {/* Row 3: Participant Flow Bars | history charts stacked beside them */}
      {flows && part && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.15fr 1fr', gap: 14, alignItems: 'stretch' }}>
          <FlowBars flows={flows} part={part} isMobile={isMobile} />
          <ParticipantHistory isMobile={isMobile} />
        </div>
      )}

      {/* Row 4: Sector Rotation — full width, top 10 + expand */}
      {allSectors.length > 0 && <SectorHeatmap sectors={allSectors} isMobile={isMobile} />}

      {/* Row 5: Catalysts + Institutional Deals */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 2fr', gap: 14, alignItems: 'start' }}>
        <CatalystsCard catalysts={catalysts} />
        <DealsCard deals={deals} />
      </div>

      {/* Row 7: Intelligence Ticker */}
      <SocialPulse />

      {/* Row 8: News Section */}
      <NewsSection />
    </div>
  )
}
