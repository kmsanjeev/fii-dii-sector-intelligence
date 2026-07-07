/**
 * AstroSignalCard — Phase AF-3
 * Displays AstroFinance planetary intelligence for a stock's sector.
 * Uses platform design tokens (T / FS / FW) throughout.
 */

import React from 'react'
import { T, FS, FW } from '../../styles/tokens'

// ── Types ─────────────────────────────────────────────────────────────────────

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

// ── Action config ─────────────────────────────────────────────────────────────

const ACTION_CFG: Record<string, { color: string; bg: string; border: string }> = {
  BUY:     { color: T.green,  bg: `${T.green}14`,  border: `${T.green}55`  },
  HOLD:    { color: T.blue,   bg: `${T.blue}14`,   border: `${T.blue}55`   },
  CAUTION: { color: T.amber,  bg: `${T.amber}14`,  border: `${T.amber}55`  },
  EXIT:    { color: '#F97316', bg: '#F9731614',     border: '#F9731655'     },
  AVOID:   { color: T.red,    bg: `${T.red}14`,    border: `${T.red}55`    },
}

const PLANET_EMOJI: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
  Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}

const STATE_COLOR: Record<string, string> = {
  EXALTED:     T.green,
  OWN_SIGN:    T.blue,
  NEUTRAL:     T.textSub,
  WEAK:        T.amber,
  DEBILITATED: T.red,
  RETROGRADE:  '#F97316',
}

const MOON_PHASE_LABEL: Record<string, string> = {
  NEW_MOON:        'New Moon',
  WAXING_CRESCENT: 'Waxing Crescent',
  FIRST_QUARTER:   '1st Quarter',
  WAXING_GIBBOUS:  'Waxing Gibbous',
  FULL_MOON:       'Full Moon',
  WANING_GIBBOUS:  'Waning Gibbous',
  LAST_QUARTER:    'Last Quarter',
  WANING_CRESCENT: 'Waning Crescent',
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ text }: { text: string }) {
  return (
    <div style={{
      fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1.4,
      textTransform: 'uppercase' as const, color: T.muted,
      borderBottom: `1px solid ${T.border}`, paddingBottom: 5, marginBottom: 8, marginTop: 12,
    }}>
      {text}
    </div>
  )
}

function InfoRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
      <span style={{ color: T.muted, fontSize: FS.caption, flexShrink: 0, minWidth: 110 }}>{label}</span>
      <span style={{ color: valueColor ?? T.textSub, fontSize: FS.caption, fontWeight: FW.medium, textAlign: 'right', maxWidth: '55%' }}>
        {value}
      </span>
    </div>
  )
}

function PlanetChip({ name, state }: { name: string; state?: string }) {
  const color = state ? (STATE_COLOR[state] ?? T.textSub) : T.textSub
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 9px', borderRadius: 12,
      fontSize: FS.caption, fontWeight: FW.bold,
      background: `${color}18`, border: `1px solid ${color}44`, color,
      letterSpacing: 0.4, marginRight: 4, marginBottom: 4,
    }}>
      <span style={{ fontFamily: 'monospace', fontSize: FS.caption }}>{PLANET_EMOJI[name] ?? name.slice(0, 2)}</span>
      {name}
    </span>
  )
}

function RetroWarning({ planet }: { planet: string }) {
  return (
    <span style={{
      padding: '3px 8px', borderRadius: 4,
      fontSize: FS.caption, fontWeight: FW.bold,
      background: `#F9731618`, border: `1px solid #F9731644`, color: '#F97316',
      letterSpacing: 0.5, marginRight: 4,
    }}>
      {planet} RETRO
    </span>
  )
}

function AstroScoreBar({ score, color }: { score: number; color: string }) {
  const pct = Math.min(100, Math.max(2, (score + 100) / 2))
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ color: T.muted, fontSize: FS.caption, letterSpacing: 0.8, fontWeight: FW.bold, textTransform: 'uppercase' as const }}>
          Astro Score
        </span>
        <span style={{ color, fontSize: FS.label, fontWeight: FW.heavy, fontVariantNumeric: 'tabular-nums' }}>
          {score > 0 ? '+' : ''}{score.toFixed(0)} / 100
        </span>
      </div>
      <div style={{ height: 5, background: T.border, borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.5s ease' }} />
      </div>
    </div>
  )
}

// ── Main Card ─────────────────────────────────────────────────────────────────

export function AstroSignalCard({ astro }: { astro: AstroSignal }) {
  const cfg       = ACTION_CFG[astro.astro_action] ?? ACTION_CFG.HOLD
  const stateColor = STATE_COLOR[astro.planet_state] ?? T.textSub
  const scoreColor = astro.astro_score >= 20 ? T.green
                   : astro.astro_score >= 0  ? T.blue
                   : astro.astro_score >= -20 ? T.amber : T.red
  const moonLabel  = MOON_PHASE_LABEL[astro.moon_phase] ?? astro.moon_phase

  return (
    <div style={{
      background: T.panel, border: `1px solid ${T.border}`, borderRadius: 8,
      padding: 16, marginBottom: 16,
    }}>
      {/* ── Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
            <span style={{ color: T.muted, fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1.4, textTransform: 'uppercase' as const }}>
              Astro Signal
            </span>
            <span style={{ color: T.muted, fontSize: FS.caption }}>{astro.as_of_date}</span>
          </div>
          <div style={{ color: T.textSub, fontSize: FS.caption }}>
            Sector: <span style={{ color: T.text, fontWeight: FW.bold }}>{astro.sector}</span>
          </div>
        </div>
        <div style={{
          padding: '5px 14px', borderRadius: 5,
          background: cfg.bg, border: `1px solid ${cfg.border}`, color: cfg.color,
          fontSize: FS.label, fontWeight: FW.heavy, letterSpacing: 1, flexShrink: 0,
        }}>
          {astro.astro_action}
        </div>
      </div>

      {/* ── Score bar ── */}
      <AstroScoreBar score={astro.astro_score} color={scoreColor} />

      {/* ── Reason ── */}
      <div style={{
        padding: '8px 12px', borderRadius: 5,
        background: `${cfg.color}0e`, border: `1px solid ${cfg.border}`,
        color: T.text, fontSize: FS.body, lineHeight: 1.55, marginBottom: 14,
      }}>
        {astro.astro_reason}
      </div>

      {/* ── Ruling planets ── */}
      <SectionLabel text="Ruling Planets" />
      <div style={{ display: 'flex', flexWrap: 'wrap', marginBottom: 4 }}>
        {astro.ruling_planets.split(', ').map(p => (
          <PlanetChip
            key={p}
            name={p.trim()}
            state={p.trim() === astro.primary_planet ? astro.planet_state : undefined}
          />
        ))}
      </div>

      {/* ── Retrograde warnings ── */}
      {(astro.planet_retrograde || astro.mercury_retrograde || astro.venus_retrograde) && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6, marginBottom: 10 }}>
          {astro.planet_retrograde && astro.primary_planet !== 'Rahu' && astro.primary_planet !== 'Ketu' && (
            <RetroWarning planet={astro.primary_planet} />
          )}
          {astro.mercury_retrograde && !astro.planet_retrograde && <RetroWarning planet="Mercury" />}
          {astro.venus_retrograde && <RetroWarning planet="Venus" />}
        </div>
      )}

      {/* ── Planet details ── */}
      <SectionLabel text="Planet Details" />
      <InfoRow
        label={`${astro.primary_planet} position`}
        value={`${astro.planet_sign}  —  ${astro.planet_state}`}
        valueColor={stateColor}
      />
      <InfoRow
        label="Key aspects"
        value={astro.key_aspects || 'None significant'}
      />
      <InfoRow
        label="Moon phase"
        value={`${moonLabel}${astro.moon_illumination ? ` (${astro.moon_illumination}%)` : ''}`}
        valueColor={astro.moon_phase === 'FULL_MOON' || astro.moon_phase === 'NEW_MOON' ? T.amber : T.textSub}
      />
      <InfoRow label="Jupiter / Saturn" value={`${astro.jupiter_sign || '?'}  /  ${astro.saturn_sign || '?'}`} />
      <InfoRow
        label="Market astro signal"
        value={astro.market_astro_signal || 'UNKNOWN'}
        valueColor={
          astro.market_astro_signal === 'BULLISH'            ? T.green
          : astro.market_astro_signal === 'BEARISH'          ? T.red
          : astro.market_astro_signal?.includes('POSITIVE')  ? T.blue
          : T.amber
        }
      />

      {/* ── Alerts ── */}
      {astro.eclipse_active && (
        <div style={{
          marginTop: 10, padding: '6px 10px', borderRadius: 4,
          background: `${T.amber}14`, border: `1px solid ${T.amber}44`,
          color: T.amber, fontSize: FS.caption, fontWeight: FW.bold, letterSpacing: 0.4,
        }}>
          ECLIPSE ACTIVE — High volatility zone
        </div>
      )}
      {astro.reversal_note && (
        <div style={{
          marginTop: 6, padding: '6px 10px', borderRadius: 4,
          background: `${T.amber}0e`, border: `1px solid ${T.amber}33`,
          color: T.textSub, fontSize: FS.caption, lineHeight: 1.5,
        }}>
          {astro.reversal_note}
        </div>
      )}

      {/* ── Footer ── */}
      <div style={{ color: T.muted, fontSize: FS.caption, borderTop: `1px solid ${T.border}`, paddingTop: 8, marginTop: 12 }}>
        Based on Vedic planet-sector mapping (Banerjee 2009) + Western aspects (Pesavento 2015).
        Supplementary to technical and fundamental analysis.
      </div>
    </div>
  )
}
