import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MessageEvidence } from '../components/veda/MessageEvidence'

describe('MessageEvidence', () => {
  it('shows the research fallback note when outside lookup is unavailable', () => {
    render(
      <MessageEvidence
        previous={{
          role: 'user',
          content: 'Research this for me',
          ts: 1,
        }}
        msg={{
          role: 'assistant',
          content: 'Here is the local fallback answer.',
          ts: 2,
          research: {
            requested: true,
            used: false,
            provider: 'ddgs',
            reason: 'research_mode',
            source_count: 0,
            cached: false,
            error: 'provider_unavailable',
            sources: [],
          },
        }}
      />,
    )

    expect(screen.getByText('Research fallback')).toBeInTheDocument()
    expect(
      screen.getByText('Outside lookup was requested but unavailable, so Veda fell back to local platform data.'),
    ).toBeInTheDocument()
  })

  it('shows the document-memory badge after an approved attachment save', () => {
    render(
      <MessageEvidence
        previous={{
          role: 'user',
          content: 'Study this file and remember it',
          ts: 1,
          attachments: [
            {
              name: 'astro-book.txt',
              mime_type: 'text/plain',
              storage_key: 'astro-book.txt',
            },
          ],
        }}
        msg={{
          role: 'assistant',
          content: 'I studied the uploaded file and saved it after review.',
          ts: 2,
          intent: 'RESEARCH',
          knowledge: {
            draft_id: 'draft-1',
            doc_id: 'doc-1',
            saved_at: '2026-08-04T16:00:00Z',
            title: 'Astrology timing notes',
            status: 'approved',
            attachment_doc_count: 1,
            attachment_chunk_count: 2,
          },
        }}
      />,
    )

    expect(screen.getByText('Saved to knowledge')).toBeInTheDocument()
    expect(screen.getByText('Document memory added')).toBeInTheDocument()
  })

  it('shows research governance notes when outside research is temporary and conflicts with saved memory', () => {
    render(
      <MessageEvidence
        previous={{
          role: 'user',
          content: 'Research this topic for me',
          ts: 1,
        }}
        msg={{
          role: 'assistant',
          content: 'Here is the outside view with a saved-memory caution.',
          ts: 2,
          intent: 'RESEARCH',
          research: {
            requested: true,
            used: true,
            provider: 'ddgs',
            reason: 'explicit_research_mode',
            source_count: 1,
            cached: false,
            error: null,
            temporary: true,
            save_requires_review: true,
            conflict_note: 'Outside research looks more cautious than the saved memory already stored in Veda.',
            governance_note: 'Outside research stays temporary unless you explicitly save it through review.',
            sources: [
              {
                title: 'Fresh caution note',
                url: 'https://example.com/caution',
                snippet: 'Outside report looks more cautious than the older saved note.',
                source: 'Example News',
                published_at: '2026-08-04',
                kind: 'text',
              },
            ],
          },
        }}
      />,
    )

    expect(screen.getByText('Research note')).toBeInTheDocument()
    expect(screen.getByText(/temporary unless you explicitly save it through review/i)).toBeInTheDocument()
    expect(screen.getByText('Research vs saved memory')).toBeInTheDocument()
    expect(screen.getByText(/more cautious than the saved memory/i)).toBeInTheDocument()
  })

  it('shows when local predictive ML signals were part of the answer basis', () => {
    render(
      <MessageEvidence
        previous={{
          role: 'user',
          content: 'What is the local stock setup?',
          ts: 1,
        }}
        msg={{
          role: 'assistant',
          content: 'ETHOSLTD still scores well on local signals.',
          ts: 2,
          intent: 'STOCK',
          localEvidence: {
            used: true,
            source_count: 2,
            evidence_kinds: ['predictive_ml_signal', 'platform_signal_snapshot'],
            predictive_ml_count: 1,
            platform_snapshot_count: 1,
            approved_memory_count: 0,
            attachment_memory_count: 0,
            repo_count: 0,
            top_date: '2026-08-04',
            sources: [
              {
                source_id: 'stock_ethosltd',
                source_type: 'platform_intelligence',
                source_label: 'platform intelligence',
                evidence_kind: 'predictive_ml_signal',
                evidence_label: 'predictive ML signal',
                domain: 'STOCK',
                title: 'ETHOSLTD',
                entity: 'ETHOSLTD',
                date: '2026-08-04',
                freshness_class: 'dated_snapshot',
                confidence: 0.88,
                summary: 'ETHOSLTD still looks strong on local scored signals.',
                model_name: 'bull_run_score_pipeline',
                model_version: '2026-08-04',
                score_meaning: 'Higher model scores indicate a stronger local bullish continuation signal.',
                reliability_note: 'Treat this as predictive scored evidence, not guaranteed fact.',
                rank: 1,
              },
            ],
            conflict_note: null,
            freshness_note: 'This answer mixes current local platform signals with saved memory. Treat saved memory as background context, and use the dated platform signal for the latest market state.',
          },
        }}
      />,
    )

    expect(screen.getByText('Local ML signals')).toBeInTheDocument()
    expect(screen.getByText('Basis: local ML signals + platform data')).toBeInTheDocument()
    expect(screen.getAllByText(/scored evidence, not guaranteed fact/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Main local signal date: 2026-08-04/i)).toBeInTheDocument()
    expect(screen.getByText('ETHOSLTD')).toBeInTheDocument()
    expect(screen.getByText(/platform intelligence \| predictive ML signal \| STOCK \| 2026-08-04/i)).toBeInTheDocument()
    expect(screen.getByText(/Freshness note/i)).toBeInTheDocument()
  })
})
