import type { Msg } from '../../store/vedaStore'

type EvidenceSummary = {
  basisLabel: string
  confidenceLabel: 'High confidence' | 'Medium confidence' | 'Low confidence'
  confidenceColor: string
  confidenceBorder: string
  note: string
  researchLabel: string | null
  attachmentLabel: string | null
}

function pluralize(count: number, singular: string, plural: string) {
  return `${count} ${count === 1 ? singular : plural}`
}

function deriveEvidence(msg: Msg, previous?: Msg | null): EvidenceSummary | null {
  if (msg.role !== 'assistant') return null
  if (!previous || previous.role !== 'user') return null
  if (!msg.intent && !msg.research && !msg.localEvidence) return null

  const research = msg.research
  const attachments = previous.attachments ?? []
  const attachmentCount = attachments.length
  const attachmentWarnings = attachments.some(attachment => Boolean(attachment.warning))
  const researchUsed = Boolean(research?.used)
  const researchRequested = Boolean(research?.requested)
  const researchError = Boolean(research?.error)
  const sourceCount = research?.source_count ?? 0
  const localEvidence = msg.localEvidence
  const predictiveMlCount = localEvidence?.predictive_ml_count ?? 0
  const approvedMemoryCount = localEvidence?.approved_memory_count ?? 0
  const attachmentMemoryCount = localEvidence?.attachment_memory_count ?? 0
  const repoCount = localEvidence?.repo_count ?? 0
  const localTopDate = localEvidence?.top_date ?? null

  let basisLabel = 'Basis: local platform only'
  if (researchUsed && attachmentCount > 0) {
    basisLabel = 'Basis: local data + outside sources + your files'
  } else if (researchUsed) {
    basisLabel = 'Basis: local data + outside sources'
  } else if (attachmentCount > 0) {
    basisLabel = 'Basis: local data + your files'
  } else if (predictiveMlCount > 0 && (approvedMemoryCount > 0 || attachmentMemoryCount > 0)) {
    basisLabel = 'Basis: local ML signals + approved memory'
  } else if (predictiveMlCount > 0) {
    basisLabel = 'Basis: local ML signals + platform data'
  } else if (approvedMemoryCount > 0 || attachmentMemoryCount > 0) {
    basisLabel = 'Basis: local platform data + approved memory'
  } else if (repoCount > 0) {
    basisLabel = 'Basis: local platform data + MIT notes'
  }

  let confidenceLabel: EvidenceSummary['confidenceLabel'] = 'High confidence'
  if (researchError) {
    confidenceLabel = 'Low confidence'
  } else if ((researchUsed && sourceCount <= 1) || attachmentCount > 0 || attachmentWarnings) {
    confidenceLabel = 'Medium confidence'
  }

  const confidenceColor = confidenceLabel === 'High confidence'
    ? '#22C55E'
    : confidenceLabel === 'Medium confidence'
      ? '#F59E0B'
      : '#EF4444'
  const confidenceBorder = confidenceLabel === 'High confidence'
    ? '#22C55E33'
    : confidenceLabel === 'Medium confidence'
      ? '#F59E0B44'
      : '#EF444444'

  let note = 'Veda answered from the platform intelligence already available in the app.'
  if (researchError && attachmentCount > 0) {
    note = 'Outside lookup was requested but unavailable, so Veda fell back to local data and your uploaded files.'
  } else if (researchError) {
    note = 'Outside lookup was requested but unavailable, so Veda fell back to local platform data.'
  } else if (researchUsed && attachmentCount > 0) {
    note = 'Veda combined local platform data, outside sources, and your uploaded files for this answer.'
  } else if (researchUsed) {
    note = 'Veda combined local platform data with outside sources for this answer.'
  } else if (attachmentCount > 0) {
    note = 'Veda used your uploaded files together with local platform data for this answer.'
  }
  const localNotes: string[] = []
  if (predictiveMlCount > 0) {
    localNotes.push('Local predictive ML signals were used as scored evidence, not guaranteed fact.')
  }
  if (approvedMemoryCount > 0 || attachmentMemoryCount > 0) {
    localNotes.push('Approved memory also contributed supporting context.')
  }
  if (repoCount > 0) {
    localNotes.push('Approved MIT capability notes also contributed reusable implementation context.')
  }
  if (localTopDate && predictiveMlCount > 0) {
    localNotes.push(`Main local signal date: ${localTopDate}.`)
  }
  if (attachmentWarnings) {
    note += ' Some file extraction was partial, so details may need manual checking.'
  }
  if (research?.cached && researchUsed) {
    note += ' The outside lookup came from cache.'
  }
  if (localNotes.length) {
    note += ` ${localNotes.join(' ')}`
  }

  const researchLabel = researchUsed
    ? `Research: ${research?.provider || 'outside'}${sourceCount ? `, ${pluralize(sourceCount, 'source', 'sources')}` : ''}${research?.cached ? ', cache' : ''}`
    : researchRequested && researchError
      ? 'Research fallback'
      : researchRequested
        ? 'Research checked'
        : null

  const attachmentLabel = attachmentCount > 0
    ? `Files: ${pluralize(attachmentCount, 'attachment', 'attachments')}`
    : null

  return {
    basisLabel,
    confidenceLabel,
    confidenceColor,
    confidenceBorder,
    note,
    researchLabel,
    attachmentLabel,
  }
}

function formatLocalSourceMeta(source: NonNullable<Msg['localEvidence']>['sources'][number]) {
  const parts = [
    source.source_label,
    source.evidence_label,
    source.domain,
  ]
  if (source.date) parts.push(source.date)
  return parts.join(' | ')
}

function renderLocalSourceDetails(source: NonNullable<Msg['localEvidence']>['sources'][number]) {
  const details = [
    source.model_name
      ? `Model: ${source.model_version ? `${source.model_name}@${source.model_version}` : source.model_name}`
      : null,
    source.repo_label ? `Repo: ${source.repo_label}` : null,
    source.license_name ? `License: ${source.license_name}` : null,
    source.confidence !== undefined && source.confidence !== null ? `Confidence: ${source.confidence.toFixed(2)}` : null,
  ].filter(Boolean)
  return details.join(' | ')
}

function LocalEvidenceNotes({
  msg,
  compact,
}: {
  msg: Msg
  compact?: boolean
}) {
  const conflictNote = msg.localEvidence?.conflict_note
  const freshnessNote = msg.localEvidence?.freshness_note
  if (!conflictNote && !freshnessNote) return null

  return (
    <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
      {conflictNote && (
        <div style={{
          border: '1px solid #F59E0B44',
          background: '#1A1200',
          borderRadius: 8,
          padding: compact ? '6px 8px' : '8px 10px',
        }}>
          <div style={{ color: '#FBBF24', fontSize: compact ? 8 : 9, fontWeight: 700 }}>
            Local conflict note
          </div>
          <div style={{ color: '#FDE68A', fontSize: compact ? 9 : 10, marginTop: 4, lineHeight: 1.5 }}>
            {conflictNote}
          </div>
        </div>
      )}
      {freshnessNote && (
        <div style={{
          border: '1px solid #3B82F644',
          background: '#0B1220',
          borderRadius: 8,
          padding: compact ? '6px 8px' : '8px 10px',
        }}>
          <div style={{ color: '#93C5FD', fontSize: compact ? 8 : 9, fontWeight: 700 }}>
            Freshness note
          </div>
          <div style={{ color: '#BFDBFE', fontSize: compact ? 9 : 10, marginTop: 4, lineHeight: 1.5 }}>
            {freshnessNote}
          </div>
        </div>
      )}
    </div>
  )
}

function LocalEvidenceSources({
  msg,
  compact,
}: {
  msg: Msg
  compact?: boolean
}) {
  const sources = msg.localEvidence?.sources ?? []
  if (!sources.length) return null

  return (
    <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
      {sources.map((source, index) => {
        const detailLine = renderLocalSourceDetails(source)
        return (
          <div
            key={`${source.source_id}-${index}`}
            style={{
              border: '1px solid #1E2332',
              background: '#0D1117',
              borderRadius: 8,
              padding: compact ? '7px 8px' : '8px 10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'baseline' }}>
              <div style={{ color: '#E2E8F0', fontSize: compact ? 10 : 11, fontWeight: 700, lineHeight: 1.4 }}>
                {source.title}
              </div>
              {source.rank > 0 && (
                <div style={{ color: '#475569', fontSize: compact ? 8 : 9 }}>
                  #{source.rank}
                </div>
              )}
            </div>
            <div style={{ color: '#64748B', fontSize: compact ? 8 : 9, marginTop: 3, lineHeight: 1.5 }}>
              {formatLocalSourceMeta(source)}
            </div>
            {source.summary && (
              <div style={{ color: '#94A3B8', fontSize: compact ? 9 : 10, marginTop: 5, lineHeight: 1.5 }}>
                {source.summary}
              </div>
            )}
            {detailLine && (
              <div style={{ color: '#60A5FA', fontSize: compact ? 8 : 9, marginTop: 5, lineHeight: 1.5 }}>
                {detailLine}
              </div>
            )}
            {source.score_meaning && (
              <div style={{ color: '#C4B5FD', fontSize: compact ? 8 : 9, marginTop: 5, lineHeight: 1.5 }}>
                Meaning: {source.score_meaning}
              </div>
            )}
            {source.reliability_note && (
              <div style={{ color: '#FBBF24', fontSize: compact ? 8 : 9, marginTop: 5, lineHeight: 1.5 }}>
                Reliability: {source.reliability_note}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function ResearchGovernanceNotes({
  msg,
  compact,
}: {
  msg: Msg
  compact?: boolean
}) {
  const research = msg.research
  const governanceNote = research?.used ? research.governance_note : null
  const conflictNote = research?.used ? research.conflict_note : null
  if (!governanceNote && !conflictNote) return null

  return (
    <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
      {governanceNote && (
        <div style={{
          border: '1px solid #334155',
          background: '#0D1117',
          borderRadius: 8,
          padding: compact ? '6px 8px' : '8px 10px',
        }}>
          <div style={{ color: '#CBD5E1', fontSize: compact ? 8 : 9, fontWeight: 700 }}>
            Research note
          </div>
          <div style={{ color: '#94A3B8', fontSize: compact ? 9 : 10, marginTop: 4, lineHeight: 1.5 }}>
            {governanceNote}
          </div>
        </div>
      )}
      {conflictNote && (
        <div style={{
          border: '1px solid #F59E0B44',
          background: '#1A1200',
          borderRadius: 8,
          padding: compact ? '6px 8px' : '8px 10px',
        }}>
          <div style={{ color: '#FBBF24', fontSize: compact ? 8 : 9, fontWeight: 700 }}>
            Research vs saved memory
          </div>
          <div style={{ color: '#FDE68A', fontSize: compact ? 9 : 10, marginTop: 4, lineHeight: 1.5 }}>
            {conflictNote}
          </div>
        </div>
      )}
    </div>
  )
}

function ResearchSources({
  msg,
  compact,
}: {
  msg: Msg
  compact?: boolean
}) {
  const sources = msg.research?.used ? (msg.research.sources ?? []) : []
  if (!sources.length) return null

  if (compact) {
    return (
      <div style={{ marginTop: 7, fontSize: 9, color: '#94A3B8', lineHeight: 1.5 }}>
        Sources:{' '}
        {sources.map((source, index) => (
          <span key={`${source.url}-${index}`}>
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              style={{ color: '#60A5FA', textDecoration: 'none' }}
              title={source.title}
            >
              {source.source || source.title}
            </a>
            {source.published_at ? ` (${source.published_at})` : ''}
            {index < sources.length - 1 ? ', ' : ''}
          </span>
        ))}
      </div>
    )
  }

  return (
    <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
      {sources.map((source, index) => (
        <a
          key={`${source.url}-${index}`}
          href={source.url}
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'block',
            textDecoration: 'none',
            border: '1px solid #1E2332',
            background: '#0D1117',
            borderRadius: 8,
            padding: '8px 10px',
          }}
          title={source.url}
        >
          <div style={{ color: '#60A5FA', fontSize: 11, fontWeight: 700, lineHeight: 1.4 }}>
            {source.title}
          </div>
          <div style={{ color: '#64748B', fontSize: 9, marginTop: 2 }}>
            {(source.source || 'Outside source')}{source.published_at ? ` | ${source.published_at}` : ''}
          </div>
          {source.snippet && (
            <div style={{ color: '#94A3B8', fontSize: 10, marginTop: 5, lineHeight: 1.5 }}>
              {source.snippet}
            </div>
          )}
        </a>
      ))}
    </div>
  )
}

export function MessageEvidence({
  msg,
  previous,
  compact = false,
}: {
  msg: Msg
  previous?: Msg | null
  compact?: boolean
}) {
  const summary = deriveEvidence(msg, previous)
  if (!summary) return null

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {msg.knowledge?.status === 'approved' && (
          <div style={{
            fontSize: compact ? 8 : 9,
            color: '#4ADE80',
            border: '1px solid #22C55E44',
            background: '#0D1117',
            borderRadius: 999,
            padding: compact ? '2px 6px' : '3px 8px',
          }}>
            Saved to knowledge
          </div>
        )}
        {(msg.knowledge?.attachment_doc_count ?? 0) > 0 && (
          <div style={{
            fontSize: compact ? 8 : 9,
            color: '#BFDBFE',
            border: '1px solid #3B82F644',
            background: '#0D1117',
            borderRadius: 999,
            padding: compact ? '2px 6px' : '3px 8px',
          }}>
            Document memory added
          </div>
        )}
        <div style={{
          fontSize: compact ? 8 : 9,
          color: '#60A5FA',
          border: '1px solid #3B82F644',
          background: '#0D1117',
          borderRadius: 999,
          padding: compact ? '2px 6px' : '3px 8px',
        }}>
          {summary.basisLabel}
        </div>
        <div style={{
          fontSize: compact ? 8 : 9,
          color: summary.confidenceColor,
          border: `1px solid ${summary.confidenceBorder}`,
          background: '#0D1117',
          borderRadius: 999,
          padding: compact ? '2px 6px' : '3px 8px',
        }}>
          {summary.confidenceLabel}
        </div>
        {summary.researchLabel && (
          <div style={{
            fontSize: compact ? 8 : 9,
            color: '#94A3B8',
            border: '1px solid #334155',
            background: '#0D1117',
            borderRadius: 999,
            padding: compact ? '2px 6px' : '3px 8px',
          }}>
            {summary.researchLabel}
          </div>
        )}
        {(msg.localEvidence?.predictive_ml_count ?? 0) > 0 && (
          <div style={{
            fontSize: compact ? 8 : 9,
            color: '#C4B5FD',
            border: '1px solid #8B5CF644',
            background: '#0D1117',
            borderRadius: 999,
            padding: compact ? '2px 6px' : '3px 8px',
          }}>
            Local ML signals
          </div>
        )}
        {((msg.localEvidence?.approved_memory_count ?? 0) + (msg.localEvidence?.attachment_memory_count ?? 0)) > 0 && (
          <div style={{
            fontSize: compact ? 8 : 9,
            color: '#BFDBFE',
            border: '1px solid #3B82F644',
            background: '#0D1117',
            borderRadius: 999,
            padding: compact ? '2px 6px' : '3px 8px',
          }}>
            Approved memory
          </div>
        )}
        {summary.attachmentLabel && (
          <div style={{
            fontSize: compact ? 8 : 9,
            color: '#94A3B8',
            border: '1px solid #334155',
            background: '#0D1117',
            borderRadius: 999,
            padding: compact ? '2px 6px' : '3px 8px',
          }}>
            {summary.attachmentLabel}
          </div>
        )}
      </div>
      <div style={{ marginTop: 6, fontSize: compact ? 9 : 10, color: '#94A3B8', lineHeight: 1.5 }}>
        {summary.note}
      </div>
      <LocalEvidenceNotes msg={msg} compact={compact} />
      <LocalEvidenceSources msg={msg} compact={compact} />
      <ResearchGovernanceNotes msg={msg} compact={compact} />
      <ResearchSources msg={msg} compact={compact} />
    </div>
  )
}
