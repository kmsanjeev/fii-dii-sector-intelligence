import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchHealth } from '../api/client'

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

// ── API ───────────────────────────────────────────────────────────────────────

const fetchBrokerStatus = (): Promise<BrokerStatus> =>
  fetch(`${API}/api/broker/status`).then(r => r.json())

async function saveAuth(broker: string, client_id: string, access_token: string) {
  const r = await fetch(`${API}/api/broker/auth`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ broker, client_id, access_token }),
  })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Auth save failed')
  return r.json()
}

async function clearAuth() {
  const r = await fetch(`${API}/api/broker/auth`, { method: 'DELETE' })
  return r.json()
}

// ── Shared style constants ────────────────────────────────────────────────────

const CARD: React.CSSProperties = {
  background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 20,
}
const inp: React.CSSProperties = {
  background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 4,
  color: '#E2E8F0', padding: '6px 10px', fontSize: 11, outline: 'none', width: '100%',
}

function Row({ label, value, valueColor }: { label: string; value: React.ReactNode; valueColor?: string }) {
  return (
    <div className="flex justify-between items-center">
      <span style={{ color: '#64748B', fontSize: 12 }}>{label}</span>
      <span style={{ color: valueColor ?? '#94A3B8', fontSize: 12 }}>{value}</span>
    </div>
  )
}

function SectionHead({ title }: { title: string }) {
  return (
    <h2 style={{ color: '#64748B', fontSize: 10, letterSpacing: 2, margin: '0 0 12px 0' }}>{title}</h2>
  )
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span style={{
      display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
      background: ok ? '#22C55E' : '#475569', marginRight: 6, flexShrink: 0,
    }} />
  )
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <div style={{ color: '#64748B', fontSize: 10, marginBottom: 4 }}>{children}</div>
}

function Btn({ onClick, children, disabled = false, color = '#22C55E' }: {
  onClick?: () => void; children: React.ReactNode; disabled?: boolean; color?: string
}) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      padding: '6px 16px', borderRadius: 4, fontSize: 11, fontWeight: 700,
      border: `1px solid ${color}`, background: 'transparent',
      color: disabled ? '#334155' : color,
      cursor: disabled ? 'not-allowed' : 'pointer',
      borderColor: disabled ? '#334155' : color,
    }}>
      {children}
    </button>
  )
}

// ── Dhan connection form ──────────────────────────────────────────────────────

function DhanForm({ status }: { status: BrokerStatus }) {
  const qc = useQueryClient()
  const [clientId,    setClientId]    = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [showForm,    setShowForm]    = useState(!status.connected)
  const [msg,         setMsg]         = useState('')

  const authMut = useMutation({
    mutationFn: () => saveAuth('dhan', clientId, accessToken),
    onSuccess: d => {
      setMsg(d.valid ? 'Connected successfully.' : 'Saved -- Dhan ping failed. Check credentials.')
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
    <div>
      {status.connected && (
        <div style={{ display: 'flex', gap: 20, marginBottom: 14, flexWrap: 'wrap' }}>
          <div>
            <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>CLIENT ID</div>
            <div style={{ color: '#E2E8F0', fontSize: 12, fontWeight: 600, marginTop: 2 }}>{status.client_id}</div>
          </div>
          <div>
            <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>HOLDINGS</div>
            <div style={{ color: '#E2E8F0', fontSize: 12, fontWeight: 600, marginTop: 2 }}>{status.holdings_count}</div>
          </div>
          <div>
            <div style={{ color: '#64748B', fontSize: 9, letterSpacing: 1 }}>CREDENTIALS SET</div>
            <div style={{ color: '#94A3B8', fontSize: 12, marginTop: 2 }}>
              {status.credentials_set_at?.slice(0, 16) ?? '--'}
            </div>
          </div>
        </div>
      )}

      {showForm && (
        <div>
          <div style={{ color: '#64748B', fontSize: 10, marginBottom: 12 }}>
            Client ID = Dhan User ID. Access token: Dhan app &gt; My Profile &gt; Generate Access Token
            (valid 30 days). Credentials are stored locally in data/portfolio/broker_auth.json.
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
            <div style={{ flex: 1, minWidth: 140 }}>
              <FieldLabel>Client ID (Dhan User ID)</FieldLabel>
              <input value={clientId} onChange={e => setClientId(e.target.value)}
                placeholder="e.g. 1100123456" style={inp} />
            </div>
            <div style={{ flex: 2, minWidth: 220 }}>
              <FieldLabel>Access Token</FieldLabel>
              <input type="password" value={accessToken} onChange={e => setAccessToken(e.target.value)}
                placeholder="Paste Dhan access token" style={inp} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Btn onClick={() => authMut.mutate()} disabled={!clientId || !accessToken || authMut.isPending}>
              {authMut.isPending ? 'Connecting...' : 'Connect Dhan'}
            </Btn>
            {status.connected && (
              <Btn onClick={() => setShowForm(false)} color="#64748B">Cancel</Btn>
            )}
          </div>
        </div>
      )}

      {!showForm && status.connected && (
        <div style={{ display: 'flex', gap: 8 }}>
          <Btn onClick={() => setShowForm(true)} color="#64748B">Update Token</Btn>
          <Btn onClick={() => clearMut.mutate()} color="#EF4444" disabled={clearMut.isPending}>
            Disconnect
          </Btn>
        </div>
      )}

      {msg && (
        <div style={{
          color: msg.toLowerCase().includes('success') || msg.toLowerCase().includes('connected') ? '#22C55E' : '#F59E0B',
          fontSize: 11, marginTop: 10,
        }}>
          {msg}
        </div>
      )}
    </div>
  )
}

// ── Broker Card ───────────────────────────────────────────────────────────────

function BrokerCard({
  name, logo, status, children, comingSoon = false,
}: {
  name: string
  logo: string
  status?: 'CONNECTED' | 'DISCONNECTED'
  children?: React.ReactNode
  comingSoon?: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const isConnected = status === 'CONNECTED'

  return (
    <div style={{
      background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 6, overflow: 'hidden',
      borderColor: isConnected ? '#22C55E44' : '#1E2332',
    }}>
      {/* Header row */}
      <div
        style={{
          display: 'flex', alignItems: 'center', padding: '12px 16px', gap: 12,
          cursor: comingSoon ? 'default' : 'pointer',
        }}
        onClick={() => !comingSoon && setExpanded(v => !v)}
      >
        <span style={{ fontSize: 20, width: 28, textAlign: 'center' }}>{logo}</span>
        <div style={{ flex: 1 }}>
          <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 13 }}>{name}</div>
          {comingSoon && (
            <div style={{ color: '#475569', fontSize: 10, marginTop: 1 }}>Coming soon</div>
          )}
        </div>
        {!comingSoon && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <StatusDot ok={isConnected} />
            <span style={{ color: isConnected ? '#22C55E' : '#475569', fontSize: 11, fontWeight: 700 }}>
              {status}
            </span>
          </div>
        )}
        {!comingSoon && (
          <span style={{ color: '#475569', fontSize: 14 }}>{expanded ? '-' : '+'}</span>
        )}
      </div>

      {/* Expanded body */}
      {expanded && !comingSoon && children && (
        <div style={{ padding: '0 16px 16px 16px', borderTop: '1px solid #1E2332' }}>
          <div style={{ height: 14 }} />
          {children}
        </div>
      )}
    </div>
  )
}

// ── CSV-only note ─────────────────────────────────────────────────────────────

function CsvNote() {
  return (
    <div style={{ color: '#64748B', fontSize: 11 }}>
      No broker API? Upload holdings and trades CSV files from any broker export on the
      &nbsp;<a href="/broker" style={{ color: '#3B82F6' }}>Broker page</a>.
      Compatible formats: Dhan, Zerodha, HDFC Securities, ICICI Direct, Angel Broking.
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export function SettingsPage() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'], queryFn: fetchHealth, refetchInterval: 60000,
  })
  const { data: brokerStatus } = useQuery<BrokerStatus>({
    queryKey: ['broker-status'], queryFn: fetchBrokerStatus, refetchInterval: 30000,
  })

  return (
    <div style={{ maxWidth: 720, display: 'flex', flexDirection: 'column', gap: 28 }}>
      <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
        SETTINGS
      </h1>

      {/* ── Broker Connections ────────────────────────────────────────────── */}
      <section>
        <SectionHead title="BROKER CONNECTIONS" />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>

          {/* Dhan */}
          <BrokerCard
            name="Dhan"
            logo="D"
            status={brokerStatus?.connected && brokerStatus?.broker === 'dhan' ? 'CONNECTED' : 'DISCONNECTED'}
          >
            {brokerStatus && <DhanForm status={brokerStatus} />}
          </BrokerCard>

          {/* Zerodha — coming soon */}
          <BrokerCard name="Zerodha / Kite" logo="Z" comingSoon />

          {/* Groww — coming soon */}
          <BrokerCard name="Groww / Angel One" logo="G" comingSoon />

          {/* CSV import */}
          <div style={{ ...CARD, padding: '12px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: 18 }}>F</span>
              <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 13 }}>CSV / File Import</div>
              <div style={{ marginLeft: 'auto' }}>
                <span style={{ color: '#22C55E', fontSize: 11, fontWeight: 700 }}>ALWAYS ON</span>
              </div>
            </div>
            <CsvNote />
          </div>
        </div>
      </section>

      {/* ── Data Freshness ───────────────────────────────────────────────── */}
      <section>
        <SectionHead title="DATA FRESHNESS" />
        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {isLoading ? (
            <div style={{ color: '#64748B', fontSize: 12 }}>Loading...</div>
          ) : (
            <>
              <Row label="API Status"       value="ONLINE" valueColor="#22C55E" />
              <Row
                label="Datasets Loaded"
                value={`${(health as Record<string, number>)?.datasets_loaded ?? 0} / ${(health as Record<string, number>)?.datasets_total ?? 11}`}
              />
            </>
          )}
        </div>
      </section>

      {/* ── Alert Configuration ───────────────────────────────────────────── */}
      <section>
        <SectionHead title="ALERT CONFIGURATION" />
        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Row label="Telegram Alerts" value="Configure via .env (TELEGRAM_BOT_TOKEN)" />
          <Row label="Daily Digest"    value="18:30 IST (run alert_scheduler.py)" />
          <Row label="Alert Checks"    value="Every 30 min post-market" />
          <Row label="Active Types"    value="10 alert types (P1-P10)" />
        </div>
      </section>

      {/* ── Platform ─────────────────────────────────────────────────────── */}
      <section>
        <SectionHead title="PLATFORM" />
        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Row label="Backend API"    value="http://localhost:8001 (uvicorn)" />
          <Row label="API Docs"       value={<a href="http://localhost:8001/docs" target="_blank" rel="noreferrer" style={{ color: '#3B82F6' }}>http://localhost:8001/docs</a>} />
          <Row label="Intelligence"   value="data/intelligence/ (30+ CSVs)" />
          <Row label="Auth"           value="Disabled by default (enable via Admin page)" />
        </div>
      </section>

      {/* ── AI Configuration ─────────────────────────────────────────────── */}
      <section>
        <SectionHead title="AI CONFIGURATION" />
        <div style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Row label="Chat LLM"         value="Groq llama-3.3-70b-versatile" />
          <Row label="Daily Token Limit" value="100,000 tokens / day (free tier)" />
          <Row label="RAG Indexes"       value="6 domain indexes (FAISS + BM25)" />
          <Row label="Sentiment Engine"  value="Anthropic API (management_sentiment.csv)" />
        </div>
      </section>
    </div>
  )
}
