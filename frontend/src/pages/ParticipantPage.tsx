import { useQuery } from '@tanstack/react-query'
import { fetchParticipantLatest, fetchParticipantHistory } from '../api/client'
import { FlowCard } from '../components/platform/FlowCard'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useNavigate } from 'react-router-dom'

export function ParticipantPage() {
  const navigate = useNavigate()
  const { data: latest } = useQuery({ queryKey: ['participant_latest'], queryFn: fetchParticipantLatest, refetchInterval: 300000 })
  const { data: history } = useQuery({ queryKey: ['participant_history', 252], queryFn: () => fetchParticipantHistory(252), refetchInterval: 300000 })

  const chartData = (history?.rows ?? []).slice(-90)

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate(-1)}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'none', border: '1px solid #1E2332',
          color: '#64748B', cursor: 'pointer',
          padding: '4px 12px', borderRadius: 4, fontSize: 11,
        }}
      >&larr; Back</button>
      <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>PARTICIPANT INTELLIGENCE</h1>

      {latest && (
        <>
          {/* Flow cards */}
          <section>
            <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>CURRENT FLOWS (F&O)</h2>
            <div className="grid grid-cols-4 gap-3">
              <FlowCard participant="FII" score={0} conviction={latest.FII_conviction} />
              <FlowCard participant="DII" score={0} conviction={latest.DII_conviction} />
              <FlowCard participant="Smart Money" score={latest.Smart_Money_Score} />
              <FlowCard participant="Retail" score={latest.Retail_Score} />
            </div>
          </section>

          {/* Divergence + Ensemble */}
          <section>
            <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>SIGNALS</h2>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Regime', value: latest.Market_Regime, isText: true },
                { label: 'FII/DII Divergence', value: latest.FII_DII_Divergence, suffix: 'σ' },
                { label: 'Smart/Retail Div', value: latest.Smart_Retail_Divergence, suffix: 'σ' },
                { label: 'Market Opportunity', value: latest.Market_Opportunity },
                { label: 'Ensemble Score', value: latest.Ensemble_Score },
                { label: 'Data Date', value: latest.date, isText: true },
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
        </>
      )}

      {/* Flow history chart */}
      {chartData.length > 0 && (
        <section>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>FII vs DII FLOW SCORE (90D)</h2>
          <div style={{ backgroundColor: '#141720', borderRadius: 8, padding: 16 }}>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="fii" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22C55E" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="dii" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} tickLine={false} axisLine={false} interval={14} />
                <YAxis tick={{ fontSize: 10, fill: '#64748B' }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#141720', border: '1px solid #1E2332', fontSize: 11 }}
                  labelStyle={{ color: '#64748B' }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="FII_flow_score" name="FII" stroke="#22C55E" fill="url(#fii)" strokeWidth={1.5} dot={false} />
                <Area type="monotone" dataKey="DII_flow_score" name="DII" stroke="#3B82F6" fill="url(#dii)" strokeWidth={1.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}
    </div>
  )
}
