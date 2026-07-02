import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

export function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const r = await fetch('http://localhost:8001/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await r.json()
      if (!r.ok) { setError(data.detail || 'Login failed'); return }
      localStorage.setItem('cfip_token', data.token)
      localStorage.setItem('cfip_user',  JSON.stringify(data.user))
      navigate('/', { replace: true })
    } catch (err) {
      setError('Cannot reach server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      backgroundColor: '#0A0D14', color: '#E2E8F0',
    }}>
      <div style={{
        width: 380, padding: 40, borderRadius: 12,
        border: '1px solid #1E2332', backgroundColor: '#141720',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 4, color: '#22C55E', marginBottom: 8 }}>
            CAPITAL FLOW
          </div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Intelligence Platform</div>
          <div style={{ fontSize: 13, color: '#64748B', marginTop: 6 }}>Sign in to continue</div>
        </div>

        <form onSubmit={submit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, color: '#64748B', display: 'block', marginBottom: 6 }}>Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              required autoFocus placeholder="admin@localhost"
              style={{
                width: '100%', boxSizing: 'border-box',
                background: '#1E2332', border: '1px solid #2D3348',
                color: '#E2E8F0', padding: '10px 12px', borderRadius: 8, fontSize: 14,
              }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ fontSize: 12, color: '#64748B', display: 'block', marginBottom: 6 }}>Password</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              required placeholder="••••••••"
              style={{
                width: '100%', boxSizing: 'border-box',
                background: '#1E2332', border: '1px solid #2D3348',
                color: '#E2E8F0', padding: '10px 12px', borderRadius: 8, fontSize: 14,
              }}
            />
          </div>

          {error && (
            <div style={{ padding: '10px 12px', borderRadius: 6, background: '#3B1F1F', color: '#FCA5A5', fontSize: 13, marginBottom: 16 }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: '11px 0', borderRadius: 8, border: 'none',
              background: loading ? '#1E2332' : '#22C55E',
              color: loading ? '#64748B' : '#000',
              fontWeight: 700, fontSize: 14, cursor: loading ? 'default' : 'pointer',
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: 24, padding: 12, borderRadius: 6, background: '#1A1D2E', fontSize: 12, color: '#64748B' }}>
          Auth disabled? Access the platform directly at{' '}
          <a href="/" style={{ color: '#22C55E' }}>the dashboard</a>.
        </div>
      </div>
    </div>
  )
}
