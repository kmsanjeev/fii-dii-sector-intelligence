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
    bull_run:     number
    emerging:     number
    watchlist:    number
    neutral:      number
    accumulation: number
    markdown:     number
  }
}

export type Sector = {
  sector:            string
  rotation_signal:   string
  combined_score:    number | null   // z-score vs 252D baseline, ±100 scale
  relative_score:    number | null   // cross-sectional rank, ±100 (best sector = +100)
  FII_flow_score:    number | null
  DII_flow_score:    number | null
  Smart_Money_Score: number | null
  fpi_score?:        number | null
  fpi_signal?:       string
  auc_pct_of_total?: number | null
  auc_z?:            number | null
  net_z?:            number | null
  price_momentum_score?: number | null
  nse_index?:        string
  last_date:         string
  fpi_date?:         string
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
  // RSI
  rsi:           number | null
  rsi_signal:    string
  // MACD
  macd_line:     number | null
  macd_signal:   number | null
  macd_hist:     number | null
  macd_cross:    string
  // ATR
  atr_14:        number | null
  atr_pct:       number | null
  // Bollinger Bands
  bb_upper:      number | null
  bb_lower:      number | null
  bb_mid:        number | null
  bb_pct:        number | null
  bb_width:      number | null
  bb_signal:     string
  bb_squeeze:    boolean
  // OBV
  obv_signal:    string
  // ADX
  adx:           number | null
  adx_plus_di:   number | null
  adx_minus_di:  number | null
  adx_strength:  string
  adx_direction: string
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
  driving_participant?: string
  ath_proximity_score?: number
  sector_rotation_signal?: string
  components: {
    price_score: number
    ath_proximity_score?: number
    sector_flow_score: number
    deal_score: number
    corporate_score: number
  }
  price: {
    ret_30d: number | null; ret_90d: number | null; ret_365d: number | null; vol_ratio: number | null
    ret_7d?: number | null; ret_15d?: number | null
    change_1d_pct?: number | null; change_1d_abs?: number | null; prev_close?: number | null
  }
  as_of_date: string
  deal_signals?: Record<string, unknown>
  corporate_confidence?: Record<string, unknown>
  fundamentals?: Record<string, number | string | null>
  shareholding?: Record<string, number | string | null>
  holding_trends?: Record<string, number | string | null>[]
  management?: Record<string, number | string | null>
  ml_scores?: { accumulation_score: number | null; ml_bull_run_score: number | null; forward_return_score?: number | null; forward_return_prob?: number | null }
  technical?: TechnicalIndicators
  fno?: FnoData
  catalyst?: { event_date: string; purpose_type: string; catalyst_score: number | null }
  analyst_insights?: string[]
  quarterly_results?: Record<string, string | number | null>[]
  // Phase F alt-data
  news?:    Record<string, string | number | null>
  insider?: Record<string, string | number | null>
  concall?: Record<string, string | number | null>
  agm?:     Record<string, string | number | null>
  // Phase G consensus
  consensus?: Record<string, string | number | null>
  // Phase AF AstroFinance
  astro?: {
    sector: string; ruling_planets: string; primary_planet: string
    planet_sign: string; planet_state: string; planet_retrograde: boolean
    key_aspects: string; astro_score: number; astro_action: string
    astro_reason: string; moon_phase: string; eclipse_active: boolean
    as_of_date: string; market_astro_signal: string
    mercury_retrograde: boolean; venus_retrograde: boolean
    moon_illumination: number | null; jupiter_sign: string
    saturn_sign: string; reversal_note: string | null
  }
  // Phase D — four new intelligence cards
  structured_thesis?: {
    verdict: string; score: number
    bull_signals: string[]; bear_signals: string[]
    conflict_note: string; dominant_factor: string; confidence: string; ml_note: string
  }
  key_levels?: {
    close: number | null; atr_14: number | null
    conf_res_1: number | null; conf_res_1_score: number | null; conf_res_1_tags: string
    conf_res_2: number | null; conf_res_2_score: number | null; conf_res_2_tags: string
    conf_sup_1: number | null; conf_sup_1_score: number | null; conf_sup_1_tags: string
    conf_sup_2: number | null; conf_sup_2_score: number | null; conf_sup_2_tags: string
    entry_zone_low: number | null; entry_zone_high: number | null
    stop_loss: number | null; target_1atr: number | null; target_2atr: number | null
    as_of_date: string
  }
  sector_peer_valuation?: {
    sector_pe?: number; sector_roe?: number; sector_roce?: number
    peer_count?: number; sector?: string
  }
  upcoming_events?: Array<{ event_date: string; purpose_type: string; bm_desc: string }>
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
export const fetchStockAnnouncements = (symbol: string, limit = 20) =>
  api.get<{ symbol: string; announcements: Announcement[]; total: number }>(
    `/stocks/${symbol}/announcements?limit=${limit}`
  ).then(r => r.data)

export const fetchAnnouncementSummary = (pdf_url: string, seq_id: string, title: string) =>
  api.get<{ summary: string; cached: boolean }>(
    `/stocks/announcement-summary?pdf_url=${encodeURIComponent(pdf_url)}&seq_id=${encodeURIComponent(seq_id)}&title=${encodeURIComponent(title)}`
  ).then(r => r.data)

export const fetchNewsArticleSummary = (url: string, article_id: string, headline: string, themes = '') =>
  api.get<{ summary: string; cached: boolean }>(
    `/stocks/news-article-summary?url=${encodeURIComponent(url)}&article_id=${encodeURIComponent(article_id)}&headline=${encodeURIComponent(headline)}&themes=${encodeURIComponent(themes)}`
  ).then(r => r.data)

export interface NewsArticle {
  headline:   string
  source:     string
  date:       string
  sentiment:  string
  link:       string
  article_id: string
  themes:     string
}

export interface Announcement {
  date:              string
  announcement_type: string
  signal_score:      number | null
  title:             string
  desc:              string
  seq_id:            string
  pdf_url:           string | null
}

export interface CorpAction {
  ex_date:      string
  rec_date:     string | null
  action_type:  'DIVIDEND' | 'BONUS' | 'SPLIT' | 'BUYBACK' | 'RIGHTS' | string
  dividend_rs:  number | null
  bonus_ratio:  number | null
  split_new_fv: number | null
  subject:      string
}

export interface CorpActionsResponse {
  symbol:  string
  years:   number
  count:   number
  actions: CorpAction[]
  summary: Record<string, number | null>
}

export const fetchStockCorpActions = (symbol: string, years = 5) =>
  api.get<CorpActionsResponse>(`/stocks/${symbol}/corporate-actions?years=${years}`).then(r => r.data)
export const fetchParticipantLatest  = () => api.get<ParticipantLatest>('/participant/latest').then(r => r.data)
export const fetchParticipantHistory = (limit = 252) =>
  api.get<{ rows: Record<string, number | string>[]; count: number }>(`/participant/history?limit=${limit}`).then(r => r.data)
export const fetchSectorDetail  = (sector: string) =>
  api.get<Sector & { top_stocks: Stock[] }>(`/sectors/${sector}`).then(r => r.data)
export const fetchDeals         = (min_cr = 25, limit = 50) =>
  api.get<{ deals: Record<string, unknown>[]; count: number }>(`/corporate/deals?min_cr=${min_cr}&limit=${limit}`).then(r => r.data)
export const fetchCatalysts     = () =>
  api.get<{ catalysts: Record<string, unknown>[]; count: number }>('/corporate/catalysts').then(r => r.data)
// Phase UI-C — Corporate Intelligence Hub
export const fetchDealTape      = (min_cr = 0, limit = 40, participant?: string) =>
  api.get<{ deals: Record<string, unknown>[]; count: number }>(
    `/corporate/deal-tape?min_cr=${min_cr}&limit=${limit}${participant ? `&participant=${participant}` : ''}`).then(r => r.data)
export const fetchUpcomingActions = (days = 45, limit = 60) =>
  api.get<{ actions: Record<string, unknown>[]; count: number }>(`/corporate/upcoming-actions?days=${days}&limit=${limit}`).then(r => r.data)
export const fetchCorporateSummary = () =>
  api.get<Record<string, number>>('/corporate/summary').then(r => r.data)
export const fetchAnnouncements = (days = 7, min_score = 0, ann_type?: string, limit = 100) =>
  api.get<{ announcements: Record<string, unknown>[]; count: number }>(
    `/corporate/announcements?days=${days}&min_score=${min_score}&limit=${limit}${ann_type ? `&ann_type=${ann_type}` : ''}`).then(r => r.data)
export const fetchConfidence    = (limit = 20) =>
  api.get<{ confidence_scores: Record<string, unknown>[]; count: number }>(`/corporate/confidence?limit=${limit}`).then(r => r.data)
export const fetchAllStocks     = (page = 1, per_page = 100, label?: string, sector?: string, search?: string) => {
  const params = new URLSearchParams({ page: String(page), per_page: String(per_page) })
  if (label && label !== 'ALL') params.set('label', label)
  if (sector && sector !== 'ALL') params.set('sector', sector)
  return api.get<{ stocks: Stock[]; total: number; page: number }>(`/stocks?${params}`).then(r => r.data)
}
export type IndexTick = { name: string; ret_30d: number; ret_365d: number; momentum_score: number }
export const fetchIndicesTicker = () =>
  api.get<{ indices: IndexTick[]; count: number }>('/market/indices').then(r => r.data)

export const fetchHealth        = () => api.get('/health').then(r => r.data)
export const fetchDataStatus    = () => api.get('/data/status').then(r => r.data)
export const fetchEngineList    = () => api.get('/data/engines').then(r => r.data)

// Social Pulse -- X (Twitter) intelligence ticker
export type SocialPulseItem = {
  title:         string
  url:           string
  published_ts:  number
  published_rel: string
  sentiment:     'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  impact_score:  number
}
export type SocialPulseHandle = {
  handle:       string
  display_name: string
  avatar:       string   // 2-4 char abbreviation
  category:     string
  region:       'INDIA' | 'GLOBAL'
  item_count:   number
  items:        SocialPulseItem[]
  is_x:         boolean
}
export type SocialPulseResponse = {
  handles:   SocialPulseHandle[]
  active:    number
  total:     number
  cached_at: number
}
export const fetchSocialPulse = () =>
  api.get<SocialPulseResponse>('/social-pulse').then(r => r.data)

// Phase News — RSS aggregator
export type NewsItem = {
  title:        string
  url:          string
  source:       string
  published:    string   // ISO 8601
  published_ts: number   // unix timestamp
  summary:      string
  sentiment:    'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  region:       'INDIA' | 'GLOBAL' | 'US' | 'ASIA'
  category:     string   // EQUITIES | MACRO | COMMODITIES | FOREX | FLOWS | EARNINGS | IPO | OTHER
}
export type NewsResponse = { items: NewsItem[]; cached_at: number; count: number }
export const fetchNews = () => api.get<NewsResponse>('/news').then(r => r.data)

// Phase 14 — AI Chat (separate instance with longer timeout for multi-round Groq tool calls)
const chatApi = axios.create({ baseURL: '/api', timeout: 60000 })
export type ChatAttachmentStub = {
  name: string
  mime_type: string
  size_bytes?: number | null
  storage_key?: string | null
  excerpt?: string | null
}
export type ChatResearchSource = {
  title: string
  url: string
  snippet?: string | null
  source?: string | null
  published_at?: string | null
  kind?: string
}
export type ChatResearchMeta = {
  requested: boolean
  used: boolean
  provider?: string | null
  reason?: string | null
  source_count: number
  cached?: boolean
  error?: string | null
  sources: ChatResearchSource[]
}
export type ChatCapabilities = {
  research_enabled: boolean
  default_research_provider: string
  auto_research_for_research_intent: boolean
  attachments_enabled: boolean
  save_to_knowledge_enabled: boolean
  mcp_enabled: boolean
  supported_attachment_mime_prefixes: string[]
}
export type ChatResponseData = {
  reply: string
  session_id: string
  intent: string
  symbols_discussed?: string[]
  flagged?: boolean
  flag_reason?: string | null
  research?: ChatResearchMeta
}
export const sendChat = (
  message: string,
  session_id?: string,
  mode: 'voice' | 'text' = 'text',
  extras?: { research_mode?: boolean; attachments?: ChatAttachmentStub[] },
) =>
  chatApi.post<ChatResponseData>('/chat', {
    message,
    session_id,
    mode,
    research_mode: extras?.research_mode ?? false,
    attachments: extras?.attachments ?? [],
  }).then(r => r.data)
export const resetChatSession = (session_id: string) =>
  chatApi.delete(`/chat/session/${session_id}`).then(r => r.data)
export const fetchChatCapabilities = () =>
  chatApi.get<ChatCapabilities>('/chat/capabilities').then(r => r.data)

// Phase V-DATA-3 — chat demand analytics ("Recently Asked" panel)
export type ChatAnalyticsRow = { key: string; count: number; share_pct?: number; last_seen?: string | null }
export type ChatAnalytics = {
  source: string
  summary?: Record<string, number>
  top_symbols?: ChatAnalyticsRow[]
}
export const fetchVoiceAnalytics = () =>
  api.get<ChatAnalytics>('/voice/analytics').then(r => r.data)
