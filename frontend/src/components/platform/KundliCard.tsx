/**
 * KundliCard — Phase KU-5
 * Vedic natal chart + Gann analysis card.
 * Uses platform design tokens (T / FS / FW) throughout.
 *
 * Tabs: Overview | Planets | Houses | Dasha | Gann | Report
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { T, FS, FW } from '../../styles/tokens'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Planet {
  longitude:       number
  sign:            string
  sign_num:        number
  degree:          number
  house:           number
  nakshatra:       string
  pada:            number
  nakshatra_lord:  string
  dignity:         string
  retrograde:      boolean
}

interface DashaEntry {
  planet:     string
  start_date: string
  end_date:   string
}

interface HouseData {
  sign:          string
  lord:          string
  lord_house:    number | null
  lord_dignity:  string
  occupants:     string[]
  strength:      string
  signification: string
}

interface Yoga {
  name:   string
  effect: string
  score:  number
  signal: string
}

interface KundliData {
  entity:   { type: string; name: string; inception_date: string; inception_time: string }
  lagna:    { sign: string; degree: number; lord: string; full_longitude: number }
  planets:  Record<string, Planet>
  current_dasha: {
    mahadasha:       DashaEntry
    antardasha:      DashaEntry
    pratyantardasha: DashaEntry
    all_mahadashas:  DashaEntry[]
  }
  financial_houses: Record<string, HouseData>
  yogas:            Yoga[]
  transits:         Record<string, { current_sign: string; natal_sign: string; aspect: string }>
  astro_score:      number
  astro_action:     string
  computed_date:    string
}

interface GannData {
  square_of_9: {
    current_degree: number
    nearest_angle:  string
    levels:         Record<string, { angle: number; resistances: number[]; supports: number[]; is_nearest: boolean }>
  }
  gann_levels: {
    resistance: number[]
    support:    number[]
    key_r1:     number | null
    key_s1:     number | null
  }
  time_cycles: {
    current_sun_degree: number
    fixed_future_dates: Record<string, string>
  }
  planetary_lines: Record<string, { longitude: number; base_price: number }>
}

interface Interpretation {
  signal:          string
  astro_score:     number
  bullish_factors: string[]
  bearish_factors: string[]
  dasha_outlook:   Array<{ period: string; start: string; end: string; outlook: string }>
  narrative:       string
  yogas:           string[]
}

interface KundliResponse {
  symbol:         string
  exchange:       string
  kundli:         KundliData
  gann:           GannData | null
  interpretation: Interpretation
}

// ── Design constants ──────────────────────────────────────────────────────────

const ACTION_CFG: Record<string, { color: string; bg: string; border: string }> = {
  STRONG_BUY: { color: T.green,   bg: `${T.green}14`,   border: `${T.green}55`   },
  BUY:        { color: T.green,   bg: `${T.green}14`,   border: `${T.green}55`   },
  HOLD:       { color: T.blue,    bg: `${T.blue}14`,    border: `${T.blue}55`    },
  CAUTION:    { color: T.amber,   bg: `${T.amber}14`,   border: `${T.amber}55`   },
  EXIT:       { color: '#F97316', bg: '#F9731614',       border: '#F9731655'      },
  AVOID:      { color: T.red,     bg: `${T.red}14`,     border: `${T.red}55`     },
}

const DIGNITY_COLOR: Record<string, string> = {
  exalted_exact: T.green,
  exalted:       T.green,
  moolatrikona:  T.teal,
  own_sign:      T.blue,
  friendly:      T.textSub,
  neutral:       T.muted,
  enemy:         T.amber,
  debilitated:   T.red,
}

const HOUSE_STRENGTH_COLOR: Record<string, string> = {
  strong:            T.green,
  'moderate-strong': T.blue,
  moderate:          T.textSub,
  weak:              T.red,
}

const YOGA_SIGNAL_COLOR: Record<string, string> = {
  BUY: T.green, HOLD: T.blue, CAUTION: T.amber, EXIT: '#F97316', AVOID: T.red,
}

const DASHA_COLOR: Record<string, string> = {
  Sun: T.amber, Moon: T.blue, Mars: T.red, Mercury: T.green,
  Jupiter: T.teal, Venus: T.purple, Saturn: '#F97316',
  Rahu: '#E879F9', Ketu: T.muted,
}

const PLANET_ORDER = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Rahu','Ketu']

const TABS = ['Overview', 'Planets', 'Houses', 'Dasha', 'Gann', 'Report'] as const
type Tab = (typeof TABS)[number]

// ── Shared sub-components ─────────────────────────────────────────────────────

function SectionLabel({ text }: { text: string }) {
  return (
    <div style={{
      fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1.4,
      textTransform: 'uppercase' as const,
      color: T.muted,
      borderBottom: `1px solid ${T.border}`,
      paddingBottom: 5, marginBottom: 8, marginTop: 14,
    }}>
      {text}
    </div>
  )
}

function InfoRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 7 }}>
      <span style={{ color: T.muted, fontSize: FS.caption, flexShrink: 0, minWidth: 120 }}>{label}</span>
      <span style={{ color: valueColor ?? T.textSub, fontSize: FS.caption, fontWeight: FW.medium, textAlign: 'right', maxWidth: '55%' }}>
        {value}
      </span>
    </div>
  )
}

function Tag({ text, color }: { text: string; color: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '3px 8px', borderRadius: 10,
      fontSize: FS.caption, fontWeight: FW.bold,
      background: `${color}18`, border: `1px solid ${color}44`, color,
      letterSpacing: 0.4, marginRight: 4, marginBottom: 4,
    }}>
      {text}
    </span>
  )
}

function ScoreBar({ score }: { score: number }) {
  const color   = score >= 30 ? T.green : score >= 5 ? T.blue : score >= -10 ? T.amber : T.red
  const absPct  = Math.min(50, Math.abs(score) / 100 * 50)   // 0–50% from centre
  const positive = score >= 0
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ color: T.muted, fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 0.8, textTransform: 'uppercase' as const }}>
          Astro Score
        </span>
        <span style={{ color, fontSize: FS.label, fontWeight: FW.heavy, fontVariantNumeric: 'tabular-nums' }}>
          {score > 0 ? '+' : ''}{score.toFixed(0)}
        </span>
      </div>
      {/* Diverging bar — 0 at centre; negative fills left, positive fills right */}
      <div style={{ height: 5, background: T.border, borderRadius: 3, position: 'relative', overflow: 'hidden' }}>
        {/* centre tick */}
        <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: T.borderHi, zIndex: 1 }} />
        {/* fill */}
        {positive ? (
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: `${absPct}%`, background: color, borderRadius: '0 3px 3px 0', transition: 'width 0.5s ease' }} />
        ) : (
          <div style={{ position: 'absolute', right: '50%', top: 0, bottom: 0, width: `${absPct}%`, background: color, borderRadius: '3px 0 0 3px', transition: 'width 0.5s ease' }} />
        )}
      </div>
      {/* axis labels */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
        <span style={{ color: T.muted, fontSize: FS.caption }}>−100</span>
        <span style={{ color: T.muted, fontSize: FS.caption }}>0</span>
        <span style={{ color: T.muted, fontSize: FS.caption }}>+100</span>
      </div>
    </div>
  )
}

// ── Tab content ───────────────────────────────────────────────────────────────

function OverviewTab({ kundli, interp }: { kundli: KundliData; interp: Interpretation }) {
  const lagna = kundli.lagna
  const dasha = kundli.current_dasha
  const moon  = kundli.planets['Moon']
  const jup   = kundli.planets['Jupiter']

  return (
    <div>
      <SectionLabel text="Lagna (Ascendant)" />
      <InfoRow label="Rising sign"    value={`${lagna.sign}  ${lagna.degree.toFixed(1)}°`}       valueColor={T.text} />
      <InfoRow label="Lagna lord"     value={lagna.lord}                                           valueColor={T.blue} />
      <InfoRow label="Inception date" value={`${kundli.entity.inception_date}  ${kundli.entity.inception_time}`} />

      <SectionLabel text="Current Dasha Period" />
      <InfoRow label="Mahadasha"       value={`${dasha.mahadasha.planet}  until ${dasha.mahadasha.end_date}`}       valueColor={T.amber} />
      <InfoRow label="Antardasha"      value={`${dasha.antardasha.planet}  until ${dasha.antardasha.end_date}`}      valueColor={T.textSub} />
      <InfoRow label="Pratyantardasha" value={`${dasha.pratyantardasha.planet}  until ${dasha.pratyantardasha.end_date}`} />

      <SectionLabel text="Key Planets" />
      {moon && (
        <InfoRow
          label="Moon (sentiment)"
          value={`${moon.sign}  H${moon.house}  —  ${moon.nakshatra} Pada ${moon.pada}`}
          valueColor={DIGNITY_COLOR[moon.dignity] ?? T.textSub}
        />
      )}
      {jup && (
        <InfoRow
          label="Jupiter (growth)"
          value={`${jup.sign}  H${jup.house}  —  ${jup.dignity.replace(/_/g,' ')}`}
          valueColor={DIGNITY_COLOR[jup.dignity] ?? T.textSub}
        />
      )}

      {kundli.yogas.length > 0 && (
        <>
          <SectionLabel text="Active Yogas" />
          <div style={{ display: 'flex', flexWrap: 'wrap', marginBottom: 4 }}>
            {kundli.yogas.map((y, i) => (
              <Tag key={i} text={y.name} color={YOGA_SIGNAL_COLOR[y.signal] ?? T.textSub} />
            ))}
          </div>
        </>
      )}

      <SectionLabel text="Financial Interpretation" />
      {interp.bullish_factors.slice(0, 4).map((f, i) => (
        <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'flex-start' }}>
          <span style={{ color: T.green, fontSize: FS.label, marginTop: 1, flexShrink: 0 }}>+</span>
          <span style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>{f}</span>
        </div>
      ))}
      {interp.bearish_factors.slice(0, 2).map((f, i) => (
        <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'flex-start' }}>
          <span style={{ color: T.red, fontSize: FS.label, marginTop: 1, flexShrink: 0 }}>−</span>
          <span style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>{f}</span>
        </div>
      ))}

      {/* Context: what the Kundli score measures vs AstroSignal */}
      <div style={{
        marginTop: 14, padding: '12px 14px', borderRadius: 6,
        background: `${T.purple}09`, border: `1px solid ${T.purple}20`,
      }}>
        <div style={{
          fontSize: FS.caption, color: T.purple, fontWeight: FW.heavy,
          letterSpacing: 1, textTransform: 'uppercase' as const, marginBottom: 6,
        }}>
          What the Kundli score measures
        </div>
        <div style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.6, marginBottom: 8 }}>
          This score is based on the company's <span style={{ color: T.text, fontWeight: FW.bold }}>natal birth chart</span> — the exact planetary positions at the time of its IPO ({kundli.entity.inception_date}). It reflects the intrinsic astrological quality of the company's founding moment and is a fixed, stock-specific reading.
        </div>
        <div style={{
          fontSize: FS.body, color: T.textSub, lineHeight: 1.6,
          paddingTop: 8, borderTop: `1px solid ${T.border}`,
        }}>
          <span style={{ color: T.amber, fontWeight: FW.bold }}>Why this may differ from the Astro Signal score:</span>
          {' '}The Astro Signal card (above) measures today's planetary positions for the sector's ruling planets — a dynamic, daily reading that applies equally to all stocks in the sector. This Kundli score reflects only this company's natal planetary configuration and does not change day to day. A company can have a strong natal chart yet face a weak sector planetary period today, or vice versa. Both are valid and complementary.
        </div>
      </div>
    </div>
  )
}

function PlanetsTab({ planets }: { planets: Record<string, Planet> }) {
  const listed = PLANET_ORDER.filter(p => planets[p])
  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: FS.body }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${T.border}` }}>
              {['Planet','Sign','H','Nakshatra','Pd','Dignity','R'].map(h => (
                <th key={h} style={{
                  padding: '5px 8px', textAlign: 'left',
                  color: T.muted, fontSize: FS.caption, fontWeight: FW.bold, letterSpacing: 0.5,
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {listed.map(name => {
              const p  = planets[name]
              const dc = DIGNITY_COLOR[p.dignity] ?? T.textSub
              return (
                <tr key={name} style={{ borderBottom: `1px solid ${T.border}33` }}>
                  <td style={{ padding: '6px 8px', color: T.text, fontWeight: FW.bold }}>{name}</td>
                  <td style={{ padding: '6px 8px', color: T.textSub }}>
                    {p.sign}
                    <span style={{ color: T.muted, fontSize: FS.caption }}> {p.degree.toFixed(1)}</span>
                  </td>
                  <td style={{ padding: '6px 8px', color: T.textSub, fontVariantNumeric: 'tabular-nums' }}>H{p.house}</td>
                  <td style={{ padding: '6px 8px', color: T.muted,   fontSize: FS.caption }}>{p.nakshatra}</td>
                  <td style={{ padding: '6px 8px', color: T.muted,   fontSize: FS.caption }}>{p.pada}</td>
                  <td style={{ padding: '6px 8px' }}>
                    <span style={{ color: dc, fontSize: FS.caption, fontWeight: FW.bold }}>
                      {p.dignity.replace(/_/g,' ')}
                    </span>
                  </td>
                  <td style={{ padding: '6px 8px', color: p.retrograde ? '#F97316' : T.border, fontSize: FS.caption, fontWeight: p.retrograde ? FW.heavy : FW.regular }}>
                    {p.retrograde ? 'R' : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <SectionLabel text="D9 Navamsa — Core Destiny Chart" />
      <p style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.55, margin: 0 }}>
        The Navamsa chart reveals the deeper karmic structure of the entity's purpose.
        It is considered the most important divisional chart for qualitative assessment.
      </p>
    </div>
  )
}

function HousesTab({ houses }: { houses: Record<string, HouseData> }) {
  const HOUSE_LABELS: Record<string, string> = {
    '2H':  '2nd House  —  Wealth / Balance Sheet',
    '5H':  '5th House  —  Speculation / R&D',
    '8H':  '8th House  —  Volatility / M&A Events',
    '10H': '10th House  —  Management / Reputation',
    '11H': '11th House  —  Revenue / Profits',
  }
  return (
    <div>
      <p style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5, margin: '0 0 12px' }}>
        Financial houses show the operational strength of key corporate areas.
      </p>
      {['2H','5H','8H','10H','11H'].map(hk => {
        const h = houses[hk]
        if (!h) return null
        const sc = HOUSE_STRENGTH_COLOR[h.strength] ?? T.textSub
        return (
          <div key={hk} style={{
            marginBottom: 10, padding: '10px 14px', borderRadius: 6,
            background: T.cell, border: `1px solid ${T.border}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: FS.body, fontWeight: FW.bold, color: T.text }}>
                {HOUSE_LABELS[hk] ?? hk}
              </span>
              <span style={{
                padding: '2px 9px', borderRadius: 10,
                fontSize: FS.caption, fontWeight: FW.bold,
                background: `${sc}18`, border: `1px solid ${sc}44`, color: sc,
                letterSpacing: 0.4, flexShrink: 0, marginLeft: 8,
              }}>
                {h.strength.replace(/-/g,' ')}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 4 }}>
              <span style={{ fontSize: FS.caption, color: T.muted }}>
                Sign: <span style={{ color: T.textSub }}>{h.sign}</span>
              </span>
              <span style={{ fontSize: FS.caption, color: T.muted }}>
                Lord: <span style={{ color: DIGNITY_COLOR[h.lord_dignity] ?? T.textSub, fontWeight: FW.bold }}>{h.lord}</span>
                {h.lord_house && <span style={{ color: T.muted }}> in H{h.lord_house}</span>}
              </span>
              {h.occupants.length > 0 && (
                <span style={{ fontSize: FS.caption, color: T.muted }}>
                  Occupants: <span style={{ color: T.blue }}>{h.occupants.join(', ')}</span>
                </span>
              )}
            </div>
            <div style={{ fontSize: FS.caption, color: T.muted }}>{h.signification}</div>
          </div>
        )
      })}
    </div>
  )
}

function DashaTab({ dasha, interp }: { dasha: KundliData['current_dasha']; interp: Interpretation }) {
  return (
    <div>
      <SectionLabel text="Current Period" />
      {[
        { label: 'Mahadasha (major period)',       d: dasha.mahadasha        },
        { label: 'Antardasha (sub-period)',         d: dasha.antardasha       },
        { label: 'Pratyantardasha (micro-period)', d: dasha.pratyantardasha  },
      ].map(({ label, d }) => {
        const c = DASHA_COLOR[d.planet] ?? T.textSub
        return (
          <div key={label} style={{
            marginBottom: 8, padding: '10px 14px', borderRadius: 6,
            background: T.cell, border: `1px solid ${T.border}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: FS.caption, color: T.muted }}>{label}</span>
              <span style={{ fontSize: FS.md, fontWeight: FW.heavy, color: c }}>{d.planet}</span>
            </div>
            <div style={{ fontSize: FS.caption, color: T.muted, marginTop: 3 }}>
              {d.start_date}  —  {d.end_date}
            </div>
          </div>
        )
      })}

      <SectionLabel text="Dasha Outlook" />
      {interp.dasha_outlook.map((outlook, i) => (
        <div key={i} style={{
          marginBottom: 8, padding: '9px 14px', borderRadius: 6,
          background: T.cell, border: `1px solid ${T.border}`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: FS.body, fontWeight: FW.bold, color: T.text }}>{outlook.period}</span>
            <span style={{ fontSize: FS.caption, color: T.muted }}>{outlook.start?.slice(0,4)}–{outlook.end?.slice(0,4)}</span>
          </div>
          {outlook.outlook && (
            <div style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.45 }}>{outlook.outlook}</div>
          )}
        </div>
      ))}

      <SectionLabel text="Mahadasha Timeline" />
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${T.border}` }}>
              <th style={{ padding: '4px 8px', textAlign: 'left', color: T.muted, fontSize: FS.caption, fontWeight: FW.bold }}>Planet</th>
              <th style={{ padding: '4px 8px', textAlign: 'left', color: T.muted, fontSize: FS.caption, fontWeight: FW.bold }}>Start</th>
              <th style={{ padding: '4px 8px', textAlign: 'left', color: T.muted, fontSize: FS.caption, fontWeight: FW.bold }}>End</th>
            </tr>
          </thead>
          <tbody>
            {dasha.all_mahadashas.slice(0, 9).map((m, i) => {
              const c       = DASHA_COLOR[m.planet] ?? T.textSub
              const nowYear = new Date().getFullYear()
              const sYear   = parseInt(m.start_date?.slice(0,4) ?? '0')
              const eYear   = parseInt(m.end_date?.slice(0,4) ?? '9999')
              const active  = sYear <= nowYear && nowYear <= eYear
              return (
                <tr key={i} style={{
                  background: active ? `${T.green}0a` : 'transparent',
                  borderBottom: `1px solid ${T.border}22`,
                }}>
                  <td style={{ padding: '5px 8px', color: c, fontWeight: active ? FW.heavy : FW.regular }}>
                    {m.planet}{active ? '  ◀' : ''}
                  </td>
                  <td style={{ padding: '5px 8px', color: T.textSub, fontSize: FS.caption, fontVariantNumeric: 'tabular-nums' }}>{m.start_date?.slice(0,7)}</td>
                  <td style={{ padding: '5px 8px', color: T.textSub, fontSize: FS.caption, fontVariantNumeric: 'tabular-nums' }}>{m.end_date?.slice(0,7)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function GannTab({ gann }: { gann: GannData | null }) {
  if (!gann) {
    return (
      <div style={{ color: T.muted, fontSize: FS.body, padding: '24px 0', textAlign: 'center' }}>
        Gann data not available for this symbol.
      </div>
    )
  }
  const so9    = gann.square_of_9
  const levels = gann.gann_levels
  const cycles = gann.time_cycles
  const plines = gann.planetary_lines

  return (
    <div>
      <SectionLabel text="Square of 9" />
      <InfoRow label="Price degree"     value={`${so9.current_degree.toFixed(1)}°`} valueColor={T.amber} />
      <InfoRow label="Nearest cardinal" value={so9.nearest_angle}                   valueColor={T.blue}  />

      <SectionLabel text="Key Price Levels" />
      <div style={{ display: 'flex', gap: 10 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: FS.caption, color: T.muted, marginBottom: 6, fontWeight: FW.bold, textTransform: 'uppercase' as const, letterSpacing: 0.8 }}>
            Resistance
          </div>
          {levels.resistance.map((r, i) => (
            <div key={i} style={{
              padding: '5px 10px', borderRadius: 4, marginBottom: 4,
              background: `${T.red}0e`, border: `1px solid ${T.red}33`,
              color: T.red, fontSize: FS.body, fontWeight: FW.bold,
              fontVariantNumeric: 'tabular-nums', textAlign: 'right',
            }}>
              {r.toFixed(2)}
            </div>
          ))}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: FS.caption, color: T.muted, marginBottom: 6, fontWeight: FW.bold, textTransform: 'uppercase' as const, letterSpacing: 0.8 }}>
            Support
          </div>
          {levels.support.map((s, i) => (
            <div key={i} style={{
              padding: '5px 10px', borderRadius: 4, marginBottom: 4,
              background: `${T.green}0e`, border: `1px solid ${T.green}33`,
              color: T.green, fontSize: FS.body, fontWeight: FW.bold,
              fontVariantNumeric: 'tabular-nums', textAlign: 'right',
            }}>
              {s.toFixed(2)}
            </div>
          ))}
        </div>
      </div>

      <SectionLabel text="Solar Time Cycles" />
      <InfoRow label="Sun position" value={`${cycles.current_sun_degree.toFixed(1)}° sidereal`} />
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
        {Object.entries(cycles.fixed_future_dates).map(([label, date]) => (
          <div key={label} style={{
            padding: '5px 10px', borderRadius: 5,
            background: T.cell, border: `1px solid ${T.border}`,
          }}>
            <span style={{ fontSize: FS.caption, color: T.muted }}>{label}  </span>
            <span style={{ fontSize: FS.caption, color: T.textSub, fontVariantNumeric: 'tabular-nums', fontWeight: FW.bold }}>{date}</span>
          </div>
        ))}
      </div>

      <SectionLabel text="Planetary Price Lines  (1× factor)" />
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${T.border}` }}>
              <th style={{ padding: '4px 8px', textAlign: 'left',  color: T.muted, fontSize: FS.caption, fontWeight: FW.bold }}>Planet</th>
              <th style={{ padding: '4px 8px', textAlign: 'right', color: T.muted, fontSize: FS.caption, fontWeight: FW.bold }}>Longitude</th>
              <th style={{ padding: '4px 8px', textAlign: 'right', color: T.muted, fontSize: FS.caption, fontWeight: FW.bold }}>Base Price</th>
            </tr>
          </thead>
          <tbody>
            {['Sun','Moon','Mars','Jupiter','Saturn','Venus','Mercury'].map(planet => {
              const pl = plines?.[planet]
              if (!pl) return null
              return (
                <tr key={planet} style={{ borderBottom: `1px solid ${T.border}11` }}>
                  <td style={{ padding: '5px 8px', color: T.textSub, fontSize: FS.body }}>{planet}</td>
                  <td style={{ padding: '5px 8px', color: T.muted,   fontSize: FS.caption, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{pl.longitude.toFixed(1)}</td>
                  <td style={{ padding: '5px 8px', color: T.amber,   fontSize: FS.body,    textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: FW.bold }}>{pl.base_price.toFixed(1)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ReportTab({ kundli, interp }: { kundli: KundliData; interp: Interpretation }) {
  const cfg = ACTION_CFG[interp.signal] ?? ACTION_CFG.HOLD
  const scoreColor = interp.astro_score >= 30 ? T.green : interp.astro_score >= 5 ? T.blue : interp.astro_score >= -10 ? T.amber : T.red

  return (
    <div>
      <SectionLabel text="Financial Signal" />
      <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
        <div style={{
          flex: 1, padding: '14px', borderRadius: 6,
          background: T.cell, border: `1px solid ${T.border}`,
          display: 'flex', flexDirection: 'column', alignItems: 'center',
        }}>
          <span style={{ fontSize: FS.caption, color: T.muted, marginBottom: 5, letterSpacing: 0.8, textTransform: 'uppercase' as const }}>Vedic Signal</span>
          <span style={{ fontSize: FS['2xl'], fontWeight: FW.black, color: cfg.color }}>{interp.signal}</span>
        </div>
        <div style={{
          flex: 1, padding: '14px', borderRadius: 6,
          background: T.cell, border: `1px solid ${T.border}`,
          display: 'flex', flexDirection: 'column', alignItems: 'center',
        }}>
          <span style={{ fontSize: FS.caption, color: T.muted, marginBottom: 5, letterSpacing: 0.8, textTransform: 'uppercase' as const }}>Astro Score</span>
          <span style={{ fontSize: FS['2xl'], fontWeight: FW.black, color: scoreColor, fontVariantNumeric: 'tabular-nums' }}>
            {interp.astro_score > 0 ? '+' : ''}{interp.astro_score.toFixed(0)}
          </span>
        </div>
      </div>

      {interp.narrative && (
        <div style={{
          padding: '12px 14px', borderRadius: 6, marginBottom: 14,
          background: T.cell, border: `1px solid ${T.border}`,
          color: T.textSub, fontSize: FS.body, lineHeight: 1.6,
        }}>
          {interp.narrative}
        </div>
      )}

      <SectionLabel text="Bullish Factors" />
      {interp.bullish_factors.map((f, i) => (
        <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 7, alignItems: 'flex-start' }}>
          <span style={{ color: T.green, fontSize: FS.label, marginTop: 1, flexShrink: 0, fontWeight: FW.black }}>+</span>
          <span style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>{f}</span>
        </div>
      ))}

      {interp.bearish_factors.length > 0 && (
        <>
          <SectionLabel text="Bearish Factors" />
          {interp.bearish_factors.map((f, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 7, alignItems: 'flex-start' }}>
              <span style={{ color: T.red, fontSize: FS.label, marginTop: 1, flexShrink: 0, fontWeight: FW.black }}>−</span>
              <span style={{ fontSize: FS.body, color: T.textSub, lineHeight: 1.5 }}>{f}</span>
            </div>
          ))}
        </>
      )}

      {interp.yogas && interp.yogas.length > 0 && (
        <>
          <SectionLabel text="Active Yogas" />
          <div style={{ display: 'flex', flexWrap: 'wrap' }}>
            {interp.yogas.map((y, i) => <Tag key={i} text={y} color={T.purple} />)}
          </div>
        </>
      )}

      <div style={{
        color: T.muted, fontSize: FS.caption,
        borderTop: `1px solid ${T.border}`, paddingTop: 10, marginTop: 14, lineHeight: 1.5,
      }}>
        Computed: {kundli.computed_date}. Uses Swiss Ephemeris with Lahiri ayanamsha + Whole Sign houses.
        Supplementary to technical and fundamental analysis.
      </div>
    </div>
  )
}

// ── Main Card ─────────────────────────────────────────────────────────────────

export function KundliCard({ symbol }: { symbol: string }) {
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const [expanded,  setExpanded]  = useState(false)

  const { data, isLoading, error } = useQuery<KundliResponse>({
    queryKey: ['kundli', symbol],
    queryFn:  () => api.get(`/stocks/${symbol}/kundli?include_gann=true&generate_narrative=false`).then(r => r.data),
    staleTime: 3_600_000,
    retry: false,
    enabled: expanded,
  })

  const signal   = data?.interpretation?.signal
  const actionCfg = ACTION_CFG[signal ?? ''] ?? ACTION_CFG.HOLD

  return (
    <div style={{
      background: T.panel, border: `1px solid ${T.border}`, borderRadius: 8, marginBottom: 16,
    }}>
      {/* ── Collapsed header (always visible) ── */}
      <div
        role="button"
        onClick={() => setExpanded(e => !e)}
        style={{ padding: '11px 16px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{ color: T.muted, fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1.4, textTransform: 'uppercase' as const }}>
              Vedic Kundli + Gann
            </span>
            <span style={{ color: T.muted, fontSize: FS.caption }}>IPO natal chart analysis</span>
          </div>
          {data && (
            <div style={{ color: T.muted, fontSize: FS.caption }}>
              Lagna: <span style={{ color: T.textSub, fontWeight: FW.bold }}>{data.kundli.lagna.sign}</span>
              {'  |  '}
              Mahadasha: <span style={{ color: T.amber, fontWeight: FW.bold }}>{data.kundli.current_dasha.mahadasha.planet}</span>
              {' until '}
              <span style={{ color: T.muted }}>{data.kundli.current_dasha.mahadasha.end_date}</span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {data && (
            <div style={{
              padding: '4px 12px', borderRadius: 5,
              background: actionCfg.bg, border: `1px solid ${actionCfg.border}`,
              color: actionCfg.color, fontSize: FS.label, fontWeight: FW.heavy,
            }}>
              {signal}
            </div>
          )}
          <span style={{ color: T.muted, fontSize: FS.label, fontWeight: FW.bold }}>
            {expanded ? '▲' : '▼'}
          </span>
        </div>
      </div>

      {/* ── Expanded content ── */}
      {expanded && (
        <div style={{ borderTop: `1px solid ${T.border}`, padding: '14px 16px' }}>
          {isLoading && (
            <div style={{ color: T.muted, fontSize: FS.body, padding: '24px 0', textAlign: 'center' }}>
              Computing Kundli…
            </div>
          )}

          {error && (
            <div style={{
              color: T.red, fontSize: FS.body, padding: '10px 14px', borderRadius: 5,
              background: `${T.red}0e`, border: `1px solid ${T.red}33`,
            }}>
              Failed to load Kundli. Check that the backend is running and the symbol exists in equity_master.
            </div>
          )}

          {data && (
            <>
              <ScoreBar score={data.interpretation?.astro_score ?? data.kundli.astro_score} />

              {/* Tab bar */}
              <div style={{ display: 'flex', borderBottom: `1px solid ${T.border}`, marginBottom: 14, overflowX: 'auto' }}>
                {TABS.map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      padding: '7px 12px',
                      fontSize: FS.caption, fontWeight: FW.bold, letterSpacing: 0.6,
                      textTransform: 'uppercase' as const,
                      color: activeTab === tab ? T.text : T.muted,
                      borderBottom: activeTab === tab ? `2px solid ${T.blue}` : '2px solid transparent',
                      marginBottom: -1, flexShrink: 0, transition: 'color 0.15s',
                    }}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {activeTab === 'Overview'  && <OverviewTab  kundli={data.kundli} interp={data.interpretation} />}
              {activeTab === 'Planets'   && <PlanetsTab   planets={data.kundli.planets} />}
              {activeTab === 'Houses'    && <HousesTab    houses={data.kundli.financial_houses} />}
              {activeTab === 'Dasha'     && <DashaTab     dasha={data.kundli.current_dasha} interp={data.interpretation} />}
              {activeTab === 'Gann'      && <GannTab      gann={data.gann} />}
              {activeTab === 'Report'    && <ReportTab    kundli={data.kundli} interp={data.interpretation} />}
            </>
          )}
        </div>
      )}
    </div>
  )
}
