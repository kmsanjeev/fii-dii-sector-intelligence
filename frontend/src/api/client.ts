import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

export type MarketRegime = {
  regime: string
  smart_money_score: number
  fii_conviction_pct: number
  flow_scores: { FII: number; DII: number; PRO: number; CLIENT: number }
  data_date: string
}

export type Sector = {
  sector: string
  rotation_signal: string
  combined_score: number
  FII_flow_score: number
  DII_flow_score: number
  Smart_Money_Score: number
  last_date: string
}

export type Stock = {
  symbol: string
  sector: string
  bull_run_score: number
  label: string
  market_regime: string
  regime_multiplier: number
  components: {
    price_score: number
    sector_flow_score: number
    deal_score: number
    corporate_score: number
  }
  price: { ret_30d: number | null; ret_90d: number | null; ret_365d: number | null; vol_ratio: number | null }
  as_of_date: string
  deal_signals?: Record<string, unknown>
  corporate_confidence?: Record<string, unknown>
  fundamentals?: Record<string, number | string | null>
  shareholding?: Record<string, number | string | null>
}

export type ParticipantLatest = {
  date: string
  Market_Regime: string
  Smart_Money_Score: number
  Retail_Score: number
  FII_conviction: number
  DII_conviction: number
  FII_DII_Divergence: number
  Smart_Retail_Divergence: number
  Market_Opportunity: number
  Ensemble_Score: number
}

// API helpers
export const fetchRegime = () => api.get<MarketRegime>('/market/regime').then(r => r.data)
export const fetchSectors = () => api.get<{ sectors: Sector[]; count: number }>('/sectors').then(r => r.data)
export const fetchWatchlist = (label = 'EMERGING', limit = 50) =>
  api.get<{ stocks: Stock[]; count: number; label: string }>(`/stocks/watchlist?label=${label}&limit=${limit}`).then(r => r.data)
export const fetchStockDetail = (symbol: string) => api.get<Stock>(`/stocks/${symbol}`).then(r => r.data)
export const fetchParticipantLatest = () => api.get<ParticipantLatest>('/participant/latest').then(r => r.data)
export const fetchParticipantHistory = (limit = 252) =>
  api.get<{ rows: Record<string, number | string>[]; count: number }>(`/participant/history?limit=${limit}`).then(r => r.data)
export const fetchSectorDetail = (sector: string) =>
  api.get<Sector & { top_stocks: Stock[] }>(`/sectors/${sector}`).then(r => r.data)
export const fetchDeals = (min_cr = 50, limit = 50) =>
  api.get<{ deals: Record<string, unknown>[]; count: number }>(`/corporate/deals?min_cr=${min_cr}&limit=${limit}`).then(r => r.data)
export const fetchCatalysts = () =>
  api.get<{ catalysts: Record<string, unknown>[]; count: number }>('/corporate/catalysts').then(r => r.data)
export const fetchAllStocks = (page = 1, per_page = 100, label?: string) => {
  const params = new URLSearchParams({ page: String(page), per_page: String(per_page) })
  if (label && label !== 'ALL') params.set('label', label)
  return api.get<{ stocks: Stock[]; total: number; page: number }>(`/stocks?${params}`).then(r => r.data)
}
export const fetchHealth = () => api.get('/health').then(r => r.data)
export const fetchDataStatus = () => api.get('/data/status').then(r => r.data)
export const fetchEngineList = () => api.get('/data/engines').then(r => r.data)
