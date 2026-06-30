import { useState, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchDataStatus } from '../api/client'

const BASE = 'http://localhost:8000'

type ModuleInfo = {
  label: string
  status: 'OK' | 'EMPTY' | 'PARTIAL' | 'UNKNOWN'
  records: string
  coverage?: string
  last_modified?: string | null
  as_of_date?: string | null
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    OK:      '#22C55E',
    EMPTY:   '#EF4444',
    PARTIAL: '#F59E0B',
    UNKNOWN: '#64748B',
  }
  return (
    <span style={{
      backgroundColor: colors[status] + '22',
      color: colors[status],
      border: `1px solid ${colors[status]}`,
      padding: '1px 8px',
      borderRadius: 4,
      fontSize: 10,
      fontWeight: 700,
    }}>
      {status}
    </span>
  )
}

function ModuleTable({ title, modules }: { title: string; modules: Record<string, ModuleInfo>; }) {
  const [running, setRunning] = useState<string | null>(null)
  const [logs, setLogs] = useState<Record<string, string[]>>({})
  const [openLog, setOpenLog] = useState<string | null>(null)
  const logRef = useRef<HTMLDivElement>(null)

  function runEngine(engineKey: string) {
    setRunning(engineKey)
    setLogs(prev => ({ ...prev, [engineKey]: [`Starting ${engineKey}...`] }))
    setOpenLog(engineKey)

    const es = new EventSource(`${BASE}/api/data/run/${engineKey}`)
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.line !== undefined) {
          setLogs(prev => ({
            ...prev,
            [engineKey]: [...(prev[engineKey] || []), data.line],
          }))
          if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
        }
        if (data.done || data.all_done) {
          es.close()
          setRunning(null)
        }
      } catch {}
    }
    es.onerror = () => {
      setLogs(prev => ({ ...prev, [engineKey]: [...(prev[engineKey] || []), '--- Connection closed ---'] }))
      es.close()
      setRunning(null)
    }
  }

  // Map module key to engine key
  const ENGINE_MAP: Record<string, string> = {
    bhavcopy_equity:      'bhavcopy_equity',
    bhavcopy_fno:         'bhavcopy_fno',
    corporate_actions:    'corporate_actions',
    equity_master:        'equity_master',
    stock_history_cache:  'stock_history_build',
    participant_flows:    'participant_5a',
    participant_intelligence: 'participant_5c',
    sector_rotation_intelligence: 'sector_6c',
    bull_run_probability: 'bull_run_8b',
    price_momentum:       'momentum_8a',
    ml_scores_combined:   'ml_12',
    block_bulk_deals:     'deals_7a',
    event_calendar:       'events_7b',
    corporate_action_signals: 'corp_actions_7c',
    upcoming_catalysts:   'events_7b',
    deal_signals:         'deals_7a',
    corporate_confidence: 'corp_actions_7c',
    sector_flow_scores:   'sector_6b',
    participant_flow_scores: 'participant_5b',
  }

  const okCount = Object.values(modules).filter(m => m.status === 'OK').length
  const total = Object.keys(modules).length
  const pct = total > 0 ? Math.round((okCount / total) * 100) : 0

  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
        <h2 style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700, letterSpacing: 2, margin: 0 }}>{title}</h2>
        <div style={{ flex: 1, height: 6, backgroundColor: '#1E2332', borderRadius: 3 }}>
          <div style={{ width: `${pct}%`, height: 6, backgroundColor: pct === 100 ? '#22C55E' : pct > 50 ? '#F59E0B' : '#EF4444', borderRadius: 3, transition: 'width 0.5s' }} />
        </div>
        <span style={{ color: '#64748B', fontSize: 11 }}>{okCount}/{total} ({pct}%)</span>
      </div>

      <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #1E2332', color: '#64748B' }}>
            <th style={{ textAlign: 'left', padding: '6px 8px' }}>Module</th>
            <th style={{ textAlign: 'center', padding: '6px 8px' }}>Status</th>
            <th style={{ textAlign: 'left', padding: '6px 8px' }}>Records</th>
            <th style={{ textAlign: 'left', padding: '6px 8px' }}>Coverage / As-of</th>
            <th style={{ textAlign: 'left', padding: '6px 8px' }}>Last Updated</th>
            <th style={{ textAlign: 'center', padding: '6px 8px' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(modules).map(([key, m]) => {
            const engineKey = ENGINE_MAP[key]
            const isRunning = running === engineKey
            const hasLogs = (logs[engineKey] || []).length > 0
            return (
              <>
                <tr key={key} style={{ borderBottom: '1px solid #1E233240' }}>
                  <td style={{ padding: '6px 8px', color: '#E2E8F0', fontWeight: 600 }}>{m.label}</td>
                  <td style={{ padding: '6px 8px', textAlign: 'center' }}><StatusBadge status={m.status} /></td>
                  <td style={{ padding: '6px 8px', color: '#94A3B8' }}>{m.records}</td>
                  <td style={{ padding: '6px 8px', color: '#64748B' }}>{m.as_of_date || m.coverage || '-'}</td>
                  <td style={{ padding: '6px 8px', color: '#64748B' }}>{m.last_modified || '-'}</td>
                  <td style={{ padding: '6px 8px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: 4, justifyContent: 'center' }}>
                      {engineKey && (
                        <button
                          onClick={() => runEngine(engineKey)}
                          disabled={running !== null}
                          style={{
                            padding: '2px 10px',
                            borderRadius: 4,
                            border: '1px solid #22C55E',
                            backgroundColor: isRunning ? '#22C55E22' : 'transparent',
                            color: '#22C55E',
                            cursor: running ? 'not-allowed' : 'pointer',
                            fontSize: 10,
                            fontWeight: 700,
                          }}
                        >
                          {isRunning ? 'Running...' : 'Run'}
                        </button>
                      )}
                      {hasLogs && (
                        <button
                          onClick={() => setOpenLog(openLog === engineKey ? null : engineKey)}
                          style={{ padding: '2px 8px', borderRadius: 4, border: '1px solid #334155', backgroundColor: 'transparent', color: '#64748B', cursor: 'pointer', fontSize: 10 }}
                        >
                          {openLog === engineKey ? 'Hide Log' : 'Log'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
                {openLog === engineKey && hasLogs && (
                  <tr key={`${key}_log`}>
                    <td colSpan={6} style={{ padding: '0 8px 8px 8px' }}>
                      <div
                        ref={logRef}
                        style={{
                          backgroundColor: '#0A0D14',
                          border: '1px solid #1E2332',
                          borderRadius: 4,
                          padding: 8,
                          maxHeight: 200,
                          overflowY: 'auto',
                          fontFamily: 'monospace',
                          fontSize: 10,
                          color: '#94A3B8',
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {(logs[engineKey] || []).map((line, i) => (
                          <div key={i} style={{ color: line.startsWith('ERROR') ? '#EF4444' : line.startsWith('---') ? '#22C55E' : '#94A3B8' }}>
                            {line || ' '}
                          </div>
                        ))}
                        {isRunning && <div style={{ color: '#F59E0B' }}>... running ...</div>}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export function DataControlPage() {
  const { data: status, isLoading, refetch } = useQuery({
    queryKey: ['data_status'],
    queryFn: fetchDataStatus,
    staleTime: 30000,
  })

  const [pipelineRunning, setPipelineRunning] = useState(false)
  const [pipelineLogs, setPipelineLogs] = useState<string[]>([])
  const pipelineRef = useRef<HTMLDivElement>(null)

  function runPipeline() {
    setPipelineRunning(true)
    setPipelineLogs(['Starting full intelligence pipeline...'])
    const es = new EventSource(`${BASE}/api/data/run/pipeline_all`)
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.line !== undefined) {
          setPipelineLogs(prev => [...prev, data.line])
          if (pipelineRef.current) pipelineRef.current.scrollTop = pipelineRef.current.scrollHeight
        }
        if (data.all_done) { es.close(); setPipelineRunning(false); refetch() }
      } catch {}
    }
    es.onerror = () => { es.close(); setPipelineRunning(false) }
  }

  if (isLoading) return <div style={{ color: '#64748B', padding: 40, textAlign: 'center' }}>Scanning data modules...</div>

  const acquisition = status?.acquisition || {}
  const intelligence = status?.intelligence || {}

  // Summary counts
  const acqOk = Object.values(acquisition).filter((m: any) => m.status === 'OK').length
  const intOk = Object.values(intelligence).filter((m: any) => m.status === 'OK').length
  const total = Object.keys(acquisition).length + Object.keys(intelligence).length
  const totalOk = acqOk + intOk
  const overallPct = total > 0 ? Math.round((totalOk / total) * 100) : 0

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
          DATA CONTROL
        </h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => refetch()}
            style={{ padding: '4px 14px', borderRadius: 4, border: '1px solid #334155', backgroundColor: 'transparent', color: '#64748B', cursor: 'pointer', fontSize: 11 }}
          >
            Refresh Status
          </button>
          <button
            onClick={runPipeline}
            disabled={pipelineRunning}
            style={{ padding: '4px 14px', borderRadius: 4, border: '1px solid #22C55E', backgroundColor: pipelineRunning ? '#22C55E22' : 'transparent', color: '#22C55E', cursor: pipelineRunning ? 'not-allowed' : 'pointer', fontSize: 11, fontWeight: 700 }}
          >
            {pipelineRunning ? 'Pipeline Running...' : 'Run Full Pipeline'}
          </button>
        </div>
      </div>

      {/* Overall health bar */}
      <div style={{ backgroundColor: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ fontSize: 28, fontWeight: 700, color: overallPct === 100 ? '#22C55E' : overallPct > 70 ? '#F59E0B' : '#EF4444' }}>
          {overallPct}%
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: '#94A3B8', fontSize: 12, marginBottom: 6 }}>Platform Health — {totalOk}/{total} modules operational</div>
          <div style={{ height: 8, backgroundColor: '#1E2332', borderRadius: 4 }}>
            <div style={{ width: `${overallPct}%`, height: 8, backgroundColor: overallPct === 100 ? '#22C55E' : overallPct > 70 ? '#F59E0B' : '#EF4444', borderRadius: 4 }} />
          </div>
        </div>
        <div style={{ fontSize: 11, color: '#64748B', textAlign: 'right' }}>
          <div>Acquisition: {acqOk}/{Object.keys(acquisition).length}</div>
          <div>Intelligence: {intOk}/{Object.keys(intelligence).length}</div>
        </div>
      </div>

      <ModuleTable title="DATA ACQUISITION" modules={acquisition as any} />
      <ModuleTable title="INTELLIGENCE OUTPUTS" modules={intelligence as any} />

      {/* Pipeline log */}
      {pipelineLogs.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ color: '#64748B', fontSize: 11, marginBottom: 6 }}>PIPELINE LOG</div>
          <div
            ref={pipelineRef}
            style={{ backgroundColor: '#0A0D14', border: '1px solid #1E2332', borderRadius: 4, padding: 12, height: 300, overflowY: 'auto', fontFamily: 'monospace', fontSize: 10, color: '#94A3B8', whiteSpace: 'pre-wrap' }}
          >
            {pipelineLogs.map((line, i) => (
              <div key={i} style={{ color: line.startsWith('ERROR') ? '#EF4444' : line.startsWith('---') ? '#22C55E' : '#94A3B8' }}>
                {line || ' '}
              </div>
            ))}
            {pipelineRunning && <div style={{ color: '#F59E0B' }}>... running ...</div>}
          </div>
        </div>
      )}
    </div>
  )
}
