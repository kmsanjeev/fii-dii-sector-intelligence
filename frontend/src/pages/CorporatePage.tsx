/**
 * Corporate Intelligence Hub — Phase UI-C
 * Single-scroll page: KPI strip, Announcement Radar, Deal Tape, Action Calendar,
 * Confidence leaderboard, Upcoming Catalysts.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  fetchCorporateSummary, fetchAnnouncements, fetchDealTape, fetchUpcomingActions,
  fetchConfidence, fetchCatalysts,
} from '../api/client'
import { T, FS, FW } from '../styles/tokens'
import { useMobile } from '../hooks/useMobile'

const C = {
  bg: T.bg, panel: T.panel, cell: T.cell, border: `1px solid ${T.border}`,
  h1: T.h1, text: T.text, sub: T.textSub, muted: T.muted, dim: T.dim,
  green: T.green, red: T.red, amber: T.amber, blue: T.blue, teal: T.teal, purple: T.purple,
} as const

const CARD: React.CSSProperties = { background: C.panel, border: C.border, borderRadius: 10 }
const LABEL: React.CSSProperties = {
  color: C.sub, fontSize: FS.label, fontWeight: FW.bold, letterSpacing: 1.5, textTransform: 'uppercase',
}

const PART_COLOR: Record<string, string> = {
  FII: C.blue, MF: C.purple, INSURANCE: '#7C4DFF', PROMOTER: C.amber, RETAIL: C.muted,
}

const ANN_TYPE_COLOR: Record<string, string> = {
  RESULT_UPDATE:     C.green,
  ACQUISITION:       C.amber,
  BOARD_OUTCOME:     C.blue,
  MANAGEMENT_CHANGE: C.purple,
  REGULATORY:        C.red,
  ANALYST_MEET:      C.teal,
  PRESS_RELEASE:     C.muted,
  OTHER:             C.muted,
}

function relTime(dateStr: string): string {
  const d = new Date(dateStr).getTime()
  const diff = Math.floor((Date.now() - d) / 1000)
  if (diff < 3600)   return `${Math.max(1, Math.floor(diff / 60))}m ago`
  if (diff < 86400)  return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

// ─── KPI Strip ──────────────────────────────────────────────────────────────

function KpiStrip({ s }: { s: Record<string, number> | undefined }) {
  if (!s) return null
  const netColor = (s.inst_net_30d_cr ?? 0) >= 0 ? C.green : C.red
  const cells = [
    { label: 'ANNOUNCEMENTS (7D)', value: s.announcements_7d, sub: `${s.high_signal_7d ?? 0} high-signal`, color: C.h1 },
    { label: 'INST. NET FLOW (30D)', value: `${(s.inst_net_30d_cr ?? 0) >= 0 ? '+' : ''}${(s.inst_net_30d_cr ?? 0).toLocaleString('en-IN')} Cr`, sub: `${s.accumulating_30d ?? 0} accum / ${s.distributing_30d ?? 0} distr`, color: netColor },
    { label: 'RESULTS DUE (7D)', value: s.results_7d, sub: `${s.catalysts_60d ?? 0} catalysts in 60D`, color: C.amber },
    { label: 'EX-DATES (14D)', value: s.ex_dates_14d, sub: 'dividend / bonus / split / buyback', color: C.teal },
  ]
  return (
    <div style={{ ...CARD, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', overflow: 'hidden' }}>
      {cells.map((c, i) => (
        <div key={i} style={{ padding: '14px 20px', borderRight: i < 3 ? C.border : 'none' }}>
          <div style={{ ...LABEL, marginBottom: 8 }}>{c.label}</div>
          <div style={{ color: c.color, fontSize: 26, fontWeight: 800, fontFamily: 'monospace', lineHeight: 1 }}>
            {c.value ?? '--'}
          </div>
          <div style={{ color: C.muted, fontSize: 10, marginTop: 6 }}>{c.sub}</div>
        </div>
      ))}
    </div>
  )
}

// ─── Announcement Radar ─────────────────────────────────────────────────────

const ANN_TYPES = ['ALL', 'RESULT_UPDATE', 'ACQUISITION', 'BOARD_OUTCOME', 'MANAGEMENT_CHANGE', 'REGULATORY']

function AnnouncementRadar() {
  const [minScore, setMinScore] = useState(55)
  const [annType, setAnnType]   = useState('ALL')
  const { data } = useQuery({
    queryKey: ['ann-radar', minScore, annType],
    queryFn: () => fetchAnnouncements(3, minScore, annType === 'ALL' ? undefined : annType, 40),
    refetchInterval: 300_000,
  })
  const rows = data?.announcements ?? []

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div style={LABEL}>ANNOUNCEMENT RADAR <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(last 72h, high-signal first)</span></div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {ANN_TYPES.map(t => (
            <button key={t} onClick={() => setAnnType(t)} style={{
              background: annType === t ? `${ANN_TYPE_COLOR[t] ?? C.blue}22` : 'transparent',
              border: `1px solid ${annType === t ? (ANN_TYPE_COLOR[t] ?? C.blue) + '66' : T.border}`,
              borderRadius: 4, color: annType === t ? (ANN_TYPE_COLOR[t] ?? C.blue) : C.muted,
              fontSize: 9, fontWeight: 700, padding: '3px 8px', cursor: 'pointer', letterSpacing: 0.3,
            }}>{t.replace(/_/g, ' ')}</button>
          ))}
          <select value={minScore} onChange={e => setMinScore(Number(e.target.value))} style={{
            background: C.cell, border: `1px solid ${T.border}`, borderRadius: 4, color: C.sub,
            fontSize: 9, fontWeight: 700, padding: '3px 6px',
          }}>
            <option value={0}>ALL SCORES</option>
            <option value={55}>SCORE ≥ 55</option>
            <option value={70}>SCORE ≥ 70</option>
            <option value={85}>SCORE ≥ 85</option>
          </select>
        </div>
      </div>

      {rows.length === 0 && (
        <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '24px 0' }}>No announcements match this filter</div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {rows.map((a, i) => {
          const rec = a as Record<string, unknown>
          const type  = String(rec.announcement_type ?? 'OTHER')
          const score = Number(rec.signal_score ?? 0)
          const color = ANN_TYPE_COLOR[type] ?? C.muted
          return (
            <Link key={i} to={`/stocks/${String(rec.symbol)}`} style={{ textDecoration: 'none' }}>
              <div style={{ display: 'flex', gap: 10, padding: '9px 4px', borderBottom: `1px solid #1E2D44`, alignItems: 'flex-start' }}
                onMouseEnter={e => (e.currentTarget.style.background = C.cell)}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                <div style={{
                  flexShrink: 0, width: 34, textAlign: 'center', color, fontSize: 13, fontWeight: 800,
                  fontFamily: 'monospace', border: `1px solid ${color}44`, borderRadius: 4, padding: '3px 0',
                  background: `${color}12`,
                }}>{score}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                    <span style={{ color: C.h1, fontSize: 12, fontWeight: 700 }}>{String(rec.symbol)}</span>
                    <span style={{
                      fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                      background: `${color}18`, color, border: `1px solid ${color}44`,
                    }}>{type.replace(/_/g, ' ')}</span>
                  </div>
                  <div style={{ color: C.sub, fontSize: 11, lineHeight: 1.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {String(rec.title_snippet ?? '')}
                  </div>
                </div>
                <div style={{ color: C.dim, fontSize: 9, flexShrink: 0, marginTop: 2 }}>{relTime(String(rec.date))}</div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ─── Deal Tape ──────────────────────────────────────────────────────────────

const PARTICIPANTS = ['ALL', 'FII', 'MF', 'INSURANCE', 'PROMOTER', 'RETAIL']

function DealTape() {
  const [participant, setParticipant] = useState('ALL')
  const { data } = useQuery({
    queryKey: ['deal-tape', participant],
    queryFn: () => fetchDealTape(0.5, 30, participant === 'ALL' ? undefined : participant),
    refetchInterval: 300_000,
  })
  const rows = data?.deals ?? []

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div style={LABEL}>DEAL TAPE <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(individual block/bulk deals)</span></div>
        <div style={{ display: 'flex', gap: 6 }}>
          {PARTICIPANTS.map(p => (
            <button key={p} onClick={() => setParticipant(p)} style={{
              background: participant === p ? `${PART_COLOR[p] ?? C.blue}22` : 'transparent',
              border: `1px solid ${participant === p ? (PART_COLOR[p] ?? C.blue) + '66' : T.border}`,
              borderRadius: 4, color: participant === p ? (PART_COLOR[p] ?? C.blue) : C.muted,
              fontSize: 9, fontWeight: 700, padding: '3px 8px', cursor: 'pointer', letterSpacing: 0.3,
            }}>{p}</button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Symbol', 'Client', 'Participant', 'Dir', 'Qty', 'Price', 'Value (Cr)', 'Date'].map((h, i) => (
                <th key={h} style={{
                  padding: '6px 8px', textAlign: i >= 4 ? 'right' : 'left', fontSize: 10, fontWeight: 700,
                  color: C.muted, borderBottom: `1px solid ${T.border}`, whiteSpace: 'nowrap',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((d, i) => {
              const deal = d as Record<string, unknown>
              const part = String(deal.participant ?? 'RETAIL')
              const dir  = String(deal.direction ?? '')
              const val  = Number(deal.value_cr ?? 0)
              return (
                <tr key={i} style={{ borderBottom: '1px solid #1E233220' }}>
                  <td style={{ padding: '6px 8px' }}>
                    <Link to={`/stocks/${String(deal.symbol)}`} style={{ color: C.h1, fontWeight: 700, textDecoration: 'none' }}>
                      {String(deal.symbol)}
                    </Link>
                  </td>
                  <td style={{ padding: '6px 8px', color: C.sub, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {String(deal.client_name ?? '')}
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <span style={{
                      fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 3,
                      background: `${PART_COLOR[part] ?? C.muted}18`, color: PART_COLOR[part] ?? C.muted,
                      border: `1px solid ${PART_COLOR[part] ?? C.muted}44`,
                    }}>{part}</span>
                  </td>
                  <td style={{ padding: '6px 8px', fontWeight: 700, color: dir === 'BUY' ? C.green : C.red }}>{dir}</td>
                  <td style={{ padding: '6px 8px', textAlign: 'right', color: C.sub, fontFamily: 'monospace' }}>
                    {Number(deal.qty ?? 0).toLocaleString('en-IN')}
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'right', color: C.sub, fontFamily: 'monospace' }}>
                    ₹{Number(deal.price ?? 0).toLocaleString('en-IN')}
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'right', fontWeight: 800, fontFamily: 'monospace', color: dir === 'BUY' ? C.green : C.red }}>
                    {val.toFixed(1)}
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'right', color: C.dim, fontSize: 10, whiteSpace: 'nowrap' }}>
                    {String(deal.date ?? '').slice(5)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {rows.length === 0 && (
          <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '24px 0' }}>No deals ≥ 0.5 Cr for this filter</div>
        )}
      </div>
    </div>
  )
}

// ─── Action Calendar ────────────────────────────────────────────────────────

const ACTION_COLOR: Record<string, string> = {
  DIVIDEND: C.green, BONUS: C.teal, SPLIT: C.blue, BUYBACK: C.purple, RIGHTS: C.amber,
}

function ActionCalendar() {
  const { data } = useQuery({ queryKey: ['upcoming-actions'], queryFn: () => fetchUpcomingActions(45, 40), refetchInterval: 600_000 })
  const rows = data?.actions ?? []

  const detail = (a: Record<string, unknown>) => {
    const type = String(a.action_type ?? '')
    if (type === 'DIVIDEND' && a.dividend_rs) return `₹${a.dividend_rs}/share`
    if (type === 'BONUS' && a.bonus_ratio) return String(a.bonus_ratio)
    if (type === 'SPLIT' && a.split_new_fv) return `FV → ₹${a.split_new_fv}`
    return String(a.subject ?? '').slice(0, 40)
  }

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ ...LABEL, marginBottom: 12 }}>CORPORATE ACTION CALENDAR <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(next 45 days, ex-date)</span></div>
      {rows.length === 0 && (
        <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '20px 0' }}>No scheduled ex-dates in this window</div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))', gap: 8 }}>
        {rows.map((a, i) => {
          const act = a as Record<string, unknown>
          const type  = String(act.action_type ?? 'OTHER')
          const color = ACTION_COLOR[type] ?? C.muted
          const exDate = String(act.ex_date_dt ?? '')
          return (
            <Link key={i} to={`/stocks/${String(act.symbol)}`} style={{ textDecoration: 'none' }}>
              <div style={{
                background: C.cell, border: `1px solid ${color}33`, borderLeft: `3px solid ${color}`,
                borderRadius: 6, padding: '10px 12px', transition: 'border-color 0.15s',
              }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = `${color}88`)}
                onMouseLeave={e => { e.currentTarget.style.borderColor = `${color}33`; e.currentTarget.style.borderLeftColor = color }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ color: C.h1, fontSize: 12, fontWeight: 800 }}>{String(act.symbol)}</span>
                  <span style={{
                    fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                    background: `${color}18`, color, border: `1px solid ${color}44`,
                  }}>{type}</span>
                </div>
                <div style={{ color: C.sub, fontSize: 10, marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {detail(act)}
                </div>
                <div style={{ color: C.dim, fontSize: 9 }}>ex-date {exDate.slice(5)}</div>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ─── Confidence Leaderboard ─────────────────────────────────────────────────

function ConfidenceLeaderboard() {
  const { data } = useQuery({ queryKey: ['confidence-lb'], queryFn: () => fetchConfidence(12), refetchInterval: 600_000 })
  const rows = data?.confidence_scores ?? []
  const max = Math.max(...rows.map(r => Number((r as Record<string, unknown>).confidence_score_12m ?? 0)), 1)

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ ...LABEL, marginBottom: 12 }}>MANAGEMENT CONFIDENCE <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(12M rolling, buyback/bonus/dividend weighted)</span></div>
      {rows.length === 0 && (
        <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '20px 0' }}>No confidence scores available</div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {rows.map((r, i) => {
          const rec = r as Record<string, unknown>
          const score = Number(rec.confidence_score_12m ?? 0)
          const pct = Math.max(4, (score / max) * 100)
          return (
            <Link key={i} to={`/stocks/${String(rec.symbol)}`} style={{ textDecoration: 'none' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr 64px', alignItems: 'center', gap: 10 }}>
                <span style={{ color: C.h1, fontSize: 12, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {String(rec.symbol)}
                </span>
                <div style={{ height: 8, background: C.cell, borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: `linear-gradient(90deg, ${C.teal}55, ${C.teal})`, borderRadius: 4 }} />
                </div>
                <span style={{ color: C.teal, fontSize: 12, fontWeight: 800, fontFamily: 'monospace', textAlign: 'right' }}>
                  {score.toFixed(1)} <span style={{ color: C.dim, fontSize: 9, fontWeight: 600 }}>pts</span>
                </span>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ─── Upcoming Catalysts (results-priority) ─────────────────────────────────

function CatalystsPanel() {
  const { data } = useQuery({ queryKey: ['catalysts-hub'], queryFn: fetchCatalysts, refetchInterval: 600_000 })
  const rows = (data?.catalysts ?? []).slice(0, 12)

  return (
    <div style={{ ...CARD, padding: '20px' }}>
      <div style={{ ...LABEL, marginBottom: 12 }}>UPCOMING CATALYSTS <span style={{ color: C.dim, fontWeight: 400, letterSpacing: 0 }}>(next 60D, sector-flow weighted)</span></div>
      {rows.length === 0 && (
        <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: '20px 0' }}>No catalysts in the next 60 days</div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {rows.map((c, i) => {
          const cat = c as Record<string, unknown>
          const dateStr = String(cat.event_date ?? '')
          const score = Number(cat.catalyst_score ?? NaN)
          return (
            <Link key={i} to={`/stocks/${String(cat.symbol)}`} style={{ textDecoration: 'none' }}>
              <div style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: `1px solid #1E2D44`, alignItems: 'center' }}>
                <div style={{
                  flexShrink: 0, background: '#1A1508', border: '1px solid #F5A52455',
                  borderRadius: 5, padding: '4px 7px', textAlign: 'center', minWidth: 34,
                }}>
                  <div style={{ color: C.amber, fontSize: 11, fontWeight: 800, lineHeight: 1 }}>{dateStr.slice(8)}</div>
                  <div style={{ color: C.muted, fontSize: 8, marginTop: 1 }}>{dateStr.slice(5, 7)}</div>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: C.h1, fontSize: 12, fontWeight: 700 }}>{String(cat.symbol)}</div>
                  <div style={{ color: C.muted, fontSize: 9, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {String(cat.purpose_type ?? '').replace(/_/g, ' ')} · {String(cat.sector ?? '')}
                  </div>
                </div>
                {Number.isFinite(score) && (
                  <div style={{ color: C.amber, fontSize: 12, fontWeight: 800, fontFamily: 'monospace', flexShrink: 0 }}>{score.toFixed(0)}</div>
                )}
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

// ─── Main Page ──────────────────────────────────────────────────────────────

export function CorporatePage() {
  const isMobile = useMobile()
  const { data: summary } = useQuery({ queryKey: ['corp-summary'], queryFn: fetchCorporateSummary, refetchInterval: 300_000 })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <h1 style={{ fontSize: 15, fontWeight: 800, letterSpacing: 2, color: C.h1 }}>CORPORATE INTELLIGENCE</h1>

      <KpiStrip s={summary} />

      <AnnouncementRadar />

      <DealTape />

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.4fr 1fr', gap: 14, alignItems: 'start' }}>
        <ActionCalendar />
        <ConfidenceLeaderboard />
      </div>

      <CatalystsPanel />
    </div>
  )
}
