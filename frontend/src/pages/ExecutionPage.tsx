import { useState, useEffect, useCallback } from 'react'

const API = '/api/execution'

// ── Types ─────────────────────────────────────────────────────────────────────

interface ExecConfig {
  paper_mode:             boolean
  portfolio_value:        number
  max_position_pct:       number
  max_sector_pct:         number
  min_cash_pct:           number
  allow_duplicate_orders: boolean
}

interface Recommendation {
  symbol:          string
  sector:          string
  label:           string
  bull_run_score:  number
  ml_score:        number
  composite_score: number
  rotation_signal: string
  close_now:       number
  action:          string
  suggested_qty:   number
  suggested_value: number
  suggested_pct:   number
}

interface QueueItem extends Recommendation {
  qty:        number
  price:      number
  order_type: 'MARKET' | 'LIMIT'
}

interface BlotterOrder {
  order_id:        string
  created_at:      string
  symbol:          string
  sector:          string
  action:          string
  qty:             number
  price:           number
  order_type:      string
  status:          string
  paper:           boolean
  filled_qty:      number
  avg_fill_price:  number
  broker_order_id: string
  reject_reason:   string
  order_value:     number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined, dec = 2) {
  if (n == null || isNaN(n)) return '-'
  return n.toLocaleString('en-IN', { maximumFractionDigits: dec })
}

function fmtINR(n: number | null | undefined) {
  if (n == null || isNaN(n)) return '-'
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

function rotColor(sig: string) {
  const s = (sig || '').toUpperCase()
  if (s === 'ROTATING_IN')  return '#22C55E'
  if (s === 'PRICE_LED')    return '#EAB308'
  if (s === 'ROTATING_OUT') return '#EF4444'
  return '#64748B'
}

function statusColor(s: string) {
  if (s === 'FILLED')    return '#22C55E'
  if (s === 'PENDING')   return '#EAB308'
  if (s === 'CANCELLED') return '#64748B'
  if (s === 'REJECTED')  return '#EF4444'
  return '#94A3B8'
}

// ── Sub-components ────────────────────────────────────────────────────────────

function PaperBadge({ paper }: { paper: boolean }) {
  return (
    <span style={{
      fontSize: 10, padding: '2px 6px', borderRadius: 4, fontWeight: 700,
      background: paper ? '#1E3A5F' : '#3B1F1F',
      color:      paper ? '#60A5FA' : '#FCA5A5',
    }}>
      {paper ? 'PAPER' : 'LIVE'}
    </span>
  )
}

function LabelBadge({ label }: { label: string }) {
  const colors: Record<string, [string, string]> = {
    EMERGING:    ['#14532D', '#4ADE80'],
    ACCUMULATION:['#1E3A5F', '#60A5FA'],
    WATCHLIST:   ['#1C1917', '#A8A29E'],
    AVOID:       ['#3B1F1F', '#FCA5A5'],
  }
  const [bg, fg] = colors[label] ?? ['#1E2332', '#94A3B8']
  return (
    <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: bg, color: fg, fontWeight: 700 }}>
      {label}
    </span>
  )
}

// ── Signals Tab ───────────────────────────────────────────────────────────────

function SignalsTab({
  queue,
  onQueue,
  paperMode,
}: {
  queue: QueueItem[]
  onQueue: (rec: Recommendation) => void
  paperMode: boolean
}) {
  const [pfValue, setPfValue]   = useState('')
  const [topN, setTopN]         = useState('10')
  const [minScore, setMinScore] = useState('50')
  const [labelFilter, setLabelFilter] = useState<string>('EMERGING')
  const [recs, setRecs]         = useState<Recommendation[]>([])
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')

  const generate = async () => {
    setLoading(true); setErr('')
    try {
      const body: Record<string, unknown> = {
        top_n:     parseInt(topN) || 10,
        min_score: parseFloat(minScore) || 50,
        action:    'BUY',
      }
      const pf = parseFloat(pfValue)
      if (pf > 0) body['portfolio_value'] = pf
      if (labelFilter) body['labels'] = [labelFilter]

      const r = await fetch(`${API}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await r.json()
      if (!r.ok) { setErr(data.detail || 'Error'); return }
      setRecs(data.recommendations || [])
    } catch (e: unknown) {
      setErr(String(e))
    } finally {
      setLoading(false)
    }
  }

  const queuedSymbols = new Set(queue.map(q => q.symbol))

  const LABELS = ['EMERGING', 'ACCUMULATION', 'WATCHLIST', '']

  return (
    <div>
      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' }}>
        <div>
          <div style={{ fontSize: 11, color: '#64748B', marginBottom: 4 }}>Portfolio Value (INR)</div>
          <input
            value={pfValue} onChange={e => setPfValue(e.target.value)}
            placeholder="e.g. 1000000"
            style={{ background: '#1E2332', border: '1px solid #2D3348', color: '#E2E8F0', padding: '6px 10px', borderRadius: 6, width: 150, fontSize: 13 }}
          />
        </div>
        <div>
          <div style={{ fontSize: 11, color: '#64748B', marginBottom: 4 }}>Top N</div>
          <input
            value={topN} onChange={e => setTopN(e.target.value)} type="number"
            style={{ background: '#1E2332', border: '1px solid #2D3348', color: '#E2E8F0', padding: '6px 10px', borderRadius: 6, width: 70, fontSize: 13 }}
          />
        </div>
        <div>
          <div style={{ fontSize: 11, color: '#64748B', marginBottom: 4 }}>Min Score</div>
          <input
            value={minScore} onChange={e => setMinScore(e.target.value)} type="number"
            style={{ background: '#1E2332', border: '1px solid #2D3348', color: '#E2E8F0', padding: '6px 10px', borderRadius: 6, width: 70, fontSize: 13 }}
          />
        </div>
        <div>
          <div style={{ fontSize: 11, color: '#64748B', marginBottom: 4 }}>Label</div>
          <select
            value={labelFilter} onChange={e => setLabelFilter(e.target.value)}
            style={{ background: '#1E2332', border: '1px solid #2D3348', color: '#E2E8F0', padding: '6px 10px', borderRadius: 6, fontSize: 13 }}
          >
            {LABELS.map(l => <option key={l} value={l}>{l || 'All labels'}</option>)}
          </select>
        </div>
        <button
          onClick={generate} disabled={loading}
          style={{ padding: '7px 18px', background: '#22C55E', color: '#000', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
        >
          {loading ? 'Generating...' : 'Generate'}
        </button>
        <PaperBadge paper={paperMode} />
      </div>

      {err && <div style={{ color: '#EF4444', fontSize: 13, marginBottom: 12 }}>{err}</div>}

      {recs.length === 0 ? (
        <div style={{ color: '#64748B', fontSize: 13 }}>
          {loading ? 'Fetching recommendations...' : 'Click Generate to load signal-based recommendations.'}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ color: '#64748B', borderBottom: '1px solid #1E2332' }}>
                {['Symbol','Sector','Label','Score','ML','LTP','Qty','Value','%PF','Rotation',''].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontWeight: 600, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recs.map(rec => {
                const inQueue = queuedSymbols.has(rec.symbol)
                return (
                  <tr key={rec.symbol} style={{ borderBottom: '1px solid #1A1D2E', background: inQueue ? '#0F2010' : 'transparent' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 700, color: '#E2E8F0' }}>{rec.symbol}</td>
                    <td style={{ padding: '8px 10px', color: '#94A3B8', fontSize: 12 }}>{rec.sector}</td>
                    <td style={{ padding: '8px 10px' }}><LabelBadge label={rec.label} /></td>
                    <td style={{ padding: '8px 10px', color: '#22C55E', fontWeight: 700 }}>{fmt(rec.composite_score)}</td>
                    <td style={{ padding: '8px 10px', color: '#60A5FA' }}>{fmt(rec.ml_score)}</td>
                    <td style={{ padding: '8px 10px', color: '#E2E8F0' }}>{fmtINR(rec.close_now)}</td>
                    <td style={{ padding: '8px 10px', color: '#E2E8F0' }}>{rec.suggested_qty}</td>
                    <td style={{ padding: '8px 10px', color: '#E2E8F0' }}>{fmtINR(rec.suggested_value)}</td>
                    <td style={{ padding: '8px 10px', color: '#94A3B8' }}>{fmt(rec.suggested_pct, 1)}%</td>
                    <td style={{ padding: '8px 10px', color: rotColor(rec.rotation_signal), fontSize: 11 }}>{rec.rotation_signal}</td>
                    <td style={{ padding: '8px 10px' }}>
                      <button
                        onClick={() => onQueue(rec)}
                        disabled={inQueue}
                        style={{
                          padding: '4px 12px', borderRadius: 4, border: 'none', cursor: inQueue ? 'default' : 'pointer',
                          background: inQueue ? '#1E2332' : '#22C55E',
                          color:      inQueue ? '#64748B' : '#000',
                          fontWeight: 700, fontSize: 11,
                        }}
                      >
                        {inQueue ? 'Queued' : '+ Queue'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Queue Tab ─────────────────────────────────────────────────────────────────

function QueueTab({
  queue,
  onRemove,
  onPlace,
  onPlaceAll,
  paperMode,
}: {
  queue: QueueItem[]
  onRemove: (symbol: string) => void
  onPlace: (item: QueueItem) => Promise<void>
  onPlaceAll: () => Promise<void>
  paperMode: boolean
}) {
  const [placing, setPlacing] = useState<Set<string>>(new Set())

  const handlePlace = async (item: QueueItem) => {
    setPlacing(prev => new Set([...prev, item.symbol]))
    try { await onPlace(item) }
    finally { setPlacing(prev => { const n = new Set(prev); n.delete(item.symbol); return n }) }
  }

  if (queue.length === 0) {
    return <div style={{ color: '#64748B', fontSize: 13 }}>Queue is empty. Add recommendations from the Signals tab.</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ color: '#94A3B8', fontSize: 13 }}>{queue.length} orders in queue</span>
          <PaperBadge paper={paperMode} />
        </div>
        <button
          onClick={onPlaceAll}
          style={{ padding: '7px 18px', background: '#22C55E', color: '#000', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
        >
          Place All
        </button>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ color: '#64748B', borderBottom: '1px solid #1E2332' }}>
            {['Symbol','Sector','Action','Qty','Type','Est. Value','Score',''].map(h => (
              <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontWeight: 600, fontSize: 11 }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {queue.map(item => (
            <tr key={item.symbol} style={{ borderBottom: '1px solid #1A1D2E' }}>
              <td style={{ padding: '8px 10px', fontWeight: 700, color: '#E2E8F0' }}>{item.symbol}</td>
              <td style={{ padding: '8px 10px', color: '#94A3B8', fontSize: 12 }}>{item.sector}</td>
              <td style={{ padding: '8px 10px', color: '#22C55E', fontWeight: 700 }}>{item.action}</td>
              <td style={{ padding: '8px 10px', color: '#E2E8F0' }}>{item.qty}</td>
              <td style={{ padding: '8px 10px', color: '#94A3B8' }}>MARKET</td>
              <td style={{ padding: '8px 10px', color: '#E2E8F0' }}>{fmtINR(item.suggested_value)}</td>
              <td style={{ padding: '8px 10px', color: '#22C55E' }}>{fmt(item.composite_score)}</td>
              <td style={{ padding: '8px 10px', display: 'flex', gap: 6 }}>
                <button
                  onClick={() => handlePlace(item)}
                  disabled={placing.has(item.symbol)}
                  style={{ padding: '4px 12px', borderRadius: 4, border: 'none', cursor: 'pointer', background: '#22C55E', color: '#000', fontWeight: 700, fontSize: 11 }}
                >
                  {placing.has(item.symbol) ? '...' : 'Place'}
                </button>
                <button
                  onClick={() => onRemove(item.symbol)}
                  style={{ padding: '4px 10px', borderRadius: 4, border: '1px solid #2D3348', cursor: 'pointer', background: 'transparent', color: '#EF4444', fontSize: 11 }}
                >
                  X
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Blotter Tab ───────────────────────────────────────────────────────────────

function BlotterTab() {
  const [filter, setFilter]   = useState('ALL')
  const [orders, setOrders]   = useState<BlotterOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState<Set<string>>(new Set())

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API}/orders?status=${filter === 'ALL' ? '' : filter}&limit=200`)
      const d = await r.json()
      setOrders(d.orders || [])
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => { load() }, [load])

  const cancelOrder = async (orderId: string) => {
    setCancelling(prev => new Set([...prev, orderId]))
    try {
      await fetch(`${API}/order/${orderId}`, { method: 'DELETE' })
      await load()
    } finally {
      setCancelling(prev => { const n = new Set(prev); n.delete(orderId); return n })
    }
  }

  const FILTERS = ['ALL', 'PENDING', 'FILLED', 'CANCELLED', 'REJECTED']

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
        {FILTERS.map(f => (
          <button key={f} onClick={() => setFilter(f)}
            style={{
              padding: '5px 12px', borderRadius: 4, border: '1px solid #2D3348', cursor: 'pointer', fontSize: 11, fontWeight: 700,
              background: filter === f ? '#22C55E' : 'transparent',
              color:      filter === f ? '#000' : '#64748B',
            }}
          >{f}</button>
        ))}
        <button onClick={load}
          style={{ marginLeft: 'auto', padding: '5px 12px', borderRadius: 4, border: '1px solid #2D3348', cursor: 'pointer', background: 'transparent', color: '#64748B', fontSize: 11 }}
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ color: '#64748B', fontSize: 13 }}>Loading...</div>
      ) : orders.length === 0 ? (
        <div style={{ color: '#64748B', fontSize: 13 }}>No orders found.</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ color: '#64748B', borderBottom: '1px solid #1E2332' }}>
                {['Order ID','Time','Symbol','Action','Qty','Type','Status','Mode','Fill Qty','Avg Price','Value',''].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, fontSize: 11, whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.order_id} style={{ borderBottom: '1px solid #1A1D2E' }}>
                  <td style={{ padding: '7px 8px', color: '#64748B', fontSize: 11, fontFamily: 'monospace' }}>{o.order_id}</td>
                  <td style={{ padding: '7px 8px', color: '#64748B', fontSize: 11, whiteSpace: 'nowrap' }}>
                    {o.created_at ? new Date(o.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'}
                  </td>
                  <td style={{ padding: '7px 8px', fontWeight: 700, color: '#E2E8F0' }}>{o.symbol}</td>
                  <td style={{ padding: '7px 8px', color: o.action === 'BUY' ? '#22C55E' : '#EF4444', fontWeight: 700, fontSize: 11 }}>{o.action}</td>
                  <td style={{ padding: '7px 8px', color: '#E2E8F0' }}>{o.qty}</td>
                  <td style={{ padding: '7px 8px', color: '#94A3B8', fontSize: 11 }}>{o.order_type}</td>
                  <td style={{ padding: '7px 8px' }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: statusColor(o.status) }}>{o.status}</span>
                    {o.reject_reason && <div style={{ fontSize: 10, color: '#EF4444', marginTop: 2 }}>{o.reject_reason}</div>}
                  </td>
                  <td style={{ padding: '7px 8px' }}><PaperBadge paper={o.paper} /></td>
                  <td style={{ padding: '7px 8px', color: '#94A3B8' }}>{o.filled_qty || '-'}</td>
                  <td style={{ padding: '7px 8px', color: '#94A3B8' }}>{o.avg_fill_price > 0 ? fmtINR(o.avg_fill_price) : '-'}</td>
                  <td style={{ padding: '7px 8px', color: '#E2E8F0' }}>{o.order_value > 0 ? fmtINR(o.order_value) : '-'}</td>
                  <td style={{ padding: '7px 8px' }}>
                    {o.status === 'PENDING' && (
                      <button
                        onClick={() => cancelOrder(o.order_id)}
                        disabled={cancelling.has(o.order_id)}
                        style={{ padding: '3px 8px', borderRadius: 4, border: '1px solid #EF4444', cursor: 'pointer', background: 'transparent', color: '#EF4444', fontSize: 10 }}
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Risk Config Tab ───────────────────────────────────────────────────────────

function ConfigTab() {
  const [config, setConfig] = useState<ExecConfig>({
    paper_mode: true, portfolio_value: 0,
    max_position_pct: 10, max_sector_pct: 25, min_cash_pct: 10,
    allow_duplicate_orders: false,
  })
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [msg, setMsg]           = useState('')

  useEffect(() => {
    fetch(`${API}/config`)
      .then(r => r.json())
      .then(d => { setConfig(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const save = async () => {
    setSaving(true); setMsg('')
    try {
      const r = await fetch(`${API}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      const d = await r.json()
      if (!r.ok) { setMsg(d.detail || 'Error'); return }
      setConfig(d)
      setMsg('Settings saved.')
    } catch (e: unknown) {
      setMsg(String(e))
    } finally {
      setSaving(false)
    }
  }

  const refreshSecurityMaster = async () => {
    setRefreshing(true); setMsg('')
    try {
      const r = await fetch(`${API}/security-master/refresh`, { method: 'POST' })
      const d = await r.json()
      setMsg(r.ok ? `Security master refreshed: ${d.symbols_loaded} symbols loaded.` : (d.detail || 'Error'))
    } catch (e: unknown) {
      setMsg(String(e))
    } finally {
      setRefreshing(false)
    }
  }

  if (loading) return <div style={{ color: '#64748B', fontSize: 13 }}>Loading config...</div>

  const inputStyle = {
    background: '#1E2332', border: '1px solid #2D3348',
    color: '#E2E8F0', padding: '6px 10px', borderRadius: 6, width: 160, fontSize: 13,
  }

  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
      <div style={{ width: 220, color: '#94A3B8', fontSize: 13 }}>{label}</div>
      {children}
    </div>
  )

  return (
    <div style={{ maxWidth: 600 }}>
      {/* Paper mode prominent toggle */}
      <div style={{
        padding: 16, borderRadius: 8, marginBottom: 24,
        border: `2px solid ${config.paper_mode ? '#1D4ED8' : '#DC2626'}`,
        background: config.paper_mode ? '#0F172A' : '#1F0000',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: config.paper_mode ? '#60A5FA' : '#FCA5A5' }}>
              {config.paper_mode ? 'PAPER MODE (Simulated)' : 'LIVE MODE (Real Orders)'}
            </div>
            <div style={{ fontSize: 12, color: '#64748B', marginTop: 4 }}>
              {config.paper_mode
                ? 'Orders are simulated. No real money at risk.'
                : 'Orders are placed via Dhan API. Real money at risk.'}
            </div>
          </div>
          <button
            onClick={() => setConfig(c => ({ ...c, paper_mode: !c.paper_mode }))}
            style={{
              padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13,
              background: config.paper_mode ? '#1D4ED8' : '#DC2626', color: '#FFF',
            }}
          >
            {config.paper_mode ? 'Switch to LIVE' : 'Switch to PAPER'}
          </button>
        </div>
      </div>

      <Field label="Portfolio Value (INR)">
        <input type="number" style={inputStyle} value={config.portfolio_value}
          onChange={e => setConfig(c => ({ ...c, portfolio_value: parseFloat(e.target.value) || 0 }))} />
        <span style={{ fontSize: 11, color: '#64748B' }}>Used for position sizing</span>
      </Field>

      <Field label="Max Position Size (%)">
        <input type="number" style={inputStyle} value={config.max_position_pct}
          onChange={e => setConfig(c => ({ ...c, max_position_pct: parseFloat(e.target.value) || 10 }))} />
        <span style={{ fontSize: 11, color: '#64748B' }}>Single stock cap</span>
      </Field>

      <Field label="Max Sector Concentration (%)">
        <input type="number" style={inputStyle} value={config.max_sector_pct}
          onChange={e => setConfig(c => ({ ...c, max_sector_pct: parseFloat(e.target.value) || 25 }))} />
        <span style={{ fontSize: 11, color: '#64748B' }}>Per-sector cap</span>
      </Field>

      <Field label="Min Cash Reserve (%)">
        <input type="number" style={inputStyle} value={config.min_cash_pct}
          onChange={e => setConfig(c => ({ ...c, min_cash_pct: parseFloat(e.target.value) || 10 }))} />
        <span style={{ fontSize: 11, color: '#64748B' }}>Floor after order</span>
      </Field>

      <Field label="Allow Duplicate Orders">
        <button
          onClick={() => setConfig(c => ({ ...c, allow_duplicate_orders: !c.allow_duplicate_orders }))}
          style={{
            padding: '6px 16px', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13,
            background: config.allow_duplicate_orders ? '#22C55E' : '#1E2332',
            color:      config.allow_duplicate_orders ? '#000' : '#64748B',
          }}
        >
          {config.allow_duplicate_orders ? 'ON' : 'OFF'}
        </button>
        <span style={{ fontSize: 11, color: '#64748B' }}>Multiple orders for same symbol</span>
      </Field>

      <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
        <button
          onClick={save} disabled={saving}
          style={{ padding: '8px 24px', background: '#22C55E', color: '#000', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {msg && <div style={{ marginTop: 12, fontSize: 13, color: msg.includes('Error') || msg.includes('error') ? '#EF4444' : '#22C55E' }}>{msg}</div>}

      {/* Security master section */}
      <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid #1E2332' }}>
        <div style={{ fontWeight: 700, fontSize: 13, color: '#94A3B8', marginBottom: 8 }}>LIVE EXECUTION — Dhan Security Master</div>
        <div style={{ fontSize: 12, color: '#64748B', marginBottom: 12 }}>
          Required for live orders. Downloads Dhan's scrip master and maps symbols to security IDs.
          Requires active Dhan credentials (set in Broker page).
        </div>
        <button
          onClick={refreshSecurityMaster} disabled={refreshing}
          style={{ padding: '7px 18px', background: '#1E2332', border: '1px solid #2D3348', color: '#94A3B8', borderRadius: 6, cursor: 'pointer', fontSize: 12 }}
        >
          {refreshing ? 'Downloading...' : 'Refresh Security Master'}
        </button>
      </div>
    </div>
  )
}

// ── TCA + Slicer Tab (Phase R4) ───────────────────────────────────────────────

interface TcaSummary {
  n_fills:                 number
  n_with_arrival:          number
  total_traded_value:      number
  mean_slip_arrival_bps:   number | null
  mean_slip_vwap_bps:      number | null
  median_slip_vwap_bps:    number | null
  total_cost_vwap_inr:     number | null
  buy_mean_vwap_bps:       number | null
  sell_mean_vwap_bps:      number | null
  worst_fill_order_id:     string
  worst_fill_bps:          number | null
}

interface TcaFill {
  order_id:         string
  fill_date:        string
  symbol:           string
  action:           string
  filled_qty:       number
  avg_fill_price:   number
  arrival_price:    number | null
  vwap_hlc3:        number | null
  slip_arrival_bps: number | null
  slip_vwap_bps:    number | null
  slip_close_bps:   number | null
  benchmark_status: string
}

interface SlicePlan {
  symbol:                string
  qty:                   number
  adv_20d:               number
  participation_pct:     number
  max_participation_pct: number
  exceeds:               boolean
  slices_needed:         boolean
  slices: { slice_no: number; time_ist: string; qty: number; pct_of_order: number }[]
  note:  string
}

function slipColor(bps: number | null): string {
  if (bps == null) return '#64748B'
  if (bps > 25)  return '#EF4444'   // meaningful cost
  if (bps > 0)   return '#EAB308'
  return '#22C55E'                  // favorable
}

function TcaTab() {
  const [summary, setSummary] = useState<TcaSummary | null>(null)
  const [fills,   setFills]   = useState<TcaFill[]>([])
  const [loading, setLoading] = useState(false)
  const [msg,     setMsg]     = useState('')

  const [sliceSym, setSliceSym] = useState('')
  const [sliceQty, setSliceQty] = useState('')
  const [plan,     setPlan]     = useState<SlicePlan | null>(null)
  const [planErr,  setPlanErr]  = useState('')

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/tca`)
      if (r.status === 404) { setMsg('No TCA report yet — click Refresh to compute.'); return }
      const d = await r.json()
      if (!r.ok) { setMsg(d.detail || 'Error'); return }
      setSummary(d.summary); setFills(d.fills ?? []); setMsg('')
    } catch { setMsg('Failed to load TCA') }
  }, [])

  useEffect(() => { load() }, [load])

  const refresh = async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API}/tca/refresh`, { method: 'POST' })
      const d = await r.json()
      if (!r.ok) { setMsg(d.detail || 'Refresh failed'); return }
      setSummary(d.summary); setFills(d.fills ?? []); setMsg('')
    } finally { setLoading(false) }
  }

  const fetchPlan = async () => {
    setPlan(null); setPlanErr('')
    const q = parseInt(sliceQty)
    if (!sliceSym.trim() || !(q > 0)) { setPlanErr('Enter a symbol and positive qty'); return }
    const r = await fetch(`${API}/slice_plan?symbol=${sliceSym.trim().toUpperCase()}&qty=${q}`)
    const d = await r.json()
    if (!r.ok) { setPlanErr(d.detail || 'Failed'); return }
    setPlan(d)
  }

  const card: React.CSSProperties = {
    background: '#141720', border: '1px solid #1E2332', borderRadius: 8,
    padding: '14px 18px', flex: 1, minWidth: 150,
  }
  const th: React.CSSProperties = { padding: '6px 10px', textAlign: 'left', color: '#64748B', fontSize: 11, fontWeight: 600 }
  const td: React.CSSProperties = { padding: '6px 10px', fontSize: 12 }
  const inputSt: React.CSSProperties = {
    background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 6,
    color: '#E2E8F0', padding: '7px 10px', fontSize: 13, outline: 'none',
  }

  return (
    <div>
      {/* TCA summary */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#94A3B8', letterSpacing: 1 }}>
          TRANSACTION COST ANALYSIS
          <span style={{ color: '#475569', fontWeight: 400, marginLeft: 10, fontSize: 11 }}>
            positive bps = cost (bought above / sold below benchmark)
          </span>
        </div>
        <button onClick={refresh} disabled={loading} style={{
          padding: '6px 16px', borderRadius: 6, border: '1px solid #3B82F6',
          background: 'transparent', color: loading ? '#334155' : '#3B82F6',
          cursor: 'pointer', fontSize: 12, fontWeight: 600,
        }}>{loading ? 'Computing...' : 'Refresh TCA'}</button>
      </div>

      {msg && <div style={{ color: '#64748B', fontSize: 12, marginBottom: 14 }}>{msg}</div>}

      {summary && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 18, flexWrap: 'wrap' }}>
          <div style={card}>
            <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1.5, marginBottom: 6 }}>FILLS ANALYZED</div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>{summary.n_fills}</div>
            <div style={{ color: '#64748B', fontSize: 10, marginTop: 4 }}>
              {summary.n_with_arrival} with arrival price · {fmtINR(summary.total_traded_value)} traded
            </div>
          </div>
          <div style={card}>
            <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1.5, marginBottom: 6 }}>MEAN SLIPPAGE vs VWAP</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: slipColor(summary.mean_slip_vwap_bps) }}>
              {summary.mean_slip_vwap_bps != null ? `${summary.mean_slip_vwap_bps > 0 ? '+' : ''}${summary.mean_slip_vwap_bps} bps` : '-'}
            </div>
            <div style={{ color: '#64748B', fontSize: 10, marginTop: 4 }}>
              median {summary.median_slip_vwap_bps ?? '-'} bps · total cost {fmtINR(summary.total_cost_vwap_inr)}
            </div>
          </div>
          <div style={card}>
            <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1.5, marginBottom: 6 }}>BUY / SELL SPLIT (VWAP)</div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>
              <span style={{ color: slipColor(summary.buy_mean_vwap_bps) }}>{summary.buy_mean_vwap_bps ?? '-'}</span>
              <span style={{ color: '#334155', margin: '0 8px' }}>/</span>
              <span style={{ color: slipColor(summary.sell_mean_vwap_bps) }}>{summary.sell_mean_vwap_bps ?? '-'}</span>
            </div>
            <div style={{ color: '#64748B', fontSize: 10, marginTop: 4 }}>mean bps per side</div>
          </div>
          <div style={card}>
            <div style={{ color: '#64748B', fontSize: 10, letterSpacing: 1.5, marginBottom: 6 }}>WORST FILL</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: slipColor(summary.worst_fill_bps) }}>
              {summary.worst_fill_bps != null ? `+${summary.worst_fill_bps} bps` : '-'}
            </div>
            <div style={{ color: '#64748B', fontSize: 10, marginTop: 4 }}>order {summary.worst_fill_order_id || '-'}</div>
          </div>
        </div>
      )}

      {/* Fills table */}
      {fills.length > 0 && (
        <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 8, overflow: 'hidden', marginBottom: 24 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 820 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1E2332' }}>
                  <th style={th}>Date</th><th style={th}>Symbol</th><th style={th}>Side</th>
                  <th style={{ ...th, textAlign: 'right' }}>Qty</th>
                  <th style={{ ...th, textAlign: 'right' }}>Fill</th>
                  <th style={{ ...th, textAlign: 'right' }}>Arrival</th>
                  <th style={{ ...th, textAlign: 'right' }}>VWAP (HLC3)</th>
                  <th style={{ ...th, textAlign: 'right' }}>vs Arrival</th>
                  <th style={{ ...th, textAlign: 'right' }}>vs VWAP</th>
                  <th style={th}>Status</th>
                </tr>
              </thead>
              <tbody>
                {fills.map(f => (
                  <tr key={f.order_id} style={{ borderBottom: '1px solid #1E233230' }}>
                    <td style={{ ...td, color: '#64748B' }}>{f.fill_date}</td>
                    <td style={{ ...td, fontWeight: 700 }}>{f.symbol}</td>
                    <td style={{ ...td, color: f.action === 'BUY' ? '#22C55E' : '#EF4444', fontWeight: 600 }}>{f.action}</td>
                    <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>{f.filled_qty}</td>
                    <td style={{ ...td, textAlign: 'right' }}>{fmt(f.avg_fill_price)}</td>
                    <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>{f.arrival_price != null ? fmt(f.arrival_price) : '-'}</td>
                    <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>{f.vwap_hlc3 != null ? fmt(f.vwap_hlc3) : '-'}</td>
                    <td style={{ ...td, textAlign: 'right', color: slipColor(f.slip_arrival_bps), fontWeight: 600 }}>
                      {f.slip_arrival_bps != null ? `${f.slip_arrival_bps > 0 ? '+' : ''}${f.slip_arrival_bps}` : '-'}
                    </td>
                    <td style={{ ...td, textAlign: 'right', color: slipColor(f.slip_vwap_bps), fontWeight: 600 }}>
                      {f.slip_vwap_bps != null ? `${f.slip_vwap_bps > 0 ? '+' : ''}${f.slip_vwap_bps}` : '-'}
                    </td>
                    <td style={{ ...td, fontSize: 10, color: f.benchmark_status === 'OK' ? '#22C55E' : '#EAB308' }}>{f.benchmark_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Order slicer tool */}
      <div style={{ fontSize: 13, fontWeight: 700, color: '#94A3B8', letterSpacing: 1, marginBottom: 12 }}>
        ORDER SLICER — TWAP PLAN
        <span style={{ color: '#475569', fontWeight: 400, marginLeft: 10, fontSize: 11 }}>
          checks order size against 20-day ADV participation limit
        </span>
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap' }}>
        <input placeholder="SYMBOL" value={sliceSym} onChange={e => setSliceSym(e.target.value.toUpperCase())} style={{ ...inputSt, width: 130 }} />
        <input placeholder="Quantity" type="number" value={sliceQty} onChange={e => setSliceQty(e.target.value)} style={{ ...inputSt, width: 130 }} />
        <button onClick={fetchPlan} style={{
          padding: '7px 18px', borderRadius: 6, border: '1px solid #22C55E',
          background: 'transparent', color: '#22C55E', cursor: 'pointer', fontSize: 12, fontWeight: 600,
        }}>Build Plan</button>
        {planErr && <span style={{ color: '#EF4444', fontSize: 12 }}>{planErr}</span>}
      </div>

      {plan && (
        <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 8, padding: 16, maxWidth: 620 }}>
          <div style={{ display: 'flex', gap: 20, marginBottom: 10, fontSize: 12, flexWrap: 'wrap' }}>
            <span><span style={{ color: '#64748B' }}>20d ADV:</span> <b>{fmt(plan.adv_20d, 0)}</b></span>
            <span><span style={{ color: '#64748B' }}>Participation:</span>{' '}
              <b style={{ color: plan.exceeds ? '#EF4444' : '#22C55E' }}>{plan.participation_pct}%</b>
              <span style={{ color: '#475569' }}> (limit {plan.max_participation_pct}%)</span>
            </span>
          </div>
          <div style={{ color: plan.exceeds ? '#EAB308' : '#22C55E', fontSize: 12, marginBottom: plan.slices_needed ? 12 : 0 }}>
            {plan.note}
          </div>
          {plan.slices_needed && (
            <table style={{ borderCollapse: 'collapse', width: '100%' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1E2332' }}>
                  <th style={th}>Slice</th><th style={th}>Release (IST)</th>
                  <th style={{ ...th, textAlign: 'right' }}>Qty</th>
                  <th style={{ ...th, textAlign: 'right' }}>% of Order</th>
                </tr>
              </thead>
              <tbody>
                {plan.slices.map(s => (
                  <tr key={s.slice_no} style={{ borderBottom: '1px solid #1E233230' }}>
                    <td style={td}>#{s.slice_no}</td>
                    <td style={{ ...td, fontFamily: 'monospace' }}>{s.time_ist}</td>
                    <td style={{ ...td, textAlign: 'right' }}>{fmt(s.qty, 0)}</td>
                    <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>{s.pct_of_order}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export function ExecutionPage() {
  const [tab, setTab]     = useState<'signals' | 'queue' | 'blotter' | 'tca' | 'config'>('signals')
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [paperMode, setPaperMode] = useState(true)
  const [toast, setToast] = useState('')

  // Load paper mode state on mount
  useEffect(() => {
    fetch(`${API}/config`)
      .then(r => r.json())
      .then(d => setPaperMode(!!d.paper_mode))
      .catch(() => {})
  }, [])

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  const addToQueue = (rec: Recommendation) => {
    if (queue.find(q => q.symbol === rec.symbol)) return
    setQueue(prev => [...prev, { ...rec, qty: rec.suggested_qty, price: 0, order_type: 'MARKET' }])
  }

  const removeFromQueue = (symbol: string) => {
    setQueue(prev => prev.filter(q => q.symbol !== symbol))
  }

  const placeOne = async (item: QueueItem) => {
    const body = {
      symbol: item.symbol, sector: item.sector,
      action: item.action, qty: item.qty,
      price: 0, order_type: 'MARKET', exchange: 'NSE',
    }
    const r = await fetch(`${API}/order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const d = await r.json()
    if (r.ok) {
      removeFromQueue(item.symbol)
      showToast(d.message || `Order placed for ${item.symbol}`)
    } else {
      showToast(`Failed: ${d.detail || 'unknown error'}`)
    }
  }

  const placeAll = async () => {
    for (const item of [...queue]) {
      await placeOne(item)
    }
  }

  const TABS = [
    { key: 'signals', label: 'Signals' },
    { key: 'queue',   label: `Queue${queue.length > 0 ? ` (${queue.length})` : ''}` },
    { key: 'blotter', label: 'Blotter' },
    { key: 'tca',     label: 'TCA' },
    { key: 'config',  label: 'Risk Config' },
  ] as const

  return (
    <div style={{ color: '#E2E8F0' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 20 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Execution Platform</h1>
        <PaperBadge paper={paperMode} />
      </div>

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', top: 20, right: 20, zIndex: 9999,
          background: '#1E2332', border: '1px solid #2D3348',
          color: '#E2E8F0', padding: '10px 16px', borderRadius: 8, fontSize: 13,
          boxShadow: '0 4px 24px rgba(0,0,0,0.5)',
        }}>
          {toast}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid #1E2332', marginBottom: 20 }}>
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: '8px 20px', background: 'transparent', border: 'none',
              borderBottom: tab === t.key ? '2px solid #22C55E' : '2px solid transparent',
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
              color: tab === t.key ? '#22C55E' : '#64748B',
              marginBottom: -1,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'signals' && (
        <SignalsTab queue={queue} onQueue={addToQueue} paperMode={paperMode} />
      )}
      {tab === 'queue' && (
        <QueueTab
          queue={queue}
          onRemove={removeFromQueue}
          onPlace={placeOne}
          onPlaceAll={placeAll}
          paperMode={paperMode}
        />
      )}
      {tab === 'blotter' && <BlotterTab />}
      {tab === 'tca'     && <TcaTab />}
      {tab === 'config'  && <ConfigTab />}
    </div>
  )
}
