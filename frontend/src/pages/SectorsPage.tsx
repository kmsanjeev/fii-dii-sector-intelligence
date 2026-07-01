import { useQuery } from '@tanstack/react-query'
import { fetchSectors } from '../api/client'
import { SectorTile } from '../components/platform/SectorTile'
import { Link, useNavigate } from 'react-router-dom'

const SIGNAL_ORDER = ['EARLY_ROTATION', 'LEADING', 'MOMENTUM', 'EMERGING', 'LAGGING', 'DECLINING']

const backBtn = (navigate: ReturnType<typeof useNavigate>) => (
  <button
    onClick={() => navigate(-1)}
    style={{
      display: 'flex', alignItems: 'center', gap: 6,
      background: 'none', border: '1px solid #1E2332',
      color: '#64748B', cursor: 'pointer',
      padding: '4px 12px', borderRadius: 4, fontSize: 11, marginBottom: 16,
    }}
  >&larr; Back</button>
)

export function SectorsPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({ queryKey: ['sectors'], queryFn: fetchSectors, refetchInterval: 300000 })

  if (isLoading) return <div className="text-center py-20" style={{ color: '#64748B' }}>Loading sector intelligence...</div>

  const sorted = [...(data?.sectors ?? [])].sort((a, b) => {
    const ai = SIGNAL_ORDER.indexOf(a.rotation_signal)
    const bi = SIGNAL_ORDER.indexOf(b.rotation_signal)
    if (ai !== bi) return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
    return (b.combined_score ?? 0) - (a.combined_score ?? 0)
  })

  const bySignal = SIGNAL_ORDER.reduce((acc, sig) => {
    const items = sorted.filter(s => s.rotation_signal === sig)
    if (items.length) acc[sig] = items
    return acc
  }, {} as Record<string, typeof sorted>)

  return (
    <div className="space-y-8">
      {backBtn(navigate)}
      <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
        SECTOR INTELLIGENCE <span className="text-sm font-normal ml-2" style={{ color: '#64748B' }}>{data?.count} sectors</span>
      </h1>

      {Object.entries(bySignal).map(([signal, sectors]) => (
        <section key={signal}>
          <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>{signal} ({sectors.length})</h2>
          <div className="grid grid-cols-4 gap-3">
            {sectors.map(s => (
              <Link key={s.sector} to={`/sectors/${s.sector}`}>
                <SectorTile sector={s} />
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
