import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppShell } from './components/ui/AppShell'
import { Dashboard } from './pages/Dashboard'
import { SectorsPage } from './pages/SectorsPage'
import { SectorDetailPage } from './pages/SectorDetailPage'
import { WatchlistPage } from './pages/WatchlistPage'
import { StockDetailPage } from './pages/StockDetailPage'
import { ParticipantPage } from './pages/ParticipantPage'
import { CorporatePage } from './pages/CorporatePage'
import { ChatPage } from './pages/ChatPage'
import { SettingsPage } from './pages/SettingsPage'
import { DataControlPage } from './pages/DataControlPage'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 4 * 60 * 1000,   // 4 min
      retry: 2,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sectors" element={<SectorsPage />} />
            <Route path="/sectors/:sector" element={<SectorDetailPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/stocks/:symbol" element={<StockDetailPage />} />
            <Route path="/participant" element={<ParticipantPage />} />
            <Route path="/corporate" element={<CorporatePage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/data" element={<DataControlPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
