import { useState, useRef, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchDataStatus } from '../api/client'

const BASE = 'http://localhost:8000'

async function killBackend(): Promise<void> {
  try { await fetch(`${BASE}/api/data/kill`, { method: 'POST' }) } catch {}
}

type ModuleInfo = {
  label: string
  status: 'OK' | 'EMPTY' | 'PARTIAL' | 'UNKNOWN'
  records: string
  coverage?: string
  last_modified?: string | null
  as_of_date?: string | null
}

type ProgressInfo = {
  label: string
  pct: number
  n: number
  total: number
  elapsed?: string
  eta?: string
}

function parseProgress(data: Record<string, unknown>): ProgressInfo | null {
  if (data.type !== 'progress') return null
  const line = (data.line as string) ?? ''
  const labelMatch = line.match(/^(.+?):\s+\d+%\|/)
  return {
    label: labelMatch ? labelMatch[1].trim() : 'Progress',
    pct:     (data.pct   as number) ?? 0,
    n:       (data.n     as number) ?? 0,
    total:   (data.total as number) ?? 0,
    elapsed: data.elapsed as string | undefined,
    eta:     data.eta     as string | undefined,
  }
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    OK:      '#22C55E',
    EMPTY:   '#EF4444',
    PARTIAL: '#F59E0B',
    UNKNOWN: '#64748B',
  }
  const c = colors[status] ?? '#64748B'
  return (
    <span style={{
      backgroundColor: c + '22', color: c,
      border: `1px solid ${c}`,
      padding: '1px 8px', borderRadius: 4,
      fontSize: 10, fontWeight: 700,
    }}>
      {status}
    </span>
  )
}

function ProgressBar({ info }: { info: ProgressInfo }) {
  const done = info.pct === 100
  return (
    <div style={{ padding: '6px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#94A3B8', marginBottom: 3 }}>
        <span style={{ color: '#F59E0B', fontWeight: 600 }}>{info.label}</span>
        <span style={{ color: '#64748B' }}>
          {info.n}/{info.total}
          {info.elapsed ? ` | ${info.elapsed} elapsed` : ''}
          {info.eta && !done ? ` | ETA: ${info.eta}` : ''}
          {done ? ' | complete' : ''}
        </span>
      </div>
      <div style={{ height: 6, backgroundColor: '#1E2332', borderRadius: 3 }}>
        <div style={{
          width: `${info.pct}%`, height: 6,
          backgroundColor: done ? '#22C55E' : '#F59E0B',
          borderRadius: 3, transition: 'width 0.4s',
        }} />
      </div>
      <div style={{ fontSize: 9, color: '#64748B', marginTop: 2 }}>{info.pct}%</div>
    </div>
  )
}

// Engine key lookup by module key
const ENGINE_MAP: Record<string, string> = {
  bhavcopy_equity:              'bhavcopy_equity',
  bhavcopy_fno:                 'bhavcopy_fno',
  corporate_actions:            'corporate_actions',
  equity_master:                'equity_master',
  stock_history_cache:          'stock_history_build',
  participant_flows:            'participant_5a',
  participant_flow_scores:      'participant_5b',
  participant_intelligence:     'participant_5c',
  sector_flow_scores:           'sector_6b',
  sector_rotation_intelligence: 'sector_6c',
  price_momentum:               'momentum_8a',
  bull_run_probability:         'bull_run_8b',
  ml_scores_combined:           'ml_12',
  block_bulk_deals:             'deals_7a',
  deal_signals:                 'deals_7a',
  event_calendar:               'events_7b',
  upcoming_catalysts:           'events_7b',
  corporate_action_signals:     'corp_actions_7c',
  corporate_confidence:         'corp_actions_7c',
}

function ModuleTable({
  title,
  modules,
  pipelineKey,
  onBusyChange,
  onRunComplete,
}: {
  title: string
  modules: Record<string, ModuleInfo>
  pipelineKey: string
  onBusyChange?: (busy: boolean) => void
  onRunComplete?: () => void
}) {
  const [running, setRunning]             = useState<string | null>(null)
  const [logs, setLogs]                   = useState<Record<string, string[]>>({})
  const [engProgress, setEngProgress]     = useState<Record<string, ProgressInfo | null>>({})
  const [openLog, setOpenLog]             = useState<string | null>(null)
  const [pipeRunning, setPipeRunning]     = useState(false)
  const [pipeLogs, setPipeLogs]           = useState<string[]>([])
  const [pipeProgress, setPipeProgress]   = useState<ProgressInfo | null>(null)
  const logRef   = useRef<HTMLDivElement>(null)
  const pipeRef  = useRef<HTMLDivElement>(null)
  const activeEs = useRef<EventSource | null>(null)

  const busy = running !== null || pipeRunning

  useEffect(() => { onBusyChange?.(busy) }, [busy])

  function streamEngine(key: string, onLine: (line: string) => void, onProgress: (p: ProgressInfo) => void, onDone: () => void) {
    activeEs.current?.close()
    const es = new EventSource(`${BASE}/api/data/run/${key}`)
    activeEs.current = es
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.ping) return                          // keepalive — ignore
        if (data.type === 'progress') {
          const p = parseProgress(data)
          if (p) onProgress(p)
        } else if (data.line !== undefined) {
          onLine(data.line as string)
        }
        if (data.done || data.all_done) { es.close(); activeEs.current = null; onDone() }
      } catch {}
    }
    es.onerror = () => { es.close(); activeEs.current = null; onDone() }
  }

  function stopAll() {
    activeEs.current?.close()
    activeEs.current = null
    killBackend()
    setRunning(null)
    setPipeRunning(false)
  }

  function runEngine(engineKey: string) {
    setRunning(engineKey)
    setLogs(prev => ({ ...prev, [engineKey]: [`Starting ${engineKey}...`] }))
    setEngProgress(prev => ({ ...prev, [engineKey]: null }))
    setOpenLog(engineKey)
    streamEngine(
      engineKey,
      (line) => {
        setLogs(prev => ({ ...prev, [engineKey]: [...(prev[engineKey] ?? []), line] }))
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
      },
      (p) => setEngProgress(prev => ({ ...prev, [engineKey]: p })),
      () => { setRunning(null); onRunComplete?.() },
    )
  }

  function runSectionPipeline() {
    setPipeRunning(true)
    setPipeLogs([`Starting ${title} pipeline...`])
    setPipeProgress(null)
    streamEngine(
      pipelineKey,
      (line) => {
        setPipeLogs(prev => [...prev, line])
        if (pipeRef.current) pipeRef.current.scrollTop = pipeRef.current.scrollHeight
      },
      (p) => setPipeProgress(p),
      () => { setPipeRunning(false); onRunComplete?.() },
    )
  }

  const okCount = Object.values(modules).filter(m => m.status === 'OK').length
  const total   = Object.keys(modules).length
  const pct     = total > 0 ? Math.round((okCount / total) * 100) : 0

  return (
    <div style={{ marginBottom: 32 }}>

      {/* Section header + health bar + pipeline button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <h2 style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700, letterSpacing: 2, margin: 0, whiteSpace: 'nowrap' }}>
          {title}
        </h2>
        <div style={{ flex: 1, height: 6, backgroundColor: '#1E2332', borderRadius: 3 }}>
          <div style={{
            width: `${pct}%`, height: 6, borderRadius: 3,
            backgroundColor: pct === 100 ? '#22C55E' : pct > 50 ? '#F59E0B' : '#EF4444',
            transition: 'width 0.5s',
          }} />
        </div>
        <span style={{ color: '#64748B', fontSize: 11, whiteSpace: 'nowrap' }}>{okCount}/{total} ({pct}%)</span>
        {busy ? (
          <button
            onClick={stopAll}
            style={{
              padding: '3px 14px', borderRadius: 4,
              border: '1px solid #EF4444',
              backgroundColor: '#EF444422',
              color: '#EF4444',
              cursor: 'pointer',
              fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap',
            }}
          >
            Stop
          </button>
        ) : (
          <button
            onClick={runSectionPipeline}
            style={{
              padding: '3px 14px', borderRadius: 4,
              border: '1px solid #22C55E',
              backgroundColor: 'transparent',
              color: '#22C55E',
              cursor: 'pointer',
              fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap',
            }}
          >
            Run Pipeline
          </button>
        )}
      </div>

      {/* Module table */}
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
            const hasLogs   = (logs[engineKey] ?? []).length > 0
            const progress  = engProgress[engineKey] ?? null

            return (
              <>
                <tr key={key} style={{ borderBottom: '1px solid #1E233230' }}>
                  <td style={{ padding: '6px 8px', color: '#E2E8F0', fontWeight: 600 }}>{m.label}</td>
                  <td style={{ padding: '6px 8px', textAlign: 'center' }}><StatusBadge status={m.status} /></td>
                  <td style={{ padding: '6px 8px', color: '#94A3B8' }}>{m.records}</td>
                  <td style={{ padding: '6px 8px', color: '#64748B' }}>{m.as_of_date ?? m.coverage ?? '-'}</td>
                  <td style={{ padding: '6px 8px', color: '#64748B' }}>{m.last_modified ?? '-'}</td>
                  <td style={{ padding: '6px 8px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: 4, justifyContent: 'center' }}>
                      {engineKey && (
                        <button
                          onClick={() => runEngine(engineKey)}
                          disabled={busy}
                          style={{
                            padding: '2px 10px', borderRadius: 4,
                            border: '1px solid #22C55E',
                            backgroundColor: isRunning ? '#22C55E22' : 'transparent',
                            color: '#22C55E',
                            cursor: busy ? 'not-allowed' : 'pointer',
                            fontSize: 10, fontWeight: 700,
                          }}
                        >
                          {isRunning ? 'Running...' : 'Run'}
                        </button>
                      )}
                      {hasLogs && (
                        <button
                          onClick={() => setOpenLog(openLog === engineKey ? null : engineKey)}
                          style={{
                            padding: '2px 8px', borderRadius: 4,
                            border: '1px solid #334155',
                            backgroundColor: 'transparent', color: '#64748B',
                            cursor: 'pointer', fontSize: 10,
                          }}
                        >
                          {openLog === engineKey ? 'Hide' : 'Log'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>

                {/* Inline progress bar while running */}
                {isRunning && progress && (
                  <tr key={`${key}_prog`}>
                    <td colSpan={6} style={{ padding: '0 8px 4px 8px' }}>
                      <ProgressBar info={progress} />
                    </td>
                  </tr>
                )}

                {/* Log panel */}
                {openLog === engineKey && hasLogs && (
                  <tr key={`${key}_log`}>
                    <td colSpan={6} style={{ padding: '0 8px 8px 8px' }}>
                      <div
                        ref={logRef}
                        style={{
                          backgroundColor: '#0A0D14', border: '1px solid #1E2332',
                          borderRadius: 4, padding: 8,
                          maxHeight: 180, overflowY: 'auto',
                          fontFamily: 'monospace', fontSize: 10,
                          color: '#94A3B8', whiteSpace: 'pre-wrap',
                        }}
                      >
                        {(logs[engineKey] ?? []).map((line, i) => (
                          <div key={i} style={{
                            color: line.startsWith('ERROR') ? '#EF4444'
                                 : line.startsWith('---')   ? '#22C55E'
                                 : '#94A3B8',
                          }}>
                            {line || ' '}
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

      {/* Section pipeline log */}
      {pipeLogs.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div style={{ color: '#64748B', fontSize: 10, marginBottom: 4, letterSpacing: 1 }}>
            {title} PIPELINE LOG
          </div>
          {pipeProgress && <ProgressBar info={pipeProgress} />}
          <div
            ref={pipeRef}
            style={{
              backgroundColor: '#0A0D14', border: '1px solid #1E2332',
              borderRadius: 4, padding: 8,
              maxHeight: 220, overflowY: 'auto',
              fontFamily: 'monospace', fontSize: 10,
              color: '#94A3B8', whiteSpace: 'pre-wrap',
              marginTop: pipeProgress ? 4 : 0,
            }}
          >
            {pipeLogs.map((line, i) => (
              <div key={i} style={{
                color: line.startsWith('ERROR') ? '#EF4444'
                     : line.startsWith('---')   ? '#22C55E'
                     : '#94A3B8',
              }}>
                {line || ' '}
              </div>
            ))}
            {pipeRunning && <div style={{ color: '#F59E0B' }}>... running ...</div>}
          </div>
        </div>
      )}
    </div>
  )
}

export function DataControlPage() {
  const { data: status, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['data_status'],
    queryFn: fetchDataStatus,
    staleTime: 0,           // always consider stale so manual refetch hits the network
    refetchOnWindowFocus: false,
  })

  const [pipeRunning, setPipeRunning]     = useState(false)
  const [pipeLogs, setPipeLogs]           = useState<string[]>([])
  const [pipeProgress, setPipeProgress]   = useState<ProgressInfo | null>(null)
  const [sectionBusy, setSectionBusy]     = useState<Record<string, boolean>>({})
  const pipeRef  = useRef<HTMLDivElement>(null)
  const activeEs = useRef<EventSource | null>(null)

  // Kill any stale subprocess from a previous session on page load
  useEffect(() => { killBackend() }, [])

  const anythingRunning = pipeRunning || Object.values(sectionBusy).some(Boolean)

  const handleSectionBusy = useCallback((section: string) => (busy: boolean) => {
    setSectionBusy(prev => ({ ...prev, [section]: busy }))
  }, [])

  function stopAll() {
    activeEs.current?.close()
    activeEs.current = null
    killBackend()
    setPipeRunning(false)
  }

  function runFullPipeline() {
    killBackend()          // clear any stale process before starting
    setPipeRunning(true)
    setPipeLogs(['Starting full intelligence pipeline...'])
    setPipeProgress(null)
    activeEs.current?.close()
    const es = new EventSource(`${BASE}/api/data/run/pipeline_all`)
    activeEs.current = es
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.ping) return                        // keepalive — ignore
        if (data.type === 'progress') {
          const p = parseProgress(data)
          if (p) setPipeProgress(p)
        } else if (data.line !== undefined) {
          setPipeLogs(prev => [...prev, data.line as string])
          if (pipeRef.current) pipeRef.current.scrollTop = pipeRef.current.scrollHeight
        }
        if (data.all_done) { es.close(); activeEs.current = null; setPipeRunning(false); refetch() }
      } catch {}
    }
    es.onerror = () => { es.close(); activeEs.current = null; setPipeRunning(false); refetch() }
  }

  if (isLoading) return (
    <div style={{ color: '#64748B', padding: 40, textAlign: 'center' }}>Scanning data modules...</div>
  )

  const acquisition  = (status?.acquisition  ?? {}) as Record<string, ModuleInfo>
  const intelligence = (status?.intelligence ?? {}) as Record<string, ModuleInfo>

  const acqOk   = Object.values(acquisition).filter(m => m.status === 'OK').length
  const intOk   = Object.values(intelligence).filter(m => m.status === 'OK').length
  const total   = Object.keys(acquisition).length + Object.keys(intelligence).length
  const totalOk = acqOk + intOk
  const pct     = total > 0 ? Math.round((totalOk / total) * 100) : 0

  return (
    <div style={{ maxWidth: 1100 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
          DATA CONTROL
        </h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            style={{
              padding: '4px 14px', borderRadius: 4,
              border: '1px solid #334155', backgroundColor: 'transparent',
              color: isFetching ? '#22C55E' : '#64748B',
              cursor: isFetching ? 'not-allowed' : 'pointer',
              fontSize: 11,
              transition: 'color 0.2s',
            }}
          >
            {isFetching ? 'Refreshing...' : 'Refresh Status'}
          </button>
          {anythingRunning && (
            <button
              onClick={stopAll}
              style={{
                padding: '4px 18px', borderRadius: 4,
                border: '1px solid #EF4444',
                backgroundColor: '#EF444433',
                color: '#EF4444',
                cursor: 'pointer',
                fontSize: 11, fontWeight: 700, letterSpacing: 1,
              }}
            >
              STOP
            </button>
          )}
          <button
            onClick={runFullPipeline}
            disabled={anythingRunning}
            style={{
              padding: '4px 14px', borderRadius: 4,
              border: '1px solid #22C55E',
              backgroundColor: pipeRunning ? '#22C55E22' : 'transparent',
              color: '#22C55E',
              cursor: anythingRunning ? 'not-allowed' : 'pointer',
              fontSize: 11, fontWeight: 700,
            }}
          >
            {pipeRunning ? 'Full Pipeline Running...' : 'Run Full Pipeline'}
          </button>
        </div>
      </div>

      {/* Overall health */}
      <div style={{
        backgroundColor: '#141720', border: '1px solid #1E2332',
        borderRadius: 6, padding: 16, marginBottom: 24,
        display: 'flex', alignItems: 'center', gap: 16,
      }}>
        <div style={{
          fontSize: 28, fontWeight: 700,
          color: pct === 100 ? '#22C55E' : pct > 70 ? '#F59E0B' : '#EF4444',
        }}>
          {pct}%
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: '#94A3B8', fontSize: 12, marginBottom: 6 }}>
            Platform Health — {totalOk}/{total} modules operational
          </div>
          <div style={{ height: 8, backgroundColor: '#1E2332', borderRadius: 4 }}>
            <div style={{
              width: `${pct}%`, height: 8, borderRadius: 4,
              backgroundColor: pct === 100 ? '#22C55E' : pct > 70 ? '#F59E0B' : '#EF4444',
            }} />
          </div>
        </div>
        <div style={{ fontSize: 11, color: '#64748B', textAlign: 'right' }}>
          <div>Acquisition: {acqOk}/{Object.keys(acquisition).length}</div>
          <div>Intelligence: {intOk}/{Object.keys(intelligence).length}</div>
        </div>
      </div>

      <ModuleTable title="DATA ACQUISITION"     modules={acquisition}  pipelineKey="pipeline_acquisition"  onBusyChange={handleSectionBusy('acquisition')}  onRunComplete={refetch} />
      <ModuleTable title="INTELLIGENCE OUTPUTS" modules={intelligence} pipelineKey="pipeline_intelligence" onBusyChange={handleSectionBusy('intelligence')} onRunComplete={refetch} />

      {/* Full pipeline log */}
      {pipeLogs.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ color: '#64748B', fontSize: 11, marginBottom: 6 }}>FULL PIPELINE LOG</div>
          {pipeProgress && <ProgressBar info={pipeProgress} />}
          <div
            ref={pipeRef}
            style={{
              backgroundColor: '#0A0D14', border: '1px solid #1E2332',
              borderRadius: 4, padding: 12,
              height: 280, overflowY: 'auto',
              fontFamily: 'monospace', fontSize: 10,
              color: '#94A3B8', whiteSpace: 'pre-wrap',
              marginTop: pipeProgress ? 4 : 0,
            }}
          >
            {pipeLogs.map((line, i) => (
              <div key={i} style={{
                color: line.startsWith('ERROR') ? '#EF4444'
                     : line.startsWith('---')   ? '#22C55E'
                     : '#94A3B8',
              }}>
                {line || ' '}
              </div>
            ))}
            {pipeRunning && <div style={{ color: '#F59E0B' }}>... running ...</div>}
          </div>
        </div>
      )}
    </div>
  )
}
