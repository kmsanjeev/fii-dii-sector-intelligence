import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchSectors, type Sector } from '../api/client'
import { Link } from 'react-router-dom'
import { T } from '../styles/tokens'

// ─── Page palette (aliases from shared tokens) ─────────────────────────────────

const C = {
  bg:       T.bg,
  card:     T.cell,
  border:   `1px solid ${T.border}`,
  h1:       T.h1,
  primary:  T.text,
  secondary:T.textSub,
  muted:    T.muted,
  dim:      T.dim,
  bull:     T.green,
  bear:     T.red,
  blue:     T.fii,
}

// ─── Signal config — covers ALL actual values from the engine ─────────────────

const SIGNAL_CFG: Record<string, { color: string; bg: string; label: string; order: number }> = {
  EARLY_ROTATION: { color: '#22D35E', bg: '#052E1688', label: 'Early Rotation', order: 1 },
  LEADING:        { color: '#10B981', bg: '#064E3B55', label: 'Leading',         order: 2 },
  MOMENTUM:       { color: '#3BAEF0', bg: '#0C2A4055', label: 'Momentum',        order: 3 },
  BUILDING:       { color: '#60A5FA', bg: '#1E3A5F55', label: 'Building',        order: 4 },
  PRICE_LED:      { color: '#F5A524', bg: '#45260055', label: 'Price-Led',       order: 5 },
  NEUTRAL:        { color: '#7B90A8', bg: '#1E2D4455', label: 'Neutral',         order: 6 },
  LAGGING:        { color: '#FB923C', bg: '#3A140055', label: 'Lagging',         order: 7 },
  DISTRIBUTION:   { color: '#F44B4B', bg: '#45090955', label: 'Distribution',    order: 8 },
  DECLINING:      { color: '#DC2626', bg: '#3B0A0A55', label: 'Declining',       order: 9 },
}

function sigCfg(sig: string) {
  return SIGNAL_CFG[sig] ?? { color: C.muted, bg: '#1E2D4455', label: sig.replace(/_/g,' '), order: 99 }
}

// ─── Bidirectional flow bar ────────────────────────────────────────────────────

function FlowBar({ value, color }: { value: number; color: string }) {
  const halfPct = Math.min(50, Math.abs(value) / 100 * 50)
  return (
    <div style={{ height: 3, background: '#1A2740', borderRadius: 2, position: 'relative' }}>
      <div style={{
        position: 'absolute', height: '100%', borderRadius: 2, background: color,
        ...(value >= 0
          ? { left: '50%', width: `${halfPct}%` }
          : { right: '50%', width: `${halfPct}%` }),
      }} />
      <div style={{ position: 'absolute', left: '50%', top: -1, width: 1, height: 5, background: '#2D4A6B' }} />
    </div>
  )
}

// ─── Sector card ──────────────────────────────────────────────────────────────

function SectorCard({ s }: { s: Sector }) {
  const cfg   = sigCfg(s.rotation_signal)
  const score = s.combined_score ?? 0
  const fii   = s.FII_flow_score ?? 0
  const dii   = s.DII_flow_score ?? 0
  const sm    = s.Smart_Money_Score ?? 0

  return (
    <Link to={`/sectors/${s.sector}`} style={{ textDecoration: 'none' }}>
      <div style={{
        background: C.card, borderRadius: 8, cursor: 'pointer',
        border: `1px solid #1E2D44`,
        borderTop: `3px solid ${cfg.color}`,
        padding: 14, transition: 'transform 0.12s, box-shadow 0.12s',
      }}
        onMouseEnter={e => {
          e.currentTarget.style.transform = 'translateY(-2px)'
          e.currentTarget.style.boxShadow = `0 4px 20px ${cfg.color}22`
        }}
        onMouseLeave={e => {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.boxShadow = 'none'
        }}
      >
        {/* Header row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
          <div>
            <div style={{ color: C.primary, fontSize: 12, fontWeight: 800, letterSpacing: 0.3, marginBottom: 4 }}>
              {s.sector.replace(/_/g, ' ')}
            </div>
            <span style={{
              fontSize: 8, fontWeight: 700, padding: '2px 7px', borderRadius: 3,
              background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}44`,
              letterSpacing: 0.8, textTransform: 'uppercase',
            }}>
              {cfg.label}
            </span>
          </div>
          <div style={{
            fontSize: 20, fontWeight: 900, fontFamily: 'monospace',
            color: score >= 0 ? C.bull : C.bear, lineHeight: 1,
          }}>
            {score >= 0 ? '+' : ''}{score.toFixed(1)}
          </div>
        </div>

        {/* Flow indicators */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[
            { label: 'FII', val: fii, color: '#3BAEF0', desc: 'Foreign funds' },
            { label: 'DII', val: dii, color: '#9B7BEA', desc: 'Domestic MFs' },
            { label: 'SM',  val: sm,  color: '#22D35E', desc: 'Smart money' },
          ].map(({ label, val, color, desc }) => (
            <div key={label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                <span style={{ color: C.dim, fontSize: 8, fontWeight: 700 }}>{label} ({desc})</span>
                <span style={{ color: val >= 0 ? color : C.bear, fontSize: 9, fontWeight: 700 }}>
                  {val >= 0 ? '+' : ''}{val.toFixed(1)}
                </span>
              </div>
              <FlowBar value={val} color={color} />
            </div>
          ))}
        </div>
      </div>
    </Link>
  )
}

// ─── Signal group header ───────────────────────────────────────────────────────

function GroupHeader({ signal, count }: { signal: string; count: number }) {
  const cfg = sigCfg(signal)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, marginTop: 4 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: cfg.color, flexShrink: 0 }} />
      <span style={{ color: cfg.color, fontSize: 11, fontWeight: 800, letterSpacing: 1.5, textTransform: 'uppercase' }}>
        {cfg.label}
      </span>
      <span style={{ color: C.dim, fontSize: 10 }}>— {count} sector{count !== 1 ? 's' : ''}</span>
      <div style={{ flex: 1, height: 1, background: `${cfg.color}25` }} />
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function SectorsPage() {
  const [filter, setFilter] = useState<'all' | 'positive' | 'negative'>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['sectors'],
    queryFn:  fetchSectors,
    refetchInterval: 300_000,
  })

  if (isLoading) return (
    <div style={{ color: C.muted, textAlign: 'center', padding: 60 }}>
      Loading sector intelligence...
    </div>
  )

  const all = data?.sectors ?? []
  const positive = all.filter(s => (s.combined_score ?? 0) >= 0).length

  // Sort by signal order then by combined score descending
  const sorted = [...all].sort((a, b) => {
    const ao = sigCfg(a.rotation_signal).order
    const bo = sigCfg(b.rotation_signal).order
    if (ao !== bo) return ao - bo
    return (b.combined_score ?? 0) - (a.combined_score ?? 0)
  })

  const filtered = sorted.filter(s => {
    if (filter === 'positive') return (s.combined_score ?? 0) >= 0
    if (filter === 'negative') return (s.combined_score ?? 0) < 0
    return true
  })

  // Group by signal
  const groups: Record<string, Sector[]> = {}
  for (const s of filtered) {
    const sig = s.rotation_signal || 'NEUTRAL'
    if (!groups[sig]) groups[sig] = []
    groups[sig].push(s)
  }

  const sortedGroups = Object.entries(groups).sort(
    ([a], [b]) => (SIGNAL_CFG[a]?.order ?? 99) - (SIGNAL_CFG[b]?.order ?? 99)
  )

  const topSector = all.length > 0
    ? all.reduce((best, s) => (s.combined_score ?? -Infinity) > (best.combined_score ?? -Infinity) ? s : best, all[0])
    : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Page header ──────────────────────────────────────────────────────── */}
      <div style={{
        background: C.card, border: C.border, borderRadius: 8,
        padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ color: C.secondary, fontSize: 10, fontWeight: 700, letterSpacing: 2, marginBottom: 5 }}>
            SECTOR ROTATION INTELLIGENCE — {all.length} SECTORS TRACKED
          </div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ color: C.bull, fontSize: 14, fontWeight: 800 }}>{positive}</span>
            <span style={{ color: C.muted, fontSize: 11 }}>sectors in positive territory</span>
            <span style={{ color: C.bear, fontSize: 14, fontWeight: 800 }}>{all.length - positive}</span>
            <span style={{ color: C.muted, fontSize: 11 }}>sectors under flow pressure</span>
            {topSector && (
              <>
                <span style={{ color: C.dim }}>|</span>
                <span style={{ color: C.muted, fontSize: 11 }}>
                  Best: <span style={{ color: C.bull, fontWeight: 700 }}>{topSector.sector.replace(/_/g,' ')}</span>
                  {' '}({topSector.combined_score != null ? `+${topSector.combined_score.toFixed(1)}` : '--'})
                </span>
              </>
            )}
          </div>
        </div>

        {/* Filter chips */}
        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          {([
            { key: 'all',      label: `All (${all.length})`,         activeColor: '#1E3A5F', activeText: C.secondary },
            { key: 'positive', label: `Positive (${positive})`,       activeColor: '#052E16', activeText: C.bull },
            { key: 'negative', label: `Negative (${all.length - positive})`, activeColor: '#2D0A0A', activeText: C.bear },
          ] as const).map(({ key, label, activeColor, activeText }) => (
            <button key={key}
              onClick={() => setFilter(key)}
              style={{
                padding: '5px 12px', borderRadius: 5, border: C.border, cursor: 'pointer',
                fontSize: 10, fontWeight: 700, letterSpacing: 0.5,
                background: filter === key ? activeColor : 'transparent',
                color: filter === key ? activeText : C.dim,
                transition: 'all 0.15s',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Legend / how to read ─────────────────────────────────────────────── */}
      <div style={{
        background: '#0A1220', border: '1px solid #1E3A5F', borderLeft: `4px solid ${C.blue}`,
        borderRadius: 6, padding: '10px 16px', display: 'flex', gap: 20, flexWrap: 'wrap',
      }}>
        <span style={{ color: C.blue, fontSize: 10, fontWeight: 700, letterSpacing: 1, alignSelf: 'center' }}>HOW TO READ</span>
        {[
          { key: 'Score', desc: 'Combined sector score. Positive = capital is flowing into this sector.' },
          { key: 'FII',   desc: 'Foreign funds (global money) buying (+) or selling (-).' },
          { key: 'DII',   desc: 'Indian MFs & insurance companies buying (+) or selling (-).' },
          { key: 'SM',    desc: 'Smart Money = sophisticated traders. Leading indicator for price direction.' },
        ].map(({ key, desc }) => (
          <div key={key} style={{ display: 'flex', gap: 5 }}>
            <span style={{ color: C.secondary, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>{key}:</span>
            <span style={{ color: C.muted, fontSize: 10 }}>{desc}</span>
          </div>
        ))}
      </div>

      {/* ── Grouped sector cards ─────────────────────────────────────────────── */}
      {sortedGroups.map(([signal, sectors]) => (
        <section key={signal}>
          <GroupHeader signal={signal} count={sectors.length} />
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))',
            gap: 10,
          }}>
            {sectors.map(s => <SectorCard key={s.sector} s={s} />)}
          </div>
        </section>
      ))}

      {filtered.length === 0 && (
        <div style={{ color: C.muted, textAlign: 'center', padding: 40 }}>
          No sectors match the current filter.
        </div>
      )}
    </div>
  )
}
