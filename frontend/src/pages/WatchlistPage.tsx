import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchAllStocks } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { Link, useNavigate } from 'react-router-dom'

const LABELS = ['ALL', 'STRONG_CANDIDATE', 'EMERGING', 'WATCHLIST', 'NEUTRAL', 'AVOID']

export function WatchlistPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [labelFilter, setLabelFilter] = useState('EMERGING')

  const { data, isLoading } = useQuery({
    queryKey: ['all_stocks', page, labelFilter],
    queryFn: () => fetchAllStocks(page, 50, labelFilter),
    refetchInterval: 300000,
  })

  return (
    <div className="space-y-4">
      <button
        onClick={() => navigate(-1)}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'none', border: '1px solid #1E2332',
          color: '#64748B', cursor: 'pointer',
          padding: '4px 12px', borderRadius: 4, fontSize: 11,
        }}
      >&larr; Back</button>
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
          WATCHLIST <span className="text-sm font-normal ml-2" style={{ color: '#64748B' }}>{data?.total ?? 0} symbols</span>
        </h1>
        <div className="flex gap-2">
          {LABELS.map(l => (
            <button
              key={l}
              className="px-2 py-1 rounded text-xs border transition-all"
              style={{
                borderColor: labelFilter === l ? '#22C55E' : '#1E2332',
                color: labelFilter === l ? '#22C55E' : '#64748B',
                backgroundColor: '#141720',
              }}
              onClick={() => { setLabelFilter(l); setPage(1) }}
            >
              {l === 'ALL' ? 'All' : l.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <div className="text-center py-20" style={{ color: '#64748B' }}>Loading...</div>}

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ borderBottom: '1px solid #1E2332', color: '#64748B' }}>
              <th className="text-left py-2 pr-4">Symbol</th>
              <th className="text-left py-2 pr-4">Sector</th>
              <th className="text-right py-2 pr-4">Score</th>
              <th className="text-left py-2 pr-4">Label</th>
              <th className="text-right py-2 pr-4">30D Ret</th>
              <th className="text-right py-2 pr-4">365D Ret</th>
            </tr>
          </thead>
          <tbody>
            {(data?.stocks ?? []).map(s => (
              <tr
                key={s.symbol}
                style={{ borderBottom: '1px solid #1E233240' }}
                className="hover:brightness-125 transition-all"
              >
                <td className="py-2 pr-4">
                  <Link to={`/stocks/${s.symbol}`} className="font-bold" style={{ color: '#E2E8F0' }}>
                    {s.symbol}
                  </Link>
                </td>
                <td className="py-2 pr-4" style={{ color: '#64748B' }}>{s.sector}</td>
                <td className="py-2 pr-4 text-right">
                  <ScoreGauge score={s.bull_run_score} size={36} />
                </td>
                <td className="py-2 pr-4"><CapFlowBadge label={s.label} /></td>
                <td className="py-2 pr-4 text-right" style={{ color: (s.price?.ret_30d ?? 0) >= 0 ? '#22C55E' : '#EF4444' }}>
                  {s.price?.ret_30d != null ? `${s.price.ret_30d > 0 ? '+' : ''}${s.price.ret_30d.toFixed(1)}%` : '-'}
                </td>
                <td className="py-2 pr-4 text-right" style={{ color: (s.price?.ret_365d ?? 0) >= 0 ? '#22C55E' : '#EF4444' }}>
                  {s.price?.ret_365d != null ? `${s.price.ret_365d > 0 ? '+' : ''}${s.price.ret_365d.toFixed(1)}%` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex gap-2 justify-center">
        {page > 1 && <button onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded text-xs" style={{ backgroundColor: '#141720', color: '#64748B', border: '1px solid #1E2332' }}>Prev</button>}
        <span className="px-3 py-1 text-xs" style={{ color: '#64748B' }}>Page {page}</span>
        {(data?.stocks?.length ?? 0) === 50 && <button onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded text-xs" style={{ backgroundColor: '#141720', color: '#64748B', border: '1px solid #1E2332' }}>Next</button>}
      </div>
    </div>
  )
}
