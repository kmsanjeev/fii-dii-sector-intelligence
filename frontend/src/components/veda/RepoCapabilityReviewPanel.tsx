import { useEffect, useState, type CSSProperties } from 'react'
import type { ChatRepoCapabilityDraft } from '../../api/client'

export type RepoCapabilityScanPayload = {
  repo_path: string
  repo_label?: string
  focus?: string
}

export type RepoCapabilityApprovePayload = {
  title: string
  summary: string
  facts: string[]
  tags: string[]
  review_note?: string
}

export function RepoCapabilityReviewPanel({
  open,
  draft,
  loading,
  submitting,
  error,
  onClose,
  onScan,
  onApprove,
}: {
  open: boolean
  draft: ChatRepoCapabilityDraft | null
  loading: boolean
  submitting: boolean
  error?: string | null
  onClose: () => void
  onScan: (payload: RepoCapabilityScanPayload) => Promise<void> | void
  onApprove: (payload: RepoCapabilityApprovePayload) => Promise<void> | void
}) {
  const [repoPath, setRepoPath] = useState('')
  const [repoLabel, setRepoLabel] = useState('')
  const [focus, setFocus] = useState('')
  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [factsText, setFactsText] = useState('')
  const [tagsText, setTagsText] = useState('')
  const [reviewNote, setReviewNote] = useState('')

  useEffect(() => {
    if (!draft) return
    setRepoPath(draft.repo_path)
    setRepoLabel(draft.repo_label)
    setFocus(draft.focus ?? '')
    setTitle(draft.title)
    setSummary(draft.summary)
    setFactsText(draft.facts.join('\n'))
    setTagsText(draft.tags.join(', '))
    setReviewNote('')
  }, [draft])

  if (!open) return null

  const handleScan = () => {
    const payload: RepoCapabilityScanPayload = {
      repo_path: repoPath.trim(),
    }
    if (repoLabel.trim()) payload.repo_label = repoLabel.trim()
    if (focus.trim()) payload.focus = focus.trim()
    void onScan(payload)
  }

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
    })
  }

  return (
    <>
      <div
        onClick={submitting ? undefined : onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(2, 6, 23, 0.72)',
          zIndex: 1320,
        }}
      />
      <div style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: 'min(820px, calc(100vw - 28px))',
        maxHeight: 'calc(100vh - 36px)',
        overflowY: 'auto',
        background: '#0A0D14',
        border: '1px solid #1E2332',
        borderRadius: 14,
        boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
        zIndex: 1321,
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
              Study MIT Repo
            </div>
            <div style={{ color: '#94A3B8', fontSize: 11, marginTop: 3 }}>
              Works with a local cloned repo path in this runtime. Nothing becomes Veda memory without approval.
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
            x
          </button>
        </div>

        <div style={{ padding: 16, display: 'grid', gap: 14 }}>
          <div style={calloutStyle}>
            Veda treats repo files as content only. This step extracts reusable ideas from MIT-licensed repos and keeps the license path visible.
          </div>

          <div style={{ display: 'grid', gap: 10 }}>
            <div style={{ display: 'grid', gap: 6 }}>
              <label style={labelStyle}>Local Repo Path</label>
              <input
                value={repoPath}
                onChange={e => setRepoPath(e.target.value)}
                placeholder="D:\\Repos\\some-mit-project"
                style={fieldStyle}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div style={{ display: 'grid', gap: 6 }}>
                <label style={labelStyle}>Repo Label</label>
                <input
                  value={repoLabel}
                  onChange={e => setRepoLabel(e.target.value)}
                  placeholder="Optional short name"
                  style={fieldStyle}
                />
              </div>
              <div style={{ display: 'grid', gap: 6 }}>
                <label style={labelStyle}>Focus</label>
                <input
                  value={focus}
                  onChange={e => setFocus(e.target.value)}
                  placeholder="Optional: prompts, tools, MCP, memory..."
                  style={fieldStyle}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={handleScan}
                disabled={loading || submitting || !repoPath.trim()}
                style={primaryButtonStyle}
              >
                {loading ? 'Scanning Repo...' : 'Scan Repo'}
              </button>
            </div>
          </div>

          {loading && !draft && (
            <div style={{ color: '#94A3B8', fontSize: 13 }}>
              Veda is checking the MIT license and reading the most useful repo files...
            </div>
          )}

          {!loading && draft && (
            <>
              <div style={sectionCardStyle}>
                <div style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>License Check</div>
                <div style={{ color: '#E2E8F0', fontSize: 12, marginTop: 7 }}>
                  {draft.license_name} license found at <span style={{ color: '#93C5FD' }}>{draft.license_path}</span>
                </div>
                <div style={{ color: '#94A3B8', fontSize: 11, lineHeight: 1.55, marginTop: 7 }}>
                  {draft.license_excerpt}
                </div>
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={labelStyle}>Title</label>
                <input
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  style={fieldStyle}
                />
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={labelStyle}>Summary</label>
                <textarea
                  value={summary}
                  onChange={e => setSummary(e.target.value)}
                  rows={5}
                  style={{ ...fieldStyle, resize: 'vertical', minHeight: 120 }}
                />
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={labelStyle}>Facts</label>
                <textarea
                  value={factsText}
                  onChange={e => setFactsText(e.target.value)}
                  rows={6}
                  style={{ ...fieldStyle, resize: 'vertical', minHeight: 150 }}
                />
                <div style={{ color: '#64748B', fontSize: 10 }}>One fact per line.</div>
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={labelStyle}>Tags</label>
                <input
                  value={tagsText}
                  onChange={e => setTagsText(e.target.value)}
                  style={fieldStyle}
                />
                <div style={{ color: '#64748B', fontSize: 10 }}>Separate tags with commas.</div>
              </div>

              <div style={{ display: 'grid', gap: 6 }}>
                <label style={labelStyle}>Review Note</label>
                <textarea
                  value={reviewNote}
                  onChange={e => setReviewNote(e.target.value)}
                  rows={3}
                  style={{ ...fieldStyle, resize: 'vertical', minHeight: 90 }}
                  placeholder="Optional: what should Veda reuse from this repo?"
                />
              </div>

              <div style={sectionCardStyle}>
                <div style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>
                  Candidate Files
                </div>
                <div style={{ display: 'grid', gap: 6 }}>
                  {draft.candidate_files.map(file => (
                    <div
                      key={file}
                      style={{
                        border: '1px solid #1E2332',
                        background: '#0D1117',
                        borderRadius: 9,
                        padding: '8px 10px',
                        color: '#94A3B8',
                        fontSize: 11,
                        fontFamily: 'Consolas, monospace',
                      }}
                    >
                      {file}
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gap: 8 }}>
                <div style={{ color: '#CBD5E1', fontSize: 11, fontWeight: 700 }}>Trace Sources</div>
                <div style={{ display: 'grid', gap: 8 }}>
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
                        {source.kind}{source.storage_key ? ` | ${source.storage_key}` : ''}
                      </div>
                      {(source.excerpt || source.warning) && (
                        <div style={{ color: source.warning ? '#FCD34D' : '#94A3B8', fontSize: 10, lineHeight: 1.55, marginTop: 5 }}>
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
            onClick={onClose}
            disabled={submitting}
            style={secondaryButtonStyle}
          >
            Close
          </button>
          <button
            onClick={handleApprove}
            disabled={loading || submitting || !draft}
            style={primaryButtonStyle}
          >
            {submitting ? 'Saving...' : 'Approve And Save'}
          </button>
        </div>
      </div>
    </>
  )
}

const labelStyle: CSSProperties = {
  color: '#CBD5E1',
  fontSize: 11,
  fontWeight: 700,
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

const calloutStyle: CSSProperties = {
  color: '#BFDBFE',
  background: '#122033',
  border: '1px solid #1D4ED8',
  borderRadius: 10,
  padding: '10px 12px',
  fontSize: 11,
  lineHeight: 1.55,
}

const sectionCardStyle: CSSProperties = {
  border: '1px solid #1E2332',
  background: '#0B111B',
  borderRadius: 12,
  padding: 12,
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
