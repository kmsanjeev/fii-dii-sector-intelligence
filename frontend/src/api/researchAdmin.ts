import { api } from './client'

export type ResearchPriority = 'P0' | 'P1' | 'P2' | 'P3' | 'P4'

export type ResearchDashboardResponse = {
  research_status: string
  engine_status: string
  active_domains: number
  active_missions: number
  runs_today: number
  successful_runs: number
  failed_runs: number
  sources_today: number
  new_candidates: number
  pending_approvals: number
  needs_more_research: number
  high_priority_conflicts: number
  approved_today: number
  rejected_today: number
  last_research_run?: string | null
  next_expected_run?: string | null
  metrics: Record<string, number>
  domains: ResearchDomain[]
  provider_health: ResearchProviderHealth[]
  external_web_research_status: string
  knowledge_gaps: ResearchKnowledgeGap[]
  notifications: ResearchNotification[]
  analytics: ResearchAnalytics
  coverage: ResearchCoverageRow[]
}

export type ResearchDomain = {
  domain_id: string
  name: string
  status: string
  description: string
  schedule_policy: Record<string, string>
}

export type ResearchProviderHealth = {
  provider_id: string
  provider_type: string
  status: string
  last_successful_use?: string | null
  capabilities: string[]
  enabled?: boolean
  cooldown_until?: string | null
  last_failure?: string | null
  last_error?: string | null
  calls_today?: number
  budget_used?: {
    queries_today?: number
    retrievals_today?: number
    observations_today?: number
  }
  [key: string]: unknown
}

export type ResearchNotification = {
  id: string
  kind: string
  entity_id: string
  message: string
  priority: string
  target: string
}

export type ResearchKnowledgeGap = {
  gap_id?: string | null
  domain: string
  gap: string
  priority: string
  legacy_rule_ids: string[]
  mission_count: number
  candidate_count: number
  status: string
}

export type ResearchCoverageRow = {
  domain: string
  existing_rules: number
  source_validated: number
  under_research: number
  conflicts: number
  coverage: string
  recommended_action: string
}

export type ResearchAnalytics = {
  research_volume: {
    missions: number
    runs: number
    sources: number
    candidates: number
  }
  approval_rate: number
  rejection_rate: number
  contradiction_rate: number
  legacy_rule_provenance_progress: {
    total: number
    source_validated: number
    under_research: number
    unsourced: number
    unresolved: number
  }
  average_review_age_days: number
  mission_success_failure: {
    successful_runs: number
    failed_runs: number
  }
  source_quality: Record<string, number>
}

export type ResearchMissionRow = {
  mission_id: string
  domain_id: string
  title: string
  objective: string
  research_type: string
  priority: ResearchPriority
  status: string
  created_at: string
  updated_at: string
  last_run?: string | null
  next_run?: string | null
  candidate_count: number
  open_conflicts: number
  follow_up_mission_count: number
  known_gap_ids: string[]
  required_source_classes: string[]
  minimum_independent_sources: number
  query_strategy: Record<string, unknown>
  notes?: string | null
}

export type ResearchMissionListResponse = {
  missions: ResearchMissionRow[]
  total: number
  page: number
  per_page: number
  returned: number
}

export type ResearchMissionDetailResponse = {
  mission: ResearchMissionRow
  schedule?: ResearchScheduleRow | null
  run_history: ResearchRunRow[]
  candidate_history: ResearchCandidateRow[]
  follow_up_missions: ResearchMissionRow[]
  ledger: ResearchLedgerEvent[]
  open_conflicts: number
}

export type ResearchRunRow = {
  run_id: string
  mission_id: string
  domain_id: string
  trigger_type: string
  started_at: string
  completed_at?: string | null
  status: string
  provider_calls: number
  queries_executed: number
  sources_discovered: number
  sources_accepted: number
  sources_rejected: number
  evidence_created: number
  candidates_created: number
  duplicates_detected: number
  conflicts_created: number
  errors: string[]
  mission_title?: string
  provider_id?: string | null
  retrieval_provider_id?: string | null
  run_scope?: string
  duration_seconds?: number | null
}

export type ResearchRunListResponse = {
  runs: ResearchRunRow[]
  total: number
  page: number
  per_page: number
  returned: number
  sources?: ResearchSourceSummary[]
}

export type ResearchRunDetailResponse = {
  run: ResearchRunRow
  mission: ResearchMissionRow
  observations: ResearchSourceSummary[]
  evidence: ResearchEvidenceView[]
  candidates: ResearchCandidateRow[]
  timeline: ResearchLedgerEvent[]
}

export type ResearchCandidateRow = {
  candidate_id: string
  domain_id: string
  mission_id: string
  run_id: string
  title: string
  candidate_type: string
  claim: string
  topic_key: string
  priority: ResearchPriority
  approval_status: string
  promotion_state: string
  novelty_status: string
  contradiction_status: string
  validation_status: string
  safety_class: string
  confidence: {
    source_confidence: number
    authority_confidence: number
    cross_source_confidence: number
    provenance_confidence: number
    novelty_confidence: number
    contradiction_confidence: number
    domain_confidence: number
  }
  mission_title: string
  evidence_count: number
  source_count: number
  source_quality: number
  cross_source_support: number
  high_stakes: boolean
  research_recommendation: string
  age_days: number
  evolution_status: string
  approval_history_count: number
  conflict_count: number
  created_at: string
  updated_at: string
}

export type ResearchCandidateListResponse = {
  candidates: ResearchCandidateRow[]
  total: number
  page: number
  per_page: number
  returned: number
}

export type ResearchSourceSummary = {
  observation_id: string
  run_id: string
  provider_id: string
  source_uri: string
  canonical_uri: string
  source_title: string
  source_type: string
  author?: string | null
  publisher?: string | null
  retrieved_at: string
  access_status: string
  claims_supported: string[]
  candidate_ids: string[]
  authority_level?: string | null
  state: string
  discovery_only: boolean
  provider_type?: string | null
  domain_metadata: Record<string, unknown>
  trust_metadata: Record<string, unknown>
  raw_reference: Record<string, unknown>
}

export type ResearchEvidenceView = {
  evidence_id: string
  observation_id: string
  passage: string
  claim_hint: string
  confidence: number
  domain_metadata: Record<string, unknown>
  source?: ResearchSourceSummary | null
  presentation: {
    source_text?: string | null
    translation?: string | null
    model_summary?: string | null
    model_inference: boolean
  }
}

export type ResearchConflict = {
  conflict_id: string
  topic: string
  candidate_id: string
  conflicting_candidate_id?: string | null
  conflicting_core_id?: string | null
  conflict_type: string
  analysis: string
  resolution_status: string
  approved_resolution?: string | null
  confidence: number
  created_at: string
}

export type ResearchApprovalRecord = {
  approval_id: string
  candidate_id: string
  action: string
  status: string
  actor_type?: string
  decided_by: string
  decided_at: string
  reason: string
  conditions: string[]
  promotion_state: string
}

export type ResearchPromotionPreflightRecord = {
  preflight_id: string
  candidate_id: string
  domain_id: string
  approval_id?: string | null
  promotion_id?: string | null
  status: string
  proposed_operation: string
  checks: Array<{ code: string; status: string; message: string }>
  blocking_reasons: string[]
  warnings: string[]
  required_actions: string[]
  source_ids: string[]
  evidence_ids: string[]
  existing_core_ids: string[]
  high_stakes: boolean
  created_at: string
}

export type ResearchPromotionRecord = {
  promotion_id: string
  candidate_id: string
  domain_id: string
  approval_id: string
  promotion_status: string
  preflight_result: string
  source_ids: string[]
  passage_ids: string[]
  claim_ids: string[]
  rule_ids: string[]
  conflict_ids: string[]
  core_ids: string[]
  previous_version_ids: string[]
  created_at: string
  completed_at?: string | null
  promoted_by: string
  promotion_notes?: string | null
  index_sync_status: string
}

export type ResearchRollbackRecord = {
  rollback_id: string
  promotion_id: string
  domain_id: string
  affected_core_ids: string[]
  restored_core_ids: string[]
  rolled_back_by: string
  rolled_back_at: string
  reason: string
}

export type ResearchIndexSyncRecord = {
  index_sync_id: string
  promotion_id: string
  domain_id: string
  status: string
  created_at: string
  completed_at?: string | null
  result: Record<string, unknown>
}

export type ResearchRagDiagnosticsRequest = {
  query: string
  mode?: 'unified' | 'legacy' | 'shadow'
  top_k?: number
}

export type ResearchRagDiagnosticsResponse = {
  query: string
  mode: string
  resolved_mode: string
  context: string
  summary: Record<string, unknown>
  results: Array<Record<string, unknown>>
  shadow_summary?: Record<string, unknown>
  shadow_results?: Array<Record<string, unknown>>
  retrieval_audit?: Record<string, unknown>
  approved_core: {
    result_count: number
    ontology_matches: Array<{
      entity_id: string
      alias: string
      canonical_name?: string
      entity_type?: string
    }>
    ontology_gaps: string[]
    source_class_diversity: Record<string, number>
    results: Array<Record<string, unknown>>
  }
}

export type CareerValidatedProfile = {
  symbol: string
  domain_id: string
  role_id: string
  canonical_role: string
  detected_synonyms: string
  skills: string
  industry: string
  confidence_score: number
  provenance: string
  shadow_payload_id: string | null
  created_at: string
  validated_by: string
  supporting_signals?: string
  opposing_signals?: string
}

export type CareerValidationSummary = {
  profiles_total: number
  canonical_rows: number
  synthetic_rows: number
  synthetic_rate: number
  symbols_total: number
  industries_covered: number
  top_industries: Array<{ industry: string; count: number }>
  domain_counts: Array<{ domain_id: string; count: number }>
  as_of: string
}

export type CareerValidatedProfilesResponse = {
  records: CareerValidatedProfile[]
  total: number
  returned: number
  summary: CareerValidationSummary
}

export type ResearchValidationRecord = {
  validation_id: string
  validator: string
  status: string
  reason: string
  score: number
  requires_follow_up: boolean
}

export type ResearchLedgerEvent = {
  event_id: string
  timestamp: string
  event_type: string
  domain_id?: string | null
  mission_id?: string | null
  run_id?: string | null
  candidate_id?: string | null
  actor_type: string
  actor_id: string
  action: string
  reason?: string | null
  metadata: Record<string, unknown>
}

export type ResearchCandidateDetailResponse = {
  candidate: ResearchCandidateRow
  mission: ResearchMissionRow
  run: ResearchRunRow
  evidence_summary: ResearchEvidenceView[]
  source_observations: ResearchSourceSummary[]
  validation_summary: ResearchValidationRecord[]
  approval_history: ResearchApprovalRecord[]
  conflicts: ResearchConflict[]
  promotion_preflights: ResearchPromotionPreflightRecord[]
  promotion_history: ResearchPromotionRecord[]
  rollback_history: ResearchRollbackRecord[]
  index_sync_history: ResearchIndexSyncRecord[]
  core_history: Array<Record<string, unknown>>
  related_candidates: ResearchCandidateRow[]
  follow_up_missions: ResearchMissionRow[]
  ledger: ResearchLedgerEvent[]
  novelty: string
  contradiction: string
  confidence: ResearchCandidateRow['confidence']
  current_knowledge_comparison: Record<string, unknown>
  status: string
}

export type ResearchLedgerResponse = {
  events: ResearchLedgerEvent[]
  returned: number
  total: number
  page: number
  per_page: number
}

export type ResearchScheduleRow = {
  schedule_id: string
  domain_id: string
  mission_id: string
  cadence_type: string
  timezone: string
  enabled: boolean
  next_run_at?: string | null
  last_run_at?: string | null
  misfire_policy: string
  overlap_policy: string
  priority: ResearchPriority
  mission_title?: string
  mission_status?: string | null
}

export type ResearchSchedulesResponse = {
  schedules: ResearchScheduleRow[]
  returned: number
}

export type CandidateDecisionPayload = {
  action: string
  reason: string
  conditions?: string[]
  acknowledged_high_stakes?: boolean
  conflict_id?: string | null
  conflict_resolution?: string | null
  conflict_note?: string | null
}

export type CandidatePromotionPayload = {
  promotion_notes?: string | null
}

export type PromotionRollbackPayload = {
  reason: string
}

export const fetchResearchDashboard = (domainId?: string) =>
  api.get<ResearchDashboardResponse>('/research/dashboard', { params: domainId ? { domain_id: domainId } : undefined }).then(r => r.data)

export const fetchResearchPlatformHealth = () =>
  api.get<{ status: string; providers: Record<string, unknown>; failed_runs: number; db_path: string }>('/research/platform/health').then(r => r.data)

export const fetchResearchDomains = () =>
  api.get<{ domains: ResearchDomain[] }>('/research/domains').then(r => r.data)

export const fetchResearchMissions = (params: Record<string, unknown>) =>
  api.get<ResearchMissionListResponse>('/research/missions', { params }).then(r => r.data)

export const createResearchMission = (payload: Record<string, unknown>) =>
  api.post<ResearchMissionRow>('/research/missions', payload).then(r => r.data)

export const fetchResearchMissionDetail = (missionId: string) =>
  api.get<ResearchMissionDetailResponse>(`/research/missions/${missionId}`).then(r => r.data)

export const pauseResearchMission = (missionId: string, payload?: { notes?: string; mode?: string }) =>
  api.post<ResearchMissionRow>(`/research/missions/${missionId}/pause`, payload ?? {}).then(r => r.data)

export const resumeResearchMission = (missionId: string, payload?: { priority?: string; notes?: string }) =>
  api.post<ResearchMissionRow>(`/research/missions/${missionId}/resume`, payload ?? {}).then(r => r.data)

export const triggerResearchMission = (missionId: string) =>
  api.post<ResearchRunRow>(`/research/missions/${missionId}/trigger`).then(r => r.data)

export const fetchResearchRuns = (params: Record<string, unknown>) =>
  api.get<ResearchRunListResponse>('/research/runs', { params }).then(r => r.data)

export const fetchResearchRunDetail = (runId: string) =>
  api.get<ResearchRunDetailResponse>(`/research/runs/${runId}`).then(r => r.data)

export const fetchResearchCandidates = (params: Record<string, unknown>) =>
  api.get<ResearchCandidateListResponse>('/research/candidates', { params }).then(r => r.data)

export const fetchResearchCandidateDetail = (candidateId: string) =>
  api.get<ResearchCandidateDetailResponse>(`/research/candidates/${candidateId}`).then(r => r.data)

export const decideResearchCandidate = (candidateId: string, payload: CandidateDecisionPayload) =>
  api.post<ResearchApprovalRecord>(`/research/candidates/${candidateId}/decision`, payload).then(r => r.data)

export const fetchResearchCandidatePromotionPreflight = (candidateId: string) =>
  api.get<ResearchPromotionPreflightRecord>(`/research/candidates/${candidateId}/promotion-preflight`).then(r => r.data)

export const promoteResearchCandidate = (candidateId: string, payload?: CandidatePromotionPayload) =>
  api.post<{
    preflight: ResearchPromotionPreflightRecord
    promotion: ResearchPromotionRecord
    index_sync?: ResearchIndexSyncRecord | null
    core_records: Array<Record<string, unknown>>
  }>(`/research/candidates/${candidateId}/promote`, payload ?? {}).then(r => r.data)

export const rollbackResearchPromotion = (promotionId: string, payload: PromotionRollbackPayload) =>
  api.post<{
    rollback: ResearchRollbackRecord
    index_sync: ResearchIndexSyncRecord
  }>(`/research/promotions/${promotionId}/rollback`, payload).then(r => r.data)

export const fetchResearchLedger = (params: Record<string, unknown>) =>
  api.get<ResearchLedgerResponse>('/research/ledger', { params }).then(r => r.data)

export const fetchResearchSchedules = (domainId?: string) =>
  api.get<ResearchSchedulesResponse>('/research/schedules', { params: domainId ? { domain_id: domainId } : undefined }).then(r => r.data)

export const updateResearchSchedule = (scheduleId: string, payload: Record<string, unknown>) =>
  api.put<ResearchScheduleRow>(`/research/schedules/${scheduleId}`, payload).then(r => r.data)

export const runResearchRagDiagnostics = (payload: ResearchRagDiagnosticsRequest) =>
  api.post<ResearchRagDiagnosticsResponse>('/research/rag/diagnostics', payload).then(r => r.data)

export const fetchCareerValidatedProfiles = (params?: Record<string, unknown>) =>
  api.get<CareerValidatedProfilesResponse>('/career/validated', { params }).then(r => r.data)
