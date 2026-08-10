import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import App from '../App'

vi.mock('../components/ui/AppShell', () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div data-testid="app-shell">{children}</div>,
}))

vi.mock('../pages/Dashboard', () => ({ Dashboard: () => <div>Dashboard Page</div> }))
vi.mock('../pages/SectorsPage', () => ({ SectorsPage: () => <div>Sectors Page</div> }))
vi.mock('../pages/SectorDetailPage', () => ({ SectorDetailPage: () => <div>Sector Detail Page</div> }))
vi.mock('../pages/WatchlistPage', () => ({ WatchlistPage: () => <div>Watchlist Page</div> }))
vi.mock('../pages/CorporatePage', () => ({ CorporatePage: () => <div>Corporate Page</div> }))
vi.mock('../pages/ChatPage', () => ({ ChatPage: () => <div>Chat Page</div> }))
vi.mock('../pages/SettingsPage', () => ({ SettingsPage: () => <div>Settings Page</div> }))
vi.mock('../pages/DataControlPage', () => ({ DataControlPage: () => <div>Data Control Page</div> }))
vi.mock('../pages/StocksPage', () => ({ StocksPage: () => <div>Stocks Page</div> }))
vi.mock('../pages/PortfolioPage', () => ({ PortfolioPage: () => <div>Portfolio Page</div> }))
vi.mock('../pages/BacktestPage', () => ({ BacktestPage: () => <div>Backtest Page</div> }))
vi.mock('../pages/BrokerPage', () => ({ BrokerPage: () => <div>Broker Page</div> }))
vi.mock('../pages/ResearchPage', () => ({ ResearchPage: () => <div>Research Page</div> }))
vi.mock('../pages/ExecutionPage', () => ({ ExecutionPage: () => <div>Execution Page</div> }))
vi.mock('../pages/LoginPage', () => ({ LoginPage: () => <div>Login Page</div> }))
vi.mock('../pages/AdminPage', () => ({ AdminPage: () => <div>Admin Page</div> }))
vi.mock('../pages/ThemesPage', () => ({ ThemesPage: () => <div>Themes Page</div> }))
vi.mock('../pages/ReportPage', () => ({ ReportPage: () => <div>Report Page</div> }))
vi.mock('../pages/FullChartPage', () => ({ FullChartPage: () => <div>Full Chart Page</div> }))

function renderRoute(path: string) {
  window.history.pushState({}, '', path)
  return render(<App />)
}

describe('App router baseline', () => {
  afterEach(() => {
    window.history.pushState({}, '', '/')
  })

  it('routes /chat through the shell', () => {
    renderRoute('/chat')

    expect(screen.getByTestId('app-shell')).toBeInTheDocument()
    expect(screen.getByText('Chat Page')).toBeInTheDocument()
  })

  it('routes /settings through the shell', () => {
    renderRoute('/settings')

    expect(screen.getByTestId('app-shell')).toBeInTheDocument()
    expect(screen.getByText('Settings Page')).toBeInTheDocument()
  })

  it('routes /report/RELIANCE through the shell', () => {
    renderRoute('/report/RELIANCE')

    expect(screen.getByTestId('app-shell')).toBeInTheDocument()
    expect(screen.getByText('Report Page')).toBeInTheDocument()
  })

  it('routes /fullchart/RELIANCE outside the shell', () => {
    renderRoute('/fullchart/RELIANCE')

    expect(screen.queryByTestId('app-shell')).not.toBeInTheDocument()
    expect(screen.getByText('Full Chart Page')).toBeInTheDocument()
  })

  it('keeps /participant redirected to the dashboard', () => {
    renderRoute('/participant')

    expect(screen.getByTestId('app-shell')).toBeInTheDocument()
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
  })
})
