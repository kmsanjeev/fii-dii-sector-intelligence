import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API = ''

// ── Types ─────────────────────────────────────────────────────────────────────

type Position = {
  symbol:              string
  qty:                 number
  avg_cost:            number | null
  invested:            number | null
  ltp:                 number | null
  current_value:       number | null
  unrealized_pnl:      number | null
  unrealized_pnl_pct:  number | null
  sector:              string | null
  bull_run_label:      string | null
  bull_run_score:      number | null
  ml_bull_run_score:   number | null
  ml_label:            string | null
  ann_score_30d:       number | null
  corp_confidence:     number | null
  rotation_signal:     string | null
  key_signal:          string | null
  first_bought:        string | null
}

type SectorConc = { sector: string; value: number; pct: number }

type Analytics = {
  total_invested:       number
  current_value:        number
  unrealized_pnl:       number
  unrealized_pnl_pct:   number
  num_positions:        number
  avg_bull_run_score:   number
  sector_concentration: SectorConc[]
  label_distribution:   Record<string, number>
}

type Portfolio = { analytics: Analytics; positions: Position[] }

type RiskSnapshot = {
  run_date:            string
  portfolio_value:     number
  n_positions:         number
  n_excluded:          number
  common_days:         number
  var_hist_95_1d:      number
  var_hist_99_1d:      number
  var_hist_95_10d:     number
  var_hist_99_10d:     number
  var_param_95_1d:     number
  var_param_99_1d:     number
  es_hist_975_1d:      number
  es_hist_99_1d:       number
  vol_annualized_pct:  number
  beta_vs_nifty50_ew:  number | null
  max_drawdown_pct:    number
}

type RiskComponent = {
  symbol:                string
  sector:                string
  weight_pct:            number | null
  standalone_vol_pct:    number | null
  component_var_95_1d:   number | null
  risk_contribution_pct: number | null
  status:                string
}

type RiskData = {
  snapshot:   RiskSnapshot
  components: RiskComponent[]
  history:    { run_date: string; var_hist_95_1d: number; es_hist_975_1d: number }[]
}

type StressScenario = {
  scenario:           string
  scenario_type:      'HISTORICAL' | 'HYPOTHETICAL'
  label:              string
  window_start:       string
  window_end:         string
  portfolio_value:    number
  pnl:                number
  pnl_pct:            number
  n_symbol_basis:     number
  n_sector_basis:     number
  n_market_basis:     number
  worst_position:     string
  worst_position_pct: number
}

type FactorExposure = {
  factor:                    string
  factor_type:               'SECTOR' | 'STYLE'
  exposure:                  number
  factor_vol_annualized_pct: number
  var_contribution_pct:      number
}

type FactorData = {
  summary: {
    run_date:                 string
    universe_size:            number
    mean_daily_r2:            number
    n_positions_modeled:      number
    total_vol_annualized_pct: number | null
    systematic_vol_pct:       number | null
    idiosyncratic_vol_pct:    number | null
    systematic_share_pct:     number | null
  }
  exposures: FactorExposure[]
}

type McResult = {
  run_date:        string
  horizon_days:    number
  n_paths:         number
  portfolio_value: number
  mc_var_95:       number
  mc_var_99:       number
  mc_es_975:       number
  mc_es_99:        number
  pnl_std:         number
  pnl_p01:         number
  pnl_p99:         number
}

type McBin = { horizon_days: number; bin_left: number; bin_right: number; count: number }

type McData = { results: McResult[]; distribution: McBin[] }

// ── API helpers ───────────────────────────────────────────────────────────────

async function fetchPortfolio(): Promise<Portfolio> {
  const r = await fetch(`${API}/api/portfolio`)
  if (!r.ok) throw new Error('Failed to load portfolio')
  return r.json()
}

async function postTransaction(action: 'buy' | 'sell', body: object): Promise<void> {
  const r = await fetch(`${API}/api/portfolio/${action}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  })
  if (!r.ok) {
    const e = await r.json()
    throw new Error(e.detail || 'Transaction failed')
  }
}

async function deletePosition(symbol: string): Promise<void> {
  const r = await fetch(`${API}/api/portfolio/positions/${symbol}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('Delete failed')
}

// ── Small reusable UI pieces ──────────────────────────────────────────────────

const LABEL_COLORS: Record<string, string> = {
  BULL_RUN:     '#22C55E',
  EMERGING:     '#10B981',
  WATCHLIST:    '#F59E0B',
  NEUTRAL:      '#64748B',
  ACCUMULATION: '#9575CD',
  MARKDOWN:     '#EF4444',
}

function LabelBadge({ label }: { label: string | null }) {
  if (!label) return <span style={{ color: '#334155' }}>--</span>
  const c = LABEL_COLORS[label] ?? '#64748B'
  return (
    <span style={{
      background: c + '22', color: c,
      border: `1px solid ${c}`, borderRadius: 3,
      padding: '1px 7px', fontSize: 9, fontWeight: 700, whiteSpace: 'nowrap',
    }}>
      {label.replace('_', ' ')}
    </span>
  )
}

function PnlCell({ val, pct }: { val: number | null; pct: number | null }) {
  if (val == null) return <span style={{ color: '#334155' }}>--</span>
  const c    = val >= 0 ? '#22C55E' : '#EF4444'
  const sign = val >= 0 ? '+' : ''
  return (
    <span style={{ color: c }}>
      {sign}{Math.abs(val).toFixed(0)}
      <span style={{ fontSize: 9, marginLeft: 4, color: c + 'BB' }}>
        ({sign}{(pct ?? 0).toFixed(1)}%)
      </span>
    </span>
  )
}

function SummaryCard({ label, value, color = '#E2E8F0', sub }: {
  label: string; value: string; color?: string; sub?: string
}) {
  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: '14px 18px', flex: 1, minWidth: 140,
    }}>
      <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 2, marginBottom: 6 }}>{label}</div>
      <div style={{ color, fontSize: 20, fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ color: '#64748B', fontSize: 10, marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function signalColor(signal: string | null): string {
  if (!signal) return '#64748B'
  if (signal === 'STRONG BUY SIGNAL' || signal === 'MOMENTUM BUILDING') return '#22C55E'
  if (signal === 'ACCUMULATION')       return '#10B981'
  if (signal === 'SECTOR ROTATING IN') return '#3B82F6'
  if (signal === 'REVIEW POSITION' || signal === 'CONSIDER STOP LOSS')  return '#EF4444'
  if (signal === 'WATCHLIST')          return '#F59E0B'
  return '#94A3B8'
}

// ── Input style ───────────────────────────────────────────────────────────────

const inp: React.CSSProperties = {
  background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 4,
  color: '#E2E8F0', padding: '5px 10px', fontSize: 11, outline: 'none',
}
const th: React.CSSProperties = { padding: '6px 8px', textAlign: 'left', fontWeight: 600, whiteSpace: 'nowrap' }
const td: React.CSSProperties = { padding: '6px 8px' }
const ghostBtn: React.CSSProperties = {
  padding: '2px 8px', borderRadius: 3, border: '1px solid #334155',
  background: 'transparent', color: '#64748B', cursor: 'pointer', fontSize: 10,
}
const dangerBtn: React.CSSProperties = {
  padding: '2px 8px', borderRadius: 3, border: '1px solid #EF4444',
  background: '#EF444422', color: '#EF4444', cursor: 'pointer', fontSize: 10, marginRight: 4,
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function PortfolioPage() {
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery<Portfolio>({
    queryKey:      ['portfolio'],
    queryFn:       fetchPortfolio,
    staleTime:     60_000,
    refetchOnWindowFocus: false,
  })

  // Form state
  const [txnAction, setTxnAction] = useState<'BUY' | 'SELL'>('BUY')
  const [symbol,    setSymbol]    = useState('')
  const [qty,       setQty]       = useState('')
  const [price,     setPrice]     = useState('')
  const [txnDate,   setTxnDate]   = useState('')
  const [formMsg,   setFormMsg]   = useState('')
  const [formErr,   setFormErr]   = useState('')

  // Delete confirm
  const [delSym, setDelSym] = useState<string | null>(null)

  // Show transactions panel
  const [showTxns, setShowTxns] = useState(false)

  const mutation = useMutation({
    mutationFn: () => postTransaction(txnAction.toLowerCase() as 'buy' | 'sell', {
      symbol,
      qty:   parseFloat(qty),
      price: parseFloat(price),
      date:  txnDate || undefined,
    }),
    onSuccess: () => {
      setFormMsg(`${txnAction} ${symbol.toUpperCase()} recorded.`)
      setFormErr('')
      setSymbol(''); setQty(''); setPrice(''); setTxnDate('')
      qc.invalidateQueries({ queryKey: ['portfolio'] })
    },
    onError: (e: Error) => { setFormErr(e.message); setFormMsg('') },
  })

  const delMutation = useMutation({
    mutationFn: deletePosition,
    onSuccess:  () => { setDelSym(null); qc.invalidateQueries({ queryKey: ['portfolio'] }) },
  })

  const a   = data?.analytics
  const pos = data?.positions ?? []
  const pnlPositive = (a?.unrealized_pnl ?? 0) >= 0
  const pnlColor    = pnlPositive ? '#22C55E' : '#EF4444'

  const formReady = symbol.trim() && parseFloat(qty) > 0 && parseFloat(price) > 0

  return (
    <div style={{ maxWidth: 1300 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
          PORTFOLIO
        </h1>
        <span style={{ color: '#475569', fontSize: 10 }}>
          Intelligence overlay updates on every transaction and after each daily pipeline run
        </span>
      </div>

      {/* Summary cards */}
      {a && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          <SummaryCard
            label="TOTAL INVESTED"
            value={`Rs ${(a.total_invested / 1000).toFixed(1)}K`}
            sub={`${a.num_positions} position${a.num_positions !== 1 ? 's' : ''}`}
          />
          <SummaryCard
            label="CURRENT VALUE"
            value={`Rs ${(a.current_value / 1000).toFixed(1)}K`}
          />
          <SummaryCard
            label="UNREALIZED P&L"
            value={`${pnlPositive ? '+' : ''}Rs ${(Math.abs(a.unrealized_pnl) / 1000).toFixed(1)}K`}
            color={pnlColor}
            sub={`${pnlPositive ? '+' : ''}${a.unrealized_pnl_pct.toFixed(2)}%`}
          />
          <SummaryCard
            label="AVG BULL SCORE"
            value={a.avg_bull_run_score.toFixed(1)}
            color={
              a.avg_bull_run_score >= 60 ? '#22C55E'
              : a.avg_bull_run_score >= 35 ? '#F59E0B'
              : '#EF4444'
            }
            sub={
              Object.entries(a.label_distribution)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 2)
                .map(([l, n]) => `${n} ${l.replace('_', ' ')}`)
                .join(' · ')
              || 'no labels'
            }
          />
        </div>
      )}

      {/* Add transaction */}
      <div style={{
        background: '#141720', border: '1px solid #1E2332',
        borderRadius: 6, padding: 16, marginBottom: 20,
      }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 12 }}>
          ADD TRANSACTION
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>

          {(['BUY', 'SELL'] as const).map(act => (
            <button key={act} onClick={() => setTxnAction(act)} style={{
              padding: '5px 16px', borderRadius: 4, fontWeight: 700, fontSize: 11, cursor: 'pointer',
              border:      `1px solid ${act === 'BUY' ? '#22C55E' : '#EF4444'}`,
              background:  txnAction === act ? (act === 'BUY' ? '#22C55E22' : '#EF444422') : 'transparent',
              color:       act === 'BUY' ? '#22C55E' : '#EF4444',
            }}>{act}</button>
          ))}

          <input
            placeholder="SYMBOL"
            value={symbol}
            onChange={e => setSymbol(e.target.value.toUpperCase())}
            style={{ ...inp, width: 110 }}
          />
          <input
            placeholder="Qty"
            type="number"
            min="0"
            step="1"
            value={qty}
            onChange={e => setQty(e.target.value)}
            style={{ ...inp, width: 80 }}
          />
          <input
            placeholder="Price (Rs)"
            type="number"
            min="0"
            step="0.01"
            value={price}
            onChange={e => setPrice(e.target.value)}
            style={{ ...inp, width: 110 }}
          />
          <input
            type="date"
            value={txnDate}
            onChange={e => setTxnDate(e.target.value)}
            style={{ ...inp, width: 140, colorScheme: 'dark' }}
          />

          <button
            onClick={() => mutation.mutate()}
            disabled={!formReady || mutation.isPending}
            style={{
              padding: '5px 18px', borderRadius: 4, fontWeight: 700, fontSize: 11,
              border: '1px solid #22C55E', background: 'transparent',
              color: formReady && !mutation.isPending ? '#22C55E' : '#334155',
              cursor: formReady && !mutation.isPending ? 'pointer' : 'not-allowed',
            }}
          >
            {mutation.isPending ? 'Saving...' : 'Record'}
          </button>

          {formMsg && <span style={{ color: '#22C55E', fontSize: 10 }}>{formMsg}</span>}
          {formErr && <span style={{ color: '#EF4444', fontSize: 10 }}>{formErr}</span>}
        </div>
      </div>

      {isLoading && <div style={{ color: '#64748B', padding: 40, textAlign: 'center' }}>Loading portfolio...</div>}
      {error     && <div style={{ color: '#EF4444', padding: 20 }}>Error loading portfolio.</div>}

      {/* Holdings table */}
      {pos.length > 0 && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332',
          borderRadius: 6, padding: 16, marginBottom: 20,
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12,
          }}>
            <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>
              HOLDINGS — {pos.length} POSITION{pos.length !== 1 ? 'S' : ''}
            </div>
            <button
              onClick={() => setShowTxns(v => !v)}
              style={ghostBtn}
            >
              {showTxns ? 'Hide Transactions' : 'Show Transactions'}
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse', minWidth: 960 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1E2332', color: '#64748B', fontSize: 10 }}>
                  <th style={th}>Symbol</th>
                  <th style={th}>Qty</th>
                  <th style={{ ...th, textAlign: 'right' }}>Avg Cost</th>
                  <th style={{ ...th, textAlign: 'right' }}>LTP</th>
                  <th style={{ ...th, textAlign: 'right' }}>Invested</th>
                  <th style={{ ...th, textAlign: 'right' }}>Value</th>
                  <th style={{ ...th, textAlign: 'right' }}>P&L</th>
                  <th style={{ ...th, textAlign: 'center' }}>Label</th>
                  <th style={{ ...th, textAlign: 'right' }}>Score</th>
                  <th style={{ ...th, textAlign: 'right' }}>ML</th>
                  <th style={{ ...th, textAlign: 'right' }}>Ann 30d</th>
                  <th style={th}>Sector</th>
                  <th style={th}>Signal</th>
                  <th style={th}></th>
                </tr>
              </thead>
              <tbody>
                {pos
                  .slice()
                  .sort((a, b) => (b.invested ?? 0) - (a.invested ?? 0))
                  .map(p => (
                  <tr key={p.symbol} style={{ borderBottom: '1px solid #1E233220' }}>

                    <td style={{ ...td, color: '#E2E8F0', fontWeight: 700 }}>
                      <a
                        href={`/stocks/${p.symbol}`}
                        style={{ color: '#E2E8F0', textDecoration: 'none' }}
                        onMouseOver={e => (e.currentTarget.style.color = '#22C55E')}
                        onMouseOut={e  => (e.currentTarget.style.color = '#E2E8F0')}
                      >
                        {p.symbol}
                      </a>
                    </td>

                    <td style={{ ...td, color: '#94A3B8' }}>{p.qty}</td>
                    <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                      {p.avg_cost?.toFixed(2) ?? '--'}
                    </td>
                    <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>
                      {p.ltp?.toFixed(2) ?? <span style={{ color: '#334155' }}>N/A</span>}
                    </td>
                    <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                      {p.invested?.toFixed(0) ?? '--'}
                    </td>
                    <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>
                      {p.current_value?.toFixed(0) ?? '--'}
                    </td>
                    <td style={{ ...td, textAlign: 'right' }}>
                      <PnlCell val={p.unrealized_pnl} pct={p.unrealized_pnl_pct} />
                    </td>
                    <td style={{ ...td, textAlign: 'center' }}>
                      <LabelBadge label={p.bull_run_label} />
                    </td>
                    <td style={{ ...td, textAlign: 'right' }}>
                      {p.bull_run_score != null
                        ? <span style={{
                            color: p.bull_run_score >= 60 ? '#22C55E'
                                 : p.bull_run_score >= 35 ? '#F59E0B' : '#EF4444',
                          }}>{p.bull_run_score.toFixed(0)}</span>
                        : <span style={{ color: '#334155' }}>--</span>
                      }
                    </td>
                    <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                      {p.ml_bull_run_score?.toFixed(0) ?? '--'}
                    </td>
                    <td style={{ ...td, textAlign: 'right' }}>
                      <span style={{ color: (p.ann_score_30d ?? 0) > 100 ? '#F59E0B' : '#64748B' }}>
                        {p.ann_score_30d?.toFixed(0) ?? '--'}
                      </span>
                    </td>
                    <td style={{ ...td, color: '#64748B', fontSize: 10 }}>
                      {p.sector ?? '--'}
                    </td>
                    <td style={td}>
                      <span style={{ fontSize: 9, fontWeight: 700, color: signalColor(p.key_signal) }}>
                        {p.key_signal ?? '--'}
                      </span>
                    </td>
                    <td style={td}>
                      {delSym === p.symbol ? (
                        <span>
                          <button
                            onClick={() => delMutation.mutate(p.symbol)}
                            style={dangerBtn}
                          >
                            {delMutation.isPending ? '...' : 'Confirm'}
                          </button>
                          <button onClick={() => setDelSym(null)} style={ghostBtn}>Cancel</button>
                        </span>
                      ) : (
                        <button onClick={() => setDelSym(p.symbol)} style={ghostBtn}>Remove</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transaction history */}
      {showTxns && <TransactionHistory />}

      {/* Portfolio risk — Phase R1 */}
      {pos.length >= 2 && <RiskPanel />}

      {/* Stress scenarios + factor decomposition — Phase R2 */}
      {pos.length >= 1 && <StressPanel />}
      {pos.length >= 1 && <FactorPanel />}

      {/* Monte Carlo simulation — Phase R3 */}
      {pos.length >= 2 && <MonteCarloPanel />}

      {/* Empty state */}
      {!isLoading && pos.length === 0 && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332',
          borderRadius: 6, padding: 48, textAlign: 'center', color: '#64748B', fontSize: 12,
        }}>
          No positions yet. Record your first transaction above.
        </div>
      )}

      {/* Sector concentration */}
      {(a?.sector_concentration ?? []).length > 0 && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332',
          borderRadius: 6, padding: 16,
        }}>
          <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 12 }}>
            SECTOR CONCENTRATION
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {a!.sector_concentration.map(s => (
              <div key={s.sector}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: 10, color: '#94A3B8', marginBottom: 3,
                }}>
                  <span>{s.sector || 'Unknown'}</span>
                  <span style={{ color: '#64748B' }}>Rs {s.value.toFixed(0)} — {s.pct}%</span>
                </div>
                <div style={{ height: 5, background: '#1E2332', borderRadius: 3 }}>
                  <div style={{
                    width: `${s.pct}%`, height: 5, borderRadius: 3,
                    background: '#3B82F6', transition: 'width 0.5s',
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Transaction history sub-panel ─────────────────────────────────────────────

type TxnRow = { date: string; symbol: string; action: string; qty: number; price: number; notes: string }

function TransactionHistory() {
  const { data, isLoading } = useQuery<{ transactions: TxnRow[]; count: number }>({
    queryKey: ['portfolio_transactions'],
    queryFn: async () => {
      const r = await fetch(`${API}/api/portfolio/transactions`)
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    staleTime: 30_000,
  })

  if (isLoading) return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16, marginBottom: 20,
      color: '#64748B', fontSize: 11,
    }}>Loading transactions...</div>
  )

  const txns = (data?.transactions ?? []).slice().reverse()

  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 20,
    }}>
      <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 12 }}>
        TRANSACTION HISTORY — {data?.count ?? 0} ENTRIES
      </div>
      <div style={{ overflowY: 'auto', maxHeight: 280 }}>
        <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #1E2332', color: '#64748B', fontSize: 10 }}>
              <th style={th}>Date</th>
              <th style={th}>Symbol</th>
              <th style={th}>Action</th>
              <th style={{ ...th, textAlign: 'right' }}>Qty</th>
              <th style={{ ...th, textAlign: 'right' }}>Price</th>
              <th style={{ ...th, textAlign: 'right' }}>Value</th>
              <th style={th}>Notes</th>
            </tr>
          </thead>
          <tbody>
            {txns.map((t, i) => {
              const isBuy = t.action === 'BUY'
              const c = isBuy ? '#22C55E' : '#EF4444'
              return (
                <tr key={i} style={{ borderBottom: '1px solid #1E233220' }}>
                  <td style={{ ...td, color: '#64748B' }}>{t.date}</td>
                  <td style={{ ...td, color: '#E2E8F0', fontWeight: 600 }}>{t.symbol}</td>
                  <td style={td}>
                    <span style={{
                      color: c, border: `1px solid ${c}`, background: c + '22',
                      borderRadius: 3, padding: '0 6px', fontSize: 9, fontWeight: 700,
                    }}>
                      {t.action}
                    </span>
                  </td>
                  <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>{t.qty}</td>
                  <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>
                    {Number(t.price).toFixed(2)}
                  </td>
                  <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                    {(t.qty * t.price).toFixed(0)}
                  </td>
                  <td style={{ ...td, color: '#475569', fontSize: 10 }}>{t.notes || ''}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Portfolio Risk panel (Phase R1: VaR / ES / component risk) ────────────────

function riskFmt(v: number | null | undefined): string {
  if (v == null) return '--'
  return v >= 1000 ? `Rs ${(v / 1000).toFixed(1)}K` : `Rs ${v.toFixed(0)}`
}

function RiskPanel() {
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery<RiskData>({
    queryKey: ['portfolio_risk'],
    queryFn: async () => {
      const r = await fetch(`${API}/api/risk/portfolio`)
      if (r.status === 404 || r.status === 422) throw new Error('NO_DATA')
      if (!r.ok) throw new Error('Failed to load risk data')
      return r.json()
    },
    staleTime: 5 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
  })

  const refresh = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${API}/api/risk/refresh`, { method: 'POST' })
      if (!r.ok) {
        const e = await r.json()
        throw new Error(e.detail || 'Risk refresh failed')
      }
      return r.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portfolio_risk'] }),
  })

  const s     = data?.snapshot
  const comps = (data?.components ?? []).filter(c => c.status === 'OK')
  const excl  = (data?.components ?? []).filter(c => c.status !== 'OK')
  const noData = (error as Error | null)?.message === 'NO_DATA'

  // % of portfolio value for color-coding VaR severity
  const varPct = s ? (s.var_hist_95_1d / s.portfolio_value) * 100 : 0
  const varColor = varPct > 3 ? '#EF4444' : varPct > 1.8 ? '#F59E0B' : '#22C55E'

  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>
          PORTFOLIO RISK — VaR / EXPECTED SHORTFALL
          {s && <span style={{ color: '#475569', fontWeight: 400, marginLeft: 10, letterSpacing: 0 }}>
            as of {s.run_date} · {s.common_days} trading days · 95%/99% confidence
          </span>}
        </div>
        <button
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
          style={{ ...ghostBtn, borderColor: '#3B82F6', color: refresh.isPending ? '#334155' : '#3B82F6' }}
        >
          {refresh.isPending ? 'Computing...' : 'Refresh Risk'}
        </button>
      </div>

      {isLoading && <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>Loading risk data...</div>}

      {noData && !isLoading && (
        <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>
          No risk snapshot yet. Click <span style={{ color: '#3B82F6' }}>Refresh Risk</span> to compute
          VaR from current positions (needs 2+ positions with 60+ trading days of history).
        </div>
      )}
      {refresh.isError && (
        <div style={{ color: '#EF4444', fontSize: 10, padding: '0 0 8px' }}>{(refresh.error as Error).message}</div>
      )}

      {s && (
        <>
          {/* Headline risk cards */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <SummaryCard
              label="VaR 95% · 1 DAY"
              value={riskFmt(s.var_hist_95_1d)}
              color={varColor}
              sub={`${varPct.toFixed(2)}% of portfolio · param ${riskFmt(s.var_param_95_1d)}`}
            />
            <SummaryCard
              label="VaR 99% · 1 DAY"
              value={riskFmt(s.var_hist_99_1d)}
              color={varColor}
              sub={`10-day: ${riskFmt(s.var_hist_99_10d)} (sqrt-scaled)`}
            />
            <SummaryCard
              label="EXP. SHORTFALL 97.5%"
              value={riskFmt(s.es_hist_975_1d)}
              color="#F59E0B"
              sub={`ES 99%: ${riskFmt(s.es_hist_99_1d)} · avg loss beyond VaR`}
            />
            <SummaryCard
              label="ANNUALIZED VOL"
              value={`${s.vol_annualized_pct.toFixed(1)}%`}
              sub={s.beta_vs_nifty50_ew != null ? `beta ${s.beta_vs_nifty50_ew.toFixed(2)} vs NIFTY50 (EW)` : 'beta unavailable'}
            />
            <SummaryCard
              label="MAX DRAWDOWN (2Y)"
              value={`${s.max_drawdown_pct.toFixed(1)}%`}
              color={s.max_drawdown_pct < -25 ? '#EF4444' : s.max_drawdown_pct < -15 ? '#F59E0B' : '#E2E8F0'}
              sub="synthetic curve of current holdings"
            />
          </div>

          {/* Component risk: weight vs risk contribution */}
          {comps.length > 0 && (
            <div>
              <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1, marginBottom: 8 }}>
                RISK CONTRIBUTION BY POSITION (component VaR, Euler decomposition)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                {comps
                  .slice()
                  .sort((a, b) => (b.risk_contribution_pct ?? 0) - (a.risk_contribution_pct ?? 0))
                  .map(c => {
                    const rc = c.risk_contribution_pct ?? 0
                    const wt = c.weight_pct ?? 0
                    const hot = rc > wt * 1.35   // contributes disproportionate risk
                    return (
                      <div key={c.symbol}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 3 }}>
                          <span style={{ color: '#E2E8F0', fontWeight: 600 }}>
                            {c.symbol}
                            <span style={{ color: '#475569', fontWeight: 400, marginLeft: 8 }}>{c.sector}</span>
                            {hot && <span style={{ color: '#F59E0B', marginLeft: 8 }}>risk-heavy</span>}
                          </span>
                          <span style={{ color: '#64748B' }}>
                            {riskFmt(c.component_var_95_1d)} · risk {rc.toFixed(1)}% vs weight {wt.toFixed(1)}%
                            · vol {c.standalone_vol_pct?.toFixed(0)}%
                          </span>
                        </div>
                        <div style={{ position: 'relative', height: 6, background: '#1E2332', borderRadius: 3 }}>
                          <div style={{
                            width: `${Math.min(rc, 100)}%`, height: 6, borderRadius: 3,
                            background: hot ? '#F59E0B' : '#3B82F6', transition: 'width 0.5s',
                          }} />
                          {/* weight marker for visual weight-vs-risk comparison */}
                          <div style={{
                            position: 'absolute', top: -2, left: `${Math.min(wt, 100)}%`,
                            width: 2, height: 10, background: '#94A3B8',
                          }} />
                        </div>
                      </div>
                    )
                  })}
              </div>
              <div style={{ color: '#475569', fontSize: 9, marginTop: 6 }}>
                Bar = share of portfolio risk · grey tick = capital weight. Bar past the tick = position adds more risk than capital.
              </div>
            </div>
          )}

          {/* Excluded symbols warning */}
          {excl.length > 0 && (
            <div style={{
              marginTop: 12, padding: '8px 12px', borderRadius: 4,
              border: '1px solid #F59E0B44', background: '#F59E0B11',
              color: '#F59E0B', fontSize: 10,
            }}>
              Excluded from risk math ({excl.length}): {excl.map(e =>
                `${e.symbol} (${e.status.replace('EXCLUDED_', '').replace('_', ' ').toLowerCase()})`
              ).join(', ')} — VaR understates true portfolio risk.
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ── Stress scenario panel (Phase R2) ──────────────────────────────────────────

function StressPanel() {
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery<{ scenarios: StressScenario[] }>({
    queryKey: ['portfolio_stress'],
    queryFn: async () => {
      const r = await fetch(`${API}/api/risk/stress`)
      if (r.status === 404 || r.status === 422) throw new Error('NO_DATA')
      if (!r.ok) throw new Error('Failed to load stress data')
      return r.json()
    },
    staleTime: 5 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
  })

  const refresh = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${API}/api/risk/stress/refresh`, { method: 'POST' })
      if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Stress refresh failed') }
      return r.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portfolio_stress'] }),
  })

  const noData    = (error as Error | null)?.message === 'NO_DATA'
  const scenarios = data?.scenarios ?? []
  const hist = scenarios.filter(s => s.scenario_type === 'HISTORICAL')
  const hypo = scenarios.filter(s => s.scenario_type === 'HYPOTHETICAL')

  const pnlColor = (pct: number) =>
    pct < -25 ? '#EF4444' : pct < -12 ? '#F59E0B' : pct < 0 ? '#FBBF24' : '#22C55E'

  const ScenarioCard = ({ s }: { s: StressScenario }) => (
    <div style={{
      background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 6,
      padding: '12px 14px', flex: '1 1 200px', minWidth: 190, maxWidth: 260,
    }}>
      <div style={{ color: '#94A3B8', fontSize: 10, fontWeight: 700, marginBottom: 2 }}>
        {s.scenario.replace(/_/g, ' ')}
      </div>
      <div style={{ color: '#475569', fontSize: 9, marginBottom: 8, minHeight: 22 }}>{s.label}</div>
      <div style={{ color: pnlColor(s.pnl_pct), fontSize: 22, fontWeight: 700 }}>
        {s.pnl_pct.toFixed(1)}%
      </div>
      <div style={{ color: '#64748B', fontSize: 9, marginTop: 4 }}>
        {riskFmt(Math.abs(s.pnl))} {s.pnl < 0 ? 'loss' : 'gain'}
        {s.worst_position && <> · worst: {s.worst_position} {s.worst_position_pct.toFixed(0)}%</>}
      </div>
      {(s.n_sector_basis > 0 || s.n_market_basis > 0) && s.scenario_type === 'HISTORICAL' && (
        <div style={{ color: '#F59E0B', fontSize: 9, marginTop: 3 }}>
          {s.n_sector_basis + s.n_market_basis} position(s) proxied (no history in window)
        </div>
      )}
    </div>
  )

  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>
          STRESS TESTING — CRISIS REPLAY &amp; SHOCK SCENARIOS
        </div>
        <button
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
          style={{ ...ghostBtn, borderColor: '#3B82F6', color: refresh.isPending ? '#334155' : '#3B82F6' }}
        >
          {refresh.isPending ? 'Computing...' : 'Refresh Stress'}
        </button>
      </div>

      {isLoading && <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>Loading stress results...</div>}
      {noData && !isLoading && (
        <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>
          No stress results yet. Click <span style={{ color: '#3B82F6' }}>Refresh Stress</span> to replay
          2008 / 2013 / 2018 / 2020 crises and hypothetical shocks against current holdings.
        </div>
      )}
      {refresh.isError && (
        <div style={{ color: '#EF4444', fontSize: 10, padding: '0 0 8px' }}>{(refresh.error as Error).message}</div>
      )}

      {hist.length > 0 && (
        <>
          <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1, marginBottom: 8 }}>
            HISTORICAL REPLAY — actual holding returns over each crisis window
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
            {hist.map(s => <ScenarioCard key={s.scenario} s={s} />)}
          </div>
        </>
      )}
      {hypo.length > 0 && (
        <>
          <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1, marginBottom: 8 }}>
            HYPOTHETICAL SHOCKS — sector-level shock maps on current weights
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {hypo.map(s => <ScenarioCard key={s.scenario} s={s} />)}
          </div>
        </>
      )}
    </div>
  )
}

// ── Factor decomposition panel (Phase R2) ─────────────────────────────────────

function FactorPanel() {
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery<FactorData>({
    queryKey: ['portfolio_factors'],
    queryFn: async () => {
      const r = await fetch(`${API}/api/risk/factors`)
      if (r.status === 404 || r.status === 422) throw new Error('NO_DATA')
      if (!r.ok) throw new Error('Failed to load factor data')
      return r.json()
    },
    staleTime: 5 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
  })

  const refresh = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${API}/api/risk/factors/refresh`, { method: 'POST' })
      if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Factor refresh failed') }
      return r.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portfolio_factors'] }),
  })

  const noData = (error as Error | null)?.message === 'NO_DATA'
  const s      = data?.summary
  const hasPortfolio = (s?.n_positions_modeled ?? 0) > 0
  const exposures = (data?.exposures ?? [])
    .slice()
    .sort((a, b) => b.var_contribution_pct - a.var_contribution_pct)
    .slice(0, 10)
  const maxContrib = Math.max(...exposures.map(e => Math.abs(e.var_contribution_pct)), 1)

  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>
          FACTOR DECOMPOSITION — SYSTEMATIC vs STOCK-SPECIFIC RISK
          {s && <span style={{ color: '#475569', fontWeight: 400, marginLeft: 10, letterSpacing: 0 }}>
            {s.universe_size}-stock model · R² {(s.mean_daily_r2 * 100).toFixed(0)}% · {s.run_date}
          </span>}
        </div>
        <button
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
          style={{ ...ghostBtn, borderColor: '#3B82F6', color: refresh.isPending ? '#334155' : '#3B82F6' }}
          title="Re-estimates the factor model over NIFTY 500 — takes up to a minute"
        >
          {refresh.isPending ? 'Estimating...' : 'Refresh Factors'}
        </button>
      </div>

      {isLoading && <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>Loading factor model...</div>}
      {noData && !isLoading && (
        <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>
          No factor model yet. Click <span style={{ color: '#3B82F6' }}>Refresh Factors</span> —
          estimates sector + momentum/size/value factor returns over the NIFTY 500.
        </div>
      )}
      {refresh.isError && (
        <div style={{ color: '#EF4444', fontSize: 10, padding: '0 0 8px' }}>{(refresh.error as Error).message}</div>
      )}

      {s && !hasPortfolio && !isLoading && (
        <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>
          Factor model estimated ({s.universe_size} stocks), but no holdings could be mapped
          into the factor universe yet.
        </div>
      )}

      {s && hasPortfolio && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <SummaryCard
              label="SYSTEMATIC SHARE"
              value={`${(s.systematic_share_pct ?? 0).toFixed(0)}%`}
              color={(s.systematic_share_pct ?? 0) > 85 ? '#3B82F6' : '#E2E8F0'}
              sub="of portfolio variance from common factors"
            />
            <SummaryCard
              label="SYSTEMATIC VOL"
              value={`${(s.systematic_vol_pct ?? 0).toFixed(1)}%`}
              sub="market/sector/style driven (annualized)"
            />
            <SummaryCard
              label="STOCK-SPECIFIC VOL"
              value={`${(s.idiosyncratic_vol_pct ?? 0).toFixed(1)}%`}
              sub="diversifiable idiosyncratic risk"
            />
          </div>

          <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1, marginBottom: 8 }}>
            TOP FACTOR CONTRIBUTIONS TO PORTFOLIO VARIANCE
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
            {exposures.map(e => (
              <div key={e.factor}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 3 }}>
                  <span style={{ color: '#E2E8F0', fontWeight: 600 }}>
                    {e.factor.replace(/_/g, ' ')}
                    <span style={{
                      marginLeft: 8, fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                      color: e.factor_type === 'STYLE' ? '#9575CD' : '#3B82F6',
                      border: `1px solid ${e.factor_type === 'STYLE' ? '#9575CD' : '#3B82F6'}44`,
                    }}>{e.factor_type}</span>
                  </span>
                  <span style={{ color: '#64748B' }}>
                    exposure {e.exposure.toFixed(2)} · {e.var_contribution_pct.toFixed(1)}% of variance
                  </span>
                </div>
                <div style={{ height: 5, background: '#1E2332', borderRadius: 3 }}>
                  <div style={{
                    width: `${Math.min(Math.abs(e.var_contribution_pct) / maxContrib * 100, 100)}%`,
                    height: 5, borderRadius: 3,
                    background: e.factor_type === 'STYLE' ? '#9575CD' : '#3B82F6',
                    transition: 'width 0.5s',
                  }} />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ── Monte Carlo simulation panel (Phase R3) ───────────────────────────────────

const MC_PATH_CHOICES = [50_000, 100_000, 250_000]

function MonteCarloPanel() {
  const qc = useQueryClient()
  const [nPaths,  setNPaths]  = useState(100_000)
  const [horizon, setHorizon] = useState<1 | 10>(1)

  const { data, isLoading, error } = useQuery<McData>({
    queryKey: ['portfolio_mc'],
    queryFn: async () => {
      const r = await fetch(`${API}/api/risk/simulate`)
      if (r.status === 404 || r.status === 422) throw new Error('NO_DATA')
      if (!r.ok) throw new Error('Failed to load simulation results')
      return r.json()
    },
    staleTime: 5 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
  })

  const simulate = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${API}/api/risk/simulate?n_paths=${nPaths}`, { method: 'POST' })
      if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Simulation failed') }
      return r.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portfolio_mc'] }),
  })

  const noData = (error as Error | null)?.message === 'NO_DATA'
  const res  = (data?.results ?? []).find(r => r.horizon_days === horizon)
  const bins = (data?.distribution ?? []).filter(b => b.horizon_days === horizon)
  const maxCount = Math.max(...bins.map(b => b.count), 1)
  const varCut = res ? -res.mc_var_95 : 0   // P&L value at the VaR95 threshold

  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>
          MONTE CARLO SIMULATION — CORRELATED P&amp;L DISTRIBUTION
          {res && <span style={{ color: '#475569', fontWeight: 400, marginLeft: 10, letterSpacing: 0 }}>
            {(res.n_paths / 1000).toFixed(0)}K paths · {res.run_date} · seeded (reproducible)
          </span>}
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <select
            value={nPaths}
            onChange={e => setNPaths(Number(e.target.value))}
            style={{ ...inp, width: 100, fontSize: 10, padding: '3px 6px' }}
          >
            {MC_PATH_CHOICES.map(n => <option key={n} value={n}>{n / 1000}K paths</option>)}
          </select>
          <button
            onClick={() => simulate.mutate()}
            disabled={simulate.isPending}
            style={{ ...ghostBtn, borderColor: '#22C55E', color: simulate.isPending ? '#334155' : '#22C55E' }}
          >
            {simulate.isPending ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {isLoading && <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>Loading simulation results...</div>}
      {noData && !isLoading && (
        <div style={{ color: '#64748B', fontSize: 11, padding: 12 }}>
          No simulation yet. Click <span style={{ color: '#22C55E' }}>Run Simulation</span> —
          generates correlated return paths (Ledoit-Wolf covariance, Cholesky, antithetic
          variates) and prices the full P&amp;L distribution. Takes ~5 seconds.
        </div>
      )}
      {simulate.isError && (
        <div style={{ color: '#EF4444', fontSize: 10, padding: '0 0 8px' }}>{(simulate.error as Error).message}</div>
      )}

      {res && (
        <>
          {/* Horizon toggle */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
            {([1, 10] as const).map(h => (
              <button key={h} onClick={() => setHorizon(h)} style={{
                padding: '3px 12px', borderRadius: 3, fontSize: 10, cursor: 'pointer',
                border: `1px solid ${horizon === h ? '#22C55E' : '#1E2332'}`,
                background: horizon === h ? '#22C55E18' : 'transparent',
                color: horizon === h ? '#22C55E' : '#64748B',
                fontWeight: horizon === h ? 700 : 400,
              }}>{h} Day{h > 1 ? 's' : ''}</button>
            ))}
            <span style={{ color: '#475569', fontSize: 9, alignSelf: 'center', marginLeft: 6 }}>
              10-day figures are fully compounded paths, not sqrt-scaled
            </span>
          </div>

          {/* MC risk cards */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <SummaryCard
              label={`MC VaR 95% · ${horizon}D`}
              value={riskFmt(res.mc_var_95)}
              color="#F59E0B"
              sub={`${(res.mc_var_95 / res.portfolio_value * 100).toFixed(2)}% of portfolio`}
            />
            <SummaryCard
              label={`MC VaR 99% · ${horizon}D`}
              value={riskFmt(res.mc_var_99)}
              color="#EF4444"
              sub={`${(res.mc_var_99 / res.portfolio_value * 100).toFixed(2)}% of portfolio`}
            />
            <SummaryCard
              label={`MC ES 97.5% · ${horizon}D`}
              value={riskFmt(res.mc_es_975)}
              color="#EF4444"
              sub={`ES 99%: ${riskFmt(res.mc_es_99)}`}
            />
            <SummaryCard
              label="P&L RANGE (1-99 PCTL)"
              value={`${riskFmt(res.pnl_p01)} / +${riskFmt(res.pnl_p99)}`}
              sub={`std ${riskFmt(res.pnl_std)}`}
            />
          </div>

          {/* Distribution histogram */}
          {bins.length > 0 && (
            <div>
              <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1, marginBottom: 8 }}>
                SIMULATED P&amp;L DISTRIBUTION — red bins fall beyond the 95% VaR cut
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 110 }}>
                {bins.map((b, i) => {
                  const beyondVar = b.bin_right <= varCut
                  const positive  = b.bin_left >= 0
                  return (
                    <div
                      key={i}
                      title={`${riskFmt(b.bin_left)} to ${riskFmt(b.bin_right)}: ${b.count} paths`}
                      style={{
                        flex: 1,
                        height: `${Math.max(b.count / maxCount * 100, b.count > 0 ? 2 : 0)}%`,
                        background: beyondVar ? '#EF4444' : positive ? '#22C55E88' : '#3B82F688',
                        borderRadius: '2px 2px 0 0',
                      }}
                    />
                  )
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#475569', marginTop: 4 }}>
                <span>{riskFmt(bins[0]?.bin_left)}</span>
                <span>0</span>
                <span>+{riskFmt(bins[bins.length - 1]?.bin_right)}</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
