/**
 * Dashboard — Professional infographic redesign
 * Design system: high-contrast text, rich navy card palette, visual data encoding
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  fetchMarketContext, fetchParticipantLatest, fetchSectors,
  fetchWatchlist, fetchCatalysts, fetchDeals,
  type MarketContext, type ParticipantLatest, type Sector,
} from '../api/client'
import { ScoreGauge }   from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
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
            <div key={k} style={{ textAlign: 'center' }}>
              <div style={{ color: col, fontSize: 18, fontWeight: 800, lineHeight: 1 }}>
                {ctx.breadth![k as keyof typeof ctx.breadth]}
              </div>
              <div style={{ color: C.muted, fontSize: 9, marginTop: 3 }}>{l}</div>
            </div>
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
      <svg viewBox="0 0 240 130" width="100%" style={{ display: 'block', margin: '8px auto 0' }}>
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
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={LABEL}>UNIVERSE BREADTH</div>
      <div style={{ display: 'flex', gap: 20, marginTop: 12, alignItems: 'center' }}>
        <svg viewBox="0 0 130 130" width={130} height={130} style={{ flexShrink: 0 }}>
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

        {/* Legend */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {segments.map(({ key, label, color, bg, count, pct }) => {
            const pctStr = (pct * 100).toFixed(0)
            return (
              <div key={key} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: bg, borderRadius: 5, padding: '4px 8px',
              }}>
                <div style={{ width: 8, height: 8, borderRadius: 2, background: color, flexShrink: 0 }} />
                <span style={{ color: C.secondary, fontSize: 10, flex: 1, fontWeight: 600 }}>{label}</span>
                <span style={{ color, fontSize: 12, fontWeight: 800, fontFamily: 'monospace' }}>{count}</span>
                <span style={{ color: C.muted, fontSize: 9, minWidth: 26, textAlign: 'right' }}>{pctStr}%</span>
              </div>
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
  const maxAbs = Math.max(...flowBars.map(f => Math.abs(f.value)), 1000)

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

      {/* 5D Net Cash Flows */}
      {flowBars.length > 0 && (
        <div style={{ borderTop: `1px solid #1E2D44`, paddingTop: 12 }}>
          <div style={{ ...LABEL, marginBottom: 10 }}>5-DAY NET CASH FLOWS</div>
          {flowBars.map(({ label, value, color }) => {
            const pct = Math.min(100, Math.abs(value) / maxAbs * 100)
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
      )}
    </div>
  )
}

// ─── Participant Flow Bars ─────────────────────────────────────────────────────

function FlowBars({ flows, part, isMobile }: {
  flows: { FII: number; DII: number; PRO: number; CLIENT: number }
  part:  ParticipantLatest
  isMobile: boolean
}) {
  const maxAbs = Math.max(...Object.values(flows).map(Math.abs), 10)
  const rows = [
    { key: 'FII',    score: flows.FII,    color: C.fii,    conv: part.FII_conviction, label: 'FII / FPI',  sub: 'Foreign Institutional' },
    { key: 'DII',    score: flows.DII,    color: C.dii,    conv: part.DII_conviction, label: 'DII / MF',   sub: 'Domestic Institutional' },
    { key: 'PRO',    score: flows.PRO,    color: C.pro,    conv: null,                label: 'PRO',         sub: 'Proprietary Desks' },
    { key: 'CLIENT', score: flows.CLIENT, color: C.client, conv: null,                label: 'CLIENT',      sub: 'Retail / HNI' },
  ]

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={LABEL}>F&amp;O PARTICIPANT FLOWS  <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(z-score, rolling)</span></div>
        <Link to="/participant" style={{ color: C.blue, fontSize: 11, textDecoration: 'none', fontWeight: 600 }}>Full Analysis →</Link>
      </div>

      {rows.map(({ key, score, color, conv, label, sub }) => {
        const pct = (Math.abs(score) / maxAbs) * 50  // max 50% of half-width
        const pos = score >= 0
        return (
          <div key={key} style={{ display: 'grid', gridTemplateColumns: isMobile ? '80px 1fr 65px' : '130px 1fr 80px', alignItems: 'center', gap: isMobile ? 8 : 12, marginBottom: 14 }}>
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

// ─── Sector Heatmap ───────────────────────────────────────────────────────────

const SIG: Record<string, { bg: string; glow: string; badge: string; text: string }> = {
  STRONG_ACCUMULATION: { bg: '#061A0E', glow: '#22D35E40', badge: '#0A3320', text: C.bull },
  EARLY_ROTATION:      { bg: '#041A10', glow: '#10B98140', badge: '#083320', text: '#10B981' },
  PRICE_LED:           { bg: '#040E22', glow: '#3BAEF040', badge: '#071830', text: C.fii },
  NEUTRAL:             { bg: '#0E1420', glow: 'transparent', badge: '#131B2E', text: '#64748B' },
  DISTRIBUTION:        { bg: '#1A0408', glow: '#F44B4B30', badge: '#2A0608', text: C.bear },
}

function SectorHeatmap({ sectors, isMobile }: { sectors: Sector[]; isMobile: boolean }) {
  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div style={LABEL}>SECTOR CAPITAL ROTATION  <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>({sectors.length} sectors)</span></div>
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

      {/* Grid — 3 cols desktop / 2 cols mobile */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)', gap: 6 }}>
        {sectors.map(s => {
          const st = SIG[s.rotation_signal] ?? SIG['NEUTRAL']
          const score = s.combined_score
          return (
            <Link key={s.sector} to={`/sectors/${s.sector}`} style={{ textDecoration: 'none' }}>
              <div style={{
                background: st.bg,
                border: `1px solid ${st.text}33`,
                boxShadow: st.glow !== 'transparent' ? `0 0 12px ${st.glow}` : 'none',
                borderRadius: 7, padding: '10px 12px',
                transition: 'all 0.18s',
                cursor: 'pointer',
              }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = `${st.text}88`; e.currentTarget.style.transform = 'translateY(-1px)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = `${st.text}33`; e.currentTarget.style.transform = 'none' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ color: C.primary, fontSize: 11, fontWeight: 700, flex: 1, marginRight: 8 }}>
                    {s.sector.replace(/_/g, ' ')}
                  </div>
                  {score != null && (
                    <div style={{ color: score >= 0 ? C.bull : C.bear, fontSize: 12, fontWeight: 800, fontFamily: 'monospace', flexShrink: 0 }}>
                      {score >= 0 ? '+' : ''}{Number(score).toFixed(0)}
                    </div>
                  )}
                </div>
                <div style={{
                  display: 'inline-block', marginTop: 5,
                  background: st.badge, color: st.text,
                  fontSize: 8, fontWeight: 700, padding: '2px 6px',
                  borderRadius: 3, letterSpacing: 0.5,
                }}>
                  {s.rotation_signal.replace(/_/g, ' ')}
                </div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ─── Side Panel ───────────────────────────────────────────────────────────────

function SidePanel({ strong, catalysts, deals }: {
  strong:    { stocks: import('../api/client').Stock[]; count: number } | undefined
  catalysts: { catalysts: Record<string, unknown>[]; count: number }   | undefined
  deals:     { deals:    Record<string, unknown>[]; count: number }    | undefined
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

      {/* Top Conviction */}
      <div style={{ ...CARD, padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={LABEL}>TOP CONVICTION</div>
          <Link to="/watchlist" style={{ color: C.blue, fontSize: 10, textDecoration: 'none', fontWeight: 600 }}>All →</Link>
        </div>
        {(strong?.stocks ?? []).length === 0 ? (
          <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '12px 0' }}>None currently</div>
        ) : (
          (strong?.stocks ?? []).map(s => (
            <Link key={s.symbol} to={`/stocks/${s.symbol}`} style={{ textDecoration: 'none' }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 0', borderBottom: `1px solid #1E2D44`,
              }}
                onMouseEnter={e => (e.currentTarget.style.paddingLeft = '4px')}
                onMouseLeave={e => (e.currentTarget.style.paddingLeft = '0')}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: C.h1, fontWeight: 800, fontSize: 13 }}>{s.symbol}</div>
                  <div style={{ color: C.muted, fontSize: 10, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                    {s.sector}
                    {s.price?.ret_30d != null && (
                      <span style={{ color: (s.price.ret_30d ?? 0) >= 0 ? C.bull : C.bear, fontWeight: 700, marginLeft: 6 }}>
                        {s.price.ret_30d >= 0 ? '+' : ''}{s.price.ret_30d.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
                <ScoreGauge score={s.bull_run_score} size={40} />
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Upcoming Catalysts */}
      <div style={{ ...CARD, padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={LABEL}>UPCOMING CATALYSTS</div>
          <Link to="/corporate" style={{ color: C.blue, fontSize: 10, textDecoration: 'none', fontWeight: 600 }}>All →</Link>
        </div>
        {(catalysts?.catalysts ?? []).slice(0, 5).map((c, i) => {
          const cat = c as Record<string, unknown>
          const dateStr = String(cat.event_date ?? '')
          return (
            <div key={i} style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: `1px solid #1E2D44`, alignItems: 'center' }}>
              <div style={{
                flexShrink: 0, background: '#1A1508', border: '1px solid #F5A52455',
                borderRadius: 5, padding: '4px 7px', textAlign: 'center', minWidth: 34,
              }}>
                <div style={{ color: C.neutral, fontSize: 11, fontWeight: 800, lineHeight: 1 }}>{dateStr.slice(8)}</div>
                <div style={{ color: C.muted, fontSize: 8, marginTop: 1 }}>{dateStr.slice(5, 7)}</div>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: C.primary, fontSize: 12, fontWeight: 700 }}>{String(cat.symbol ?? '')}</div>
                <div style={{ color: C.muted, fontSize: 9, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {String(cat.purpose_type ?? cat.purpose ?? '').replace(/_/g, ' ')}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Block Deals */}
      <div style={{ ...CARD, padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={LABEL}>BLOCK DEALS</div>
          <Link to="/corporate" style={{ color: C.blue, fontSize: 10, textDecoration: 'none', fontWeight: 600 }}>All →</Link>
        </div>
        {(deals?.deals ?? []).slice(0, 4).map((d, i) => {
          const deal = d as Record<string, unknown>
          const cr = Number(deal.net_value_cr ?? deal.value_cr ?? 0)
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 0', borderBottom: `1px solid #1E2D44` }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: C.primary, fontSize: 12, fontWeight: 700 }}>{String(deal.symbol ?? deal.SYMBOL ?? '')}</div>
                <div style={{ color: C.muted, fontSize: 9, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {String(deal.client_name ?? deal.CLIENT_NAME ?? '').slice(0, 24)}
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{ color: '#C668E8', fontSize: 12, fontWeight: 800 }}>
                  {cr !== 0 ? `${cr >= 0 ? '+' : ''}${cr.toFixed(0)} Cr` : '--'}
                </div>
                <div style={{ color: C.dim, fontSize: 9 }}>{String(deal.trade_date ?? deal.TRADE_DATE ?? '').slice(5)}</div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Emerging Watchlist Card ──────────────────────────────────────────────────

function EmergeCard({ stock }: { stock: import('../api/client').Stock }) {
  const ret = stock.price?.ret_30d
  const pos = (ret ?? 0) >= 0
  return (
    <Link to={`/stocks/${stock.symbol}`} style={{ textDecoration: 'none' }}>
      <div style={{
        ...CARD, padding: '12px 14px',
        display: 'flex', flexDirection: 'column', gap: 8,
        transition: 'all 0.18s',
      }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = '#2D4A6B'; e.currentTarget.style.boxShadow = '0 4px 16px #0008'; e.currentTarget.style.transform = 'translateY(-2px)' }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = '#1E2D44'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ color: C.h1, fontWeight: 800, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {stock.symbol}
            </div>
            <div style={{ color: C.muted, fontSize: 10, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {stock.sector}
            </div>
          </div>
          <ScoreGauge score={stock.bull_run_score} size={40} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {stock.close_now != null && (
            <span style={{ color: C.secondary, fontSize: 11, fontWeight: 600 }}>
              &#8377;{stock.close_now.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </span>
          )}
          {ret != null && (
            <span style={{ fontSize: 11, fontWeight: 800, color: pos ? C.bull : C.bear }}>
              {pos ? '+' : ''}{ret.toFixed(1)}%
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <CapFlowBadge label={stock.label} />
          {(stock.trend_signal === 'STRONG_UPTREND' || stock.trend_signal === 'UPTREND') && (
            <span style={{
              fontSize: 8, fontWeight: 700, padding: '2px 5px', borderRadius: 3,
              border: `1px solid ${C.bull}44`, color: C.bull, background: '#061A0E',
            }}>
              {stock.trend_signal === 'STRONG_UPTREND' ? 'STR UP' : 'UPTRD'}
            </span>
          )}
          {stock.oi_signal === 'LONG_BUILDUP' && (
            <span style={{
              fontSize: 8, fontWeight: 700, padding: '2px 5px', borderRadius: 3,
              border: `1px solid ${C.fii}44`, color: C.fii, background: '#040E22',
            }}>LB</span>
          )}
        </div>
      </div>
    </Link>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export function Dashboard() {
  const isMobile = useMobile()

  const { data: ctx }       = useQuery({ queryKey: ['market-context'],    queryFn: fetchMarketContext,    refetchInterval: 300_000 })
  const { data: part }      = useQuery({ queryKey: ['participant-latest'], queryFn: fetchParticipantLatest, refetchInterval: 300_000 })
  const { data: sectors }   = useQuery({ queryKey: ['sectors'],            queryFn: fetchSectors,           refetchInterval: 300_000 })
  const { data: emerging }  = useQuery({ queryKey: ['watchlist','EMRG'],  queryFn: () => fetchWatchlist('EMERGING', 15),        refetchInterval: 300_000 })
  const { data: strong }    = useQuery({ queryKey: ['watchlist','STR'],   queryFn: () => fetchWatchlist('BULL_RUN', 6), refetchInterval: 300_000 })
  const { data: catalysts } = useQuery({ queryKey: ['catalysts'],          queryFn: fetchCatalysts,         refetchInterval: 600_000 })
  const { data: deals }     = useQuery({ queryKey: ['deals-dash'],         queryFn: () => fetchDeals(10, 6), refetchInterval: 600_000 })

  const allSectors = sectors?.sectors ?? []
  const flows      = ctx?.flow_scores

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* Row 1: Command Strip */}
      {ctx && <CommandStrip ctx={ctx} part={part} isMobile={isMobile} />}

      {/* Row 2: Three visual instruments */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 14 }}>
        {ctx ? <RegimeDial score={ctx.smart_money_score ?? 0} regime={ctx.regime} /> : (
          <div style={{ ...CARD, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: C.dim }}>Loading…</span>
          </div>
        )}
        <BreadthDonut breadth={ctx?.breadth} />
        {part && ctx ? <ConvictionPanel part={part} cash={ctx.cash_flows} /> : (
          <div style={{ ...CARD, padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: C.dim }}>Loading…</span>
          </div>
        )}
      </div>

      {/* Row 3: Participant Flow Bars */}
      {flows && part && <FlowBars flows={flows} part={part} isMobile={isMobile} />}

      {/* Row 4: Sector Heatmap + Side Panel */}
      {allSectors.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2.4fr 1fr', gap: 14, alignItems: 'start' }}>
          <SectorHeatmap sectors={allSectors} isMobile={isMobile} />
          <SidePanel strong={strong} catalysts={catalysts} deals={deals} />
        </div>
      )}

      {/* Row 5: Emerging Watchlist */}
      {(emerging?.stocks ?? []).length > 0 && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div style={LABEL}>EMERGING WATCHLIST</div>
            <Link to="/watchlist" style={{ color: C.blue, fontSize: 11, textDecoration: 'none', fontWeight: 600 }}>
              View all ({emerging?.count ?? 0}) →
            </Link>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(5, 1fr)', gap: 8 }}>
            {(emerging?.stocks ?? []).map(stock => (
              <EmergeCard key={stock.symbol} stock={stock} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
