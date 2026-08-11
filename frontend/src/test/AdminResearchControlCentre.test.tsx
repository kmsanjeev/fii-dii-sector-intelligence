import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ResearchAdminConsole } from '../components/admin/ResearchAdminConsole'


const researchApiMock = vi.hoisted(() => ({
  createResearchMission: vi.fn(),
  decideResearchCandidate: vi.fn(),
  fetchResearchCandidateDetail: vi.fn(),
  fetchResearchCandidatePromotionPreflight: vi.fn(),
  fetchResearchCandidates: vi.fn(),
  fetchResearchDashboard: vi.fn(),
  fetchResearchDomains: vi.fn(),
  fetchResearchLedger: vi.fn(),
  fetchResearchMissionDetail: vi.fn(),
  fetchResearchMissions: vi.fn(),
  fetchResearchPlatformHealth: vi.fn(),
  fetchResearchRunDetail: vi.fn(),
  fetchResearchRuns: vi.fn(),
  fetchResearchSchedules: vi.fn(),
  pauseResearchMission: vi.fn(),
  promoteResearchCandidate: vi.fn(),
  rollbackResearchPromotion: vi.fn(),
  resumeResearchMission: vi.fn(),
  triggerResearchMission: vi.fn(),
  updateResearchSchedule: vi.fn(),
}))

vi.mock('../api/researchAdmin', async () => {
  const actual = await vi.importActual<typeof import('../api/researchAdmin')>('../api/researchAdmin')
  return {
    ...actual,
    createResearchMission: researchApiMock.createResearchMission,
    decideResearchCandidate: researchApiMock.decideResearchCandidate,
    fetchResearchCandidateDetail: researchApiMock.fetchResearchCandidateDetail,
    fetchResearchCandidatePromotionPreflight: researchApiMock.fetchResearchCandidatePromotionPreflight,
    fetchResearchCandidates: researchApiMock.fetchResearchCandidates,
    fetchResearchDashboard: researchApiMock.fetchResearchDashboard,
    fetchResearchDomains: researchApiMock.fetchResearchDomains,
    fetchResearchLedger: researchApiMock.fetchResearchLedger,
    fetchResearchMissionDetail: researchApiMock.fetchResearchMissionDetail,
    fetchResearchMissions: researchApiMock.fetchResearchMissions,
    fetchResearchPlatformHealth: researchApiMock.fetchResearchPlatformHealth,
    fetchResearchRunDetail: researchApiMock.fetchResearchRunDetail,
    fetchResearchRuns: researchApiMock.fetchResearchRuns,
    fetchResearchSchedules: researchApiMock.fetchResearchSchedules,
    pauseResearchMission: researchApiMock.pauseResearchMission,
    promoteResearchCandidate: researchApiMock.promoteResearchCandidate,
    rollbackResearchPromotion: researchApiMock.rollbackResearchPromotion,
    resumeResearchMission: researchApiMock.resumeResearchMission,
    triggerResearchMission: researchApiMock.triggerResearchMission,
    updateResearchSchedule: researchApiMock.updateResearchSchedule,
  }
})


function renderConsole() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ResearchAdminConsole />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}


const dashboardPayload = {
  research_status: 'HEALTHY',
  engine_status: 'IDLE',
  active_domains: 1,
  active_missions: 2,
  runs_today: 3,
  successful_runs: 2,
  failed_runs: 1,
  sources_today: 4,
  new_candidates: 2,
  pending_approvals: 1,
  needs_more_research: 1,
  high_priority_conflicts: 1,
  approved_today: 1,
  rejected_today: 0,
  last_research_run: '2026-08-11T05:00:00Z',
  next_expected_run: '2026-08-12T05:00:00Z',
  metrics: {},
  domains: [
    {
      domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
      name: 'Vedic Astrology / Jyotisha',
      status: 'ACTIVE',
      description: 'Primary live research domain',
      schedule_policy: {},
    },
  ],
  provider_health: [
    {
      provider_id: 'ddgs-search',
      provider_type: 'WEB_SEARCH',
      status: 'HEALTHY',
      capabilities: ['search'],
      last_successful_use: '2026-08-11T05:00:00Z',
      enabled: true,
      calls_today: 3,
      cooldown_until: null,
      last_failure: null,
      budget_used: {
        queries_today: 2,
        retrievals_today: 1,
      },
    },
  ],
  external_web_research_status: 'ACTIVE',
  knowledge_gaps: [
    {
      gap_id: 'gap-1',
      domain: 'Dasha',
      gap: 'Validate one legacy Vimshottari interpretation rule.',
      priority: 'P1',
      legacy_rule_ids: ['VEDA-LEG-001'],
      mission_count: 1,
      candidate_count: 1,
      status: 'ACTIVE',
    },
  ],
  notifications: [
    {
      id: 'notif-1',
      kind: 'NEW_HIGH_PRIORITY_CANDIDATE',
      entity_id: 'VEDA-RC-001',
      message: 'One high-priority candidate awaits review.',
      priority: 'P1',
      target: 'queue',
    },
  ],
  analytics: {
    research_volume: { missions: 2, runs: 3, sources: 4, candidates: 2 },
    approval_rate: 1,
    rejection_rate: 0,
    contradiction_rate: 1,
    legacy_rule_provenance_progress: { total: 32, source_validated: 1, under_research: 7, unsourced: 18, unresolved: 3 },
    average_review_age_days: 2,
    mission_success_failure: { successful_runs: 2, failed_runs: 1 },
    source_quality: { CLASSICAL_PRIMARY: 1, DISCOVERY_ONLY: 2 },
  },
  coverage: [
    {
      domain: 'Dasha',
      existing_rules: 5,
      source_validated: 1,
      under_research: 2,
      conflicts: 1,
      coverage: 'PARTIAL',
      recommended_action: 'SOURCE_AND_MIGRATE',
    },
  ],
}


const missionListPayload = {
  missions: [
    {
      mission_id: 'VEDA-RM-001',
      domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
      title: 'Validate Vimshottari foundation',
      objective: 'Review governed Vimshottari research findings.',
      research_type: 'CLAIM_VALIDATION',
      priority: 'P1',
      status: 'ACTIVE',
      created_at: '2026-08-10T05:00:00Z',
      updated_at: '2026-08-11T05:00:00Z',
      last_run: '2026-08-11T05:00:00Z',
      next_run: '2026-08-12T05:00:00Z',
      candidate_count: 1,
      open_conflicts: 1,
      follow_up_mission_count: 0,
      known_gap_ids: ['gap-1'],
      required_source_classes: ['CLASSICAL_PRIMARY'],
      minimum_independent_sources: 2,
      query_strategy: {},
      notes: null,
    },
  ],
  total: 1,
  page: 1,
  per_page: 50,
  returned: 1,
}


const runListPayload = {
  runs: [
    {
      run_id: 'VEDA-RUN-001',
      mission_id: 'VEDA-RM-001',
      domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
      trigger_type: 'MANUAL',
      started_at: '2026-08-11T05:00:00Z',
      completed_at: '2026-08-11T05:05:00Z',
      status: 'SUCCESS',
      provider_calls: 1,
      queries_executed: 1,
      sources_discovered: 2,
      sources_accepted: 1,
      sources_rejected: 1,
      evidence_created: 1,
      candidates_created: 1,
      duplicates_detected: 0,
      conflicts_created: 1,
      errors: [],
      mission_title: 'Validate Vimshottari foundation',
      provider_id: 'ddgs-search',
      retrieval_provider_id: 'requests-fetch',
      run_scope: 'EXTERNAL',
      duration_seconds: 300,
    },
  ],
  total: 1,
  page: 1,
  per_page: 50,
  returned: 1,
  sources: [
    {
      observation_id: 'VEDA-OBS-001',
      run_id: 'VEDA-RUN-001',
      provider_id: 'requests-fetch',
      source_uri: 'file://vedic/source',
      canonical_uri: 'file://vedic/source',
      source_title: 'Phaladeepika sample edition',
      source_type: 'PRIMARY_SOURCE',
      author: 'Mantreswara',
      publisher: 'Archive',
      retrieved_at: '2026-08-11T05:01:00Z',
      access_status: 'ACCEPTED',
      claims_supported: ['VEDA-CLM-001'],
      candidate_ids: ['VEDA-RC-001'],
      authority_level: 'Tier A',
      state: 'GOVERNED',
      discovery_only: false,
      provider_type: 'DIRECT_WEB',
      domain_metadata: {},
      trust_metadata: {},
      raw_reference: {},
    },
  ],
}


const candidateListPayload = {
  candidates: [
    {
      candidate_id: 'VEDA-RC-001',
      domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
      mission_id: 'VEDA-RM-001',
      run_id: 'VEDA-RUN-001',
      title: 'Dasha foundation refinement',
      candidate_type: 'NEW_CLAIM',
      claim: 'A pilot governed claim for dasha validation.',
      topic_key: 'dasha.foundation',
      priority: 'P1',
      approval_status: 'PENDING',
      promotion_state: 'NONE',
      novelty_status: 'NEW',
      contradiction_status: 'DIRECT',
      validation_status: 'PASS_WITH_CONDITIONS',
      safety_class: 'HIGH_STAKES',
      confidence: {
        source_confidence: 0.8,
        authority_confidence: 0.9,
        cross_source_confidence: 0.7,
        provenance_confidence: 0.8,
        novelty_confidence: 0.9,
        contradiction_confidence: 0.5,
        domain_confidence: 0.76,
      },
      mission_title: 'Validate Vimshottari foundation',
      evidence_count: 1,
      source_count: 1,
      source_quality: 0.9,
      cross_source_support: 0.7,
      high_stakes: true,
      research_recommendation: 'APPROVE_WITH_CONDITIONS',
      age_days: 1,
      evolution_status: 'UPDATED - NEW EVIDENCE',
      approval_history_count: 0,
      conflict_count: 1,
      created_at: '2026-08-10T05:05:00Z',
      updated_at: '2026-08-11T05:06:00Z',
    },
  ],
  total: 1,
  page: 1,
  per_page: 20,
  returned: 1,
}


const candidateDetailPayload = {
  candidate: candidateListPayload.candidates[0],
  mission: missionListPayload.missions[0],
  run: runListPayload.runs[0],
  evidence_summary: [
    {
      evidence_id: 'VEDA-EVD-001',
      observation_id: 'VEDA-OBS-001',
      passage: 'Translated passage text.',
      claim_hint: 'Candidate summary from extracted evidence.',
      confidence: 0.82,
      domain_metadata: {},
      source: runListPayload.sources[0],
      presentation: {
        source_text: 'Original passage text.',
        translation: 'Translated passage text.',
        model_summary: 'Candidate summary from extracted evidence.',
        model_inference: true,
      },
    },
  ],
  source_observations: [runListPayload.sources[0]],
  validation_summary: [
    {
      validation_id: 'VEDA-VAL-001',
      validator: 'authority',
      status: 'PASS_WITH_CONDITIONS',
      reason: 'Cross-source support is still partial.',
      score: 0.75,
      requires_follow_up: true,
    },
  ],
  approval_history: [],
  conflicts: [
    {
      conflict_id: 'VEDA-CNF-001',
      topic: 'Dasha foundation',
      candidate_id: 'VEDA-RC-001',
      conflicting_candidate_id: 'VEDA-RC-000',
      conflicting_core_id: null,
      conflict_type: 'DIRECT_CONTRADICTION',
      analysis: 'Two sources describe the same condition differently.',
      resolution_status: 'UNRESOLVED',
      approved_resolution: null,
      confidence: 0.61,
      created_at: '2026-08-11T05:04:00Z',
    },
  ],
  related_candidates: [],
  follow_up_missions: [],
  ledger: [
    {
      event_id: 'VEDA-EVT-001',
      timestamp: '2026-08-11T05:05:00Z',
      event_type: 'CANDIDATE_CREATED',
      domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
      mission_id: 'VEDA-RM-001',
      run_id: 'VEDA-RUN-001',
      candidate_id: 'VEDA-RC-001',
      actor_type: 'SYSTEM',
      actor_id: 'system',
      action: 'candidate_created',
      reason: null,
      metadata: {},
    },
  ],
  novelty: 'NEW',
  contradiction: 'DIRECT',
  confidence: candidateListPayload.candidates[0].confidence,
  current_knowledge_comparison: { outcome: 'EXTENDS_EXISTING' },
  status: 'PENDING',
  promotion_preflights: [],
  promotion_history: [],
  rollback_history: [],
  index_sync_history: [],
  core_history: [],
}


const missionDetailPayload = {
  mission: missionListPayload.missions[0],
  schedule: {
    schedule_id: 'VEDA-RSCH-001',
    domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
    mission_id: 'VEDA-RM-001',
    cadence_type: 'DAILY',
    timezone: 'Asia/Calcutta',
    enabled: true,
    next_run_at: '2026-08-12T05:00:00Z',
    last_run_at: '2026-08-11T05:00:00Z',
    misfire_policy: 'RUN_ONCE',
    overlap_policy: 'SKIP',
    priority: 'P1',
    mission_title: 'Validate Vimshottari foundation',
    mission_status: 'ACTIVE',
  },
  run_history: [runListPayload.runs[0]],
  candidate_history: [candidateListPayload.candidates[0]],
  follow_up_missions: [],
  ledger: [],
  open_conflicts: 1,
}


beforeEach(() => {
  vi.clearAllMocks()
  researchApiMock.fetchResearchDashboard.mockResolvedValue(dashboardPayload)
  researchApiMock.fetchResearchDomains.mockResolvedValue({ domains: dashboardPayload.domains })
  researchApiMock.fetchResearchPlatformHealth.mockResolvedValue({
    status: 'HEALTHY',
    providers: {},
    failed_runs: 0,
    db_path: 'tmp/research.sqlite3',
  })
  researchApiMock.fetchResearchMissions.mockResolvedValue(missionListPayload)
  researchApiMock.fetchResearchMissionDetail.mockResolvedValue(missionDetailPayload)
  researchApiMock.fetchResearchRuns.mockResolvedValue(runListPayload)
  researchApiMock.fetchResearchRunDetail.mockResolvedValue({
    run: runListPayload.runs[0],
    mission: missionListPayload.missions[0],
    observations: runListPayload.sources,
    evidence: candidateDetailPayload.evidence_summary,
    candidates: candidateListPayload.candidates,
    timeline: candidateDetailPayload.ledger,
  })
  researchApiMock.fetchResearchCandidates.mockResolvedValue(candidateListPayload)
  researchApiMock.fetchResearchCandidateDetail.mockResolvedValue(candidateDetailPayload)
  researchApiMock.fetchResearchCandidatePromotionPreflight.mockResolvedValue({
    preflight_id: 'VEDA-RPFL-000001',
    candidate_id: 'VEDA-RC-001',
    domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
    approval_id: 'VEDA-RAPR-001',
    promotion_id: null,
    status: 'PASS_WITH_CONDITIONS',
    proposed_operation: 'PROMOTE_WITH_CONDITIONS',
    checks: [],
    blocking_reasons: [],
    warnings: ['Conflict metadata remains attached to promoted knowledge.'],
    required_actions: [],
    existing_core_ids: [],
    created_at: '2026-08-11T06:05:00Z',
  })
  researchApiMock.fetchResearchLedger.mockResolvedValue({
    events: candidateDetailPayload.ledger,
    returned: 1,
    total: 1,
    page: 1,
    per_page: 200,
  })
  researchApiMock.fetchResearchSchedules.mockResolvedValue({
    schedules: [missionDetailPayload.schedule],
    returned: 1,
  })
  researchApiMock.createResearchMission.mockResolvedValue(missionListPayload.missions[0])
  researchApiMock.pauseResearchMission.mockResolvedValue(missionListPayload.missions[0])
  researchApiMock.promoteResearchCandidate.mockResolvedValue({
    preflight: { status: 'PASS_WITH_CONDITIONS' },
    promotion: { promotion_id: 'VEDA-RPRM-000001', promotion_status: 'PROMOTED_WITH_CONDITIONS' },
    index_sync: { status: 'SYNCED' },
    core_records: [{ core_id: 'VEDA-RCORE-000001' }],
  })
  researchApiMock.rollbackResearchPromotion.mockResolvedValue({
    rollback: { rollback_id: 'VEDA-RRBK-000001', promotion_id: 'VEDA-RPRM-000001' },
  })
  researchApiMock.resumeResearchMission.mockResolvedValue(missionListPayload.missions[0])
  researchApiMock.triggerResearchMission.mockResolvedValue(runListPayload.runs[0])
  researchApiMock.updateResearchSchedule.mockResolvedValue(missionDetailPayload.schedule)
  researchApiMock.decideResearchCandidate.mockResolvedValue({
    approval_id: 'VEDA-RAPR-001',
    candidate_id: 'VEDA-RC-001',
    action: 'APPROVE_WITH_CONDITIONS',
    status: 'APPROVED_WITH_CONDITIONS',
    decided_by: 'admin@example.com',
    decided_at: '2026-08-11T06:00:00Z',
    reason: 'Approved with conditions.',
    conditions: ['Track contradiction resolution.'],
    promotion_state: 'PROMOTION_READY',
  })
})


describe('Admin Research Control Centre', () => {
  it('renders dashboard, domain selector, provider health, and attention cards', async () => {
    renderConsole()

    expect(await screen.findByText('Research Control Centre')).toBeInTheDocument()
    expect(await screen.findByText('Research Engine Status')).toBeInTheDocument()
    expect(screen.getByText('Vedic Astrology / Jyotisha')).toBeInTheDocument()
    expect(screen.getByText('One high-priority candidate awaits review.')).toBeInTheDocument()
    expect(screen.getByText('ddgs-search')).toBeInTheDocument()
    expect(screen.getByText(/External web research status: ACTIVE/i)).toBeInTheDocument()
    expect(screen.getByText(/Calls today 3/i)).toBeInTheDocument()
  })

  it('shows candidate evidence detail and submits an acknowledged high-stakes decision', async () => {
    renderConsole()

    fireEvent.click(await screen.findByRole('button', { name: 'Approval Queue' }))
    fireEvent.click(await screen.findByText('Dasha foundation refinement'))

    expect(await screen.findByText('SUPPORTING SOURCES / PASSAGES')).toBeInTheDocument()
    expect(screen.getByText('Original passage text.')).toBeInTheDocument()
    expect(screen.getByText('Explicitly acknowledge high-stakes review.')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('Decision rationale'), {
      target: { value: 'Approve after evidence review.' },
    })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: 'Apply Decision' }))

    await waitFor(() => {
      expect(researchApiMock.decideResearchCandidate).toHaveBeenCalledWith(
        'VEDA-RC-001',
        expect.objectContaining({
          action: 'APPROVE',
          reason: 'Approve after evidence review.',
          acknowledged_high_stakes: true,
        }),
      )
    })
  })

  it('renders mission control and exposes manual mission creation fields', async () => {
    renderConsole()

    fireEvent.click(await screen.findByRole('button', { name: 'Missions' }))

    expect(await screen.findByText('MANUAL RESEARCH MISSION')).toBeInTheDocument()
    expect(screen.getByText('Validate Vimshottari foundation')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Validate Vimshottari foundation'))
    expect(await screen.findByText('RUN HISTORY')).toBeInTheDocument()
    expect(screen.getByText('Research Type: CLAIM_VALIDATION')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('Research question or objective'), {
      target: { value: 'Investigate one additional dignity passage.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create Mission' }))

    await waitFor(() => {
      expect(researchApiMock.createResearchMission).toHaveBeenCalledWith(
        expect.objectContaining({
          objective: 'Investigate one additional dignity passage.',
          domain_id: 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
        }),
      )
    })
  })

  it('runs promotion preflight and promotion for an approved candidate without changing approval semantics', async () => {
    const promotionReadyDetail = {
      ...candidateDetailPayload,
      candidate: {
        ...candidateDetailPayload.candidate,
        approval_status: 'APPROVED_WITH_CONDITIONS',
        promotion_state: 'PROMOTION_READY',
      },
      status: 'APPROVED_WITH_CONDITIONS',
    }

    researchApiMock.fetchResearchCandidateDetail.mockResolvedValue(promotionReadyDetail)

    renderConsole()

    fireEvent.click(await screen.findByRole('button', { name: 'Approval Queue' }))
    fireEvent.click(await screen.findByText('Dasha foundation refinement'))

    expect(await screen.findByText('PROMOTION TO CORE KNOWLEDGE')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('Promotion notes'), {
      target: { value: 'Promote as governed core knowledge pilot.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Run Promotion Preflight' }))

    await waitFor(() => {
      expect(researchApiMock.fetchResearchCandidatePromotionPreflight).toHaveBeenCalledWith('VEDA-RC-001')
    })

    fireEvent.click(screen.getByRole('button', { name: 'Promote to Core Knowledge' }))

    await waitFor(() => {
      expect(researchApiMock.promoteResearchCandidate).toHaveBeenCalledWith('VEDA-RC-001', {
        promotion_notes: 'Promote as governed core knowledge pilot.',
      })
    })
  })
})
