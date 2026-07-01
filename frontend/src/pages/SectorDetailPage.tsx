import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchSectorDetail } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'

export function SectorDetailPage() {
  const { sector } = useParams<{ sector: string }>()
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['sector', sector],
    queryFn: () => fetchSectorDetail(sector!),
  })

  const BackBtn = () => (
    <button
      onClick={() => navigate(-1)}
      style={{
        display: 'flex', alignItems: 'center', gap: 6,
        background: 'none', border: '1px solid #1E2332',
        color: '#64748B', cursor: 'pointer',
        padding: '4px 12px', borderRadius: 4, fontSize: 11,
        marginBottom: 16,
      }}
    >
      &larr; Back
    </button>
  )

  if (isLoading) return <div className="text-center py-20" style={{ color: '#64748B' }}>Loading {sector}...</div>
  if (!data) return (
    <div>
      <BackBtn />
      <div className="text-center py-20" style={{ color: '#EF4444' }}>Sector {sector} not found</div>
    </div>
  )

  return (
    <div className="max-w-3xl space-y-6">
      <BackBtn />
      <div>
        <h1 className="text-2xl font-bold" style={{ color: '#E2E8F0' }}>{data.sector}</h1>
        <div className="text-sm mt-1" style={{ color: '#64748B' }}>{data.rotation_signal} | Score: {data.combined_score.toFixed(1)}</div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'FII Flow', value: data.FII_flow_score },
          { label: 'DII Flow', value: data.DII_flow_score },
          { label: 'Smart Money', value: data.Smart_Money_Score },
        ].map(({ label, value }) => (
          <div key={label} className="p-3 rounded border" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
            <div className="text-xs mb-1" style={{ color: '#64748B' }}>{label}</div>
            <div className="text-lg font-bold" style={{ color: (value ?? 0) >= 0 ? '#22C55E' : '#EF4444' }}>
              {(value ?? 0) >= 0 ? '+' : ''}{(value ?? 0).toFixed(2)}
            </div>
          </div>
        ))}
      </div>

      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>TOP STOCKS IN SECTOR</h2>
        <div className="space-y-2">
          {(data.top_stocks ?? []).map((s: { symbol: string; bull_run_score: number; label: string }) => (
            <Link
              key={s.symbol}
              to={`/stocks/${s.symbol}`}
              className="flex items-center justify-between p-3 rounded border hover:brightness-110 transition-all"
              style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}
            >
              <div className="flex items-center gap-4">
                <span className="font-bold text-sm" style={{ color: '#E2E8F0' }}>{s.symbol}</span>
                <CapFlowBadge label={s.label} />
              </div>
              <ScoreGauge score={s.bull_run_score} size={42} />
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
