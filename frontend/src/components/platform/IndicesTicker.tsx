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
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '0 20px', borderRight: '1px solid #1A2540' }}>
      <span style={{ color: '#B0C4D8', fontSize: 11, fontWeight: 600, letterSpacing: 0.3 }}>
        {SHORT[t.name] ?? t.name}
      </span>
      <span style={{ fontSize: 11, fontWeight: 700, color: pos ? '#22D35E' : '#F44B4B' }}>
        {pos ? '+' : ''}{chg.toFixed(2)}%
      </span>
      <span style={{ fontSize: 9, color: '#4E6074', fontWeight: 500 }}>30D</span>
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
      background: '#08101E',
      borderBottom: '1px solid #1A2540',
      height: 30,
      display: 'flex',
      alignItems: 'center',
    }}>
      <div style={{
        color: '#22D35E', fontSize: 10, fontWeight: 800, letterSpacing: 2.5,
        padding: '0 14px', flexShrink: 0, borderRight: '1px solid #1A2540',
        height: '100%', display: 'flex', alignItems: 'center', background: '#0D1A2E',
      }}>
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
