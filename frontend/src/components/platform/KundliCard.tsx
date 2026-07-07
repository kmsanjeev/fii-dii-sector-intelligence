/**
 * KundliCard — Phase KU-5
 * Vedic natal chart + Gann analysis for a stock (fetched on-demand from /api/stocks/{symbol}/kundli).
 *
 * Tabs: Overview | Planets | Houses | Dasha | Gann | Report
 * Uses the same dark design language as AstroSignalCard.
 */

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Planet {
  longitude:      number
  sign:           string
  sign_num:       number
  degree:         number
  house:          number
  nakshatra:      string
  pada:           number
  nakshatra_lord: string
  dignity:        string
  retrograde:     boolean
}

interface DashaEntry {
  planet:     string
  start_date: string
  end_date:   string
}

interface HouseData {
  sign:         string
  lord:         string
  lord_house:   number | null
  lord_dignity: string
  occupants:    string[]
  strength:     string
  signification: string
}

interface Yoga {
  name:    string
  effect:  string
  score:   number
  signal:  string
}

interface KundliData {
  entity:   { type: string; name: string; inception_date: string; inception_time: string }
  lagna:    { sign: string; degree: number; lord: string; full_longitude: number }
  planets:  Record<string, Planet>
  current_dasha: {
    mahadasha:        DashaEntry
    antardasha:       DashaEntry
    pratyantardasha:  DashaEntry
    all_mahadashas:   DashaEntry[]
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
  planetary_lines: Record<string, { longitude: number; base_price: number; quadrant_levels?: number[] }>
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

// ── Colors ────────────────────────────────────────────────────────────────────

const C = {
  bg:      '#0D1117',
  border:  '#1E2332',
  text:    '#E2E8F0',
  sub:     '#94A3B8',
  dim:     '#475569',
  dimmer:  '#1E2D3D',
  green:   '#4ADE80',
  blue:    '#60A5FA',
  amber:   '#FBBF24',
  orange:  '#F97316',
  red:     '#F87171',
  purple:  '#C084FC',
  teal:    '#2DD4BF',
}

const ACTION_CFG: Record<string, { color: string; bg: string; border: string }> = {
  STRONG_BUY: { color: '#4ADE80', bg: '#022c22', border: '#059669' },
  BUY:        { color: '#4ADE80', bg: '#052e16', border: '#16a34a' },
  HOLD:       { color: '#60A5FA', bg: '#0c1a2e', border: '#2563eb' },
  CAUTION:    { color: '#FBBF24', bg: '#1c1500', border: '#d97706' },
  EXIT:       { color: '#F97316', bg: '#1c0a00', border: '#ea580c' },
  AVOID:      { color: '#F87171', bg: '#1c0000', border: '#dc2626' },
}

const DIGNITY_COLOR: Record<string, string> = {
  exalted_exact: '#4ADE80', exalted: '#4ADE80', moolatrikona: '#2DD4BF',
  own_sign: '#60A5FA', friendly: '#94A3B8', neutral: '#475569',
  enemy: '#FBBF24', debilitated: '#F87171',
}

const HOUSE_STRENGTH_COLOR: Record<string, string> = {
  strong:          '#4ADE80',
  'moderate-strong': '#60A5FA',
  moderate:        '#94A3B8',
  weak:            '#F87171',
}

const SIGNAL_YOGA: Record<string, string> = {
  BUY: C.green, HOLD: C.blue, CAUTION: C.amber, EXIT: C.orange, AVOID: C.red,
}

// ── Tabs ──────────────────────────────────────────────────────────────────────

const TABS = ['Overview', 'Planets', 'Houses', 'Dasha', 'Gann', 'Report'] as const
type Tab = (typeof TABS)[number]

// ── Sub-components ────────────────────────────────────────────────────────────

function InfoRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
      <span style={{ color: C.dim, fontSize: 10, flexShrink: 0, minWidth: 100 }}>{label}</span>
      <span style={{ color: valueColor ?? C.sub, fontSize: 10, fontWeight: 600, textAlign: 'right', maxWidth: '55%' }}>
        {value}
      </span>
    </div>
  )
}

function ScoreBar({ score, label }: { score: number; label?: string }) {
  const pct   = Math.min(100, Math.max(0, (score + 100) / 2))
  const color = score >= 30 ? C.green : score >= 5 ? C.blue : score >= -10 ? C.amber : C.red
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ color: C.dim, fontSize: 9, letterSpacing: 0.5 }}>{label ?? 'ASTRO SCORE'}</span>
        <span style={{ color, fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
          {score > 0 ? '+' : ''}{score.toFixed(0)}
        </span>
      </div>
      <div style={{ height: 4, background: '#1E2332', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 2, transition: 'width 0.5s ease' }} />
      </div>
    </div>
  )
}

function Tag({ text, color }: { text: string; color: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 7px', borderRadius: 10, fontSize: 9, fontWeight: 700,
      background: `${color}18`, border: `1px solid ${color}44`, color, letterSpacing: 0.4,
    }}>
      {text}
    </span>
  )
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div style={{
      fontSize: 9, fontWeight: 700, letterSpacing: 1, color: C.dim,
      borderBottom: `1px solid ${C.border}`, paddingBottom: 5, marginBottom: 8, marginTop: 12,
    }}>
      {label}
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
      <SectionHeader label="LAGNA (ASCENDANT)" />
      <InfoRow label="Rising Sign (Lagna)" value={`${lagna.sign} ${lagna.degree.toFixed(1)}`} valueColor={C.text} />
      <InfoRow label="Lagna Lord" value={lagna.lord} valueColor={C.blue} />
      <InfoRow label="IPO Date / Time" value={`${kundli.entity.inception_date} ${kundli.entity.inception_time}`} />

      <SectionHeader label="CURRENT DASHA" />
      <InfoRow label="Mahadasha" value={`${dasha.mahadasha.planet} until ${dasha.mahadasha.end_date}`} valueColor={C.amber} />
      <InfoRow label="Antardasha" value={`${dasha.antardasha.planet} until ${dasha.antardasha.end_date}`} />
      <InfoRow label="Pratyantardasha" value={`${dasha.pratyantardasha.planet} until ${dasha.pratyantardasha.end_date}`} />

      <SectionHeader label="KEY PLANETS" />
      {moon && (
        <InfoRow label="Moon (sentiment)"
          value={`${moon.sign} H${moon.house} — ${moon.nakshatra} Pada ${moon.pada}`}
          valueColor={DIGNITY_COLOR[moon.dignity] ?? C.sub}
        />
      )}
      {jup && (
        <InfoRow label="Jupiter (growth)"
          value={`${jup.sign} H${jup.house} — ${jup.dignity}`}
          valueColor={DIGNITY_COLOR[jup.dignity] ?? C.sub}
        />
      )}

      {kundli.yogas.length > 0 && (
        <>
          <SectionHeader label="ACTIVE YOGAS" />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {kundli.yogas.map((y, i) => (
              <Tag key={i} text={y.name} color={SIGNAL_YOGA[y.signal] ?? C.sub} />
            ))}
          </div>
        </>
      )}

      <SectionHeader label="INTERPRETATION" />
      {interp.bullish_factors.slice(0, 3).map((f, i) => (
        <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 5, alignItems: 'flex-start' }}>
          <span style={{ color: C.green, fontSize: 9, marginTop: 1 }}>+</span>
          <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.45 }}>{f}</span>
        </div>
      ))}
      {interp.bearish_factors.slice(0, 2).map((f, i) => (
        <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 5, alignItems: 'flex-start' }}>
          <span style={{ color: C.red, fontSize: 9, marginTop: 1 }}>-</span>
          <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.45 }}>{f}</span>
        </div>
      ))}
    </div>
  )
}

function PlanetsTab({ planets }: { planets: Record<string, Planet> }) {
  const PLANET_ORDER = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Rahu','Ketu']
  const listed = PLANET_ORDER.filter(p => planets[p])

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              {['Planet','Sign','House','Nakshatra','Pada','Dignity','R'].map(h => (
                <th key={h} style={{ padding: '4px 6px', textAlign: 'left', color: C.dim, fontSize: 9, fontWeight: 600, letterSpacing: 0.3 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {listed.map(name => {
              const p    = planets[name]
              const dc   = DIGNITY_COLOR[p.dignity] ?? C.sub
              const retro = p.retrograde
              return (
                <tr key={name} style={{ borderBottom: `1px solid ${C.border}22` }}>
                  <td style={{ padding: '5px 6px', color: C.text, fontWeight: 700 }}>{name}</td>
                  <td style={{ padding: '5px 6px', color: C.sub }}>
                    {p.sign}
                    <span style={{ color: C.dimmer, fontSize: 9 }}> {p.degree.toFixed(1)}</span>
                  </td>
                  <td style={{ padding: '5px 6px', color: C.sub, fontVariantNumeric: 'tabular-nums' }}>H{p.house}</td>
                  <td style={{ padding: '5px 6px', color: C.dim, fontSize: 9 }}>{p.nakshatra}</td>
                  <td style={{ padding: '5px 6px', color: C.dim, fontSize: 9 }}>{p.pada}</td>
                  <td style={{ padding: '5px 6px' }}>
                    <span style={{ color: dc, fontSize: 9, fontWeight: 700 }}>
                      {p.dignity.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={{ padding: '5px 6px', color: retro ? C.orange : C.dimmer, fontSize: 9, fontWeight: retro ? 700 : 400 }}>
                    {retro ? 'R' : '-'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <SectionHeader label="D9 NAVAMSA (CORE DESTINY CHART)" />
      <div style={{ color: C.dim, fontSize: 9, marginBottom: 6 }}>
        The Navamsa reveals the deeper karmic blueprint of the entity.
      </div>
      {/* Navamsa signs are in divisional_charts.D9 */}
    </div>
  )
}

function HousesTab({ houses }: { houses: Record<string, HouseData> }) {
  const HOUSE_ORDER = ['2H','5H','8H','10H','11H']
  const labels: Record<string, string> = {
    '2H':  '2H — Wealth / Balance Sheet',
    '5H':  '5H — Speculation / R&D',
    '8H':  '8H — Volatility / M&A',
    '10H': '10H — Management / Reputation',
    '11H': '11H — Revenue / Profits',
  }

  return (
    <div>
      <div style={{ color: C.dim, fontSize: 9, marginBottom: 10, lineHeight: 1.5 }}>
        Financial houses show the strength of key operational areas.
        Green = strong lord; Red = weak/debilitated lord.
      </div>
      {HOUSE_ORDER.map(hk => {
        const h = houses[hk]
        if (!h) return null
        const sc = HOUSE_STRENGTH_COLOR[h.strength] ?? C.sub
        return (
          <div key={hk} style={{
            marginBottom: 10, padding: '10px 12px', borderRadius: 6,
            background: '#0a0f1a', border: `1px solid ${C.border}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: C.text }}>{labels[hk] ?? hk}</span>
              <Tag text={h.strength.toUpperCase()} color={sc} />
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 9, color: C.dim }}>Sign: <span style={{ color: C.sub }}>{h.sign}</span></span>
              <span style={{ fontSize: 9, color: C.dim }}>Lord: <span style={{ color: DIGNITY_COLOR[h.lord_dignity] ?? C.sub }}>{h.lord}</span></span>
              {h.lord_house && (
                <span style={{ fontSize: 9, color: C.dim }}>Lord in: <span style={{ color: C.sub }}>H{h.lord_house}</span></span>
              )}
              {h.occupants.length > 0 && (
                <span style={{ fontSize: 9, color: C.dim }}>Occupants: <span style={{ color: C.blue }}>{h.occupants.join(', ')}</span></span>
              )}
            </div>
            <div style={{ fontSize: 9, color: C.dimmer, marginTop: 4 }}>{h.signification}</div>
          </div>
        )
      })}
    </div>
  )
}

function DashaTab({ dasha, interp }: { dasha: KundliData['current_dasha']; interp: Interpretation }) {
  const DASHA_COLOR: Record<string, string> = {
    Sun: C.amber, Moon: C.blue, Mars: C.red, Mercury: C.green, Jupiter: C.teal,
    Venus: C.purple, Saturn: C.orange, Rahu: '#E879F9', Ketu: '#94A3B8',
  }

  return (
    <div>
      <SectionHeader label="CURRENT PERIOD" />
      {[
        { label: 'Mahadasha (major)',          d: dasha.mahadasha },
        { label: 'Antardasha (sub)',            d: dasha.antardasha },
        { label: 'Pratyantardasha (micro)',     d: dasha.pratyantardasha },
      ].map(({ label, d }) => {
        const c = DASHA_COLOR[d.planet] ?? C.sub
        return (
          <div key={label} style={{ marginBottom: 8, padding: '8px 10px', borderRadius: 5, background: '#0a0f1a', border: `1px solid ${C.border}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 9, color: C.dim }}>{label}</span>
              <span style={{ fontSize: 11, fontWeight: 700, color: c }}>{d.planet}</span>
            </div>
            <div style={{ fontSize: 9, color: C.dimmer, marginTop: 2 }}>
              {d.start_date} — {d.end_date}
            </div>
          </div>
        )
      })}

      <SectionHeader label="DASHA OUTLOOK (NEXT 4 PERIODS)" />
      {interp.dasha_outlook.map((outlook, i) => (
        <div key={i} style={{ marginBottom: 8, padding: '7px 10px', borderRadius: 5, background: '#0a0f1a', border: `1px solid ${C.border}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: C.text }}>{outlook.period}</span>
            <span style={{ fontSize: 9, color: C.dim }}>{outlook.start} — {outlook.end}</span>
          </div>
          {outlook.outlook && (
            <div style={{ fontSize: 9, color: C.sub, lineHeight: 1.4 }}>{outlook.outlook}</div>
          )}
        </div>
      ))}

      <SectionHeader label="MAHADASHA TIMELINE" />
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 9 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              <th style={{ padding: '3px 6px', textAlign: 'left', color: C.dim }}>Planet</th>
              <th style={{ padding: '3px 6px', textAlign: 'left', color: C.dim }}>Start</th>
              <th style={{ padding: '3px 6px', textAlign: 'left', color: C.dim }}>End</th>
            </tr>
          </thead>
          <tbody>
            {dasha.all_mahadashas.slice(0, 9).map((m, i) => {
              const c   = DASHA_COLOR[m.planet] ?? C.sub
              const now = new Date().getFullYear()
              const s   = parseInt(m.start_date?.slice(0, 4) ?? '0')
              const e   = parseInt(m.end_date?.slice(0, 4) ?? '9999')
              const isCurrent = s <= now && now <= e
              return (
                <tr key={i} style={{ background: isCurrent ? '#0d1a12' : 'transparent', borderBottom: `1px solid ${C.border}22` }}>
                  <td style={{ padding: '4px 6px', color: c, fontWeight: isCurrent ? 800 : 400 }}>
                    {m.planet}{isCurrent ? ' *' : ''}
                  </td>
                  <td style={{ padding: '4px 6px', color: C.dim, fontVariantNumeric: 'tabular-nums' }}>{m.start_date?.slice(0,7)}</td>
                  <td style={{ padding: '4px 6px', color: C.dim, fontVariantNumeric: 'tabular-nums' }}>{m.end_date?.slice(0,7)}</td>
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
    return <div style={{ color: C.dim, fontSize: 10, padding: '20px 0', textAlign: 'center' }}>Gann data not available</div>
  }

  const so9    = gann.square_of_9
  const levels = gann.gann_levels
  const cycles = gann.time_cycles
  const plines = gann.planetary_lines

  return (
    <div>
      <SectionHeader label="SQUARE OF 9" />
      <InfoRow label="Price Degree" value={`${so9.current_degree.toFixed(1)} deg`} valueColor={C.amber} />
      <InfoRow label="Nearest Cardinal" value={so9.nearest_angle} valueColor={C.blue} />

      <SectionHeader label="KEY PRICE LEVELS" />
      {levels.key_r1 && <InfoRow label="R1 (next resistance)" value={levels.key_r1.toFixed(1)} valueColor={C.red} />}
      {levels.key_s1 && <InfoRow label="S1 (next support)"    value={levels.key_s1.toFixed(1)} valueColor={C.green} />}

      <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 9, color: C.dim, marginBottom: 4 }}>RESISTANCE LEVELS</div>
          {levels.resistance.map((r, i) => (
            <div key={i} style={{ padding: '3px 6px', borderRadius: 3, background: '#1c0000', border: `1px solid ${C.red}22`, marginBottom: 3, fontSize: 10, color: C.red, fontVariantNumeric: 'tabular-nums', textAlign: 'right' }}>
              {r.toFixed(2)}
            </div>
          ))}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 9, color: C.dim, marginBottom: 4 }}>SUPPORT LEVELS</div>
          {levels.support.map((s, i) => (
            <div key={i} style={{ padding: '3px 6px', borderRadius: 3, background: '#052e16', border: `1px solid ${C.green}22`, marginBottom: 3, fontSize: 10, color: C.green, fontVariantNumeric: 'tabular-nums', textAlign: 'right' }}>
              {s.toFixed(2)}
            </div>
          ))}
        </div>
      </div>

      <SectionHeader label="SOLAR TIME CYCLES" />
      <InfoRow label="Sun Position" value={`${cycles.current_sun_degree.toFixed(1)} deg sidereal`} />
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 4 }}>
        {Object.entries(cycles.fixed_future_dates).map(([label, date]) => (
          <div key={label} style={{ padding: '4px 8px', borderRadius: 4, background: '#0a0f1a', border: `1px solid ${C.border}`, fontSize: 9 }}>
            <span style={{ color: C.dim }}>{label}</span>
            <span style={{ color: C.sub, marginLeft: 4, fontVariantNumeric: 'tabular-nums' }}>{date}</span>
          </div>
        ))}
      </div>

      <SectionHeader label="PLANETARY PRICE LINES (×1 factor)" />
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 9 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              <th style={{ padding: '3px 6px', textAlign: 'left', color: C.dim }}>Planet</th>
              <th style={{ padding: '3px 6px', textAlign: 'right', color: C.dim }}>Lon</th>
              <th style={{ padding: '3px 6px', textAlign: 'right', color: C.dim }}>Base Price</th>
            </tr>
          </thead>
          <tbody>
            {['Sun','Moon','Mars','Jupiter','Saturn','Venus','Mercury'].map(planet => {
              const pl = plines?.[planet]
              if (!pl) return null
              return (
                <tr key={planet} style={{ borderBottom: `1px solid ${C.border}11` }}>
                  <td style={{ padding: '3px 6px', color: C.sub }}>{planet}</td>
                  <td style={{ padding: '3px 6px', color: C.dim, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{pl.longitude.toFixed(1)}</td>
                  <td style={{ padding: '3px 6px', color: C.amber, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{pl.base_price.toFixed(1)}</td>
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
  return (
    <div>
      <SectionHeader label="FINANCIAL SIGNAL SUMMARY" />
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <div style={{
          flex: 1, padding: '10px 12px', borderRadius: 6, background: '#0a0f1a', border: `1px solid ${C.border}`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: 9, color: C.dim, marginBottom: 3 }}>VEDIC SIGNAL</span>
          <span style={{ fontSize: 16, fontWeight: 900, color: (ACTION_CFG[interp.signal] ?? ACTION_CFG.HOLD).color }}>
            {interp.signal}
          </span>
        </div>
        <div style={{
          flex: 1, padding: '10px 12px', borderRadius: 6, background: '#0a0f1a', border: `1px solid ${C.border}`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: 9, color: C.dim, marginBottom: 3 }}>ASTRO SCORE</span>
          <span style={{ fontSize: 16, fontWeight: 900, color: interp.astro_score >= 20 ? C.green : interp.astro_score >= 0 ? C.blue : C.red, fontVariantNumeric: 'tabular-nums' }}>
            {interp.astro_score > 0 ? '+' : ''}{interp.astro_score.toFixed(0)}
          </span>
        </div>
      </div>

      {interp.narrative && (
        <div style={{
          padding: '10px 12px', borderRadius: 6, background: '#08101c',
          border: `1px solid ${C.border}`, marginBottom: 12, lineHeight: 1.6,
          color: C.sub, fontSize: 10,
        }}>
          {interp.narrative}
        </div>
      )}

      <SectionHeader label="BULLISH FACTORS" />
      {interp.bullish_factors.map((f, i) => (
        <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 6, alignItems: 'flex-start' }}>
          <span style={{ color: C.green, fontSize: 9, marginTop: 2, flexShrink: 0 }}>+</span>
          <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.4 }}>{f}</span>
        </div>
      ))}

      {interp.bearish_factors.length > 0 && (
        <>
          <SectionHeader label="BEARISH FACTORS" />
          {interp.bearish_factors.map((f, i) => (
            <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 6, alignItems: 'flex-start' }}>
              <span style={{ color: C.red, fontSize: 9, marginTop: 2, flexShrink: 0 }}>-</span>
              <span style={{ fontSize: 10, color: C.sub, lineHeight: 1.4 }}>{f}</span>
            </div>
          ))}
        </>
      )}

      {interp.yogas && interp.yogas.length > 0 && (
        <>
          <SectionHeader label="ACTIVE YOGAS" />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {interp.yogas.map((y, i) => (
              <Tag key={i} text={y} color={C.purple} />
            ))}
          </div>
        </>
      )}

      <div style={{ color: C.dimmer, fontSize: 8, borderTop: `1px solid ${C.dimmer}22`, paddingTop: 6, marginTop: 12 }}>
        Computed: {kundli.computed_date}. Vedic astrology uses Lahiri ayanamsha + Whole Sign houses.
        This signal is supplementary — always verify with fundamentals and technicals.
      </div>
    </div>
  )
}

// ── Main Card ─────────────────────────────────────────────────────────────────

interface Props {
  symbol: string
}

export function KundliCard({ symbol }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const [expanded, setExpanded]   = useState(false)

  const { data, isLoading, error } = useQuery<KundliResponse>({
    queryKey: ['kundli', symbol],
    queryFn:  () => api.get(`/api/stocks/${symbol}/kundli?include_gann=true&generate_narrative=false`).then(r => r.data),
    staleTime: 3600_000,  // cache 1 hour
    retry: false,
    enabled: expanded,
  })

  const actionBadgeCfg = data
    ? (ACTION_CFG[data.interpretation?.signal] ?? ACTION_CFG.HOLD)
    : ACTION_CFG.HOLD

  return (
    <div style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 8, marginBottom: 16 }}>
      {/* Header row (always visible) */}
      <div
        style={{ padding: '10px 14px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        onClick={() => setExpanded(e => !e)}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: C.sub, fontSize: 9, fontWeight: 700, letterSpacing: 1 }}>VEDIC KUNDLI + GANN</span>
            <span style={{ color: C.dimmer, fontSize: 9 }}>IPO natal chart analysis</span>
          </div>
          {data && (
            <div style={{ color: C.dim, fontSize: 9, marginTop: 2 }}>
              Lagna: {data.kundli.lagna.sign} | Mahadasha: {data.kundli.current_dasha.mahadasha.planet}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {data && (
            <div style={{ padding: '3px 10px', borderRadius: 4, background: actionBadgeCfg.bg, border: `1px solid ${actionBadgeCfg.border}`, color: actionBadgeCfg.color, fontSize: 10, fontWeight: 700 }}>
              {data.interpretation?.signal ?? '--'}
            </div>
          )}
          <span style={{ color: C.dim, fontSize: 11 }}>{expanded ? 'v' : '>'}</span>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div style={{ borderTop: `1px solid ${C.border}`, padding: 14 }}>
          {isLoading && (
            <div style={{ color: C.dim, fontSize: 11, padding: '20px 0', textAlign: 'center' }}>
              Computing Kundli...
            </div>
          )}

          {error && (
            <div style={{ color: C.red, fontSize: 10, padding: '10px 0' }}>
              Failed to load Kundli. The engine may need to be run first.
            </div>
          )}

          {data && (
            <>
              {/* Signal badge + score bar */}
              <div style={{ marginBottom: 12 }}>
                <ScoreBar score={data.interpretation?.astro_score ?? data.kundli.astro_score} />
              </div>

              {/* Tab bar */}
              <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${C.border}`, marginBottom: 12, overflowX: 'auto' }}>
                {TABS.map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)} style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    padding: '5px 10px', fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
                    color: activeTab === tab ? C.text : C.dim,
                    borderBottom: activeTab === tab ? `2px solid ${C.blue}` : '2px solid transparent',
                    marginBottom: -1, flexShrink: 0,
                  }}>
                    {tab.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {activeTab === 'Overview'  && <OverviewTab kundli={data.kundli} interp={data.interpretation} />}
              {activeTab === 'Planets'   && <PlanetsTab planets={data.kundli.planets} />}
              {activeTab === 'Houses'    && <HousesTab houses={data.kundli.financial_houses} />}
              {activeTab === 'Dasha'     && <DashaTab dasha={data.kundli.current_dasha} interp={data.interpretation} />}
              {activeTab === 'Gann'      && <GannTab gann={data.gann} />}
              {activeTab === 'Report'    && <ReportTab kundli={data.kundli} interp={data.interpretation} />}
            </>
          )}
        </div>
      )}
    </div>
  )
}
