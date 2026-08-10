/*
 * AstroSignalCard - bounded AstroFinance presentation
 * Displays sector-level planetary context without prescriptive trading language.
 */

import { T, FS, FW } from '../../styles/tokens'

export interface AstroSignal {
  sector: string
  ruling_planets: string
  primary_planet: string
  planet_sign: string
  planet_state: string
  planet_retrograde: boolean
  key_aspects: string
  astro_score: number
  astro_action: 'BUY' | 'HOLD' | 'CAUTION' | 'EXIT' | 'AVOID' | string
  astro_action_code?: 'BUY' | 'HOLD' | 'CAUTION' | 'EXIT' | 'AVOID' | string
  astro_action_label?: string
  astro_reason: string
  moon_phase: string
  eclipse_active: boolean
  as_of_date: string
  market_astro_signal: string
  mercury_retrograde: boolean
  venus_retrograde: boolean
  moon_illumination: number | null
  jupiter_sign: string
  saturn_sign: string
  reversal_note: string | null
  evidence_class?: string
  source_status?: string
  interpretation_type?: string
  high_stakes?: boolean
  actionability?: string
  output_classification?: string
  boundary_note?: string
}

const ACTION_CFG: Record<string, { color: string; bg: string; border: string }> = {
  BUY: { color: T.green, bg: `${T.green}14`, border: `${T.green}55` },
  HOLD: { color: T.blue, bg: `${T.blue}14`, border: `${T.blue}55` },
  CAUTION: { color: T.amber, bg: `${T.amber}14`, border: `${T.amber}55` },
  EXIT: { color: '#F97316', bg: '#F9731614', border: '#F9731655' },
  AVOID: { color: T.red, bg: `${T.red}14`, border: `${T.red}55` },
}

const STATE_PLAIN: Record<string, { label: string; meaning: string; color: string }> = {
  EXALTED: { label: 'Peak Strength', color: T.green, meaning: 'The model treats the ruling planet as strongly supportive.' },
  OWN_SIGN: { label: 'Own Sign', color: T.blue, meaning: 'The ruling planet is in a stable sign state within the model.' },
  NEUTRAL: { label: 'Neutral', color: T.textSub, meaning: 'The ruling planet is not strongly amplified or weakened.' },
  WEAK: { label: 'Under Stress', color: T.amber, meaning: 'The model reads reduced support from the ruling planet.' },
  DEBILITATED: { label: 'Weakest Position', color: T.red, meaning: 'The model treats the ruling planet as materially weakened.' },
  RETROGRADE: { label: 'Retrograde', color: '#F97316', meaning: 'Retrograde motion is treated as a friction or delay factor.' },
}

const PHASE_PLAIN: Record<string, { label: string; meaning: string; color: string }> = {
  NEW_MOON: { label: 'New Moon', color: T.muted, meaning: 'Cycle reset phase; sentiment can change quickly.' },
  WAXING_CRESCENT: { label: 'Waxing Crescent', color: T.blue, meaning: 'The model associates this phase with improving sentiment.' },
  FIRST_QUARTER: { label: 'First Quarter', color: T.blue, meaning: 'The model often reads this as a stronger participation phase.' },
  WAXING_GIBBOUS: { label: 'Waxing Gibbous', color: T.green, meaning: 'The model treats this as a stronger momentum backdrop.' },
  FULL_MOON: { label: 'Full Moon', color: T.amber, meaning: 'Peak energy phase; watch for exhaustion or reversal conditions.' },
  WANING_GIBBOUS: { label: 'Waning Gibbous', color: T.amber, meaning: 'Momentum can soften as the lunar cycle fades.' },
  LAST_QUARTER: { label: 'Last Quarter', color: '#F97316', meaning: 'The model often associates this with heavier friction.' },
  WANING_CRESCENT: { label: 'Waning Crescent', color: T.red, meaning: 'Consolidation conditions can dominate before the next cycle begins.' },
}

const MARKET_PLAIN: Record<string, { label: string; color: string }> = {
  BULLISH: { label: 'Broadly supportive planetary backdrop', color: T.green },
  NEUTRAL_POSITIVE: { label: 'Mildly positive planetary backdrop', color: T.blue },
  NEUTRAL: { label: 'No strong market-wide planetary bias', color: T.textSub },
  CAUTION: { label: 'Mixed or stressed planetary backdrop', color: T.amber },
  BEARISH: { label: 'Broad planetary headwinds across the market', color: T.red },
}

const ASPECT_DESC: Record<string, string> = {
  Trine: 'harmonious support (120 deg trine)',
  Sextile: 'mild support (60 deg sextile)',
  Conjunction: 'merged energy (0 deg conjunction)',
  Square: 'tension and challenge (90 deg square)',
  Opposition: 'opposing pull (180 deg opposition)',
  Quincunx: 'friction and misalignment (150 deg quincunx)',
}

function buildPlainReason(astro: AstroSignal): string {
  const {
    sector,
    primary_planet,
    planet_sign,
    planet_state,
    planet_retrograde,
    astro_score,
    eclipse_active,
    mercury_retrograde,
  } = astro

  if (eclipse_active) {
    return (
      `An eclipse window is active in the AstroFinance model, so ${sector} is being treated as a higher-volatility heuristic regime. ` +
      `Use this as bounded context rather than as a directional market instruction.`
    )
  }
  if (planet_retrograde && primary_planet !== 'Rahu' && primary_planet !== 'Ketu') {
    return (
      `${primary_planet}, the AstroFinance ruling planet for ${sector}, is retrograde in ${planet_sign}. ` +
      `The model treats that as a weakening factor for short-term sector momentum, not as validated investment advice.`
    )
  }
  if (planet_state === 'DEBILITATED') {
    return (
      `${primary_planet} is in a weak sign state for the AstroFinance model, which currently lowers the heuristic outlook for ${sector}. ` +
      `This remains a non-classical experimental signal that should be cross-checked against market evidence.`
    )
  }
  if (primary_planet === 'Mercury' && mercury_retrograde) {
    return (
      `Mercury is retrograde, which this model associates with communication friction, contract delays, and noisier sector signals. ` +
      `Treat the reading as bounded AstroFinance context rather than as a direct portfolio action.`
    )
  }
  if (astro_score >= 25) {
    return (
      `${primary_planet} is in a supportive sign state in ${planet_sign}, so the AstroFinance model reads the backdrop for ${sector} as relatively constructive. ` +
      `Use the signal as a heuristic layer alongside price, flow, and fundamental analysis.`
    )
  }
  if (astro_score >= -15) {
    return (
      `The model finds mixed planetary conditions around ${sector}, with no strong directional conclusion. ` +
      `Interpret the signal as a context layer rather than as a trade instruction.`
    )
  }
  if (astro_score >= -35) {
    return (
      `The model reads challenging planetary conditions for ${sector} today. ` +
      `This is a cautionary heuristic signal, not a validated instruction to buy, sell, or exit.`
    )
  }
  return (
    `The model flags pronounced planetary stress around ${sector} in its current heuristic framework. ` +
    `Treat the signal as experimental and non-actionable without independent market confirmation.`
  )
}

function parseAspects(raw: string, primaryPlanet: string): Array<{ positive: boolean; text: string }> {
  if (!raw || raw === 'None') return []
  return raw.split(';').map(a => {
    const trimmed = a.trim()
    const match = trimmed.match(/^(\w+)\s+(\w+)\s+\((\w[\w_]*)\)$/)
    if (!match) return { positive: true, text: trimmed }
    const [, planet, aspect, polarity] = match
    const positive = polarity === 'benefic'
    const desc = ASPECT_DESC[aspect] ?? aspect
    return {
      positive,
      text: `${planet}: ${positive ? 'supporting' : 'challenging'} ${primaryPlanet} via ${desc}.`,
    }
  })
}

function SectionLabel({ text }: { text: string }) {
  return (
    <div style={{
      fontSize: FS.caption,
      fontWeight: FW.heavy,
      letterSpacing: 1.4,
      textTransform: 'uppercase' as const,
      color: T.muted,
      borderBottom: `1px solid ${T.border}`,
      paddingBottom: 5,
      marginBottom: 8,
      marginTop: 12,
    }}>
      {text}
    </div>
  )
}

function PlanetChip({ name, retrograde }: { name: string; retrograde?: boolean }) {
  const abbr: Record<string, string> = {
    Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
    Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
  }
  const color = retrograde ? '#F97316' : T.blue
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      padding: '3px 9px',
      borderRadius: 12,
      fontSize: FS.caption,
      fontWeight: FW.bold,
      background: `${color}18`,
      border: `1px solid ${color}44`,
      color,
      letterSpacing: 0.4,
      marginRight: 4,
      marginBottom: 4,
    }}>
      <span style={{ fontFamily: 'monospace' }}>{abbr[name] ?? name.slice(0, 2)}</span>
      {name}{retrograde ? ' R' : ''}
    </span>
  )
}

function AstroScoreBar({ score, color }: { score: number; color: string }) {
  const absPct = Math.min(50, Math.abs(score) / 100 * 50)
  const positive = score >= 0
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ color: T.muted, fontSize: FS.caption, fontWeight: FW.bold, textTransform: 'uppercase' as const, letterSpacing: 0.8 }}>
          Astro Score <span style={{ color: T.dim, fontWeight: FW.regular, letterSpacing: 0, textTransform: 'none' as const }}>sector / daily</span>
        </span>
        <span style={{ color, fontSize: FS.label, fontWeight: FW.heavy, fontVariantNumeric: 'tabular-nums' }}>
          {score > 0 ? '+' : ''}{score.toFixed(0)}
        </span>
      </div>
      <div style={{ height: 5, background: T.border, borderRadius: 3, position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: T.borderHi, zIndex: 1 }} />
        {positive ? (
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: `${absPct}%`, background: color, borderRadius: '0 3px 3px 0', transition: 'width 0.5s ease' }} />
        ) : (
          <div style={{ position: 'absolute', right: '50%', top: 0, bottom: 0, width: `${absPct}%`, background: color, borderRadius: '3px 0 0 3px', transition: 'width 0.5s ease' }} />
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
        <span style={{ color: T.muted, fontSize: FS.caption }}>-100</span>
        <span style={{ color: T.muted, fontSize: FS.caption }}>0</span>
        <span style={{ color: T.muted, fontSize: FS.caption }}>+100</span>
      </div>
    </div>
  )
}

export function AstroSignalCard({ astro }: { astro: AstroSignal }) {
  const actionCode = astro.astro_action_code ?? astro.astro_action
  const actionLabel = astro.astro_action_label ?? astro.astro_action
  const cfg = ACTION_CFG[actionCode] ?? ACTION_CFG.HOLD
  const scoreColor = astro.astro_score >= 20 ? T.green
    : astro.astro_score >= 0 ? T.blue
      : astro.astro_score >= -20 ? T.amber : T.red
  const statePlain = STATE_PLAIN[astro.planet_state] ?? { label: astro.planet_state, meaning: '', color: T.textSub }
  const moonPlain = PHASE_PLAIN[astro.moon_phase] ?? { label: astro.moon_phase, meaning: '', color: T.muted }
  const marketPlain = MARKET_PLAIN[astro.market_astro_signal] ?? { label: astro.market_astro_signal, color: T.muted }

  const aspects = parseAspects(astro.key_aspects, astro.primary_planet)
  const plainReason = astro.astro_reason || buildPlainReason(astro)
  const rulingList = astro.ruling_planets.split(',').map(s => s.trim()).filter(Boolean)

  return (
    <div style={{
      background: T.panel,
      border: `1px solid ${T.border}`,
      borderRadius: 8,
      padding: 16,
      marginBottom: 16,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
            <span style={{ color: T.muted, fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1.4, textTransform: 'uppercase' as const }}>
              AstroFinance Heuristic
            </span>
            <span style={{ color: T.muted, fontSize: FS.caption }}>{astro.as_of_date}</span>
          </div>
          <div style={{ color: T.textSub, fontSize: FS.body }}>
            Today's planetary context for <span style={{ color: T.text, fontWeight: FW.bold }}>{astro.sector}</span>{' '}
            <span style={{ color: T.muted, fontSize: FS.caption }}>sector stocks</span>
          </div>
        </div>
        <div style={{
          padding: '5px 14px',
          borderRadius: 5,
          background: cfg.bg,
          border: `1px solid ${cfg.border}`,
          color: cfg.color,
          fontSize: FS.label,
          fontWeight: FW.heavy,
          letterSpacing: 1,
          flexShrink: 0,
        }}>
          {actionLabel}
        </div>
      </div>

      <AstroScoreBar score={astro.astro_score} color={scoreColor} />

      <div style={{
        padding: '10px 14px',
        borderRadius: 5,
        background: `${cfg.color}0e`,
        border: `1px solid ${cfg.border}`,
        color: T.text,
        fontSize: FS.body,
        lineHeight: 1.65,
        marginBottom: 14,
      }}>
        {plainReason}
      </div>

      {astro.boundary_note && (
        <div style={{
          padding: '9px 12px',
          borderRadius: 6,
          marginBottom: 14,
          background: `${T.purple}0b`,
          border: `1px solid ${T.purple}22`,
          color: T.textSub,
          fontSize: FS.caption,
          lineHeight: 1.55,
        }}>
          {astro.boundary_note}
        </div>
      )}

      <SectionLabel text="Ruling Planet Today" />
      <div style={{
        padding: '10px 14px',
        borderRadius: 6,
        marginBottom: 10,
        background: T.cell,
        border: `1px solid ${statePlain.color}33`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
          <span style={{ color: T.text, fontSize: FS.body, fontWeight: FW.bold }}>
            {astro.primary_planet} in {astro.planet_sign}
          </span>
          <span style={{
            padding: '2px 9px',
            borderRadius: 10,
            fontSize: FS.caption,
            fontWeight: FW.bold,
            flexShrink: 0,
            marginLeft: 8,
            background: `${statePlain.color}18`,
            border: `1px solid ${statePlain.color}44`,
            color: statePlain.color,
          }}>
            {statePlain.label}
          </span>
        </div>
        <div style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>
          {statePlain.meaning}
        </div>
      </div>

      {aspects.length > 0 && (
        <>
          <SectionLabel text={`Influences on ${astro.primary_planet} Today`} />
          {aspects.map((aspect, index) => (
            <div key={index} style={{ display: 'flex', gap: 8, marginBottom: 7, alignItems: 'flex-start' }}>
              <span style={{ color: aspect.positive ? T.green : T.red, fontSize: FS.label, marginTop: 1, flexShrink: 0, fontWeight: FW.black }}>
                {aspect.positive ? '+' : '-'}
              </span>
              <span style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>{aspect.text}</span>
            </div>
          ))}
        </>
      )}

      <SectionLabel text="Moon & Market Conditions" />
      <div style={{
        padding: '10px 14px',
        borderRadius: 6,
        marginBottom: 10,
        background: T.cell,
        border: `1px solid ${T.border}`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
          <span style={{ color: T.muted, fontSize: FS.caption, flexShrink: 0, minWidth: 90 }}>Moon today</span>
          <div style={{ textAlign: 'right' }}>
            <span style={{ color: moonPlain.color, fontSize: FS.caption, fontWeight: FW.bold }}>{moonPlain.label}</span>
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

      <SectionLabel text={`Planets Governing ${astro.sector}`} />
      <div style={{ display: 'flex', flexWrap: 'wrap', marginBottom: 4 }}>
        {rulingList.map(planet => (
          <PlanetChip
            key={planet}
            name={planet}
            retrograde={
              (planet === astro.primary_planet && astro.planet_retrograde) ||
              (planet === 'Mercury' && astro.mercury_retrograde) ||
              (planet === 'Venus' && astro.venus_retrograde)
            }
          />
        ))}
      </div>

      {(astro.planet_retrograde || astro.mercury_retrograde || astro.venus_retrograde) && (
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
          {astro.planet_retrograde && astro.primary_planet !== 'Rahu' && astro.primary_planet !== 'Ketu' && (
            <div style={{ padding: '6px 10px', borderRadius: 4, background: '#F9731614', border: '1px solid #F9731644', color: '#F97316', fontSize: FS.caption, fontWeight: FW.bold }}>
              {astro.primary_planet} retrograde - the model reads that as a weaker momentum condition.
            </div>
          )}
          {astro.mercury_retrograde && (
            <div style={{ padding: '6px 10px', borderRadius: 4, background: '#F9731614', border: '1px solid #F9731644', color: '#F97316', fontSize: FS.caption }}>
              Mercury retrograde - the model associates this with communication friction and noisier sector signals.
            </div>
          )}
          {astro.venus_retrograde && (
            <div style={{ padding: '6px 10px', borderRadius: 4, background: '#F9731614', border: '1px solid #F9731644', color: '#F97316', fontSize: FS.caption }}>
              Venus retrograde - FMCG, luxury, and auto names can see a weaker AstroFinance backdrop.
            </div>
          )}
        </div>
      )}

      {astro.eclipse_active && (
        <div style={{
          marginTop: 8,
          padding: '6px 10px',
          borderRadius: 4,
          background: `${T.amber}14`,
          border: `1px solid ${T.amber}44`,
          color: T.amber,
          fontSize: FS.caption,
          fontWeight: FW.bold,
          letterSpacing: 0.4,
        }}>
          ECLIPSE ACTIVE - the model marks this as a higher-volatility heuristic regime.
        </div>
      )}
      {astro.reversal_note && (
        <div style={{
          marginTop: 6,
          padding: '6px 10px',
          borderRadius: 4,
          background: `${T.amber}0e`,
          border: `1px solid ${T.amber}33`,
          color: T.textSub,
          fontSize: FS.caption,
          lineHeight: 1.5,
        }}>
          {astro.reversal_note}
        </div>
      )}

      <div style={{
        marginTop: 14,
        padding: '12px 14px',
        borderRadius: 6,
        background: `${T.blue}09`,
        border: `1px solid ${T.blue}20`,
      }}>
        <div style={{
          fontSize: FS.caption,
          color: T.blue,
          fontWeight: FW.heavy,
          letterSpacing: 1,
          textTransform: 'uppercase' as const,
          marginBottom: 6,
        }}>
          What this score measures
        </div>
        <div style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.6, marginBottom: 8 }}>
          This is a <span style={{ color: T.text, fontWeight: FW.bold }}>real-time sector-level heuristic</span> based on the planets that the model maps to {astro.sector}. It updates daily as planetary positions change.
        </div>
        <div style={{
          fontSize: FS.body,
          color: T.textSub,
          lineHeight: 1.6,
          paddingTop: 8,
          borderTop: `1px solid ${T.border}`,
        }}>
          <span style={{ color: T.amber, fontWeight: FW.bold }}>Why this may differ from the Kundli score:</span>{' '}
          The Kundli score is based on a company's natal chart at IPO and stays fixed. This AstroFinance score is a daily sector backdrop. Both are context layers, and neither replaces technical or fundamental analysis.
        </div>
      </div>

      <div style={{ color: T.muted, fontSize: FS.caption, borderTop: `1px solid ${T.border}`, paddingTop: 8, marginTop: 12 }}>
        Evidence class: {astro.evidence_class ?? 'INTERNAL_HEURISTIC'} / Source status: {astro.source_status ?? 'UNVERIFIED'}.
      </div>
    </div>
  )
}
