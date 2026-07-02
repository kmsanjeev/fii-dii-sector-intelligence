/**
 * Trade Intelligence Card — Phase B
 * Synthesises all available signals into a single entry/exit guidance panel.
 * Pure frontend component: reads the already-fetched Stock detail object.
 */
import type { Stock } from '../../api/client'

// ─── Types ────────────────────────────────────────────────────────────────────

type Bullet = { text: string; type: 'bullish' | 'bearish' }

type TradeSignal = {
  score:   number
  bullish: Bullet[]
  bearish: Bullet[]
  action:  { label: string; color: string; bg: string }
  entryLow:  number | null
  entryHigh: number | null
  stopLoss:  number | null
  trailStop: string
}

// ─── Scoring engine ────────────────────────────────────────────────────────────

function computeTradeSignal(data: Stock): TradeSignal {
  const tech    = data.technical
  const fno     = data.fno
  const fund    = data.fundamentals
  const mgmt    = data.management as Record<string, number | string | null> | undefined
  const trends  = (data.holding_trends ?? []) as Record<string, number | null | string>[]
  const latest  = trends.length > 0 ? trends[trends.length - 1] : null
  const sRot    = data.sector_rotation_signal ?? ''
  const close   = data.close_now

  const bullish: Bullet[] = []
  const bearish: Bullet[] = []
  let score = 50

  // ── 1. Trend / DMA ──────────────────────────────────────────────────────────
  if (tech) {
    const vs200 = tech.vs_dma_200
    if (tech.trend_signal === 'STRONG_UPTREND') {
      bullish.push({ text: `Above all DMAs — strong uptrend confirmed (${vs200 != null ? '+' + vs200.toFixed(1) : ''}% above 200 DMA)`, type: 'bullish' })
      score += 18
    } else if (tech.trend_signal === 'UPTREND') {
      bullish.push({ text: `Above 200 DMA (${vs200 != null ? '+' + vs200.toFixed(1) : ''}%) — uptrend intact`, type: 'bullish' })
      score += 12
    } else if (tech.trend_signal === 'CONSOLIDATING') {
      bullish.push({ text: `Above 200 DMA — consolidating above key institutional support`, type: 'bullish' })
      score += 4
    } else if (tech.trend_signal === 'DOWNTREND') {
      bearish.push({ text: `Below 200 DMA (${vs200 != null ? vs200.toFixed(1) : '--'}%) — technical breakdown, high risk zone`, type: 'bearish' })
      score -= 18
    }

    const prox = tech.prox_52w_high
    if (prox != null && prox >= -3) {
      bullish.push({ text: `At/near 52-week high (${prox.toFixed(1)}%) — breakout watch zone`, type: 'bullish' })
      score += 10
    } else if (prox != null && prox >= -8) {
      bullish.push({ text: `Within 8% of 52-week high (${prox.toFixed(1)}%) — momentum building`, type: 'bullish' })
      score += 6
    } else if (prox != null && prox < -35) {
      bearish.push({ text: `${Math.abs(prox).toFixed(0)}% below 52-week high — deep correction, mean reversion risk`, type: 'bearish' })
      score -= 6
    }
  }

  // ── 2. F&O / OI signal ──────────────────────────────────────────────────────
  if (fno?.oi_signal) {
    const oi1d = fno.oi_1d != null ? ` (1D: ${fno.oi_1d >= 0 ? '+' : ''}${fno.oi_1d.toLocaleString('en-IN', { maximumFractionDigits: 0 })})` : ''
    if (fno.oi_signal === 'LONG_BUILDUP') {
      bullish.push({ text: `Long buildup in F&O${oi1d} — institutions entering fresh long positions`, type: 'bullish' })
      score += 15
    } else if (fno.oi_signal === 'SHORT_COVERING') {
      bullish.push({ text: `Short covering in F&O${oi1d} — bears capitulating, upside pressure`, type: 'bullish' })
      score += 8
    } else if (fno.oi_signal === 'SHORT_BUILDUP') {
      bearish.push({ text: `Short buildup in F&O${oi1d} — institutions building short positions, caution`, type: 'bearish' })
      score -= 15
    } else if (fno.oi_signal === 'LONG_UNWINDING') {
      bearish.push({ text: `Long unwinding in F&O${oi1d} — longs exiting, selling pressure likely`, type: 'bearish' })
      score -= 10
    }
  }

  // ── 3. Sector rotation ──────────────────────────────────────────────────────
  if (sRot === 'EARLY_ROTATION') {
    bullish.push({ text: `Sector in EARLY ROTATION — capital just beginning to enter, best risk/reward phase`, type: 'bullish' })
    score += 14
  } else if (sRot === 'LEADING') {
    bullish.push({ text: `Sector LEADING — top capital inflow rank, institutional momentum strong`, type: 'bullish' })
    score += 10
  } else if (sRot === 'MOMENTUM') {
    bullish.push({ text: `Sector in MOMENTUM — sustained capital inflows, trend intact`, type: 'bullish' })
    score += 7
  } else if (sRot === 'DECLINING') {
    bearish.push({ text: `Sector DECLINING — capital rotating out, sector-level headwind`, type: 'bearish' })
    score -= 12
  } else if (sRot === 'LAGGING') {
    bearish.push({ text: `Sector LAGGING — underperforming market, low institutional interest`, type: 'bearish' })
    score -= 5
  }

  // ── 4. FII / Promoter shareholding trends ──────────────────────────────────
  if (latest) {
    const fiiD = latest.fii_delta as number | null
    const proD = latest.promoter_delta as number | null
    const diiD = latest.dii_delta as number | null

    if (fiiD != null && fiiD > 0.5) {
      bullish.push({ text: `FII stake increased +${fiiD.toFixed(2)}% last quarter — foreign capital accumulating`, type: 'bullish' })
      score += 9
    } else if (fiiD != null && fiiD < -1) {
      bearish.push({ text: `FII stake reduced ${fiiD.toFixed(2)}% last quarter — foreign selling`, type: 'bearish' })
      score -= 9
    }

    if (diiD != null && diiD > 0.5) {
      bullish.push({ text: `DII stake increased +${diiD.toFixed(2)}% — domestic funds accumulating (conviction signal)`, type: 'bullish' })
      score += 6
    }

    if (proD != null && proD < -3) {
      bearish.push({ text: `Promoter stake dropped ${Math.abs(proD).toFixed(2)}% — insider selling, monitor closely`, type: 'bearish' })
      score -= 9
    }

    const conv = latest.conviction_signal as string | null
    if (conv === 'STRONG_ACCUMULATION') {
      bullish.push({ text: `FII + DII both increasing stake — STRONG ACCUMULATION (rare confluence)`, type: 'bullish' })
      score += 6
    }
  }

  // Promoter pledge (from latest shareholding if holding_trends doesn't have it)
  const pledgePct = (data.shareholding as Record<string, unknown> | undefined)?.pledge_pct as number | null
  if (pledgePct != null && pledgePct > 40) {
    bearish.push({ text: `Promoter pledge at ${pledgePct.toFixed(1)}% — high leverage risk, stress event can crash price`, type: 'bearish' })
    score -= 12
  } else if (pledgePct != null && pledgePct > 20) {
    bearish.push({ text: `Promoter pledge at ${pledgePct.toFixed(1)}% — moderate pledge risk, watch for margin calls`, type: 'bearish' })
    score -= 5
  }

  // ── 5. Fundamentals ─────────────────────────────────────────────────────────
  if (fund) {
    const val   = fund.valuation_label as string | null
    const yoyP  = fund.yoy_profit_pct  as number | null
    const yoyR  = fund.yoy_revenue_pct as number | null
    const roe   = fund.roe_pct         as number | null

    if (val === 'CHEAP_QUALITY') {
      bullish.push({ text: `CHEAP QUALITY valuation — P/E below peers with strong ROE. Undervalued entry`, type: 'bullish' })
      score += 10
    } else if (val === 'FAIR_VALUE') {
      bullish.push({ text: `FAIR VALUE — reasonable valuation, not stretched. Comfortable entry`, type: 'bullish' })
      score += 5
    } else if (val === 'EXPENSIVE') {
      bearish.push({ text: `EXPENSIVE valuation — P/E stretched well beyond historical range. Margin of safety is low`, type: 'bearish' })
      score -= 8
    }

    if (yoyP != null && yoyP > 20) {
      bullish.push({ text: `YoY net profit +${yoyP.toFixed(1)}% — strong earnings momentum driving fundamentals`, type: 'bullish' })
      score += 8
    } else if (yoyP != null && yoyP > 0) {
      bullish.push({ text: `YoY net profit +${yoyP.toFixed(1)}% — positive earnings growth`, type: 'bullish' })
      score += 4
    } else if (yoyP != null && yoyP < -15) {
      bearish.push({ text: `YoY net profit ${yoyP.toFixed(1)}% — earnings deteriorating. Review before entry`, type: 'bearish' })
      score -= 10
    } else if (yoyP != null && yoyP < 0) {
      bearish.push({ text: `YoY net profit ${yoyP.toFixed(1)}% — earnings declining. Fundamental risk`, type: 'bearish' })
      score -= 5
    }

    if (yoyR != null && yoyR > 15) {
      bullish.push({ text: `Revenue growing +${yoyR.toFixed(1)}% YoY — strong top-line expansion`, type: 'bullish' })
      score += 5
    }

    if (roe != null && roe > 20) {
      bullish.push({ text: `ROE ${roe.toFixed(1)}% — high capital efficiency, quality business`, type: 'bullish' })
      score += 4
    }
  }

  // ── 6. Management sentiment ─────────────────────────────────────────────────
  if (mgmt) {
    const ms = mgmt.management_score as number | null
    const ml = mgmt.management_label as string | null
    if (ms != null && ms > 65) {
      bullish.push({ text: `Management sentiment POSITIVE (score ${ms.toFixed(0)}/100) — confident tone in recent announcements`, type: 'bullish' })
      score += 6
    } else if (ms != null && ms < 35) {
      bearish.push({ text: `Management sentiment NEGATIVE (score ${ms.toFixed(0)}/100) — cautious or concerning tone`, type: 'bearish' })
      score -= 6
    }
    if (ml === 'DECLINING') {
      bearish.push({ text: `Management signal DECLINING — reduction in holdings/activity. Watch for weakness`, type: 'bearish' })
      score -= 4
    }
  }

  // ── 7. ML model ─────────────────────────────────────────────────────────────
  if (data.ml_scores?.ml_bull_run_score != null) {
    const mlS = data.ml_scores.ml_bull_run_score
    if (mlS >= 70) {
      bullish.push({ text: `ML model score ${mlS.toFixed(0)}/100 — algorithm classifies high bull-run probability`, type: 'bullish' })
      score += 6
    } else if (mlS < 30) {
      bearish.push({ text: `ML model score ${mlS.toFixed(0)}/100 — algorithm classifies low bull-run probability`, type: 'bearish' })
      score -= 6
    }
  }

  const finalScore = Math.max(0, Math.min(100, Math.round(score)))

  // ── Action recommendation ────────────────────────────────────────────────────
  const hardExit = bearish.some(b =>
    b.text.includes('Below 200 DMA') ||
    b.text.includes('short buildup') ||
    b.text.includes('FII + DII both reducing')
  )

  let action: { label: string; color: string; bg: string }
  if (finalScore >= 72 && !hardExit) {
    action = { label: 'STRONG BUY', color: '#22C55E', bg: '#052e16' }
  } else if (finalScore >= 58 && !hardExit) {
    action = { label: 'BUY',         color: '#10B981', bg: '#022c22' }
  } else if (finalScore >= 42) {
    action = { label: 'HOLD / WATCH', color: '#F59E0B', bg: '#1c1400' }
  } else if (finalScore >= 28) {
    action = { label: 'REDUCE',       color: '#F97316', bg: '#1c0a00' }
  } else {
    action = { label: 'EXIT / AVOID', color: '#EF4444', bg: '#1c0000' }
  }

  // ── Entry zone & stop loss ───────────────────────────────────────────────────
  let entryLow: number | null = null
  let entryHigh: number | null = null
  let stopLoss: number | null = null
  let trailStop = 'Trail stop: 7% below swing high after entry'

  if (close != null && close > 0) {
    if (finalScore >= 58) {
      entryLow  = +(close * 0.99).toFixed(2)
      entryHigh = +(close * 1.02).toFixed(2)
    } else if (finalScore >= 42) {
      entryLow  = +(close * 0.97).toFixed(2)
      entryHigh = +(close * 1.00).toFixed(2)
      trailStop = 'Wait for confirmed reversal before entry'
    }

    const dma200 = tech?.dma_200
    if (dma200 != null && close > dma200) {
      stopLoss = +Math.max(dma200 * 0.98, close * 0.90).toFixed(2)
      trailStop = `Trail stop: 3% below 200 DMA (₹${(dma200 * 0.97).toFixed(0)}) or swing low, whichever is higher`
    } else {
      stopLoss = +(close * 0.92).toFixed(2)
    }
  }

  return { score: finalScore, bullish, bearish, action, entryLow, entryHigh, stopLoss, trailStop }
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number }) {
  const segments = [
    { from: 0,  to: 28,  color: '#7F1D1D' },
    { from: 28, to: 42,  color: '#92400E' },
    { from: 42, to: 58,  color: '#713F12' },
    { from: 58, to: 72,  color: '#14532D' },
    { from: 72, to: 100, color: '#052E16' },
  ]
  const active = segments.find(s => score <= s.to) ?? segments[segments.length - 1]
  const color = score >= 72 ? '#22C55E' : score >= 58 ? '#10B981' : score >= 42 ? '#F59E0B' : score >= 28 ? '#F97316' : '#EF4444'

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#475569', marginBottom: 3 }}>
        <span>EXIT</span><span>REDUCE</span><span>HOLD</span><span>BUY</span><span>STRONG BUY</span>
      </div>
      <div style={{ position: 'relative', height: 8, borderRadius: 4, background: '#1E2332', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute', height: '100%', borderRadius: 4,
          width: `${score}%`, background: color,
          transition: 'width 0.4s ease',
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', fontSize: 10, color, marginTop: 3, fontWeight: 700 }}>
        {score}/100
      </div>
    </div>
  )
}

const fmt = (n: number) => n.toLocaleString('en-IN', { maximumFractionDigits: 2 })

// ─── Main card ────────────────────────────────────────────────────────────────

export function TradeIntelligenceCard({ data }: { data: Stock }) {
  const sig = computeTradeSignal(data)
  const { score, bullish, bearish, action, entryLow, entryHigh, stopLoss, trailStop } = sig

  if (bullish.length === 0 && bearish.length === 0) return null

  return (
    <section>
      <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>TRADE INTELLIGENCE</h2>

      {/* Card wrapper */}
      <div style={{
        background: '#0D1117',
        border: `1px solid ${action.color}44`,
        borderRadius: 8,
        overflow: 'hidden',
      }}>

        {/* Header: action badge + score bar */}
        <div style={{
          background: action.bg,
          borderBottom: `1px solid ${action.color}33`,
          padding: '12px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 20,
          flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ color: '#475569', fontSize: 9, letterSpacing: 1, marginBottom: 4 }}>RECOMMENDATION</div>
            <div style={{
              color: action.color,
              fontSize: 15, fontWeight: 700,
              letterSpacing: 1,
              padding: '4px 14px',
              border: `1px solid ${action.color}`,
              borderRadius: 4,
              display: 'inline-block',
            }}>
              {action.label}
            </div>
          </div>
          <div style={{ flex: 1, minWidth: 180 }}>
            <div style={{ color: '#475569', fontSize: 9, letterSpacing: 1, marginBottom: 6 }}>CONVICTION SCORE</div>
            <ScoreBar score={score} />
          </div>
        </div>

        {/* Body: WHY BUY / EXIT WATCH */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0 }}>

          {/* WHY BUY */}
          <div style={{ padding: '14px 16px', borderRight: '1px solid #1E2332' }}>
            <div style={{ fontSize: 9, fontWeight: 700, color: '#22C55E', letterSpacing: 1, marginBottom: 10 }}>
              WHY BUY ({bullish.length} signal{bullish.length !== 1 ? 's' : ''})
            </div>
            {bullish.length === 0 ? (
              <div style={{ color: '#334155', fontSize: 11 }}>No bullish signals at current levels</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                {bullish.map((b, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ color: '#22C55E', fontSize: 12, flexShrink: 0, lineHeight: 1.4 }}>&#10003;</span>
                    <span style={{ color: '#CBD5E1', fontSize: 11, lineHeight: 1.5 }}>{b.text}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* EXIT WATCH */}
          <div style={{ padding: '14px 16px' }}>
            <div style={{ fontSize: 9, fontWeight: 700, color: bearish.length > 0 ? '#EF4444' : '#334155', letterSpacing: 1, marginBottom: 10 }}>
              EXIT WATCH ({bearish.length} signal{bearish.length !== 1 ? 's' : ''})
            </div>
            {bearish.length === 0 ? (
              <div style={{ color: '#334155', fontSize: 11 }}>No active exit signals — position intact</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                {bearish.map((b, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ color: '#EF4444', fontSize: 11, flexShrink: 0, lineHeight: 1.4 }}>&#9650;</span>
                    <span style={{ color: '#CBD5E1', fontSize: 11, lineHeight: 1.5 }}>{b.text}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer: entry zone + stop loss */}
        {(entryLow != null || stopLoss != null) && (
          <div style={{
            borderTop: '1px solid #1E2332',
            padding: '12px 16px',
            display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'flex-start',
            background: '#080B10',
          }}>
            {entryLow != null && entryHigh != null && (
              <div>
                <div style={{ color: '#475569', fontSize: 9, letterSpacing: 1, marginBottom: 4 }}>ENTRY ZONE</div>
                <div style={{ color: '#22C55E', fontWeight: 700, fontSize: 14 }}>
                  &#8377;{fmt(entryLow)} &mdash; &#8377;{fmt(entryHigh)}
                </div>
                <div style={{ color: '#475569', fontSize: 9, marginTop: 2 }}>Buy on dips within this band</div>
              </div>
            )}
            {stopLoss != null && (
              <div>
                <div style={{ color: '#475569', fontSize: 9, letterSpacing: 1, marginBottom: 4 }}>STOP LOSS</div>
                <div style={{ color: '#EF4444', fontWeight: 700, fontSize: 14 }}>&#8377;{fmt(stopLoss)}</div>
                <div style={{ color: '#475569', fontSize: 9, marginTop: 2 }}>
                  {data.close_now != null && stopLoss != null
                    ? `${((stopLoss / data.close_now - 1) * 100).toFixed(1)}% from LTP`
                    : 'Hard stop on close below'}
                </div>
              </div>
            )}
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ color: '#475569', fontSize: 9, letterSpacing: 1, marginBottom: 4 }}>POSITION MANAGEMENT</div>
              <div style={{ color: '#64748B', fontSize: 10, lineHeight: 1.6 }}>
                {trailStop}<br />
                <span style={{ color: '#334155' }}>Risk only what you can afford to lose. Signals are probabilistic, not guarantees.</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
