/**
 * Dashboard — Infographic-first redesign
 * Visual instruments: Regime Dial, Breadth Donut, Flow Bars, Sector Heatmap
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

// ─── Tiny helpers ─────────────────────────────────────────────────────────────

const CARD = { background: '#141720', border: '1px solid #1E2332', borderRadius: 8 } as const
const S9   = { color: '#475569', fontSize: 9, letterSpacing: 1.5 } as const
const signed = (n: number | null | undefined, d = 1) =>
  n == null ? '--' : `${n >= 0 ? '+' : ''}${n.toFixed(d)}`

// ─── SVG: Regime Speedometer ──────────────────────────────────────────────────

function RegimeDial({ score, regime, pcr, pcrSignal }: {
  score: number; regime: string; pcr: number | null; pcrSignal: string
}) {
  const cx = 110, cy = 100, R = 72, Rneedle = 58
  const clamped = Math.max(-100, Math.min(100, score))
  const ratio   = (clamped + 100) / 200
  const theta   = Math.PI - ratio * Math.PI
  const nx      = cx + Rneedle * Math.cos(theta)
  const ny      = cy - Rneedle * Math.sin(theta)

  const arc = (t: number, r = R) => {
    const a = Math.PI - t * Math.PI
    return { x: cx + r * Math.cos(a), y: cy - r * Math.sin(a) }
  }

  // 3 arc segments: BEAR [0→1/3], NEUTRAL [1/3→2/3], BULL [2/3→1]
  const segs = [
    { from: 0, to: 1 / 3, color: '#EF4444', label: 'BEAR' },
    { from: 1 / 3, to: 2 / 3, color: '#F59E0B', label: 'NEUTRAL' },
    { from: 2 / 3, to: 1, color: '#22C55E', label: 'BULL' },
  ]

  const regimeColor = regime === 'BULL' ? '#22C55E' : regime === 'BEAR' ? '#EF4444' : '#F59E0B'
  const pcrColor    = pcrSignal === 'BULLISH' ? '#22C55E' : pcrSignal === 'BEARISH' ? '#EF4444' : '#F59E0B'

  return (
    <div style={{ ...CARD, padding: '16px 20px' }}>
      <div style={S9}>SMART MONEY REGIME</div>
      <svg viewBox="0 0 220 115" width="100%" style={{ display: 'block', maxWidth: 260, margin: '0 auto' }}>
        {/* Track */}
        {(() => {
          const s = arc(0); const e = arc(1)
          return <path d={`M ${s.x},${s.y} A ${R},${R} 0 0,1 ${e.x},${e.y}`} stroke="#1E2332" strokeWidth="16" fill="none" strokeLinecap="round" />
        })()}
        {/* Colored segments */}
        {segs.map(({ from, to, color }) => {
          const s = arc(from); const e = arc(to)
          return (
            <path
              key={from}
              d={`M ${s.x},${s.y} A ${R},${R} 0 0,1 ${e.x},${e.y}`}
              stroke={color} strokeWidth="14" fill="none" strokeLinecap="round" strokeOpacity="0.8"
            />
          )
        })}
        {/* Needle */}
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#E2E8F0" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="5" fill="#0A0D14" stroke="#E2E8F0" strokeWidth="2" />
        {/* Labels */}
        <text x="24" y="112" fill="#EF4444" fontSize="8" textAnchor="middle" fontFamily="monospace">BEAR</text>
        <text x={cx} y="112" fill="#F59E0B" fontSize="8" textAnchor="middle" fontFamily="monospace">NEUTRAL</text>
        <text x="198" y="112" fill="#22C55E" fontSize="8" textAnchor="middle" fontFamily="monospace">BULL</text>
        {/* Center score */}
        <text x={cx} y="78" fill={regimeColor} fontSize="18" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
          {clamped >= 0 ? '+' : ''}{clamped.toFixed(1)}
        </text>
        <text x={cx} y="91" fill="#475569" fontSize="9" textAnchor="middle" fontFamily="monospace">{regime}</text>
      </svg>
      {/* PCR row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, borderTop: '1px solid #1E2332', paddingTop: 8 }}>
        <div>
          <div style={S9}>PCR</div>
          <div style={{ color: pcrColor, fontWeight: 700, fontSize: 14, marginTop: 2 }}>
            {pcr?.toFixed(2) ?? '--'}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={S9}>SIGNAL</div>
          <div style={{ color: pcrColor, fontWeight: 700, fontSize: 11, marginTop: 2 }}>{pcrSignal}</div>
        </div>
      </div>
    </div>
  )
}

// ─── SVG: Universe Breadth Donut ──────────────────────────────────────────────

function BreadthDonut({ breadth }: { breadth: MarketContext['breadth'] }) {
  if (!breadth) return null

  const total   = Object.values(breadth).reduce((a, b) => a + b, 0)
  const R = 45, cx = 70, cy = 70
  const circ = 2 * Math.PI * R

  const segments = [
    { key: 'strong_candidate', label: 'STRONG',    color: '#22C55E' },
    { key: 'emerging',         label: 'EMERGING',  color: '#10B981' },
    { key: 'watchlist',        label: 'WATCHLIST', color: '#3B82F6' },
    { key: 'neutral',          label: 'NEUTRAL',   color: '#475569' },
    { key: 'avoid',            label: 'AVOID',     color: '#EF4444' },
  ] as const

  let offset = 0
  const gap = 2

  return (
    <div style={{ ...CARD, padding: '16px 20px' }}>
      <div style={S9}>UNIVERSE BREADTH</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginTop: 10 }}>
        <svg viewBox="0 0 140 140" width={140} height={140} style={{ flexShrink: 0 }}>
          {segments.map(({ key, color }) => {
            const count = breadth[key as keyof typeof breadth] ?? 0
            const pct   = total > 0 ? count / total : 0
            const dash  = circ * pct - (pct > 0 ? gap : 0)
            const space = circ - dash
            const thisDash = `${Math.max(0, dash)} ${space}`
            const thisDashOffset = circ * (1 - offset)
            offset += pct
            return (
              <circle key={key}
                cx={cx} cy={cy} r={R} fill="none"
                stroke={color} strokeWidth="22"
                strokeDasharray={thisDash}
                strokeDashoffset={thisDashOffset}
                transform={`rotate(-90 ${cx} ${cy})`}
              />
            )
          })}
          {/* Center */}
          <text x={cx} y={cy - 5} textAnchor="middle" fill="#E2E8F0" fontSize="16" fontWeight="bold" fontFamily="monospace">{total}</text>
          <text x={cx} y={cy + 10} textAnchor="middle" fill="#475569" fontSize="8" fontFamily="monospace">STOCKS</text>
        </svg>
        {/* Legend */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flex: 1 }}>
          {segments.map(({ key, label, color }) => {
            const count = breadth[key as keyof typeof breadth] ?? 0
            const pct   = total > 0 ? (count / total * 100).toFixed(0) : '0'
            return (
              <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 8, height: 8, borderRadius: 2, background: color, flexShrink: 0 }} />
                <span style={{ color: '#64748B', fontSize: 9, flex: 1 }}>{label}</span>
                <span style={{ color, fontSize: 11, fontWeight: 700, minWidth: 28, textAlign: 'right' }}>{count}</span>
                <span style={{ color: '#334155', fontSize: 9, minWidth: 28, textAlign: 'right' }}>{pct}%</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ─── Conviction + Divergence Panel ────────────────────────────────────────────

function ConvictionPanel({ part, cash }: { part: ParticipantLatest; cash: MarketContext['cash_flows'] }) {
  const bars = [
    { label: 'FII Conviction',  value: part.FII_conviction, color: '#22C55E', track: '#0F2D1A' },
    { label: 'DII Conviction',  value: part.DII_conviction, color: '#3B82F6', track: '#0C1E3A' },
  ]
  const div = [
    { label: 'FII vs DII',      value: part.FII_DII_Divergence,    help: 'positive = FII > DII' },
    { label: 'Smart vs Retail', value: part.Smart_Retail_Divergence, help: 'positive = institutions > retail' },
  ]

  const flowBars = cash ? [
    { label: 'FPI/FII', value: cash.fpi_5d_cr,       color: cash.fpi_5d_cr >= 0 ? '#22C55E' : '#EF4444' },
    { label: 'MF/DII',  value: cash.mf_5d_cr,        color: cash.mf_5d_cr >= 0 ? '#3B82F6' : '#EF4444' },
    { label: 'Insurance', value: cash.insurance_5d_cr, color: cash.insurance_5d_cr >= 0 ? '#8B5CF6' : '#EF4444' },
  ] : []

  const maxCash = Math.max(...flowBars.map(f => Math.abs(f.value)), 1000)

  return (
    <div style={{ ...CARD, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={S9}>CONVICTION & CASH FLOWS</div>

      {/* Conviction bars */}
      {bars.map(({ label, value, color, track }) => (
        <div key={label}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ color: '#64748B', fontSize: 10 }}>{label}</span>
            <span style={{ color, fontWeight: 700, fontSize: 12 }}>{value.toFixed(0)}%</span>
          </div>
          <div style={{ height: 8, background: track, borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              height: '100%', width: `${Math.min(100, value)}%`,
              background: `linear-gradient(90deg, ${color}88, ${color})`,
              borderRadius: 4, transition: 'width 1s',
            }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
            <span style={{ color: '#334155', fontSize: 8 }}>0%</span>
            <span style={{ color: '#334155', fontSize: 8 }}>50%</span>
            <span style={{ color: '#334155', fontSize: 8 }}>100%</span>
          </div>
        </div>
      ))}

      {/* Divergence scores */}
      <div style={{ borderTop: '1px solid #1E2332', paddingTop: 10 }}>
        <div style={{ ...S9, marginBottom: 6 }}>DIVERGENCE SCORES</div>
        {div.map(({ label, value }) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
            <span style={{ color: '#64748B', fontSize: 9 }}>{label}</span>
            <span style={{
              fontWeight: 700, fontSize: 12, fontFamily: 'monospace',
              color: value >= 0 ? '#22C55E' : '#EF4444',
            }}>{signed(value)}</span>
          </div>
        ))}
      </div>

      {/* 5D Cash flows */}
      {flowBars.length > 0 && (
        <div style={{ borderTop: '1px solid #1E2332', paddingTop: 10 }}>
          <div style={{ ...S9, marginBottom: 8 }}>5D NET CASH FLOWS</div>
          {flowBars.map(({ label, value, color }) => {
            const pct = Math.min(100, Math.abs(value) / maxCash * 100)
            const pos = value >= 0
            return (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <span style={{ color: '#475569', fontSize: 9, minWidth: 52 }}>{label}</span>
                <div style={{ flex: 1, height: 5, background: '#1E2332', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', width: `${pct}%`, borderRadius: 3,
                    background: color, float: pos ? 'left' : 'right',
                  }} />
                </div>
                <span style={{ color, fontSize: 9, fontWeight: 700, minWidth: 70, textAlign: 'right' }}>
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

function FlowBars({ flows, part }: {
  flows: { FII: number; DII: number; PRO: number; CLIENT: number };
  part: ParticipantLatest
}) {
  const maxAbs  = Math.max(...Object.values(flows).map(Math.abs), 10)
  const entries = [
    { key: 'FII',    score: flows.FII,    color: '#22C55E', conv: part.FII_conviction, label: 'FII/FPI', desc: 'Foreign Institutional' },
    { key: 'DII',    score: flows.DII,    color: '#3B82F6', conv: part.DII_conviction, label: 'DII/MF',  desc: 'Domestic Institutional' },
    { key: 'PRO',    score: flows.PRO,    color: '#F59E0B', conv: null,                label: 'PRO',     desc: 'Proprietary Desks' },
    { key: 'CLIENT', score: flows.CLIENT, color: '#8B5CF6', conv: null,                label: 'CLIENT',  desc: 'Retail/HNI' },
  ]

  return (
    <div style={{ ...CARD, padding: '16px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={S9}>F&O PARTICIPANT FLOWS</div>
        <Link to="/participant" style={{ color: '#3B82F6', fontSize: 10, textDecoration: 'none' }}>Full Analysis</Link>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {entries.map(({ key, score, color, conv, label, desc }) => {
          const pct = Math.abs(score) / maxAbs * 100
          const pos = score >= 0
          return (
            <div key={key}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <div style={{ minWidth: 70 }}>
                  <div style={{ color: '#E2E8F0', fontSize: 11, fontWeight: 700 }}>{label}</div>
                  <div style={{ color: '#334155', fontSize: 8 }}>{desc}</div>
                </div>
                {/* Centered bar */}
                <div style={{ flex: 1, position: 'relative', height: 20, display: 'flex', alignItems: 'center' }}>
                  {/* Center line */}
                  <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: '#1E2332' }} />
                  {/* Bar */}
                  <div style={{
                    position: 'absolute',
                    [pos ? 'left' : 'right']: '50%',
                    width: `${pct / 2}%`,
                    height: 14,
                    top: 3,
                    background: `linear-gradient(${pos ? '90deg' : '270deg'}, ${color}44, ${color})`,
                    borderRadius: pos ? '0 4px 4px 0' : '4px 0 0 4px',
                  }} />
                  {/* Conviction overlay bar (thinner) */}
                  {conv != null && (
                    <div style={{
                      position: 'absolute',
                      [pos ? 'left' : 'right']: '50%',
                      width: `${Math.min(conv / 2, pct / 2)}%`,
                      height: 4,
                      top: 8,
                      background: color,
                      borderRadius: pos ? '0 2px 2px 0' : '2px 0 0 2px',
                      opacity: 0.9,
                    }} />
                  )}
                </div>
                <div style={{ minWidth: 60, textAlign: 'right' }}>
                  <div style={{ color, fontSize: 13, fontWeight: 700, fontFamily: 'monospace' }}>
                    {score >= 0 ? '+' : ''}{score.toFixed(1)}
                  </div>
                  {conv != null && (
                    <div style={{ color: '#475569', fontSize: 9 }}>{conv.toFixed(0)}% conv.</div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
        {/* Scale labels */}
        <div style={{ display: 'flex', justifyContent: 'space-between', paddingLeft: 78 }}>
          <span style={{ color: '#1E2332', fontSize: 8 }}>{(-maxAbs).toFixed(0)}</span>
          <span style={{ color: '#334155', fontSize: 8 }}>0</span>
          <span style={{ color: '#1E2332', fontSize: 8 }}>+{maxAbs.toFixed(0)}</span>
        </div>
      </div>
    </div>
  )
}

// ─── Sector Heatmap ───────────────────────────────────────────────────────────

const SIG_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  STRONG_ACCUMULATION: { bg: '#052e16', text: '#22C55E', border: '#22C55E44' },
  EARLY_ROTATION:      { bg: '#064e3b', text: '#10B981', border: '#10B98144' },
  PRICE_LED:           { bg: '#1e3a5f', text: '#60A5FA', border: '#60A5FA44' },
  NEUTRAL:             { bg: '#141720', text: '#475569', border: '#1E2332' },
  DISTRIBUTION:        { bg: '#450a0a', text: '#EF4444', border: '#EF444444' },
}

function SectorHeatmap({ sectors }: { sectors: Sector[] }) {
  return (
    <div style={{ ...CARD, padding: '16px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={S9}>SECTOR CAPITAL ROTATION</div>
        <Link to="/sectors" style={{ color: '#3B82F6', fontSize: 10, textDecoration: 'none' }}>Full View</Link>
      </div>
      {/* Legend */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
        {Object.entries(SIG_STYLE).map(([sig, style]) => (
          <div key={sig} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: style.text, opacity: 0.8 }} />
            <span style={{ color: '#475569', fontSize: 8 }}>{sig.replace(/_/g, ' ')}</span>
          </div>
        ))}
      </div>
      {/* Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6 }}>
        {sectors.map(s => {
          const st = SIG_STYLE[s.rotation_signal] ?? SIG_STYLE['NEUTRAL']
          return (
            <Link key={s.sector} to={`/sectors/${s.sector}`} style={{ textDecoration: 'none' }}>
              <div style={{
                background: st.bg, border: `1px solid ${st.border}`, borderRadius: 5,
                padding: '8px 10px', cursor: 'pointer', transition: 'opacity 0.15s',
              }}
                onMouseEnter={e => (e.currentTarget.style.opacity = '0.8')}
                onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
              >
                <div style={{ color: st.text, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {s.sector}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3, alignItems: 'center' }}>
                  <span style={{ fontSize: 7, color: st.text, opacity: 0.7 }}>
                    {s.rotation_signal.replace(/_/g, ' ').slice(0, 10)}
                  </span>
                  <span style={{
                    fontSize: 10, fontWeight: 700, fontFamily: 'monospace',
                    color: s.combined_score >= 0 ? '#22C55E' : '#EF4444',
                  }}>
                    {s.combined_score >= 0 ? '+' : ''}{s.combined_score.toFixed(0)}
                  </span>
                </div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ─── Top Picks + Events column ────────────────────────────────────────────────

function SidePanel({ strong, catalysts, deals }: {
  strong:    { stocks: import('../api/client').Stock[]; count: number } | undefined
  catalysts: { catalysts: Record<string, unknown>[]; count: number }   | undefined
  deals:     { deals:    Record<string, unknown>[]; count: number }    | undefined
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* Top Conviction Picks */}
      <div style={{ ...CARD, padding: '14px 16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={S9}>TOP CONVICTION</div>
          <Link to="/watchlist" style={{ color: '#3B82F6', fontSize: 10, textDecoration: 'none' }}>All</Link>
        </div>
        {(strong?.stocks ?? []).length === 0 ? (
          <div style={{ color: '#334155', fontSize: 11, textAlign: 'center', padding: '10px 0' }}>None currently</div>
        ) : (
          (strong?.stocks ?? []).map(s => (
            <Link key={s.symbol} to={`/stocks/${s.symbol}`} style={{ textDecoration: 'none' }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8, padding: '7px 0',
                borderBottom: '1px solid #1E2332',
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 12 }}>{s.symbol}</div>
                  <div style={{ color: '#475569', fontSize: 9, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                    {s.sector}
                    {s.price?.ret_30d != null && (
                      <span style={{ color: (s.price.ret_30d ?? 0) >= 0 ? '#22C55E' : '#EF4444', marginLeft: 6 }}>
                        {s.price.ret_30d >= 0 ? '+' : ''}{s.price.ret_30d.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
                <ScoreGauge score={s.bull_run_score} size={38} />
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Upcoming Catalysts */}
      <div style={{ ...CARD, padding: '14px 16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={S9}>UPCOMING CATALYSTS</div>
          <Link to="/corporate" style={{ color: '#3B82F6', fontSize: 10, textDecoration: 'none' }}>All</Link>
        </div>
        {(catalysts?.catalysts ?? []).slice(0, 5).map((c, i) => {
          const cat = c as Record<string, unknown>
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '6px 0', borderBottom: '1px solid #1E2332' }}>
              <div style={{
                background: '#1A1A08', border: '1px solid #F59E0B44', borderRadius: 4,
                padding: '3px 6px', flexShrink: 0, textAlign: 'center',
              }}>
                <div style={{ color: '#F59E0B', fontSize: 10, fontWeight: 700 }}>
                  {String(cat.event_date ?? '').slice(5, 7)}
                </div>
                <div style={{ color: '#64748B', fontSize: 8 }}>
                  {String(cat.event_date ?? '').slice(8)}
                </div>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: '#E2E8F0', fontSize: 11, fontWeight: 700 }}>{String(cat.symbol ?? '')}</div>
                <div style={{ color: '#64748B', fontSize: 9, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {String(cat.purpose_type ?? cat.purpose ?? '').replace(/_/g, ' ')}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Block Deals */}
      <div style={{ ...CARD, padding: '14px 16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={S9}>BLOCK DEALS</div>
          <Link to="/corporate" style={{ color: '#3B82F6', fontSize: 10, textDecoration: 'none' }}>All</Link>
        </div>
        {(deals?.deals ?? []).slice(0, 4).map((d, i) => {
          const deal = d as Record<string, unknown>
          const cr = Number(deal.net_value_cr ?? deal.value_cr ?? 0)
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', borderBottom: '1px solid #1E2332' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: '#E2E8F0', fontSize: 11, fontWeight: 700 }}>{String(deal.symbol ?? deal.SYMBOL ?? '')}</div>
                <div style={{ color: '#475569', fontSize: 9, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {String(deal.client_name ?? deal.CLIENT_NAME ?? '').slice(0, 22)}
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{ color: '#8B5CF6', fontSize: 11, fontWeight: 700 }}>
                  {cr !== 0 ? `${cr >= 0 ? '+' : ''}${cr.toFixed(0)} Cr` : '--'}
                </div>
                <div style={{ color: '#334155', fontSize: 8 }}>
                  {String(deal.trade_date ?? deal.TRADE_DATE ?? '').slice(5)}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Emerging Watchlist mini-cards ────────────────────────────────────────────

function EmergeCard({ stock }: { stock: import('../api/client').Stock }) {
  const ret = stock.price?.ret_30d
  const pos = (ret ?? 0) >= 0
  return (
    <Link to={`/stocks/${stock.symbol}`} style={{ textDecoration: 'none' }}>
      <div style={{
        ...CARD, padding: '10px 12px', height: '100%',
        display: 'flex', flexDirection: 'column', gap: 6,
        transition: 'border-color 0.15s',
      }}
        onMouseEnter={e => (e.currentTarget.style.borderColor = '#22C55E44')}
        onMouseLeave={e => (e.currentTarget.style.borderColor = '#1E2332')}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {stock.symbol}
            </div>
            <div style={{ color: '#475569', fontSize: 9, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {stock.sector}
            </div>
          </div>
          <ScoreGauge score={stock.bull_run_score} size={38} />
        </div>
        {/* Price & return */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {stock.close_now != null && (
            <span style={{ color: '#94A3B8', fontSize: 10 }}>
              &#8377;{stock.close_now.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </span>
          )}
          {ret != null && (
            <span style={{ fontSize: 10, fontWeight: 700, color: pos ? '#22C55E' : '#EF4444' }}>
              {pos ? '+' : ''}{ret.toFixed(1)}%
            </span>
          )}
        </div>
        {/* Badges */}
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <CapFlowBadge label={stock.label} />
          {stock.trend_signal && (stock.trend_signal === 'STRONG_UPTREND' || stock.trend_signal === 'UPTREND') && (
            <span style={{
              fontSize: 7, fontWeight: 700, padding: '1px 4px', borderRadius: 2,
              border: '1px solid #22C55E44', color: '#22C55E', background: '#052e1688',
            }}>
              {stock.trend_signal === 'STRONG_UPTREND' ? 'STR UP' : 'UPTRD'}
            </span>
          )}
          {stock.oi_signal === 'LONG_BUILDUP' && (
            <span style={{
              fontSize: 7, fontWeight: 700, padding: '1px 4px', borderRadius: 2,
              border: '1px solid #3B82F644', color: '#3B82F6', background: '#0f1f3d88',
            }}>LB</span>
          )}
        </div>
      </div>
    </Link>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export function Dashboard() {
  const { data: ctx }       = useQuery({ queryKey: ['market-context'],    queryFn: fetchMarketContext,    refetchInterval: 300_000 })
  const { data: part }      = useQuery({ queryKey: ['participant-latest'], queryFn: fetchParticipantLatest, refetchInterval: 300_000 })
  const { data: sectors }   = useQuery({ queryKey: ['sectors'],            queryFn: fetchSectors,           refetchInterval: 300_000 })
  const { data: emerging }  = useQuery({ queryKey: ['watchlist','EMRG'],  queryFn: () => fetchWatchlist('EMERGING', 15),         refetchInterval: 300_000 })
  const { data: strong }    = useQuery({ queryKey: ['watchlist','STR'],   queryFn: () => fetchWatchlist('STRONG_CANDIDATE', 6), refetchInterval: 300_000 })
  const { data: catalysts } = useQuery({ queryKey: ['catalysts'],          queryFn: fetchCatalysts,         refetchInterval: 600_000 })
  const { data: deals }     = useQuery({ queryKey: ['deals-dash'],         queryFn: () => fetchDeals(10, 6), refetchInterval: 600_000 })

  const allSectors = sectors?.sectors ?? []
  const flows      = ctx?.flow_scores

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Row 1: Command Center ─────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14 }}>
        {ctx ? (
          <RegimeDial
            score={ctx.smart_money_score ?? 0}
            regime={ctx.regime}
            pcr={ctx.pcr ?? null}
            pcrSignal={ctx.pcr_signal ?? ''}
          />
        ) : (
          <div style={{ ...CARD, padding: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#334155', fontSize: 11 }}>Loading...</span>
          </div>
        )}
        <BreadthDonut breadth={ctx?.breadth} />
        {part && ctx ? (
          <ConvictionPanel part={part} cash={ctx.cash_flows} />
        ) : (
          <div style={{ ...CARD, padding: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#334155', fontSize: 11 }}>Loading...</span>
          </div>
        )}
      </div>

      {/* ── Row 2: Participant Flow Bars ──────────────────────────────────── */}
      {flows && part && (
        <FlowBars flows={flows} part={part} />
      )}

      {/* ── Row 3: Sector Heatmap + Side Panel ───────────────────────────── */}
      {allSectors.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 1.4fr', gap: 14, alignItems: 'start' }}>
          <SectorHeatmap sectors={allSectors} />
          <SidePanel strong={strong} catalysts={catalysts} deals={deals} />
        </div>
      )}

      {/* ── Row 4: Emerging Watchlist ─────────────────────────────────────── */}
      {(emerging?.stocks ?? []).length > 0 && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div style={S9}>EMERGING WATCHLIST</div>
            <Link to="/watchlist" style={{ color: '#3B82F6', fontSize: 10, textDecoration: 'none' }}>
              View all ({emerging?.count ?? 0})
            </Link>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
            {(emerging?.stocks ?? []).map(stock => (
              <EmergeCard key={stock.symbol} stock={stock} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
