import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchSectors, type Sector } from '../api/client'
import { Link } from 'react-router-dom'
import { T, FS, FW } from '../styles/tokens'

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

const SIGNAL_CFG: Record<string, { color: string; bg: string; label: string; order: number }> = {
  EARLY_ROTATION:     { color: '#22D35E', bg: '#052E1688', label: 'Early Rotation',     order: 1 },
  STRONG_ACCUMULATION:{ color: '#10B981', bg: '#064E3B55', label: 'Strong Accum.',      order: 2 },
  LEADING:            { color: '#10B981', bg: '#064E3B55', label: 'Leading',             order: 3 },
  MOMENTUM:           { color: '#3BAEF0', bg: '#0C2A4055', label: 'Momentum',            order: 4 },
  PRICE_LED:          { color: '#F5A524', bg: '#45260055', label: 'Price-Led',           order: 5 },
  NEUTRAL:            { color: '#7B90A8', bg: '#1E2D4455', label: 'Neutral',             order: 6 },
  DISTRIBUTION:       { color: '#F44B4B', bg: '#45090955', label: 'Distribution',        order: 7 },
  DECLINING:          { color: '#DC2626', bg: '#3B0A0A55', label: 'Declining',           order: 8 },
}

function sigCfg(sig: string) {
  return SIGNAL_CFG[sig] ?? { color: C.muted, bg: '#1E2D4455', label: sig.replace(/_/g,' '), order: 99 }
}

// ─── Relative score bar (fills from center, colour by sign) ──────────────────

function RelBar({ value }: { value: number }) {
  const pct   = Math.min(50, Math.abs(value) / 100 * 50)
  const color = value >= 0 ? '#22D35E' : '#F44B4B'
  return (
    <div style={{ height: 3, background: '#1A2740', borderRadius: 2, position: 'relative' }}>
      <div style={{
        position: 'absolute', height: '100%', borderRadius: 2, background: color,
        ...(value >= 0
          ? { left: '50%', width: `${pct}%` }
          : { right: '50%', width: `${pct}%` }),
      }} />
      <div style={{ position: 'absolute', left: '50%', top: -1, width: 1, height: 5, background: '#2D4A6B' }} />
    </div>
  )
}

// ─── Compact sub-bar (FII / DII / SM) ────────────────────────────────────────

function FlowBar({ value, color }: { value: number; color: string }) {
  const pct = Math.min(50, Math.abs(value) / 100 * 50)
  return (
    <div style={{ height: 2, background: '#1A2740', borderRadius: 2, position: 'relative' }}>
      <div style={{
        position: 'absolute', height: '100%', borderRadius: 2,
        background: value >= 0 ? color : '#F44B4B',
        ...(value >= 0 ? { left: '50%', width: `${pct}%` } : { right: '50%', width: `${pct}%` }),
      }} />
      <div style={{ position: 'absolute', left: '50%', top: -1, width: 1, height: 4, background: '#2D4A6B' }} />
    </div>
  )
}

// ─── FPI signal chip ─────────────────────────────────────────────────────────

const FPI_COLOR: Record<string, string> = {
  STRONG_ACCUMULATION: '#22D35E',
  ACCUMULATION:        '#10B981',
  NEUTRAL:             '#7B90A8',
  DISTRIBUTION:        '#F44B4B',
  STRONG_DISTRIBUTION: '#DC2626',
}

function FpiChip({ signal, auc_pct }: { signal: string; auc_pct: number | null | undefined }) {
  if (!signal) return null
  const color = FPI_COLOR[signal] ?? '#7B90A8'
  const label = signal.replace('STRONG_', 'STR. ').replace(/_/g, ' ')
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{
        fontSize: FS.label, fontWeight: FW.bold,
        padding: '2px 7px', borderRadius: 3,
        background: `${color}18`, color,
        border: `1px solid ${color}44`, letterSpacing: 0.5,
      }}>FPI {label}</span>
      {auc_pct != null && (
        <span style={{ color: C.secondary, fontSize: FS.label, fontWeight: FW.medium }}>
          {auc_pct.toFixed(1)}% AUC
        </span>
      )}
    </div>
  )
}

// ─── Sector card ──────────────────────────────────────────────────────────────

function SectorCard({ s }: { s: Sector }) {
  const cfg      = sigCfg(s.rotation_signal)
  const rel      = s.relative_score          // cross-sectional ±100, primary
  const zsc      = s.combined_score          // z-score vs 252D baseline, secondary
  const fii      = s.FII_flow_score  ?? 0
  const dii      = s.DII_flow_score  ?? 0
  const sm       = s.Smart_Money_Score ?? 0
  const relColor = rel != null ? (rel >= 0 ? C.bull : C.bear) : C.muted
  const zColor   = zsc != null ? (zsc >= 0 ? C.bull : C.bear) : C.muted

  return (
    <Link to={`/sectors/${s.sector}`} style={{ textDecoration: 'none' }}>
      <div
        style={{
          background: C.card, borderRadius: 8, cursor: 'pointer',
          border: `1px solid ${T.border}`,
          borderTop: `3px solid ${cfg.color}`,
          padding: '14px 14px 12px',
          transition: 'transform 0.12s, box-shadow 0.12s',
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
        {/* Sector name */}
        <div style={{
          color: C.h1, fontSize: FS.body, fontWeight: FW.heavy,
          letterSpacing: 0.3, marginBottom: 6,
        }}>
          {s.sector.replace(/_/g, ' ')}
        </div>

        {/* Signal badge */}
        <span style={{
          display: 'inline-block',
          fontSize: FS.label, fontWeight: FW.bold,
          padding: '3px 8px', borderRadius: 3,
          background: cfg.bg, color: cfg.color,
          border: `1px solid ${cfg.color}44`,
          letterSpacing: 0.8, textTransform: 'uppercase',
          marginBottom: 12,
        }}>
          {cfg.label}
        </span>

        {/* Two big scores side by side */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          {/* Relative Rank */}
          <div style={{
            flex: 1, background: '#ffffff06', borderRadius: 6,
            padding: '8px 10px', borderLeft: `3px solid ${relColor}`,
          }}>
            <div style={{
              color: relColor, fontSize: FS['2xl'], fontWeight: FW.black,
              fontFamily: 'monospace', lineHeight: 1, marginBottom: 4,
            }}>
              {rel != null ? (rel >= 0 ? '+' : '') + rel.toFixed(0) : '--'}
            </div>
            <div style={{
              color: C.muted, fontSize: FS.label, fontWeight: FW.bold,
              letterSpacing: 1, textTransform: 'uppercase',
            }}>
              Relative Rank
            </div>
            <div style={{ color: C.secondary, fontSize: FS.caption, marginTop: 2 }}>
              vs all {s.relative_score != null ? '27' : '--'} sectors today
            </div>
          </div>

          {/* Z-Score */}
          <div style={{
            flex: 1, background: '#ffffff06', borderRadius: 6,
            padding: '8px 10px', borderLeft: `3px solid ${zColor}55`,
          }}>
            <div style={{
              color: zColor, fontSize: FS['2xl'], fontWeight: FW.black,
              fontFamily: 'monospace', lineHeight: 1, marginBottom: 4,
            }}>
              {zsc != null ? (zsc >= 0 ? '+' : '') + zsc.toFixed(1) : '--'}
            </div>
            <div style={{
              color: C.muted, fontSize: FS.label, fontWeight: FW.bold,
              letterSpacing: 1, textTransform: 'uppercase',
            }}>
              Z-Score
            </div>
            <div style={{ color: C.secondary, fontSize: FS.caption, marginTop: 2 }}>
              vs own 1-year avg
            </div>
          </div>
        </div>

        {/* Relative bar */}
        <div style={{ marginBottom: 10 }}>
          <RelBar value={rel ?? 0} />
        </div>

        {/* FPI signal */}
        <FpiChip signal={s.fpi_signal ?? ''} auc_pct={s.auc_pct_of_total} />

        {/* Divider */}
        <div style={{ height: 1, background: T.border, margin: '10px 0 8px' }} />

        {/* FII / DII / SM bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {([
            { label: 'FII (Foreign)', val: fii, color: T.fii },
            { label: 'DII (Domestic)', val: dii, color: T.dii },
            { label: 'Smart Money',    val: sm,  color: T.green },
          ] as const).map(({ label, val, color }) => (
            <div key={label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                <span style={{ color: C.secondary, fontSize: FS.label, fontWeight: FW.bold }}>
                  {label}
                </span>
                <span style={{
                  color: val >= 0 ? color : C.bear,
                  fontSize: FS.label, fontWeight: FW.heavy,
                  fontFamily: 'monospace',
                }}>
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

// ─── Signal group header ──────────────────────────────────────────────────────

function GroupHeader({ signal, count }: { signal: string; count: number }) {
  const cfg = sigCfg(signal)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, marginTop: 4 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: cfg.color, flexShrink: 0 }} />
      <span style={{ color: cfg.color, fontSize: 11, fontWeight: 800, letterSpacing: 1.5, textTransform: 'uppercase' }}>
        {cfg.label}
      </span>
      <span style={{ color: C.muted, fontSize: FS.label }}>— {count} sector{count !== 1 ? 's' : ''}</span>
      <div style={{ flex: 1, height: 1, background: `${cfg.color}25` }} />
    </div>
  )
}

// ─── Regime badge ─────────────────────────────────────────────────────────────

function RegimeBadge({ regime, negPct }: { regime: string; negPct: number }) {
  const cfg = regime === 'NET_SELLER'
    ? { color: T.red,   bg: '#2D0A0A', label: 'FII: NET SELLER' }
    : regime === 'NET_BUYER'
    ? { color: T.green, bg: '#052E16', label: 'FII: NET BUYER' }
    : { color: T.amber, bg: '#2A1800', label: 'FII: MIXED' }
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '6px 14px', borderRadius: 5,
      background: cfg.bg, border: `1px solid ${cfg.color}44`,
    }}>
      <div style={{ width: 7, height: 7, borderRadius: '50%', background: cfg.color, flexShrink: 0 }} />
      <span style={{ color: cfg.color, fontSize: FS.label, fontWeight: FW.heavy, letterSpacing: 0.8 }}>
        {cfg.label}
      </span>
      <span style={{ color: C.muted, fontSize: FS.label }}>
        {negPct}% sectors under selling pressure
      </span>
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

  const all      = data?.sectors ?? []
  const regime   = (data as any)?.fii_regime ?? 'MIXED'
  const negPct   = (data as any)?.fii_neg_pct ?? 0
  const positive = all.filter(s => (s.relative_score ?? 0) >= 0).length

  // Sort by signal order then relative_score descending
  const sorted = [...all].sort((a, b) => {
    const ao = sigCfg(a.rotation_signal).order
    const bo = sigCfg(b.rotation_signal).order
    if (ao !== bo) return ao - bo
    return (b.relative_score ?? 0) - (a.relative_score ?? 0)
  })

  const filtered = sorted.filter(s => {
    if (filter === 'positive') return (s.relative_score ?? 0) >= 0
    if (filter === 'negative') return (s.relative_score ?? 0) < 0
    return true
  })

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
    ? all.reduce((best, s) =>
        (s.relative_score ?? -Infinity) > (best.relative_score ?? -Infinity) ? s : best, all[0])
    : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Page header ───────────────────────────────────────────────── */}
      <div style={{
        background: C.card, border: C.border, borderRadius: 8,
        padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ color: C.secondary, fontSize: 10, fontWeight: 700, letterSpacing: 2, marginBottom: 6 }}>
            SECTOR ROTATION INTELLIGENCE — {all.length} SECTORS TRACKED
          </div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ color: C.bull, fontSize: 14, fontWeight: 800 }}>{positive}</span>
            <span style={{ color: C.muted, fontSize: 11 }}>sectors relatively preferred</span>
            <span style={{ color: C.bear, fontSize: 14, fontWeight: 800 }}>{all.length - positive}</span>
            <span style={{ color: C.muted, fontSize: 11 }}>sectors under relative pressure</span>
            {topSector && (
              <>
                <span style={{ color: C.dim }}>|</span>
                <span style={{ color: C.muted, fontSize: 11 }}>
                  Top: <span style={{ color: C.bull, fontWeight: 700 }}>{topSector.sector.replace(/_/g,' ')}</span>
                  {' '}({topSector.relative_score != null ? (topSector.relative_score >= 0 ? '+' : '') + topSector.relative_score.toFixed(0) : '--'})
                </span>
              </>
            )}
          </div>
        </div>

        <RegimeBadge regime={regime} negPct={negPct} />

        {/* Filter chips */}
        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          {([
            { key: 'all',      label: `All (${all.length})`,         ac: '#1E3A5F', at: C.secondary },
            { key: 'positive', label: `Top Half (${positive})`,       ac: '#052E16', at: C.bull },
            { key: 'negative', label: `Bottom Half (${all.length - positive})`, ac: '#2D0A0A', at: C.bear },
          ] as const).map(({ key, label, ac, at }) => (
            <button key={key}
              onClick={() => setFilter(key)}
              style={{
                padding: '5px 12px', borderRadius: 5, border: C.border, cursor: 'pointer',
                fontSize: 10, fontWeight: 700, letterSpacing: 0.5,
                background: filter === key ? ac : 'transparent',
                color: filter === key ? at : C.dim,
                transition: 'all 0.15s',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── How to read ───────────────────────────────────────────────── */}
      <div style={{
        background: '#0A1220', border: '1px solid #1E3A5F', borderLeft: `4px solid ${C.blue}`,
        borderRadius: 6, padding: '10px 16px', display: 'flex', gap: 20, flexWrap: 'wrap',
      }}>
        <span style={{ color: C.blue, fontSize: 10, fontWeight: 700, letterSpacing: 1, alignSelf: 'center' }}>
          HOW TO READ
        </span>
        {[
          {
            key: 'Relative Rank',
            desc: 'Cross-sectional score ±100. +100 = most preferred sector today, -100 = most avoided. Always readable regardless of market regime.',
          },
          {
            key: 'z (Z-Score)',
            desc: 'Measures FII positioning vs each sector\'s own 1-year baseline. Negative when FII holds less than historical average — useful for spotting conviction moves.',
          },
          {
            key: 'FPI',
            desc: 'Real FPI ownership from NSDL/CDSL fortnightly AUC reports. Accumulation = FPI growing ownership. Most direct ownership signal.',
          },
          {
            key: 'FII / DII / SM',
            desc: 'F&O positioning z-scores per participant. SM (Smart Money) = FII+PRO average. Positive = above their own 1Y average in this sector.',
          },
        ].map(({ key, desc }) => (
          <div key={key} style={{ display: 'flex', gap: 5 }}>
            <span style={{ color: C.secondary, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>{key}:</span>
            <span style={{ color: C.muted, fontSize: 10 }}>{desc}</span>
          </div>
        ))}
      </div>

      {/* ── Grouped sector cards ──────────────────────────────────────── */}
      {sortedGroups.map(([signal, sectors]) => (
        <section key={signal}>
          <GroupHeader signal={signal} count={sectors.length} />
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
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
