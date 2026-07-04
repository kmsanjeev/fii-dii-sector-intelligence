import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchStockDetail, fetchStockAnnouncements, fetchAnnouncementSummary, type TechnicalIndicators, type FnoData, type Announcement } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { TradeIntelligenceCard } from '../components/platform/TradeIntelligenceCard'

// ─── Design tokens ────────────────────────────────────────────────────────────

const C = {
  bg:        '#0E1420',
  bgCard:    '#111B2E',
  bgDeep:    '#080E1A',
  border:    '1px solid #1E2D44',
  h1:        '#F8FAFC',
  primary:   '#E2E8F0',
  secondary: '#B0C4D8',
  muted:     '#7B90A8',
  dim:       '#4E6074',
  bull:      '#22D35E',
  bear:      '#F44B4B',
  neutral:   '#F5A524',
  blue:      '#3BAEF0',
  purple:    '#9B7BEA',
  teal:      '#10B981',
}

const LABEL: React.CSSProperties = {
  color: C.secondary, fontSize: 10, fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase',
}

// ─── Tiny helpers ─────────────────────────────────────────────────────────────

function pct(v: number | null | undefined) {
  if (v == null) return '--'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}
function num(v: number | null | undefined, dec = 2) {
  if (v == null) return '--'
  return Number(v).toFixed(dec)
}
function crFmt(v: number | null | undefined): string {
  if (v == null) return '--'
  const n = Number(v)
  if (n >= 100_000) return `${(n / 100_000).toFixed(1)}L Cr`
  if (n >= 1_000)   return `${(n / 1_000).toFixed(1)}K Cr`
  return `${n.toFixed(0)} Cr`
}

// ─── Shared card shell ────────────────────────────────────────────────────────

function Card({ title, children, accentColor }: { title: string; children: React.ReactNode; accentColor?: string }) {
  return (
    <div style={{
      background: C.bgCard, border: C.border, borderRadius: 8,
      overflow: 'hidden',
      borderTop: accentColor ? `3px solid ${accentColor}` : C.border,
    }}>
      <div style={{ padding: '10px 16px 0', ...LABEL, borderBottom: `1px solid #1A2540`, paddingBottom: 8 }}>
        {title}
      </div>
      <div style={{ padding: 16 }}>{children}</div>
    </div>
  )
}

// ─── Fundamental tile ─────────────────────────────────────────────────────────

function FundTile({
  label, value, subtext, headerColor, valueColor, fullSpan,
}: {
  label:       string
  value:       React.ReactNode
  subtext?:    string
  headerColor: string
  valueColor?: string
  fullSpan?:   boolean
}) {
  return (
    <div style={{
      background: C.bgCard,
      border: C.border,
      borderRadius: 8,
      overflow: 'hidden',
      gridColumn: fullSpan ? 'span 2' : undefined,
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Colored header band */}
      <div style={{
        background: headerColor,
        padding: '6px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: 9, fontWeight: 800, letterSpacing: 1.5, textTransform: 'uppercase' }}>
          {label}
        </div>
      </div>
      {/* Value body */}
      <div style={{ padding: '12px 12px 10px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{
          fontSize: 20, fontWeight: 800, fontFamily: 'monospace',
          color: valueColor ?? C.primary, lineHeight: 1.1,
        }}>
          {value}
        </div>
        {subtext && (
          <div style={{ color: C.muted, fontSize: 9, marginTop: 4, letterSpacing: 0.3 }}>
            {subtext}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Fundamental tiles grid (4×3) ─────────────────────────────────────────────

type FundTilesProps = {
  fund:  Record<string, number | string | null>
  shp:   Record<string, number | string | null>
  tech?: { prox_52w_high?: number | null; vs_dma_200?: number | null }
  price: { ret_365d: number | null; vol_ratio: number | null }
}

function FundamentalTiles({ fund, shp, tech, price }: FundTilesProps) {

  const ret1y    = price?.ret_365d
  const volRatio = price?.vol_ratio
  const prox52h  = tech?.prox_52w_high ?? null
  const vs200    = tech?.vs_dma_200 ?? null

  const valLabel  = String(fund.valuation_label ?? '')
  const [valBg, valFg, valText] = valLabel === 'CHEAP_QUALITY' ? ['#052E16', '#22D35E', 'CHEAP QUALITY']
    : valLabel === 'FAIR_VALUE'   ? ['#0C1A3A', '#3BAEF0', 'FAIR VALUE']
    : valLabel === 'MODERATE'     ? ['#1C1000', '#F5A524', 'MODERATE']
    : valLabel === 'EXPENSIVE'    ? ['#2D0A0A', '#F44B4B', 'EXPENSIVE']
    : ['#141B2E', '#7B90A8', valLabel || 'N/A']

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: 10,
    }}>
      {/* Row 1 — Financial Fundamentals */}
      <FundTile
        label="Sales TTM"
        headerColor="#1A3A6E"
        value={fund.revenue_ttm_cr != null ? crFmt(fund.revenue_ttm_cr as number) : '--'}
        subtext={fund.yoy_revenue_pct != null ? `YoY ${pct(fund.yoy_revenue_pct as number)}` : 'trailing 12 months revenue'}
        valueColor={C.primary}
      />
      <FundTile
        label="Net Profit / PAT"
        headerColor="#2D1B4E"
        value={fund.profit_ttm_cr != null ? crFmt(fund.profit_ttm_cr as number) : '--'}
        subtext={fund.yoy_profit_pct != null ? `YoY ${pct(fund.yoy_profit_pct as number)}` : 'trailing 12 months profit'}
        valueColor={(fund.profit_ttm_cr ?? 0) >= 0 ? C.primary : C.bear}
      />
      <FundTile
        label="P/E Ratio"
        headerColor="#2A1800"
        value={fund.pe_ratio != null ? `${Number(fund.pe_ratio).toFixed(1)}x` : '--'}
        subtext="price to earnings — lower is cheaper"
        valueColor={
          fund.pe_ratio == null ? C.muted
          : Number(fund.pe_ratio) < 15 ? C.bull
          : Number(fund.pe_ratio) > 40 ? C.bear
          : C.neutral
        }
      />
      <FundTile
        label="ROE %"
        headerColor="#0A2A1F"
        value={fund.roe_pct != null ? `${Number(fund.roe_pct).toFixed(1)}%` : '--'}
        subtext="return on equity — higher is better"
        valueColor={
          fund.roe_pct == null ? C.muted
          : Number(fund.roe_pct) >= 20 ? C.bull
          : Number(fund.roe_pct) >= 12 ? C.teal
          : Number(fund.roe_pct) < 8  ? C.bear
          : C.neutral
        }
      />

      {/* Row 2 — Price Performance */}
      <FundTile
        label="1-Year Return"
        headerColor={ret1y != null && ret1y >= 0 ? '#062014' : '#200606'}
        value={ret1y != null ? `${ret1y >= 0 ? '+' : ''}${ret1y.toFixed(1)}%` : '--'}
        subtext={ret1y != null ? `Rs 1L invested = Rs ${(1 + ret1y / 100).toFixed(2)}L today` : '365-day return'}
        valueColor={ret1y == null ? C.muted : ret1y >= 0 ? C.bull : C.bear}
      />
      <FundTile
        label="vs 52-Week High"
        headerColor={prox52h != null && prox52h >= -10 ? '#062014' : '#1A0D00'}
        value={prox52h != null ? `${prox52h >= 0 ? '+' : ''}${prox52h.toFixed(1)}%` : '--'}
        subtext={prox52h != null ? (prox52h >= -5 ? 'Near yearly peak!' : prox52h >= -20 ? 'Moderate distance' : 'Far from highs') : 'proximity to 52-week high'}
        valueColor={prox52h == null ? C.muted : prox52h >= -10 ? C.bull : prox52h >= -25 ? C.neutral : C.bear}
      />
      <FundTile
        label="vs 200-Day Avg"
        headerColor={vs200 != null && vs200 >= 0 ? '#062014' : '#200606'}
        value={vs200 != null ? `${vs200 >= 0 ? '+' : ''}${vs200.toFixed(1)}%` : '--'}
        subtext={vs200 != null ? (vs200 >= 5 ? 'Above long-term trend' : vs200 >= 0 ? 'Just above trend' : 'Below trend line') : 'vs 200-day moving average'}
        valueColor={vs200 == null ? C.muted : vs200 >= 5 ? C.bull : vs200 >= 0 ? C.teal : C.bear}
      />
      <FundTile
        label="Volume Ratio"
        headerColor="#0A1C2E"
        value={volRatio != null ? `${Number(volRatio).toFixed(1)}x` : '--'}
        subtext="recent volume vs 90-day average"
        valueColor={volRatio == null ? C.muted : Number(volRatio) >= 1.5 ? C.bull : Number(volRatio) >= 1 ? C.blue : C.muted}
      />

      {/* Row 3 — Ownership */}
      <FundTile
        label="Promoter Holding"
        headerColor="#1E0D3A"
        value={shp.promoter_pct != null ? `${Number(shp.promoter_pct).toFixed(2)}%` : '--'}
        subtext={shp.promoter_pct != null ? (Number(shp.promoter_pct) >= 65 ? 'Very high — insiders invested' : Number(shp.promoter_pct) >= 50 ? 'Majority control' : 'Below majority') : `as of ${shp.quarter_end_date ?? ''}`}
        valueColor={shp.promoter_pct == null ? C.muted : Number(shp.promoter_pct) >= 65 ? C.bull : Number(shp.promoter_pct) >= 50 ? C.teal : C.neutral}
      />
      <FundTile
        label="FII / Foreign"
        headerColor="#0A2014"
        value={shp.fii_pct != null ? `${Number(shp.fii_pct).toFixed(2)}%` : '--'}
        subtext={shp.fii_pct != null ? (Number(shp.fii_pct) >= 20 ? 'High foreign interest' : Number(shp.fii_pct) >= 5 ? 'Moderate FII presence' : 'Low FII holding') : 'foreign institutional investors'}
        valueColor={shp.fii_pct == null ? C.muted : Number(shp.fii_pct) >= 10 ? C.bull : C.blue}
      />
      <FundTile
        label="DII / Domestic"
        headerColor="#0A1230"
        value={shp.dii_pct != null ? `${Number(shp.dii_pct).toFixed(2)}%` : '--'}
        subtext="mutual funds + insurance companies"
        valueColor={shp.dii_pct == null ? C.muted : Number(shp.dii_pct) >= 10 ? C.bull : C.purple}
      />
      <FundTile
        label="Valuation"
        headerColor={valBg}
        value={<span style={{ fontSize: 14, letterSpacing: 0.5 }}>{valText}</span>}
        subtext={fund.valuation_score != null ? `score ${Number(fund.valuation_score).toFixed(0)}/100` : String(fund.as_of_date ?? '')}
        valueColor={valFg}
      />
    </div>
  )
}

// ─── Analyst Insights ─────────────────────────────────────────────────────────

function AnalystInsights({ insights }: { insights?: string[] }) {
  if (!insights || insights.length === 0) return null
  return (
    <div style={{
      background: '#0A1220',
      border: '1px solid #1E3A5F',
      borderLeft: '4px solid #3BAEF0',
      borderRadius: 8,
      padding: 16,
    }}>
      <div style={{ ...LABEL, marginBottom: 12, color: C.blue }}>
        ANALYST INSIGHTS — PLAIN ENGLISH SUMMARY
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {insights.map((text, i) => (
          <div key={i} style={{
            display: 'flex', gap: 10, alignItems: 'flex-start',
            background: '#111B30', border: '1px solid #1A2D48',
            borderRadius: 6, padding: '9px 12px',
          }}>
            <div style={{
              width: 20, height: 20, borderRadius: '50%', background: '#1E3A5F',
              color: C.blue, fontSize: 10, fontWeight: 800, flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {i + 1}
            </div>
            <div style={{ color: C.primary, fontSize: 12, lineHeight: 1.55, flex: 1 }}>
              {text}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Score chip ───────────────────────────────────────────────────────────────

function ScoreChip({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <ScoreGauge score={value} size={64} />
      <div style={{ color: C.secondary, fontSize: 9, marginTop: 4 }}>{label}</div>
      {sub && <div style={{ color: C.dim, fontSize: 8 }}>{sub}</div>}
    </div>
  )
}

// ─── DMA row ──────────────────────────────────────────────────────────────────

function DMARow({ label, value, close, color }: {
  label: string; value: number | null; close: number; color: string
}) {
  if (value == null) return null
  const diff  = (close - value) / value * 100
  const above = diff >= 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
      <span style={{ color: C.muted, fontSize: 10, minWidth: 48 }}>{label}</span>
      <span style={{ color: C.secondary, fontSize: 10, minWidth: 58, textAlign: 'right' }}>
        &#8377;{value.toFixed(0)}
      </span>
      <span style={{ fontSize: 10, fontWeight: 700, minWidth: 46, color: above ? C.bull : C.bear }}>
        {diff >= 0 ? '+' : ''}{diff.toFixed(1)}%
      </span>
      <div style={{ flex: 1, height: 3, background: '#1E2D44', borderRadius: 2, maxWidth: 80 }}>
        <div style={{
          width: `${Math.min(100, Math.abs(diff) / 20 * 100)}%`,
          height: '100%', borderRadius: 2, background: color, opacity: above ? 1 : 0.4,
        }} />
      </div>
      <span style={{ fontSize: 8, color, fontWeight: 700 }}>{above ? 'ABV' : 'BLW'}</span>
    </div>
  )
}

// ─── Technical section ────────────────────────────────────────────────────────

function TechSection({ t, close }: { t: TechnicalIndicators; close: number }) {
  const TREND: Record<string, { color: string; bg: string; label: string }> = {
    STRONG_UPTREND:    { color: '#22D35E', bg: '#052e1688', label: 'Strong Uptrend' },
    UPTREND:           { color: '#10B981', bg: '#064e3b55', label: 'Uptrend' },
    CONSOLIDATING:     { color: '#F5A524', bg: '#45260055', label: 'Consolidating' },
    DOWNTREND:         { color: '#F44B4B', bg: '#45090955', label: 'Downtrend' },
    INSUFFICIENT_DATA: { color: '#7B90A8', bg: '#1E2D4455', label: 'Insufficient Data' },
  }
  const ts = TREND[t.trend_signal] ?? TREND['INSUFFICIENT_DATA']

  return (
    <Card title="TECHNICAL INDICATORS" accentColor={ts.color}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <span style={{
          fontSize: 11, fontWeight: 700, padding: '4px 12px', borderRadius: 5,
          background: ts.bg, color: ts.color, border: `1px solid ${ts.color}44`,
        }}>
          {ts.label}
        </span>
        {t.vol_20d_avg != null && (
          <span style={{ color: C.muted, fontSize: 10 }}>
            Avg Vol {(t.vol_20d_avg / 1e5).toFixed(1)}L shares/day
          </span>
        )}
      </div>

      {/* 52W range bar */}
      {t.high_52w != null && t.low_52w != null && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: C.muted, marginBottom: 5 }}>
            <span>52W Low  &#8377;{t.low_52w.toFixed(0)}</span>
            <span>52W High &#8377;{t.high_52w.toFixed(0)}</span>
          </div>
          <div style={{ height: 6, background: '#1A2740', borderRadius: 3, position: 'relative' }}>
            {(() => {
              const pos = (close - t.low_52w) / (t.high_52w - t.low_52w) * 100
              return (
                <>
                  <div style={{ width: `${pos}%`, height: '100%', background: `linear-gradient(to right, #1E3A5F, #22D35E55)`, borderRadius: 3 }} />
                  <div style={{
                    position: 'absolute', top: -4, left: `${pos}%`,
                    width: 14, height: 14, borderRadius: '50%',
                    background: pos >= 80 ? C.bull : pos >= 45 ? C.neutral : C.bear,
                    transform: 'translateX(-50%)', border: '2px solid #0A0D14',
                    boxShadow: `0 0 8px ${pos >= 80 ? C.bull : pos >= 45 ? C.neutral : C.bear}88`,
                  }} />
                </>
              )
            })()}
          </div>
          {t.prox_52w_high != null && (
            <div style={{
              fontSize: 10, marginTop: 5, fontWeight: 600,
              color: t.prox_52w_high >= -5 ? C.bull : t.prox_52w_high >= -20 ? C.neutral : C.muted,
            }}>
              {t.prox_52w_high >= 0 ? '+' : ''}{t.prox_52w_high.toFixed(1)}% from 52-week high
              {t.prox_52w_high >= -5 && ' — near yearly peak'}
            </div>
          )}
        </div>
      )}

      {/* DMAs */}
      <DMARow label="20 DMA"  value={t.dma_20}  close={close} color="#60A5FA" />
      <DMARow label="50 DMA"  value={t.dma_50}  close={close} color="#A78BFA" />
      <DMARow label="200 DMA" value={t.dma_200} close={close} color="#F5A524" />

      <div style={{ color: C.dim, fontSize: 9, marginTop: 8 }}>as of {t.as_of_date}</div>
    </Card>
  )
}

// ─── F&O section ──────────────────────────────────────────────────────────────

function FnoSection({ fno }: { fno: FnoData }) {
  const OI: Record<string, { color: string; bg: string; plain: string }> = {
    LONG_BUILDUP:   { color: '#22D35E', bg: '#052e1688', plain: 'Big traders buying fresh — bullish sign' },
    SHORT_BUILDUP:  { color: '#F44B4B', bg: '#45090955', plain: 'Big traders betting on a fall — bearish' },
    LONG_UNWINDING: { color: '#F5A524', bg: '#45260055', plain: 'Buyers are exiting — weakening momentum' },
    SHORT_COVERING: { color: '#10B981', bg: '#064e3b55', plain: 'Bears buying back — potential reversal up' },
  }
  const st = OI[fno.oi_signal] ?? { color: C.muted, bg: '#1E2D4455', plain: '' }
  const fmt = (v: number | null) => v == null ? '--' : `${v >= 0 ? '+' : ''}${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

  return (
    <Card title="FUTURES & OPTIONS (DERIVATIVES)" accentColor={st.color}>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
        <div>
          <div style={LABEL}>Signal</div>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 4, marginTop: 5, display: 'inline-block',
            background: st.bg, color: st.color, border: `1px solid ${st.color}44`,
          }}>
            {fno.oi_signal.replace(/_/g, ' ')}
          </span>
        </div>
        <div>
          <div style={LABEL}>Open Interest</div>
          <div style={{ color: C.primary, fontSize: 14, fontWeight: 700, marginTop: 4 }}>
            {fno.futures_oi != null ? (fno.futures_oi / 1e6).toFixed(2) + 'M' : '--'}
          </div>
        </div>
        <div>
          <div style={LABEL}>1-Day Change</div>
          <div style={{ color: (fno.oi_1d ?? 0) >= 0 ? C.bull : C.bear, fontSize: 14, fontWeight: 700, marginTop: 4 }}>
            {fmt(fno.oi_1d)}
          </div>
        </div>
        <div>
          <div style={LABEL}>5-Day Change</div>
          <div style={{ color: (fno.oi_5d ?? 0) >= 0 ? C.bull : C.bear, fontSize: 14, fontWeight: 700, marginTop: 4 }}>
            {fmt(fno.oi_5d)}
          </div>
        </div>
      </div>
      {st.plain && (
        <div style={{
          fontSize: 11, color: st.color, background: st.bg, padding: '7px 10px',
          borderRadius: 5, border: `1px solid ${st.color}33`,
        }}>
          {st.plain}
        </div>
      )}
    </Card>
  )
}

// ─── Shareholding bar ─────────────────────────────────────────────────────────

function SHPBar({ label, pctVal, color, desc }: { label: string; pctVal: number | null; color: string; desc?: string }) {
  if (pctVal == null) return null
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <div>
          <span style={{ color: C.secondary, fontSize: 11, fontWeight: 600 }}>{label}</span>
          {desc && <span style={{ color: C.dim, fontSize: 9, marginLeft: 6 }}>{desc}</span>}
        </div>
        <span style={{ color, fontSize: 13, fontWeight: 800 }}>{pctVal.toFixed(2)}%</span>
      </div>
      <div style={{ height: 5, background: '#1A2740', borderRadius: 3 }}>
        <div style={{ width: `${Math.min(100, pctVal)}%`, height: '100%', background: color, borderRadius: 3 }} />
      </div>
    </div>
  )
}

// ─── Metric row helper ────────────────────────────────────────────────────────

function MetRow({ label, value, color }: { label: string; value: React.ReactNode; color?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 7 }}>
      <span style={{ color: C.muted, fontSize: 10 }}>{label}</span>
      <span style={{ color: color ?? C.primary, fontSize: 11, fontWeight: 600 }}>{value}</span>
    </div>
  )
}

// ─── Phase F: News Sentiment ──────────────────────────────────────────────────

function NewsCard({ news }: { news: Record<string, unknown> }) {
  const label = String(news.sentiment_label ?? '')
  const sc    = label === 'BULLISH' ? C.bull : label === 'BEARISH' ? C.bear : C.muted
  const cnt   = Number(news.news_count_7d ?? 0)
  const s7d   = Number(news.sentiment_7d ?? 0)
  if (!cnt) return null
  return (
    <Card title="NEWS SENTIMENT (7-DAY)" accentColor={sc}>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
        <div>
          <div style={LABEL}>Signal</div>
          <span style={{
            display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
            padding: '3px 10px', borderRadius: 4,
            background: sc + '22', color: sc, border: `1px solid ${sc}44`,
          }}>{label || 'NEUTRAL'}</span>
        </div>
        <div>
          <div style={LABEL}>Score</div>
          <div style={{ color: s7d >= 0.2 ? C.bull : s7d <= -0.2 ? C.bear : C.muted, fontSize: 18, fontWeight: 800, marginTop: 4, fontFamily: 'monospace' }}>
            {s7d >= 0 ? '+' : ''}{s7d.toFixed(2)}
          </div>
        </div>
        <div>
          <div style={LABEL}>Articles</div>
          <div style={{ color: C.secondary, fontSize: 18, fontWeight: 800, marginTop: 4, fontFamily: 'monospace' }}>{cnt}</div>
        </div>
        <div>
          <div style={LABEL}>Bull / Bear</div>
          <div style={{ marginTop: 4, fontSize: 13, fontWeight: 700 }}>
            <span style={{ color: C.bull }}>{Number(news.bullish_count ?? 0)}</span>
            <span style={{ color: C.dim }}> / </span>
            <span style={{ color: C.bear }}>{Number(news.bearish_count ?? 0)}</span>
          </div>
        </div>
      </div>
      {news.latest_headline && (
        <div style={{
          fontSize: 10, color: C.secondary, background: C.bgDeep,
          padding: '7px 10px', borderRadius: 5, border: C.border, lineHeight: 1.5,
        }}>
          {String(news.latest_headline)}
          {news.latest_date && <span style={{ color: C.dim, marginLeft: 8 }}>{String(news.latest_date)}</span>}
        </div>
      )}
      {news.top_theme && (
        <div style={{ marginTop: 8, fontSize: 9, color: C.blue }}>
          Top theme: {String(news.top_theme).replace(/_/g, ' ')}
        </div>
      )}
    </Card>
  )
}

// ─── Phase F: Insider Trade Signals ───────────────────────────────────────────

function InsiderCard({ insider }: { insider: Record<string, unknown> }) {
  const label = String(insider.insider_conviction ?? '')
  if (!label) return null
  const isBuy  = label.includes('BUY')
  const isSell = label.includes('SELL')
  const sc     = isBuy ? C.bull : isSell ? C.bear : C.muted
  const net    = Number(insider.net_value_30d_cr ?? 0)
  return (
    <Card title="INSIDER TRADING (30-DAY NSE PIT)" accentColor={sc}>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
        <div>
          <div style={LABEL}>Conviction</div>
          <span style={{
            display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
            padding: '3px 10px', borderRadius: 4,
            background: sc + '22', color: sc, border: `1px solid ${sc}44`,
          }}>{label.replace(/_/g, ' ')}</span>
        </div>
        <div>
          <div style={LABEL}>Net Value</div>
          <div style={{ color: net >= 0 ? C.bull : C.bear, fontSize: 18, fontWeight: 800, marginTop: 4, fontFamily: 'monospace' }}>
            {net >= 0 ? '+' : ''}{net.toFixed(2)} Cr
          </div>
        </div>
        <div>
          <div style={LABEL}>Buy / Sell Txns</div>
          <div style={{ marginTop: 4, fontSize: 13, fontWeight: 700 }}>
            <span style={{ color: C.bull }}>{Number(insider.buy_count_30d ?? 0)}</span>
            <span style={{ color: C.dim }}> / </span>
            <span style={{ color: C.bear }}>{Number(insider.sell_count_30d ?? 0)}</span>
          </div>
        </div>
      </div>
      {insider.acquirers && (
        <div style={{ fontSize: 9, color: C.muted, lineHeight: 1.5 }}>
          Insiders: {String(insider.acquirers).split('|').slice(0, 3).join(', ')}
        </div>
      )}
      {insider.latest_date && (
        <div style={{ fontSize: 9, color: C.dim, marginTop: 4 }}>Last transaction: {String(insider.latest_date)}</div>
      )}
    </Card>
  )
}

// ─── Phase F: Concall / Earnings Signal ───────────────────────────────────────

function ConcallCard({ concall }: { concall: Record<string, unknown> }) {
  const sentiment  = String(concall.sentiment ?? '')
  const guidance   = String(concall.guidance_direction ?? '')
  const capex      = String(concall.capex_signal ?? '')
  if (!sentiment) return null

  const SC: Record<string, string> = { BULLISH: C.bull, BEARISH: C.bear, NEUTRAL: C.muted }
  const GC: Record<string, string> = { RAISED: C.bull, MAINTAINED: C.neutral, LOWERED: C.bear, NOT_GIVEN: C.dim }
  const sc   = SC[sentiment] ?? C.muted
  const gc   = GC[guidance]  ?? C.muted
  const score = Number(concall.concall_score ?? 0)

  return (
    <Card title={`CONCALL SIGNAL${concall.date ? ` (${String(concall.date)})` : ''}`} accentColor={sc}>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
        <div>
          <div style={LABEL}>Tone</div>
          <span style={{
            display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
            padding: '3px 10px', borderRadius: 4, background: sc + '22', color: sc, border: `1px solid ${sc}44`,
          }}>{sentiment}</span>
        </div>
        <div>
          <div style={LABEL}>Guidance</div>
          <span style={{
            display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
            padding: '3px 10px', borderRadius: 4, background: gc + '22', color: gc, border: `1px solid ${gc}44`,
          }}>{guidance.replace(/_/g, ' ')}</span>
        </div>
        {capex === 'YES' && (
          <div>
            <div style={LABEL}>Capex</div>
            <span style={{
              display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
              padding: '3px 10px', borderRadius: 4, background: '#0C2A4044', color: C.blue, border: `1px solid ${C.blue}44`,
            }}>
              YES{concall.capex_amount_cr ? ` — ${crFmt(Number(concall.capex_amount_cr))}` : ''}
            </span>
          </div>
        )}
        <div>
          <div style={LABEL}>Compound Score</div>
          <div style={{ color: score >= 1 ? C.bull : score <= -0.5 ? C.bear : C.muted, fontSize: 18, fontWeight: 800, marginTop: 4, fontFamily: 'monospace' }}>
            {score >= 0 ? '+' : ''}{score.toFixed(2)}
          </div>
        </div>
      </div>
      {concall.key_statement && (
        <div style={{
          fontSize: 10, color: C.secondary, fontStyle: 'italic', background: C.bgDeep,
          padding: '7px 10px', borderRadius: 5, border: C.border, lineHeight: 1.5,
        }}>
          "{String(concall.key_statement)}"
        </div>
      )}
      {concall.themes && (
        <div style={{ marginTop: 8, fontSize: 9, color: C.blue }}>
          Themes: {String(concall.themes).replace(/,/g, ' · ').replace(/_/g, ' ')}
        </div>
      )}
    </Card>
  )
}

// ─── Phase G: Multi-Signal Consensus ─────────────────────────────────────────

function ConsensusCard({ con }: { con: Record<string, unknown> }) {
  const score  = Number(con.consensus_score ?? 50)
  const label  = String(con.consensus_label ?? '')
  const sigs   = String(con.signals_used ?? '').split('|').filter(Boolean)
  if (!label) return null

  const sc = score >= 68 ? C.bull : score >= 58 ? C.teal : score <= 32 ? C.bear : score <= 42 ? '#F44B4B99' : C.muted
  const [lbg, lfg] = score >= 58 ? ['#052E1688', '#22D35E']
    : score <= 42 ? ['#2D0A0A88', '#F44B4B']
    : ['#1A274088', '#7B90A8']

  const sub: { label: string; key: string; color: string }[] = [
    { label: 'Concall',  key: 'concall_norm',  color: '#9B7BEA' },
    { label: 'Insider',  key: 'insider_norm',  color: '#F5A524' },
    { label: 'News',     key: 'news_norm',     color: '#3BAEF0' },
    { label: 'Deals',    key: 'deal_norm',     color: '#22D35E' },
  ]

  return (
    <Card title={`MARKET CONSENSUS${con.as_of_date ? ` (${String(con.as_of_date)})` : ''}`} accentColor={sc}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
        <div style={{ fontSize: 28, fontWeight: 900, fontFamily: 'monospace', color: sc }}>
          {score.toFixed(0)}<span style={{ fontSize: 10, color: C.muted }}>/100</span>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ height: 6, background: '#1A2740', borderRadius: 3, marginBottom: 6, overflow: 'hidden' }}>
            <div style={{ width: `${score}%`, height: '100%', background: `linear-gradient(to right, ${sc}88, ${sc})`, borderRadius: 3 }} />
          </div>
          <span style={{
            fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 3,
            background: lbg, color: lfg,
          }}>{label.replace(/_/g, ' ')}</span>
        </div>
      </div>

      {/* Sub-signal breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6, marginBottom: 10 }}>
        {sub.map(({ label: lbl, key, color }) => {
          const v = con[key] as number | null | undefined
          const active = v != null
          return (
            <div key={key} style={{
              background: C.bgDeep, border: C.border, borderRadius: 5,
              padding: '6px 8px', opacity: active ? 1 : 0.4,
            }}>
              <div style={{ fontSize: 8, color: C.muted, marginBottom: 3 }}>{lbl}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ flex: 1, height: 4, background: '#1E2D44', borderRadius: 2 }}>
                  <div style={{
                    width: `${active ? v! : 50}%`, height: '100%',
                    background: color, borderRadius: 2,
                    opacity: active ? 1 : 0.3,
                  }} />
                </div>
                <span style={{ color: active ? color : C.dim, fontSize: 10, fontWeight: 700, minWidth: 28 }}>
                  {active ? v!.toFixed(0) : '--'}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {sigs.length > 0 && (
        <div style={{ fontSize: 9, color: C.dim }}>
          Signals active: {sigs.join(' · ')}
        </div>
      )}
    </Card>
  )
}

// ─── Corporate Announcements Feed ────────────────────────────────────────────

const ANN_COLOR: Record<string, string> = {
  BOARD_OUTCOME:     '#9B7BEA',   // purple  — governance
  MANAGEMENT_CHANGE: '#F44B4B',   // red     — leadership shift
  ACQUISITION:       '#F5A524',   // amber   — M&A
  FUNDRAISE:         '#3BAEF0',   // blue    — capital raise
  DIVIDEND:          '#22D35E',   // green   — cash return
  ORDER_WIN:         '#22D35E',   // green   — revenue visibility
  DISTRESS:          '#F44B4B',   // red     — risk flag
  RESULT_UPDATE:     '#10B981',   // teal    — earnings
  ANALYST_MEET:      '#3BAEF0',   // blue    — institutional
  REGULATORY:        '#F5A524',   // amber   — compliance
  CREDIT_RATING:     '#F5A524',   // amber
  VOLUME_ALERT:      '#F5A524',   // amber
  ESOP:              '#7B90A8',
  PRESS_RELEASE:     '#4E6074',
  OTHER:             '#4E6074',
}

function AISummaryBody({ text, accentColor }: { text: string; accentColor: string }) {
  const parts = text.split(/\*\*(.+?)\*\*/)
  const sections: { label: string; body: string }[] = []
  for (let i = 1; i < parts.length - 1; i += 2) {
    sections.push({ label: parts[i].trim(), body: (parts[i + 1] ?? '').trim() })
  }
  if (!sections.length) return <div style={{ fontSize: 11, lineHeight: 1.55 }}>{text}</div>
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
      {sections.map(({ label, body }) => (
        <div key={label}>
          <span style={{ fontWeight: 700, color: accentColor, fontSize: 10 }}>{label} </span>
          <span style={{ fontSize: 11, lineHeight: 1.55 }}>{body}</span>
        </div>
      ))}
    </div>
  )
}

function AnnItem({ ann, last }: { ann: Announcement; last: boolean }) {
  const [summary, setSummary] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const [open,    setOpen]    = useState(false)

  const typeColor  = ANN_COLOR[ann.announcement_type] ?? C.muted
  const scoreColor = ann.signal_score == null ? C.dim
    : ann.signal_score >= 75 ? C.bull
    : ann.signal_score >= 55 ? C.neutral
    : C.dim

  const handleSummarise = async () => {
    if (summary) { setOpen(o => !o); return }
    setOpen(true); setLoading(true); setError(null)
    try {
      const res = await fetchAnnouncementSummary(ann.pdf_url!, ann.seq_id, ann.title || ann.desc)
      setSummary(res.summary)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } }; message?: string })
        ?.response?.data?.detail ?? (e as { message?: string })?.message ?? 'Failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '8px 6px', borderBottom: !last ? '1px solid #131E30' : 'none' }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        {/* Left: date + score */}
        <div style={{ minWidth: 68, flexShrink: 0 }}>
          <div style={{ color: C.dim, fontSize: 9, fontFamily: 'monospace', marginBottom: 3 }}>
            {ann.date.slice(0, 10)}
          </div>
          {ann.signal_score != null && (
            <div style={{
              display: 'inline-block', fontSize: 8, fontWeight: 700,
              padding: '1px 5px', borderRadius: 2,
              background: scoreColor + '18', color: scoreColor,
              border: `1px solid ${scoreColor}33`,
            }}>
              {ann.signal_score}
            </div>
          )}
        </div>

        {/* Middle: type badge + title */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ marginBottom: 3 }}>
            <span style={{
              fontSize: 8, fontWeight: 700, padding: '1px 6px', borderRadius: 2,
              background: typeColor + '18', color: typeColor,
              border: `1px solid ${typeColor}33`, letterSpacing: 0.5,
            }}>
              {ann.announcement_type.replace(/_/g, ' ')}
            </span>
          </div>
          <div style={{
            fontSize: 10, color: C.secondary, lineHeight: 1.4,
            overflow: 'hidden', display: '-webkit-box',
            WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
          } as React.CSSProperties}>
            {ann.title || ann.desc}
          </div>
        </div>

        {/* Right: AI + PDF buttons */}
        <div style={{ flexShrink: 0, display: 'flex', gap: 5, alignSelf: 'center' }}>
          {ann.pdf_url && (
            <button
              onClick={handleSummarise}
              style={{
                display: 'flex', alignItems: 'center', gap: 3,
                padding: '3px 7px', borderRadius: 3, cursor: 'pointer',
                border: `1px solid ${C.neutral}50`,
                background: open ? C.neutral + '22' : C.neutral + '10',
                color: C.neutral, fontSize: 9, fontWeight: 700,
              }}
            >
              {loading
                ? <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
                : 'AI'
              }
            </button>
          )}
          {ann.pdf_url && (
            <a href={ann.pdf_url} target="_blank" rel="noopener noreferrer"
              style={{ display: 'flex', alignItems: 'center', padding: '4px 7px', borderRadius: 3, background: C.blue + '18', color: C.blue, border: `1px solid ${C.blue}40`, textDecoration: 'none' }}
            >
              <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </a>
          )}
        </div>
      </div>

      {/* AI summary panel */}
      {open && (
        <div style={{
          marginTop: 7, marginLeft: 78,
          padding: '8px 10px', borderRadius: 5,
          background: C.neutral + '0C', border: `1px solid ${C.neutral}28`,
          fontSize: 10, color: C.secondary, lineHeight: 1.5,
        }}>
          {loading && <span style={{ color: C.dim }}>Reading PDF and generating analysis...</span>}
          {error   && <span style={{ color: C.bear }}>Error: {error}</span>}
          {summary && !loading && <AISummaryBody text={summary} accentColor={C.neutral} />}
        </div>
      )}
    </div>
  )
}

function AnnouncementsCard({ symbol }: { symbol: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['announcements', symbol],
    queryFn:  () => fetchStockAnnouncements(symbol, 20),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return (
    <Card title="CORPORATE ANNOUNCEMENTS" accentColor={C.blue}>
      <div style={{ color: C.muted, fontSize: 11, textAlign: 'center', padding: 16 }}>Loading...</div>
    </Card>
  )

  const items: Announcement[] = data?.announcements ?? []
  if (!items.length) return null

  return (
    <Card title={`CORPORATE ANNOUNCEMENTS${data?.total && data.total > 20 ? ` (latest 20 of ${data.total})` : ` (${items.length})`}`} accentColor={C.blue}>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {items.map((ann, i) => (
          <AnnItem key={ann.seq_id || i} ann={ann} last={i === items.length - 1} />
        ))}
      </div>
    </Card>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function StockDetailPage() {
  const { symbol } = useParams<{ symbol: string }>()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['stock', symbol],
    queryFn:  () => fetchStockDetail(symbol!),
  })

  if (isLoading) return (
    <div style={{ color: C.muted, textAlign: 'center', padding: 60, fontSize: 13 }}>
      Loading intelligence for {symbol}...
    </div>
  )
  if (isError || !data) return (
    <div>
      <div style={{ color: C.bear, textAlign: 'center', padding: 40, fontSize: 13 }}>
        Symbol {symbol} not found in intelligence data
      </div>
    </div>
  )

  const c = data.components
  const t = data.technical
  const f = data.fno
  const hasFno   = f && f.oi_signal && f.oi_signal !== ''
  const hasShp   = data.shareholding && data.shareholding.promoter_pct != null
  const hasFund  = data.fundamentals && (data.fundamentals.valuation_score != null || data.fundamentals.pe_ratio != null)
  const hasHT    = Array.isArray(data.holding_trends) && (data.holding_trends as unknown[]).length > 0
  const hasMgmt  = data.management && (data.management as Record<string, unknown>).management_score != null
  const hasDeals = data.deal_signals && Object.keys(data.deal_signals).length > 0
  const close    = data.close_now ?? t?.close_now ?? 0

  const insights = data.analyst_insights

  const trendColor = t?.trend_signal === 'STRONG_UPTREND' ? C.bull
    : t?.trend_signal === 'UPTREND' ? C.teal
    : t?.trend_signal === 'CONSOLIDATING' ? C.neutral
    : t?.trend_signal ? C.bear : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Compact header ───────────────────────────────────────────────────── */}
      <div style={{
        background: C.bgCard, border: C.border, borderRadius: 8,
        padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
            <h1 style={{ color: C.h1, fontSize: 24, fontWeight: 900, fontFamily: 'monospace', margin: 0, letterSpacing: 1 }}>
              {data.symbol}
            </h1>
            {close > 0 && (
              <span style={{ color: C.h1, fontSize: 20, fontWeight: 700 }}>
                &#8377;{close.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </span>
            )}
            {data.price.ret_30d != null && (
              <span style={{ fontSize: 13, fontWeight: 700, color: data.price.ret_30d >= 0 ? C.bull : C.bear }}>
                {data.price.ret_30d >= 0 ? '+' : ''}{data.price.ret_30d.toFixed(1)}% 30D
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginTop: 6 }}>
            <span style={{ color: C.secondary, fontSize: 12 }}>{data.sector}</span>
            <span style={{ color: C.dim }}>|</span>
            <CapFlowBadge label={data.label} />
            {trendColor && t?.trend_signal && t.trend_signal !== 'INSUFFICIENT_DATA' && (
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 3,
                border: `1px solid ${trendColor}44`, color: trendColor, background: `${trendColor}18`,
              }}>
                {t.trend_signal.replace(/_/g, ' ')}
              </span>
            )}
            {hasFno && f && (
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 3,
                border: `1px solid ${f.oi_signal === 'LONG_BUILDUP' ? '#22D35E44' : '#F44B4B44'}`,
                color: f.oi_signal === 'LONG_BUILDUP' ? C.bull : C.bear,
                background: f.oi_signal === 'LONG_BUILDUP' ? '#052e1688' : '#45090955',
              }}>
                F&O: {f.oi_signal.replace(/_/g, ' ')}
              </span>
            )}
            {data.sector_rotation_signal && (
              <span style={{ fontSize: 9, color: C.muted, padding: '2px 6px', border: C.border, borderRadius: 3 }}>
                Sector: {data.sector_rotation_signal.replace(/_/g, ' ')}
              </span>
            )}
            <a
              href={`https://www.nseindia.com/get-quotes/equity?symbol=${data.symbol}`}
              target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 9, color: C.blue, textDecoration: 'none', border: '1px solid #1E3A5F', padding: '2px 7px', borderRadius: 3, marginLeft: 4 }}
            >
              NSE
            </a>
          </div>
        </div>

        {/* Score gauges */}
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexShrink: 0 }}>
          <ScoreChip label="Bull Run" value={data.bull_run_score} sub={data.market_regime} />
          {data.ml_scores?.ml_bull_run_score != null && (
            <ScoreChip label="ML Score" value={data.ml_scores.ml_bull_run_score} />
          )}
          {data.ml_scores?.accumulation_score != null && (
            <ScoreChip label="Accum." value={data.ml_scores.accumulation_score} />
          )}
        </div>
      </div>

      {/* ── Fundamental Tiles (4×3 grid) ─────────────────────────────────────── */}
      {(hasFund || hasShp) && (
        <FundamentalTiles
          fund={data.fundamentals as Record<string, number | string | null> ?? {}}
          shp={data.shareholding   as Record<string, number | string | null> ?? {}}
          tech={t}
          price={data.price}
        />
      )}

      {/* ── Analyst Insights ─────────────────────────────────────────────────── */}
      <AnalystInsights insights={insights} />

      {/* ── Two-column body ──────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16, alignItems: 'start' }}>

        {/* ── LEFT COLUMN ────────────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Score components */}
          <Card title="BULL RUN SCORE BREAKDOWN">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 10 }}>
              {[
                { label: 'Price Momentum', value: c.price_score,       sub: '30% weight' },
                { label: 'Sector Flow',    value: c.sector_flow_score, sub: '25% weight' },
                { label: 'Block Deals',    value: c.deal_score,        sub: '25% weight' },
                { label: 'Corp Events',    value: c.corporate_score,   sub: '20% weight' },
              ].map(({ label, value, sub }) => (
                <div key={label} style={{
                  background: C.bgDeep, border: C.border, borderRadius: 6,
                  padding: '10px 8px', textAlign: 'center',
                }}>
                  <ScoreGauge score={value} size={56} />
                  <div style={{ color: C.secondary, fontSize: 9, marginTop: 5 }}>{label}</div>
                  <div style={{ color: C.dim, fontSize: 8, marginTop: 2 }}>{sub}</div>
                </div>
              ))}
            </div>
            <div style={{
              display: 'flex', gap: 10, flexWrap: 'wrap',
              padding: '8px 10px', background: C.bgDeep, borderRadius: 5, border: C.border,
            }}>
              <span style={{ color: C.muted, fontSize: 9 }}>Regime: <span style={{ color: C.secondary }}>{data.market_regime}</span></span>
              <span style={{ color: C.dim }}>|</span>
              <span style={{ color: C.muted, fontSize: 9 }}>Multiplier: <span style={{ color: C.secondary }}>x{data.regime_multiplier.toFixed(2)}</span></span>
              <span style={{ color: C.dim }}>|</span>
              <span style={{ color: C.muted, fontSize: 9 }}>as of {data.as_of_date}</span>
            </div>
          </Card>

          {/* Price returns — 4 boxes */}
          <Card title="PRICE PERFORMANCE">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {[
                { label: '30-Day',    value: data.price.ret_30d, isMult: false },
                { label: '90-Day',    value: data.price.ret_90d, isMult: false },
                { label: '1-Year',    value: data.price.ret_365d, isMult: false },
                { label: 'Vol Ratio', value: data.price.vol_ratio, isMult: true },
              ].map(({ label, value, isMult }) => (
                <div key={label} style={{
                  background: C.bgDeep, border: C.border, borderRadius: 6,
                  padding: '12px 8px', textAlign: 'center',
                }}>
                  <div style={{ color: C.muted, fontSize: 9, marginBottom: 6 }}>{label}</div>
                  <div style={{
                    fontSize: 16, fontWeight: 800,
                    color: isMult ? C.blue : (value ?? 0) >= 0 ? C.bull : C.bear,
                  }}>
                    {value == null ? '--'
                      : isMult ? `${Number(value).toFixed(1)}x`
                      : pct(value)}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Deal signals */}
          {hasDeals && (
            <Card title="INSTITUTIONAL BLOCK/BULK DEALS (30 DAYS)" accentColor="#9B7BEA">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                {Object.entries(data.deal_signals as Record<string, unknown>).map(([k, v]) => (
                  <MetRow key={k}
                    label={k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    value={String(v)}
                  />
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* ── RIGHT COLUMN ─────────────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Catalyst banner */}
          {data.catalyst?.event_date && (
            <div style={{
              background: '#15100A', border: '1px solid #F5A52444',
              borderRadius: 8, padding: '10px 14px',
              display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap',
            }}>
              <span style={{ ...LABEL, color: C.neutral }}>UPCOMING EVENT</span>
              <span style={{ color: C.neutral, fontWeight: 700, fontSize: 13 }}>{data.catalyst.event_date}</span>
              <span style={{ color: C.secondary, fontSize: 12 }}>{data.catalyst.purpose_type}</span>
              {data.catalyst.catalyst_score != null && (
                <span style={{ color: C.dim, fontSize: 9, marginLeft: 'auto' }}>
                  score {data.catalyst.catalyst_score.toFixed(0)}
                </span>
              )}
            </div>
          )}

          {/* Trade Intelligence Card */}
          <TradeIntelligenceCard data={data} />

          {/* Technical */}
          {t && t.dma_200 != null && close > 0 && (
            <TechSection t={t} close={close} />
          )}

          {/* F&O */}
          {hasFno && f && <FnoSection fno={f} />}

          {/* Shareholding */}
          {hasShp && (
            <Card title={`WHO OWNS THIS STOCK${data.shareholding!.window_label ? ` (${data.shareholding!.window_label})` : ''}`}>
              <SHPBar label="Promoters"         pctVal={data.shareholding!.promoter_pct as number | null} color="#9B7BEA" desc="founders &amp; insiders" />
              <SHPBar label="FII / Foreign"     pctVal={data.shareholding!.fii_pct      as number | null} color="#22D35E" desc="global funds" />
              <SHPBar label="DII / Domestic"    pctVal={data.shareholding!.dii_pct      as number | null} color="#3BAEF0" desc="MFs &amp; insurance" />
              <SHPBar label="Public / Retail"   pctVal={data.shareholding!.public_pct   as number | null} color="#7B90A8" desc="individual investors" />
            </Card>
          )}

          {/* Holding Trends */}
          {hasHT && (
            <Card title="OWNERSHIP CHANGES — QUARTER BY QUARTER">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      {['Quarter', 'Promoter', 'FII', 'DII', 'Signal'].map(h => (
                        <th key={h} style={{
                          padding: '5px 6px', color: C.secondary, fontWeight: 700,
                          textAlign: h === 'Quarter' || h === 'Signal' ? 'left' : 'right',
                          borderBottom: '1px solid #1E2D44', fontSize: 9, letterSpacing: 0.8,
                        }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(data.holding_trends as Record<string, unknown>[]).map((q, i, arr) => {
                      const latest = i === arr.length - 1
                      const dc = (v: number | null) => v == null ? C.muted : v > 0 ? C.bull : v < 0 ? C.bear : C.muted
                      const fmt = (p: unknown, d: unknown) => {
                        if (p == null) return '--'
                        const pn = Number(p), dn = d != null ? Number(d) : null
                        return (
                          <span>
                            <span style={{ color: C.primary }}>{pn.toFixed(1)}%</span>
                            {dn != null && i > 0 && (
                              <span style={{ color: dc(dn), fontSize: 9 }}>
                                {' '}{dn >= 0 ? '+' : ''}{dn.toFixed(1)}
                              </span>
                            )}
                          </span>
                        )
                      }
                      const SIG: Record<string, string> = {
                        STRONG_PROMOTER_FII_BUY: '#22D35E',
                        FII_DII_ACCUMULATION:    '#3BAEF0',
                        FII_ACCUMULATION:        '#60A5FA',
                        DII_ACCUMULATION:        '#818CF8',
                        STRONG_PROMOTER_BUY:     '#9B7BEA',
                        STABLE:                  '#7B90A8',
                        PROMOTER_SELLING:        '#F44B4B',
                        FII_DII_DIVERGENCE:      '#F5A524',
                      }
                      const sig = String(q.conviction_signal ?? '')
                      return (
                        <tr key={String(q.period)} style={{
                          borderBottom: '1px solid #1A2D4415',
                          background: latest ? '#1A2D4420' : 'transparent',
                        }}>
                          <td style={{ padding: '5px 6px', color: latest ? C.h1 : C.muted, fontWeight: latest ? 700 : 400 }}>
                            {String(q.period)}
                            {latest && <span style={{ color: C.bull, fontSize: 8, marginLeft: 4 }}>LATEST</span>}
                          </td>
                          <td style={{ padding: '5px 6px', textAlign: 'right' }}>{fmt(q.promoter_pct, q.promoter_delta)}</td>
                          <td style={{ padding: '5px 6px', textAlign: 'right' }}>{fmt(q.fii_pct, q.fii_delta)}</td>
                          <td style={{ padding: '5px 6px', textAlign: 'right' }}>{fmt(q.dii_pct, q.dii_delta)}</td>
                          <td style={{ padding: '5px 6px' }}>
                            {sig && i > 0 && (
                              <span style={{
                                fontSize: 8, fontWeight: 700, padding: '1px 4px',
                                borderRadius: 2, color: SIG[sig] ?? C.muted,
                                border: `1px solid ${SIG[sig] ?? C.muted}55`,
                                whiteSpace: 'nowrap',
                              }}>
                                {sig.replace(/_/g, ' ')}
                              </span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Management Intelligence */}
          {hasMgmt && (() => {
            const m = data.management as Record<string, unknown>
            const ms = Number(m.management_score ?? 0)
            const lbl = String(m.management_label ?? '')
            const sc = ms >= 65 ? C.bull : ms >= 45 ? C.neutral : C.bear
            const [lbg, lfg] = lbl === 'POSITIVE' ? ['#052E16', '#22D35E']
              : lbl === 'NEGATIVE' ? ['#2D0A0A', '#F44B4B']
              : ['#1A2740', '#7B90A8']
            return (
              <Card title={`MANAGEMENT QUALITY${m.as_of_date ? ` (${m.as_of_date})` : ''}`} accentColor={sc}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
                  <div style={{ fontSize: 26, fontWeight: 800, color: sc, fontFamily: 'monospace' }}>
                    {ms.toFixed(0)}<span style={{ fontSize: 11, color: C.muted }}>/100</span>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ height: 6, background: '#1A2740', borderRadius: 3, marginBottom: 6 }}>
                      <div style={{ width: `${ms}%`, height: '100%', background: sc, borderRadius: 3 }} />
                    </div>
                    {lbl && (
                      <span style={{
                        fontSize: 9, fontWeight: 700, padding: '2px 8px',
                        borderRadius: 3, background: lbg, color: lfg,
                      }}>{lbl}</span>
                    )}
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
                  {[
                    { label: 'Insider Buy/Sell', value: m.holding_score != null ? `${Number(m.holding_score).toFixed(0)}/100` : '--' },
                    { label: 'Announcements', value: m.announcement_score != null ? `${Number(m.announcement_score).toFixed(0)}/100` : '--' },
                    { label: 'AI Tone', value: m.ai_tone_score != null ? `${Number(m.ai_tone_score).toFixed(0)}/100` : '--' },
                  ].map(({ label, value }) => (
                    <div key={label} style={{
                      background: C.bgDeep, border: C.border, borderRadius: 5, padding: '7px 8px', textAlign: 'center',
                    }}>
                      <div style={{ color: C.muted, fontSize: 8, marginBottom: 3 }}>{label}</div>
                      <div style={{ color: C.secondary, fontSize: 12, fontWeight: 700 }}>{value}</div>
                    </div>
                  ))}
                </div>
              </Card>
            )
          })()}

          {/* Phase G: Multi-signal consensus */}
          {data.consensus && (data.consensus as Record<string, unknown>).consensus_label && (
            <ConsensusCard con={data.consensus as Record<string, unknown>} />
          )}

          {/* Phase F: Alt-data intelligence */}
          {data.news && Object.keys(data.news as object).length > 0 && (
            <NewsCard news={data.news as Record<string, unknown>} />
          )}
          {data.insider && Object.keys(data.insider as object).length > 0 && (
            <InsiderCard insider={data.insider as Record<string, unknown>} />
          )}
          {data.concall && Object.keys(data.concall as object).length > 0 && (
            <ConcallCard concall={data.concall as Record<string, unknown>} />
          )}

          {/* Phase H: AGM governance signal */}
          {data.agm && Object.keys(data.agm as object).length > 0 && (() => {
            const agm = data.agm as Record<string, unknown>
            if (!agm.governance_risk) return null
            const risk = String(agm.governance_risk)
            const rc = risk === 'LOW' ? C.bull : risk === 'HIGH' ? C.bear : C.neutral
            const divSig = String(agm.dividend_signal ?? '')
            const mgmtChg = String(agm.management_change ?? '')
            const capex = String(agm.capex_confirm ?? '')
            return (
              <Card title={`GOVERNANCE SIGNAL${agm.date ? ` (${String(agm.date)})` : ''}`} accentColor={rc}>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
                  <div>
                    <div style={LABEL}>Risk</div>
                    <span style={{
                      display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
                      padding: '3px 10px', borderRadius: 4, background: rc + '22', color: rc, border: `1px solid ${rc}44`,
                    }}>{risk}</span>
                  </div>
                  {divSig && divSig !== 'NONE' && (
                    <div>
                      <div style={LABEL}>Dividend</div>
                      <span style={{
                        display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
                        padding: '3px 10px', borderRadius: 4,
                        background: C.bull + '22', color: C.bull, border: `1px solid ${C.bull}44`,
                      }}>{divSig}</span>
                    </div>
                  )}
                  {mgmtChg === 'YES' && (
                    <div>
                      <div style={LABEL}>Mgmt Change</div>
                      <span style={{
                        display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
                        padding: '3px 10px', borderRadius: 4,
                        background: C.neutral + '22', color: C.neutral, border: `1px solid ${C.neutral}44`,
                      }}>YES</span>
                    </div>
                  )}
                  {capex === 'YES' && (
                    <div>
                      <div style={LABEL}>Capex</div>
                      <span style={{
                        display: 'inline-block', marginTop: 5, fontSize: 10, fontWeight: 700,
                        padding: '3px 10px', borderRadius: 4,
                        background: C.blue + '22', color: C.blue, border: `1px solid ${C.blue}44`,
                      }}>CONFIRMED</span>
                    </div>
                  )}
                </div>
                {agm.key_decision && (
                  <div style={{
                    fontSize: 10, color: C.secondary, background: C.bgDeep,
                    padding: '7px 10px', borderRadius: 5, border: C.border, lineHeight: 1.5,
                  }}>
                    {String(agm.key_decision)}
                  </div>
                )}
              </Card>
            )
          })()}

          {/* Corporate Announcements feed */}
          {symbol && <AnnouncementsCard symbol={symbol} />}

          {/* Sector link */}
          <Link to={`/sectors/${data.sector}`} style={{
            display: 'block', textAlign: 'center', padding: '10px 0',
            color: C.blue, fontSize: 12, textDecoration: 'none',
            border: '1px solid #1E3A5F', borderRadius: 8, background: '#0A1220',
            fontWeight: 600, letterSpacing: 0.5,
          }}>
            View {data.sector} Sector Intelligence &rarr;
          </Link>
        </div>
      </div>
    </div>
  )
}
