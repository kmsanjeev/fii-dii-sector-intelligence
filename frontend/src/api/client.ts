import axios, { AxiosHeaders } from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

const VEDA_CLIENT_ID_KEY = 'cfip-veda-client-id'

function loadToken(): string | null {
  try {
    return localStorage.getItem('cfip_token')
  } catch {
    return null
  }
}

function createClientId(): string {
  const randomPart = Math.random().toString(36).slice(2, 10)
  return `veda-${Date.now().toString(36)}-${randomPart}`
}

function loadOrCreateVedaClientId(): string {
  try {
    const existing = localStorage.getItem(VEDA_CLIENT_ID_KEY)
    if (existing) return existing
    const next = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : createClientId()
    localStorage.setItem(VEDA_CLIENT_ID_KEY, next)
    return next
  } catch {
    return createClientId()
  }
}

function attachAuthHeaders(headers?: AxiosHeaders | Record<string, string>): AxiosHeaders {
  const next = AxiosHeaders.from(headers)
  const token = loadToken()
  if (token) {
    next.set('Authorization', `Bearer ${token}`)
  }
  next.set('X-Veda-Client-Id', loadOrCreateVedaClientId())
  return next
}

api.interceptors.request.use(config => {
  config.headers = attachAuthHeaders(config.headers as AxiosHeaders | Record<string, string> | undefined)
  return config
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
    astro_action_code?: string; astro_action_label?: string
    astro_reason: string; moon_phase: string; eclipse_active: boolean
    as_of_date: string; market_astro_signal: string
    mercury_retrograde: boolean; venus_retrograde: boolean
    moon_illumination: number | null; jupiter_sign: string
    saturn_sign: string; reversal_note: string | null
    evidence_class?: string; source_status?: string; interpretation_type?: string
    high_stakes?: boolean; actionability?: string; output_classification?: string
    boundary_note?: string
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
  if (search?.trim()) params.set('search', search.trim())
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
chatApi.interceptors.request.use(config => {
  config.headers = attachAuthHeaders(config.headers as AxiosHeaders | Record<string, string> | undefined)
  return config
})
export type ChatAttachmentStub = {
  name: string
  mime_type: string
  size_bytes?: number | null
  storage_key?: string | null
  excerpt?: string | null
  kind?: string | null
  warning?: string | null
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
  temporary?: boolean
  save_requires_review?: boolean
  conflict_note?: string | null
  governance_note?: string | null
}
export type ChatLocalEvidenceMeta = {
  used: boolean
  source_count: number
  evidence_kinds: string[]
  predictive_ml_count: number
  platform_snapshot_count: number
  approved_memory_count: number
  attachment_memory_count: number
  repo_count: number
  top_date?: string | null
  sources: ChatLocalEvidenceSource[]
  conflict_note?: string | null
  freshness_note?: string | null
}
export type ChatRetrievalAudit = {
  shadow_enabled: boolean
  configured_primary_mode: string
  resolved_primary_mode: string
  primary_used: boolean
  primary_source_count: number
  primary_attribution_quality: number
  primary_duplicate_noise: number
  shadow_mode?: string | null
  shadow_used: boolean
  shadow_source_count: number
  shadow_attribution_quality: number
  shadow_duplicate_noise: number
  overlap_count: number
  overlap_rate: number
  only_in_primary: string[]
  only_in_shadow: string[]
  notes: string[]
  primary_error?: string | null
  shadow_error?: string | null
}
export type ChatLocalEvidenceSource = {
  source_id: string
  source_type: string
  source_label: string
  evidence_kind: string
  evidence_label: string
  domain: string
  title: string
  entity?: string | null
  date?: string | null
  freshness_class?: string | null
  confidence?: number | null
  summary?: string | null
  attachment_name?: string | null
  repo_label?: string | null
  license_name?: string | null
  model_name?: string | null
  model_version?: string | null
  score_meaning?: string | null
  reliability_note?: string | null
  rank: number
}
export type ChatCapabilities = {
  research_enabled: boolean
  research_provider_available: boolean
  research_runtime_ready: boolean
  default_research_provider: string
  auto_research_for_research_intent: boolean
  attachments_enabled: boolean
  save_to_knowledge_enabled: boolean
  mit_repo_intake_enabled: boolean
  mcp_enabled: boolean
  mcp_server_names: string[]
  supported_attachment_mime_prefixes: string[]
  policy_version?: string
  capability_states?: CapabilityAccessState[]
  protected_safeguards?: Record<string, unknown>
}
export type CapabilityAccessState = {
  capability_id: string
  label: string
  description: string
  admin_access_state: 'ENABLED' | 'DISABLED' | 'ADMIN_ONLY'
  runtime_available: boolean
  capability_maturity: string
  effective_access: string
  effective_answer_mode: string
  reason: string
  policy_version: string
  protected?: boolean
}
export type VedaConfiguration = {
  schema_version: number
  policy_version: string
  capabilities: CapabilityAccessState[]
  protected_safeguards: Record<string, unknown>
}
export type ChatResponseData = {
  reply: string
  session_id: string
  intent: string
  symbols_discussed?: string[]
  flagged?: boolean
  flag_reason?: string | null
  research?: ChatResearchMeta
  local_evidence?: ChatLocalEvidenceMeta
  retrieval_audit?: ChatRetrievalAudit
  access?: Record<string, unknown>
  telemetry?: Record<string, unknown>
}
export type ChatKnowledgeSource = {
  kind: string
  title: string
  url?: string | null
  published_at?: string | null
  excerpt?: string | null
  storage_key?: string | null
  warning?: string | null
}
export type ChatKnowledgeExistingMatch = {
  doc_id: string
  title: string
  summary: string
  saved_at?: string | null
  memory_type: string
  overlap_score: number
  semantic_score?: number
  reason?: string | null
  exact_duplicate?: boolean
  new_value_hint?: string | null
}
export type ChatKnowledgeDraft = {
  draft_id: string
  title: string
  summary: string
  facts: string[]
  tags: string[]
  raw_question: string
  raw_answer: string
  intent?: string | null
  session_id?: string | null
  created_at: string
  sources: ChatKnowledgeSource[]
  existing_matches: ChatKnowledgeExistingMatch[]
  suggested_action: string
  suggestion_reason?: string | null
  status: string
}
export type ChatKnowledgeSaved = {
  draft_id: string
  doc_id: string
  saved_at: string
  title: string
  status: string
  duplicate?: boolean
  attachment_doc_count?: number
  attachment_chunk_count?: number
  decision?: string | null
  merged_into_doc_id?: string | null
}
export type ChatSavedMessage = {
  role: 'user' | 'assistant' | 'system'
  content: string
  intent?: string
  ts: number
  research?: ChatResearchMeta
  localEvidence?: ChatLocalEvidenceMeta
  attachments?: ChatAttachmentStub[]
  knowledge?: ChatKnowledgeSaved
}
export type ChatSavedSession = {
  id: string
  title: string
  messages: ChatSavedMessage[]
  backendSessionId?: string
  createdAt: number
  updatedAt: number
}
export type ChatSavedSessionList = {
  sessions: ChatSavedSession[]
}
export type ChatRepoCapabilityDraft = {
  draft_id: string
  repo_path: string
  repo_label: string
  focus?: string | null
  title: string
  summary: string
  facts: string[]
  tags: string[]
  license_name: string
  license_path: string
  license_excerpt: string
  candidate_files: string[]
  created_at: string
  sources: ChatKnowledgeSource[]
  status: string
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
export const fetchVedaConfiguration = () =>
  chatApi.get<VedaConfiguration>('/veda/configuration').then(r => r.data)
export const updateVedaCapabilityAccess = (capabilityId: string, state: CapabilityAccessState['admin_access_state']) =>
  chatApi.put<VedaConfiguration>(`/veda/configuration/access/${encodeURIComponent(capabilityId)}`, { state }).then(r => r.data)
export const resetVedaConfiguration = () =>
  chatApi.post<VedaConfiguration>('/veda/configuration/reset').then(r => r.data)
export const uploadChatAttachment = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return chatApi.post<ChatAttachmentStub>('/chat/attachments', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}
export const fetchChatSavedSessions = () =>
  chatApi.get<ChatSavedSessionList>('/chat/sessions').then(r => r.data)
export const upsertChatSavedSession = (session: ChatSavedSession) =>
  chatApi.put<ChatSavedSession>(`/chat/sessions/${encodeURIComponent(session.id)}`, session).then(r => r.data)
export const deleteChatSavedSession = (sessionId: string) =>
  chatApi.delete(`/chat/sessions/${encodeURIComponent(sessionId)}`).then(r => r.data)
export const deleteAllChatSavedSessions = () =>
  chatApi.delete('/chat/sessions').then(r => r.data)
export const createKnowledgeDraft = (payload: {
  question: string
  answer: string
  intent?: string
  session_id?: string
  research?: ChatResearchMeta
  attachments?: ChatAttachmentStub[]
}) =>
  chatApi.post<ChatKnowledgeDraft>('/chat/knowledge/draft', {
    question: payload.question,
    answer: payload.answer,
    intent: payload.intent,
    session_id: payload.session_id,
    research: payload.research,
    attachments: payload.attachments ?? [],
  }).then(r => r.data)
export const approveKnowledgeDraft = (
  draftId: string,
  payload: {
    title: string
    summary: string
    facts: string[]
    tags: string[]
    review_note?: string
    decision?: string
  },
) =>
  chatApi.post<ChatKnowledgeSaved>(`/chat/knowledge/draft/${draftId}/approve`, payload).then(r => r.data)
export const discardKnowledgeDraft = (draftId: string) =>
  chatApi.delete<{ draft_id: string; status: string }>(`/chat/knowledge/draft/${draftId}`).then(r => r.data)
export const createRepoCapabilityDraft = (payload: {
  repo_path: string
  repo_label?: string
  focus?: string
}) =>
  chatApi.post<ChatRepoCapabilityDraft>('/chat/capabilities/repo/draft', payload).then(r => r.data)
export const approveRepoCapabilityDraft = (
  draftId: string,
  payload: {
    title: string
    summary: string
    facts: string[]
    tags: string[]
    review_note?: string
  },
) =>
  chatApi.post<ChatKnowledgeSaved>(`/chat/capabilities/repo/draft/${draftId}/approve`, payload).then(r => r.data)

// Phase V-DATA-3 — chat demand analytics ("Recently Asked" panel)
export type ChatAnalyticsRow = { key: string; count: number; share_pct?: number; last_seen?: string | null }
export type ChatAnalytics = {
  source: string
  summary?: Record<string, number>
  top_symbols?: ChatAnalyticsRow[]
}
export const fetchVoiceAnalytics = () =>
  api.get<ChatAnalytics>('/voice/analytics').then(r => r.data)
