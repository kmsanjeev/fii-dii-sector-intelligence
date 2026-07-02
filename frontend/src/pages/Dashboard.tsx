/**
 * Dashboard — enhanced with full intelligence panel coverage
 * Fetches: market context, participant latest, sectors, watchlists, catalysts, deals
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  fetchMarketContext, fetchParticipantLatest, fetchSectors,
  fetchWatchlist, fetchCatalysts, fetchDeals,
} from '../api/client'
import { ScoreGauge }  from '../components/platform/ScoreGauge'
import { FlowCard }    from '../components/platform/FlowCard'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'

// ─── Style helpers ────────────────────────────────────────────────────────────

const LABEL  = { color: '#64748B', fontSize: 9, letterSpacing: 1 } as const
const CARD   = { background: '#141720', border: '1px solid #1E2332', borderRadius: 6 } as const
const DIV    = { width: 1, height: 36, background: '#1E2332', flexShrink: 0 } as const

const SIGNAL_COLOR: Record<string, string> = {
  STRONG_ACCUMULATION: '#22C55E',
  EARLY_ROTATION:      '#10B981',
  PRICE_LED:           '#3B82F6',
  NEUTRAL:             '#64748B',
  DISTRIBUTION:        '#EF4444',
}

function signed(n: number | null | undefined, decimals = 1) {
  if (n == null) return '--'
  return `${n >= 0 ? '+' : ''}${n.toFixed(decimals)}`
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function PulseCell({ label, children, width }: {
  label: string; children: React.ReactNode; width?: number
}) {
  return (
    <div style={{ minWidth: width }}>
      <div style={LABEL}>{label}</div>
      <div style={{ marginTop: 4 }}>{children}</div>
    </div>
  )
}

function MetricChip({ label, value, color, to }: {
  label: string; value: string | number; color?: string; to?: string
}) {
  const inner = (
    <div style={{
      ...CARD, padding: '8px 12px', cursor: to ? 'pointer' : 'default',
      display: 'flex', flexDirection: 'column', gap: 2, flex: 1,
    }}>
      <div style={{ color: '#475569', fontSize: 9, letterSpacing: 1 }}>{label}</div>
      <div style={{ color: color ?? '#E2E8F0', fontSize: 16, fontWeight: 700 }}>{value}</div>
    </div>
  )
  return to ? <Link to={to} style={{ flex: 1, textDecoration: 'none' }}>{inner}</Link> : inner
}

function CashBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
      <span style={{ color: '#64748B', minWidth: 60 }}>{label}</span>
      <span style={{ color, fontWeight: 700, minWidth: 80 }}>
        {value >= 0 ? '+' : ''}{value.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr
      </span>
      <div style={{ flex: 1, height: 3, background: '#1E2332', borderRadius: 2, maxWidth: 70 }}>
        <div style={{ height: '100%', borderRadius: 2, background: color,
          width: `${Math.min(100, Math.abs(value) / 3000 * 100)}%` }} />
      </div>
    </div>
  )
}

function ConvictionBar({ label, pct }: { label: string; pct: number }) {
  const color = pct >= 60 ? '#22C55E' : pct >= 40 ? '#F59E0B' : '#EF4444'
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ color: '#64748B', fontSize: 10 }}>{label}</span>
        <span style={{ color, fontSize: 11, fontWeight: 700 }}>{pct.toFixed(0)}%</span>
      </div>
      <div style={{ height: 4, background: '#1E2332', borderRadius: 2 }}>
        <div style={{ height: '100%', borderRadius: 2, background: color, width: `${pct}%`, transition: 'width 0.5s' }} />
      </div>
    </div>
  )
}

function SectionHeader({ title, link, linkLabel }: { title: string; link?: string; linkLabel?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
      <h2 style={{ color: '#64748B', fontSize: 9, letterSpacing: 2, margin: 0 }}>{title}</h2>
      {link && <Link to={link} style={{ color: '#3B82F6', fontSize: 11 }}>{linkLabel ?? 'View all'}</Link>}
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export function Dashboard() {
  const { data: ctx }        = useQuery({ queryKey: ['market-context'],     queryFn: fetchMarketContext,     refetchInterval: 300000 })
  const { data: part }       = useQuery({ queryKey: ['participant-latest'],  queryFn: fetchParticipantLatest, refetchInterval: 300000 })
  const { data: sectors }    = useQuery({ queryKey: ['sectors'],             queryFn: fetchSectors,           refetchInterval: 300000 })
  const { data: emerging }   = useQuery({ queryKey: ['watchlist','EMRG'],   queryFn: () => fetchWatchlist('EMERGING', 12),          refetchInterval: 300000 })
  const { data: strong }     = useQuery({ queryKey: ['watchlist','STRONG'],  queryFn: () => fetchWatchlist('STRONG_CANDIDATE', 5),  refetchInterval: 300000 })
  const { data: catalysts }  = useQuery({ queryKey: ['catalysts'],           queryFn: fetchCatalysts,         refetchInterval: 600000 })
  const { data: deals }      = useQuery({ queryKey: ['deals-dash'],          queryFn: () => fetchDeals(10, 6), refetchInterval: 600000 })

  const flows   = ctx?.flow_scores
  const cash    = ctx?.cash_flows
  const breadth = ctx?.breadth

  // Sector signal counts
  const allSectors   = sectors?.sectors ?? []
  const earlyRot     = allSectors.filter(s => s.rotation_signal === 'EARLY_ROTATION').length
  const strongAccum  = allSectors.filter(s => s.rotation_signal === 'STRONG_ACCUMULATION').length

  // Conviction counts
  const strongBuyCount = strong?.count ?? 0

  // F&O signal
  const uptrends = (emerging?.stocks ?? []).filter(s => s.trend_signal === 'STRONG_UPTREND' || s.trend_signal === 'UPTREND').length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Row 1: Market Pulse ──────────────────────────────────────────── */}
      {ctx && (
        <div style={{ ...CARD, padding: '12px 20px', display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-start' }}>

          {/* Regime */}
          <PulseCell label="REGIME" width={80}>
            <span style={{
              fontSize: 14, fontWeight: 700,
              color: ctx.regime === 'BULL' ? '#22C55E' : ctx.regime === 'BEAR' ? '#EF4444' : '#F59E0B',
            }}>{ctx.regime}</span>
            <div style={{ color: '#475569', fontSize: 9, marginTop: 2 }}>market</div>
          </PulseCell>

          <div style={DIV} />

          {/* PCR */}
          <PulseCell label="PCR" width={72}>
            <span style={{
              fontSize: 16, fontWeight: 700,
              color: ctx.pcr_signal === 'BULLISH' ? '#22C55E' : ctx.pcr_signal === 'BEARISH' ? '#EF4444' : '#F59E0B',
            }}>{ctx.pcr?.toFixed(2) ?? '--'}</span>
            <div style={{ fontSize: 9, color: '#475569', marginTop: 2 }}>{ctx.pcr_signal}</div>
          </PulseCell>

          <div style={DIV} />

          {/* Smart Money + Market Opportunity */}
          <PulseCell label="SMART MONEY" width={90}>
            <span style={{ fontSize: 16, fontWeight: 700,
              color: (ctx.smart_money_score ?? 0) >= 0 ? '#22C55E' : '#EF4444' }}>
              {signed(ctx.smart_money_score)}
            </span>
            {part && (
              <div style={{ fontSize: 9, color: '#475569', marginTop: 2 }}>
                Opp: {signed(part.Market_Opportunity)}
              </div>
            )}
          </PulseCell>

          <div style={DIV} />

          {/* Conviction bars */}
          {part && (
            <div style={{ minWidth: 120 }}>
              <div style={{ ...LABEL, marginBottom: 6 }}>CONVICTION</div>
              <ConvictionBar label="FII" pct={part.FII_conviction * 100} />
              <div style={{ marginTop: 5 }}>
                <ConvictionBar label="DII" pct={part.DII_conviction * 100} />
              </div>
            </div>
          )}

          <div style={DIV} />

          {/* Divergence */}
          {part && (
            <PulseCell label="DIVERGENCE" width={100}>
              <div style={{ fontSize: 11 }}>
                <div>
                  <span style={{ color: '#64748B', fontSize: 9 }}>FII/DII</span>
                  {' '}
                  <span style={{ fontWeight: 700, color: part.FII_DII_Divergence >= 0 ? '#22C55E' : '#EF4444' }}>
                    {signed(part.FII_DII_Divergence)}
                  </span>
                </div>
                <div style={{ marginTop: 3 }}>
                  <span style={{ color: '#64748B', fontSize: 9 }}>Sm/Ret</span>
                  {' '}
                  <span style={{ fontWeight: 700, color: part.Smart_Retail_Divergence >= 0 ? '#22C55E' : '#EF4444' }}>
                    {signed(part.Smart_Retail_Divergence)}
                  </span>
                </div>
              </div>
            </PulseCell>
          )}

          <div style={DIV} />

          {/* Cash flows */}
          {cash && (
            <div>
              <div style={{ ...LABEL, marginBottom: 6 }}>CASH FLOWS (5D NET)</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <CashBar label="FII/FPI"  value={cash.fpi_5d_cr}      color={cash.fpi_5d_cr >= 0 ? '#22C55E' : '#EF4444'} />
                <CashBar label="MF/DII"   value={cash.mf_5d_cr}       color={cash.mf_5d_cr >= 0 ? '#3B82F6' : '#EF4444'} />
                <CashBar label="Insurance" value={cash.insurance_5d_cr} color={cash.insurance_5d_cr >= 0 ? '#8B5CF6' : '#EF4444'} />
              </div>
            </div>
          )}

          <div style={DIV} />

          {/* Universe Breadth */}
          {breadth && (
            <div>
              <div style={{ ...LABEL, marginBottom: 6 }}>UNIVERSE BREADTH</div>
              <div style={{ display: 'flex', gap: 8 }}>
                {([
                  { label: 'STRONG', count: breadth.strong_candidate, color: '#22C55E' },
                  { label: 'EMRG',   count: breadth.emerging,         color: '#10B981' },
                  { label: 'WATCH',  count: breadth.watchlist,        color: '#F59E0B' },
                  { label: 'AVOID',  count: breadth.avoid,            color: '#EF4444' },
                ] as const).map(({ label, count, color }) => (
                  <div key={label} style={{ textAlign: 'center', minWidth: 42 }}>
                    <div style={{ color, fontSize: 15, fontWeight: 700 }}>{count}</div>
                    <div style={{ color: '#475569', fontSize: 8 }}>{label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginLeft: 'auto', textAlign: 'right', alignSelf: 'center' }}>
            <div style={LABEL}>DATA AS OF</div>
            <div style={{ color: '#475569', fontSize: 11, marginTop: 4 }}>
              {new Date(ctx.data_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: '2-digit' })}
            </div>
          </div>
        </div>
      )}

      {/* ── Row 2: Intelligence Signal Chips ──────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <MetricChip label="STRONG BUY STOCKS"  value={strongBuyCount}  color="#22C55E" to="/watchlist" />
        <MetricChip label="EARLY ROTATION SECTORS" value={earlyRot}   color="#10B981" to="/sectors" />
        <MetricChip label="ACCUMULATION SECTORS"   value={strongAccum} color="#22C55E" to="/sectors" />
        <MetricChip label="UPTREND STOCKS (EMRG)"  value={uptrends}   color="#3B82F6" to="/watchlist" />
        <MetricChip label="UPCOMING CATALYSTS"     value={catalysts?.count ?? '--'} color="#F59E0B" to="/corporate" />
        <MetricChip label="RECENT BLOCK DEALS"     value={deals?.count ?? '--'}     color="#8B5CF6" to="/corporate" />
      </div>

      {/* ── Row 3: Participant Flows ──────────────────────────────────────── */}
      {flows && (
        <section>
          <SectionHeader title="PARTICIPANT FLOWS (F&O)" link="/participant" linkLabel="Full Analysis" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
            <FlowCard participant="FII"    score={flows.FII}    conviction={ctx?.fii_conviction_pct} />
            <FlowCard participant="DII"    score={flows.DII} />
            <FlowCard participant="PRO"    score={flows.PRO} />
            <FlowCard participant="CLIENT" score={flows.CLIENT} />
          </div>
        </section>
      )}

      {/* ── Row 4: 3-column — Sectors | Top Conviction | Events ──────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, alignItems: 'start' }}>

        {/* Col 1: Sector Rotation */}
        <section>
          <SectionHeader title="SECTOR ROTATION" link="/sectors" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {allSectors.slice(0, 10).map(s => {
              const sigColor = SIGNAL_COLOR[s.rotation_signal] ?? '#64748B'
              const isHot = s.rotation_signal === 'EARLY_ROTATION' || s.rotation_signal === 'STRONG_ACCUMULATION'
              return (
                <Link key={s.sector} to={`/sectors/${s.sector}`} style={{ textDecoration: 'none' }}>
                  <div style={{
                    ...CARD, padding: '8px 10px',
                    borderColor: isHot ? `${sigColor}55` : '#1E2332',
                    background: isHot ? `${sigColor}08` : '#141720',
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: '#E2E8F0', fontSize: 11, fontWeight: 600, textOverflow: 'ellipsis',overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {s.sector}
                      </div>
                      <div style={{ fontSize: 8, color: sigColor, fontWeight: 700, marginTop: 1 }}>
                        {s.rotation_signal.replace(/_/g, ' ')}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: s.combined_score >= 0 ? '#22C55E' : '#EF4444' }}>
                        {signed(s.combined_score, 0)}
                      </div>
                      <div style={{ fontSize: 8, color: '#475569' }}>score</div>
                    </div>
                  </div>
                </Link>
              )
            })}
            {allSectors.length > 10 && (
              <Link to="/sectors" style={{ color: '#3B82F6', fontSize: 10, textAlign: 'center', padding: '4px 0' }}>
                +{allSectors.length - 10} more sectors
              </Link>
            )}
          </div>
        </section>

        {/* Col 2: Top Conviction Picks */}
        <section>
          <SectionHeader title="TOP CONVICTION PICKS" link="/watchlist" linkLabel="Full Watchlist" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {(strong?.stocks ?? []).map(stock => (
              <Link key={stock.symbol} to={`/stocks/${stock.symbol}`} style={{ textDecoration: 'none' }}>
                <div style={{ ...CARD, padding: '10px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700 }}>{stock.symbol}</div>
                      <div style={{ color: '#64748B', fontSize: 10, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                        {stock.sector}
                      </div>
                      {stock.close_now != null && (
                        <div style={{ color: '#94A3B8', fontSize: 11, marginTop: 2 }}>
                          &#8377;{stock.close_now.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </div>
                      )}
                    </div>
                    <ScoreGauge score={stock.bull_run_score} size={48} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                    <CapFlowBadge label={stock.label} />
                    {stock.trend_signal && (
                      <span style={{
                        fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 2,
                        background: stock.trend_signal.includes('UP') ? '#052e1688' : '#1a000088',
                        color: stock.trend_signal.includes('UP') ? '#22C55E' : '#EF4444',
                        border: `1px solid ${stock.trend_signal.includes('UP') ? '#22C55E44' : '#EF444444'}`,
                      }}>
                        {stock.trend_signal?.replace(/_/g, ' ')}
                      </span>
                    )}
                    {stock.price?.ret_30d != null && (
                      <span style={{
                        fontSize: 10, marginLeft: 'auto', fontWeight: 600,
                        color: stock.price.ret_30d >= 0 ? '#22C55E' : '#EF4444',
                      }}>
                        {stock.price.ret_30d >= 0 ? '+' : ''}{stock.price.ret_30d.toFixed(1)}% 30D
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
            {(strong?.stocks ?? []).length === 0 && (
              <div style={{ ...CARD, padding: 16, color: '#475569', fontSize: 11, textAlign: 'center' }}>
                No STRONG_CANDIDATE stocks currently
              </div>
            )}
          </div>
        </section>

        {/* Col 3: Market Events */}
        <section>
          <SectionHeader title="UPCOMING CATALYSTS" link="/corporate" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
            {(catalysts?.catalysts ?? []).slice(0, 4).map((c, i) => {
              const cat = c as Record<string, unknown>
              return (
                <div key={i} style={{ ...CARD, padding: '8px 10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 6 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: '#E2E8F0', fontSize: 12, fontWeight: 600 }}>{cat.symbol as string}</div>
                      <div style={{ color: '#64748B', fontSize: 9, marginTop: 2, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                        {String(cat.purpose_type ?? cat.purpose ?? '').replace(/_/g, ' ')}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ color: '#F59E0B', fontSize: 10, fontWeight: 700 }}>
                        {String(cat.event_date ?? '').slice(5)}
                      </div>
                      {cat.catalyst_score != null && (
                        <div style={{ color: '#475569', fontSize: 8 }}>
                          score {Number(cat.catalyst_score).toFixed(0)}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
            {(catalysts?.catalysts ?? []).length === 0 && (
              <div style={{ ...CARD, padding: 12, color: '#475569', fontSize: 11, textAlign: 'center' }}>
                No upcoming catalysts
              </div>
            )}
          </div>

          {/* Recent block deals */}
          <SectionHeader title="RECENT BLOCK DEALS" link="/corporate" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {(deals?.deals ?? []).slice(0, 4).map((d, i) => {
              const deal = d as Record<string, unknown>
              const cr = Number(deal.net_value_cr ?? deal.value_cr ?? 0)
              return (
                <div key={i} style={{ ...CARD, padding: '8px 10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 6 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: '#E2E8F0', fontSize: 12, fontWeight: 600 }}>
                        {String(deal.symbol ?? deal.SYMBOL ?? '')}
                      </div>
                      <div style={{ color: '#64748B', fontSize: 9, marginTop: 2, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                        {String(deal.client_name ?? deal.CLIENT_NAME ?? '').slice(0, 28)}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#8B5CF6' }}>
                        {cr !== 0 ? `${cr >= 0 ? '+' : ''}${cr.toFixed(0)} Cr` : '--'}
                      </div>
                      <div style={{ color: '#475569', fontSize: 8 }}>
                        {String(deal.trade_date ?? deal.TRADE_DATE ?? '').slice(5)}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>

      {/* ── Row 5: Emerging Watchlist ─────────────────────────────────────── */}
      <section>
        <SectionHeader
          title="EMERGING WATCHLIST"
          link="/watchlist"
          linkLabel={`View all (${emerging?.count ?? 0})`}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
          {(emerging?.stocks ?? []).map(stock => (
            <Link
              key={stock.symbol}
              to={`/stocks/${stock.symbol}`}
              style={{ textDecoration: 'none' }}
            >
              <div style={{
                ...CARD, padding: 12,
                transition: 'border-color 0.15s',
              }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = '#3B82F644')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = '#1E2332')}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {stock.symbol}
                    </div>
                    <div style={{ color: '#64748B', fontSize: 10, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {stock.sector}
                    </div>
                    {stock.close_now != null && (
                      <div style={{ color: '#94A3B8', fontSize: 11, marginTop: 3 }}>
                        &#8377;{stock.close_now.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                      </div>
                    )}
                  </div>
                  <ScoreGauge score={stock.bull_run_score} size={44} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 8, flexWrap: 'wrap' }}>
                  <CapFlowBadge label={stock.label} />
                  {(stock.trend_signal === 'STRONG_UPTREND' || stock.trend_signal === 'UPTREND') && (
                    <span style={{
                      fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 2,
                      border: '1px solid #22C55E44', color: '#22C55E', background: '#052e1688',
                    }}>
                      {stock.trend_signal === 'STRONG_UPTREND' ? 'STR BUY' : 'BUY'}
                    </span>
                  )}
                  {stock.oi_signal === 'LONG_BUILDUP' && (
                    <span style={{
                      fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 2,
                      border: '1px solid #3B82F644', color: '#3B82F6', background: '#0f1f3d88',
                    }}>F&amp;O LB</span>
                  )}
                  {stock.price?.ret_30d != null && (
                    <span style={{
                      fontSize: 10, marginLeft: 'auto', fontWeight: 600,
                      color: stock.price.ret_30d >= 0 ? '#22C55E' : '#EF4444',
                    }}>
                      {stock.price.ret_30d >= 0 ? '+' : ''}{stock.price.ret_30d.toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
