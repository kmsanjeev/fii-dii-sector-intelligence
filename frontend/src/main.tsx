import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Global fetch interceptor: attaches Bearer token to all API calls and
// redirects to /login on 401 (only when auth is enabled server-side).
const _fetch = window.fetch.bind(window)
window.fetch = async (input: RequestInfo | URL, init: RequestInit = {}) => {
  const token = localStorage.getItem('cfip_token')
  const url   = typeof input === 'string' ? input
              : input instanceof URL      ? input.toString()
              : (input as Request).url

  const isApi    = url.includes('/api/')
  const isAuthEp = url.includes('/api/auth/')

  if (token && isApi && !isAuthEp) {
    init = {
      ...init,
      headers: { ...(init.headers as Record<string, string> || {}), 'Authorization': `Bearer ${token}` },
    }
  }

  const response = await _fetch(input, init)

  // If any API call returns 401 outside the auth endpoints, clear session and redirect
  if (response.status === 401 && isApi && !isAuthEp) {
    localStorage.removeItem('cfip_token')
    localStorage.removeItem('cfip_user')
    window.location.href = '/login'
  }

  return response
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
