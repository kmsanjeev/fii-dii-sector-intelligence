import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchStockDetail } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'

function pct(v: number | null | undefined) {
  if (v == null) return '-'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}

export function StockDetailPage() {
  const { symbol } = useParams<{ symbol: string }>()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockDetail(symbol!),
  })

  if (isLoading) return <div className="text-center py-20" style={{ color: '#64748B' }}>Loading {symbol}...</div>
  if (isError || !data) return <div className="text-center py-20" style={{ color: '#EF4444' }}>Symbol {symbol} not found</div>

  const c = data.components

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: '#E2E8F0' }}>{data.symbol}</h1>
          <div className="text-sm mt-1" style={{ color: '#64748B' }}>{data.sector}</div>
          <div className="mt-2"><CapFlowBadge label={data.label} /></div>
        </div>
        <ScoreGauge score={data.bull_run_score} size={90} label="Bull Run" />
      </div>

      {/* Factor breakdown */}
      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>SCORE COMPONENTS (4-factor)</h2>
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Price Score', value: c.price_score, weight: '30%' },
            { label: 'Sector Flow', value: c.sector_flow_score, weight: '25%' },
            { label: 'Deal Score', value: c.deal_score, weight: '25%' },
            { label: 'Corporate', value: c.corporate_score, weight: '20%' },
          ].map(({ label, value, weight }) => (
            <div key={label} className="p-3 rounded border" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
              <div className="text-xs" style={{ color: '#64748B' }}>{label} ({weight})</div>
              <ScoreGauge score={value} size={56} />
            </div>
          ))}
        </div>
        <div className="mt-2 text-xs" style={{ color: '#64748B' }}>
          Regime: {data.market_regime} (x{data.regime_multiplier.toFixed(2)}) | As of: {data.as_of_date}
        </div>
      </section>

      {/* Price returns */}
      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>PRICE PERFORMANCE</h2>
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: '30D Return', value: data.price.ret_30d },
            { label: '90D Return', value: data.price.ret_90d },
            { label: '365D Return', value: data.price.ret_365d },
            { label: 'Vol Ratio', value: data.price.vol_ratio },
          ].map(({ label, value }) => (
            <div key={label} className="p-3 rounded border" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
              <div className="text-xs mb-1" style={{ color: '#64748B' }}>{label}</div>
              <div className="text-lg font-bold" style={{ color: (value ?? 0) >= 0 ? '#22C55E' : '#EF4444' }}>
                {label === 'Vol Ratio' ? (value != null ? `${value.toFixed(1)}x` : '-') : pct(value)}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Deal signals */}
      {data.deal_signals && Object.keys(data.deal_signals).length > 0 && (
        <section>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>INSTITUTIONAL DEALS (30D)</h2>
          <div className="p-3 rounded border text-xs space-y-1" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
            {Object.entries(data.deal_signals as Record<string, unknown>).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span style={{ color: '#64748B' }}>{k}</span>
                <span style={{ color: '#E2E8F0' }}>{String(v)}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
