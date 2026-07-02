import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchStockDetail, type TechnicalIndicators, type FnoData } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { TradeIntelligenceCard } from '../components/platform/TradeIntelligenceCard'
import { StockChart } from '../components/platform/StockChart'

// ─── Tiny helpers ─────────────────────────────────────────────────────────────

function pct(v: number | null | undefined) {
  if (v == null) return '--'
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
}
function num(v: number | null | undefined, dec = 2) {
  if (v == null) return '--'
  return Number(v).toFixed(dec)
}

const SL: React.CSSProperties = { color: '#64748B', fontSize: 9, letterSpacing: 1 }

// ─── Shared card shell ────────────────────────────────────────────────────────

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16 }}>
      <div style={{ color: '#475569', fontSize: 9, letterSpacing: 2, marginBottom: 12 }}>{title}</div>
      {children}
    </div>
  )
}

// ─── Score chip ───────────────────────────────────────────────────────────────

function ScoreChip({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <ScoreGauge score={value} size={64} />
      <div style={{ color: '#64748B', fontSize: 9, marginTop: 4 }}>{label}</div>
      {sub && <div style={{ color: '#334155', fontSize: 8 }}>{sub}</div>}
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
      <span style={{ color: '#475569', fontSize: 10, minWidth: 48 }}>{label}</span>
      <span style={{ color: '#94A3B8', fontSize: 10, minWidth: 58, textAlign: 'right' }}>
        &#8377;{value.toFixed(0)}
      </span>
      <span style={{ fontSize: 10, fontWeight: 700, minWidth: 46, color: above ? '#22C55E' : '#EF4444' }}>
        {diff >= 0 ? '+' : ''}{diff.toFixed(1)}%
      </span>
      <div style={{ flex: 1, height: 3, background: '#1E2332', borderRadius: 2, maxWidth: 80 }}>
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
  const TREND: Record<string, { color: string; bg: string }> = {
    STRONG_UPTREND:    { color: '#22C55E', bg: '#052e1688' },
    UPTREND:           { color: '#10B981', bg: '#064e3b55' },
    CONSOLIDATING:     { color: '#F59E0B', bg: '#45260055' },
    DOWNTREND:         { color: '#EF4444', bg: '#45090955' },
    INSUFFICIENT_DATA: { color: '#475569', bg: '#1E233255' },
  }
  const ts = TREND[t.trend_signal] ?? TREND['INSUFFICIENT_DATA']

  return (
    <Card title="TECHNICAL">
      {/* Trend signal */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <span style={{
          fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 4,
          background: ts.bg, color: ts.color, border: `1px solid ${ts.color}44`,
        }}>
          {t.trend_signal.replace(/_/g, ' ')}
        </span>
        {t.vol_20d_avg != null && (
          <span style={{ color: '#475569', fontSize: 10 }}>
            Avg Vol {(t.vol_20d_avg / 1e5).toFixed(1)}L
          </span>
        )}
      </div>

      {/* 52W range bar */}
      {t.high_52w != null && t.low_52w != null && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#475569', marginBottom: 4 }}>
            <span>52W Low &#8377;{t.low_52w.toFixed(0)}</span>
            <span>52W High &#8377;{t.high_52w.toFixed(0)}</span>
          </div>
          <div style={{ height: 5, background: '#1E2332', borderRadius: 3, position: 'relative' }}>
            {(() => {
              const pos = (close - t.low_52w) / (t.high_52w - t.low_52w) * 100
              return (
                <>
                  <div style={{ width: `${pos}%`, height: '100%', background: '#22C55E44', borderRadius: 3 }} />
                  <div style={{
                    position: 'absolute', top: -3, left: `${pos}%`,
                    width: 11, height: 11, borderRadius: '50%',
                    background: pos >= 85 ? '#22C55E' : pos >= 50 ? '#F59E0B' : '#EF4444',
                    transform: 'translateX(-50%)', border: '2px solid #0A0D14',
                  }} />
                </>
              )
            })()}
          </div>
          {t.prox_52w_high != null && (
            <div style={{ fontSize: 9, color: t.prox_52w_high >= -5 ? '#22C55E' : '#64748B', marginTop: 4 }}>
              {t.prox_52w_high >= 0 ? '+' : ''}{t.prox_52w_high.toFixed(1)}% from 52W high
            </div>
          )}
        </div>
      )}

      {/* DMAs */}
      <DMARow label="20 DMA"  value={t.dma_20}  close={close} color="#60A5FA" />
      <DMARow label="50 DMA"  value={t.dma_50}  close={close} color="#A78BFA" />
      <DMARow label="200 DMA" value={t.dma_200} close={close} color="#F59E0B" />

      <div style={{ color: '#334155', fontSize: 9, marginTop: 8 }}>as of {t.as_of_date}</div>
    </Card>
  )
}

// ─── F&O section ──────────────────────────────────────────────────────────────

function FnoSection({ fno }: { fno: FnoData }) {
  const OI: Record<string, { color: string; bg: string; desc: string }> = {
    LONG_BUILDUP:   { color: '#22C55E', bg: '#052e1688', desc: 'OI + price rising — bulls in control' },
    SHORT_BUILDUP:  { color: '#EF4444', bg: '#45090955', desc: 'OI rising + price falling — bears building' },
    LONG_UNWINDING: { color: '#F59E0B', bg: '#45260055', desc: 'OI + price falling — longs exiting' },
    SHORT_COVERING: { color: '#10B981', bg: '#064e3b55', desc: 'OI falling + price rising — shorts covering' },
  }
  const st = OI[fno.oi_signal] ?? { color: '#475569', bg: '#1E233255', desc: '' }
  const fmt = (v: number | null) => v == null ? '--' : `${v >= 0 ? '+' : ''}${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

  return (
    <Card title="F&O">
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 8 }}>
        <div>
          <div style={SL}>SIGNAL</div>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 3, marginTop: 4, display: 'inline-block',
            background: st.bg, color: st.color, border: `1px solid ${st.color}44`,
          }}>
            {fno.oi_signal.replace(/_/g, ' ')}
          </span>
        </div>
        <div>
          <div style={SL}>FUTURES OI</div>
          <div style={{ color: '#E2E8F0', fontSize: 12, fontWeight: 700 }}>
            {fno.futures_oi != null ? (fno.futures_oi / 1e6).toFixed(2) + 'M' : '--'}
          </div>
        </div>
        <div>
          <div style={SL}>1D CHANGE</div>
          <div style={{ color: (fno.oi_1d ?? 0) >= 0 ? '#22C55E' : '#EF4444', fontSize: 12, fontWeight: 700 }}>
            {fmt(fno.oi_1d)}
          </div>
        </div>
        <div>
          <div style={SL}>5D CHANGE</div>
          <div style={{ color: (fno.oi_5d ?? 0) >= 0 ? '#22C55E' : '#EF4444', fontSize: 12, fontWeight: 700 }}>
            {fmt(fno.oi_5d)}
          </div>
        </div>
      </div>
      {st.desc && (
        <div style={{ fontSize: 10, color: st.color, background: st.bg, padding: '5px 8px', borderRadius: 4, border: `1px solid ${st.color}33` }}>
          {st.desc}
        </div>
      )}
    </Card>
  )
}

// ─── Shareholding bar ─────────────────────────────────────────────────────────

function SHPBar({ label, pctVal, color }: { label: string; pctVal: number | null; color: string }) {
  if (pctVal == null) return null
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ color: '#64748B', fontSize: 10 }}>{label}</span>
        <span style={{ color, fontSize: 11, fontWeight: 700 }}>{pctVal.toFixed(2)}%</span>
      </div>
      <div style={{ height: 4, background: '#1E2332', borderRadius: 2 }}>
        <div style={{ width: `${Math.min(100, pctVal)}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
    </div>
  )
}

// ─── Metric row helper ────────────────────────────────────────────────────────

function MetRow({ label, value, color }: { label: string; value: React.ReactNode; color?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
      <span style={{ color: '#64748B', fontSize: 10 }}>{label}</span>
      <span style={{ color: color ?? '#E2E8F0', fontSize: 11, fontWeight: 600 }}>{value}</span>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function StockDetailPage() {
  const { symbol } = useParams<{ symbol: string }>()
  const navigate   = useNavigate()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['stock', symbol],
    queryFn:  () => fetchStockDetail(symbol!),
  })

  if (isLoading) return (
    <div style={{ color: '#64748B', textAlign: 'center', padding: 60, fontSize: 13 }}>
      Loading {symbol}...
    </div>
  )
  if (isError || !data) return (
    <div>
      <button onClick={() => navigate(-1)} style={{
        background: 'none', border: '1px solid #1E2332', color: '#64748B',
        padding: '4px 12px', borderRadius: 4, fontSize: 11, cursor: 'pointer', marginBottom: 16,
      }}>
        &larr; Back
      </button>
      <div style={{ color: '#EF4444', textAlign: 'center', padding: 40, fontSize: 13 }}>
        Symbol {symbol} not found in intelligence data
      </div>
    </div>
  )

  const c = data.components
  const t = data.technical
  const f = data.fno
  const hasFno   = f && f.oi_signal && f.oi_signal !== ''
  const hasShp   = data.shareholding && data.shareholding.promoter_pct != null
  const hasFund  = data.fundamentals && data.fundamentals.valuation_score != null
  const hasHT    = Array.isArray(data.holding_trends) && (data.holding_trends as unknown[]).length > 0
  const hasMgmt  = data.management && (data.management as Record<string, unknown>).management_score != null
  const hasDeals = data.deal_signals && Object.keys(data.deal_signals).length > 0
  const close    = data.close_now ?? t?.close_now ?? 0

  // Trend badge color
  const trendColor = t?.trend_signal === 'STRONG_UPTREND' ? '#22C55E'
    : t?.trend_signal === 'UPTREND' ? '#10B981'
    : t?.trend_signal === 'CONSOLIDATING' ? '#F59E0B'
    : t?.trend_signal ? '#EF4444' : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Header bar ─────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
        {/* Back */}
        <button onClick={() => navigate(-1)} style={{
          background: 'none', border: '1px solid #1E2332', color: '#475569',
          padding: '4px 10px', borderRadius: 4, fontSize: 11, cursor: 'pointer', flexShrink: 0, marginTop: 4,
        }}>
          &larr;
        </button>

        {/* Name + price + badges */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
            <h1 style={{ color: '#E2E8F0', fontSize: 22, fontWeight: 800, fontFamily: 'monospace', margin: 0 }}>
              {data.symbol}
            </h1>
            {close > 0 && (
              <span style={{ color: '#E2E8F0', fontSize: 20, fontWeight: 700 }}>
                &#8377;{close.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </span>
            )}
            {data.price.ret_30d != null && (
              <span style={{
                fontSize: 12, fontWeight: 600,
                color: data.price.ret_30d >= 0 ? '#22C55E' : '#EF4444',
              }}>
                {data.price.ret_30d >= 0 ? '+' : ''}{data.price.ret_30d.toFixed(1)}% 30D
              </span>
            )}
          </div>

          <div style={{ color: '#475569', fontSize: 12, margin: '3px 0 8px' }}>{data.sector}</div>

          {/* Badges row */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            <CapFlowBadge label={data.label} />
            {trendColor && t?.trend_signal && t.trend_signal !== 'INSUFFICIENT_DATA' && (
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 3,
                border: `1px solid ${trendColor}44`, color: trendColor, background: `${trendColor}18`,
              }}>
                {t.trend_signal.replace(/_/g, ' ')}
              </span>
            )}
            {hasFno && (
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 3,
                border: `1px solid ${f!.oi_signal === 'LONG_BUILDUP' ? '#22C55E44' : '#EF444444'}`,
                color: f!.oi_signal === 'LONG_BUILDUP' ? '#22C55E' : '#EF4444',
                background: f!.oi_signal === 'LONG_BUILDUP' ? '#052e1688' : '#45090955',
              }}>
                {f!.oi_signal.replace(/_/g, ' ')}
              </span>
            )}
            {data.sector_rotation_signal && (
              <span style={{ fontSize: 9, color: '#64748B', padding: '2px 6px', border: '1px solid #1E2332', borderRadius: 3 }}>
                {data.sector_rotation_signal.replace(/_/g, ' ')}
              </span>
            )}
            {/* NSE quick link */}
            <a
              href={`https://www.nseindia.com/get-quotes/equity?symbol=${data.symbol}`}
              target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 9, color: '#3B82F6', textDecoration: 'none', border: '1px solid #1E3A5F', padding: '2px 7px', borderRadius: 3, marginLeft: 4 }}
            >
              NSE
            </a>
          </div>
        </div>

        {/* Score gauges */}
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexShrink: 0 }}>
          <ScoreChip label="Bull Run" value={data.bull_run_score} sub={`${data.market_regime}`} />
          {data.ml_scores?.ml_bull_run_score != null && (
            <ScoreChip label="ML Score" value={data.ml_scores.ml_bull_run_score} />
          )}
          {data.ml_scores?.accumulation_score != null && (
            <ScoreChip label="Accum." value={data.ml_scores.accumulation_score} />
          )}
        </div>
      </div>

      {/* ── Two-column body ─────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16, alignItems: 'start' }}>

        {/* ── LEFT COLUMN ────────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Chart */}
          <Card title={`PRICE CHART — ${data.symbol}`}>
            <StockChart symbol={data.symbol} />
          </Card>

          {/* Score components */}
          <Card title="SCORE COMPONENTS">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
              {[
                { label: 'Price',   value: c.price_score,       sub: '30%' },
                { label: 'Sector',  value: c.sector_flow_score, sub: '25%' },
                { label: 'Deal',    value: c.deal_score,        sub: '25%' },
                { label: 'Corp.',   value: c.corporate_score,   sub: '20%' },
              ].map(({ label, value, sub }) => (
                <div key={label} style={{
                  background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 4,
                  padding: '10px 8px', textAlign: 'center',
                }}>
                  <ScoreGauge score={value} size={56} />
                  <div style={{ color: '#475569', fontSize: 9, marginTop: 4 }}>{label} ({sub})</div>
                </div>
              ))}
            </div>
            <div style={{ color: '#334155', fontSize: 9, marginTop: 10 }}>
              Regime: {data.market_regime} (x{data.regime_multiplier.toFixed(2)}) &nbsp;|&nbsp; as of {data.as_of_date}
            </div>
          </Card>

          {/* Price returns */}
          <Card title="PRICE PERFORMANCE">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {[
                { label: '30D', value: data.price.ret_30d },
                { label: '90D', value: data.price.ret_90d },
                { label: '1Y',  value: data.price.ret_365d },
                { label: 'Vol Ratio', value: data.price.vol_ratio, isMult: true },
              ].map(({ label, value, isMult }) => (
                <div key={label} style={{
                  background: '#0A0D14', border: '1px solid #1E2332',
                  borderRadius: 4, padding: '10px 8px', textAlign: 'center',
                }}>
                  <div style={{ color: '#475569', fontSize: 9, marginBottom: 4 }}>{label}</div>
                  <div style={{
                    fontSize: 15, fontWeight: 700,
                    color: isMult
                      ? '#94A3B8'
                      : (value ?? 0) >= 0 ? '#22C55E' : '#EF4444',
                  }}>
                    {value == null ? '--'
                      : isMult ? `${Number(value).toFixed(1)}x`
                      : pct(value)}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Fundamentals */}
          {hasFund && (
            <Card title={`FUNDAMENTALS${data.fundamentals!.as_of_date ? ` (${data.fundamentals!.as_of_date})` : ''}`}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <MetRow label="Revenue TTM"
                    value={data.fundamentals!.revenue_ttm_cr != null
                      ? `₹${Number(data.fundamentals!.revenue_ttm_cr).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr`
                      : '--'} />
                  <MetRow label="Net Profit TTM"
                    value={data.fundamentals!.profit_ttm_cr != null
                      ? `₹${Number(data.fundamentals!.profit_ttm_cr).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr`
                      : '--'} />
                  <MetRow label="YoY Revenue"
                    value={pct(data.fundamentals!.yoy_revenue_pct as number | null)}
                    color={(data.fundamentals!.yoy_revenue_pct ?? 0) >= 0 ? '#22C55E' : '#EF4444'} />
                  <MetRow label="YoY Profit"
                    value={pct(data.fundamentals!.yoy_profit_pct as number | null)}
                    color={(data.fundamentals!.yoy_profit_pct ?? 0) >= 0 ? '#22C55E' : '#EF4444'} />
                </div>
                <div>
                  <MetRow label="P/E Ratio"    value={num(data.fundamentals!.pe_ratio as number | null)} />
                  <MetRow label="ROE"           value={`${num(data.fundamentals!.roe_pct as number | null)}%`} />
                  <MetRow label="Val. Score"    value={num(data.fundamentals!.valuation_score as number | null)} />
                  {data.fundamentals!.valuation_label && (() => {
                    const lbl = String(data.fundamentals!.valuation_label)
                    const [bg, fg] = lbl === 'CHEAP_QUALITY' ? ['#14532D', '#4ADE80']
                      : lbl === 'FAIR_VALUE' ? ['#1E3A5F', '#60A5FA']
                      : lbl === 'MODERATE'   ? ['#422006', '#FB923C']
                      : ['#450A0A', '#F87171']
                    return (
                      <div style={{ background: bg, color: fg, fontSize: 9, fontWeight: 700, padding: '3px 8px', borderRadius: 3, textAlign: 'center', marginTop: 6 }}>
                        {lbl.replace(/_/g, ' ')}
                      </div>
                    )
                  })()}
                </div>
              </div>
            </Card>
          )}

          {/* Deal signals */}
          {hasDeals && (
            <Card title="INSTITUTIONAL DEALS (30D)">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                {Object.entries(data.deal_signals as Record<string, unknown>).map(([k, v]) => (
                  <MetRow key={k} label={k.replace(/_/g, ' ')} value={String(v)} />
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* ── RIGHT COLUMN ───────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Catalyst banner */}
          {data.catalyst?.event_date && (
            <div style={{
              background: '#1A1A08', border: '1px solid #F59E0B44',
              borderRadius: 6, padding: '10px 14px',
              display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap',
            }}>
              <span style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>CATALYST</span>
              <span style={{ color: '#F59E0B', fontWeight: 700, fontSize: 12 }}>{data.catalyst.event_date}</span>
              <span style={{ color: '#94A3B8', fontSize: 11 }}>{data.catalyst.purpose_type}</span>
              {data.catalyst.catalyst_score != null && (
                <span style={{ color: '#64748B', fontSize: 9, marginLeft: 'auto' }}>
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
          {hasFno && <FnoSection fno={f!} />}

          {/* Shareholding */}
          {hasShp && (
            <Card title={`SHAREHOLDING${data.shareholding!.window_label ? ` (${data.shareholding!.window_label})` : ''}`}>
              <SHPBar label="Promoters" pctVal={data.shareholding!.promoter_pct as number | null} color="#A78BFA" />
              <SHPBar label="FII / FPI" pctVal={data.shareholding!.fii_pct      as number | null} color="#22C55E" />
              <SHPBar label="DII"       pctVal={data.shareholding!.dii_pct      as number | null} color="#3B82F6" />
              <SHPBar label="Public"    pctVal={data.shareholding!.public_pct   as number | null} color="#64748B" />
            </Card>
          )}

          {/* Holding Trends */}
          {hasHT && (
            <Card title="HOLDING TRENDS — QoQ">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      {['Quarter', 'Promoter', 'FII', 'DII', 'Signal'].map(h => (
                        <th key={h} style={{
                          padding: '4px 6px', color: '#475569', fontWeight: 600,
                          textAlign: h === 'Quarter' || h === 'Signal' ? 'left' : 'right',
                          borderBottom: '1px solid #1E2332',
                        }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(data.holding_trends as Record<string, unknown>[]).map((q, i, arr) => {
                      const latest = i === arr.length - 1
                      const dc = (v: number | null) => v == null ? '#475569' : v > 0 ? '#22C55E' : v < 0 ? '#EF4444' : '#475569'
                      const fmt = (p: unknown, d: unknown) => {
                        if (p == null) return '--'
                        const pn = Number(p), dn = d != null ? Number(d) : null
                        return (
                          <span>
                            <span style={{ color: '#E2E8F0' }}>{pn.toFixed(1)}%</span>
                            {dn != null && i > 0 && (
                              <span style={{ color: dc(dn), fontSize: 9 }}>
                                {' '}{dn >= 0 ? '+' : ''}{dn.toFixed(1)}
                              </span>
                            )}
                          </span>
                        )
                      }
                      const SIG: Record<string, string> = {
                        STRONG_PROMOTER_FII_BUY: '#22C55E',
                        FII_DII_ACCUMULATION: '#3B82F6',
                        FII_ACCUMULATION: '#60A5FA',
                        DII_ACCUMULATION: '#818CF8',
                        STRONG_PROMOTER_BUY: '#A78BFA',
                        STABLE: '#475569',
                        PROMOTER_SELLING: '#EF4444',
                        FII_DII_DIVERGENCE: '#F59E0B',
                      }
                      const sig = String(q.conviction_signal ?? '')
                      return (
                        <tr key={String(q.period)} style={{
                          borderBottom: '1px solid #1E233215',
                          background: latest ? '#1E233218' : 'transparent',
                        }}>
                          <td style={{ padding: '5px 6px', color: latest ? '#E2E8F0' : '#64748B', fontWeight: latest ? 700 : 400 }}>
                            {String(q.period)}
                            {latest && <span style={{ color: '#22C55E', fontSize: 8, marginLeft: 4 }}>NEW</span>}
                          </td>
                          <td style={{ padding: '5px 6px', textAlign: 'right' }}>{fmt(q.promoter_pct, q.promoter_delta)}</td>
                          <td style={{ padding: '5px 6px', textAlign: 'right' }}>{fmt(q.fii_pct, q.fii_delta)}</td>
                          <td style={{ padding: '5px 6px', textAlign: 'right' }}>{fmt(q.dii_pct, q.dii_delta)}</td>
                          <td style={{ padding: '5px 6px' }}>
                            {sig && i > 0 && (
                              <span style={{
                                fontSize: 8, fontWeight: 700, padding: '1px 4px',
                                borderRadius: 2, color: SIG[sig] ?? '#475569',
                                border: `1px solid ${SIG[sig] ?? '#475569'}55`,
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
            const sc = ms >= 65 ? '#22C55E' : ms >= 45 ? '#F59E0B' : '#EF4444'
            const [lbg, lfg] = lbl === 'POSITIVE' ? ['#14532D', '#4ADE80']
              : lbl === 'NEGATIVE' ? ['#450A0A', '#F87171']
              : ['#1E293B', '#94A3B8']
            return (
              <Card title={`MANAGEMENT${m.as_of_date ? ` (${m.as_of_date})` : ''}`}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: sc, fontFamily: 'monospace' }}>
                    {ms.toFixed(0)}<span style={{ fontSize: 10, color: '#475569' }}>/100</span>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ height: 5, background: '#1E2332', borderRadius: 3, marginBottom: 6 }}>
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
                    { label: 'Holding', value: m.holding_score != null ? `${Number(m.holding_score).toFixed(0)}/100` : '--' },
                    { label: 'Announcements', value: m.announcement_score != null ? `${Number(m.announcement_score).toFixed(0)}/100` : '--' },
                    { label: 'AI Tone', value: m.ai_tone_score != null ? `${Number(m.ai_tone_score).toFixed(0)}/100` : '--' },
                  ].map(({ label, value }) => (
                    <div key={label} style={{
                      background: '#0A0D14', border: '1px solid #1E2332',
                      borderRadius: 4, padding: '6px 8px', textAlign: 'center',
                    }}>
                      <div style={{ color: '#475569', fontSize: 8, marginBottom: 2 }}>{label}</div>
                      <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 600 }}>{value}</div>
                    </div>
                  ))}
                </div>
                {m.holding_signal && (
                  <div style={{ color: '#64748B', fontSize: 9, marginTop: 8 }}>
                    Signal: <span style={{ color: '#94A3B8' }}>{String(m.holding_signal)}</span>
                  </div>
                )}
              </Card>
            )
          })()}

          {/* Sector link */}
          <Link to={`/sectors/${data.sector}`} style={{
            display: 'block', textAlign: 'center', padding: '8px 0',
            color: '#3B82F6', fontSize: 11, textDecoration: 'none',
            border: '1px solid #1E3A5F', borderRadius: 6, background: '#0F172A55',
          }}>
            View {data.sector} sector intelligence &rarr;
          </Link>
        </div>
      </div>
    </div>
  )
}
