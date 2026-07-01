import { useParams, useNavigate } from 'react-router-dom'
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
  const navigate = useNavigate()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockDetail(symbol!),
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

  if (isLoading) return <div className="text-center py-20" style={{ color: '#64748B' }}>Loading {symbol}...</div>
  if (isError || !data) return (
    <div>
      <BackBtn />
      <div className="text-center py-20" style={{ color: '#EF4444' }}>Symbol {symbol} not found</div>
    </div>
  )

  const c = data.components

  return (
    <div className="max-w-3xl space-y-6">
      <BackBtn />
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

      {/* Fundamentals (Phase 15B) */}
      {data.fundamentals && data.fundamentals.valuation_score != null && (
        <section>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>
            FUNDAMENTALS
            {data.fundamentals.as_of_date ? <span className="ml-2 font-normal">({data.fundamentals.as_of_date})</span> : null}
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {/* Left: financials */}
            <div className="p-3 rounded border text-xs space-y-2" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
              {[
                { label: 'Revenue TTM', value: data.fundamentals.revenue_ttm_cr != null ? `₹${Number(data.fundamentals.revenue_ttm_cr).toLocaleString('en-IN')} Cr` : '-' },
                { label: 'Net Profit TTM', value: data.fundamentals.profit_ttm_cr != null ? `₹${Number(data.fundamentals.profit_ttm_cr).toLocaleString('en-IN')} Cr` : '-' },
                { label: 'YoY Revenue', value: data.fundamentals.yoy_revenue_pct != null ? `${Number(data.fundamentals.yoy_revenue_pct) >= 0 ? '+' : ''}${Number(data.fundamentals.yoy_revenue_pct).toFixed(1)}%` : '-' },
                { label: 'YoY Profit', value: data.fundamentals.yoy_profit_pct != null ? `${Number(data.fundamentals.yoy_profit_pct) >= 0 ? '+' : ''}${Number(data.fundamentals.yoy_profit_pct).toFixed(1)}%` : '-' },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between">
                  <span style={{ color: '#64748B' }}>{label}</span>
                  <span style={{ color: '#E2E8F0' }}>{value}</span>
                </div>
              ))}
            </div>
            {/* Right: ratios + valuation */}
            <div className="p-3 rounded border text-xs space-y-2" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
              {[
                { label: 'P/E Ratio', value: data.fundamentals.pe_ratio != null ? Number(data.fundamentals.pe_ratio).toFixed(1) : '-' },
                { label: 'ROE', value: data.fundamentals.roe_pct != null ? `${Number(data.fundamentals.roe_pct).toFixed(1)}%` : '-' },
                { label: 'Valuation Score', value: data.fundamentals.valuation_score != null ? Number(data.fundamentals.valuation_score).toFixed(1) : '-' },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between">
                  <span style={{ color: '#64748B' }}>{label}</span>
                  <span style={{ color: '#E2E8F0' }}>{value}</span>
                </div>
              ))}
              {data.fundamentals.valuation_label && (
                <div className="mt-2 text-center font-bold text-xs py-1 rounded" style={{
                  backgroundColor: data.fundamentals.valuation_label === 'CHEAP_QUALITY' ? '#14532D' :
                                   data.fundamentals.valuation_label === 'FAIR_VALUE'    ? '#1E3A5F' :
                                   data.fundamentals.valuation_label === 'MODERATE'      ? '#422006' : '#450A0A',
                  color: data.fundamentals.valuation_label === 'CHEAP_QUALITY' ? '#4ADE80' :
                         data.fundamentals.valuation_label === 'FAIR_VALUE'    ? '#60A5FA' :
                         data.fundamentals.valuation_label === 'MODERATE'      ? '#FB923C' : '#F87171',
                }}>
                  {String(data.fundamentals.valuation_label).replace(/_/g, ' ')}
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Shareholding (Phase 15C) */}
      {data.shareholding && data.shareholding.promoter_pct != null && (
        <section>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>
            SHAREHOLDING PATTERN
            {data.shareholding.window_label ? <span className="ml-2 font-normal">({data.shareholding.window_label})</span> : null}
          </h2>
          <div className="p-3 rounded border" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
            {[
              { label: 'Promoters', value: data.shareholding.promoter_pct, color: '#A78BFA' },
              { label: 'FII',       value: data.shareholding.fii_pct,      color: '#22C55E' },
              { label: 'DII',       value: data.shareholding.dii_pct,      color: '#3B82F6' },
              { label: 'Public',    value: data.shareholding.public_pct,   color: '#64748B' },
            ].map(({ label, value, color }) => {
              const pctVal = value != null ? Number(value) : null
              const barW = pctVal != null ? Math.min(100, pctVal) : 0
              return (
                <div key={label} className="mb-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: '#94A3B8' }}>{label}</span>
                    <span style={{ color }}>{pctVal != null ? `${pctVal.toFixed(2)}%` : '-'}</span>
                  </div>
                  <div style={{ height: 4, backgroundColor: '#1E2332', borderRadius: 2 }}>
                    <div style={{ width: `${barW}%`, height: '100%', backgroundColor: color, borderRadius: 2 }} />
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

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
