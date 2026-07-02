import { useQuery } from '@tanstack/react-query'
import { fetchMarketContext, fetchSectors, fetchWatchlist } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { FlowCard } from '../components/platform/FlowCard'
import { SectorTile } from '../components/platform/SectorTile'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { Link } from 'react-router-dom'

const S = { color: '#64748B', fontSize: 9, letterSpacing: 1 } as const
const V = (c: string) => ({ color: c, fontSize: 20, fontWeight: 700 }) as const

function StatBox({ label, value, color = '#E2E8F0', sub }: {
  label: string; value: string; color?: string; sub?: string
}) {
  return (
    <div style={{ padding: '10px 14px', borderRadius: 6, background: '#141720', border: '1px solid #1E2332', minWidth: 100 }}>
      <div style={S}>{label}</div>
      <div style={{ color, fontSize: 16, fontWeight: 700, marginTop: 4 }}>{value}</div>
      {sub && <div style={{ color: '#475569', fontSize: 10, marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function CashFlowBar({ label, value, color }: { label: string; value: number; color: string }) {
  const sign = value >= 0 ? '+' : ''
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
      <span style={{ color: '#64748B', minWidth: 72 }}>{label}</span>
      <span style={{ color, fontWeight: 700 }}>{sign}{value.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr</span>
      <div style={{ flex: 1, height: 3, background: '#1E2332', borderRadius: 2, maxWidth: 80 }}>
        <div style={{
          height: '100%', borderRadius: 2, background: color,
          width: `${Math.min(100, Math.abs(value) / 3000 * 100)}%`,
        }} />
      </div>
    </div>
  )
}

function PCRGauge({ pcr, signal }: { pcr: number | null; signal: string }) {
  const color = signal === 'BULLISH' ? '#22C55E' : signal === 'BEARISH' ? '#EF4444' : '#F59E0B'
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={S}>PCR</div>
      <div style={{ color, fontSize: 20, fontWeight: 700 }}>{pcr?.toFixed(2) ?? '--'}</div>
      <div style={{ fontSize: 9, color, fontWeight: 600 }}>{signal}</div>
      <div style={{ fontSize: 9, color: '#334155', marginTop: 2 }}>&gt;1.2 bullish | &lt;0.7 bearish</div>
    </div>
  )
}

export function Dashboard() {
  const { data: ctx }       = useQuery({ queryKey: ['market-context'],  queryFn: fetchMarketContext, refetchInterval: 300000 })
  const { data: sectors }   = useQuery({ queryKey: ['sectors'],         queryFn: fetchSectors,       refetchInterval: 300000 })
  const { data: watchlist } = useQuery({ queryKey: ['watchlist','EMERGING'], queryFn: () => fetchWatchlist('EMERGING', 10), refetchInterval: 300000 })

  const topSectors = (sectors?.sectors ?? []).slice(0, 6)
  const topStocks  = (watchlist?.stocks ?? []).slice(0, 8)
  const flows      = ctx?.flow_scores
  const cash       = ctx?.cash_flows
  const breadth    = ctx?.breadth

  return (
    <div className="space-y-6">
      {/* ── Market Pulse strip ─────────────────────────────────────────────── */}
      {ctx && (
        <div style={{
          background: '#0D1117', border: '1px solid #1E2332', borderRadius: 8,
          padding: '14px 20px', display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'center',
        }}>
          {/* Regime */}
          <div>
            <div style={S}>REGIME</div>
            <div style={{
              fontSize: 14, fontWeight: 700, marginTop: 4,
              color: ctx.regime === 'BULL' ? '#22C55E' : ctx.regime === 'BEAR' ? '#EF4444' : '#F59E0B',
            }}>
              {ctx.regime}
            </div>
          </div>

          <div style={{ width: 1, height: 36, background: '#1E2332' }} />

          {/* PCR */}
          <PCRGauge pcr={ctx.pcr} signal={ctx.pcr_signal} />

          <div style={{ width: 1, height: 36, background: '#1E2332' }} />

          {/* Smart Money */}
          <div>
            <div style={S}>SMART MONEY</div>
            <div style={{
              fontSize: 16, fontWeight: 700, marginTop: 4,
              color: (ctx.smart_money_score ?? 0) >= 0 ? '#22C55E' : '#EF4444',
            }}>
              {(ctx.smart_money_score ?? 0) >= 0 ? '+' : ''}{ctx.smart_money_score?.toFixed(1)}
            </div>
          </div>

          <div style={{ width: 1, height: 36, background: '#1E2332' }} />

          {/* Cash flows (5D rolling net) */}
          {cash && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ ...S, marginBottom: 2 }}>CASH FLOWS (5D NET)</div>
              <CashFlowBar label="FII/FPI" value={cash.fpi_5d_cr}       color={cash.fpi_5d_cr >= 0 ? '#22C55E' : '#EF4444'} />
              <CashFlowBar label="MF/DII"  value={cash.mf_5d_cr}        color={cash.mf_5d_cr  >= 0 ? '#3B82F6' : '#EF4444'} />
              <CashFlowBar label="INSUR"   value={cash.insurance_5d_cr}  color={cash.insurance_5d_cr >= 0 ? '#8B5CF6' : '#EF4444'} />
            </div>
          )}

          <div style={{ width: 1, height: 36, background: '#1E2332' }} />

          {/* Market breadth */}
          {breadth && (
            <div>
              <div style={{ ...S, marginBottom: 6 }}>UNIVERSE BREADTH</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {[
                  { label: 'STRONG', count: breadth.strong_candidate, color: '#22C55E' },
                  { label: 'EMRG',  count: breadth.emerging,         color: '#10B981' },
                  { label: 'WATCH', count: breadth.watchlist,        color: '#F59E0B' },
                  { label: 'AVOID', count: breadth.avoid,            color: '#EF4444' },
                ].map(({ label, count, color }) => (
                  <div key={label} style={{ textAlign: 'center', minWidth: 44 }}>
                    <div style={{ color, fontSize: 14, fontWeight: 700 }}>{count}</div>
                    <div style={{ color: '#475569', fontSize: 8 }}>{label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
            <div style={S}>DATA AS OF</div>
            <div style={{ color: '#475569', fontSize: 11, marginTop: 4 }}>{ctx.data_date}</div>
          </div>
        </div>
      )}

      {/* ── Participant Flows ───────────────────────────────────────────────── */}
      {flows && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs tracking-widest" style={{ color: '#64748B' }}>PARTICIPANT FLOWS (F&amp;O)</h2>
            <Link to="/participant" style={{ color: '#3B82F6', fontSize: 11 }}>Details</Link>
          </div>
          <div className="grid grid-cols-4 gap-3">
            <FlowCard participant="FII"    score={flows.FII}    conviction={ctx?.fii_conviction_pct} />
            <FlowCard participant="DII"    score={flows.DII} />
            <FlowCard participant="PRO"    score={flows.PRO} />
            <FlowCard participant="CLIENT" score={flows.CLIENT} />
          </div>
        </section>
      )}

      {/* ── Top Sectors ────────────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs tracking-widest" style={{ color: '#64748B' }}>TOP SECTORS</h2>
          <Link to="/sectors" className="text-xs" style={{ color: '#3B82F6' }}>View all</Link>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {topSectors.map(s => (
            <Link key={s.sector} to={`/sectors/${s.sector}`}>
              <SectorTile sector={s} />
            </Link>
          ))}
        </div>
      </section>

      {/* ── Emerging Watchlist ─────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs tracking-widest" style={{ color: '#64748B' }}>EMERGING WATCHLIST</h2>
          <Link to="/watchlist" className="text-xs" style={{ color: '#3B82F6' }}>View all ({watchlist?.count ?? 0})</Link>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {topStocks.map(stock => (
            <Link
              key={stock.symbol}
              to={`/stocks/${stock.symbol}`}
              className="p-3 rounded border hover:brightness-110 transition-all"
              style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}
            >
              <div className="flex items-start justify-between gap-2">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="font-bold text-sm truncate" style={{ color: '#E2E8F0' }}>{stock.symbol}</div>
                  <div className="text-xs truncate mt-0.5" style={{ color: '#64748B' }}>{stock.sector}</div>
                  {stock.close_now != null && (
                    <div style={{ color: '#94A3B8', fontSize: 11, marginTop: 3 }}>
                      &#8377;{stock.close_now.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </div>
                  )}
                </div>
                <ScoreGauge score={stock.bull_run_score} size={44} />
              </div>
              <div className="mt-2 flex items-center justify-between">
                <CapFlowBadge label={stock.label} />
                {stock.price?.ret_30d != null && (
                  <span style={{ fontSize: 10, color: stock.price.ret_30d >= 0 ? '#22C55E' : '#EF4444' }}>
                    {stock.price.ret_30d >= 0 ? '+' : ''}{stock.price.ret_30d.toFixed(1)}%
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
