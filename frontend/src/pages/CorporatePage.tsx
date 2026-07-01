import { useQuery } from '@tanstack/react-query'
import { fetchDeals, fetchCatalysts } from '../api/client'
import { useNavigate } from 'react-router-dom'

export function CorporatePage() {
  const navigate = useNavigate()
  const { data: deals } = useQuery({ queryKey: ['deals'], queryFn: () => fetchDeals(25, 30), refetchInterval: 300000 })
  const { data: catalysts } = useQuery({ queryKey: ['catalysts'], queryFn: fetchCatalysts, refetchInterval: 300000 })

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
      <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>CORPORATE INTELLIGENCE</h1>

      {/* Deals */}
      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>INSTITUTIONAL DEALS ({deals?.count ?? 0})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid #1E2332', color: '#64748B' }}>
                <th className="text-left py-2 pr-4">Symbol</th>
                <th className="text-right py-2 pr-4">Net (Cr)</th>
                <th className="text-left py-2 pr-4">Dominant</th>
                <th className="text-left py-2 pr-4">Signal</th>
                <th className="text-left py-2 pr-4">Last Deal</th>
              </tr>
            </thead>
            <tbody>
              {(deals?.deals ?? []).map((d: Record<string, unknown>) => {
                const net = Number(d.inst_net_value_cr ?? 0)
                return (
                  <tr key={String(d.symbol)} style={{ borderBottom: '1px solid #1E233240' }}>
                    <td className="py-2 pr-4 font-bold" style={{ color: '#E2E8F0' }}>{String(d.symbol)}</td>
                    <td className="py-2 pr-4 text-right font-bold" style={{ color: net >= 0 ? '#22C55E' : '#EF4444' }}>
                      {net >= 0 ? '+' : ''}{net.toFixed(0)} Cr
                    </td>
                    <td className="py-2 pr-4" style={{ color: '#64748B' }}>{String(d.dominant_participant ?? '')}</td>
                    <td className="py-2 pr-4" style={{ color: '#64748B' }}>{String(d.deal_signal ?? '')}</td>
                    <td className="py-2 pr-4" style={{ color: '#64748B' }}>{String(d.last_deal_date ?? '')}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Upcoming catalysts */}
      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>UPCOMING CATALYSTS ({catalysts?.count ?? 0})</h2>
        <div className="space-y-2">
          {(catalysts?.catalysts ?? []).map((c: Record<string, unknown>, i: number) => (
            <div key={i} className="p-3 rounded border text-xs flex justify-between" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
              <div>
                <span className="font-bold mr-2" style={{ color: '#E2E8F0' }}>{String(c.symbol)}</span>
                <span style={{ color: '#64748B' }}>{String(c.purpose_type)}</span>
              </div>
              <span style={{ color: '#64748B' }}>{String(c.event_date)}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
