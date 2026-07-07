/**
 * AstroSignalCard — Phase AF-3 v2
 * Displays AstroFinance planetary intelligence for a stock's sector.
 * Uses platform design tokens (T / FS / FW) throughout.
 * v2: Plain-English explanations, diverging score bar, context note.
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

// ── Design config ─────────────────────────────────────────────────────────────

const ACTION_CFG: Record<string, { color: string; bg: string; border: string }> = {
  BUY:     { color: T.green,    bg: `${T.green}14`,  border: `${T.green}55`  },
  HOLD:    { color: T.blue,     bg: `${T.blue}14`,   border: `${T.blue}55`   },
  CAUTION: { color: T.amber,    bg: `${T.amber}14`,  border: `${T.amber}55`  },
  EXIT:    { color: '#F97316',  bg: '#F9731614',      border: '#F9731655'     },
  AVOID:   { color: T.red,      bg: `${T.red}14`,    border: `${T.red}55`    },
}

// ── Plain-English translation maps ────────────────────────────────────────────

const STATE_PLAIN: Record<string, { label: string; meaning: string; color: string }> = {
  EXALTED:     { label: 'Peak Strength',    color: T.green,   meaning: 'In its strongest zodiac position — maximum positive influence on the sector'  },
  OWN_SIGN:    { label: 'Own Sign',         color: T.blue,    meaning: 'Comfortable in its home sign — strong, direct, and fully expressive influence' },
  NEUTRAL:     { label: 'Neutral',          color: T.textSub, meaning: 'Neither strong nor weak — balanced, low-key influence on the sector'           },
  WEAK:        { label: 'Under Stress',     color: T.amber,   meaning: 'In an unfriendly sign — reduced capacity to support sector performance'        },
  DEBILITATED: { label: 'Weakest Position', color: T.red,     meaning: 'In its most unfavorable zodiac sign — minimal positive energy available'       },
  RETROGRADE:  { label: 'Retrograde',       color: '#F97316', meaning: 'Moving backward — reversed energy; signals delays or price corrections ahead'  },
}

const PHASE_PLAIN: Record<string, { label: string; meaning: string; color: string }> = {
  NEW_MOON:        { label: 'New Moon',        color: T.muted,   meaning: 'Cycle beginning — potential reversal zone; watch for direction change'          },
  WAXING_CRESCENT: { label: 'Waxing Crescent', color: T.blue,    meaning: 'Energy building — conditions improving; favorable for opening new positions'    },
  FIRST_QUARTER:   { label: 'First Quarter',   color: T.blue,    meaning: 'Momentum accelerating — good phase for holding and adding to positions'         },
  WAXING_GIBBOUS:  { label: 'Waxing Gibbous',  color: T.green,   meaning: 'Near peak energy — strong upward momentum in its final stage'                  },
  FULL_MOON:       { label: 'Full Moon',        color: T.amber,   meaning: 'Peak energy reached — potential exhaustion or reversal point; stay alert'       },
  WANING_GIBBOUS:  { label: 'Waning Gibbous',  color: T.amber,   meaning: 'Energy declining — momentum fading; be cautious about fresh entries'            },
  LAST_QUARTER:    { label: 'Last Quarter',     color: '#F97316', meaning: 'Declining phase — distribution and selling pressure increasing'                 },
  WANING_CRESCENT: { label: 'Waning Crescent',  color: T.red,     meaning: 'Low energy zone — consolidation phase; wait for the next cycle to begin'        },
}

const MARKET_PLAIN: Record<string, { label: string; color: string }> = {
  BULLISH:          { label: 'Broadly bullish — planetary support for broad market rise',                  color: T.green   },
  NEUTRAL_POSITIVE: { label: 'Mildly positive — modest upward planetary bias across the market',           color: T.blue    },
  NEUTRAL:          { label: 'Neutral — no significant market-level planetary signal today',                color: T.textSub },
  CAUTION:          { label: 'Cautionary — mixed or stressful planetary conditions market-wide',            color: T.amber   },
  BEARISH:          { label: 'Broadly bearish — planetary headwinds across the entire market today',        color: T.red     },
}

const ASPECT_DESC: Record<string, string> = {
  Trine:       'harmonious support (120° Trine)',
  Sextile:     'mild support (60° Sextile)',
  Conjunction: 'merged energy (0° Conjunction)',
  Square:      'tension and challenge (90° Square)',
  Opposition:  'opposing pull (180° Opposition)',
  Quincunx:    'friction and misalignment (150° Quincunx)',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildPlainReason(astro: AstroSignal): string {
  const {
    sector, primary_planet, planet_sign, planet_state, planet_retrograde,
    astro_score, eclipse_active, mercury_retrograde,
  } = astro

  if (eclipse_active) {
    return (
      `An eclipse is active — in Vedic astrology, this signals heightened volatility and potential trend reversals. ` +
      `${sector} stocks may experience sudden or unpredictable price moves during this eclipse window. ` +
      `This is a high-risk zone; exercise caution with new positions.`
    )
  }
  if (planet_retrograde && primary_planet !== 'Rahu' && primary_planet !== 'Ketu') {
    return (
      `${primary_planet} — the planet that governs ${sector} stocks — is currently moving backward (retrograde) in ${planet_sign}. ` +
      `When a sector's ruling planet goes retrograde, it weakens forward momentum and often signals ` +
      `a period of price correction, consolidation, or delayed recovery for the sector.`
    )
  }
  if (planet_state === 'DEBILITATED') {
    return (
      `${primary_planet} (the planet governing ${sector}) is in ${planet_sign} — its weakest zodiac position, ` +
      `where it has minimal positive energy to support sector performance. ` +
      `This creates a strong astrological headwind for ${sector} stocks. ` +
      `The planet will regain strength once it transits to a more favorable sign.`
    )
  }
  if (primary_planet === 'Mercury' && mercury_retrograde) {
    return (
      `Mercury is retrograde — this disrupts communication, contracts, and decision-making ` +
      `in sectors it governs, including ${sector}. ` +
      `Expect erratic price moves, news-driven volatility, and possible delays. ` +
      `Avoid opening new positions until Mercury turns direct.`
    )
  }
  if (astro_score >= 25) {
    return (
      `${primary_planet} is in a strong, favorable position in ${planet_sign} ` +
      `and receiving supportive aspects from other planets. ` +
      `This creates positive astrological conditions — a planetary tailwind for ${sector} stocks ` +
      `that historically supports sector outperformance.`
    )
  }
  if (astro_score >= -15) {
    return (
      `Mixed planetary signals: ${primary_planet} in ${planet_sign} faces both supportive and challenging ` +
      `planetary aspects, creating no clear directional bias for ${sector}. ` +
      `Hold existing positions but avoid aggressive new entries until conditions clarify.`
    )
  }
  if (astro_score >= -35) {
    return (
      `${primary_planet} (ruler of ${sector}) in ${planet_sign} is under pressure from challenging ` +
      `planetary alignments today. This creates astrological friction that may cause ` +
      `${sector} stocks to underperform the broader market in the near term.`
    )
  }
  return (
    `${primary_planet} (ruler of ${sector}) in ${planet_sign} faces severe stress from multiple ` +
    `adverse planetary positions today. This is a strong astrological headwind for ${sector} — ` +
    `Vedic astrology signals caution or reduced exposure until planetary conditions improve.`
  )
}

function parseAspects(raw: string, primaryPlanet: string): Array<{ positive: boolean; text: string }> {
  if (!raw || raw === 'None') return []
  return raw.split(';').map(a => {
    const m = a.trim().match(/^(\w+)\s+(\w+)\s+\((\w[\w_]*)\)$/)
    if (!m) return { positive: true, text: a.trim() }
    const [, planet, aspect, polarity] = m
    const positive = polarity === 'benefic'
    const desc = ASPECT_DESC[aspect] ?? aspect
    const verb = positive ? 'Supporting' : 'Challenging'
    return {
      positive,
      text: `${planet}: ${verb} ${primaryPlanet} via ${desc} — ${positive ? 'adds positive energy to the sector' : 'adds stress and resistance to the sector'}`,
    }
  })
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

function PlanetChip({ name, retrograde }: { name: string; retrograde?: boolean }) {
  const ABBR: Record<string, string> = {
    Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
    Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
  }
  const color = retrograde ? '#F97316' : T.blue
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 9px', borderRadius: 12,
      fontSize: FS.caption, fontWeight: FW.bold,
      background: `${color}18`, border: `1px solid ${color}44`, color,
      letterSpacing: 0.4, marginRight: 4, marginBottom: 4,
    }}>
      <span style={{ fontFamily: 'monospace' }}>{ABBR[name] ?? name.slice(0, 2)}</span>
      {name}{retrograde ? ' R' : ''}
    </span>
  )
}

function AstroScoreBar({ score, color }: { score: number; color: string }) {
  const absPct   = Math.min(50, Math.abs(score) / 100 * 50)
  const positive = score >= 0
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ color: T.muted, fontSize: FS.caption, fontWeight: FW.bold, textTransform: 'uppercase' as const, letterSpacing: 0.8 }}>
          Astro Score{' '}
          <span style={{ color: T.dim, fontWeight: FW.regular, letterSpacing: 0, textTransform: 'none' as const }}>
            sector · daily
          </span>
        </span>
        <span style={{ color, fontSize: FS.label, fontWeight: FW.heavy, fontVariantNumeric: 'tabular-nums' }}>
          {score > 0 ? '+' : ''}{score.toFixed(0)}
        </span>
      </div>
      {/* Diverging bar — 0 at centre; negative fills left, positive fills right */}
      <div style={{ height: 5, background: T.border, borderRadius: 3, position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: T.borderHi, zIndex: 1 }} />
        {positive ? (
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: `${absPct}%`, background: color, borderRadius: '0 3px 3px 0', transition: 'width 0.5s ease' }} />
        ) : (
          <div style={{ position: 'absolute', right: '50%', top: 0, bottom: 0, width: `${absPct}%`, background: color, borderRadius: '3px 0 0 3px', transition: 'width 0.5s ease' }} />
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
        <span style={{ color: T.muted, fontSize: FS.caption }}>−100</span>
        <span style={{ color: T.muted, fontSize: FS.caption }}>0</span>
        <span style={{ color: T.muted, fontSize: FS.caption }}>+100</span>
      </div>
    </div>
  )
}

// ── Main Card ─────────────────────────────────────────────────────────────────

export function AstroSignalCard({ astro }: { astro: AstroSignal }) {
  const cfg         = ACTION_CFG[astro.astro_action] ?? ACTION_CFG.HOLD
  const scoreColor  = astro.astro_score >= 20 ? T.green
                    : astro.astro_score >= 0   ? T.blue
                    : astro.astro_score >= -20  ? T.amber : T.red
  const statePlain  = STATE_PLAIN[astro.planet_state]  ?? { label: astro.planet_state,        meaning: '', color: T.textSub }
  const moonPlain   = PHASE_PLAIN[astro.moon_phase]    ?? { label: astro.moon_phase,           meaning: '', color: T.muted   }
  const marketPlain = MARKET_PLAIN[astro.market_astro_signal] ?? { label: astro.market_astro_signal, color: T.muted }

  const aspects     = parseAspects(astro.key_aspects, astro.primary_planet)
  const plainReason = buildPlainReason(astro)
  const rulingList  = astro.ruling_planets.split(',').map(s => s.trim())

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
          <div style={{ color: T.textSub, fontSize: FS.body }}>
            Today's planetary conditions for{' '}
            <span style={{ color: T.text, fontWeight: FW.bold }}>{astro.sector}</span>{' '}
            <span style={{ color: T.muted, fontSize: FS.caption }}>sector stocks</span>
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

      {/* ── Plain-English reason ── */}
      <div style={{
        padding: '10px 14px', borderRadius: 5,
        background: `${cfg.color}0e`, border: `1px solid ${cfg.border}`,
        color: T.text, fontSize: FS.body, lineHeight: 1.65, marginBottom: 14,
      }}>
        {plainReason}
      </div>

      {/* ── Ruling planet status ── */}
      <SectionLabel text="Ruling Planet Today" />
      <div style={{
        padding: '10px 14px', borderRadius: 6, marginBottom: 10,
        background: T.cell, border: `1px solid ${statePlain.color}33`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
          <span style={{ color: T.text, fontSize: FS.body, fontWeight: FW.bold }}>
            {astro.primary_planet} in {astro.planet_sign}
          </span>
          <span style={{
            padding: '2px 9px', borderRadius: 10,
            fontSize: FS.caption, fontWeight: FW.bold, flexShrink: 0, marginLeft: 8,
            background: `${statePlain.color}18`, border: `1px solid ${statePlain.color}44`,
            color: statePlain.color,
          }}>
            {statePlain.label}
          </span>
        </div>
        <div style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>
          {statePlain.meaning}
        </div>
      </div>

      {/* ── Planetary aspects in plain English ── */}
      {aspects.length > 0 && (
        <>
          <SectionLabel text={`Influences on ${astro.primary_planet} Today`} />
          {aspects.map((a, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 7, alignItems: 'flex-start' }}>
              <span style={{ color: a.positive ? T.green : T.red, fontSize: FS.label, marginTop: 1, flexShrink: 0, fontWeight: FW.black }}>
                {a.positive ? '+' : '−'}
              </span>
              <span style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>{a.text}</span>
            </div>
          ))}
        </>
      )}

      {/* ── Moon & market conditions ── */}
      <SectionLabel text="Moon & Market Conditions" />
      <div style={{
        padding: '10px 14px', borderRadius: 6, marginBottom: 10,
        background: T.cell, border: `1px solid ${T.border}`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
          <span style={{ color: T.muted, fontSize: FS.caption, flexShrink: 0, minWidth: 90 }}>Moon today</span>
          <div style={{ textAlign: 'right' }}>
            <span style={{ color: moonPlain.color, fontSize: FS.caption, fontWeight: FW.bold }}>
              {moonPlain.label}
            </span>
            {astro.moon_illumination != null && (
              <span style={{ color: T.muted, fontSize: FS.caption }}> ({astro.moon_illumination}%)</span>
            )}
            <div style={{ color: T.muted, fontSize: FS.caption, marginTop: 2, lineHeight: 1.4 }}>
              {moonPlain.meaning}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderTop: `1px solid ${T.border}33`, paddingTop: 7 }}>
          <span style={{ color: T.muted, fontSize: FS.caption, flexShrink: 0, minWidth: 90 }}>Market-wide</span>
          <span style={{ color: marketPlain.color, fontSize: FS.caption, fontWeight: FW.bold, textAlign: 'right', maxWidth: '68%', lineHeight: 1.4 }}>
            {marketPlain.label}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${T.border}33`, paddingTop: 7, marginTop: 7 }}>
          <span style={{ color: T.muted, fontSize: FS.caption }}>Jupiter / Saturn</span>
          <span style={{ color: T.textSub, fontSize: FS.caption, fontVariantNumeric: 'tabular-nums' }}>
            {astro.jupiter_sign || '?'} / {astro.saturn_sign || '?'}
          </span>
        </div>
      </div>

      {/* ── Ruling planets chips ── */}
      <SectionLabel text={`Planets Governing ${astro.sector}`} />
      <div style={{ display: 'flex', flexWrap: 'wrap', marginBottom: 4 }}>
        {rulingList.map(p => (
          <PlanetChip
            key={p}
            name={p}
            retrograde={
              (p === astro.primary_planet && astro.planet_retrograde) ||
              (p === 'Mercury' && astro.mercury_retrograde) ||
              (p === 'Venus' && astro.venus_retrograde)
            }
          />
        ))}
      </div>

      {/* ── Retrograde warnings ── */}
      {(astro.planet_retrograde || astro.mercury_retrograde || astro.venus_retrograde) && (
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
          {astro.planet_retrograde && astro.primary_planet !== 'Rahu' && astro.primary_planet !== 'Ketu' && (
            <div style={{ padding: '6px 10px', borderRadius: 4, background: '#F9731614', border: '1px solid #F9731644', color: '#F97316', fontSize: FS.caption, fontWeight: FW.bold }}>
              {astro.primary_planet} RETROGRADE — ruling planet is moving backward; sector momentum is weakened
            </div>
          )}
          {astro.mercury_retrograde && (
            <div style={{ padding: '6px 10px', borderRadius: 4, background: '#F9731614', border: '1px solid #F9731644', color: '#F97316', fontSize: FS.caption }}>
              Mercury retrograde — watch for contract delays, earnings surprises, and mixed data signals
            </div>
          )}
          {astro.venus_retrograde && (
            <div style={{ padding: '6px 10px', borderRadius: 4, background: '#F9731614', border: '1px solid #F9731644', color: '#F97316', fontSize: FS.caption }}>
              Venus retrograde — FMCG, luxury, and auto sectors are particularly affected
            </div>
          )}
        </div>
      )}

      {/* ── Eclipse alert ── */}
      {astro.eclipse_active && (
        <div style={{
          marginTop: 8, padding: '6px 10px', borderRadius: 4,
          background: `${T.amber}14`, border: `1px solid ${T.amber}44`,
          color: T.amber, fontSize: FS.caption, fontWeight: FW.bold, letterSpacing: 0.4,
        }}>
          ECLIPSE ACTIVE — High-volatility zone; sudden reversals are possible
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

      {/* ── Context: what this score measures vs Kundli ── */}
      <div style={{
        marginTop: 14, padding: '12px 14px', borderRadius: 6,
        background: `${T.blue}09`, border: `1px solid ${T.blue}20`,
      }}>
        <div style={{
          fontSize: FS.caption, color: T.blue, fontWeight: FW.heavy,
          letterSpacing: 1, textTransform: 'uppercase' as const, marginBottom: 6,
        }}>
          What this score measures
        </div>
        <div style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.6, marginBottom: 8 }}>
          This is a <span style={{ color: T.text, fontWeight: FW.bold }}>real-time sector-level signal</span> — it reflects today's positions of the planets that govern <em>all</em> {astro.sector} stocks (ruling planets: {astro.ruling_planets}). It updates daily as planets move through the zodiac.
        </div>
        <div style={{
          fontSize: FS.body, color: T.textSub, lineHeight: 1.6,
          paddingTop: 8, borderTop: `1px solid ${T.border}`,
        }}>
          <span style={{ color: T.amber, fontWeight: FW.bold }}>Why this may differ from the Kundli score:</span>
          {' '}The Kundli score (shown separately) is based on this company's natal birth chart — the planetary positions at its IPO date. That score is fixed and stock-specific. This Astro Signal score reflects sector-wide planetary conditions today and changes daily. A stock can have a strong natal chart (high Kundli score) yet face a weak sector planetary period (low Astro Signal), or vice versa — both perspectives together give the fullest picture.
        </div>
      </div>

      {/* ── Footer ── */}
      <div style={{ color: T.muted, fontSize: FS.caption, borderTop: `1px solid ${T.border}`, paddingTop: 8, marginTop: 12 }}>
        Based on Vedic planet-sector mapping (Banerjee 2009) + Western aspects (Pesavento 2015). Supplementary to technical and fundamental analysis.
      </div>
    </div>
  )
}
