import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AstroSignalCard, type AstroSignal } from '../components/platform/AstroSignalCard'


const SAMPLE_ASTRO: AstroSignal = {
  sector: 'BANKING',
  ruling_planets: 'Jupiter, Mercury',
  primary_planet: 'Jupiter',
  planet_sign: 'Cancer',
  planet_state: 'EXALTED',
  planet_retrograde: false,
  key_aspects: 'Moon Trine (benefic)',
  astro_score: 34,
  astro_action: 'Positive AstroFinance heuristic',
  astro_action_code: 'BUY',
  astro_action_label: 'Positive AstroFinance heuristic',
  astro_reason: 'The AstroFinance model reads Jupiter in Cancer as a supportive backdrop for BANKING. Use this as a bounded heuristic signal alongside price, flow, and fundamental analysis.',
  moon_phase: 'WAXING_GIBBOUS',
  eclipse_active: false,
  as_of_date: '2026-08-10',
  market_astro_signal: 'BULLISH',
  mercury_retrograde: false,
  venus_retrograde: false,
  moon_illumination: 72,
  jupiter_sign: 'Cancer',
  saturn_sign: 'Pisces',
  reversal_note: null,
  evidence_class: 'INTERNAL_HEURISTIC',
  source_status: 'UNVERIFIED',
  interpretation_type: 'ASTROFINANCE_HEURISTIC',
  high_stakes: true,
  actionability: 'NON_ACTIONABLE_HEURISTIC',
  output_classification: 'ASTROLOGY_HEURISTIC',
  boundary_note: 'AstroFinance heuristic only; cross-check with market, technical, and fundamental evidence.',
}


describe('AstroFinance safety presentation', () => {
  it('renders bounded heuristic labels and boundary copy', () => {
    render(<AstroSignalCard astro={SAMPLE_ASTRO} />)

    expect(screen.getByText('AstroFinance Heuristic')).toBeInTheDocument()
    expect(screen.getByText('Positive AstroFinance heuristic')).toBeInTheDocument()
    expect(screen.getByText(/cross-check with market, technical, and fundamental evidence/i)).toBeInTheDocument()
    expect(screen.queryByText('BUY')).not.toBeInTheDocument()
    expect(screen.queryByText(/avoid opening new positions/i)).not.toBeInTheDocument()
  })
})
