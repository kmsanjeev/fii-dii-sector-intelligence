import { useState, useEffect, useCallback } from 'react'
import { ResearchAdminConsole } from '../components/admin/ResearchAdminConsole'
import { EmpiricalCaseIntake } from '../components/admin/EmpiricalCaseIntake'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchVedaConfiguration, resetVedaConfiguration, updateVedaCapabilityAccess, type CapabilityAccessState } from '../api/client'

const API = '/api/auth'

// ── Types ─────────────────────────────────────────────────────────────────────

interface AuthUser { id: string; email: string; role: string; active: boolean; created_at: string }
interface ApiKey   { id: string; name: string; key_prefix: string; created_at: string; last_used_at: string | null }

// ── Users Tab ─────────────────────────────────────────────────────────────────

function UsersTab({ currentUser }: { currentUser: AuthUser | null }) {
  const [users, setUsers]         = useState<AuthUser[]>([])
  const [loading, setLoading]     = useState(true)
  const [creating, setCreating]   = useState(false)
  const [newEmail, setNewEmail]   = useState('')
  const [newPw, setNewPw]         = useState('')
  const [newRole, setNewRole]     = useState('analyst')
  const [msg, setMsg]             = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API}/users`)
      const d = await r.json()
      setUsers(d.users || [])
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const createUser = async () => {
    setMsg('')
    if (!newEmail || !newPw) { setMsg('Email and password required'); return }
    setCreating(true)
    try {
      const r = await fetch(`${API}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newEmail, password: newPw, role: newRole }),
      })
      const d = await r.json()
      if (!r.ok) { setMsg(d.detail || 'Error'); return }
      setNewEmail(''); setNewPw(''); setNewRole('analyst')
      setMsg(`User ${d.email} created.`)
      await load()
    } finally { setCreating(false) }
  }

  const toggleActive = async (u: AuthUser) => {
    await fetch(`${API}/users/${u.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !u.active }),
    })
    await load()
  }

  const changeRole = async (u: AuthUser, role: string) => {
    await fetch(`${API}/users/${u.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    })
    await load()
  }

  const inputStyle = {
    background: '#1E2332', border: '1px solid #2D3348',
    color: '#E2E8F0', padding: '7px 10px', borderRadius: 6, fontSize: 13,
  }

  return (
    <div>
      {/* Create user form */}
      <div style={{ padding: 16, borderRadius: 8, background: '#141720', border: '1px solid #1E2332', marginBottom: 20 }}>
        <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12, color: '#94A3B8' }}>CREATE USER</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <input placeholder="Email" value={newEmail} onChange={e => setNewEmail(e.target.value)}
            style={{ ...inputStyle, width: 200 }} />
          <input placeholder="Password (min 12, upper/lower/digit)" type="password" value={newPw} onChange={e => setNewPw(e.target.value)}
            style={{ ...inputStyle, width: 180 }} />
          <select value={newRole} onChange={e => setNewRole(e.target.value)} style={{ ...inputStyle }}>
            <option value="analyst">analyst</option>
            <option value="trader">trader</option>
            <option value="admin">admin</option>
          </select>
          <button onClick={createUser} disabled={creating}
            style={{ padding: '7px 18px', background: '#22C55E', color: '#000', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}>
            {creating ? '...' : 'Create'}
          </button>
        </div>
        {msg && <div style={{ marginTop: 10, fontSize: 13, color: msg.includes('Error') || msg.includes('required') ? '#EF4444' : '#22C55E' }}>{msg}</div>}
      </div>

      {/* Users list */}
      {loading ? <div style={{ color: '#64748B', fontSize: 13 }}>Loading...</div> : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ color: '#64748B', borderBottom: '1px solid #1E2332' }}>
              {['Email', 'Role', 'Status', 'Created', 'Actions'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontSize: 11, fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid #1A1D2E', opacity: u.active ? 1 : 0.5 }}>
                <td style={{ padding: '9px 10px', color: '#E2E8F0' }}>
                  {u.email}
                  {currentUser?.id === u.id && <span style={{ fontSize: 10, color: '#22C55E', marginLeft: 6 }}>(you)</span>}
                </td>
                <td style={{ padding: '9px 10px' }}>
                  <select value={u.role} onChange={e => changeRole(u, e.target.value)}
                    disabled={currentUser?.id === u.id}
                    style={{ background: 'transparent', border: 'none', color: '#E2E8F0', fontSize: 12, cursor: 'pointer' }}>
                    <option value="analyst">analyst</option>
                    <option value="trader">trader</option>
                    <option value="admin">admin</option>
                  </select>
                </td>
                <td style={{ padding: '9px 10px' }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: u.active ? '#22C55E' : '#64748B' }}>
                    {u.active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </td>
                <td style={{ padding: '9px 10px', color: '#64748B', fontSize: 12 }}>
                  {new Date(u.created_at).toLocaleDateString('en-IN')}
                </td>
                <td style={{ padding: '9px 10px' }}>
                  {currentUser?.id !== u.id && (
                    <button onClick={() => toggleActive(u)}
                      style={{
                        padding: '3px 10px', borderRadius: 4, border: `1px solid ${u.active ? '#EF4444' : '#22C55E'}`,
                        background: 'transparent', color: u.active ? '#EF4444' : '#22C55E',
                        cursor: 'pointer', fontSize: 11,
                      }}>
                      {u.active ? 'Deactivate' : 'Activate'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ── API Keys Tab ──────────────────────────────────────────────────────────────

function ApiKeysTab() {
  const [keys, setKeys]       = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [newKey, setNewKey]   = useState('')
  const [msg, setMsg]         = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API}/api-keys`)
      const d = await r.json()
      setKeys(d.keys || [])
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const create = async () => {
    if (!newName.trim()) { setMsg('Key name required'); return }
    setCreating(true); setMsg(''); setNewKey('')
    try {
      const r = await fetch(`${API}/api-keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName.trim() }),
      })
      const d = await r.json()
      if (!r.ok) { setMsg(d.detail || 'Error'); return }
      setNewKey(d.key)
      setNewName('')
      await load()
    } finally { setCreating(false) }
  }

  const revoke = async (keyId: string) => {
    await fetch(`${API}/api-keys/${keyId}`, { method: 'DELETE' })
    await load()
  }

  return (
    <div>
      <div style={{ padding: 16, borderRadius: 8, background: '#141720', border: '1px solid #1E2332', marginBottom: 20 }}>
        <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12, color: '#94A3B8' }}>GENERATE API KEY</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input placeholder="Key name (e.g. my-script)" value={newName} onChange={e => setNewName(e.target.value)}
            style={{ background: '#1E2332', border: '1px solid #2D3348', color: '#E2E8F0', padding: '7px 10px', borderRadius: 6, fontSize: 13, width: 240 }} />
          <button onClick={create} disabled={creating}
            style={{ padding: '7px 18px', background: '#22C55E', color: '#000', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}>
            {creating ? '...' : 'Generate'}
          </button>
        </div>
        {msg && <div style={{ marginTop: 10, fontSize: 13, color: '#EF4444' }}>{msg}</div>}
        {newKey && (
          <div style={{ marginTop: 12, padding: 12, borderRadius: 6, background: '#0F2010', border: '1px solid #22C55E' }}>
            <div style={{ fontSize: 12, color: '#22C55E', fontWeight: 700, marginBottom: 6 }}>
              Key generated -- copy it now, it will not be shown again:
            </div>
            <code style={{ fontSize: 12, color: '#E2E8F0', wordBreak: 'break-all', fontFamily: 'monospace' }}>{newKey}</code>
          </div>
        )}
      </div>

      {loading ? <div style={{ color: '#64748B', fontSize: 13 }}>Loading...</div> : keys.length === 0 ? (
        <div style={{ color: '#64748B', fontSize: 13 }}>No API keys yet.</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ color: '#64748B', borderBottom: '1px solid #1E2332' }}>
              {['Name', 'Prefix', 'Created', 'Last Used', ''].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '6px 10px', fontSize: 11, fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {keys.map(k => (
              <tr key={k.id} style={{ borderBottom: '1px solid #1A1D2E' }}>
                <td style={{ padding: '9px 10px', color: '#E2E8F0' }}>{k.name}</td>
                <td style={{ padding: '9px 10px', fontFamily: 'monospace', color: '#60A5FA', fontSize: 12 }}>{k.key_prefix}...</td>
                <td style={{ padding: '9px 10px', color: '#64748B', fontSize: 12 }}>{new Date(k.created_at).toLocaleDateString('en-IN')}</td>
                <td style={{ padding: '9px 10px', color: '#64748B', fontSize: 12 }}>{k.last_used_at ? new Date(k.last_used_at).toLocaleDateString('en-IN') : 'Never'}</td>
                <td style={{ padding: '9px 10px' }}>
                  <button onClick={() => revoke(k.id)}
                    style={{ padding: '3px 10px', borderRadius: 4, border: '1px solid #EF4444', background: 'transparent', color: '#EF4444', cursor: 'pointer', fontSize: 11 }}>
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ── Auth Config Tab ───────────────────────────────────────────────────────────

function AuthConfigTab() {
  const [cfg, setCfg]         = useState({ enabled: false, token_expiry_days: 7 })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [msg, setMsg]         = useState('')

  useEffect(() => {
    fetch(`${API}/config`)
      .then(r => r.json())
      .then(d => { setCfg(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const save = async () => {
    setSaving(true); setMsg('')
    try {
      const r = await fetch(`${API}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg),
      })
      const d = await r.json()
      if (!r.ok) { setMsg(d.detail || 'Error'); return }
      setCfg(d); setMsg('Saved.')
    } finally { setSaving(false) }
  }

  const inputStyle = {
    background: '#1E2332', border: '1px solid #2D3348',
    color: '#E2E8F0', padding: '7px 10px', borderRadius: 6, fontSize: 13, width: 80,
  }

  if (loading) return <div style={{ color: '#64748B', fontSize: 13 }}>Loading...</div>

  return (
    <div style={{ maxWidth: 480 }}>
      <div style={{
        padding: 16, borderRadius: 8, marginBottom: 24,
        border: `2px solid ${cfg.enabled ? '#22C55E' : '#1E2332'}`,
        background: cfg.enabled ? '#0F2010' : '#141720',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, color: cfg.enabled ? '#22C55E' : '#64748B' }}>
              {cfg.enabled ? 'Authentication ENABLED' : 'Authentication DISABLED'}
            </div>
            <div style={{ fontSize: 12, color: '#64748B', marginTop: 4 }}>
              {cfg.enabled
                ? 'All API endpoints require a valid session token.'
                : 'Platform is open for loopback-only local/dev use. Production requires explicit auth.'}
            </div>
          </div>
          <button
            onClick={() => setCfg(c => ({ ...c, enabled: !c.enabled }))}
            style={{
              padding: '8px 20px', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13,
              background: cfg.enabled ? '#1E2332' : '#22C55E',
              color: cfg.enabled ? '#EF4444' : '#000',
            }}>
            {cfg.enabled ? 'Disable' : 'Enable'}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
        <div style={{ width: 200, color: '#94A3B8', fontSize: 13 }}>Session expiry (days)</div>
        <input type="number" style={inputStyle} value={cfg.token_expiry_days}
          onChange={e => setCfg(c => ({ ...c, token_expiry_days: parseInt(e.target.value) || 7 }))} />
      </div>

      <button onClick={save} disabled={saving}
        style={{ padding: '8px 24px', background: '#22C55E', color: '#000', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}>
        {saving ? 'Saving...' : 'Save'}
      </button>
      {msg && <span style={{ marginLeft: 12, fontSize: 13, color: '#22C55E' }}>{msg}</span>}

      <div style={{ marginTop: 28, padding: 12, borderRadius: 6, background: '#1A1D2E', fontSize: 12, color: '#64748B' }}>
        <strong style={{ color: '#94A3B8' }}>Note:</strong> Auth-disabled mode is intended only for trusted
        local/dev use. Non-loopback requests are rejected when auth is off.
      </div>
    </div>
  )
}

function VedaConfigurationTab() {
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['veda-configuration'],
    queryFn: fetchVedaConfiguration,
  })
  const update = useMutation({
    mutationFn: ({ id, state }: { id: string; state: CapabilityAccessState['admin_access_state'] }) => updateVedaCapabilityAccess(id, state),
    onSuccess: next => queryClient.setQueryData(['veda-configuration'], next),
  })
  const reset = useMutation({
    mutationFn: resetVedaConfiguration,
    onSuccess: next => queryClient.setQueryData(['veda-configuration'], next),
  })

  if (isLoading) return <div style={{ color: '#64748B', fontSize: 13 }}>Loading Veda configuration...</div>
  if (error || !data) return <div style={{ color: '#EF4444', fontSize: 13 }}>Veda configuration is unavailable. Admin authentication may be required.</div>

  const stateColor = (state: string) => state === 'ENABLED' ? '#22C55E' : state === 'DISABLED' ? '#EF4444' : '#F59E0B'
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#E2E8F0' }}>Veda conversational access</div>
          <div style={{ color: '#64748B', fontSize: 12, marginTop: 4 }}>Policy {data.policy_version}. Access is configurable; maturity and safety are not.</div>
        </div>
        <button onClick={() => reset.mutate()} disabled={reset.isPending}
          style={{ padding: '7px 14px', borderRadius: 5, border: '1px solid #22C55E', background: 'transparent', color: '#22C55E', cursor: 'pointer', fontSize: 12 }}>
          {reset.isPending ? 'Resetting...' : 'Enable all available'}
        </button>
      </div>
      <div style={{ display: 'grid', gap: 10 }}>
        {data.capabilities.map(cap => (
          <div key={cap.capability_id} style={{ padding: 14, borderRadius: 7, background: '#141720', border: '1px solid #1E2332', display: 'grid', gridTemplateColumns: 'minmax(180px, 1.4fr) repeat(4, minmax(100px, 1fr))', gap: 12, alignItems: 'center' }}>
            <div>
              <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 13 }}>{cap.label}</div>
              <div style={{ color: '#64748B', fontSize: 11, marginTop: 3 }}>{cap.description}</div>
            </div>
            <label style={{ color: '#94A3B8', fontSize: 11 }}>Access
              <select value={cap.admin_access_state} disabled={Boolean(cap.protected) || update.isPending}
                onChange={e => update.mutate({ id: cap.capability_id, state: e.target.value as CapabilityAccessState['admin_access_state'] })}
                style={{ display: 'block', marginTop: 4, background: '#1E2332', border: '1px solid #2D3348', color: stateColor(cap.admin_access_state), padding: '4px 6px', borderRadius: 4, fontSize: 11 }}>
                <option value="ENABLED">ON</option><option value="DISABLED">OFF</option><option value="ADMIN_ONLY">ADMIN</option>
              </select>
            </label>
            <div style={{ color: cap.runtime_available ? '#22C55E' : '#F59E0B', fontSize: 11 }}>Runtime<br /><strong>{cap.runtime_available ? 'AVAILABLE' : 'UNAVAILABLE'}</strong></div>
            <div style={{ color: '#94A3B8', fontSize: 11 }}>Maturity<br /><strong>{cap.capability_maturity}</strong></div>
            <div style={{ color: stateColor(cap.effective_access), fontSize: 11 }}>Effective<br /><strong>{cap.effective_access} / {cap.effective_answer_mode}</strong></div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 18, padding: 12, borderRadius: 6, background: '#1A1D2E', color: '#94A3B8', fontSize: 12 }}>
        <strong style={{ color: '#22C55E' }}>Protected safeguards: ACTIVE</strong> — safety, privacy, prompt-leak, and high-stakes boundaries cannot be disabled. Research access may be on while its external provider remains unavailable.
      </div>
    </div>
  )
}

// ── Password Tab ──────────────────────────────────────────────────────────────

function PasswordTab() {
  const [pw, setPw]         = useState('')
  const [confirm, setConfirm] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg]       = useState('')

  const save = async () => {
    setMsg('')
    if (pw.length < 12) { setMsg('Minimum 12 characters with upper/lower/digit'); return }
    if (pw !== confirm) { setMsg('Passwords do not match'); return }
    setSaving(true)
    try {
      const r = await fetch(`${API}/me/password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: pw }),
      })
      const d = await r.json()
      if (!r.ok) { setMsg(d.detail || 'Error'); return }
      setPw(''); setConfirm(''); setMsg('Password updated.')
    } finally { setSaving(false) }
  }

  const inputStyle = {
    background: '#1E2332', border: '1px solid #2D3348',
    color: '#E2E8F0', padding: '8px 12px', borderRadius: 6, fontSize: 13, width: '100%', boxSizing: 'border-box' as const,
  }

  return (
    <div style={{ maxWidth: 360 }}>
      <div style={{ marginBottom: 14 }}>
        <label style={{ fontSize: 12, color: '#64748B', display: 'block', marginBottom: 6 }}>New Password</label>
        <input type="password" value={pw} onChange={e => setPw(e.target.value)} style={inputStyle} placeholder="min 12 characters with upper/lower/digit" />
      </div>
      <div style={{ marginBottom: 20 }}>
        <label style={{ fontSize: 12, color: '#64748B', display: 'block', marginBottom: 6 }}>Confirm Password</label>
        <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} style={inputStyle} />
      </div>
      <button onClick={save} disabled={saving}
        style={{ padding: '8px 24px', background: '#22C55E', color: '#000', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}>
        {saving ? 'Saving...' : 'Change Password'}
      </button>
      {msg && <div style={{ marginTop: 10, fontSize: 13, color: msg === 'Password updated.' ? '#22C55E' : '#EF4444' }}>{msg}</div>}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export function AdminPage() {
  const storedUser = (() => {
    try { return JSON.parse(localStorage.getItem('cfip_user') || 'null') } catch { return null }
  })()

  const isAdmin = !storedUser || storedUser.role === 'admin'
  const defaultTab: 'users' | 'apikeys' | 'config' | 'veda' | 'password' | 'research' | 'empirical' = isAdmin ? 'users' : 'apikeys'
  const [tab, setTab] = useState<'users' | 'apikeys' | 'config' | 'veda' | 'password' | 'research' | 'empirical'>(defaultTab)

  useEffect(() => {
    if (!isAdmin && ['users', 'config', 'veda', 'research'].includes(tab)) {
      setTab('apikeys')
    }
  }, [isAdmin, tab])

  const TABS = [
    { key: 'users',    label: 'Users',       adminOnly: true  },
    { key: 'research', label: 'Research',    adminOnly: true  },
    { key: 'empirical', label: 'Empirical Cases', adminOnly: true },
    { key: 'apikeys',  label: 'API Keys',    adminOnly: false },
    { key: 'config',   label: 'Auth Config', adminOnly: true  },
    { key: 'veda',     label: 'Veda Access', adminOnly: true  },
    { key: 'password', label: 'My Password', adminOnly: false },
  ] as const

  return (
    <div style={{ color: '#E2E8F0' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>Admin</h1>

      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid #1E2332', marginBottom: 24 }}>
        {TABS.filter(t => !t.adminOnly || isAdmin).map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{
              padding: '8px 20px', background: 'transparent', border: 'none',
              borderBottom: tab === t.key ? '2px solid #22C55E' : '2px solid transparent',
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
              color: tab === t.key ? '#22C55E' : '#64748B', marginBottom: -1,
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'users'    && <UsersTab currentUser={storedUser} />}
      {tab === 'research' && isAdmin && <ResearchAdminConsole />}
      {tab === 'empirical' && isAdmin && <EmpiricalCaseIntake />}
      {tab === 'apikeys'  && <ApiKeysTab />}
      {tab === 'config'   && isAdmin && <AuthConfigTab />}
      {tab === 'veda'     && isAdmin && <VedaConfigurationTab />}
      {tab === 'password' && <PasswordTab />}
    </div>
  )
}
