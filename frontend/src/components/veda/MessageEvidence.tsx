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
  if (!msg.intent && !msg.research) return null

  const research = msg.research
  const attachments = previous.attachments ?? []
  const attachmentCount = attachments.length
  const attachmentWarnings = attachments.some(attachment => Boolean(attachment.warning))
  const researchUsed = Boolean(research?.used)
  const researchRequested = Boolean(research?.requested)
  const researchError = Boolean(research?.error)
  const sourceCount = research?.source_count ?? 0

  let basisLabel = 'Basis: local platform only'
  if (researchUsed && attachmentCount > 0) {
    basisLabel = 'Basis: local data + outside sources + your files'
  } else if (researchUsed) {
    basisLabel = 'Basis: local data + outside sources'
  } else if (attachmentCount > 0) {
    basisLabel = 'Basis: local data + your files'
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
  if (attachmentWarnings) {
    note += ' Some file extraction was partial, so details may need manual checking.'
  }
  if (research?.cached && researchUsed) {
    note += ' The outside lookup came from cache.'
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
      <ResearchSources msg={msg} compact={compact} />
    </div>
  )
}
