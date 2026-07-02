import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchParticipantLatest, fetchParticipantHistory } from '../api/client'
import { FlowCard } from '../components/platform/FlowCard'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Legend, BarChart, Bar, ReferenceLine,
} from 'recharts'
import { useNavigate } from 'react-router-dom'

const S = { color: '#64748B', fontSize: 9, letterSpacing: 1 } as const

const PERIOD_OPTIONS = [
  { label: '30D',  days: 30  },
  { label: '90D',  days: 90  },
  { label: '180D', days: 180 },
  { label: '1Y',   days: 252 },
]

function DivergenceInterpretation({
  fii, dii, smart, retail, divergence,
}: {
  fii: number; dii: number; smart: number; retail: number; divergence: number
}) {
  const lines: { text: string; color: string }[] = []

  if (fii > 1 && dii > 1)
    lines.push({ text: 'FII + DII both accumulating — broad institutional conviction. Historically precedes sustained rally.', color: '#22C55E' })
  else if (fii > 1 && dii < -1)
    lines.push({ text: 'FII buying while DII selling — foreign led rally. DII caution is a mild headwind; watch for confirmation.', color: '#F59E0B' })
  else if (fii < -1 && dii > 1)
    lines.push({ text: 'FII exiting while DII absorbing — DII acting as last buyer. Typical pre-consolidation setup. Not a buy signal.', color: '#F59E0B' })
  else if (fii < -1 && dii < -1)
    lines.push({ text: 'FII + DII both reducing — institutional distribution. High risk of further downside. Reduce exposure.', color: '#EF4444' })
  else
    lines.push({ text: 'Flows are within normal range — no strong directional signal from institutional participants.', color: '#64748B' })

  if (Math.abs(divergence) > 2)
    lines.push({
      text: `FII/DII divergence at ${Math.abs(divergence).toFixed(1)}σ — extreme divergence. ${divergence < 0 ? 'FII pressure dominant; short-term weakness likely.' : 'DII pressure; possible base forming.'}`,
      color: '#8B5CF6',
    })

  if (smart > 1 && retail < -1)
    lines.push({ text: 'Smart money buying while retail exits — classic accumulation pattern. Bullish for 15–45 days.', color: '#22C55E' })
  if (smart < -1 && retail > 1)
    lines.push({ text: 'Smart money selling into retail buying — distribution. High reversal risk.', color: '#EF4444' })

  return (
    <div style={{ padding: '12px 16px', borderRadius: 6, background: '#0D1117', border: '1px solid #1E2332' }}>
      <div style={{ ...S, marginBottom: 8 }}>FLOW INTERPRETATION</div>
      {lines.map((l, i) => (
        <div key={i} style={{ color: l.color, fontSize: 11, marginBottom: 4, display: 'flex', gap: 6 }}>
          <span style={{ flexShrink: 0 }}>&#9679;</span>
          <span>{l.text}</span>
        </div>
      ))}
    </div>
  )
}

function CashFlowPanel({ cash }: { cash: { fpi_5d_cr: number; mf_5d_cr: number; insurance_5d_cr: number; fpi_20d_cr: number; mf_20d_cr: number } }) {
  const rows = [
    { label: 'FII / FPI (5D net)',     value: cash.fpi_5d_cr,       color: '#22C55E' },
    { label: 'MF / DII (5D net)',      value: cash.mf_5d_cr,        color: '#3B82F6' },
    { label: 'Insurance (5D net)',     value: cash.insurance_5d_cr, color: '#8B5CF6' },
    { label: 'FII / FPI (20D net)',    value: cash.fpi_20d_cr,      color: '#22C55E' },
    { label: 'MF / DII (20D net)',     value: cash.mf_20d_cr,       color: '#3B82F6' },
  ]
  return (
    <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16 }}>
      <div style={{ ...S, marginBottom: 12 }}>CASH MARKET FLOWS (Cr)</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {rows.map(({ label, value, color }) => {
          const sign = value >= 0 ? '+' : ''
          const barW = Math.min(100, Math.abs(value) / 8000 * 100)
          return (
            <div key={label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                <span style={{ color: '#94A3B8' }}>{label}</span>
                <span style={{ color, fontWeight: 700 }}>{sign}{value.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr</span>
              </div>
              <div style={{ height: 4, background: '#1E2332', borderRadius: 2 }}>
                <div style={{ width: `${barW}%`, height: '100%', background: color, borderRadius: 2, opacity: value < 0 ? 0.5 : 1 }} />
              </div>
            </div>
          )
        })}
      </div>
      <div style={{ marginTop: 10, fontSize: 10, color: '#334155' }}>
        Source: NSE cash market filings (FPI = FII in cash segment, MF = domestic mutual funds)
      </div>
    </div>
  )
}

export function ParticipantPage() {
  const navigate = useNavigate()
  const [period, setPeriod] = useState(90)

  const { data: latest }  = useQuery({ queryKey: ['participant_latest'],       queryFn: fetchParticipantLatest,              refetchInterval: 300000 })
  const { data: history } = useQuery({ queryKey: ['participant_history', 252], queryFn: () => fetchParticipantHistory(252), refetchInterval: 300000 })

  const chartData = (history?.rows ?? []).slice(-period)

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} style={{
        display: 'flex', alignItems: 'center', gap: 6, background: 'none',
        border: '1px solid #1E2332', color: '#64748B', cursor: 'pointer',
        padding: '4px 12px', borderRadius: 4, fontSize: 11,
      }}>&larr; Back</button>

      <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>PARTICIPANT INTELLIGENCE</h1>

      {latest && (
        <>
          {/* ── F&O Flow cards (FIXED: use actual flow scores) ─────────────── */}
          <section>
            <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>F&amp;O FLOW SCORES (z-score, 60D window)</h2>
            <div className="grid grid-cols-4 gap-3">
              <FlowCard participant="FII"    score={latest.FII_flow_score}    conviction={latest.FII_conviction} />
              <FlowCard participant="DII"    score={latest.DII_flow_score}    conviction={latest.DII_conviction} />
              <FlowCard participant="PRO"    score={latest.PRO_flow_score} />
              <FlowCard participant="CLIENT" score={latest.CLIENT_flow_score} />
            </div>
          </section>

          {/* ── Cash market sub-participant flows ───────────────────────────── */}
          <section>
            <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>CASH MARKET SUB-PARTICIPANTS</h2>
            <div className="grid grid-cols-4 gap-3">
              <FlowCard participant="FPI (FII cash)"  score={latest.FPI_flow_score} />
              <FlowCard participant="MF (Mutual Fund)" score={latest.MF_flow_score} />
              <FlowCard participant="Insurance"        score={latest.INSURANCE_flow_score} />
              <FlowCard participant="Retail"           score={latest.RETAIL_flow_score} />
            </div>
          </section>

          {/* ── Signal boxes ────────────────────────────────────────────────── */}
          <section>
            <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>DERIVED SIGNALS</h2>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Regime',                  value: latest.Market_Regime,            isText: true },
                { label: 'FII/DII Divergence',      value: latest.FII_DII_Divergence,       suffix: 'σ' },
                { label: 'Smart/Retail Div',        value: latest.Smart_Retail_Divergence,  suffix: 'σ' },
                { label: 'Smart Money Score',       value: latest.Smart_Money_Score },
                { label: 'Cash Institutional Score',value: latest.Cash_Institutional_Score },
                { label: 'Data Date',               value: latest.date, isText: true },
              ].map(({ label, value, suffix, isText }) => (
                <div key={label} className="p-3 rounded border" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
                  <div className="text-xs mb-1" style={{ color: '#64748B' }}>{label}</div>
                  {isText ? (
                    <div className="font-bold text-sm" style={{ color: '#E2E8F0' }}>{String(value)}</div>
                  ) : (
                    <div className="text-lg font-bold" style={{ color: (value as number) >= 0 ? '#22C55E' : '#EF4444' }}>
                      {(value as number) >= 0 ? '+' : ''}{(value as number).toFixed(2)}{suffix ?? ''}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* ── Interpretation ───────────────────────────────────────────────── */}
          <DivergenceInterpretation
            fii={latest.FII_flow_score}
            dii={latest.DII_flow_score}
            smart={latest.Smart_Money_Score}
            retail={latest.RETAIL_flow_score}
            divergence={latest.FII_DII_Divergence}
          />

          {/* ── Cash flows panel ─────────────────────────────────────────────── */}
          {latest.cash_flows && <CashFlowPanel cash={latest.cash_flows} />}
        </>
      )}

      {/* ── Flow history charts ──────────────────────────────────────────────── */}
      {chartData.length > 0 && (
        <section>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h2 className="text-xs tracking-widest" style={{ color: '#64748B' }}>FII vs DII FLOW SCORE</h2>
            <div style={{ display: 'flex', gap: 6 }}>
              {PERIOD_OPTIONS.map(o => (
                <button
                  key={o.label} onClick={() => setPeriod(o.days)}
                  style={{
                    padding: '3px 10px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
                    border: `1px solid ${period === o.days ? '#22C55E' : '#1E2332'}`,
                    background: 'transparent', color: period === o.days ? '#22C55E' : '#64748B',
                  }}
                >{o.label}</button>
              ))}
            </div>
          </div>
          <div style={{ backgroundColor: '#141720', borderRadius: 8, padding: 16 }}>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="fii" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#22C55E" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="dii" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748B' }} tickLine={false} axisLine={false} interval={Math.floor(period / 6)} />
                <YAxis tick={{ fontSize: 9, fill: '#64748B' }} tickLine={false} axisLine={false} />
                <ReferenceLine y={0} stroke="#1E2332" strokeDasharray="3 3" />
                <Tooltip contentStyle={{ backgroundColor: '#141720', border: '1px solid #1E2332', fontSize: 11 }} labelStyle={{ color: '#64748B' }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Area type="monotone" dataKey="FII_flow_score" name="FII (F&O)" stroke="#22C55E" fill="url(#fii)" strokeWidth={1.5} dot={false} />
                <Area type="monotone" dataKey="DII_flow_score" name="DII (F&O)" stroke="#3B82F6" fill="url(#dii)" strokeWidth={1.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* ── Cash participant bar chart ──────────────────────────────────────── */}
      {chartData.length > 0 && chartData[0] && 'FPI_flow_5D' in chartData[0] && (
        <section>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>FPI vs MF CASH FLOWS (5D ROLLING, Cr)</h2>
          <div style={{ backgroundColor: '#141720', borderRadius: 8, padding: 16 }}>
            <ResponsiveContainer width="100%" height={180}>
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
        </section>
      )}
    </div>
  )
}
