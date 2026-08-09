import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { KnowledgeReviewPanel } from '../components/veda/KnowledgeReviewPanel'

describe('KnowledgeReviewPanel', () => {
  it('shows a duplicate-memory recommendation and lets the user discard or save anyway', () => {
    const onApprove = vi.fn()
    const onDiscard = vi.fn()

    render(
      <KnowledgeReviewPanel
        open
        draft={{
          draft_id: 'draft-1',
          title: 'Research: Banking memory check',
          summary: 'A similar banking memory already exists.',
          facts: ['Banking rotation remains strong.'],
          tags: ['research', 'banking'],
          raw_question: 'Review the same banking topic again.',
          raw_answer: 'Banking rotation and FII support still look strong.',
          intent: 'SECTOR',
          session_id: 'session-1',
          created_at: '2026-08-04T10:00:00Z',
          sources: [],
          existing_matches: [
            {
              doc_id: 'veda_review_existing',
              title: 'Banking rotation and FII support',
              summary: 'Existing saved banking note.',
              saved_at: '2026-08-04T09:00:00Z',
              memory_type: 'reviewed_note',
              overlap_score: 14,
              semantic_score: 89,
              reason: 'This saved memory already overlaps strongly with the new material.',
              exact_duplicate: false,
            },
          ],
          suggested_action: 'discard',
          suggestion_reason: 'A strong saved memory already exists on this same topic.',
          status: 'draft',
        }}
        loading={false}
        submitting={false}
        error={null}
        onClose={() => undefined}
        onApprove={onApprove}
        onDiscard={onDiscard}
      />,
    )

    expect(screen.getByText('Veda found similar saved memory')).toBeInTheDocument()
    expect(screen.getByText('Recommended: discard this draft')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Discard Draft' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save Anyway' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Discard Draft' }))
    expect(onDiscard).toHaveBeenCalledWith('draft-1')

    fireEvent.click(screen.getByRole('button', { name: 'Save Anyway' }))
    expect(onApprove).toHaveBeenCalledWith(expect.objectContaining({ decision: 'save' }))
  })

  it('shows a merge recommendation and submits a merge decision', () => {
    const onApprove = vi.fn()
    const onDiscard = vi.fn()

    render(
      <KnowledgeReviewPanel
        open
        draft={{
          draft_id: 'draft-2',
          title: 'Research: Updated astrology timing notes',
          summary: 'A similar astrology memory exists, but this draft adds Mercury rules.',
          facts: ['Mercury periods can change communication and trading behavior.'],
          tags: ['research', 'astrology'],
          raw_question: 'Study this second astrology book.',
          raw_answer: 'The new draft adds Mercury timing details to an existing astrology topic.',
          intent: 'RESEARCH',
          session_id: 'session-2',
          created_at: '2026-08-04T10:30:00Z',
          sources: [],
          existing_matches: [
            {
              doc_id: 'veda_review_existing_2',
              title: 'Astrology timing rules',
              summary: 'Existing saved astrology note.',
              saved_at: '2026-08-04T08:30:00Z',
              memory_type: 'reviewed_note',
              overlap_score: 9,
              semantic_score: 72,
              reason: 'This saved memory covers the same topic, but the new draft appears to add something useful.',
              exact_duplicate: false,
              new_value_hint: 'Possible new value: mercury, communication, trading.',
            },
          ],
          suggested_action: 'merge',
          suggestion_reason: 'Veda found saved memory on the same topic, but this draft appears to add new value.',
          status: 'draft',
        }}
        loading={false}
        submitting={false}
        error={null}
        onClose={() => undefined}
        onApprove={onApprove}
        onDiscard={onDiscard}
      />,
    )

    expect(screen.getByText('Recommended: merge into saved memory')).toBeInTheDocument()
    expect(screen.getByText('Possible new value: mercury, communication, trading.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Merge And Save' }))
    expect(onApprove).toHaveBeenCalledWith(expect.objectContaining({ decision: 'merge' }))
  })

  it('tells the user that outside research stays temporary until approval', () => {
    render(
      <KnowledgeReviewPanel
        open
        draft={{
          draft_id: 'draft-3',
          title: 'Research: Outside market note',
          summary: 'Outside research found a fresh market note.',
          facts: ['Outside research added one fresh caution point.'],
          tags: ['research', 'market'],
          raw_question: 'Research this market topic.',
          raw_answer: 'Outside research found a fresh market note.',
          intent: 'RESEARCH',
          session_id: 'session-3',
          created_at: '2026-08-04T11:00:00Z',
          sources: [
            {
              kind: 'research',
              title: 'Fresh market note',
              url: 'https://example.com/market-note',
              published_at: '2026-08-04',
              excerpt: 'Fresh outside market note.',
            },
          ],
          existing_matches: [],
          suggested_action: 'save',
          suggestion_reason: null,
          status: 'draft',
        }}
        loading={false}
        submitting={false}
        error={null}
        onClose={() => undefined}
        onApprove={() => undefined}
        onDiscard={() => undefined}
      />,
    )

    expect(
      screen.getByText(/Outside research is still temporary here. It only becomes saved knowledge if you approve this review./i),
    ).toBeInTheDocument()
  })
})
