import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

const API = 'http://localhost:8001'

// ── Types ─────────────────────────────────────────────────────────────────────

type Metrics = {
  trade_count:   number
  win_count:     number
  loss_count:    number
  hit_rate:      number
  avg_return:    number
  median_return: number
  best_trade:    number
  worst_trade:   number
  std_return:    number
  sharpe:        number
}

type TradeRow = {
  symbol:         string
  sector:         string | null
  entry_date:     string
  entry_price:    number | null
  label:          string | null
  bull_run_score: number | null
  strategy:       string
  ret_30d:        number | null
  ret_60d:        number | null
  ret_90d:        number | null
  ret_180d:       number | null
  ret_365d:       number | null
}

type BacktestResult = {
  strategy:    string
  metrics:     Metrics
  trades:      TradeRow[]
  total_trades: number
}

type Strategy = 'label' | 'momentum' | 'portfolio'

// ── API calls ─────────────────────────────────────────────────────────────────

async function runLabelScreen(label: string, lookback_days: number): Promise<BacktestResult> {
  const r = await fetch(`${API}/api/backtest/label-screen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label, lookback_days }),
  })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Label screen failed')
  return r.json()
}

async function runMomentumScreen(params: {
  min_ret_30d: number; min_ret_365d: number; hold_days: number
  start_date?: string; end_date?: string; max_symbols: number
}): Promise<BacktestResult> {
  const r = await fetch(`${API}/api/backtest/momentum-screen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Momentum screen failed')
  return r.json()
}

async function runPortfolioTrades(): Promise<BacktestResult> {
  const r = await fetch(`${API}/api/backtest/portfolio-trades`, { method: 'POST' })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Portfolio backtest failed')
  return r.json()
}

// ── Shared styles ─────────────────────────────────────────────────────────────

const inp: React.CSSProperties = {
  background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 4,
  color: '#E2E8F0', padding: '5px 10px', fontSize: 11, outline: 'none', width: '100%',
}

const th: React.CSSProperties = {
  padding: '6px 10px', textAlign: 'left', fontSize: 10, fontWeight: 600,
  color: '#64748B', whiteSpace: 'nowrap', borderBottom: '1px solid #1E2332',
}

const td: React.CSSProperties = { padding: '6px 10px', fontSize: 11 }

const LABEL_COLORS: Record<string, string> = {
  STRONG_CANDIDATE: '#22C55E',
  EMERGING:         '#10B981',
  WATCHLIST:        '#F59E0B',
  NEUTRAL:          '#64748B',
  AVOID:            '#EF4444',
}

// ── Small components ──────────────────────────────────────────────────────────

function MetricCard({ label, value, color = '#E2E8F0', sub }: {
  label: string; value: string; color?: string; sub?: string
}) {
  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332', borderRadius: 6,
      padding: '12px 16px', flex: 1, minWidth: 110,
    }}>
      <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 2, marginBottom: 5 }}>{label}</div>
      <div style={{ color, fontSize: 18, fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ color: '#475569', fontSize: 10, marginTop: 3 }}>{sub}</div>}
    </div>
  )
}

function MetricsBar({ m }: { m: Metrics }) {
  const hitC    = m.hit_rate >= 60 ? '#22C55E' : m.hit_rate >= 45 ? '#F59E0B' : '#EF4444'
  const retC    = m.avg_return >= 0 ? '#22C55E' : '#EF4444'
  const sharpeC = m.sharpe >= 1 ? '#22C55E' : m.sharpe >= 0 ? '#F59E0B' : '#EF4444'
  const sign    = (v: number) => v >= 0 ? `+${v}` : String(v)
  return (
    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
      <MetricCard label="TRADES"    value={String(m.trade_count)} sub={`${m.win_count}W / ${m.loss_count}L`} />
      <MetricCard label="HIT RATE"  value={`${m.hit_rate}%`}     color={hitC} />
      <MetricCard label="AVG RETURN" value={`${sign(m.avg_return)}%`} color={retC} />
      <MetricCard label="MEDIAN"    value={`${sign(m.median_return)}%`} color={retC} />
      <MetricCard label="BEST"      value={`+${m.best_trade}%`}  color="#22C55E" />
      <MetricCard label="WORST"     value={`${m.worst_trade}%`}  color="#EF4444" />
      <MetricCard label="SHARPE"    value={m.sharpe.toFixed(2)}  color={sharpeC} sub="annualised" />
      <MetricCard label="STD DEV"   value={`${m.std_return}%`}   color="#94A3B8" />
    </div>
  )
}

function RetCell({ val }: { val: number | null }) {
  if (val == null) return <span style={{ color: '#1E2332' }}>--</span>
  const c    = val > 0 ? '#22C55E' : val < 0 ? '#EF4444' : '#64748B'
  const sign = val > 0 ? '+' : ''
  return <span style={{ color: c }}>{sign}{val.toFixed(1)}%</span>
}

function LabelBadge({ label }: { label: string | null }) {
  if (!label) return <span style={{ color: '#334155' }}>--</span>
  const c = LABEL_COLORS[label] ?? '#64748B'
  return (
    <span style={{
      background: `${c}22`, color: c, border: `1px solid ${c}44`,
      borderRadius: 3, padding: '1px 6px', fontSize: 9, fontWeight: 700,
      whiteSpace: 'nowrap',
    }}>
      {label.replace('_', ' ')}
    </span>
  )
}

function TabBtn({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      padding: '6px 18px', borderRadius: 4, fontSize: 11, fontWeight: 700,
      cursor: 'pointer', border: '1px solid',
      borderColor:     active ? '#22C55E' : '#1E2332',
      backgroundColor: active ? '#22C55E22' : 'transparent',
      color:           active ? '#22C55E' : '#64748B',
    }}>
      {label}
    </button>
  )
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <div style={{ color: '#64748B', fontSize: 10, marginBottom: 4 }}>{children}</div>
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export function BacktestPage() {
  const [strategy, setStrategy] = useState<Strategy>('label')
  const [result,   setResult]   = useState<BacktestResult | null>(null)
  const [error,    setError]    = useState('')

  // Label screen params
  const [lsLabel,    setLsLabel]    = useState('EMERGING')
  const [lsLookback, setLsLookback] = useState(180)

  // Momentum screen params
  const [msRet30,   setMsRet30]   = useState(15)
  const [msRet365,  setMsRet365]  = useState(30)
  const [msHold,    setMsHold]    = useState(60)
  const [msStart,   setMsStart]   = useState('')
  const [msEnd,     setMsEnd]     = useState('')
  const [msMaxSym,  setMsMaxSym]  = useState(1000)

  const mutation = useMutation<BacktestResult, Error, void>({
    mutationFn: async () => {
      setError('')
      if (strategy === 'label')    return runLabelScreen(lsLabel, lsLookback)
      if (strategy === 'momentum') return runMomentumScreen({
        min_ret_30d: msRet30, min_ret_365d: msRet365, hold_days: msHold,
        start_date: msStart || undefined, end_date: msEnd || undefined,
        max_symbols: msMaxSym,
      })
      return runPortfolioTrades()
    },
    onSuccess: d  => setResult(d),
    onError:   e  => setError(e.message),
  })

  const trades     = result?.trades ?? []
  const isRunning  = mutation.isPending

  return (
    <div style={{ maxWidth: 1320 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
          BACKTESTING
        </h1>
        <span style={{ color: '#475569', fontSize: 10 }}>
          Phase 21 -- uses 30yr parquet price cache. Symbol renames resolved via Phase 17.
        </span>
      </div>

      {/* Strategy panel */}
      <div style={{
        background: '#141720', border: '1px solid #1E2332',
        borderRadius: 6, padding: 20, marginBottom: 20,
      }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 14 }}>
          STRATEGY
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 18 }}>
          <TabBtn label="Label Screen"    active={strategy === 'label'}     onClick={() => setStrategy('label')} />
          <TabBtn label="Momentum Screen" active={strategy === 'momentum'}  onClick={() => setStrategy('momentum')} />
          <TabBtn label="Portfolio Trades" active={strategy === 'portfolio'} onClick={() => setStrategy('portfolio')} />
        </div>

        {/* Label Screen params */}
        {strategy === 'label' && (
          <div>
            <p style={{ color: '#64748B', fontSize: 10, margin: '0 0 14px' }}>
              Takes all stocks currently labelled with the selected class and computes
              what the return would have been if bought N days ago. Validates label quality.
            </p>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ width: 160 }}>
                <FieldLabel>Label</FieldLabel>
                <select value={lsLabel} onChange={e => setLsLabel(e.target.value)} style={inp}>
                  <option value="EMERGING">EMERGING</option>
                  <option value="WATCHLIST">WATCHLIST</option>
                  <option value="STRONG_CANDIDATE">STRONG_CANDIDATE</option>
                  <option value="NEUTRAL">NEUTRAL</option>
                </select>
              </div>
              <div style={{ width: 140 }}>
                <FieldLabel>Lookback days</FieldLabel>
                <input type="number" min={30} max={730} value={lsLookback}
                  onChange={e => setLsLookback(parseInt(e.target.value) || 180)}
                  style={inp} />
              </div>
            </div>
          </div>
        )}

        {/* Momentum Screen params */}
        {strategy === 'momentum' && (
          <div>
            <p style={{ color: '#64748B', fontSize: 10, margin: '0 0 14px' }}>
              Scans the intelligence universe for historical momentum entry signals.
              Entry when 30d AND 365d returns (trading days) cross the thresholds.
              <span style={{ color: '#F59E0B' }}> Large symbol counts take 20-40 seconds.</span>
            </p>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ width: 130 }}>
                <FieldLabel>Min 30d return %</FieldLabel>
                <input type="number" value={msRet30}
                  onChange={e => setMsRet30(parseFloat(e.target.value) || 15)}
                  style={inp} />
              </div>
              <div style={{ width: 130 }}>
                <FieldLabel>Min 365d return %</FieldLabel>
                <input type="number" value={msRet365}
                  onChange={e => setMsRet365(parseFloat(e.target.value) || 30)}
                  style={inp} />
              </div>
              <div style={{ width: 110 }}>
                <FieldLabel>Hold days</FieldLabel>
                <input type="number" min={10} max={365} value={msHold}
                  onChange={e => setMsHold(parseInt(e.target.value) || 60)}
                  style={inp} />
              </div>
              <div style={{ width: 140 }}>
                <FieldLabel>Start date</FieldLabel>
                <input type="date" value={msStart} onChange={e => setMsStart(e.target.value)}
                  style={{ ...inp, colorScheme: 'dark' }} />
              </div>
              <div style={{ width: 140 }}>
                <FieldLabel>End date</FieldLabel>
                <input type="date" value={msEnd} onChange={e => setMsEnd(e.target.value)}
                  style={{ ...inp, colorScheme: 'dark' }} />
              </div>
              <div style={{ width: 120 }}>
                <FieldLabel>Max symbols</FieldLabel>
                <input type="number" min={50} max={2500} value={msMaxSym}
                  onChange={e => setMsMaxSym(parseInt(e.target.value) || 1000)}
                  style={inp} />
              </div>
            </div>
          </div>
        )}

        {/* Portfolio Trades description */}
        {strategy === 'portfolio' && (
          <p style={{ color: '#64748B', fontSize: 10, margin: 0 }}>
            Replays each BUY transaction in your portfolio at the actual buy price and
            computes forward returns at 30/60/90/180/365 days. Add trades on the
            Portfolio page first.
          </p>
        )}

        {/* Run button */}
        <div style={{ display: 'flex', gap: 14, alignItems: 'center', marginTop: 18 }}>
          <button
            onClick={() => mutation.mutate()}
            disabled={isRunning}
            style={{
              padding: '8px 28px', borderRadius: 4, fontWeight: 700, fontSize: 12,
              border: '1px solid #22C55E', background: 'transparent',
              color: isRunning ? '#334155' : '#22C55E',
              cursor: isRunning ? 'not-allowed' : 'pointer',
            }}
          >
            {isRunning
              ? strategy === 'momentum' ? 'Scanning... (20-40s)' : 'Running...'
              : 'Run Backtest'}
          </button>
          {error && (
            <span style={{ color: '#EF4444', fontSize: 11 }}>{error}</span>
          )}
          {result && !isRunning && (
            <span style={{ color: '#64748B', fontSize: 10 }}>
              {result.total_trades} signals -- showing top 200
            </span>
          )}
        </div>
      </div>

      {/* Metrics bar */}
      {result?.metrics && <MetricsBar m={result.metrics} />}

      {/* Results table */}
      {trades.length > 0 && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16,
        }}>
          <div style={{
            color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 14,
          }}>
            TRADE RESULTS -- {result?.strategy}
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 960 }}>
              <thead>
                <tr>
                  <th style={th}>Symbol</th>
                  <th style={th}>Entry Date</th>
                  <th style={{ ...th, textAlign: 'right' }}>Entry Price</th>
                  <th style={th}>Label</th>
                  <th style={{ ...th, textAlign: 'right' }}>Score</th>
                  <th style={th}>Sector</th>
                  <th style={{ ...th, textAlign: 'right' }}>+30d</th>
                  <th style={{ ...th, textAlign: 'right' }}>+60d</th>
                  <th style={{ ...th, textAlign: 'right' }}>+90d</th>
                  <th style={{ ...th, textAlign: 'right' }}>+180d</th>
                  <th style={{ ...th, textAlign: 'right' }}>+365d</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1E233210' }}>
                    <td style={{ ...td, fontWeight: 700 }}>
                      <a
                        href={`/stocks/${t.symbol}`}
                        style={{ color: '#E2E8F0', textDecoration: 'none' }}
                        onMouseOver={e => (e.currentTarget.style.color = '#22C55E')}
                        onMouseOut={e  => (e.currentTarget.style.color = '#E2E8F0')}
                      >
                        {t.symbol}
                      </a>
                    </td>
                    <td style={{ ...td, color: '#64748B' }}>{t.entry_date}</td>
                    <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>
                      {t.entry_price != null ? t.entry_price.toFixed(2) : '--'}
                    </td>
                    <td style={td}><LabelBadge label={t.label} /></td>
                    <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                      {t.bull_run_score != null ? t.bull_run_score.toFixed(0) : '--'}
                    </td>
                    <td style={{ ...td, color: '#475569', fontSize: 10 }}>
                      {t.sector ?? '--'}
                    </td>
                    <td style={{ ...td, textAlign: 'right' }}><RetCell val={t.ret_30d} /></td>
                    <td style={{ ...td, textAlign: 'right' }}><RetCell val={t.ret_60d} /></td>
                    <td style={{ ...td, textAlign: 'right' }}><RetCell val={t.ret_90d} /></td>
                    <td style={{ ...td, textAlign: 'right' }}><RetCell val={t.ret_180d} /></td>
                    <td style={{ ...td, textAlign: 'right' }}><RetCell val={t.ret_365d} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isRunning && !result && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332', borderRadius: 6,
          padding: 60, textAlign: 'center', color: '#334155', fontSize: 12,
        }}>
          Select a strategy above and click Run Backtest.
        </div>
      )}
    </div>
  )
}
