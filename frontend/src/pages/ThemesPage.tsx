import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

// ─── Types ───────────────────────────────────────────────────────────────────

type TopPick = {
  symbol: string
  bull_run_score: number
  label: string
  close_now?: number | null
  ret_30d?: number | null
  ret_365d?: number | null
  sector?: string
}

type Theme = {
  theme:             string
  display_name:      string
  description:       string
  macro_driver:      string
  risk_factor:       string
  global_peer:       string
  sectors:           string[]
  stock_count:       number
  scored_count:      number
  strong_count:      number
  emerging_count:    number
  theme_score:       number | null
  theme_signal:      string
  momentum_phase:    string
  participant_leader:string
  avg_bull_score:    number | null
  avg_ret_30d:       number | null
  avg_ret_90d:       number | null
  avg_ret_365d:      number | null
  avg_vol_ratio:     number | null
  fii_flow_score:    number | null
  dii_flow_score:    number | null
  smart_money_score: number | null
  top_picks:         TopPick[]
  as_of_date:        string
}

// ─── Design tokens ────────────────────────────────────────────────────────────

const C = {
  bg:       '#0E1420',
  card:     '#111B2E',
  deep:     '#080E1A',
  border:   '1px solid #1E2D44',
  h1:       '#F8FAFC',
  primary:  '#E2E8F0',
  secondary:'#B0C4D8',
  muted:    '#7B90A8',
  dim:      '#4E6074',
  bull:     '#22D35E',
  bear:     '#F44B4B',
  neutral:  '#F5A524',
  blue:     '#3BAEF0',
  purple:   '#9B7BEA',
}

const LABEL: React.CSSProperties = {
  color: C.secondary, fontSize: 10, fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase',
}

// ─── Signal config ─────────────────────────────────────────────────────────────

const SIG_CFG: Record<string, { color: string; bg: string; label: string; emoji: string }> = {
  HEATING_UP:    { color: '#22D35E', bg: '#052E1688', label: 'Heating Up',     emoji: 'HOT' },
  MOMENTUM:      { color: '#3BAEF0', bg: '#0C2A4055', label: 'Momentum',       emoji: 'UP' },
  BUILDING:      { color: '#60A5FA', bg: '#1E3A5F55', label: 'Building',       emoji: 'BLD' },
  PRICE_LED:     { color: '#F5A524', bg: '#45260055', label: 'Price-Led',      emoji: 'PRC' },
  NEUTRAL:       { color: '#7B90A8', bg: '#1E2D4455', label: 'Neutral',        emoji: 'NEU' },
  DISTRIBUTION:  { color: '#F44B4B', bg: '#45090955', label: 'Distribution',   emoji: 'OUT' },
}

const PHASE_CFG: Record<string, { color: string; label: string }> = {
  ACCELERATING:  { color: '#22D35E', label: 'Accelerating' },
  MOMENTUM:      { color: '#3BAEF0', label: 'Full Momentum' },
  EARLY_ROTATION:{ color: '#60A5FA', label: 'Early Rotation' },
  CONSOLIDATING: { color: '#F5A524', label: 'Consolidating' },
  DECELERATING:  { color: '#FB923C', label: 'Decelerating' },
  DORMANT:       { color: '#7B90A8', label: 'Dormant' },
}

const PARTICIPANT_COLORS: Record<string, string> = {
  FII:         '#22D35E',
  DII:         '#9B7BEA',
  SMART_MONEY: '#3BAEF0',
  RETAIL:      '#7B90A8',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function pct(v: number | null | undefined, dec = 1) {
  if (v == null) return '--'
  return `${v >= 0 ? '+' : ''}${v.toFixed(dec)}%`
}

function sigC(sig: string) {
  return SIG_CFG[sig] ?? { color: C.muted, bg: '#1E2D4455', label: sig, emoji: '?' }
}

function phaseC(phase: string) {
  return PHASE_CFG[phase] ?? { color: C.muted, label: phase }
}

const fetchThemes = () => api.get<{ themes: Theme[]; count: number }>('/themes').then(r => r.data)

// ─── Score ring (simple circle progress) ──────────────────────────────────────

function ScoreRing({ score, color, size = 56 }: { score: number; color: string; size?: number }) {
  const r     = (size - 6) / 2
  const circ  = 2 * Math.PI * r
  const fill  = (score / 100) * circ
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1A2740" strokeWidth={4} />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={4}
        strokeDasharray={`${fill} ${circ}`} strokeLinecap="round" />
      <text x={size/2} y={size/2} dominantBaseline="middle" textAnchor="middle"
        fill={color} fontSize={size * 0.22} fontWeight="900" fontFamily="monospace"
        style={{ transform: `rotate(90deg)`, transformOrigin: `${size/2}px ${size/2}px` }}>
        {score.toFixed(0)}
      </text>
    </svg>
  )
}

// ─── Mini flow arrow ──────────────────────────────────────────────────────────

function FlowArrow({ value, label, color }: { value: number | null; label: string; color: string }) {
  const v = value ?? 0
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
      <div style={{
        fontSize: 8, fontWeight: 700, color: v >= 0 ? color : C.bear,
        background: v >= 0 ? `${color}22` : '#F44B4B22',
        border: `1px solid ${v >= 0 ? color : C.bear}44`,
        borderRadius: 3, padding: '1px 5px', whiteSpace: 'nowrap',
      }}>
        {v >= 0 ? '+' : ''}{v.toFixed(1)}
      </div>
      <div style={{ color: C.dim, fontSize: 8, letterSpacing: 0.5 }}>{label}</div>
    </div>
  )
}

// ─── Theme card ───────────────────────────────────────────────────────────────

function ThemeCard({ t, onClick, expanded }: { t: Theme; onClick: () => void; expanded: boolean }) {
  const score     = t.theme_score ?? 0
  const sig       = sigC(t.theme_signal)
  const phase     = phaseC(t.momentum_phase)
  const partColor = PARTICIPANT_COLORS[t.participant_leader] ?? C.muted
  const ret1y     = t.avg_ret_365d
  const ret30     = t.avg_ret_30d

  // Score color: green above 50, amber 40-50, muted below 40
  const scoreColor = score >= 55 ? C.bull : score >= 45 ? C.neutral : score >= 35 ? C.blue : C.muted

  return (
    <div style={{
      background: C.card, border: expanded ? `1px solid ${sig.color}66` : C.border,
      borderRadius: 10, overflow: 'hidden', cursor: 'pointer',
      transition: 'all 0.2s',
      borderTop: `3px solid ${sig.color}`,
      boxShadow: expanded ? `0 0 20px ${sig.color}22` : 'none',
    }}
      onClick={onClick}
    >
      {/* ── Card header ────────────────────────────────────────────────────── */}
      <div style={{ padding: '14px 16px 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1, marginRight: 12 }}>
            <div style={{ color: C.h1, fontSize: 13, fontWeight: 800, lineHeight: 1.3, marginBottom: 4 }}>
              {t.display_name}
            </div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 8 }}>
              <span style={{
                fontSize: 8, fontWeight: 700, padding: '2px 7px', borderRadius: 3,
                background: sig.bg, color: sig.color, border: `1px solid ${sig.color}44`, letterSpacing: 0.8,
              }}>
                {sig.label.toUpperCase()}
              </span>
              <span style={{
                fontSize: 8, fontWeight: 700, padding: '2px 7px', borderRadius: 3,
                background: `${phase.color}18`, color: phase.color, border: `1px solid ${phase.color}44`,
                letterSpacing: 0.8,
              }}>
                {phase.label.toUpperCase()}
              </span>
            </div>
          </div>
          <ScoreRing score={score} color={scoreColor} size={52} />
        </div>

        {/* Description */}
        <p style={{ color: C.muted, fontSize: 11, lineHeight: 1.5, marginBottom: 12, marginTop: 0 }}>
          {t.description}
        </p>

        {/* Flow indicators */}
        <div style={{
          display: 'flex', gap: 8, justifyContent: 'space-between',
          padding: '10px 0', borderTop: '1px solid #1A2740', borderBottom: '1px solid #1A2740',
          marginBottom: 12,
        }}>
          <FlowArrow value={t.fii_flow_score}    label="FII"    color="#3BAEF0" />
          <FlowArrow value={t.dii_flow_score}    label="DII"    color="#9B7BEA" />
          <FlowArrow value={t.smart_money_score} label="Smart$" color="#22D35E" />
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <div style={{ color: ret1y != null && ret1y >= 0 ? C.bull : C.bear, fontSize: 11, fontWeight: 800 }}>
              {pct(ret1y)}
            </div>
            <div style={{ color: C.dim, fontSize: 8 }}>1Y Ret</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <div style={{ color: ret30 != null && ret30 >= 0 ? C.bull : C.bear, fontSize: 11, fontWeight: 800 }}>
              {pct(ret30)}
            </div>
            <div style={{ color: C.dim, fontSize: 8 }}>30D Ret</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <div style={{ color: partColor, fontSize: 9, fontWeight: 800, letterSpacing: 0.5 }}>
              {t.participant_leader.replace('_', ' ')}
            </div>
            <div style={{ color: C.dim, fontSize: 8 }}>Leader</div>
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display: 'flex', gap: 14, marginBottom: 14 }}>
          <div>
            <div style={{ color: C.dim, fontSize: 8 }}>STOCKS</div>
            <div style={{ color: C.secondary, fontSize: 12, fontWeight: 700 }}>{t.stock_count}</div>
          </div>
          <div>
            <div style={{ color: C.dim, fontSize: 8 }}>STRONG+EMERGING</div>
            <div style={{ color: C.bull, fontSize: 12, fontWeight: 700 }}>
              {t.strong_count + t.emerging_count}
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: C.dim, fontSize: 8, marginBottom: 3 }}>SECTORS IN THEME</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              {t.sectors.slice(0, 4).map(sec => (
                <span key={sec} style={{
                  fontSize: 8, padding: '1px 5px', borderRadius: 2,
                  background: '#1A2740', color: C.muted, border: '1px solid #2A3F5F',
                }}>
                  {sec.replace(/_/g, ' ')}
                </span>
              ))}
              {t.sectors.length > 4 && (
                <span style={{ color: C.dim, fontSize: 8 }}>+{t.sectors.length - 4}</span>
              )}
            </div>
          </div>
        </div>

        {/* Top picks chips */}
        {t.top_picks.length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <div style={{ color: C.dim, fontSize: 8, fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>
              TOP PICKS
            </div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              {t.top_picks.slice(0, 4).map(p => (
                <a key={p.symbol}
                  href={`/stocks/${p.symbol}`}
                  onClick={e => e.stopPropagation()}
                  style={{
                    textDecoration: 'none',
                    display: 'inline-flex', flexDirection: 'column', alignItems: 'center',
                    background: '#0E1C30', border: '1px solid #2A3F5F', borderRadius: 5,
                    padding: '4px 8px', minWidth: 56,
                  }}
                >
                  <span style={{ color: sig.color, fontSize: 10, fontWeight: 800 }}>{p.symbol}</span>
                  <span style={{ color: C.dim, fontSize: 8 }}>{p.bull_run_score.toFixed(0)}/100</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Expanded detail ─────────────────────────────────────────────────── */}
      {expanded && (
        <div style={{ padding: '0 16px 16px', borderTop: '1px solid #1A2740', marginTop: 0 }}>
          <div style={{ paddingTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>

            {/* Macro driver */}
            <div style={{ background: '#0A1820', border: '1px solid #1E3A5F', borderRadius: 6, padding: '10px 12px' }}>
              <div style={{ color: C.blue, fontSize: 9, fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>
                MACRO DRIVER
              </div>
              <div style={{ color: C.secondary, fontSize: 11, lineHeight: 1.5 }}>{t.macro_driver}</div>
            </div>

            {/* Risk + Global peer */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div style={{ background: '#1A0A0A', border: '1px solid #3A1A1A', borderRadius: 6, padding: '10px 12px' }}>
                <div style={{ color: C.bear, fontSize: 9, fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>
                  KEY RISK
                </div>
                <div style={{ color: C.secondary, fontSize: 10, lineHeight: 1.5 }}>{t.risk_factor}</div>
              </div>
              <div style={{ background: '#0A1420', border: '1px solid #1E2D44', borderRadius: 6, padding: '10px 12px' }}>
                <div style={{ color: C.purple, fontSize: 9, fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>
                  GLOBAL PARALLEL
                </div>
                <div style={{ color: C.secondary, fontSize: 10, lineHeight: 1.5 }}>{t.global_peer}</div>
              </div>
            </div>

            {/* All top picks with detail */}
            {t.top_picks.length > 0 && (
              <div>
                <div style={{ ...LABEL, marginBottom: 8 }}>TOP PICKS — MONEY TRAIL LEADERS</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {t.top_picks.map((p, i) => (
                    <a key={p.symbol}
                      href={`/stocks/${p.symbol}`}
                      onClick={e => e.stopPropagation()}
                      style={{ textDecoration: 'none' }}
                    >
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        background: '#0A1420', border: '1px solid #1E2D44', borderRadius: 6,
                        padding: '8px 12px', transition: 'border-color 0.15s',
                      }}
                        onMouseEnter={e => (e.currentTarget.style.borderColor = sig.color + '66')}
                        onMouseLeave={e => (e.currentTarget.style.borderColor = '#1E2D44')}
                      >
                        <div style={{
                          width: 22, height: 22, borderRadius: '50%', background: '#1A2740',
                          color: C.dim, fontSize: 9, fontWeight: 700,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          flexShrink: 0,
                        }}>
                          {i + 1}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ color: sig.color, fontSize: 12, fontWeight: 800 }}>{p.symbol}</div>
                          {p.sector && <div style={{ color: C.dim, fontSize: 9 }}>{p.sector}</div>}
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ color: C.secondary, fontSize: 12, fontWeight: 700 }}>
                            {p.bull_run_score.toFixed(0)}/100
                          </div>
                          <div style={{ color: C.dim, fontSize: 8 }}>{p.label}</div>
                        </div>
                        {p.ret_365d != null && (
                          <div style={{
                            color: p.ret_365d >= 0 ? C.bull : C.bear,
                            fontSize: 11, fontWeight: 700, minWidth: 48, textAlign: 'right',
                          }}>
                            {pct(p.ret_365d)} 1Y
                          </div>
                        )}
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function ThemesPage() {
  const [expanded, setExpanded] = useState<string | null>(null)
  const [filter, setFilter]     = useState<string>('ALL')

  const { data, isLoading } = useQuery({
    queryKey: ['themes'],
    queryFn:  fetchThemes,
    refetchInterval: 600_000,
    staleTime: 300_000,
  })

  if (isLoading) return (
    <div style={{ color: C.muted, textAlign: 'center', padding: 60 }}>
      Loading theme intelligence...
    </div>
  )

  const themes = data?.themes ?? []

  // Filter
  const filters = ['ALL', 'HEATING_UP', 'BUILDING', 'MOMENTUM', 'PRICE_LED', 'NEUTRAL', 'DISTRIBUTION']
  const displayed = filter === 'ALL' ? themes : themes.filter(t => t.theme_signal === filter)

  // Summary stats
  const topTheme      = themes[0]
  const heating       = themes.filter(t => t.theme_signal === 'HEATING_UP').length
  const building      = themes.filter(t => t.theme_signal === 'BUILDING').length
  const totalStocks   = themes.reduce((s, t) => s + t.stock_count, 0)
  const totalEmerging = themes.reduce((s, t) => s + t.emerging_count + t.strong_count, 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div style={{
        background: C.card, border: C.border, borderRadius: 8, padding: '18px 20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
          <div style={{ flex: 1 }}>
            <div style={{ ...LABEL, marginBottom: 6 }}>THEMATIC INVESTMENT INTELLIGENCE</div>
            <div style={{ color: C.h1, fontSize: 22, fontWeight: 900, marginBottom: 6 }}>
              {themes.length} Investment Themes
            </div>
            <p style={{ color: C.muted, fontSize: 12, lineHeight: 1.6, margin: 0, maxWidth: 600 }}>
              India's macro investment themes tracked by money trail — where FII, DII, and smart money
              are positioning ahead of broad market recognition. Each theme aggregates intelligence
              signals from {totalStocks.toLocaleString()} classified stocks.
            </p>
          </div>

          {/* Summary tiles */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {[
              { label: 'Heating Up', value: heating,       color: C.bull   },
              { label: 'Building',   value: building,      color: C.blue   },
              { label: 'Strong+Emerging', value: totalEmerging, color: C.neutral },
              { label: 'Total Stocks', value: totalStocks, color: C.muted  },
            ].map(({ label, value, color }) => (
              <div key={label} style={{
                background: C.deep, border: C.border, borderRadius: 6,
                padding: '10px 16px', textAlign: 'center', minWidth: 80,
              }}>
                <div style={{ color, fontSize: 20, fontWeight: 900 }}>
                  {value.toLocaleString()}
                </div>
                <div style={{ color: C.dim, fontSize: 9, marginTop: 2 }}>{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* What is theme investing - layman explanation */}
        <div style={{
          marginTop: 16, padding: '12px 14px', background: '#0A1220',
          border: '1px solid #1E3A5F', borderLeft: `4px solid ${C.blue}`, borderRadius: 6,
        }}>
          <div style={{ color: C.blue, fontSize: 10, fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>
            WHAT IS THEMATIC INVESTING?
          </div>
          <p style={{ color: C.secondary, fontSize: 11, lineHeight: 1.6, margin: 0 }}>
            Instead of picking individual stocks, theme investing bets on broad economic shifts — like India's EV transition
            or the China+1 manufacturing shift. When a theme heats up, multiple stocks across sectors rise together.
            Our system tracks <strong style={{ color: C.h1 }}>where institutional money flows first</strong>, before prices reflect it.
            A "Heating Up" theme means smart money is quietly accumulating before the crowd notices.
          </p>
        </div>
      </div>

      {/* ── Filter chips ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ color: C.dim, fontSize: 10, marginRight: 4 }}>Filter:</span>
        {filters.map(f => {
          const cfg = f === 'ALL' ? { color: C.secondary, bg: '#1E3A5F' } : (SIG_CFG[f] ?? { color: C.muted, bg: '#1E2D44' })
          const count = f === 'ALL' ? themes.length : themes.filter(t => t.theme_signal === f).length
          return (
            <button key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '5px 12px', borderRadius: 5, border: C.border, cursor: 'pointer',
                fontSize: 10, fontWeight: 700,
                background: filter === f ? cfg.bg : 'transparent',
                color: filter === f ? cfg.color : C.dim,
                transition: 'all 0.15s',
              }}
            >
              {f === 'ALL' ? `All (${count})` : `${SIG_CFG[f]?.label ?? f} (${count})`}
            </button>
          )
        })}
      </div>

      {/* ── Theme cards grid ─────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 14 }}>
        {displayed.map(t => (
          <ThemeCard
            key={t.theme}
            t={t}
            expanded={expanded === t.theme}
            onClick={() => setExpanded(expanded === t.theme ? null : t.theme)}
          />
        ))}
      </div>

      {displayed.length === 0 && (
        <div style={{ color: C.muted, textAlign: 'center', padding: 40 }}>
          No themes match the current filter.
        </div>
      )}

      {/* ── Methodology note ─────────────────────────────────────────────────── */}
      <div style={{
        background: C.deep, border: C.border, borderRadius: 6,
        padding: '12px 16px', color: C.dim, fontSize: 10, lineHeight: 1.6,
      }}>
        <strong style={{ color: C.muted }}>Methodology:</strong> Theme Score (0-100) = 35% stock intelligence (bull-run scores)
        + 30% smart money flow (FII+PRO sector positioning) + 20% 1-year price momentum + 15% 30-day momentum.
        Signals are derived from participant F&O flow analysis, sector rotation models, and institutional deal intelligence.
        Data refreshed daily post-market.
      </div>
    </div>
  )
}
