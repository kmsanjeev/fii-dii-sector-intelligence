import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API = 'http://localhost:8001'

// ── Types ─────────────────────────────────────────────────────────────────────

type BrokerStatus = {
  connected:           boolean
  broker:              string | null
  client_id:           string | null
  credentials_set_at:  string | null
  holdings_count:      number
  last_synced:         string | null
}

type HoldingRow = {
  symbol:           string
  exchange:         string
  isin:             string | null
  qty:              number
  avg_cost:         number
  ltp:              number
  current_value:    number
  pnl:              number
  pnl_pct:          number
  last_synced:      string | null
  label:            string | null
  bull_run_score:   number | null
  sector:           string | null
  ml_bull_run_score: number | null
  rotation_signal:  string | null
  key_signal:       string | null
}

type HoldingsResponse = {
  holdings:    HoldingRow[]
  total:       number
  last_synced: string | null
  message?:    string
}

// ── API ───────────────────────────────────────────────────────────────────────

const fetchStatus    = (): Promise<BrokerStatus>    => fetch(`${API}/api/broker/status`).then(r => r.json())
const fetchHoldings  = (): Promise<HoldingsResponse> => fetch(`${API}/api/broker/holdings`).then(r => r.json())

async function saveAuth(broker: string, client_id: string, access_token: string) {
  const r = await fetch(`${API}/api/broker/auth`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ broker, client_id, access_token }),
  })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Auth save failed')
  return r.json()
}

async function triggerSync() {
  const r = await fetch(`${API}/api/broker/sync`, { method: 'POST' })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Sync failed')
  return r.json()
}

async function triggerSyncTrades(from_date: string, to_date: string) {
  const r = await fetch(`${API}/api/broker/sync-trades`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from_date: from_date || null, to_date: to_date || null }),
  })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Trade sync failed')
  return r.json()
}

async function clearAuth() {
  const r = await fetch(`${API}/api/broker/auth`, { method: 'DELETE' })
  return r.json()
}

async function importCsv(holdingsFile?: File, tradesFile?: File) {
  const form = new FormData()
  if (holdingsFile) form.append('holdings_file', holdingsFile)
  if (tradesFile)   form.append('trades_file',   tradesFile)
  const r = await fetch(`${API}/api/broker/import-csv`, { method: 'POST', body: form })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Import failed')
  return r.json()
}

// ── Style constants ───────────────────────────────────────────────────────────

const inp: React.CSSProperties = {
  background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 4,
  color: '#E2E8F0', padding: '6px 10px', fontSize: 11, outline: 'none', width: '100%',
}
const th: React.CSSProperties = {
  padding: '6px 10px', textAlign: 'left', fontSize: 10, fontWeight: 600,
  color: '#64748B', whiteSpace: 'nowrap', borderBottom: '1px solid #1E2332',
}
const td: React.CSSProperties = { padding: '6px 10px', fontSize: 11 }

const LABEL_COLORS: Record<string, string> = {
  STRONG_CANDIDATE: '#22C55E', EMERGING: '#10B981',
  WATCHLIST: '#F59E0B', NEUTRAL: '#64748B', AVOID: '#EF4444',
}

const SIGNAL_COLORS: Record<string, string> = {
  'STRONG BUY':        '#22C55E',
  'MOMENTUM BUILDING': '#10B981',
  'ACCUMULATION':      '#3B82F6',
  'SECTOR ROTATING IN':'#8B5CF6',
  'WATCHLIST':         '#F59E0B',
  'HOLD':              '#64748B',
  'REVIEW POSITION':   '#EF4444',
  'CONSIDER STOP LOSS':'#DC2626',
}

// ── Small components ──────────────────────────────────────────────────────────

function LabelBadge({ label }: { label: string | null }) {
  if (!label) return <span style={{ color: '#334155' }}>--</span>
  const c = LABEL_COLORS[label] ?? '#64748B'
  return (
    <span style={{
      background: `${c}22`, color: c, border: `1px solid ${c}44`,
      borderRadius: 3, padding: '1px 6px', fontSize: 9, fontWeight: 700,
    }}>
      {label.replace('_', ' ')}
    </span>
  )
}

function SignalBadge({ signal }: { signal: string | null }) {
  if (!signal) return <span style={{ color: '#334155' }}>--</span>
  const c = SIGNAL_COLORS[signal] ?? '#64748B'
  return (
    <span style={{
      background: `${c}18`, color: c, border: `1px solid ${c}33`,
      borderRadius: 3, padding: '2px 8px', fontSize: 9, fontWeight: 700, whiteSpace: 'nowrap',
    }}>
      {signal}
    </span>
  )
}

function PnlCell({ pnl, pct }: { pnl: number; pct: number }) {
  const c    = pct >= 0 ? '#22C55E' : '#EF4444'
  const sign = pct >= 0 ? '+' : ''
  return (
    <div>
      <span style={{ color: c, fontWeight: 700 }}>{sign}{pct.toFixed(2)}%</span>
      <div style={{ color: '#475569', fontSize: 9 }}>{sign}{pnl.toFixed(0)}</div>
    </div>
  )
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span style={{
      display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
      background: ok ? '#22C55E' : '#EF4444', marginRight: 6,
    }} />
  )
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <div style={{ color: '#64748B', fontSize: 10, marginBottom: 4 }}>{children}</div>
}

function Btn({ onClick, children, disabled = false, color = '#22C55E' }: {
  onClick: () => void; children: React.ReactNode; disabled?: boolean; color?: string
}) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      padding: '7px 18px', borderRadius: 4, fontSize: 11, fontWeight: 700,
      border: `1px solid ${color}`, background: 'transparent',
      color: disabled ? '#334155' : color,
      cursor: disabled ? 'not-allowed' : 'pointer',
    }}>
      {children}
    </button>
  )
}

// ── Connection Panel ──────────────────────────────────────────────────────────

function ConnectionPanel({ status, onRefresh }: { status: BrokerStatus; onRefresh: () => void }) {
  const qc = useQueryClient()
  const [clientId,     setClientId]     = useState('')
  const [accessToken,  setAccessToken]  = useState('')
  const [showForm,     setShowForm]     = useState(!status.connected)
  const [msg,          setMsg]          = useState('')

  const authMut = useMutation({
    mutationFn: () => saveAuth('dhan', clientId, accessToken),
    onSuccess: (d) => {
      setMsg(d.valid ? 'Connected successfully.' : 'Saved -- but ping failed. Check credentials.')
      setShowForm(false)
      qc.invalidateQueries({ queryKey: ['broker-status'] })
    },
    onError: (e: Error) => setMsg(e.message),
  })

  const clearMut = useMutation({
    mutationFn: clearAuth,
    onSuccess: () => {
      setShowForm(true)
      setMsg('')
      qc.invalidateQueries({ queryKey: ['broker-status'] })
    },
  })

  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>
          BROKER CONNECTION
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <StatusDot ok={status.connected} />
          <span style={{ color: status.connected ? '#22C55E' : '#EF4444', fontSize: 11, fontWeight: 700 }}>
            {status.connected ? `DHAN -- ${status.client_id}` : 'NOT CONNECTED'}
          </span>
        </div>
      </div>

      {status.connected && (
        <div style={{ display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>HOLDINGS</div>
            <div style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700 }}>{status.holdings_count}</div>
          </div>
          <div>
            <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>LAST SYNCED</div>
            <div style={{ color: '#94A3B8', fontSize: 12 }}>{status.last_synced ?? 'Never'}</div>
          </div>
          <div>
            <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>CREDENTIALS SET</div>
            <div style={{ color: '#94A3B8', fontSize: 12 }}>
              {status.credentials_set_at ? status.credentials_set_at.slice(0, 16) : '--'}
            </div>
          </div>
        </div>
      )}

      {/* Credentials form */}
      {showForm && (
        <div>
          <div style={{ color: '#64748B', fontSize: 10, marginBottom: 14 }}>
            Enter your Dhan credentials. Client ID is your Dhan User ID.
            Access token: Dhan app > My Profile > Generate Access Token (valid 30 days).
            Credentials are stored locally in data/portfolio/broker_auth.json and never committed to git.
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
            <div style={{ flex: 1, minWidth: 160 }}>
              <FieldLabel>Client ID (Dhan User ID)</FieldLabel>
              <input value={clientId} onChange={e => setClientId(e.target.value)}
                placeholder="e.g. 1100123456" style={inp} />
            </div>
            <div style={{ flex: 2, minWidth: 240 }}>
              <FieldLabel>Access Token</FieldLabel>
              <input type="password" value={accessToken} onChange={e => setAccessToken(e.target.value)}
                placeholder="Paste Dhan access token" style={inp} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <Btn onClick={() => authMut.mutate()} disabled={!clientId || !accessToken || authMut.isPending}>
              {authMut.isPending ? 'Connecting...' : 'Connect'}
            </Btn>
            {status.connected && (
              <Btn onClick={() => setShowForm(false)} color="#64748B">Cancel</Btn>
            )}
          </div>
        </div>
      )}

      {/* Connected actions */}
      {!showForm && status.connected && (
        <div style={{ display: 'flex', gap: 10 }}>
          <Btn onClick={() => setShowForm(true)} color="#64748B">Update Token</Btn>
          <Btn onClick={() => clearMut.mutate()} color="#EF4444" disabled={clearMut.isPending}>
            Disconnect
          </Btn>
        </div>
      )}

      {msg && (
        <div style={{ color: msg.includes('success') || msg.includes('Connected') ? '#22C55E' : '#F59E0B',
          fontSize: 11, marginTop: 10 }}>{msg}</div>
      )}
    </div>
  )
}

// ── Sync Panel ────────────────────────────────────────────────────────────────

function SyncPanel({ connected, onSynced }: { connected: boolean; onSynced: () => void }) {
  const [fromDate, setFromDate] = useState('')
  const [toDate,   setToDate]   = useState('')
  const [msg,      setMsg]      = useState('')
  const holdingsRef = useRef<HTMLInputElement>(null)
  const tradesRef   = useRef<HTMLInputElement>(null)

  const syncMut = useMutation({
    mutationFn: triggerSync,
    onSuccess: d => { setMsg(`Synced ${d.holdings_count} holdings.`); onSynced() },
    onError:   e => setMsg((e as Error).message),
  })

  const tradesMut = useMutation({
    mutationFn: () => triggerSyncTrades(fromDate, toDate),
    onSuccess: d => {
      setMsg(`Synced ${d.holdings_count} holdings + ${d.trades_imported} trades imported.`)
      onSynced()
    },
    onError: e => setMsg((e as Error).message),
  })

  const csvMut = useMutation({
    mutationFn: () => importCsv(
      holdingsRef.current?.files?.[0],
      tradesRef.current?.files?.[0],
    ),
    onSuccess: d => {
      setMsg(`Imported ${d.holdings_count} holdings, ${d.trades_imported} trades.`)
      onSynced()
    },
    onError: e => setMsg((e as Error).message),
  })

  const busy = syncMut.isPending || tradesMut.isPending || csvMut.isPending

  return (
    <div style={{
      background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 20,
    }}>
      <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 16 }}>
        SYNC
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        {/* Live sync */}
        <div>
          <div style={{ color: '#64748B', fontSize: 10, marginBottom: 6 }}>
            Live sync via Dhan API
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Btn onClick={() => syncMut.mutate()} disabled={!connected || busy}>
              {syncMut.isPending ? 'Syncing...' : 'Sync Holdings'}
            </Btn>
          </div>
        </div>

        {/* Sync + import trades */}
        <div>
          <div style={{ color: '#64748B', fontSize: 10, marginBottom: 6 }}>
            Holdings + import trade history to Portfolio
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <div>
              <FieldLabel>From</FieldLabel>
              <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)}
                style={{ ...inp, width: 140, colorScheme: 'dark' }} />
            </div>
            <div>
              <FieldLabel>To</FieldLabel>
              <input type="date" value={toDate} onChange={e => setToDate(e.target.value)}
                style={{ ...inp, width: 140, colorScheme: 'dark' }} />
            </div>
            <div style={{ paddingTop: 16 }}>
              <Btn onClick={() => tradesMut.mutate()} disabled={!connected || busy} color="#8B5CF6">
                {tradesMut.isPending ? 'Importing...' : 'Sync + Import Trades'}
              </Btn>
            </div>
          </div>
        </div>

        {/* CSV import */}
        <div>
          <div style={{ color: '#64748B', fontSize: 10, marginBottom: 6 }}>
            No API? Upload broker CSV export
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <FieldLabel>Holdings CSV</FieldLabel>
              <input ref={holdingsRef} type="file" accept=".csv" style={{ ...inp, width: 180, color: '#64748B' }} />
            </div>
            <div>
              <FieldLabel>Trades CSV (optional)</FieldLabel>
              <input ref={tradesRef} type="file" accept=".csv" style={{ ...inp, width: 180, color: '#64748B' }} />
            </div>
            <div style={{ paddingTop: 16 }}>
              <Btn onClick={() => csvMut.mutate()} disabled={busy} color="#F59E0B">
                {csvMut.isPending ? 'Importing...' : 'Import CSV'}
              </Btn>
            </div>
          </div>
        </div>
      </div>

      {msg && (
        <div style={{ color: '#22C55E', fontSize: 11, marginTop: 12 }}>{msg}</div>
      )}
    </div>
  )
}

// ── Holdings Table ─────────────────────────────────────────────────────────────

function HoldingsTable({ data }: { data: HoldingsResponse }) {
  if (data.message && !data.holdings.length) {
    return (
      <div style={{
        background: '#141720', border: '1px solid #1E2332', borderRadius: 6,
        padding: 48, textAlign: 'center', color: '#334155', fontSize: 12,
      }}>
        {data.message}
      </div>
    )
  }

  const totalValue = data.holdings.reduce((s, h) => s + (h.current_value ?? 0), 0)
  const totalPnl   = data.holdings.reduce((s, h) => s + (h.pnl ?? 0), 0)
  const totalCost  = totalValue - totalPnl
  const totalPct   = totalCost > 0 ? totalPnl / totalCost * 100 : 0
  const pnlC       = totalPnl >= 0 ? '#22C55E' : '#EF4444'

  return (
    <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16 }}>
      {/* Summary bar */}
      <div style={{ display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap' }}>
        <div>
          <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>HOLDINGS</div>
          <div style={{ color: '#E2E8F0', fontSize: 18, fontWeight: 700 }}>{data.total}</div>
        </div>
        <div>
          <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>CURRENT VALUE</div>
          <div style={{ color: '#E2E8F0', fontSize: 18, fontWeight: 700 }}>
            {totalValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div>
          <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>TOTAL P&L</div>
          <div style={{ color: pnlC, fontSize: 18, fontWeight: 700 }}>
            {totalPnl >= 0 ? '+' : ''}{totalPnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            <span style={{ fontSize: 11, marginLeft: 6 }}>
              ({totalPnl >= 0 ? '+' : ''}{totalPct.toFixed(2)}%)
            </span>
          </div>
        </div>
        <div>
          <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>LAST SYNCED</div>
          <div style={{ color: '#64748B', fontSize: 11 }}>{data.last_synced ?? '--'}</div>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 1000 }}>
          <thead>
            <tr>
              <th style={th}>Symbol</th>
              <th style={{ ...th, textAlign: 'right' }}>Qty</th>
              <th style={{ ...th, textAlign: 'right' }}>Avg Cost</th>
              <th style={{ ...th, textAlign: 'right' }}>LTP</th>
              <th style={{ ...th, textAlign: 'right' }}>Value</th>
              <th style={{ ...th, textAlign: 'right' }}>P&L</th>
              <th style={th}>Label</th>
              <th style={{ ...th, textAlign: 'right' }}>Score</th>
              <th style={th}>Sector</th>
              <th style={th}>Signal</th>
            </tr>
          </thead>
          <tbody>
            {data.holdings.map((h, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #1E233210' }}>
                <td style={{ ...td, fontWeight: 700 }}>
                  <a href={`/stocks/${h.symbol}`}
                    style={{ color: '#E2E8F0', textDecoration: 'none' }}
                    onMouseOver={e => (e.currentTarget.style.color = '#22C55E')}
                    onMouseOut={e  => (e.currentTarget.style.color = '#E2E8F0')}
                  >
                    {h.symbol}
                  </a>
                  {h.exchange && h.exchange !== 'NSE' && (
                    <span style={{ color: '#475569', fontSize: 9, marginLeft: 5 }}>{h.exchange}</span>
                  )}
                </td>
                <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>{h.qty}</td>
                <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>
                  {h.avg_cost?.toFixed(2) ?? '--'}
                </td>
                <td style={{ ...td, textAlign: 'right', color: '#E2E8F0' }}>
                  {h.ltp?.toFixed(2) ?? '--'}
                </td>
                <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>
                  {h.current_value?.toLocaleString('en-IN', { maximumFractionDigits: 0 }) ?? '--'}
                </td>
                <td style={{ ...td, textAlign: 'right' }}>
                  <PnlCell pnl={h.pnl ?? 0} pct={h.pnl_pct ?? 0} />
                </td>
                <td style={td}><LabelBadge label={h.label} /></td>
                <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                  {h.bull_run_score?.toFixed(0) ?? '--'}
                </td>
                <td style={{ ...td, color: '#475569', fontSize: 10 }}>{h.sector ?? '--'}</td>
                <td style={td}><SignalBadge signal={h.key_signal} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export function BrokerPage() {
  const qc = useQueryClient()

  const { data: status } = useQuery<BrokerStatus>({
    queryKey:      ['broker-status'],
    queryFn:       fetchStatus,
    refetchInterval: 30_000,
  })

  const { data: holdings, refetch: refetchHoldings } = useQuery<HoldingsResponse>({
    queryKey: ['broker-holdings'],
    queryFn:  fetchHoldings,
    enabled:  !!status?.holdings_count,
  })

  const onSynced = () => {
    qc.invalidateQueries({ queryKey: ['broker-status'] })
    refetchHoldings()
  }

  if (!status) return (
    <div style={{ color: '#64748B', padding: 40, textAlign: 'center' }}>Loading...</div>
  )

  return (
    <div style={{ maxWidth: 1320, display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
          BROKER
        </h1>
        <span style={{ color: '#475569', fontSize: 10 }}>
          Phase 22 -- Dhan read-only adapter. No orders are ever placed.
        </span>
      </div>

      <ConnectionPanel status={status} onRefresh={() => qc.invalidateQueries({ queryKey: ['broker-status'] })} />
      <SyncPanel connected={status.connected} onSynced={onSynced} />

      {holdings && <HoldingsTable data={holdings} />}

      {!holdings && status.connected && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332', borderRadius: 6,
          padding: 48, textAlign: 'center', color: '#334155', fontSize: 12,
        }}>
          Click "Sync Holdings" to pull your current portfolio from Dhan.
        </div>
      )}
    </div>
  )
}
