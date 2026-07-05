/**
 * AstroSignalCard — Phase AF-3
 * Displays AstroFinance planetary intelligence for a stock's sector.
 *
 * Knowledge source: 6 financial astrology books including Banerjee (Indian/Vedic
 * sector-planet mapping), Pesavento (aspect theory), and Almanac 2023 (cycle frameworks).
 */

import React from 'react'

// ── Types ────────────────────────────────────────────────────────────────────

export interface AstroSignal {
  sector:              string
  ruling_planets:      string
  primary_planet:      string
  planet_sign:         string
  planet_state:        string
  planet_retrograde:   boolean
  key_aspects:         string
  astro_score:         number
  astro_action:        'BUY' | 'HOLD' | 'CAUTION' | 'EXIT' | 'AVOID' | string
  astro_reason:        string
  moon_phase:          string
  eclipse_active:      boolean
  as_of_date:          string
  market_astro_signal: string
  mercury_retrograde:  boolean
  venus_retrograde:    boolean
  moon_illumination:   number | null
  jupiter_sign:        string
  saturn_sign:         string
  reversal_note:       string | null
}

// ── Config ───────────────────────────────────────────────────────────────────

const ACTION_CFG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  BUY:     { color: '#4ADE80', bg: '#052e16', border: '#16a34a', label: 'BUY' },
  HOLD:    { color: '#60A5FA', bg: '#0c1a2e', border: '#2563eb', label: 'HOLD' },
  CAUTION: { color: '#FBBF24', bg: '#1c1500', border: '#d97706', label: 'CAUTION' },
  EXIT:    { color: '#F97316', bg: '#1c0a00', border: '#ea580c', label: 'EXIT' },
  AVOID:   { color: '#F87171', bg: '#1c0000', border: '#dc2626', label: 'AVOID' },
}

const PLANET_EMOJI: Record<string, string> = {
  Sun: 'O', Moon: ')', Mercury: '*', Venus: 'V', Mars: 'M',
  Jupiter: 'J', Saturn: 'S', Rahu: 'R', Ketu: 'K',
  Uranus: 'U', Neptune: 'N', Pluto: 'P',
}

const MOON_PHASE_LABEL: Record<string, { icon: string; label: string }> = {
  NEW_MOON:       { icon: 'N', label: 'New Moon' },
  WAXING_CRESCENT:{ icon: 'C', label: 'Waxing' },
  FIRST_QUARTER:  { icon: 'Q', label: '1st Quarter' },
  WAXING_GIBBOUS: { icon: 'G', label: 'Waxing Gibbous' },
  FULL_MOON:      { icon: 'F', label: 'Full Moon' },
  WANING_GIBBOUS: { icon: 'g', label: 'Waning Gibbous' },
  LAST_QUARTER:   { icon: 'q', label: 'Last Quarter' },
  WANING_CRESCENT:{ icon: 'c', label: 'Waning' },
}

const STATE_COLOR: Record<string, string> = {
  EXALTED:    '#4ADE80',
  OWN_SIGN:   '#60A5FA',
  NEUTRAL:    '#94A3B8',
  WEAK:       '#FBBF24',
  DEBILITATED:'#F87171',
  RETROGRADE: '#F97316',
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function PlanetChip({ name, state }: { name: string; state?: string }) {
  const color = state ? (STATE_COLOR[state] ?? '#94A3B8') : '#94A3B8'
  const emoji = PLANET_EMOJI[name] ?? name[0]
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 12, fontSize: 10, fontWeight: 700,
      background: `${color}18`, border: `1px solid ${color}44`, color,
      letterSpacing: 0.5, marginRight: 4,
    }}>
      <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{emoji}</span>
      {name}
    </span>
  )
}

function RetroWarning({ planet }: { planet: string }) {
  return (
    <span style={{
      padding: '2px 7px', borderRadius: 3, fontSize: 9, fontWeight: 700,
      background: '#3d1c00', border: '1px solid #ea580c44', color: '#F97316',
      letterSpacing: 0.5,
    }}>
      {planet} RETROGRADE
    </span>
  )
}

function InfoRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
      <span style={{ color: '#475569', fontSize: 10 }}>{label}</span>
      <span style={{ color: valueColor ?? '#94A3B8', fontSize: 10, fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>
        {value}
      </span>
    </div>
  )
}

// ── Score Bar ────────────────────────────────────────────────────────────────

function AstroScoreBar({ score }: { score: number }) {
  const pct = (score + 100) / 2  // -100..+100 -> 0..100
  const color = score >= 20 ? '#4ADE80' : score >= 0 ? '#60A5FA' : score >= -20 ? '#FBBF24' : '#F87171'
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ color: '#475569', fontSize: 9, letterSpacing: 0.5 }}>ASTRO SCORE</span>
        <span style={{ color, fontSize: 11, fontWeight: 700 }}>
          {score > 0 ? '+' : ''}{score.toFixed(0)} / 100
        </span>
      </div>
      <div style={{ height: 4, background: '#1E2332', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${Math.max(2, pct)}%`,
          background: color, borderRadius: 2,
          transition: 'width 0.5s ease',
        }} />
      </div>
    </div>
  )
}

// ── Main Card ────────────────────────────────────────────────────────────────

interface Props {
  astro: AstroSignal
}

export function AstroSignalCard({ astro }: Props) {
  const cfg = ACTION_CFG[astro.astro_action] ?? ACTION_CFG.HOLD
  const moonInfo = MOON_PHASE_LABEL[astro.moon_phase] ?? { icon: '~', label: astro.moon_phase }
  const stateColor = STATE_COLOR[astro.planet_state] ?? '#94A3B8'

  return (
    <div style={{
      background: '#0D1117', border: '1px solid #1E2332', borderRadius: 8,
      padding: 16, marginBottom: 16,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
            <span style={{ color: '#94A3B8', fontSize: 9, fontWeight: 700, letterSpacing: 1 }}>
              ASTRO SIGNAL
            </span>
            <span style={{ color: '#334155', fontSize: 9 }}>
              {astro.as_of_date}
            </span>
          </div>
          <div style={{ color: '#475569', fontSize: 9, letterSpacing: 0.3 }}>
            Planetary intelligence based on Financial Astrology principles
          </div>
        </div>
        {/* Action Badge */}
        <div style={{
          padding: '5px 14px', borderRadius: 4, border: `1px solid ${cfg.border}`,
          background: cfg.bg, color: cfg.color, fontSize: 11, fontWeight: 700,
          letterSpacing: 1, flexShrink: 0,
        }}>
          {cfg.label}
        </div>
      </div>

      {/* Score bar */}
      <AstroScoreBar score={astro.astro_score} />

      {/* Reason */}
      <div style={{
        padding: '6px 10px', borderRadius: 4, background: `${cfg.border}11`,
        border: `1px solid ${cfg.border}33`, marginBottom: 12,
        color: cfg.color, fontSize: 10, lineHeight: 1.5,
      }}>
        {astro.astro_reason}
      </div>

      {/* Planet row */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ color: '#475569', fontSize: 9, letterSpacing: 0.5, marginBottom: 5 }}>
          RULING PLANET(S)
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }}>
          {astro.ruling_planets.split(', ').map(p => (
            <PlanetChip
              key={p}
              name={p.trim()}
              state={p.trim() === astro.primary_planet ? astro.planet_state : undefined}
            />
          ))}
        </div>
      </div>

      {/* Retrograde warnings */}
      {(astro.planet_retrograde || astro.mercury_retrograde || astro.venus_retrograde) && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
          {astro.planet_retrograde && astro.primary_planet !== 'Rahu' && astro.primary_planet !== 'Ketu' && (
            <RetroWarning planet={astro.primary_planet} />
          )}
          {astro.mercury_retrograde && !astro.planet_retrograde && (
            <RetroWarning planet="Mercury" />
          )}
          {astro.venus_retrograde && (
            <RetroWarning planet="Venus" />
          )}
        </div>
      )}

      {/* Planetary details grid */}
      <div style={{ borderTop: '1px solid #1E2332', paddingTop: 10, marginBottom: 10 }}>
        <InfoRow
          label={`${astro.primary_planet} Position`}
          value={`${astro.planet_sign} — ${astro.planet_state}`}
          valueColor={stateColor}
        />
        <InfoRow
          label="Key Aspects"
          value={astro.key_aspects || 'None significant'}
          valueColor="#94A3B8"
        />
        <InfoRow
          label="Moon Phase"
          value={`${moonInfo.icon} ${moonInfo.label}${astro.moon_illumination ? ` (${astro.moon_illumination}%)` : ''}`}
          valueColor={astro.moon_phase === 'NEW_MOON' || astro.moon_phase === 'FULL_MOON' ? '#FBBF24' : '#94A3B8'}
        />
        <InfoRow
          label="Jupiter / Saturn"
          value={`${astro.jupiter_sign || '?'} / ${astro.saturn_sign || '?'}`}
        />
        <InfoRow
          label="Market Astro Signal"
          value={astro.market_astro_signal || 'UNKNOWN'}
          valueColor={
            astro.market_astro_signal === 'BULLISH' ? '#4ADE80' :
            astro.market_astro_signal === 'BEARISH' ? '#F87171' :
            astro.market_astro_signal?.includes('POSITIVE') ? '#60A5FA' :
            '#FBBF24'
          }
        />
      </div>

      {/* Eclipse / reversal note */}
      {astro.eclipse_active && (
        <div style={{
          padding: '5px 10px', borderRadius: 3, background: '#2d1200',
          border: '1px solid #92400e', color: '#FBBF24', fontSize: 9,
          fontWeight: 600, letterSpacing: 0.5, marginBottom: 8,
        }}>
          ECLIPSE ACTIVE — High volatility zone. Ketu eclipse = downtrend warning.
        </div>
      )}
      {astro.reversal_note && (
        <div style={{
          padding: '5px 10px', borderRadius: 3, background: '#1e1600',
          border: '1px solid #78350f', color: '#FCD34D', fontSize: 9,
          fontWeight: 600, letterSpacing: 0.3, marginBottom: 8,
        }}>
          {astro.reversal_note}
        </div>
      )}

      {/* Footer disclaimer */}
      <div style={{ color: '#1E2D3D', fontSize: 8, borderTop: '1px solid #0f172a', paddingTop: 6, marginTop: 6 }}>
        Astro signals are supplementary to technical & fundamental analysis.
        Based on Vedic (Indian) planet-sector mapping per Banerjee (2009) + Western aspects per Pesavento (2015).
      </div>
    </div>
  )
}
