import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API = 'http://localhost:8001'

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
  STRONG_CANDIDATE: '#22C55E',
  EMERGING:         '#10B981',
  WATCHLIST:        '#F59E0B',
  NEUTRAL:          '#64748B',
  AVOID:            '#EF4444',
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
