import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchRegime, type MarketRegime } from '../../api/client'
import { RegimeBanner } from '../platform/RegimeBanner'
import { usePlatformStore } from '../../store/platformStore'

const NAV = [
  { path: '/',           label: 'Dashboard' },
  { path: '/sectors',    label: 'Sectors' },
  { path: '/watchlist',  label: 'Watchlist' },
  { path: '/participant',label: 'Participant' },
  { path: '/corporate',  label: 'Corporate' },
  { path: '/charts',     label: 'Charts' },
  { path: '/portfolio',  label: 'Portfolio' },
  { path: '/backtest',   label: 'Backtest' },
  { path: '/broker',     label: 'Broker' },
  { path: '/research',   label: 'Research' },
  { path: '/chat',       label: 'AI Chat' },
  { path: '/data',       label: 'Data Control' },
  { path: '/settings',   label: 'Settings' },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const setRegime = usePlatformStore(s => s.setRegime)

  const { data: regime } = useQuery<MarketRegime>({
    queryKey: ['regime'],
    queryFn: fetchRegime,
    refetchInterval: 5 * 60 * 1000,
  })

  useEffect(() => {
    if (regime) setRegime(regime)
  }, [regime, setRegime])

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0A0D14' }}>
      {regime && (
        <RegimeBanner
          regime={regime.regime}
          smartMoney={regime.smart_money_score}
          fiiConviction={regime.fii_conviction_pct}
        />
      )}
      <header className="px-6 py-3 border-b flex items-center gap-8" style={{ borderColor: '#1E2332', backgroundColor: '#141720' }}>
        <span className="font-bold text-sm tracking-widest" style={{ color: '#22C55E' }}>CAPITAL FLOW</span>
        <nav className="flex gap-4">
          {NAV.map(n => (
            <Link
              key={n.path}
              to={n.path}
              className="text-xs tracking-wide transition-colors"
              style={{ color: location.pathname === n.path ? '#22C55E' : '#64748B' }}
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
