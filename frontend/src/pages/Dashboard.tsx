import { useQuery } from '@tanstack/react-query'
import { fetchRegime, fetchSectors, fetchWatchlist, fetchParticipantLatest } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { FlowCard } from '../components/platform/FlowCard'
import { SectorTile } from '../components/platform/SectorTile'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { Link } from 'react-router-dom'

export function Dashboard() {
  const { data: regime } = useQuery({ queryKey: ['regime'], queryFn: fetchRegime, refetchInterval: 300000 })
  const { data: sectors } = useQuery({ queryKey: ['sectors'], queryFn: fetchSectors, refetchInterval: 300000 })
  const { data: watchlist } = useQuery({ queryKey: ['watchlist', 'EMERGING'], queryFn: () => fetchWatchlist('EMERGING', 10), refetchInterval: 300000 })
  const { data: participant } = useQuery({ queryKey: ['participant_latest'], queryFn: fetchParticipantLatest, refetchInterval: 300000 })

  const topSectors = (sectors?.sectors ?? []).slice(0, 6)
  const topStocks = (watchlist?.stocks ?? []).slice(0, 8)
  const flows = regime?.flow_scores

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>DASHBOARD</h1>

      {/* Participant Flows */}
      {flows && (
        <section>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>PARTICIPANT FLOWS</h2>
          <div className="grid grid-cols-4 gap-3">
            <FlowCard participant="FII" score={flows.FII} conviction={participant?.FII_conviction} />
            <FlowCard participant="DII" score={flows.DII} conviction={participant?.DII_conviction} />
            <FlowCard participant="PRO" score={flows.PRO} />
            <FlowCard participant="CLIENT" score={flows.CLIENT} />
          </div>
        </section>
      )}

      {/* Top Sectors */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs tracking-widest" style={{ color: '#64748B' }}>TOP SECTORS</h2>
          <Link to="/sectors" className="text-xs" style={{ color: '#3B82F6' }}>View all</Link>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {topSectors.map(s => (
            <Link key={s.sector} to={`/sectors/${s.sector}`}>
              <SectorTile sector={s} />
            </Link>
          ))}
        </div>
      </section>

      {/* Top Watchlist */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs tracking-widest" style={{ color: '#64748B' }}>EMERGING WATCHLIST</h2>
          <Link to="/watchlist" className="text-xs" style={{ color: '#3B82F6' }}>View all ({watchlist?.count ?? 0})</Link>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {topStocks.map(stock => (
            <Link
              key={stock.symbol}
              to={`/stocks/${stock.symbol}`}
              className="p-3 rounded border hover:brightness-110 transition-all"
              style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-bold text-sm" style={{ color: '#E2E8F0' }}>{stock.symbol}</div>
                  <div className="text-xs truncate mt-0.5" style={{ color: '#64748B' }}>{stock.sector}</div>
                </div>
                <ScoreGauge score={stock.bull_run_score} size={44} />
              </div>
              <div className="mt-2">
                <CapFlowBadge label={stock.label} />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Smart Money Summary */}
      {participant && (
        <section>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>SMART MONEY SIGNALS</h2>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Smart Money Score', value: participant.Smart_Money_Score, suffix: '' },
              { label: 'Market Opportunity', value: participant.Market_Opportunity, suffix: '' },
              { label: 'FII/DII Divergence', value: participant.FII_DII_Divergence, suffix: 'σ' },
            ].map(({ label, value, suffix }) => (
              <div key={label} className="p-3 rounded border" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
                <div className="text-xs mb-1" style={{ color: '#64748B' }}>{label}</div>
                <div className="text-lg font-bold" style={{ color: value >= 0 ? '#22C55E' : '#EF4444' }}>
                  {value >= 0 ? '+' : ''}{value.toFixed(2)}{suffix}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
