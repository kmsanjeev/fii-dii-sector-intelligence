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

export type MarketContext = MarketRegime & {
  pcr:        number | null
  pcr_signal: string
  pcr_date:   string
  cash_flows: {
    fpi_5d_cr:       number
    mf_5d_cr:        number
    insurance_5d_cr: number
    fpi_20d_cr:      number
    mf_20d_cr:       number
  }
  breadth: {
    strong_candidate: number
    emerging:         number
    watchlist:        number
    neutral:          number
    avoid:            number
  }
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

export type TechnicalIndicators = {
  close_now:     number | null
  high_52w:      number | null
  low_52w:       number | null
  prox_52w_high: number | null
  prox_52w_low:  number | null
  dma_20:        number | null
  dma_50:        number | null
  dma_200:       number | null
  vs_dma_20:     number | null
  vs_dma_50:     number | null
  vs_dma_200:    number | null
  trend_signal:  string
  vol_20d_avg:   number | null
  as_of_date:    string
}

export type FnoData = {
  futures_oi: number | null
  oi_1d:      number | null
  oi_5d:      number | null
  oi_signal:  string
  fut_close:  number | null
  expiry:     string
  as_of_date: string
}

export type Stock = {
  symbol: string
  sector: string
  close_now: number | null
  bull_run_score: number
  label: string
  market_regime: string
  regime_multiplier: number
  sector_rotation_signal?: string
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
  holding_trends?: Record<string, number | string | null>[]
  management?: Record<string, number | string | null>
  ml_scores?: { accumulation_score: number | null; ml_bull_run_score: number | null }
  technical?: TechnicalIndicators
  fno?: FnoData
  catalyst?: { event_date: string; purpose_type: string; catalyst_score: number | null }
  // fields available in bulk listing (merged from technical/fno/ml datasets)
  trend_signal?: string
  vs_dma_200?: number | null
  prox_52w_high?: number | null
  oi_signal?: string
  ml_bull_run_score?: number | null
  accumulation_score?: number | null
}

export type ParticipantLatest = {
  date: string
  Market_Regime: string
  FII_flow_score:         number
  DII_flow_score:         number
  PRO_flow_score:         number
  CLIENT_flow_score:      number
  FPI_flow_score:         number
  MF_flow_score:          number
  INSURANCE_flow_score:   number
  RETAIL_flow_score:      number
  Smart_Money_Score:      number
  Retail_Score:           number
  Cash_Institutional_Score: number
  FII_conviction:         number
  DII_conviction:         number
  FII_DII_Divergence:     number
  Smart_Retail_Divergence: number
  Market_Opportunity:     number
  Ensemble_Score:         number
  cash_flows: {
    fpi_5d_cr:       number
    mf_5d_cr:        number
    insurance_5d_cr: number
    fpi_20d_cr:      number
    mf_20d_cr:       number
  }
}

// API helpers
export const fetchRegime        = () => api.get<MarketRegime>('/market/regime').then(r => r.data)
export const fetchMarketContext = () => api.get<MarketContext>('/market/context').then(r => r.data)
export const fetchSectors       = () => api.get<{ sectors: Sector[]; count: number }>('/sectors').then(r => r.data)
export const fetchWatchlist     = (label = 'EMERGING', limit = 50) =>
  api.get<{ stocks: Stock[]; count: number; label: string }>(`/stocks/watchlist?label=${label}&limit=${limit}`).then(r => r.data)
export const fetchStockDetail   = (symbol: string) => api.get<Stock>(`/stocks/${symbol}`).then(r => r.data)
export const fetchParticipantLatest  = () => api.get<ParticipantLatest>('/participant/latest').then(r => r.data)
export const fetchParticipantHistory = (limit = 252) =>
  api.get<{ rows: Record<string, number | string>[]; count: number }>(`/participant/history?limit=${limit}`).then(r => r.data)
export const fetchSectorDetail  = (sector: string) =>
  api.get<Sector & { top_stocks: Stock[] }>(`/sectors/${sector}`).then(r => r.data)
export const fetchDeals         = (min_cr = 25, limit = 50) =>
  api.get<{ deals: Record<string, unknown>[]; count: number }>(`/corporate/deals?min_cr=${min_cr}&limit=${limit}`).then(r => r.data)
export const fetchCatalysts     = () =>
  api.get<{ catalysts: Record<string, unknown>[]; count: number }>('/corporate/catalysts').then(r => r.data)
export const fetchAllStocks     = (page = 1, per_page = 100, label?: string, sector?: string, search?: string) => {
  const params = new URLSearchParams({ page: String(page), per_page: String(per_page) })
  if (label && label !== 'ALL') params.set('label', label)
  if (sector && sector !== 'ALL') params.set('sector', sector)
  return api.get<{ stocks: Stock[]; total: number; page: number }>(`/stocks?${params}`).then(r => r.data)
}
export const fetchHealth        = () => api.get('/health').then(r => r.data)
export const fetchDataStatus    = () => api.get('/data/status').then(r => r.data)
export const fetchEngineList    = () => api.get('/data/engines').then(r => r.data)
