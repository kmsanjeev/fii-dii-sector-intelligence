/**
 * ReportPage — Print-optimised stock intelligence report
 * Route: /report/:symbol
 *
 * Full replica of StocksPage data, formatted for A4 paper.
 * Print button triggers browser print dialog (choose printer or Save as PDF).
 * Download PDF button also triggers print dialog with PDF preset hint.
 */

import { useEffect, useRef, type ReactNode } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  api, fetchStockDetail, fetchStockCorpActions, fetchStockAnnouncements,
  type TechnicalIndicators, type FnoData, type Announcement, type CorpAction,
} from '../api/client'
import { AstroSignalCard, type AstroSignal } from '../components/platform/AstroSignalCard'
import { KundliCard } from '../components/platform/KundliCard'
import { TradeIntelligenceCard } from '../components/platform/TradeIntelligenceCard'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { T, FS, FW } from '../styles/tokens'

// ── Design tokens (same as StocksPage) ─────────────────────────────────────

const P = {
  bg:     T.bg,
  panel:  T.panel,
  cell:   T.cell,
  border: T.border,
  litBdr: T.borderHi,
  text:   T.text,
  sub:    T.textSub,
  dim:    T.muted,
  green:  T.green,
  red:    T.red,
  blue:   T.blue,
  amber:  T.amber,
  purple: T.purple,
  teal:   T.teal,
}

const LABEL: React.CSSProperties = {
  fontSize: FS.caption, color: P.dim, fontWeight: FW.heavy,
  letterSpacing: 1, textTransform: 'uppercase' as const,
}

const CARD_HDR_STYLE: React.CSSProperties = {
  padding: '10px 14px', fontSize: FS.label, fontWeight: FW.heavy,
  letterSpacing: 1, textTransform: 'uppercase' as const, color: P.sub,
  borderBottom: `1px solid ${P.border}`,
}

// ── OHLCV type ─────────────────────────────────────────────────────────────
type Bar = { time: string | number; open: number; high: number; low: number; close: number; volume: number }
type OhlcvResponse = { bars: Bar[]; count: number; from: string | number | null; to: string | number | null }

const fetchOhlcv = (sym: string) =>
  api.get<OhlcvResponse>('/charts/ohlcv', { params: { symbol: sym, timeframe: '1D' } }).then(r => r.data)

// ── Formatting helpers ─────────────────────────────────────────────────────

function crFmt(v: number): string {
  if (v >= 1e5) return `${(v / 1e5).toFixed(1)}L Cr`
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K Cr`
  return `${v.toFixed(0)} Cr`
}

function pct(v: number | null | undefined): string {
  if (v == null) return '--'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}

function scoreColor(v: number | null | undefined): string {
  if (v == null) return P.dim
  return v >= 65 ? P.green : v >= 42 ? P.amber : P.red
}

// ── Shared sub-components ──────────────────────────────────────────────────

function RCard({
  title, accentColor, children, pageBreak = false,
}: {
  title: string; accentColor?: string; children: ReactNode; pageBreak?: boolean
}) {
  return (
    <div
      className="r-card"
      style={{
        background: P.panel, borderRadius: 8, overflow: 'hidden',
        border: `1px solid ${P.border}`,
        borderTop: accentColor ? `3px solid ${accentColor}` : `1px solid ${P.border}`,
        pageBreakInside: 'avoid',
        breakInside: 'avoid',
        marginBottom: pageBreak ? 0 : undefined,
      }}
    >
      <div style={CARD_HDR_STYLE}>{title}</div>
      <div style={{ padding: 14 }}>{children}</div>
    </div>
  )
}

function RSectionDivider({ label }: { label: string }) {
  return (
    <div className="r-divider" style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '4px 0 2px' }}>
      <div style={{ fontSize: 9, fontWeight: 800, color: P.dim, letterSpacing: '0.12em', flexShrink: 0 }}>{label}</div>
      <div style={{ flex: 1, height: 1, background: P.border }} />
    </div>
  )
}

function RScoreBar({ label, value, max = 100, color }: { label: string; value: number | null | undefined; max?: number; color?: string }) {
  if (value == null) return null
  const fill = Math.min(Math.max(value / max, 0), 1) * 100
  const c = color ?? scoreColor(max === 100 ? value : value / max * 100)
  return (
    <div style={{ marginBottom: 7 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: 10, color: P.sub }}>{label}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: c, fontVariantNumeric: 'tabular-nums' }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ height: 3, background: '#1A2D44', borderRadius: 2 }}>
        <div style={{ width: `${fill}%`, height: '100%', background: c, borderRadius: 2 }} />
      </div>
    </div>
  )
}

function RChip({ label, color, size = 10 }: { label: string; color: string; size?: number }) {
  return (
    <span style={{
      fontSize: size - 1, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
      background: color + '20', color, border: `1px solid ${color}40`, letterSpacing: 0.4,
    }}>{label}</span>
  )
}

function RFundTile({ label, value, sub, hdrBg, valColor }: {
  label: string; value: ReactNode; sub?: string; hdrBg: string; valColor?: string
}) {
  return (
    <div style={{ background: P.cell, border: `1px solid ${P.border}`, borderRadius: 8, overflow: 'hidden', pageBreakInside: 'avoid', breakInside: 'avoid' }}>
      <div style={{ background: hdrBg, padding: '5px 10px', fontSize: FS.caption, fontWeight: FW.heavy, letterSpacing: 1.1, color: 'rgba(255,255,255,0.92)', textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ padding: '9px 10px 8px' }}>
        <div style={{ fontSize: 18, fontWeight: FW.black, fontFamily: 'monospace', color: valColor ?? P.text, lineHeight: 1.1 }}>{value}</div>
        {sub && <div style={{ fontSize: FS.label, color: T.muted, marginTop: 4 }}>{sub}</div>}
      </div>
    </div>
  )
}

function RDMARow({ label, dma, close, color }: { label: string; dma: number | null; close: number; color: string }) {
  if (dma == null) return null
  const diff = (close - dma) / dma * 100
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
      <span style={{ color: P.dim, fontSize: 10, minWidth: 50 }}>{label}</span>
      <span style={{ color: P.sub, fontSize: 10, minWidth: 60, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        &#8377;{dma.toFixed(0)}
      </span>
      <span style={{ fontSize: 10, fontWeight: 700, minWidth: 48, color: diff >= 0 ? P.green : P.red, fontVariantNumeric: 'tabular-nums' }}>
        {diff >= 0 ? '+' : ''}{diff.toFixed(1)}%
      </span>
      <div style={{ flex: 1, height: 3, background: P.border, borderRadius: 2, maxWidth: 80 }}>
        <div style={{ width: `${Math.min(100, Math.abs(diff) / 20 * 100)}%`, height: '100%', background: color, opacity: diff >= 0 ? 1 : 0.4, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 8, color, fontWeight: 700, minWidth: 20 }}>{diff >= 0 ? 'ABV' : 'BLW'}</span>
    </div>
  )
}

// Corporate actions
const CA_CFG: Record<string, { color: string; bg: string; label: string }> = {
  DIVIDEND: { color: P.amber, bg: '#F5A52414', label: 'Dividend' },
  BONUS:    { color: P.green, bg: '#22D35E14', label: 'Bonus' },
  SPLIT:    { color: P.blue,  bg: '#4080FF14', label: 'Split' },
  BUYBACK:  { color: P.purple,bg: '#A855F714', label: 'Buyback' },
  RIGHTS:   { color: P.teal,  bg: '#0EC4A014', label: 'Rights' },
}

function caDisplay(a: CorpAction): string {
  if (a.action_type === 'DIVIDEND' && a.dividend_rs != null) return `₹${a.dividend_rs.toFixed(2)}/sh`
  if (a.action_type === 'BONUS'    && a.bonus_ratio  != null) return `1:${a.bonus_ratio.toFixed(0)}`
  if (a.action_type === 'SPLIT'    && a.split_new_fv != null) return `FV ₹${a.split_new_fv}`
  if (a.action_type === 'BUYBACK') return 'Offer'
  if (a.action_type === 'RIGHTS')  return 'Rights'
  return a.subject.slice(0, 14)
}

// ── Print CSS injected into document head ──────────────────────────────────

const PRINT_CSS = `
@media print {
  @page {
    size: A4 portrait;
    margin: 12mm 14mm;
  }

  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }

  body, html {
    background: #ffffff !important;
  }

  /* Hide navigation shell and AppShell elements */
  nav, aside, header[class*="shell"], footer[class*="shell"],
  [class*="sidebar"], [class*="navbar"], [class*="topbar"],
  [data-no-print], .no-print {
    display: none !important;
  }

  /* Page layout */
  .report-root {
    background: #ffffff !important;
    color: #111827 !important;
    padding: 0 !important;
    max-width: 100% !important;
  }

  /* Print toolbar hidden */
  .report-toolbar {
    display: none !important;
  }

  /* Report header */
  .report-header {
    background: #1e3a5f !important;
    color: #ffffff !important;
    padding: 14px 16px !important;
    border-radius: 0 !important;
    border-bottom: 3px solid #3b82f6 !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* Cards: white bg, dark border */
  .r-card {
    background: #f8fafc !important;
    border: 1px solid #d1d5db !important;
    border-radius: 6px !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    margin-bottom: 8px !important;
  }

  .r-card > div:first-child {
    background: #f1f5f9 !important;
    color: #374151 !important;
    border-bottom: 1px solid #d1d5db !important;
  }

  /* Section dividers */
  .r-divider {
    page-break-after: avoid !important;
    break-after: avoid !important;
  }

  /* Score strip tiles */
  .score-tile {
    background: #f8fafc !important;
    border: 1px solid #d1d5db !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* Fund tiles */
  .fund-tile-inner {
    background: #f8fafc !important;
    border: 1px solid #d1d5db !important;
  }

  /* Text colors in print */
  .print-text-dark {
    color: #111827 !important;
  }

  /* Tables */
  table {
    border-collapse: collapse !important;
    width: 100% !important;
  }

  th, td {
    border: 1px solid #e5e7eb !important;
    padding: 4px 8px !important;
    color: #111827 !important;
    font-size: 9pt !important;
  }

  th {
    background: #f1f5f9 !important;
    font-weight: 700 !important;
  }

  /* Page break hints */
  .pb-before {
    page-break-before: always !important;
    break-before: page !important;
  }

  .pb-avoid {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* OHLCV bar in print */
  .ohlcv-bar-bg {
    background: #e5e7eb !important;
  }
}
`

// ── Main component ─────────────────────────────────────────────────────────

export function ReportPage() {
  const { symbol: urlSym } = useParams<{ symbol?: string }>()
  const symbol = (urlSym ?? '').toUpperCase()

  // Inject print CSS once
  const cssInjected = useRef(false)
  useEffect(() => {
    if (cssInjected.current) return
    cssInjected.current = true
    const style = document.createElement('style')
    style.id = 'report-print-css'
    style.textContent = PRINT_CSS
    document.head.appendChild(style)
    return () => {
      const el = document.getElementById('report-print-css')
      if (el) el.remove()
    }
  }, [])

  // ── Data queries ─────────────────────────────────────────────────────────

  const { data: detail, isLoading } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockDetail(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })

  const { data: ohlcv } = useQuery({
    queryKey: ['stocks-ohlcv', symbol, '1D'],
    queryFn: () => fetchOhlcv(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })

  const { data: corpActionsData } = useQuery({
    queryKey: ['stock-ca', symbol],
    queryFn: () => fetchStockCorpActions(symbol, 6),
    enabled: !!symbol,
    staleTime: 10 * 60_000,
  })

  const { data: announcementsData } = useQuery({
    queryKey: ['stock-ann', symbol],
    queryFn: () => fetchStockAnnouncements(symbol, 8),
    enabled: !!symbol,
    staleTime: 10 * 60_000,
  })

  // ── Derived data ──────────────────────────────────────────────────────────

  const t        = detail?.technical as TechnicalIndicators | undefined
  const f        = detail?.fno as FnoData | undefined
  const fund     = (detail?.fundamentals ?? {}) as Record<string, number | string | null>
  const shp      = (detail?.shareholding ?? {}) as Record<string, number | string | null>
  type KV = Record<string, string | number | null>
  const trends   = Array.isArray(detail?.holding_trends) ? detail!.holding_trends as KV[] : []
  const mgmt     = (detail?.management ?? {}) as KV
  const concall  = (detail?.concall ?? {}) as KV
  const agm      = (detail?.agm ?? {}) as KV
  const news     = (detail?.news ?? {}) as KV
  const consensus = (detail?.consensus ?? {}) as KV
  const insights  = detail?.analyst_insights as string[] | undefined
  const close     = detail?.close_now ?? ohlcv?.bars.at(-1)?.close ?? 0
  const latest    = ohlcv?.bars.at(-1)
  const prev      = ohlcv?.bars.at(-2)
  const chg1dPct  = (latest && prev) ? ((latest.close - prev.close) / prev.close * 100) : (detail?.price?.change_1d_pct ?? null)
  const chg1dAbs  = (latest && prev) ? (latest.close - prev.close) : (detail?.price?.change_1d_abs ?? null)

  const trendColor = t?.trend_signal === 'STRONG_UPTREND' ? P.green
    : t?.trend_signal === 'UPTREND' ? P.teal
    : t?.trend_signal === 'CONSOLIDATING' ? P.amber
    : t?.trend_signal ? P.red : P.dim

  const corpActions = corpActionsData?.actions ?? []
  const announcements = announcementsData?.announcements ?? []

  const today = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })

  // ── Print handlers ────────────────────────────────────────────────────────

  const handlePrint = () => window.print()

  // ── No symbol state ───────────────────────────────────────────────────────

  if (!symbol) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 120px)', gap: 16 }}>
        <div style={{ fontSize: 18, fontWeight: 800, color: P.text }}>Stock Intelligence Report</div>
        <div style={{ fontSize: 13, color: P.sub }}>Open <code style={{ color: P.amber }}>/report/SYMBOL</code> to generate a report</div>
        <div style={{ fontSize: 11, color: P.dim }}>Example: <a href="/report/RELIANCE" style={{ color: P.blue }}>/report/RELIANCE</a></div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 120px)', color: P.sub }}>
        Loading intelligence report for {symbol}...
      </div>
    )
  }

  // ── Report ────────────────────────────────────────────────────────────────

  return (
    <div
      className="report-root"
      style={{ background: P.bg, padding: '0 0 40px', minHeight: '100%' }}
    >

      {/* ── Print Toolbar (hidden when printing) ─────────────────────── */}
      <div
        className="report-toolbar no-print"
        style={{
          position: 'sticky', top: 0, zIndex: 100,
          background: '#0A111F', borderBottom: `1px solid ${P.border}`,
          padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 12,
        }}
      >
        <div style={{ fontSize: FS.body, fontWeight: FW.heavy, color: P.text, letterSpacing: 0.5 }}>
          STOCK INTELLIGENCE REPORT
        </div>
        <span style={{ fontSize: FS.label, color: P.dim }}>{symbol}</span>
        <div style={{ flex: 1 }} />

        {/* Print button */}
        <button
          onClick={handlePrint}
          title="Print report (Ctrl+P)"
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 16px', borderRadius: 6,
            background: P.blue + '22', border: `1px solid ${P.blue}66`,
            color: P.blue, fontSize: FS.body, fontWeight: FW.bold,
            cursor: 'pointer', letterSpacing: 0.3,
          }}
        >
          <PrintIcon />
          Print
        </button>

        {/* Download PDF button */}
        <button
          onClick={handlePrint}
          title="Save as PDF — select 'Save as PDF' in print dialog"
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 16px', borderRadius: 6,
            background: P.green + '22', border: `1px solid ${P.green}66`,
            color: P.green, fontSize: FS.body, fontWeight: FW.bold,
            cursor: 'pointer', letterSpacing: 0.3,
          }}
        >
          <PdfIcon />
          Download PDF
        </button>

        <Link
          to={`/stocks/${symbol}`}
          style={{
            display: 'flex', alignItems: 'center', gap: 5,
            padding: '7px 14px', borderRadius: 6,
            background: 'transparent', border: `1px solid ${P.border}`,
            color: P.sub, fontSize: FS.body, textDecoration: 'none',
          }}
        >
          <BackIcon />
          Back to Stock
        </Link>
      </div>

      {/* print hint */}
      <div
        className="no-print"
        style={{ textAlign: 'center', padding: '7px', fontSize: FS.label, color: P.dim, background: '#0D1420', borderBottom: `1px solid ${P.border}` }}
      >
        In the print dialog, select <strong style={{ color: P.amber }}>Save as PDF</strong> to download as PDF file. Optimised for A4 paper.
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '16px 16px 0' }}>

        {/* ══ REPORT HEADER ═══════════════════════════════════════════════════ */}
        <div
          className="report-header"
          style={{
            background: `linear-gradient(135deg, #0E1E3A, #102040)`,
            border: `1px solid ${P.litBdr}`, borderRadius: 10,
            padding: '18px 22px', marginBottom: 16,
            display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
            flexWrap: 'wrap', gap: 12,
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 28, fontWeight: FW.black, color: P.text, fontFamily: 'monospace', letterSpacing: 2 }}>{symbol}</span>
              {detail?.sector && (
                <span style={{ fontSize: FS.body, color: P.sub, fontWeight: FW.medium }}>{detail.sector}</span>
              )}
              {detail?.label && <CapFlowBadge label={detail.label} />}
            </div>
            {detail && (
              <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap', alignItems: 'baseline' }}>
                <span style={{ fontSize: 24, fontWeight: FW.black, color: P.text, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>
                  &#8377;{close > 0 ? close.toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 }) : '--'}
                </span>
                {chg1dPct != null && (
                  <span style={{ fontSize: 14, fontWeight: FW.bold, color: chg1dPct >= 0 ? P.green : P.red }}>
                    {chg1dPct >= 0 ? '+' : ''}{chg1dPct.toFixed(2)}%
                    {chg1dAbs != null && ` (${chg1dAbs >= 0 ? '+' : ''}${chg1dAbs.toFixed(2)})`}
                  </span>
                )}
                {detail.price.ret_30d != null && (
                  <span style={{ fontSize: 11, color: P.sub }}>
                    30D: <span style={{ fontWeight: FW.bold, color: detail.price.ret_30d >= 0 ? P.green : P.red }}>{pct(detail.price.ret_30d)}</span>
                  </span>
                )}
                {detail.price.ret_365d != null && (
                  <span style={{ fontSize: 11, color: P.sub }}>
                    1Y: <span style={{ fontWeight: FW.bold, color: detail.price.ret_365d >= 0 ? P.green : P.red }}>{pct(detail.price.ret_365d)}</span>
                  </span>
                )}
              </div>
            )}
            <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              {t?.trend_signal && t.trend_signal !== 'INSUFFICIENT_DATA' && (
                <RChip label={t.trend_signal.replace(/_/g, ' ')} color={trendColor} />
              )}
              {f?.oi_signal && (
                <RChip label={`F&O: ${f.oi_signal.replace(/_/g, ' ')}`} color={f.oi_signal.includes('LONG') ? P.green : P.red} />
              )}
              {detail?.sector_rotation_signal && (
                <RChip label={`Sector: ${detail.sector_rotation_signal}`} color={P.purple} />
              )}
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 12 }}>
            <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
              {detail && <ScoreGauge score={detail.bull_run_score} size={58} />}
              {detail?.ml_scores?.ml_bull_run_score != null && (
                <div style={{ textAlign: 'center' }}>
                  <ScoreGauge score={detail.ml_scores.ml_bull_run_score} size={46} />
                  <div style={{ fontSize: 8, color: P.dim, marginTop: 2 }}>ML</div>
                </div>
              )}
            </div>
            <div style={{ fontSize: FS.caption, color: P.dim, textAlign: 'right' }}>
              <div>Generated: {today}</div>
              <div>NSE: <a href={`https://www.nseindia.com/get-quotes/equity?symbol=${symbol}`} target="_blank" rel="noopener noreferrer" style={{ color: P.blue }}>{symbol}</a></div>
              {detail?.as_of_date && <div>Data as of: {detail.as_of_date}</div>}
            </div>
          </div>
        </div>

        {/* ══ SCORE STRIP ═════════════════════════════════════════════════════ */}
        {detail && (
          <div className="pb-avoid" style={{ marginBottom: 14 }}>
            <RSectionDivider label="INTELLIGENCE SCORES" />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginTop: 6 }}>
              {[
                { label: 'Price Momentum',  value: detail.components?.price_score },
                { label: 'ATH Proximity',   value: detail.components?.ath_proximity_score ?? detail.ath_proximity_score },
                { label: 'Sector Flow',     value: detail.components?.sector_flow_score },
                { label: 'Block Deals',     value: detail.components?.deal_score },
                { label: 'Corp Events',     value: detail.components?.corporate_score },
                { label: 'ML Bull Run',     value: detail.ml_scores?.ml_bull_run_score },
                { label: 'Accumulation',    value: detail.ml_scores?.accumulation_score },
                { label: 'Fwd Return 45D',  value: detail.ml_scores?.forward_return_score, isFwd: true },
              ].filter(m => m.value != null).map(({ label, value, isFwd }) => {
                const c = (isFwd) ? P.amber : scoreColor(value!)
                return (
                  <div key={label} className="score-tile" style={{ background: P.panel, border: `1px solid ${isFwd ? P.amber + '55' : P.border}`, borderRadius: 7, padding: '9px 12px', borderLeft: `3px solid ${c}` }}>
                    <div style={{ ...LABEL, marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: 22, fontWeight: FW.black, color: c, fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }}>
                      {value!.toFixed(0)}
                    </div>
                    <div style={{ height: 3, background: P.border, borderRadius: 2, marginTop: 5 }}>
                      <div style={{ width: `${Math.min(value!, 100)}%`, height: '100%', background: c, borderRadius: 2 }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {detail && (
          <>

            {/* ══ THESIS & CONVICTION ═════════════════════════════════════════ */}
            {(detail.structured_thesis || (insights && insights.length > 0)) && (
              <>
                <RSectionDivider label="THESIS & CONVICTION" />
                <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 14, marginTop: 6 }}>
                  {detail.structured_thesis && (
                    <div style={{ flex: '1 1 320px', minWidth: 280 }}>
                      <RCard
                        title={`Investment Verdict: ${detail.structured_thesis.verdict}`}
                        accentColor={detail.structured_thesis.verdict === 'BUY' || detail.structured_thesis.verdict === 'STRONG_BUY' ? P.green : detail.structured_thesis.verdict === 'SELL' || detail.structured_thesis.verdict === 'AVOID' ? P.red : P.amber}
                      >
                        <div style={{ display: 'flex', gap: 20, marginBottom: 14 }}>
                          <div>
                            <div style={LABEL}>Score</div>
                            <div style={{ fontSize: 28, fontWeight: FW.black, color: scoreColor(detail.structured_thesis.score), fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums', marginTop: 4 }}>{detail.structured_thesis.score}</div>
                          </div>
                          <div>
                            <div style={LABEL}>Confidence</div>
                            <RChip label={detail.structured_thesis.confidence} color={P.blue} size={12} />
                          </div>
                          {detail.structured_thesis.dominant_factor && (
                            <div>
                              <div style={LABEL}>Dominant Factor</div>
                              <div style={{ fontSize: 11, color: P.sub, marginTop: 4 }}>{detail.structured_thesis.dominant_factor.replace(/_/g, ' ')}</div>
                            </div>
                          )}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                          {detail.structured_thesis.bull_signals.length > 0 && (
                            <div>
                              <div style={{ fontSize: 9, fontWeight: FW.heavy, color: P.green, letterSpacing: 1, marginBottom: 6 }}>BULL SIGNALS</div>
                              {detail.structured_thesis.bull_signals.map((s, i) => (
                                <div key={i} style={{ fontSize: 10, color: P.sub, padding: '3px 0', borderBottom: `1px solid ${P.border}20`, lineHeight: 1.4 }}>
                                  <span style={{ color: P.green, marginRight: 4 }}>+</span>{s}
                                </div>
                              ))}
                            </div>
                          )}
                          {detail.structured_thesis.bear_signals.length > 0 && (
                            <div>
                              <div style={{ fontSize: 9, fontWeight: FW.heavy, color: P.red, letterSpacing: 1, marginBottom: 6 }}>BEAR SIGNALS</div>
                              {detail.structured_thesis.bear_signals.map((s, i) => (
                                <div key={i} style={{ fontSize: 10, color: P.sub, padding: '3px 0', borderBottom: `1px solid ${P.border}20`, lineHeight: 1.4 }}>
                                  <span style={{ color: P.red, marginRight: 4 }}>-</span>{s}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        {detail.structured_thesis.conflict_note && (
                          <div style={{ marginTop: 10, fontSize: 10, color: P.amber, background: P.amber + '0C', border: `1px solid ${P.amber}28`, borderRadius: 5, padding: '7px 10px' }}>
                            {detail.structured_thesis.conflict_note}
                          </div>
                        )}
                        {detail.structured_thesis.ml_note && (
                          <div style={{ marginTop: 8, fontSize: 10, color: P.blue, background: P.blue + '0C', border: `1px solid ${P.blue}28`, borderRadius: 5, padding: '7px 10px' }}>
                            ML: {detail.structured_thesis.ml_note}
                          </div>
                        )}
                      </RCard>
                    </div>
                  )}
                  {insights && insights.length > 0 && (
                    <div style={{ flex: '1 1 280px', minWidth: 260 }}>
                      <RCard title="Analyst Insights" accentColor={P.blue}>
                        {insights.map((s, i) => (
                          <div key={i} style={{ fontSize: 11, color: P.sub, padding: '5px 0', borderBottom: i < insights.length - 1 ? `1px solid ${P.border}` : 'none', lineHeight: 1.5 }}>
                            {s}
                          </div>
                        ))}
                      </RCard>
                    </div>
                  )}
                  {Object.keys(consensus).length > 0 && consensus.consensus_action && (
                    <div style={{ flex: '0 1 200px', minWidth: 180 }}>
                      <RCard title="Multi-Signal Consensus" accentColor={String(consensus.consensus_action) === 'BUY' ? P.green : String(consensus.consensus_action) === 'SELL' ? P.red : P.amber}>
                        {[
                          { label: 'Action',     value: String(consensus.consensus_action ?? ''),  color: String(consensus.consensus_action) === 'BUY' ? P.green : String(consensus.consensus_action) === 'SELL' ? P.red : P.amber },
                          { label: 'Confidence', value: String(consensus.confidence ?? ''),        color: P.blue },
                          { label: 'Signals In', value: String(consensus.signals_in ?? ''),        color: P.text },
                        ].map(({ label, value, color }) => value && (
                          <div key={label} style={{ marginBottom: 10 }}>
                            <div style={LABEL}>{label}</div>
                            <div style={{ fontSize: 16, fontWeight: FW.black, color, marginTop: 4 }}>{value.replace(/_/g, ' ')}</div>
                          </div>
                        ))}
                      </RCard>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* ══ PRICE HISTORY TABLE (replaces interactive chart) ═══════════ */}
            {ohlcv && ohlcv.bars.length > 0 && (
              <div className="pb-avoid" style={{ marginBottom: 14 }}>
                <RSectionDivider label="RECENT PRICE HISTORY (LAST 30 SESSIONS)" />
                <div style={{ overflowX: 'auto', marginTop: 6 }}>
                  <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse', fontFamily: 'monospace' }}>
                    <thead>
                      <tr>
                        {['Date', 'Open', 'High', 'Low', 'Close', 'Volume (L)', 'Chg%'].map(h => (
                          <th key={h} style={{ padding: '4px 8px', textAlign: h === 'Date' ? 'left' : 'right', color: P.dim, fontSize: 9, fontWeight: FW.heavy, letterSpacing: 0.8, borderBottom: `2px solid ${P.border}`, background: P.cell }}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {ohlcv.bars.slice(-30).reverse().map((bar, i) => {
                        const prevBar = ohlcv.bars.slice(-30)[ohlcv.bars.slice(-30).length - 1 - i - 1]
                        const chgPct = prevBar ? (bar.close - prevBar.close) / prevBar.close * 100 : null
                        const up = (chgPct ?? 0) >= 0
                        return (
                          <tr key={i} style={{ borderBottom: `1px solid ${P.border}20` }}>
                            <td style={{ padding: '4px 8px', color: P.sub, fontSize: 9 }}>
                              {typeof bar.time === 'string' ? bar.time : new Date(+bar.time * 1000).toISOString().slice(0, 10)}
                            </td>
                            {[bar.open, bar.high, bar.low, bar.close].map((v, vi) => (
                              <td key={vi} style={{ padding: '4px 8px', textAlign: 'right', color: vi === 1 ? P.green : vi === 2 ? P.red : P.text, fontVariantNumeric: 'tabular-nums', fontSize: 9 }}>
                                {v.toFixed(2)}
                              </td>
                            ))}
                            <td style={{ padding: '4px 8px', textAlign: 'right', color: P.sub, fontVariantNumeric: 'tabular-nums', fontSize: 9 }}>
                              {bar.volume != null ? ((bar.volume) / 1e5).toFixed(2) : '--'}
                            </td>
                            <td style={{ padding: '4px 8px', textAlign: 'right', color: chgPct == null ? P.dim : up ? P.green : P.red, fontVariantNumeric: 'tabular-nums', fontSize: 9, fontWeight: chgPct != null ? FW.bold : FW.regular }}>
                              {chgPct == null ? '--' : `${up ? '+' : ''}${chgPct.toFixed(2)}%`}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ══ PRICE & TECHNICALS ══════════════════════════════════════════ */}
            <RSectionDivider label="PRICE & TECHNICALS" />
            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6, marginBottom: 14 }}>

              {/* Technical Indicators */}
              {t && (
                <div style={{ flex: '1 1 260px', minWidth: 240 }}>
                  <RCard title="Technical Indicators" accentColor={trendColor}>
                    <div style={{ marginBottom: 12 }}>
                      {t.high_52w != null && (
                        <div style={{ marginBottom: 10 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: P.dim, marginBottom: 4 }}>
                            <span>52W Low {t.low_52w != null ? `₹${t.low_52w.toFixed(0)}` : '--'}</span>
                            <span style={{ color: P.text, fontWeight: 700 }}>Now ₹{close.toFixed(0)}</span>
                            <span>52W High ₹{t.high_52w.toFixed(0)}</span>
                          </div>
                          {t.low_52w != null && t.high_52w != null && (
                            <div style={{ height: 5, background: P.border, borderRadius: 3, position: 'relative' }}>
                              <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(to right, ${P.red}44, ${P.border}, ${P.green}44)`, borderRadius: 3 }} />
                              <div style={{
                                position: 'absolute', top: -3,
                                left: `${Math.max(0, Math.min(100, (close - t.low_52w) / (t.high_52w - t.low_52w) * 100))}%`,
                                width: 11, height: 11, borderRadius: '50%',
                                background: P.blue, transform: 'translateX(-50%)',
                                border: `2px solid ${P.bg}`,
                              }} />
                            </div>
                          )}
                          {t.prox_52w_high != null && (
                            <div style={{ fontSize: 9, color: P.dim, marginTop: 4 }}>
                              {t.prox_52w_high.toFixed(1)}% from 52-week high
                            </div>
                          )}
                        </div>
                      )}
                      {t.trend_signal && t.trend_signal !== 'INSUFFICIENT_DATA' && (
                        <div style={{ marginBottom: 8 }}>
                          <div style={LABEL}>Trend Signal</div>
                          <div style={{ marginTop: 5 }}>
                            <RChip label={t.trend_signal.replace(/_/g, ' ')} color={trendColor} size={12} />
                          </div>
                        </div>
                      )}
                      <RDMARow label="20 DMA"  dma={t.dma_20}  close={close} color={P.blue} />
                      <RDMARow label="50 DMA"  dma={t.dma_50}  close={close} color="#A78BFA" />
                      <RDMARow label="200 DMA" dma={t.dma_200} close={close} color={P.amber} />
                      {t.as_of_date && <div style={{ fontSize: 9, color: P.dim, marginTop: 6 }}>as of {t.as_of_date}</div>}
                    </div>
                  </RCard>
                </div>
              )}

              {/* Key Levels */}
              {detail.key_levels && detail.key_levels.conf_res_1 != null && (() => {
                const kl = detail.key_levels!
                const fmt = (v: number | null) => v != null ? `₹${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '--'
                return (
                  <div style={{ flex: '1 1 260px', minWidth: 240 }}>
                    <RCard title="Key Support & Resistance" accentColor={P.teal}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
                        {[
                          { label: 'R2', value: kl.conf_res_2, color: P.red,   isRes: true },
                          { label: 'R1', value: kl.conf_res_1, color: P.red,   isRes: true },
                          { label: 'S1', value: kl.conf_sup_1, color: P.green, isRes: false },
                          { label: 'S2', value: kl.conf_sup_2, color: P.green, isRes: false },
                        ].filter(l => l.value != null).map(l => (
                          <div key={l.label} style={{ background: P.cell, border: `1px solid ${l.color}30`, borderRadius: 5, padding: '6px 10px' }}>
                            <div style={{ fontSize: 9, fontWeight: FW.heavy, color: l.color, letterSpacing: 1 }}>{l.label}</div>
                            <div style={{ fontSize: 14, fontWeight: FW.black, color: l.color, fontFamily: 'monospace', marginTop: 2 }}>{fmt(l.value!)}</div>
                            <div style={{ fontSize: 9, color: P.dim, marginTop: 1 }}>{l.value! > close ? `+${((l.value! - close) / close * 100).toFixed(1)}%` : `${((l.value! - close) / close * 100).toFixed(1)}%`}</div>
                          </div>
                        ))}
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, background: P.cell, borderRadius: 5, padding: '8px 10px', border: `1px solid ${P.border}` }}>
                        {[
                          { label: 'Entry Zone', value: kl.entry_zone_low != null && kl.entry_zone_high != null ? `${fmt(kl.entry_zone_low)}-${fmt(kl.entry_zone_high)}` : '--', color: P.teal },
                          { label: 'Stop Loss',  value: fmt(kl.stop_loss),    color: P.red },
                          { label: 'ATR (14D)',  value: kl.atr_14 != null ? `₹${kl.atr_14.toFixed(1)}` : '--', color: P.sub },
                        ].map(({ label, value, color }) => (
                          <div key={label}>
                            <div style={{ fontSize: 8, color: P.dim, letterSpacing: 0.5, marginBottom: 2 }}>{label}</div>
                            <div style={{ fontSize: 10, fontWeight: FW.black, color, fontFamily: 'monospace' }}>{value}</div>
                          </div>
                        ))}
                      </div>
                    </RCard>
                  </div>
                )
              })()}

              {/* F&O */}
              {f && f.oi_signal && (
                <div style={{ flex: '1 1 220px', minWidth: 200 }}>
                  <RCard title="Futures & Options" accentColor={f.oi_signal.includes('LONG') ? P.green : P.red}>
                    {(() => {
                      const OI_MAP: Record<string, string> = { LONG_BUILDUP: P.green, SHORT_BUILDUP: P.red, LONG_UNWINDING: P.amber, SHORT_COVERING: P.teal }
                      const OI_TEXT: Record<string, string> = { LONG_BUILDUP: 'Big traders buying fresh — bullish', SHORT_BUILDUP: 'Traders betting on fall — bearish', LONG_UNWINDING: 'Buyers exiting — weakening', SHORT_COVERING: 'Bears buying back — potential reversal' }
                      const c = OI_MAP[f.oi_signal] ?? P.sub
                      return (
                        <>
                          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
                            <div><div style={LABEL}>Signal</div><div style={{ marginTop: 5 }}><RChip label={f.oi_signal.replace(/_/g, ' ')} color={c} size={11} /></div></div>
                            {f.futures_oi != null && <div><div style={LABEL}>Open Interest</div><div style={{ fontSize: 15, fontWeight: FW.black, color: P.text, marginTop: 4 }}>{(f.futures_oi / 1e6).toFixed(2)}M</div></div>}
                            {f.oi_1d != null && <div><div style={LABEL}>1D OI Chg</div><div style={{ fontSize: 15, fontWeight: FW.black, color: f.oi_1d >= 0 ? P.green : P.red, marginTop: 4 }}>{f.oi_1d >= 0 ? '+' : ''}{f.oi_1d.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div></div>}
                          </div>
                          {OI_TEXT[f.oi_signal] && <div style={{ fontSize: 11, color: c, background: c + '12', border: `1px solid ${c}33`, padding: '6px 10px', borderRadius: 5 }}>{OI_TEXT[f.oi_signal]}</div>}
                        </>
                      )
                    })()}
                  </RCard>
                </div>
              )}
            </div>

            {/* ══ FUNDAMENTALS & VALUATION ════════════════════════════════════ */}
            <RSectionDivider label="FUNDAMENTALS & VALUATION" />
            {Object.keys(fund).length > 0 && (
              <div style={{ marginTop: 6, marginBottom: 14 }}>
                {fund._sector_note === 'BANKING_XBRL_PENDING' && (
                  <div style={{ margin: '0 0 8px', padding: '7px 12px', borderRadius: 4, background: '#0A1828', border: '1px solid #1E3A5A', fontSize: 11, color: '#64748B' }}>
                    Banking sector: P&L reported under IndAS Banking taxonomy. Standard P&L metrics may be unavailable.
                  </div>
                )}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 10 }}>
                  {/* Row 1 — Valuation & Quality */}
                  <RFundTile label="Market Cap (Cr)" hdrBg="#1A3A6E" valColor={P.text}
                    value={fund.market_cap_cr != null ? crFmt(+fund.market_cap_cr) : '--'}
                    sub={fund.shares_outstanding_cr != null ? `${(+fund.shares_outstanding_cr).toFixed(1)} Cr shares` : ''} />
                  <RFundTile label="P/E Ratio" hdrBg="#2A1800"
                    value={fund.pe_ratio != null ? `${(+fund.pe_ratio).toFixed(1)}x` : '--'}
                    valColor={fund.pe_ratio == null ? P.sub : +fund.pe_ratio < 15 ? P.green : +fund.pe_ratio > 40 ? P.red : P.amber}
                    sub="price / earnings" />
                  <RFundTile label="Book Value" hdrBg="#2D1B4E"
                    valColor={fund.book_value_per_share != null ? P.text : P.sub}
                    value={fund.book_value_per_share != null ? `₹${(+fund.book_value_per_share).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '---'}
                    sub="per share" />
                  <RFundTile label="Valuation"
                    hdrBg={fund.valuation_label === 'CHEAP_QUALITY' ? '#052E16' : fund.valuation_label === 'FAIR_VALUE' ? '#0C1A3A' : fund.valuation_label === 'EXPENSIVE' ? '#2D0A0A' : '#1A1228'}
                    value={<span style={{ fontSize: FS.md }}>{String(fund.valuation_label ?? 'N/A').replace(/_/g, ' ')}</span>}
                    valColor={fund.valuation_label === 'CHEAP_QUALITY' ? P.green : fund.valuation_label === 'FAIR_VALUE' ? P.blue : fund.valuation_label === 'EXPENSIVE' ? P.red : P.amber}
                    sub={fund.valuation_score != null ? `score ${(+fund.valuation_score).toFixed(0)}/100` : ''} />
                  <RFundTile label="ROE (%)" hdrBg="#0A2A1F"
                    value={fund.roe_pct != null ? `${(+fund.roe_pct).toFixed(1)}%` : '--'}
                    valColor={fund.roe_pct == null ? P.sub : +fund.roe_pct >= 20 ? P.green : +fund.roe_pct >= 12 ? P.teal : P.red}
                    sub="return on equity" />
                  <RFundTile label="ROCE (%)" hdrBg="#0A1A2E"
                    valColor={fund.roce_pct == null ? P.sub : +fund.roce_pct >= 20 ? P.green : +fund.roce_pct >= 12 ? P.teal : P.amber}
                    value={fund.roce_pct != null ? `${(+fund.roce_pct).toFixed(1)}%` : '---'}
                    sub="return on capital" />

                  {/* Row 2 — Income Statement */}
                  <RFundTile label="Sales (Cr)" hdrBg="#1A3A6E" valColor={P.text}
                    value={fund.revenue_ttm_cr != null ? crFmt(+fund.revenue_ttm_cr) : '--'}
                    sub="trailing 12M" />
                  <RFundTile label="PAT (Cr)" hdrBg="#2D1B4E"
                    value={fund.profit_ttm_cr != null ? crFmt(+fund.profit_ttm_cr) : '--'}
                    valColor={fund.profit_ttm_cr == null ? P.sub : +fund.profit_ttm_cr >= 0 ? P.text : P.red}
                    sub="profit after tax" />
                  <RFundTile label="OPM (%)" hdrBg="#0A1A2E"
                    valColor={fund.opm_pct == null ? P.sub : +fund.opm_pct >= 20 ? P.green : +fund.opm_pct >= 10 ? P.teal : P.amber}
                    value={fund.opm_pct != null ? `${(+fund.opm_pct).toFixed(1)}%` : '---'}
                    sub="operating margin" />
                  <RFundTile label="Qtr Sales Growth"
                    hdrBg={fund.qtr_sales_growth_pct != null && +fund.qtr_sales_growth_pct >= 0 ? '#062014' : '#200606'}
                    value={fund.qtr_sales_growth_pct != null ? `${+fund.qtr_sales_growth_pct >= 0 ? '+' : ''}${(+fund.qtr_sales_growth_pct).toFixed(1)}%` : '--'}
                    valColor={fund.qtr_sales_growth_pct == null ? P.sub : +fund.qtr_sales_growth_pct >= 10 ? P.green : +fund.qtr_sales_growth_pct >= 0 ? P.teal : P.red}
                    sub={String(fund.qtr_growth_period ?? 'vs prior period')} />
                  <RFundTile label="Qtr Profit Growth"
                    hdrBg={fund.qtr_profit_growth_pct != null && +fund.qtr_profit_growth_pct >= 0 ? '#062014' : '#200606'}
                    value={fund.qtr_profit_growth_pct != null ? `${+fund.qtr_profit_growth_pct >= 0 ? '+' : ''}${(+fund.qtr_profit_growth_pct).toFixed(1)}%` : '--'}
                    valColor={fund.qtr_profit_growth_pct == null ? P.sub : +fund.qtr_profit_growth_pct >= 10 ? P.green : +fund.qtr_profit_growth_pct >= 0 ? P.teal : P.red}
                    sub="PAT vs prior period" />
                  <RFundTile
                    label="Sales CAGR"
                    hdrBg={fund.sales_growth_3y_pct != null && +fund.sales_growth_3y_pct >= 0 ? '#062014' : '#200606'}
                    valColor={fund.sales_growth_3y_pct == null ? P.sub : +fund.sales_growth_3y_pct >= 15 ? P.green : +fund.sales_growth_3y_pct >= 5 ? P.teal : P.amber}
                    value={fund.sales_growth_3y_pct != null ? `${+fund.sales_growth_3y_pct >= 0 ? '+' : ''}${(+fund.sales_growth_3y_pct).toFixed(1)}%` : '---'}
                    sub={fund.sales_growth_years != null ? `${(+fund.sales_growth_years).toFixed(0)}Y revenue` : '3Y CAGR'} />

                  {/* Row 3 — Price Position & Ownership */}
                  <RFundTile label="1Y Return"
                    hdrBg={detail.price.ret_365d != null && detail.price.ret_365d >= 0 ? '#062014' : '#200606'}
                    value={pct(detail.price.ret_365d)}
                    valColor={detail.price.ret_365d == null ? P.sub : detail.price.ret_365d >= 0 ? P.green : P.red}
                    sub="365-day return" />
                  <RFundTile label="vs 200 DMA" hdrBg={t?.vs_dma_200 != null && t.vs_dma_200 >= 0 ? '#062014' : '#200606'}
                    value={t?.vs_dma_200 != null ? `${t.vs_dma_200 >= 0 ? '+' : ''}${t.vs_dma_200.toFixed(1)}%` : '--'}
                    valColor={t?.vs_dma_200 == null ? P.sub : t.vs_dma_200 >= 5 ? P.green : t.vs_dma_200 >= 0 ? P.teal : P.red}
                    sub="long-term trend" />
                  <RFundTile label="52W Drawdown"
                    hdrBg={fund.down_from_ath_pct != null && +fund.down_from_ath_pct >= -15 ? '#062014' : '#1A0D00'}
                    value={fund.down_from_ath_pct != null ? `${(+fund.down_from_ath_pct).toFixed(1)}%` : '--'}
                    valColor={fund.down_from_ath_pct == null ? P.sub : +fund.down_from_ath_pct >= -15 ? P.teal : +fund.down_from_ath_pct >= -40 ? P.amber : P.red}
                    sub={fund.high_52w != null ? `High ₹${(+fund.high_52w).toFixed(0)}` : '52-week high'} />
                  <RFundTile label="Vol Ratio" hdrBg="#0A1C2E"
                    value={detail.price.vol_ratio != null ? `${(+detail.price.vol_ratio).toFixed(1)}x` : '--'}
                    valColor={detail.price.vol_ratio == null ? P.sub : +detail.price.vol_ratio >= 1.5 ? P.green : +detail.price.vol_ratio >= 1 ? P.blue : P.sub}
                    sub="vs 90D avg" />
                  <RFundTile label="Promoter %" hdrBg="#1E0D3A"
                    value={shp.promoter_pct != null ? `${(+shp.promoter_pct).toFixed(1)}%` : '--'}
                    valColor={shp.promoter_pct == null ? P.sub : +shp.promoter_pct >= 65 ? P.green : +shp.promoter_pct >= 50 ? P.teal : P.amber}
                    sub="promoter holding" />
                  <RFundTile label="FII %" hdrBg="#0A2014"
                    value={shp.fii_pct != null ? `${(+shp.fii_pct).toFixed(1)}%` : '--'}
                    valColor={shp.fii_pct == null ? P.sub : +shp.fii_pct >= 10 ? P.blue : P.sub}
                    sub="foreign inst." />
                </div>

                {/* Sector peer valuation */}
                {detail.sector_peer_valuation && (() => {
                  const peers = detail.sector_peer_valuation!
                  const metrics = [
                    { label: 'P/E Ratio', stock: fund.pe_ratio,  peer: peers.sector_pe,   unit: 'x', good: 'low'  as const },
                    { label: 'ROE (%)',   stock: fund.roe_pct,   peer: peers.sector_roe,  unit: '%', good: 'high' as const },
                    { label: 'ROCE (%)',  stock: fund.roce_pct,  peer: peers.sector_roce, unit: '%', good: 'high' as const },
                  ].filter(m => m.stock != null || m.peer != null)

                  if (!metrics.length) return null
                  return (
                    <div style={{ marginTop: 12 }}>
                      <RCard title={`Valuation vs ${peers.sector ?? 'Sector'} Peers (${peers.peer_count ?? 0})`} accentColor={P.purple}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
                          {metrics.map(({ label, stock, peer, unit, good }) => {
                            const sv = stock != null ? +stock : null
                            const pv = peer  != null ? +peer  : null
                            const barMax = Math.max(sv ?? 0, pv ?? 0, 5) * 1.15
                            const vsStr = sv != null && pv != null
                              ? (good === 'low'
                                ? (sv < pv * 0.85 ? 'cheaper' : sv > pv * 1.2 ? 'expensive' : 'in-line')
                                : (sv > pv * 1.1 ? 'better' : sv < pv * 0.8 ? 'below' : 'in-line'))
                              : ''
                            const vsClr = (vsStr === 'cheaper' || vsStr === 'better') ? P.green : (vsStr === 'expensive' || vsStr === 'below') ? P.red : P.amber
                            return (
                              <div key={label}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                  <span style={{ fontSize: 10, color: P.sub }}>{label}</span>
                                  {vsStr && <span style={{ fontSize: 9, fontWeight: 700, color: vsClr }}>{vsStr}</span>}
                                </div>
                                {sv != null && (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                                    <span style={{ fontSize: 9, color: P.dim, minWidth: 34 }}>Stock</span>
                                    <div style={{ flex: 1, height: 6, background: P.border, borderRadius: 3 }}>
                                      <div style={{ width: `${Math.min(100, sv / barMax * 100)}%`, height: '100%', background: P.blue, borderRadius: 3 }} />
                                    </div>
                                    <span style={{ fontSize: 10, fontWeight: 800, color: P.blue, minWidth: 36, textAlign: 'right' }}>{sv.toFixed(1)}{unit}</span>
                                  </div>
                                )}
                                {pv != null && (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <span style={{ fontSize: 9, color: P.dim, minWidth: 34 }}>Sector</span>
                                    <div style={{ flex: 1, height: 6, background: P.border, borderRadius: 3 }}>
                                      <div style={{ width: `${Math.min(100, pv / barMax * 100)}%`, height: '100%', background: P.dim, borderRadius: 3 }} />
                                    </div>
                                    <span style={{ fontSize: 10, fontWeight: 800, color: P.dim, minWidth: 36, textAlign: 'right' }}>{pv.toFixed(1)}{unit}</span>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </RCard>
                    </div>
                  )
                })()}
              </div>
            )}

            {/* ══ INSTITUTIONAL POSITIONING ════════════════════════════════════ */}
            <RSectionDivider label="INSTITUTIONAL POSITIONING" />
            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6, marginBottom: 14 }}>
              {trends.length > 0 && (
                <div style={{ flex: '1 1 300px', minWidth: 280 }}>
                  <RCard title="Shareholding Trends (QoQ)" accentColor={P.purple}>
                    <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
                      <thead>
                        <tr>
                          {['Period', 'Promoter', 'FII', 'DII', 'Signal'].map(h => (
                            <th key={h} style={{ padding: '3px 7px', textAlign: h === 'Period' ? 'left' : 'right', color: P.dim, fontSize: 8, fontWeight: 700, letterSpacing: 1, borderBottom: `1px solid ${P.border}` }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {trends.map((r, i) => {
                          const sig_ = String(r.conviction_signal ?? '')
                          const sc = sig_.includes('ACCUMULATION') ? P.green : sig_.includes('DISTRIBUTION') ? P.red : P.dim
                          return (
                            <tr key={i} style={{ borderBottom: `1px solid ${P.border}20` }}>
                              <td style={{ padding: '4px 7px', color: P.sub, fontFamily: 'monospace', fontSize: 9 }}>{String(r.period ?? '')}</td>
                              {(['promoter_pct', 'fii_pct', 'dii_pct'] as const).map(k => {
                                const dk = k + '_delta' as keyof typeof r
                                const val = r[k]; const delta = r[dk]
                                return (
                                  <td key={k} style={{ padding: '4px 7px', textAlign: 'right', color: P.text, fontVariantNumeric: 'tabular-nums', fontSize: 9 }}>
                                    {val != null ? `${(+val).toFixed(2)}%` : '--'}
                                    {delta != null && <span style={{ color: +delta >= 0 ? P.green : P.red, marginLeft: 3, fontSize: 8 }}>{+delta >= 0 ? '+' : ''}{(+delta).toFixed(2)}</span>}
                                  </td>
                                )
                              })}
                              <td style={{ padding: '4px 7px', textAlign: 'right' }}>
                                {sig_ && <span style={{ fontSize: 7, fontWeight: 700, color: sc, padding: '1px 4px', background: sc + '18', border: `1px solid ${sc}33`, borderRadius: 2 }}>{sig_.replace(/_/g, ' ')}</span>}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </RCard>
                </div>
              )}

              <div style={{ flex: '1 1 280px', minWidth: 260, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {detail.deal_signals && (() => {
                  const d = detail.deal_signals as Record<string, string | number | null>
                  if (!d.deal_signal) return null
                  const dc = String(d.deal_signal).includes('BULL') ? P.green : String(d.deal_signal).includes('BEAR') ? P.red : P.sub
                  return (
                    <RCard title="Institutional Block Deals" accentColor={dc}>
                      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 8 }}>
                        {[
                          { label: 'Signal', value: String(d.deal_signal).replace(/_/g, ' '), color: dc },
                          { label: 'Total Deals', value: String(d.total_deals ?? '--'), color: P.text },
                          { label: 'Inst Net (Cr)', value: d.inst_net_value_cr != null ? crFmt(+d.inst_net_value_cr!) : '--', color: +d.inst_net_value_cr! >= 0 ? P.green : P.red },
                        ].map(({ label, value, color }) => (
                          <div key={label}>
                            <div style={LABEL}>{label}</div>
                            <div style={{ fontSize: 14, fontWeight: FW.black, color, marginTop: 3 }}>{value}</div>
                          </div>
                        ))}
                      </div>
                      {d.last_deal_date && <div style={{ fontSize: 9, color: P.dim }}>Last deal: {String(d.last_deal_date)} | Window: {d.window_days}D</div>}
                    </RCard>
                  )
                })()}

                {Object.keys(mgmt).length > 0 && mgmt.management_score != null && (
                  <RCard title="Management Intelligence" accentColor={+mgmt.management_score! >= 65 ? P.green : +mgmt.management_score! >= 45 ? P.amber : P.red}>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 8 }}>
                      <div>
                        <div style={LABEL}>Overall Score</div>
                        <div style={{ fontSize: 22, fontWeight: FW.black, color: scoreColor(+mgmt.management_score!), fontFamily: 'monospace', marginTop: 3 }}>{(+mgmt.management_score!).toFixed(0)}</div>
                      </div>
                      {mgmt.management_label && (
                        <div style={{ alignSelf: 'flex-end', paddingBottom: 2 }}>
                          <RChip label={String(mgmt.management_label)} color={String(mgmt.management_label) === 'POSITIVE' ? P.green : String(mgmt.management_label) === 'NEGATIVE' ? P.red : P.amber} size={11} />
                        </div>
                      )}
                    </div>
                    <RScoreBar label="Holding Signal" value={mgmt.holding_score != null ? +mgmt.holding_score : null} />
                    <RScoreBar label="Announcements"  value={mgmt.announcement_score != null ? +mgmt.announcement_score : null} />
                  </RCard>
                )}
              </div>
            </div>

            {/* ══ EVENTS & CATALYSTS ══════════════════════════════════════════ */}
            <RSectionDivider label="EVENTS & CATALYSTS" />
            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6, marginBottom: 14 }}>

              {detail.upcoming_events && detail.upcoming_events.length > 0 && (
                <div style={{ flex: '1 1 260px', minWidth: 240 }}>
                  <RCard title={`Upcoming Catalysts (next 90D)`} accentColor={P.amber}>
                    {detail.upcoming_events.map((ev, i) => {
                      const TYPE_CLR: Record<string, string> = { RESULTS: P.green, DIVIDEND: P.amber, AGM: P.purple, EGM: P.blue, BUYBACK: P.teal, OTHER: P.dim }
                      const clr = TYPE_CLR[ev.purpose_type] ?? P.sub
                      const daysFrom = Math.round((new Date(ev.event_date).getTime() - Date.now()) / 86400000)
                      return (
                        <div key={i} style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: i < detail.upcoming_events!.length - 1 ? `1px solid ${P.border}` : 'none' }}>
                          <div style={{ minWidth: 52 }}>
                            <div style={{ fontSize: 10, fontWeight: FW.black, color: P.text, fontFamily: 'monospace' }}>{ev.event_date.slice(5)}</div>
                            <div style={{ fontSize: 8, color: daysFrom <= 14 ? P.amber : P.dim }}>in {daysFrom}d</div>
                          </div>
                          <div style={{ flex: 1 }}>
                            <span style={{ fontSize: 8, fontWeight: 700, padding: '1px 6px', borderRadius: 6, background: clr + '18', color: clr, border: `1px solid ${clr}33` }}>{ev.purpose_type.replace(/_/g, ' ')}</span>
                            {ev.bm_desc && ev.bm_desc.length > 4 && (
                              <div style={{ fontSize: 9, color: P.sub, marginTop: 3, lineHeight: 1.4 }}>{ev.bm_desc.replace(/=+/g, '').trim().slice(0, 80)}{ev.bm_desc.length > 80 ? '...' : ''}</div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </RCard>
                </div>
              )}

              {Object.keys(concall).length > 0 && concall.sentiment && (
                <div style={{ flex: '1 1 240px', minWidth: 220 }}>
                  <RCard title="Concall Intelligence" accentColor={String(concall.sentiment) === 'BULLISH' ? P.green : String(concall.sentiment) === 'BEARISH' ? P.red : P.amber}>
                    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
                      {[
                        { label: 'Sentiment', value: String(concall.sentiment ?? ''),          color: String(concall.sentiment) === 'BULLISH' ? P.green : String(concall.sentiment) === 'BEARISH' ? P.red : P.amber },
                        { label: 'Guidance',  value: String(concall.guidance_direction ?? ''), color: P.blue },
                        { label: 'Capex',     value: String(concall.capex_signal ?? ''),       color: String(concall.capex_signal) === 'YES' ? P.teal : P.dim },
                      ].map(({ label, value, color }) => value && value !== 'undefined' && (
                        <div key={label}>
                          <div style={LABEL}>{label}</div>
                          <RChip label={value.replace(/_/g, ' ')} color={color} size={11} />
                        </div>
                      ))}
                    </div>
                    {concall.key_statement && (
                      <div style={{ fontSize: 10, color: P.text, background: P.cell, padding: '7px 10px', borderRadius: 5, border: `1px solid ${P.border}`, lineHeight: 1.5, fontStyle: 'italic' }}>
                        "{String(concall.key_statement)}"
                      </div>
                    )}
                    {concall.concall_score != null && <div style={{ marginTop: 8 }}><RScoreBar label="Concall Score" value={+concall.concall_score} /></div>}
                  </RCard>
                </div>
              )}

              {Object.keys(agm).length > 0 && agm.governance_risk && (
                <div style={{ flex: '1 1 220px', minWidth: 200 }}>
                  <RCard title="Governance Signal" accentColor={String(agm.governance_risk) === 'LOW' ? P.green : String(agm.governance_risk) === 'HIGH' ? P.red : P.amber}>
                    {[
                      { label: 'Governance Risk', value: String(agm.governance_risk ?? ''), color: String(agm.governance_risk) === 'LOW' ? P.green : String(agm.governance_risk) === 'HIGH' ? P.red : P.amber },
                      { label: 'ESOP Signal',      value: String(agm.esop_signal ?? ''),    color: P.blue },
                      { label: 'AGM Signal',        value: String(agm.agm_signal ?? ''),    color: P.teal },
                    ].filter(r => r.value && r.value !== 'undefined').map(({ label, value, color }) => (
                      <div key={label} style={{ marginBottom: 10 }}>
                        <div style={LABEL}>{label}</div>
                        <RChip label={value.replace(/_/g, ' ')} color={color} size={11} />
                      </div>
                    ))}
                    {agm.governance_pdf_count != null && (
                      <div style={{ fontSize: 9, color: P.dim }}>AGM PDFs analyzed: {String(agm.governance_pdf_count)}</div>
                    )}
                  </RCard>
                </div>
              )}

              {Object.keys(news).length > 0 && news.news_count_7d != null && +news.news_count_7d > 0 && (
                <div style={{ flex: '1 1 220px', minWidth: 200 }}>
                  <RCard title="Recent News Signal" accentColor={P.blue}>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 10 }}>
                      {[
                        { label: 'Articles (7D)', value: String(news.news_count_7d), color: P.text },
                        { label: 'Sentiment',     value: String(news.sentiment_label ?? ''), color: String(news.sentiment_label) === 'BULLISH' ? P.green : String(news.sentiment_label) === 'BEARISH' ? P.red : P.amber },
                        { label: 'Bullish',       value: String(news.bullish_count ?? 0), color: P.green },
                        { label: 'Bearish',       value: String(news.bearish_count ?? 0), color: P.red },
                      ].map(({ label, value, color }) => (
                        <div key={label}>
                          <div style={LABEL}>{label}</div>
                          <div style={{ fontSize: 14, fontWeight: FW.black, color, marginTop: 3 }}>{value || '--'}</div>
                        </div>
                      ))}
                    </div>
                  </RCard>
                </div>
              )}
            </div>

            {/* ══ ASTRO SIGNAL ═══════════════════════════════════════════════ */}
            {detail.astro && detail.astro.astro_action && (
              <div className="pb-avoid">
                <RSectionDivider label="ASTRO SIGNAL" />
                <div style={{ marginTop: 6, marginBottom: 14 }}>
                  <AstroSignalCard astro={detail.astro as AstroSignal} />
                </div>
              </div>
            )}

            {/* ══ VEDIC KUNDLI + GANN ════════════════════════════════════════ */}
            <div className="pb-before">
              <RSectionDivider label="VEDIC KUNDLI + GANN" />
              <div style={{ marginTop: 6, marginBottom: 14 }}>
                <KundliCard symbol={symbol} />
              </div>
            </div>

            {/* ══ CORPORATE ══════════════════════════════════════════════════ */}
            <RSectionDivider label="CORPORATE" />
            <div style={{ marginTop: 6, marginBottom: 14 }}>
              <TradeIntelligenceCard data={detail} />
            </div>

            {/* Corporate Actions */}
            {corpActions.length > 0 && (
              <div className="pb-avoid" style={{ marginBottom: 14 }}>
                <RCard title={`Corporate Actions — Last ${corpActions.length}`} accentColor={P.amber}>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    {corpActions.map((a: CorpAction, i: number) => {
                      const cfg = CA_CFG[a.action_type] ?? { color: P.sub, bg: P.cell, label: a.action_type }
                      return (
                        <div key={i} style={{ flexShrink: 0, background: P.cell, border: `1px solid ${P.border}`, borderRadius: 7, overflow: 'hidden', minWidth: 120 }}>
                          <div style={{ padding: '4px 9px', background: cfg.bg, fontSize: 9, fontWeight: FW.heavy, letterSpacing: 0.8, color: cfg.color }}>
                            {cfg.label}
                          </div>
                          <div style={{ padding: '7px 9px' }}>
                            <div style={{ fontSize: 13, fontWeight: FW.black, color: cfg.color, fontFamily: 'monospace' }}>{caDisplay(a)}</div>
                            <div style={{ fontSize: 9, color: P.dim, marginTop: 3 }}>
                              {a.ex_date ? `Ex: ${a.ex_date}` : a.rec_date ? `Rec: ${a.rec_date}` : ''}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </RCard>
              </div>
            )}

            {/* Recent Announcements */}
            {announcements.length > 0 && (
              <div className="pb-avoid" style={{ marginBottom: 14 }}>
                <RCard title={`Key Announcements (${announcements.length})`} accentColor={P.purple}>
                  {announcements.slice(0, 8).map((ann: Announcement, i: number) => {
                    const scoreColor_ = ann.signal_score != null
                      ? (ann.signal_score >= 2 ? P.green : ann.signal_score <= -2 ? P.red : P.amber)
                      : P.dim
                    return (
                      <div key={i} style={{ padding: '6px 0', borderBottom: i < Math.min(announcements.length, 8) - 1 ? `1px solid ${P.border}` : 'none', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                        <div style={{ minWidth: 68, flexShrink: 0 }}>
                          <div style={{ fontSize: 9, color: P.sub, fontFamily: 'monospace' }}>{ann.date}</div>
                          {ann.signal_score != null && (
                            <div style={{ fontSize: 8, fontWeight: 700, color: scoreColor_, marginTop: 2 }}>
                              score {ann.signal_score > 0 ? '+' : ''}{ann.signal_score}
                            </div>
                          )}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 9, fontWeight: 700, color: P.blue, marginBottom: 2, letterSpacing: 0.3 }}>
                            {ann.announcement_type?.replace(/_/g, ' ')}
                          </div>
                          <div style={{ fontSize: 10, color: P.text, lineHeight: 1.4 }}>{ann.title}</div>
                        </div>
                      </div>
                    )
                  })}
                </RCard>
              </div>
            )}

            {/* Footer */}
            <div style={{ textAlign: 'center', padding: '16px 0 0', borderTop: `1px solid ${P.border}`, fontSize: FS.caption, color: P.dim }}>
              <div style={{ marginBottom: 4 }}>Capital Flow Intelligence Platform — {symbol} Stock Intelligence Report — Generated {today}</div>
              <div>Data sourced from NSE India. This report is for informational purposes only and does not constitute investment advice.</div>
            </div>

          </>
        )}
      </div>
    </div>
  )
}

// ── Icon helpers (inline SVG) ──────────────────────────────────────────────

function PrintIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 6 2 18 2 18 9" />
      <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
      <rect x="6" y="14" width="12" height="8" />
    </svg>
  )
}

function PdfIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="12" y1="18" x2="12" y2="12" />
      <line x1="9" y1="15" x2="15" y2="15" />
    </svg>
  )
}

function BackIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  )
}
