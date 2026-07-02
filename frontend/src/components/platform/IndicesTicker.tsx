import { useQuery } from '@tanstack/react-query'
import { fetchIndicesTicker, type IndexTick } from '../../api/client'

// Short display names for the ticker
const SHORT: Record<string, string> = {
  'NIFTY 50':          'NIFTY 50',
  'NIFTY BANK':        'NIFTYBANK',
  'NIFTY IT':          'NIFTY IT',
  'NIFTY PHARMA':      'NIFTYPHA',
  'NIFTY AUTO':        'NIFTYAUTO',
  'NIFTY FMCG':        'NIFTYFMCG',
  'NIFTY REALTY':      'NIFTYRLT',
  'NIFTY METAL':       'NIFTYMETAL',
  'NIFTY MIDCAP 150':  'MIDCAP150',
  'NIFTY SMALLCAP 100':'SMLCAP100',
  'NIFTY NEXT 50':     'NEXT50',
  'NIFTY INFRASTRUCTURE': 'NIFTYINFRA',
  'NIFTY MIDCAP 50':   'MIDCAP50',
}

function TickItem({ t }: { t: IndexTick }) {
  const chg = t.ret_30d
  const pos = chg >= 0
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '0 18px', borderRight: '1px solid #1E2332' }}>
      <span style={{ color: '#64748B', fontSize: 10, fontWeight: 600, letterSpacing: 0.5 }}>
        {SHORT[t.name] ?? t.name}
      </span>
      <span style={{
        fontSize: 11, fontWeight: 700,
        color: pos ? '#22C55E' : '#EF4444',
      }}>
        {pos ? '+' : ''}{chg.toFixed(2)}%
      </span>
      <span style={{ fontSize: 8, color: '#334155' }}>30D</span>
    </span>
  )
}

export function IndicesTicker() {
  const { data } = useQuery({
    queryKey: ['indices-ticker'],
    queryFn: fetchIndicesTicker,
    refetchInterval: 5 * 60_000,
    staleTime: 4 * 60_000,
  })

  const items: IndexTick[] = data?.indices ?? []
  if (items.length === 0) return null

  // Duplicate for seamless loop
  const doubled = [...items, ...items]

  return (
    <div style={{
      overflow: 'hidden',
      background: '#0D1017',
      borderBottom: '1px solid #1E2332',
      height: 28,
      display: 'flex',
      alignItems: 'center',
    }}>
      <div
        style={{ color: '#22C55E', fontSize: 9, fontWeight: 800, letterSpacing: 2, padding: '0 12px', flexShrink: 0, borderRight: '1px solid #1E2332', height: '100%', display: 'flex', alignItems: 'center' }}
      >
        NSE
      </div>
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <div className="ticker-inner">
          {doubled.map((t, i) => (
            <TickItem key={`${t.name}-${i}`} t={t} />
          ))}
        </div>
      </div>
    </div>
  )
}
