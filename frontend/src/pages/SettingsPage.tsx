import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '../api/client'

export function SettingsPage() {
  const { data: health, isLoading } = useQuery({ queryKey: ['health'], queryFn: fetchHealth, refetchInterval: 60000 })

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>SETTINGS</h1>

      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>DATA FRESHNESS</h2>
        <div className="p-4 rounded border text-xs space-y-2" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
          {isLoading ? (
            <div style={{ color: '#64748B' }}>Loading...</div>
          ) : (
            <>
              <div className="flex justify-between">
                <span style={{ color: '#64748B' }}>API Status</span>
                <span style={{ color: '#22C55E' }}>ONLINE</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: '#64748B' }}>Datasets Loaded</span>
                <span style={{ color: '#E2E8F0' }}>
                  {(health as Record<string, number>)?.datasets_loaded ?? 0} / {(health as Record<string, number>)?.datasets_total ?? 11}
                </span>
              </div>
            </>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>ALERT CONFIGURATION</h2>
        <div className="p-4 rounded border text-xs space-y-2" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
          <div className="flex justify-between">
            <span style={{ color: '#64748B' }}>Telegram Alerts</span>
            <span style={{ color: '#F59E0B' }}>Configure via .env (TELEGRAM_BOT_TOKEN)</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: '#64748B' }}>Daily Digest</span>
            <span style={{ color: '#64748B' }}>18:30 IST (run alert_scheduler.py)</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: '#64748B' }}>Alert Checks</span>
            <span style={{ color: '#64748B' }}>Every 30 min post-market</span>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xs tracking-widest mb-3" style={{ color: '#64748B' }}>PLATFORM</h2>
        <div className="p-4 rounded border text-xs space-y-2" style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}>
          <div className="flex justify-between">
            <span style={{ color: '#64748B' }}>API</span>
            <span style={{ color: '#64748B' }}>http://localhost:8000 (uvicorn)</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: '#64748B' }}>Docs</span>
            <span style={{ color: '#3B82F6' }}>http://localhost:8000/docs</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: '#64748B' }}>Intelligence</span>
            <span style={{ color: '#64748B' }}>data/intelligence/ (16 CSVs)</span>
          </div>
        </div>
      </section>
    </div>
  )
}
