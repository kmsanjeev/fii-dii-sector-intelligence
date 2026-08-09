import { useEffect, useState, type CSSProperties } from 'react'
import type { ChatKnowledgeDraft } from '../../api/client'

export type KnowledgeReviewPayload = {
  title: string
  summary: string
  facts: string[]
  tags: string[]
  review_note?: string
  decision?: 'save' | 'merge'
}

export function KnowledgeReviewPanel({
  open,
  draft,
  loading,
  submitting,
  error,
  onClose,
  onApprove,
  onDiscard,
}: {
  open: boolean
  draft: ChatKnowledgeDraft | null
  loading: boolean
  submitting: boolean
  error?: string | null
  onClose: () => void
  onApprove: (payload: KnowledgeReviewPayload) => Promise<void> | void
  onDiscard: (draftId: string) => Promise<void> | void
}) {
  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [factsText, setFactsText] = useState('')
  const [tagsText, setTagsText] = useState('')
  const [reviewNote, setReviewNote] = useState('')
  const hasResearchSources = Boolean(draft?.sources.some(source => source.kind === 'research'))
  const hasAttachmentSources = Boolean(draft?.sources.some(source => source.kind === 'attachment'))
  const hasExistingMatches = Boolean(draft?.existing_matches.length)
  const recommendation = draft?.suggested_action || 'save'

  useEffect(() => {
    if (!draft) return
    setTitle(draft.title)
    setSummary(draft.summary)
    setFactsText(draft.facts.join('\n'))
    setTagsText(draft.tags.join(', '))
    setReviewNote('')
  }, [draft])

  if (!open) return null

  const handleApprove = () => {
    const facts = factsText
      .split('\n')
      .map(line => line.trim())
      .filter(Boolean)
    const tags = tagsText
      .split(',')
      .map(tag => tag.trim())
      .filter(Boolean)
    void onApprove({
      title: title.trim(),
      summary: summary.trim(),
      facts,
      tags,
      review_note: reviewNote.trim() || undefined,
      decision: recommendation === 'merge' ? 'merge' : 'save',
    })
  }

  const handleDiscard = () => {
    if (!draft) return
    void onDiscard(draft.draft_id)
  }

  return (
    <>
      <div
        onClick={submitting ? undefined : onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(2, 6, 23, 0.72)',
          zIndex: 1300,
        }}
      />
      <div style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: 'min(760px, calc(100vw - 28px))',
        maxHeight: 'calc(100vh - 40px)',
        overflowY: 'auto',
        background: '#0A0D14',
        border: '1px solid #1E2332',
        borderRadius: 14,
        boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
        zIndex: 1301,
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '14px 16px',
          borderBottom: '1px solid #1E2332',
          background: '#111622',
        }}>
          <div>
            <div style={{ color: '#E2E8F0', fontSize: 15, fontWeight: 700 }}>
              Save To Knowledge
            </div>
            <div style={{ color: '#94A3B8', fontSize: 11, marginTop: 3 }}>
              {hasResearchSources
                ? 'Outside research is still temporary here. It only becomes saved knowledge if you approve this review.'
                : hasAttachmentSources
                ? 'Nothing is saved automatically. Approval saves this reviewed note and any readable attached file text.'
                : 'Nothing is saved automatically. Review and approve first.'}
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={submitting}
            style={{
              background: 'none',
              border: 'none',
              color: '#64748B',
              fontSize: 18,
              cursor: submitting ? 'not-allowed' : 'pointer',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        <div style={{ padding: 16, display: 'grid', gap: 14 }}>
          {loading && !draft && (
            <div style={{ color: '#94A3B8', fontSize: 13 }}>
              Preparing the review draft...
            </div>
          )}

          {!loading && draft && (
            <>
              {hasExistingMatches && (
                <div style={{
                  border: `1px solid ${recommendation === 'discard' ? '#7F1D1D' : recommendation === 'merge' ? '#92400E' : '#1D4ED8'}`,
                  background: recommendation === 'discard' ? '#2A0F16' : recommendation === 'merge' ? '#2A1A0A' : '#0F1E30',
                  borderRadius: 12,
                  padding: '12px 14px',
                  display: 'grid',
                  gap: 10,
                }}>
                  <div>
                    <div style={{ color: '#E2E8F0', fontSize: 12, fontWeight: 700 }}>
                      Veda found similar saved memory
                    </div>
                    <div style={{ color: '#CBD5E1', fontSize: 11, marginTop: 4, lineHeight: 1.55 }}>
                      {draft.suggestion_reason || 'Review the related saved memory before deciding whether to save this again.'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    <div style={{
                      fontSize: 10,
                      color: recommendation === 'discard' ? '#FCA5A5' : recommendation === 'merge' ? '#FCD34D' : '#93C5FD',
                      border: `1px solid ${recommendation === 'discard' ? '#7F1D1D' : recommendation === 'merge' ? '#92400E' : '#1D4ED8'}`,
                      background: '#0D1117',
                      borderRadius: 999,
                      padding: '3px 8px',
                    }}>
                      Recommended: {recommendation === 'discard'
                        ? 'discard this draft'
                        : recommendation === 'merge'
                          ? 'merge into saved memory'
                          : 'save as a separate memory only if it adds value'}
                    </div>
                    <div style={{
                      fontSize: 10,
                      color: '#94A3B8',
                      border: '1px solid #334155',
                      background: '#0D1117',
                      borderRadius: 999,
                      padding: '3px 8px',
                    }}>
                      Matches: {draft.existing_matches.length}
                    </div>
                  </div>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {draft.existing_matches.map(match => (
                      <div
                        key={match.doc_id}
                        style={{
                          border: '1px solid #1E2332',
                          background: '#0D1117',
                          borderRadius: 10,
                          padding: '10px 12px',
                        }}
                      >
                        <div style={{ color: '#E2E8F0', fontSize: 11, fontWeight: 700 }}>
                          {match.title}
                        </div>
                        <div style={{ color: '#64748B', fontSize: 10, marginTop: 3 }}>
                          {match.memory_type === 'attachment_chunk' ? 'attachment memory' : 'reviewed note'}
                          {match.saved_at ? ` | saved ${match.saved_at}` : ''}
                          {` | overlap score ${match.overlap_score}`}
                          {match.semantic_score ? ` | similarity ${match.semantic_score}%` : ''}
                        </div>
                        {match.summary && (
                          <div style={{ color: '#94A3B8', fontSize: 10, lineHeight: 1.5, marginTop: 5 }}>
                            {match.summary}
                          </div>
                        )}
                        {match.reason && (
                          <div style={{ color: match.exact_duplicate ? '#FCA5A5' : '#CBD5E1', fontSize: 10, lineHeight: 1.5, marginTop: 5 }}>
                            {match.reason}
                          </div>
                        )}
                        {match.new_value_hint && (
                          <div style={{ color: '#FCD34D', fontSize: 10, lineHeight: 1.5, marginTop: 5 }}>
                            {match.new_value_hint}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>Title</label>
                <input
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  style={fieldStyle}
                />
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>Summary</label>
                <textarea
                  value={summary}
                  onChange={e => setSummary(e.target.value)}
                  rows={5}
                  style={{ ...fieldStyle, resize: 'vertical', minHeight: 120 }}
                />
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>Facts</label>
                <textarea
                  value={factsText}
                  onChange={e => setFactsText(e.target.value)}
                  rows={6}
                  style={{ ...fieldStyle, resize: 'vertical', minHeight: 150 }}
                />
                <div style={{ color: '#64748B', fontSize: 10 }}>
                  One fact per line.
                </div>
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>Tags</label>
                <input
                  value={tagsText}
                  onChange={e => setTagsText(e.target.value)}
                  style={fieldStyle}
                />
                <div style={{ color: '#64748B', fontSize: 10 }}>
                  Separate tags with commas.
                </div>
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>Review Note</label>
                <textarea
                  value={reviewNote}
                  onChange={e => setReviewNote(e.target.value)}
                  rows={3}
                  style={{ ...fieldStyle, resize: 'vertical', minHeight: 90 }}
                  placeholder="Optional: why this should be saved"
                />
              </div>

              <div style={{ display: 'grid', gap: 8 }}>
                <div style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>Trace Sources</div>
                <div style={{ display: 'grid', gap: 8 }}>
                  {draft.sources.length === 0 && (
                    <div style={{ color: '#64748B', fontSize: 11 }}>
                      No outside file or web source was attached to this save.
                    </div>
                  )}
                  {draft.sources.map((source, index) => (
                    <div
                      key={`${source.kind}-${source.title}-${index}`}
                      style={{
                        border: '1px solid #1E2332',
                        background: '#0D1117',
                        borderRadius: 10,
                        padding: '10px 12px',
                      }}
                    >
                      <div style={{ color: '#E2E8F0', fontSize: 11, fontWeight: 700 }}>
                        {source.title}
                      </div>
                      <div style={{ color: '#64748B', fontSize: 10, marginTop: 3 }}>
                        {source.kind}{source.published_at ? ` | ${source.published_at}` : ''}{source.storage_key ? ` | ${source.storage_key}` : ''}
                      </div>
                      {source.url && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: '#60A5FA', fontSize: 10, textDecoration: 'none', display: 'block', marginTop: 5 }}
                        >
                          {source.url}
                        </a>
                      )}
                      {(source.excerpt || source.warning) && (
                        <div style={{ color: source.warning ? '#FCD34D' : '#94A3B8', fontSize: 10, lineHeight: 1.5, marginTop: 5 }}>
                          {source.warning || source.excerpt}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {error && (
            <div style={{
              color: '#FCA5A5',
              background: '#2A0F16',
              border: '1px solid #7F1D1D',
              borderRadius: 10,
              padding: '10px 12px',
              fontSize: 11,
            }}>
              {error}
            </div>
          )}
        </div>

        <div style={{
          padding: 16,
          borderTop: '1px solid #1E2332',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 10,
          background: '#0B0F18',
        }}>
          <button
            onClick={hasExistingMatches ? handleDiscard : onClose}
            disabled={submitting}
            style={hasExistingMatches ? discardButtonStyle : secondaryButtonStyle}
          >
            {hasExistingMatches ? 'Discard Draft' : 'Cancel'}
          </button>
          <button
            onClick={handleApprove}
            disabled={loading || submitting || !draft}
            style={recommendation === 'discard' ? secondaryButtonStyle : primaryButtonStyle}
          >
            {submitting
              ? 'Working...'
              : recommendation === 'discard'
                ? 'Save Anyway'
                : recommendation === 'merge'
                  ? 'Merge And Save'
                : 'Approve And Save'}
          </button>
        </div>
      </div>
    </>
  )
}

const fieldStyle: CSSProperties = {
  width: '100%',
  background: '#0D1117',
  border: '1px solid #1E2332',
  borderRadius: 10,
  color: '#E2E8F0',
  padding: '10px 12px',
  fontSize: 12,
  outline: 'none',
  fontFamily: 'inherit',
  lineHeight: 1.5,
}

const primaryButtonStyle: CSSProperties = {
  background: '#16314F',
  border: '1px solid #3B82F6',
  color: '#93C5FD',
  borderRadius: 10,
  padding: '10px 14px',
  fontSize: 12,
  fontWeight: 700,
  cursor: 'pointer',
}

const secondaryButtonStyle: CSSProperties = {
  background: 'transparent',
  border: '1px solid #334155',
  color: '#94A3B8',
  borderRadius: 10,
  padding: '10px 14px',
  fontSize: 12,
  fontWeight: 700,
  cursor: 'pointer',
}

const discardButtonStyle: CSSProperties = {
  background: '#2A0F16',
  border: '1px solid #7F1D1D',
  color: '#FCA5A5',
  borderRadius: 10,
  padding: '10px 14px',
  fontSize: 12,
  fontWeight: 700,
  cursor: 'pointer',
}
