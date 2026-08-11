import { useState } from 'react'
import type { CSSProperties } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  createResearchMission,
  decideResearchCandidate,
  fetchResearchCandidateDetail,
  fetchResearchCandidates,
  fetchResearchDashboard,
  fetchResearchDomains,
  fetchResearchLedger,
  fetchResearchMissionDetail,
  fetchResearchMissions,
  fetchResearchPlatformHealth,
  fetchResearchRunDetail,
  fetchResearchRuns,
  fetchResearchSchedules,
  pauseResearchMission,
  resumeResearchMission,
  triggerResearchMission,
  updateResearchSchedule,
  type CandidateDecisionPayload,
  type ResearchCandidateRow,
  type ResearchConflict,
  type ResearchCoverageRow,
  type ResearchDashboardResponse,
  type ResearchKnowledgeGap,
  type ResearchNotification,
  type ResearchScheduleRow,
} from '../../api/researchAdmin'

type Section =
  | 'dashboard'
  | 'missions'
  | 'runs'
  | 'queue'
  | 'contradictions'
  | 'gaps'
  | 'sources'
  | 'history'
  | 'schedules'
  | 'analytics'

const SURFACE: CSSProperties = {
  background: '#141720',
  border: '1px solid #1E2332',
  borderRadius: 8,
}

const muted = '#64748B'
const text = '#E2E8F0'
const line = '#1E2332'
const accent = '#22C55E'
const warn = '#F59E0B'
const danger = '#EF4444'
const info = '#60A5FA'

const sectionTabs: Array<{ key: Section; label: string }> = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'missions', label: 'Missions' },
  { key: 'runs', label: 'Runs' },
  { key: 'queue', label: 'Approval Queue' },
  { key: 'contradictions', label: 'Contradictions' },
  { key: 'gaps', label: 'Knowledge Gaps' },
  { key: 'sources', label: 'Sources' },
  { key: 'history', label: 'Research History' },
  { key: 'schedules', label: 'Schedules' },
  { key: 'analytics', label: 'Analytics' },
]

function cardStyle(clickable = false): CSSProperties {
  return {
    ...SURFACE,
    padding: 14,
    cursor: clickable ? 'pointer' : 'default',
  }
}

function buttonStyle(tone: 'default' | 'accent' | 'warning' | 'danger' | 'info' = 'default'): CSSProperties {
  const colors = {
    default: { border: '#2D3348', color: '#94A3B8', bg: 'transparent' },
    accent: { border: accent, color: accent, bg: `${accent}16` },
    warning: { border: warn, color: warn, bg: `${warn}14` },
    danger: { border: danger, color: danger, bg: `${danger}14` },
    info: { border: info, color: info, bg: `${info}14` },
  }[tone]
  return {
    padding: '7px 12px',
    borderRadius: 6,
    border: `1px solid ${colors.border}`,
    background: colors.bg,
    color: colors.color,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 700,
  }
}

const inputStyle: CSSProperties = {
  background: '#0A0D14',
  border: '1px solid #2D3348',
  borderRadius: 6,
  color: text,
  padding: '8px 10px',
  fontSize: 12,
}

function formatStamp(value?: string | null) {
  if (!value) return 'Not available'
  try {
    return new Date(value).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return value
  }
}

function shortText(value: string, length = 140) {
  if (value.length <= length) return value
  return `${value.slice(0, length - 1)}…`
}

function statusColor(value: string) {
  if (value.includes('FAIL') || value.includes('ERROR') || value.includes('REJECT')) return danger
  if (value.includes('PENDING') || value.includes('NEEDS_MORE_RESEARCH') || value.includes('CONTRADICTION')) return warn
  if (value.includes('APPROVED') || value.includes('ACTIVE') || value.includes('SUCCESS') || value.includes('RUNNING')) return accent
  if (value.includes('PROMOTION_READY')) return info
  return muted
}

function priorityColor(priority?: string) {
  if (priority === 'P0') return danger
  if (priority === 'P1') return warn
  if (priority === 'P2') return accent
  return muted
}

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      border: `1px solid ${color}44`,
      background: `${color}18`,
      color,
      fontSize: 10,
      fontWeight: 700,
      borderRadius: 999,
      padding: '2px 8px',
      whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  )
}

function StatTile({ label, value, tone = accent, onClick }: { label: string; value: string | number; tone?: string; onClick?: () => void }) {
  return (
    <div onClick={onClick} style={{ ...cardStyle(Boolean(onClick)), minWidth: 0 }}>
      <div style={{ color: muted, fontSize: 11, marginBottom: 6 }}>{label}</div>
      <div style={{ color: tone, fontSize: 22, fontWeight: 700 }}>{value}</div>
    </div>
  )
}

function SectionButton({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        ...buttonStyle(active ? 'accent' : 'default'),
        padding: '8px 12px',
      }}
    >
      {label}
    </button>
  )
}

function NotificationCard({ item, onOpen }: { item: ResearchNotification; onOpen: (item: ResearchNotification) => void }) {
  return (
    <div onClick={() => onOpen(item)} style={{ ...cardStyle(true), padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
        <Badge label={item.kind.replaceAll('_', ' ')} color={statusColor(item.priority)} />
        <Badge label={item.priority} color={priorityColor(item.priority)} />
      </div>
      <div style={{ color: text, fontSize: 12 }}>{item.message}</div>
    </div>
  )
}

function CandidateDecisionPanel({
  candidate,
  conflicts,
  onSubmit,
  saving,
}: {
  candidate: ResearchCandidateRow
  conflicts: ResearchConflict[]
  saving: boolean
  onSubmit: (payload: CandidateDecisionPayload) => void
}) {
  const [action, setAction] = useState('APPROVE')
  const [reason, setReason] = useState('')
  const [conditions, setConditions] = useState('')
  const [ack, setAck] = useState(false)
  const [conflictResolution, setConflictResolution] = useState('')
  const [selectedConflictId, setSelectedConflictId] = useState('')

  return (
    <div style={{ ...SURFACE, padding: 14 }}>
      <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 12 }}>ADMIN DECISION</div>
      <div style={{ display: 'grid', gap: 10 }}>
        <select value={action} onChange={e => setAction(e.target.value)} style={inputStyle}>
          <option value="APPROVE">APPROVE</option>
          <option value="APPROVE_WITH_CONDITIONS">APPROVE WITH CONDITIONS</option>
          <option value="REJECT">REJECT</option>
          <option value="REQUEST_MORE_RESEARCH">NEEDS MORE RESEARCH</option>
          <option value="MERGE">MERGE</option>
          <option value="SUPERSEDE">SUPERSEDE</option>
          <option value="ARCHIVE">ARCHIVE</option>
        </select>
        <textarea
          value={reason}
          onChange={e => setReason(e.target.value)}
          placeholder="Decision rationale"
          style={{ ...inputStyle, minHeight: 88, resize: 'vertical' }}
        />
        <textarea
          value={conditions}
          onChange={e => setConditions(e.target.value)}
          placeholder="Conditions, one per line when applicable"
          style={{ ...inputStyle, minHeight: 70, resize: 'vertical' }}
        />
        {conflicts.length > 1 && (
          <select value={selectedConflictId} onChange={e => setSelectedConflictId(e.target.value)} style={inputStyle}>
            <option value="">Select conflict</option>
            {conflicts.map(item => (
              <option key={item.conflict_id} value={item.conflict_id}>
                {item.conflict_id} - {item.conflict_type}
              </option>
            ))}
          </select>
        )}
        {candidate.conflict_count > 0 && (
          <select value={conflictResolution} onChange={e => setConflictResolution(e.target.value)} style={inputStyle}>
            <option value="">No conflict action</option>
            <option value="UNRESOLVED">KEEP UNRESOLVED</option>
            <option value="COEXIST">ACCEPT COEXISTENCE</option>
            <option value="CONTEXT_DEPENDENT">CONTEXT DEPENDENT</option>
            <option value="SOURCE_A_PREFERRED">SOURCE A PREFERRED</option>
            <option value="SOURCE_B_PREFERRED">SOURCE B PREFERRED</option>
            <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT EVIDENCE</option>
          </select>
        )}
        {candidate.high_stakes && (
          <label style={{ display: 'flex', gap: 8, alignItems: 'center', color: warn, fontSize: 12 }}>
            <input type="checkbox" checked={ack} onChange={e => setAck(e.target.checked)} />
            Explicitly acknowledge high-stakes review.
          </label>
        )}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={() => onSubmit({
              action,
              reason,
              conditions: conditions.split('\n').map(item => item.trim()).filter(Boolean),
              acknowledged_high_stakes: ack,
              conflict_id: conflictResolution
                ? (selectedConflictId || conflicts[0]?.conflict_id || null)
                : null,
              conflict_resolution: conflictResolution || null,
            })}
            disabled={saving || !reason.trim()}
            style={buttonStyle(action.includes('REJECT') || action === 'ARCHIVE' ? 'danger' : action.includes('RESEARCH') ? 'warning' : 'accent')}
          >
            {saving ? 'Saving…' : 'Apply Decision'}
          </button>
          <div style={{ color: muted, fontSize: 11, alignSelf: 'center' }}>
            Approval only moves the candidate to `PROMOTION_READY`. Production knowledge stays unchanged.
          </div>
        </div>
      </div>
    </div>
  )
}

function CandidateDetail({
  candidateId,
  domainId,
}: {
  candidateId: string | null
  domainId?: string
}) {
  const qc = useQueryClient()
  const detailQuery = useQuery({
    queryKey: ['research-candidate-detail', candidateId],
    queryFn: () => fetchResearchCandidateDetail(candidateId!),
    enabled: Boolean(candidateId),
  })
  const decisionMutation = useMutation({
    mutationFn: (payload: CandidateDecisionPayload) => decideResearchCandidate(candidateId!, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['research-dashboard', domainId] })
      qc.invalidateQueries({ queryKey: ['research-candidates'] })
      qc.invalidateQueries({ queryKey: ['research-candidate-detail', candidateId] })
      qc.invalidateQueries({ queryKey: ['research-ledger'] })
      qc.invalidateQueries({ queryKey: ['research-missions'] })
      qc.invalidateQueries({ queryKey: ['research-runs'] })
    },
  })

  if (!candidateId) {
    return <div style={{ ...SURFACE, padding: 18, color: muted, fontSize: 12 }}>Select a candidate to inspect evidence, contradictions, source quality, and decision history.</div>
  }
  if (detailQuery.isLoading) {
    return <div style={{ ...SURFACE, padding: 18, color: muted, fontSize: 12 }}>Loading candidate detail…</div>
  }
  if (detailQuery.isError || !detailQuery.data) {
    return <div style={{ ...SURFACE, padding: 18, color: danger, fontSize: 12 }}>Candidate detail is unavailable.</div>
  }

  const detail = detailQuery.data
  const candidate = detail.candidate

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ ...SURFACE, padding: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
          <div>
            <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 6 }}>{candidate.candidate_id}</div>
            <div style={{ color: text, fontSize: 16, fontWeight: 700 }}>{candidate.title}</div>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <Badge label={candidate.priority} color={priorityColor(candidate.priority)} />
            <Badge label={candidate.approval_status.replaceAll('_', ' ')} color={statusColor(candidate.approval_status)} />
            <Badge label={candidate.promotion_state.replaceAll('_', ' ')} color={statusColor(candidate.promotion_state)} />
            {candidate.high_stakes && <Badge label="HIGH STAKES" color={warn} />}
          </div>
        </div>
        <div style={{ color: text, fontSize: 13, lineHeight: 1.6, marginBottom: 12 }}>{candidate.claim}</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
          <StatTile label="Evidence" value={candidate.evidence_count} tone={accent} />
          <StatTile label="Source Quality" value={candidate.source_quality.toFixed(2)} tone={info} />
          <StatTile label="Cross-Source Support" value={candidate.cross_source_support.toFixed(2)} tone={accent} />
          <StatTile label="Confidence" value={candidate.confidence.domain_confidence.toFixed(2)} tone={candidate.conflict_count > 0 ? warn : accent} />
        </div>
      </div>

      <div style={{ ...SURFACE, padding: 14 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>CURRENT VEDA KNOWLEDGE</div>
        <pre style={{ margin: 0, color: muted, fontSize: 11, whiteSpace: 'pre-wrap' }}>
          {JSON.stringify(detail.current_knowledge_comparison, null, 2)}
        </pre>
      </div>

      <div style={{ ...SURFACE, padding: 14 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>SUPPORTING SOURCES / PASSAGES</div>
        <div style={{ display: 'grid', gap: 10 }}>
          {detail.evidence_summary.map(item => (
            <div key={item.evidence_id} style={{ border: `1px solid ${line}`, borderRadius: 6, padding: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.source?.source_title ?? item.evidence_id}</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Badge label={String(item.source?.state ?? 'UNKNOWN')} color={statusColor(String(item.source?.state ?? 'UNKNOWN'))} />
                  <Badge label={String(item.source?.authority_level ?? 'UNSPECIFIED')} color={info} />
                </div>
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                <div>
                  <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>SOURCE TEXT</div>
                  <div style={{ color: text, fontSize: 12 }}>{item.presentation.source_text || 'Not captured in this artifact.'}</div>
                </div>
                <div>
                  <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>TRANSLATION</div>
                  <div style={{ color: text, fontSize: 12 }}>{item.presentation.translation || 'Not available.'}</div>
                </div>
                <div>
                  <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>MODEL SUMMARY</div>
                  <div style={{ color: text, fontSize: 12 }}>{item.presentation.model_summary || 'Not available.'}</div>
                </div>
                <div>
                  <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>MODEL INFERENCE</div>
                  <div style={{ color: item.presentation.model_inference ? warn : muted, fontSize: 12 }}>
                    {item.presentation.model_inference ? 'Inference present' : 'No inference flag'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {detail.conflicts.length > 0 && (
        <div style={{ ...SURFACE, padding: 14 }}>
          <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>CONTRADICTIONS</div>
          <div style={{ display: 'grid', gap: 10 }}>
            {detail.conflicts.map(conflict => (
              <div key={conflict.conflict_id} style={{ border: `1px solid ${line}`, borderRadius: 6, padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{conflict.conflict_id}</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <Badge label={conflict.conflict_type} color={warn} />
                    <Badge label={conflict.resolution_status} color={statusColor(conflict.resolution_status)} />
                  </div>
                </div>
                <div style={{ color: text, fontSize: 12 }}>{conflict.analysis}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {detail.approval_history.length > 0 && (
        <div style={{ ...SURFACE, padding: 14 }}>
          <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>DECISION HISTORY</div>
          <div style={{ display: 'grid', gap: 8 }}>
            {detail.approval_history.map(item => (
              <div key={item.approval_id} style={{ borderBottom: `1px solid ${line}`, paddingBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                  <Badge label={item.status} color={statusColor(item.status)} />
                  <div style={{ color: muted, fontSize: 11 }}>{formatStamp(item.decided_at)}</div>
                </div>
                <div style={{ color: text, fontSize: 12, marginTop: 6 }}>{item.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <CandidateDecisionPanel
        candidate={candidate}
        conflicts={detail.conflicts}
        saving={decisionMutation.isPending}
        onSubmit={payload => decisionMutation.mutate(payload)}
      />

      <div style={{ ...SURFACE, padding: 14 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>RESEARCH HISTORY</div>
        <div style={{ display: 'grid', gap: 8 }}>
          {detail.ledger.map(item => (
            <div key={item.event_id} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, borderBottom: `1px solid ${line}`, paddingBottom: 6 }}>
              <div>
                <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.event_type}</div>
                <div style={{ color: muted, fontSize: 11 }}>{item.action}</div>
              </div>
              <div style={{ color: muted, fontSize: 11 }}>{formatStamp(item.timestamp)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function DashboardView({
  dashboard,
  onNotificationOpen,
  onOpenQueue,
  onOpenContradictions,
  onOpenGaps,
}: {
  dashboard: ResearchDashboardResponse
  onNotificationOpen: (item: ResearchNotification) => void
  onOpenQueue: () => void
  onOpenContradictions: () => void
  onOpenGaps: () => void
}) {
  return (
    <div style={{ display: 'grid', gap: 14 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
        <StatTile label="Research Engine Status" value={dashboard.engine_status} tone={statusColor(dashboard.engine_status)} />
        <StatTile label="Active Domains" value={dashboard.active_domains} tone={accent} />
        <StatTile label="Active Missions" value={dashboard.active_missions} tone={accent} />
        <StatTile label="Runs Today" value={dashboard.runs_today} tone={info} />
        <StatTile label="Successful Runs" value={dashboard.successful_runs} tone={accent} />
        <StatTile label="Failed Runs" value={dashboard.failed_runs} tone={dashboard.failed_runs > 0 ? danger : muted} />
        <StatTile label="Pending Approval" value={dashboard.pending_approvals} tone={warn} onClick={onOpenQueue} />
        <StatTile label="Open Contradictions" value={dashboard.high_priority_conflicts} tone={warn} onClick={onOpenContradictions} />
        <StatTile label="Knowledge Gaps" value={dashboard.knowledge_gaps.length} tone={info} onClick={onOpenGaps} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 12 }}>
        <div style={{ ...SURFACE, padding: 14 }}>
          <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>ATTENTION</div>
          <div style={{ display: 'grid', gap: 8 }}>
            {dashboard.notifications.length === 0 && (
              <div style={{ color: muted, fontSize: 12 }}>No active research attention items.</div>
            )}
            {dashboard.notifications.map(item => (
              <NotificationCard key={item.id} item={item} onOpen={onNotificationOpen} />
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gap: 12 }}>
          <div style={{ ...SURFACE, padding: 14 }}>
            <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>RESEARCH CONTINUITY</div>
            <div style={{ color: text, fontSize: 12, lineHeight: 1.6 }}>
              Research continues according to mission and schedule policies even if Admin does nothing today.
            </div>
            <div style={{ color: muted, fontSize: 11, marginTop: 8 }}>
              Last run: {formatStamp(dashboard.last_research_run)}<br />
              Next expected run: {formatStamp(dashboard.next_expected_run)}
            </div>
          </div>
          <div style={{ ...SURFACE, padding: 14 }}>
            <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>PROVIDER HEALTH</div>
            <div style={{ display: 'grid', gap: 8 }}>
              {dashboard.provider_health.map(item => (
                <div key={item.provider_id} style={{ borderBottom: `1px solid ${line}`, paddingBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                    <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.provider_id}</div>
                    <Badge label={String(item.status)} color={statusColor(String(item.status))} />
                  </div>
                  <div style={{ color: muted, fontSize: 11 }}>
                    {item.provider_type} · last successful use {formatStamp(item.last_successful_use)}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ color: muted, fontSize: 11, marginTop: 8 }}>
              External web research status: {dashboard.external_web_research_status}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function ResearchAdminConsole() {
  const qc = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [domainId, setDomainId] = useState<string | undefined>()
  const [missionSearch, setMissionSearch] = useState('')
  const [missionStatus, setMissionStatus] = useState('')
  const [candidateSearch, setCandidateSearch] = useState('')
  const [candidateStatus, setCandidateStatus] = useState('')
  const [candidateSortBy, setCandidateSortBy] = useState('updated_at')
  const candidateSortDir = 'desc'
  const [candidatePage, setCandidatePage] = useState(1)
  const [runStatus, setRunStatus] = useState('')
  const [historySearch, setHistorySearch] = useState('')
  const [selectedMissionId, setSelectedMissionId] = useState<string | null>(null)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null)
  const [newMissionQuestion, setNewMissionQuestion] = useState('')
  const [newMissionType, setNewMissionType] = useState('CLAIM_VALIDATION')
  const [newMissionPriority, setNewMissionPriority] = useState('P2')
  const section = (searchParams.get('research') as Section | null) || 'dashboard'

  const setSection = (value: Section) => {
    const next = new URLSearchParams(searchParams)
    next.set('research', value)
    setCandidatePage(1)
    setSearchParams(next)
  }

  const dashboardQuery = useQuery({
    queryKey: ['research-dashboard', domainId],
    queryFn: () => fetchResearchDashboard(domainId),
  })

  const domainsQuery = useQuery({
    queryKey: ['research-domains'],
    queryFn: fetchResearchDomains,
  })

  const healthQuery = useQuery({
    queryKey: ['research-health'],
    queryFn: fetchResearchPlatformHealth,
  })

  const missionsQuery = useQuery({
    queryKey: ['research-missions', domainId, missionSearch, missionStatus],
    queryFn: () => fetchResearchMissions({
      domain_id: domainId,
      search: missionSearch || undefined,
      status: missionStatus || undefined,
      page: 1,
      per_page: 50,
    }),
  })

  const runsQuery = useQuery({
    queryKey: ['research-runs', domainId, runStatus],
    queryFn: () => fetchResearchRuns({
      domain_id: domainId,
      status: runStatus || undefined,
      page: 1,
      per_page: 50,
      include_sources: true,
    }),
  })

  const queueQuery = useQuery({
    queryKey: ['research-candidates', domainId, section, candidateSearch, candidateStatus, candidateSortBy, candidateSortDir, candidatePage],
    queryFn: () => fetchResearchCandidates({
      domain_id: domainId,
      search: candidateSearch || undefined,
      approval_status: section === 'queue' ? candidateStatus || undefined : undefined,
      contradiction_only: section === 'contradictions',
      high_stakes_only: false,
      sort_by: candidateSortBy,
      sort_dir: candidateSortDir,
      page: candidatePage,
      per_page: 20,
    }),
  })

  const missionDetailQuery = useQuery({
    queryKey: ['research-mission-detail', selectedMissionId],
    queryFn: () => fetchResearchMissionDetail(selectedMissionId!),
    enabled: Boolean(selectedMissionId),
  })

  const runDetailQuery = useQuery({
    queryKey: ['research-run-detail', selectedRunId],
    queryFn: () => fetchResearchRunDetail(selectedRunId!),
    enabled: Boolean(selectedRunId),
  })

  const ledgerQuery = useQuery({
    queryKey: ['research-ledger', domainId, historySearch],
    queryFn: () => fetchResearchLedger({
      domain_id: domainId,
      search: historySearch || undefined,
      limit: 200,
      page: 1,
    }),
  })

  const schedulesQuery = useQuery({
    queryKey: ['research-schedules', domainId],
    queryFn: () => fetchResearchSchedules(domainId),
  })

  const createMissionMutation = useMutation({
    mutationFn: () => createResearchMission({
      domain_id: domainId || 'VEDA-DOMAIN-VEDIC-ASTROLOGY',
      title: shortText(newMissionQuestion || 'Manual research mission', 70),
      objective: newMissionQuestion,
      research_type: newMissionType,
      priority: newMissionPriority,
      status: 'QUEUED',
      created_by: 'admin',
      query_strategy: {},
    }),
    onSuccess: mission => {
      setSelectedMissionId(mission.mission_id)
      setNewMissionQuestion('')
      qc.invalidateQueries({ queryKey: ['research-dashboard'] })
      qc.invalidateQueries({ queryKey: ['research-missions'] })
      setSection('missions')
    },
  })

  const missionActionMutation = useMutation({
    mutationFn: async (payload: { missionId: string; action: 'pause' | 'resume' | 'archive' | 'trigger'; priority?: string }) => {
      if (payload.action === 'pause') return pauseResearchMission(payload.missionId)
      if (payload.action === 'archive') return pauseResearchMission(payload.missionId, { mode: 'ARCHIVE' })
      if (payload.action === 'resume') return resumeResearchMission(payload.missionId, { priority: payload.priority })
      return triggerResearchMission(payload.missionId)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['research-dashboard'] })
      qc.invalidateQueries({ queryKey: ['research-missions'] })
      qc.invalidateQueries({ queryKey: ['research-runs'] })
      if (selectedMissionId) qc.invalidateQueries({ queryKey: ['research-mission-detail', selectedMissionId] })
    },
  })

  const scheduleMutation = useMutation({
    mutationFn: ({ scheduleId, payload }: { scheduleId: string; payload: Record<string, unknown> }) => updateResearchSchedule(scheduleId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['research-dashboard'] })
      qc.invalidateQueries({ queryKey: ['research-schedules'] })
    },
  })

  const dashboard = dashboardQuery.data
  const missions = missionsQuery.data?.missions ?? []
  const runs = runsQuery.data?.runs ?? []
  const candidateRows = queueQuery.data?.candidates ?? []
  const schedules = schedulesQuery.data?.schedules ?? []
  const sources = runsQuery.data?.sources ?? []
  const coverageRows = dashboard?.coverage ?? []
  const selectedSource = sources.find(item => item.observation_id === selectedSourceId) ?? null

  const openNotification = (item: ResearchNotification) => {
    if (item.target === 'queue') setSection('queue')
    if (item.target === 'contradictions') setSection('contradictions')
    if (item.target === 'runs') setSection('runs')
    if (item.target === 'missions') setSection('missions')
  }

  const activeDomainOptions = (dashboard?.domains ?? domainsQuery.data?.domains ?? []).filter(item => item.status !== 'TEST')

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ ...SURFACE, padding: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 1.6 }}>ADMIN / RESEARCH</div>
            <div style={{ color: text, fontSize: 18, fontWeight: 700, marginTop: 4 }}>Research Control Centre</div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <select value={domainId ?? ''} onChange={e => setDomainId(e.target.value || undefined)} style={inputStyle}>
              <option value="">All Active Domains</option>
              {activeDomainOptions.map(item => (
                <option key={item.domain_id} value={item.domain_id}>{item.name}</option>
              ))}
            </select>
            <Badge label={dashboard?.engine_status ?? healthQuery.data?.status ?? 'LOADING'} color={statusColor(dashboard?.engine_status ?? healthQuery.data?.status ?? 'LOADING')} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
          {sectionTabs.map(item => (
            <SectionButton key={item.key} active={section === item.key} label={item.label} onClick={() => setSection(item.key)} />
          ))}
        </div>
      </div>

      {dashboardQuery.isLoading && (
        <div style={{ ...SURFACE, padding: 18, color: muted, fontSize: 12 }}>Loading research governance data…</div>
      )}

      {dashboardQuery.isError && (
        <div style={{ ...SURFACE, padding: 18, color: danger, fontSize: 12 }}>
          Research admin surfaces are unavailable. Confirm backend auth and research services are running.
        </div>
      )}

      {dashboard && section === 'dashboard' && (
        <DashboardView
          dashboard={dashboard}
          onNotificationOpen={openNotification}
          onOpenQueue={() => setSection('queue')}
          onOpenContradictions={() => setSection('contradictions')}
          onOpenGaps={() => setSection('gaps')}
        />
      )}

      {section === 'missions' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 14 }}>
          <div style={{ display: 'grid', gap: 12 }}>
            <div style={{ ...SURFACE, padding: 14 }}>
              <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>MANUAL RESEARCH MISSION</div>
              <div style={{ display: 'grid', gap: 10 }}>
                <textarea value={newMissionQuestion} onChange={e => setNewMissionQuestion(e.target.value)} placeholder="Research question or objective" style={{ ...inputStyle, minHeight: 76, resize: 'vertical' }} />
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <select value={newMissionType} onChange={e => setNewMissionType(e.target.value)} style={inputStyle}>
                    <option value="CLAIM_VALIDATION">CLAIM_VALIDATION</option>
                    <option value="LEGACY_RULE_PROVENANCE">LEGACY_RULE_PROVENANCE</option>
                    <option value="CONTRADICTION_RESOLUTION">CONTRADICTION_RESOLUTION</option>
                    <option value="KNOWLEDGE_GAP">KNOWLEDGE_GAP</option>
                    <option value="SOURCE_VERIFICATION">SOURCE_VERIFICATION</option>
                  </select>
                  <select value={newMissionPriority} onChange={e => setNewMissionPriority(e.target.value)} style={inputStyle}>
                    <option value="P0">P0</option>
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                    <option value="P4">P4</option>
                  </select>
                  <button disabled={createMissionMutation.isPending || !newMissionQuestion.trim()} onClick={() => createMissionMutation.mutate()} style={buttonStyle('accent')}>
                    {createMissionMutation.isPending ? 'Creating…' : 'Create Mission'}
                  </button>
                </div>
              </div>
            </div>

            <div style={{ ...SURFACE, padding: 14 }}>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
                <input value={missionSearch} onChange={e => setMissionSearch(e.target.value)} placeholder="Search mission title or objective" style={{ ...inputStyle, flex: 1, minWidth: 220 }} />
                <select value={missionStatus} onChange={e => setMissionStatus(e.target.value)} style={inputStyle}>
                  <option value="">All Statuses</option>
                  <option value="QUEUED">QUEUED</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PAUSED">PAUSED</option>
                  <option value="ARCHIVED">ARCHIVED</option>
                </select>
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                {missions.map(item => (
                  <div key={item.mission_id} onClick={() => setSelectedMissionId(item.mission_id)} style={{ ...cardStyle(true), padding: 12, borderColor: selectedMissionId === item.mission_id ? accent : line }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                      <div style={{ color: text, fontSize: 13, fontWeight: 700 }}>{item.title}</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        <Badge label={item.priority} color={priorityColor(item.priority)} />
                        <Badge label={item.status} color={statusColor(item.status)} />
                      </div>
                    </div>
                    <div style={{ color: muted, fontSize: 11 }}>{shortText(item.objective)}</div>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 8, color: muted, fontSize: 11 }}>
                      <span>Candidates {item.candidate_count}</span>
                      <span>Conflicts {item.open_conflicts}</span>
                      <span>Last run {item.last_run ? formatStamp(item.last_run) : 'Never'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gap: 12 }}>
            {!selectedMissionId && <div style={{ ...SURFACE, padding: 18, color: muted, fontSize: 12 }}>Select a mission to inspect objective, schedule, run history, candidate history, and follow-up work.</div>}
            {missionDetailQuery.data && (
              <>
                <div style={{ ...SURFACE, padding: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                    <div style={{ color: text, fontSize: 15, fontWeight: 700 }}>{missionDetailQuery.data.mission.title}</div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      <button style={buttonStyle('warning')} onClick={() => missionActionMutation.mutate({ missionId: selectedMissionId!, action: 'pause' })}>Pause</button>
                      <button style={buttonStyle('accent')} onClick={() => missionActionMutation.mutate({ missionId: selectedMissionId!, action: 'resume' })}>Resume</button>
                      <button style={buttonStyle('info')} onClick={() => missionActionMutation.mutate({ missionId: selectedMissionId!, action: 'trigger' })}>Run Now</button>
                      <button style={buttonStyle('danger')} onClick={() => missionActionMutation.mutate({ missionId: selectedMissionId!, action: 'archive' })}>Archive</button>
                    </div>
                  </div>
                  <div style={{ color: text, fontSize: 12, lineHeight: 1.6 }}>{missionDetailQuery.data.mission.objective}</div>
                  <div style={{ display: 'grid', gap: 8, marginTop: 12, color: muted, fontSize: 11 }}>
                    <div>Research Type: {missionDetailQuery.data.mission.research_type}</div>
                    <div>Source Requirements: {missionDetailQuery.data.mission.required_source_classes.join(', ') || 'Not constrained'}</div>
                    <div>Minimum Independent Sources: {missionDetailQuery.data.mission.minimum_independent_sources}</div>
                    <div>Schedule: {missionDetailQuery.data.schedule ? `${missionDetailQuery.data.schedule.cadence_type} · next ${formatStamp(missionDetailQuery.data.schedule.next_run_at)}` : 'Manual only'}</div>
                  </div>
                </div>
                <div style={{ ...SURFACE, padding: 14 }}>
                  <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>RUN HISTORY</div>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {missionDetailQuery.data.run_history.map(item => (
                      <div key={item.run_id} style={{ borderBottom: `1px solid ${line}`, paddingBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                          <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.run_id}</div>
                          <Badge label={item.status} color={statusColor(item.status)} />
                        </div>
                        <div style={{ color: muted, fontSize: 11 }}>{formatStamp(item.started_at)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {section === 'runs' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div style={{ ...SURFACE, padding: 14 }}>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
              <select value={runStatus} onChange={e => setRunStatus(e.target.value)} style={inputStyle}>
                <option value="">All Runs</option>
                <option value="SUCCESS">SUCCESS</option>
                <option value="PARTIAL">PARTIAL</option>
                <option value="FAILED">FAILED</option>
                <option value="RECOVERABLE">RECOVERABLE</option>
              </select>
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {runs.map(item => (
                <div key={item.run_id} onClick={() => setSelectedRunId(item.run_id)} style={{ ...cardStyle(true), padding: 12, borderColor: selectedRunId === item.run_id ? accent : line }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                    <div style={{ color: text, fontSize: 13, fontWeight: 700 }}>{item.run_id}</div>
                    <Badge label={item.status} color={statusColor(item.status)} />
                  </div>
                  <div style={{ color: muted, fontSize: 11, marginTop: 6 }}>{item.mission_title}</div>
                  <div style={{ color: muted, fontSize: 11, marginTop: 6 }}>
                    {item.provider_id} · {item.sources_discovered} sources · {item.candidates_created} candidates
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gap: 12 }}>
            {!selectedRunId && <div style={{ ...SURFACE, padding: 18, color: muted, fontSize: 12 }}>Select a run to inspect timeline, queries, sources, evidence, and candidate creation.</div>}
            {runDetailQuery.data && (
              <>
                <div style={{ ...SURFACE, padding: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                    <div style={{ color: text, fontSize: 15, fontWeight: 700 }}>{runDetailQuery.data.run.run_id}</div>
                    <Badge label={runDetailQuery.data.run.status} color={statusColor(runDetailQuery.data.run.status)} />
                  </div>
                  <div style={{ color: muted, fontSize: 11, marginBottom: 10 }}>
                    {runDetailQuery.data.mission.title} · {runDetailQuery.data.run.trigger_type} · {formatStamp(runDetailQuery.data.run.started_at)}
                  </div>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {runDetailQuery.data.timeline.map(event => (
                      <div key={event.event_id} style={{ borderBottom: `1px solid ${line}`, paddingBottom: 8 }}>
                        <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{event.event_type}</div>
                        <div style={{ color: muted, fontSize: 11 }}>{formatStamp(event.timestamp)} · {event.action}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ ...SURFACE, padding: 14 }}>
                  <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>RUN SOURCES</div>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {runDetailQuery.data.observations.map(item => (
                      <div key={item.observation_id} style={{ borderBottom: `1px solid ${line}`, paddingBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                          <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.source_title}</div>
                          <Badge label={item.state} color={statusColor(item.state)} />
                        </div>
                        <div style={{ color: muted, fontSize: 11 }}>{item.provider_id} · {formatStamp(item.retrieved_at)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {(section === 'queue' || section === 'contradictions') && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.15fr', gap: 14 }}>
          <div style={{ ...SURFACE, padding: 14 }}>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
              <input
                value={candidateSearch}
                onChange={e => {
                  setCandidateSearch(e.target.value)
                  setCandidatePage(1)
                }}
                placeholder="Search claim, title, topic"
                style={{ ...inputStyle, flex: 1, minWidth: 220 }}
              />
              {section === 'queue' && (
                <select
                  value={candidateStatus}
                  onChange={e => {
                    setCandidateStatus(e.target.value)
                    setCandidatePage(1)
                  }}
                  style={inputStyle}
                >
                  <option value="">All Queue States</option>
                  <option value="PENDING">PENDING</option>
                  <option value="UNDER_REVIEW">UNDER REVIEW</option>
                  <option value="NEEDS_MORE_RESEARCH">NEEDS MORE RESEARCH</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="APPROVED_WITH_CONDITIONS">APPROVED WITH CONDITIONS</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
              )}
              <select
                value={candidateSortBy}
                onChange={e => {
                  setCandidateSortBy(e.target.value)
                  setCandidatePage(1)
                }}
                style={inputStyle}
              >
                <option value="updated_at">Recently Updated</option>
                <option value="priority">Priority</option>
                <option value="confidence">Highest Confidence</option>
                <option value="evidence">Most Evidence</option>
                <option value="high_stakes">High Stakes</option>
                <option value="contradictions">Contradictions</option>
              </select>
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {candidateRows.map(item => (
                <div key={item.candidate_id} onClick={() => setSelectedCandidateId(item.candidate_id)} style={{ ...cardStyle(true), padding: 12, borderColor: selectedCandidateId === item.candidate_id ? accent : line }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                    <div style={{ color: text, fontSize: 13, fontWeight: 700 }}>{item.title}</div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      <Badge label={item.priority} color={priorityColor(item.priority)} />
                      <Badge label={item.approval_status} color={statusColor(item.approval_status)} />
                    </div>
                  </div>
                  <div style={{ color: text, fontSize: 12 }}>{shortText(item.claim, 180)}</div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                    <Badge label={item.novelty_status} color={info} />
                    <Badge label={item.contradiction_status} color={item.contradiction_status === 'NONE' ? muted : warn} />
                    {item.high_stakes && <Badge label="HIGH STAKES" color={warn} />}
                    <Badge label={item.evolution_status} color={accent} />
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center', marginTop: 12 }}>
              <div style={{ color: muted, fontSize: 11 }}>
                Showing {candidateRows.length} of {queueQuery.data?.total ?? 0} candidates
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  style={buttonStyle('default')}
                  disabled={candidatePage <= 1}
                  onClick={() => setCandidatePage(page => Math.max(1, page - 1))}
                >
                  Previous
                </button>
                <div style={{ color: text, fontSize: 12, alignSelf: 'center' }}>Page {candidatePage}</div>
                <button
                  style={buttonStyle('default')}
                  disabled={candidatePage * (queueQuery.data?.per_page ?? 20) >= (queueQuery.data?.total ?? 0)}
                  onClick={() => setCandidatePage(page => page + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          <CandidateDetail candidateId={selectedCandidateId} domainId={domainId} />
        </div>
      )}

      {section === 'gaps' && (
        <div style={{ display: 'grid', gap: 12 }}>
          {dashboard?.knowledge_gaps.map((gap: ResearchKnowledgeGap) => {
            const relatedMission = missions.find(item => gap.gap_id && item.known_gap_ids.includes(gap.gap_id))
            return (
              <div key={gap.gap_id ?? gap.gap} style={{ ...SURFACE, padding: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  <div>
                    <div style={{ color: text, fontSize: 14, fontWeight: 700 }}>{gap.domain}</div>
                    <div style={{ color: muted, fontSize: 11 }}>{gap.gap}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <Badge label={gap.priority} color={priorityColor(gap.priority)} />
                    <Badge label={gap.status} color={statusColor(gap.status)} />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10, color: muted, fontSize: 11 }}>
                  <span>Missions {gap.mission_count}</span>
                  <span>Candidates {gap.candidate_count}</span>
                  <span>Legacy Rules {gap.legacy_rule_ids.join(', ') || 'None'}</span>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {!relatedMission && (
                    <button
                      style={buttonStyle('accent')}
                      onClick={() => {
                        setNewMissionQuestion(gap.gap)
                        setNewMissionType('KNOWLEDGE_GAP')
                        setNewMissionPriority(gap.priority)
                        setSection('missions')
                      }}
                    >
                      Start Research
                    </button>
                  )}
                  {relatedMission && (
                    <>
                      <button style={buttonStyle('info')} onClick={() => { setSelectedMissionId(relatedMission.mission_id); setSection('missions') }}>
                        Open Mission
                      </button>
                      <button style={buttonStyle('warning')} onClick={() => missionActionMutation.mutate({ missionId: relatedMission.mission_id, action: 'resume', priority: 'P1' })}>
                        Increase Priority
                      </button>
                    </>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {section === 'sources' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div style={{ ...SURFACE, padding: 14 }}>
            <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>SOURCE INTELLIGENCE EXPLORER</div>
            <div style={{ display: 'grid', gap: 8 }}>
              {sources.map(item => (
                <div key={item.observation_id} onClick={() => setSelectedSourceId(item.observation_id)} style={{ ...cardStyle(true), padding: 12, borderColor: selectedSourceId === item.observation_id ? accent : line }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                    <div style={{ color: text, fontSize: 13, fontWeight: 700 }}>{item.source_title}</div>
                    <Badge label={item.state} color={statusColor(item.state)} />
                  </div>
                  <div style={{ color: muted, fontSize: 11, marginTop: 6 }}>
                    {item.author || 'Unknown author'} · {item.authority_level || 'Unscored'} · {formatStamp(item.retrieved_at)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ ...SURFACE, padding: 14 }}>
            {!selectedSource && <div style={{ color: muted, fontSize: 12 }}>Select a source to inspect metadata, claim usage, authority state, and trust flags.</div>}
            {selectedSource && (
              <div style={{ display: 'grid', gap: 10 }}>
                <div>
                  <div style={{ color: text, fontSize: 15, fontWeight: 700 }}>{selectedSource.source_title}</div>
                  <div style={{ color: muted, fontSize: 11, marginTop: 6 }}>
                    {selectedSource.author || 'Unknown author'} · {selectedSource.publisher || 'Unknown publisher'}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Badge label={selectedSource.state} color={statusColor(selectedSource.state)} />
                  <Badge label={String(selectedSource.authority_level || 'UNSPECIFIED')} color={info} />
                  <Badge label={selectedSource.source_type} color={muted} />
                </div>
                <pre style={{ margin: 0, color: muted, fontSize: 11, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify({
                    candidate_ids: selectedSource.candidate_ids,
                    claims_supported: selectedSource.claims_supported,
                    trust_metadata: selectedSource.trust_metadata,
                    raw_reference: selectedSource.raw_reference,
                  }, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {section === 'history' && (
        <div style={{ ...SURFACE, padding: 14 }}>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
            <input value={historySearch} onChange={e => setHistorySearch(e.target.value)} placeholder="Search date, mission, run, candidate, source, event" style={{ ...inputStyle, flex: 1, minWidth: 240 }} />
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {(ledgerQuery.data?.events ?? []).map(item => (
              <div key={item.event_id} style={{ borderBottom: `1px solid ${line}`, paddingBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                  <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.event_type}</div>
                  <div style={{ color: muted, fontSize: 11 }}>{formatStamp(item.timestamp)}</div>
                </div>
                <div style={{ color: muted, fontSize: 11 }}>
                  Mission {item.mission_id || '—'} · Run {item.run_id || '—'} · Candidate {item.candidate_id || '—'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {section === 'schedules' && (
        <div style={{ display: 'grid', gap: 12 }}>
          {schedules.map((item: ResearchScheduleRow) => (
            <div key={item.schedule_id} style={{ ...SURFACE, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                <div>
                  <div style={{ color: text, fontSize: 14, fontWeight: 700 }}>{item.mission_title || item.mission_id}</div>
                  <div style={{ color: muted, fontSize: 11 }}>{item.schedule_id}</div>
                </div>
                <Badge label={item.enabled ? 'ENABLED' : 'DISABLED'} color={item.enabled ? accent : muted} />
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <select defaultValue={item.cadence_type} onChange={e => scheduleMutation.mutate({ scheduleId: item.schedule_id, payload: { cadence_type: e.target.value } })} style={inputStyle}>
                  <option value="MANUAL_ONLY">MANUAL ONLY</option>
                  <option value="HOURLY">HOURLY</option>
                  <option value="DAILY">DAILY</option>
                  <option value="WEEKLY">WEEKLY</option>
                  <option value="CUSTOM">CUSTOM</option>
                </select>
                <select defaultValue={item.overlap_policy} onChange={e => scheduleMutation.mutate({ scheduleId: item.schedule_id, payload: { overlap_policy: e.target.value } })} style={inputStyle}>
                  <option value="SKIP">SKIP</option>
                  <option value="QUEUE">QUEUE</option>
                  <option value="COALESCE">COALESCE</option>
                  <option value="ALLOW">ALLOW</option>
                </select>
                <select defaultValue={item.misfire_policy} onChange={e => scheduleMutation.mutate({ scheduleId: item.schedule_id, payload: { misfire_policy: e.target.value } })} style={inputStyle}>
                  <option value="RUN_ONCE">RUN ONCE</option>
                  <option value="SKIP">SKIP</option>
                  <option value="RESCHEDULE">RESCHEDULE</option>
                </select>
                <button style={buttonStyle(item.enabled ? 'warning' : 'accent')} onClick={() => scheduleMutation.mutate({ scheduleId: item.schedule_id, payload: { enabled: !item.enabled } })}>
                  {item.enabled ? 'Disable' : 'Enable'}
                </button>
              </div>
              <div style={{ color: muted, fontSize: 11, marginTop: 10 }}>
                {item.timezone} · last run {formatStamp(item.last_run_at)} · next run {formatStamp(item.next_run_at)}
              </div>
            </div>
          ))}
        </div>
      )}

      {section === 'analytics' && dashboard && (
        <div style={{ display: 'grid', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
            <StatTile label="Research Missions" value={dashboard.analytics.research_volume.missions} tone={accent} />
            <StatTile label="Research Runs" value={dashboard.analytics.research_volume.runs} tone={info} />
            <StatTile label="Sources" value={dashboard.analytics.research_volume.sources} tone={accent} />
            <StatTile label="Candidates" value={dashboard.analytics.research_volume.candidates} tone={warn} />
            <StatTile label="Approvals" value={dashboard.analytics.approval_rate} tone={accent} />
            <StatTile label="Rejections" value={dashboard.analytics.rejection_rate} tone={danger} />
            <StatTile label="Contradictions" value={dashboard.analytics.contradiction_rate} tone={warn} />
            <StatTile label="Avg Review Age (days)" value={dashboard.analytics.average_review_age_days} tone={info} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ ...SURFACE, padding: 14 }}>
              <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>ASTROLOGY COVERAGE</div>
              <div style={{ display: 'grid', gap: 8 }}>
                {coverageRows.map((item: ResearchCoverageRow) => (
                  <div key={item.domain} style={{ borderBottom: `1px solid ${line}`, paddingBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                      <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.domain}</div>
                      <Badge label={item.coverage} color={statusColor(item.coverage)} />
                    </div>
                    <div style={{ color: muted, fontSize: 11 }}>
                      Known rules {item.existing_rules} · source validated {item.source_validated} · under research {item.under_research} · conflicts {item.conflicts}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ ...SURFACE, padding: 14 }}>
              <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>LEGACY PROVENANCE PROGRESS</div>
              <pre style={{ margin: 0, color: muted, fontSize: 11, whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(dashboard.analytics.legacy_rule_provenance_progress, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
