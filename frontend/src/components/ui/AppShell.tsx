import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchRegime, type MarketRegime } from '../../api/client'
import { RegimeBanner } from '../platform/RegimeBanner'
import { IndicesTicker } from '../platform/IndicesTicker'
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
  { path: '/execution',  label: 'Execution' },
  { path: '/chat',       label: 'AI Chat' },
  { path: '/data',       label: 'Data Control' },
  { path: '/settings',   label: 'Settings' },
]

function useAuthUser() {
  const [user, setUser] = useState<{ email: string; role: string } | null>(() => {
    try { return JSON.parse(localStorage.getItem('cfip_user') || 'null') }
    catch { return null }
  })

  // Sync across tabs / after login
  useEffect(() => {
    const sync = () => {
      try { setUser(JSON.parse(localStorage.getItem('cfip_user') || 'null')) }
      catch { setUser(null) }
    }
    window.addEventListener('storage', sync)
    return () => window.removeEventListener('storage', sync)
  }, [])

  return user
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const location  = useLocation()
  const navigate  = useNavigate()
  const setRegime = usePlatformStore(s => s.setRegime)
  const authUser  = useAuthUser()

  const { data: regime } = useQuery<MarketRegime>({
    queryKey: ['regime'],
    queryFn: fetchRegime,
    refetchInterval: 5 * 60 * 1000,
  })

  useEffect(() => {
    if (regime) setRegime(regime)
  }, [regime, setRegime])

  const logout = async () => {
    await fetch('http://localhost:8001/api/auth/logout', { method: 'POST' })
    localStorage.removeItem('cfip_token')
    localStorage.removeItem('cfip_user')
    navigate('/login')
  }

  const roleBg: Record<string, string> = {
    admin:   '#3B2000', trader: '#1E3A5F', analyst: '#14532D',
  }
  const roleFg: Record<string, string> = {
    admin:   '#FBBF24', trader: '#60A5FA', analyst: '#4ADE80',
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0A0D14' }}>
      {regime && (
        <RegimeBanner
          regime={regime.regime}
          smartMoney={regime.smart_money_score}
          fiiConviction={regime.fii_conviction_pct}
        />
      )}
      <IndicesTicker />
      <header className="px-6 py-3 border-b flex items-center gap-6" style={{ borderColor: '#1E2332', backgroundColor: '#141720' }}>
        <span className="font-bold text-sm tracking-widest" style={{ color: '#22C55E', whiteSpace: 'nowrap' }}>CAPITAL FLOW</span>
        <nav className="flex gap-3 flex-wrap flex-1">
          {NAV.map(n => (
            <Link
              key={n.path}
              to={n.path}
              className="text-xs tracking-wide transition-colors"
              style={{ color: location.pathname === n.path ? '#22C55E' : '#64748B', whiteSpace: 'nowrap' }}
            >
              {n.label}
            </Link>
          ))}
          {authUser?.role === 'admin' && (
            <Link
              to="/admin"
              className="text-xs tracking-wide transition-colors"
              style={{ color: location.pathname === '/admin' ? '#FBBF24' : '#64748B', whiteSpace: 'nowrap' }}
            >
              Admin
            </Link>
          )}
        </nav>

        {/* User badge */}
        {authUser && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <span style={{
              fontSize: 10, padding: '2px 6px', borderRadius: 4, fontWeight: 700,
              background: roleBg[authUser.role] ?? '#1E2332',
              color:      roleFg[authUser.role] ?? '#94A3B8',
            }}>
              {authUser.role.toUpperCase()}
            </span>
            <span style={{ fontSize: 12, color: '#94A3B8', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {authUser.email}
            </span>
            <button
              onClick={logout}
              style={{
                padding: '3px 10px', borderRadius: 4, border: '1px solid #2D3348',
                background: 'transparent', color: '#64748B', cursor: 'pointer', fontSize: 11,
              }}
            >
              Sign out
            </button>
          </div>
        )}
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
