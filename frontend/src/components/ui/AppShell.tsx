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
  { path: '/themes',     label: 'Themes' },
  { path: '/stocks',     label: 'Stocks' },
  { path: '/watchlist',  label: 'Watchlist' },
  { path: '/participant',label: 'Participant' },
  { path: '/corporate',  label: 'Corporate' },
  { path: '/portfolio',  label: 'Portfolio' },
  { path: '/backtest',   label: 'Backtest' },
  { path: '/broker',     label: 'Broker' },
  { path: '/research',   label: 'Research' },
  { path: '/execution',  label: 'Execution' },
  { path: '/chat',       label: 'ChatBot' },
  { path: '/data',       label: 'Data' },
  { path: '/settings',   label: 'Settings' },
]

function useAuthUser() {
  const [user, setUser] = useState<{ email: string; role: string } | null>(() => {
    try { return JSON.parse(localStorage.getItem('cfip_user') || 'null') }
    catch { return null }
  })
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

function useMobile(breakpoint = 900) {
  const [mobile, setMobile] = useState(() =>
    typeof window !== 'undefined' && window.innerWidth < breakpoint
  )
  useEffect(() => {
    const check = () => setMobile(window.innerWidth < breakpoint)
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [breakpoint])
  return mobile
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const location   = useLocation()
  const navigate   = useNavigate()
  const setRegime  = usePlatformStore(s => s.setRegime)
  const authUser   = useAuthUser()
  const isMobile   = useMobile()
  const [menuOpen, setMenuOpen] = useState(false)

  const { data: regime } = useQuery<MarketRegime>({
    queryKey: ['regime'],
    queryFn: fetchRegime,
    refetchInterval: 5 * 60 * 1000,
  })

  useEffect(() => { if (regime) setRegime(regime) }, [regime, setRegime])

  // Close drawer on route change
  useEffect(() => setMenuOpen(false), [location.pathname])

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    localStorage.removeItem('cfip_token')
    localStorage.removeItem('cfip_user')
    navigate('/login')
  }

  const roleBg: Record<string, string> = {
    admin: '#3B2000', trader: '#1E3A5F', analyst: '#14532D',
  }
  const roleFg: Record<string, string> = {
    admin: '#FBBF24', trader: '#60A5FA', analyst: '#4ADE80',
  }

  const canGoBack = typeof window !== 'undefined' && (window.history.state?.idx ?? 0) > 0

  const stockSymbolMatch   = location.pathname.match(/^\/stocks\/([A-Z0-9&.-]+)$/i)
  const currentStockSymbol = stockSymbolMatch?.[1]?.toUpperCase() ?? null

  const isActive = (path: string) =>
    location.pathname === path ||
    (path === '/stocks' && (location.pathname === '/charts' || location.pathname.startsWith('/stocks/')))

  return (
    <div className="flex flex-col" style={{ height: '100dvh', overflow: 'hidden', backgroundColor: '#0A0D14' }}>
      {regime && (
        <RegimeBanner
          regime={regime.regime}
          smartMoney={regime.smart_money_score}
          fiiConviction={regime.fii_conviction_pct}
        />
      )}
      <IndicesTicker />

      {/* ── Header ─────────────────────────────────────────────────────────────── */}
      <header
        className="px-4 py-2 border-b flex items-center gap-3"
        style={{ borderColor: '#1E2332', backgroundColor: '#141720', flexShrink: 0, minHeight: 44 }}
      >
        <span className="font-bold text-sm tracking-widest" style={{ color: '#22C55E', whiteSpace: 'nowrap', flexShrink: 0 }}>
          CAPITAL FLOW
        </span>

        {/* Desktop nav */}
        {!isMobile && (
          <nav className="flex gap-3 flex-wrap flex-1">
            {NAV.map(n => (
              <Link
                key={n.path}
                to={n.path}
                className="text-xs tracking-wide transition-colors"
                style={{ color: isActive(n.path) ? '#22C55E' : '#64748B', whiteSpace: 'nowrap' }}
              >
                {n.label}
              </Link>
            ))}
            {authUser?.role === 'admin' && (
              <Link
                to="/admin"
                className="text-xs tracking-wide"
                style={{ color: location.pathname === '/admin' ? '#FBBF24' : '#64748B', whiteSpace: 'nowrap' }}
              >
                Admin
              </Link>
            )}
          </nav>
        )}

        {/* Flexible spacer on mobile */}
        {isMobile && <div style={{ flex: 1 }} />}

        {/* Desktop: user badge */}
        {!isMobile && authUser && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <span style={{
              fontSize: 10, padding: '2px 6px', borderRadius: 4, fontWeight: 700,
              background: roleBg[authUser.role] ?? '#1E2332',
              color:      roleFg[authUser.role] ?? '#94A3B8',
            }}>
              {authUser.role.toUpperCase()}
            </span>
            <span style={{ fontSize: 11, color: '#94A3B8', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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

        {/* Report button — visible only on stock detail page */}
        {currentStockSymbol && (
          <Link
            to={`/report/${currentStockSymbol}`}
            style={{
              flexShrink: 0, display: 'inline-flex', alignItems: 'center', gap: 5,
              background: '#0A1F0A', border: '1px solid #22C55E40',
              color: '#22C55E', textDecoration: 'none', cursor: 'pointer',
              padding: '4px 10px', borderRadius: 4, fontSize: 11, fontWeight: 600,
              letterSpacing: '0.5px',
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            Report / PDF
          </Link>
        )}

        {/* Desktop back button */}
        {!isMobile && canGoBack && (
          <button
            onClick={() => navigate(-1)}
            style={{
              flexShrink: 0, display: 'flex', alignItems: 'center', gap: 4,
              background: 'none', border: '1px solid #2D3348',
              color: '#64748B', cursor: 'pointer',
              padding: '4px 10px', borderRadius: 4, fontSize: 11,
            }}
          >
            &larr; Back
          </button>
        )}

        {/* Mobile hamburger */}
        {isMobile && (
          <button
            onClick={() => setMenuOpen(v => !v)}
            aria-label="Toggle menu"
            style={{
              flexShrink: 0, background: 'none', border: '1px solid #2D3348',
              color: '#94A3B8', cursor: 'pointer',
              width: 36, height: 36, borderRadius: 4,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 20, lineHeight: 1,
            }}
          >
            {menuOpen ? '×' : '☰'}
          </button>
        )}
      </header>

      {/* ── Mobile drawer ──────────────────────────────────────────────────────── */}
      {isMobile && (
        <>
          {menuOpen && (
            <div
              onClick={() => setMenuOpen(false)}
              style={{
                position: 'fixed', inset: 0, zIndex: 998,
                backgroundColor: 'rgba(0,0,0,0.72)',
              }}
            />
          )}
          <div style={{
            position: 'fixed', top: 0, right: 0,
            height: '100dvh', width: 260,
            backgroundColor: '#141720', borderLeft: '1px solid #1E2332',
            zIndex: 999,
            transform: menuOpen ? 'translateX(0)' : 'translateX(110%)',
            transition: 'transform 0.22s cubic-bezier(0.4,0,0.2,1)',
            overflowY: 'auto',
            display: 'flex', flexDirection: 'column',
          }}>
            {/* Drawer header */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '14px 16px', borderBottom: '1px solid #1E2332', flexShrink: 0,
            }}>
              <span style={{ color: '#22C55E', fontWeight: 700, fontSize: 13, letterSpacing: 2 }}>
                CAPITAL FLOW
              </span>
              <button
                onClick={() => setMenuOpen(false)}
                style={{
                  background: 'none', border: 'none', color: '#64748B',
                  fontSize: 24, cursor: 'pointer', lineHeight: 1, padding: 0,
                }}
              >
                &times;
              </button>
            </div>

            {/* Nav links */}
            <nav style={{ display: 'flex', flexDirection: 'column', flex: 1, paddingTop: 4 }}>
              {NAV.map(n => (
                <Link
                  key={n.path}
                  to={n.path}
                  style={{
                    padding: '13px 20px',
                    color: isActive(n.path) ? '#22C55E' : '#94A3B8',
                    textDecoration: 'none', fontSize: 14,
                    borderLeft: isActive(n.path) ? '3px solid #22C55E' : '3px solid transparent',
                    backgroundColor: isActive(n.path) ? '#22C55E0D' : 'transparent',
                  }}
                >
                  {n.label}
                </Link>
              ))}
              {authUser?.role === 'admin' && (
                <Link
                  to="/admin"
                  style={{
                    padding: '13px 20px', fontSize: 14, textDecoration: 'none',
                    color: location.pathname === '/admin' ? '#FBBF24' : '#94A3B8',
                    borderLeft: location.pathname === '/admin' ? '3px solid #FBBF24' : '3px solid transparent',
                  }}
                >
                  Admin
                </Link>
              )}
            </nav>

            {/* Bottom: back + user */}
            <div style={{ borderTop: '1px solid #1E2332', padding: '12px 16px', flexShrink: 0 }}>
              {canGoBack && (
                <button
                  onClick={() => { navigate(-1); setMenuOpen(false) }}
                  style={{
                    width: '100%', padding: '9px', borderRadius: 4, marginBottom: 8,
                    border: '1px solid #2D3348', background: 'transparent',
                    color: '#64748B', cursor: 'pointer', fontSize: 12, textAlign: 'left',
                  }}
                >
                  &larr; Back
                </button>
              )}
              {authUser && (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <span style={{
                      fontSize: 10, padding: '2px 6px', borderRadius: 4, fontWeight: 700,
                      background: roleBg[authUser.role] ?? '#1E2332',
                      color:      roleFg[authUser.role] ?? '#94A3B8',
                    }}>
                      {authUser.role.toUpperCase()}
                    </span>
                    <span style={{ fontSize: 11, color: '#94A3B8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {authUser.email}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    style={{
                      width: '100%', padding: '9px', borderRadius: 4,
                      border: '1px solid #2D3348', background: 'transparent',
                      color: '#64748B', cursor: 'pointer', fontSize: 12,
                    }}
                  >
                    Sign out
                  </button>
                </>
              )}
            </div>
          </div>
        </>
      )}

      {/* ── Main content ───────────────────────────────────────────────────────── */}
      <main
        className="p-4"
        style={{ flex: 1, minHeight: 0, overflowY: 'auto', overflowX: 'hidden' }}
      >
        {children}
      </main>
    </div>
  )
}
