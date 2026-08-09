import { useState, useRef, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchDataStatus } from '../api/client'

const BASE     = ''
const API_BASE = ''

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

// ── Daily Pipeline Panel ──────────────────────────────────────────────────────

type StageInfo = {
  label:        string
  status:       string   // RUNNING | DONE | FAILED | TIMEOUT | STOPPED
  started_at?:  string
  finished_at?: string
  duration_s?:  number
  error?:       string
}

type PipelineStatus = {
  state:         string  // IDLE | RUNNING | DONE | FAILED | STOPPED
  run_id:        string | null
  started_at:    string | null
  last_run_at:   string | null
  current_stage: string | null
  current_label: string | null
  next_run_ist:  string | null
  stages:        Record<string, StageInfo>
}

// ── Section definitions for pipeline grouping ─────────────────────────────────

const PIPELINE_SECTIONS: { id: string; title: string; stages: string[] }[] = [
  {
    id: 'acquisition',
    title: 'Daily Acquisition',
    stages: [
      '1A_bhavcopy_equity',
      '1B_bhavcopy_fno',
      '1C_corp_actions',
      '1D_equity_master',
      '1E_price_adjust',
      '1F_stock_history',
    ],
  },
  {
    id: 'intelligence',
    title: 'Intelligence Gathering',
    stages: [
      '17_symbol_change',
      '5A_participant_acquisition',
      '5B_participant_flow',
      '5C_participant_intelligence',
      '6A_sector_capital_flow',
      '6B_sector_flow_scores',
      '6C_sector_rotation',
      '7A_block_bulk_deals',
      '7C_corp_action_intel',
      '18A_announcements',
      '16A_management_sentiment',
      'A1_technical_indicators',
      'A2_fno_intelligence',
      '8A_price_momentum',
      '8B_bull_run_probability',
      '12_ml_scorer',
      'C1_trade_conviction',
      '13A_document_builder',
      '13B_faiss_indexer',
      '13C_bm25_indexer',
      '20_portfolio',
      '9_alert_engine',
    ],
  },
]

const STAGE_ORDER = PIPELINE_SECTIONS.flatMap(s => s.stages)

const STAGE_LABELS: Record<string, string> = {
  '1A_bhavcopy_equity':          'NSE Equity Bhavcopy Download',
  '1B_bhavcopy_fno':             'NSE F&O Bhavcopy Download',
  '1C_corp_actions':             'Corporate Actions Update',
  '1D_equity_master':            'Equity Master Refresh',
  '1E_price_adjust':             'Price Adjustment (adjusted OHLCV)',
  '1F_stock_history':            'Stock History Cache (incremental)',
  '17_symbol_change':            'Symbol Change History',
  '5A_participant_acquisition':  'Participant Acquisition (NSE API)',
  '5B_participant_flow':         'Participant Flow Scores',
  '5C_participant_intelligence': 'Participant Intelligence',
  '6A_sector_capital_flow':      'Sector Capital Flow',
  '6B_sector_flow_scores':       'Sector Flow Scores',
  '6C_sector_rotation':          'Sector Rotation Intelligence',
  '7A_block_bulk_deals':         'Block/Bulk Deals (NSE API)',
  '7C_corp_action_intel':        'Corporate Action Intelligence',
  '18A_announcements':           'Corporate Announcements (incremental)',
  '16A_management_sentiment':    'Management Sentiment (Claude AI)',
  'A1_technical_indicators':     'Technical Indicators',
  'A2_fno_intelligence':         'F&O Intelligence (PCR + OI signals)',
  '8A_price_momentum':           'Price Momentum',
  '8B_bull_run_probability':     'Bull Run Probability',
  '12_ml_scorer':                'ML Scorer (inference)',
  'C1_trade_conviction':         'Trade Conviction Scores',
  '13A_document_builder':        'RAG Document Builder',
  '13B_faiss_indexer':           'FAISS Indexer (embedding)',
  '13C_bm25_indexer':            'BM25 Indexer',
  '20_portfolio':                'Portfolio Intelligence Rebuild',
  '9_alert_engine':              'Alert Engine (Telegram push)',
}

// Map stage IDs to their data-status keys for Records / Coverage columns
const STAGE_STATUS_KEY: Record<string, string> = {
  '1A_bhavcopy_equity':          'bhavcopy_equity',
  '1B_bhavcopy_fno':             'bhavcopy_fno',
  '1C_corp_actions':             'corporate_actions',
  '1D_equity_master':            'equity_master',
  '1E_price_adjust':             'adjusted_equity',
  '1F_stock_history':            'stock_history_cache',
  '5A_participant_acquisition':  'participant_flows',
  '6A_sector_capital_flow':      'sector_flow_scores',
  '7A_block_bulk_deals':         'block_bulk_deals',
  '8A_price_momentum':           'price_momentum',
  '8B_bull_run_probability':     'bull_run_probability',
  '12_ml_scorer':                'ml_scores_combined',
  'C1_trade_conviction':         'trade_conviction_scores',
  'A1_technical_indicators':     'technical_indicators',
  'A2_fno_intelligence':         'fno_intelligence',
  '13B_faiss_indexer':           'participant_intelligence',  // proxy — RAG has no direct file
  '20_portfolio':                'deal_signals',              // proxy — portfolio has no direct file
}

// Map backfill engine keys to labels/descriptions
const BACKFILL_ENGINES: { key: string; label: string; desc: string }[] = [
  { key: 'results_acquisition',               label: 'Financial Results (recent)',       desc: 'Last 2 quarters NSE XBRL P&L' },
  { key: 'results_acquisition_full',          label: 'Financial Results (full backfill)', desc: 'Full FY2018+ XBRL history' },
  { key: 'valuation_15b',                     label: 'Valuation Scores',                 desc: 'P/E, ROE per symbol' },
  { key: 'extended_financials_15b',           label: 'Extended Financials (recent)',     desc: 'OPM, ROCE, Book Value, Sales CAGR' },
  { key: 'extended_financials_15b_backfill',  label: 'Extended Financials (backfill)',   desc: '3Y growth window history' },
  { key: 'shp_acquisition',                   label: 'Shareholding (latest quarter)',    desc: 'FII/DII/promoter % from NSE' },
  { key: 'shp_acquisition_full',              label: 'Shareholding (full backfill)',     desc: 'Full FY2008+ quarterly history' },
  { key: 'stock_history_full',                label: 'Stock History Cache (full rebuild)', desc: 'Rebuild all per-symbol parquet from scratch' },
]

function stageColor(status: string): string {
  if (status === 'DONE')    return '#22C55E'
  if (status === 'RUNNING') return '#F59E0B'
  if (status === 'FAILED' || status === 'TIMEOUT') return '#EF4444'
  if (status === 'STOPPED') return '#64748B'
  return '#334155'
}

function stateColor(state: string): string {
  if (state === 'RUNNING') return '#F59E0B'
  if (state === 'DONE')    return '#22C55E'
  if (state === 'FAILED')  return '#EF4444'
  if (state === 'STOPPED') return '#64748B'
  return '#334155'
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '14px 0 6px' }}>
      <div style={{ fontSize: 9, fontWeight: 800, color: '#475569', letterSpacing: '0.12em', flexShrink: 0 }}>
        {label.toUpperCase()}
      </div>
      <div style={{ flex: 1, height: 1, background: '#1E2332' }} />
    </div>
  )
}

function DailyPipelinePanel({
  allStatus,
}: {
  allStatus: Record<string, ModuleInfo>
}) {
  const [ps, setPs]               = useState<PipelineStatus | null>(null)
  const [log, setLog]             = useState<Record<string, unknown>[]>([])
  const [showLog, setShowLog]     = useState(false)
  const [actionMsg, setActionMsg] = useState('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/pipeline/status`)
      if (r.ok) setPs(await r.json())
    } catch {}
  }, [])

  const fetchLog = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/pipeline/log?n=60`)
      if (r.ok) setLog(await r.json())
    } catch {}
  }, [])

  useEffect(() => {
    fetchStatus()
    const tick = () => {
      fetchStatus()
      if (showLog) fetchLog()
    }
    pollRef.current = setInterval(tick, ps?.state === 'RUNNING' ? 5000 : 30000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [ps?.state, showLog, fetchStatus, fetchLog])

  async function runNow() {
    setActionMsg('')
    try {
      const r    = await fetch(`${API_BASE}/api/pipeline/run`, { method: 'POST' })
      const body = await r.json()
      setActionMsg(r.ok ? 'Pipeline started.' : body.detail ?? 'Already running.')
      fetchStatus()
    } catch { setActionMsg('Could not reach backend.') }
  }

  async function killPipeline() {
    setActionMsg('')
    try {
      const r    = await fetch(`${API_BASE}/api/pipeline/stop`, { method: 'POST' })
      const body = await r.json()
      setActionMsg(body.message ?? 'Stop signal sent.')
      fetchStatus()
    } catch { setActionMsg('Could not reach backend.') }
  }

  const isRunning  = ps?.state === 'RUNNING'
  const doneCount  = STAGE_ORDER.filter(id => ps?.stages?.[id]?.status === 'DONE').length

  return (
    <div style={{
      backgroundColor: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 28,
    }}>

      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <h2 style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700, letterSpacing: 2, margin: 0 }}>
          DAILY PIPELINE
        </h2>
        <span style={{
          fontSize: 10, fontWeight: 700, letterSpacing: 1,
          color: stateColor(ps?.state ?? 'IDLE'),
          border: `1px solid ${stateColor(ps?.state ?? 'IDLE')}`,
          padding: '1px 8px', borderRadius: 4,
        }}>
          {ps?.state ?? 'IDLE'}
        </span>
        <div style={{ flex: 1 }} />
        {actionMsg && <span style={{ fontSize: 10, color: '#94A3B8' }}>{actionMsg}</span>}
        {isRunning && (
          <button onClick={killPipeline} style={{
            padding: '3px 14px', borderRadius: 4,
            border: '1px solid #EF4444', backgroundColor: '#EF444422',
            color: '#EF4444', cursor: 'pointer', fontSize: 10, fontWeight: 700,
          }}>KILL</button>
        )}
        <button
          onClick={runNow} disabled={isRunning}
          style={{
            padding: '3px 14px', borderRadius: 4,
            border: `1px solid ${isRunning ? '#334155' : '#22C55E'}`,
            backgroundColor: 'transparent',
            color: isRunning ? '#334155' : '#22C55E',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            fontSize: 10, fontWeight: 700,
          }}
        >
          {isRunning ? 'Running...' : 'Run Now'}
        </button>
      </div>

      {/* Meta row */}
      <div style={{ display: 'flex', gap: 24, fontSize: 10, color: '#64748B', marginBottom: 12 }}>
        <span>Schedule: <span style={{ color: '#94A3B8' }}>Mon-Fri 18:00 IST</span></span>
        <span>Next run: <span style={{ color: '#94A3B8' }}>{ps?.next_run_ist ?? '--'}</span></span>
        <span>Last run: <span style={{ color: '#94A3B8' }}>{ps?.last_run_at ?? 'never'}</span></span>
        {isRunning && ps?.current_label && (
          <span style={{ color: '#F59E0B' }}>Running: {ps.current_label}</span>
        )}
      </div>

      {/* Progress strip — all stages coloured by section */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', gap: 2 }}>
          {STAGE_ORDER.map(id => {
            const s   = ps?.stages?.[id]
            const col = s ? stageColor(s.status) : (
              isRunning && id === ps?.current_stage ? '#F59E0B' : '#1E2332'
            )
            return (
              <div key={id} title={`${STAGE_LABELS[id]}: ${s?.status ?? 'PENDING'}`}
                style={{
                  flex: 1, height: 8, borderRadius: 2,
                  backgroundColor: col, opacity: s ? 1 : 0.4,
                  transition: 'background-color 0.4s',
                }}
              />
            )
          })}
        </div>
        <div style={{ fontSize: 9, color: '#64748B', marginTop: 4 }}>
          {doneCount}/{STAGE_ORDER.length} stages complete
        </div>
      </div>

      {/* Sectioned stage tables */}
      {PIPELINE_SECTIONS.map(section => {
        const sectionDone = section.stages.filter(id => ps?.stages?.[id]?.status === 'DONE').length
        return (
          <div key={section.id}>
            <SectionLabel label={`${section.title} — ${sectionDone}/${section.stages.length}`} />
            <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse', marginBottom: 4 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1E2332', color: '#475569' }}>
                  <th style={{ textAlign: 'left',   padding: '3px 6px', width: '32%' }}>Stage</th>
                  <th style={{ textAlign: 'center', padding: '3px 6px', width: '10%' }}>Status</th>
                  <th style={{ textAlign: 'left',   padding: '3px 6px', width: '22%' }}>Records</th>
                  <th style={{ textAlign: 'left',   padding: '3px 6px', width: '18%' }}>Coverage</th>
                  <th style={{ textAlign: 'right',  padding: '3px 6px', width: '8%'  }}>Duration</th>
                  <th style={{ textAlign: 'left',   padding: '3px 6px', width: '10%' }}>Finished</th>
                </tr>
              </thead>
              <tbody>
                {section.stages.map(id => {
                  const s      = ps?.stages?.[id]
                  const isCurr = isRunning && ps?.current_stage === id
                  const col    = isCurr ? '#F59E0B' : (s ? stageColor(s.status) : '#334155')
                  const dataKey = STAGE_STATUS_KEY[id]
                  const dataInfo = dataKey ? allStatus[dataKey] : undefined
                  return (
                    <tr key={id} style={{ borderBottom: '1px solid #1E233218' }}>
                      <td style={{ padding: '4px 6px', color: col, fontWeight: isCurr ? 700 : 400 }}>
                        {isCurr ? '> ' : ''}{STAGE_LABELS[id]}
                        {s?.error ? (
                          <span style={{ color: '#EF4444', marginLeft: 6, fontSize: 9 }}>
                            {s.error.slice(0, 50)}
                          </span>
                        ) : null}
                      </td>
                      <td style={{ padding: '4px 6px', textAlign: 'center' }}>
                        <span style={{
                          color: col, border: `1px solid ${col}`,
                          padding: '0 6px', borderRadius: 3,
                          fontSize: 9, fontWeight: 700,
                        }}>
                          {isCurr ? 'RUNNING' : (s?.status ?? 'PENDING')}
                        </span>
                      </td>
                      <td style={{ padding: '4px 6px', color: '#94A3B8', fontSize: 9 }}>
                        {dataInfo?.records ?? '--'}
                      </td>
                      <td style={{ padding: '4px 6px', color: '#64748B', fontSize: 9 }}>
                        {dataInfo?.coverage ?? dataInfo?.as_of_date ?? '--'}
                      </td>
                      <td style={{ padding: '4px 6px', textAlign: 'right', color: '#64748B' }}>
                        {s?.duration_s != null ? `${s.duration_s}s` : '--'}
                      </td>
                      <td style={{ padding: '4px 6px', color: '#64748B', fontSize: 9 }}>
                        {s?.finished_at ?? '--'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      })}

      {/* Log toggle */}
      <div style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button
          onClick={() => { setShowLog(v => !v); if (!showLog) fetchLog() }}
          style={{
            padding: '2px 10px', borderRadius: 4,
            border: '1px solid #334155', backgroundColor: 'transparent',
            color: '#64748B', cursor: 'pointer', fontSize: 10,
          }}
        >
          {showLog ? 'Hide Log' : 'Show Log'}
        </button>
        <span style={{ fontSize: 9, color: '#475569' }}>Last 60 stage entries from refresh_log.csv</span>
      </div>

      {showLog && log.length > 0 && (
        <div style={{
          marginTop: 8, backgroundColor: '#0A0D14',
          border: '1px solid #1E2332', borderRadius: 4,
          padding: 8, maxHeight: 220, overflowY: 'auto',
          fontFamily: 'monospace', fontSize: 10, color: '#94A3B8',
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 60px 50px 100px',
            gap: '0 8px', color: '#475569', marginBottom: 4, fontWeight: 700,
          }}>
            <span>Stage</span><span>Status</span><span>Dur(s)</span><span>Finished</span>
          </div>
          {log.slice().reverse().map((row, i) => {
            const st  = String(row.status ?? '')
            const col = st === 'DONE' ? '#22C55E' : st === 'FAILED' || st === 'TIMEOUT' ? '#EF4444' : '#64748B'
            return (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '1fr 60px 50px 100px',
                gap: '0 8px', borderBottom: '1px solid #1E233220', padding: '2px 0',
              }}>
                <span style={{ color: '#94A3B8' }}>{String(row.label ?? row.stage_id ?? '')}</span>
                <span style={{ color: col }}>{st}</span>
                <span style={{ color: '#64748B' }}>{String(row.duration_s ?? '--')}</span>
                <span style={{ color: '#64748B' }}>{String(row.finished_at ?? '--').slice(0, 19)}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Backfill Historical Data Panel ────────────────────────────────────────────

function BackfillPanel({
  allStatus,
  onRunComplete,
}: {
  allStatus: Record<string, ModuleInfo>
  onRunComplete: () => void
}) {
  const [running, setRunning]   = useState<string | null>(null)
  const [logs, setLogs]         = useState<Record<string, string[]>>({})
  const [openLog, setOpenLog]   = useState<string | null>(null)
  const logRef = useRef<HTMLDivElement>(null)
  const activeEs = useRef<EventSource | null>(null)

  function streamEngine(key: string, onLine: (l: string) => void, onDone: () => void) {
    activeEs.current?.close()
    const es = new EventSource(`${BASE}/api/data/run/${key}`)
    activeEs.current = es
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.ping) return
        if (data.line !== undefined) onLine(data.line as string)
        if (data.all_done) { es.close(); activeEs.current = null; onDone() }
      } catch {}
    }
    es.onerror = () => { es.close(); activeEs.current = null; onDone() }
  }

  function runEngine(key: string) {
    setRunning(key)
    setLogs(prev => ({ ...prev, [key]: [`Starting ${key}...`] }))
    setOpenLog(key)
    streamEngine(
      key,
      (line) => {
        setLogs(prev => ({ ...prev, [key]: [...(prev[key] ?? []), line] }))
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
      },
      () => { setRunning(null); onRunComplete() },
    )
  }

  function stopAll() {
    activeEs.current?.close()
    activeEs.current = null
    killBackend()
    setRunning(null)
  }

  // Map engine key to status data key
  const ENGINE_TO_STATUS: Record<string, string> = {
    results_acquisition:              'quarterly_results',
    results_acquisition_full:         'quarterly_results',
    valuation_15b:                    'valuation_scores',
    extended_financials_15b:          'valuation_scores',
    extended_financials_15b_backfill: 'valuation_scores',
    shp_acquisition:                  'shareholding',
    shp_acquisition_full:             'shareholding',
    stock_history_full:               'stock_history_cache',
  }

  const busy = running !== null

  return (
    <div style={{
      backgroundColor: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 28,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <h2 style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700, letterSpacing: 2, margin: 0 }}>
          BACKFILL HISTORICAL DATA
        </h2>
        <div style={{ flex: 1, height: 1, background: '#1E2332' }} />
        <span style={{ fontSize: 10, color: '#64748B' }}>Run manually only — not part of daily schedule</span>
        {busy && (
          <button onClick={stopAll} style={{
            padding: '3px 14px', borderRadius: 4,
            border: '1px solid #EF4444', backgroundColor: '#EF444422',
            color: '#EF4444', cursor: 'pointer', fontSize: 10, fontWeight: 700,
          }}>STOP</button>
        )}
      </div>

      <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #1E2332', color: '#475569' }}>
            <th style={{ textAlign: 'left',   padding: '3px 6px', width: '26%' }}>Engine</th>
            <th style={{ textAlign: 'left',   padding: '3px 6px', width: '28%' }}>Description</th>
            <th style={{ textAlign: 'center', padding: '3px 6px', width: '9%'  }}>Status</th>
            <th style={{ textAlign: 'left',   padding: '3px 6px', width: '19%' }}>Records</th>
            <th style={{ textAlign: 'left',   padding: '3px 6px', width: '12%' }}>Coverage</th>
            <th style={{ textAlign: 'center', padding: '3px 6px', width: '6%'  }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {BACKFILL_ENGINES.map(({ key, label, desc }) => {
            const dataKey  = ENGINE_TO_STATUS[key]
            const dataInfo = dataKey ? allStatus[dataKey] : undefined
            const isRun    = running === key
            const hasLogs  = (logs[key] ?? []).length > 0
            return (
              <>
                <tr key={key} style={{ borderBottom: '1px solid #1E233218' }}>
                  <td style={{ padding: '5px 6px', color: isRun ? '#F59E0B' : '#E2E8F0', fontWeight: 600 }}>
                    {label}
                  </td>
                  <td style={{ padding: '5px 6px', color: '#64748B' }}>{desc}</td>
                  <td style={{ padding: '5px 6px', textAlign: 'center' }}>
                    {dataInfo ? <StatusBadge status={dataInfo.status} /> : <span style={{ color: '#475569' }}>--</span>}
                  </td>
                  <td style={{ padding: '5px 6px', color: '#94A3B8', fontSize: 9 }}>
                    {dataInfo?.records ?? '--'}
                  </td>
                  <td style={{ padding: '5px 6px', color: '#64748B', fontSize: 9 }}>
                    {dataInfo?.coverage ?? dataInfo?.as_of_date ?? '--'}
                  </td>
                  <td style={{ padding: '5px 6px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: 4, justifyContent: 'center' }}>
                      <button
                        onClick={() => runEngine(key)}
                        disabled={busy}
                        style={{
                          padding: '2px 10px', borderRadius: 4,
                          border: '1px solid #22C55E',
                          backgroundColor: isRun ? '#22C55E22' : 'transparent',
                          color: '#22C55E',
                          cursor: busy ? 'not-allowed' : 'pointer',
                          fontSize: 10, fontWeight: 700,
                        }}
                      >
                        {isRun ? 'Running...' : 'Run'}
                      </button>
                      {hasLogs && (
                        <button
                          onClick={() => setOpenLog(openLog === key ? null : key)}
                          style={{
                            padding: '2px 8px', borderRadius: 4,
                            border: '1px solid #334155',
                            backgroundColor: 'transparent', color: '#64748B',
                            cursor: 'pointer', fontSize: 10,
                          }}
                        >
                          {openLog === key ? 'Hide' : 'Log'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>

                {openLog === key && hasLogs && (
                  <tr key={`${key}_log`}>
                    <td colSpan={6} style={{ padding: '0 6px 8px 6px' }}>
                      <div ref={logRef} style={{
                        backgroundColor: '#0A0D14', border: '1px solid #1E2332',
                        borderRadius: 4, padding: 8,
                        maxHeight: 160, overflowY: 'auto',
                        fontFamily: 'monospace', fontSize: 10,
                        color: '#94A3B8', whiteSpace: 'pre-wrap',
                      }}>
                        {(logs[key] ?? []).map((line, i) => (
                          <div key={i} style={{
                            color: line.startsWith('ERROR') ? '#EF4444'
                                 : line.startsWith('---')   ? '#22C55E'
                                 : '#94A3B8',
                          }}>
                            {line || ' '}
                          </div>
                        ))}
                        {isRun && <div style={{ color: '#F59E0B' }}>... running ...</div>}
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

// ── Backup Panel (Phase R1-D1) ────────────────────────────────────────────────

type BackupStatus = {
  target:          string
  drive_available: boolean
  last_run:        string | null
  last_result:     'VERIFIED' | 'FAILED' | 'NEVER_RUN'
  verified_dirs:   string[]
  schedule:        string
}

function BackupPanel() {
  const [status,    setStatus]    = useState<BackupStatus | null>(null)
  const [statusErr, setStatusErr] = useState('')
  const [running,   setRunning]   = useState(false)
  const [log,       setLog]       = useState<string[]>([])
  const [showLog,   setShowLog]   = useState(false)
  const logRef = useRef<HTMLDivElement>(null)
  const esRef  = useRef<EventSource | null>(null)

  const loadStatus = async () => {
    try {
      const r = await fetch(`${BASE}/api/data/backup/status`)
      if (r.ok) { setStatus(await r.json()); setStatusErr(''); return }
      // 404 = backend running an older build without this endpoint
      setStatusErr(r.status === 404
        ? 'Backup status endpoint not found — restart the backend (stop.ps1 / start.ps1) to load it'
        : `Status request failed (HTTP ${r.status})`)
    } catch {
      setStatusErr('Backend unreachable')
    }
  }
  useEffect(() => { loadStatus() }, [])

  const runBackup = () => {
    esRef.current?.close()
    setRunning(true)
    setLog(['Starting backup pipeline...'])
    setShowLog(true)
    const es = new EventSource(`${BASE}/api/data/run/pipeline_backup`)
    esRef.current = es
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.ping) return
        if (data.line !== undefined) {
          setLog(prev => [...prev, data.line as string])
          if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
        }
        if (data.all_done) {
          es.close(); esRef.current = null
          setRunning(false)
          loadStatus()
        }
      } catch { /* ignore */ }
    }
    es.onerror = () => { es.close(); esRef.current = null; setRunning(false); loadStatus() }
  }

  const stopBackup = () => {
    esRef.current?.close()
    esRef.current = null
    killBackend()
    setRunning(false)
  }

  const resultColor =
    status?.last_result === 'VERIFIED' ? '#22C55E'
    : status?.last_result === 'FAILED' ? '#EF4444'
    : '#64748B'

  return (
    <div style={{
      backgroundColor: '#141720', border: '1px solid #1E2332',
      borderRadius: 6, padding: 16, marginBottom: 28,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <h2 style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 700, letterSpacing: 2, margin: 0 }}>
          DATA BACKUP
        </h2>
        <div style={{ flex: 1, height: 1, background: '#1E2332' }} />
        <span style={{ fontSize: 10, color: '#64748B' }}>
          Mirrors raw data to external drive — also runs {status?.schedule?.toLowerCase() ?? 'weekly'}
        </span>
        {running && (
          <button onClick={stopBackup} style={{
            padding: '3px 14px', borderRadius: 4,
            border: '1px solid #EF4444', backgroundColor: '#EF444422',
            color: '#EF4444', cursor: 'pointer', fontSize: 10, fontWeight: 700,
          }}>STOP</button>
        )}
      </div>

      {/* Status endpoint unavailable — distinct from drive-not-found */}
      {statusErr && (
        <div style={{
          marginBottom: 10, padding: '6px 12px', borderRadius: 4, fontSize: 10,
          border: '1px solid #F59E0B44', background: '#F59E0B11', color: '#F59E0B',
        }}>
          {statusErr}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
        {/* Drive status — three states: unknown / connected / not found */}
        <div style={{ fontSize: 11 }}>
          <span style={{ color: '#64748B' }}>Target: </span>
          <span style={{ color: '#94A3B8', fontFamily: 'monospace' }}>{status?.target ?? 'F:\\Projects\\fii-dii-backup'}</span>
          {status === null ? (
            <span style={{
              marginLeft: 8, fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
              color: '#64748B', border: '1px solid #64748B55', background: '#64748B15',
            }}>STATUS UNKNOWN</span>
          ) : (
            <span style={{
              marginLeft: 8, fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
              color:      status.drive_available ? '#22C55E' : '#EF4444',
              border:     `1px solid ${status.drive_available ? '#22C55E' : '#EF4444'}55`,
              background: (status.drive_available ? '#22C55E' : '#EF4444') + '15',
            }}>
              {status.drive_available ? 'DRIVE CONNECTED' : 'DRIVE NOT FOUND'}
            </span>
          )}
        </div>

        {/* Last run */}
        <div style={{ fontSize: 11 }}>
          <span style={{ color: '#64748B' }}>Last backup: </span>
          <span style={{ color: resultColor, fontWeight: 700 }}>
            {status?.last_result === 'NEVER_RUN' ? 'never run' : `${status?.last_result}`}
          </span>
          {status?.last_run && <span style={{ color: '#64748B' }}> · {status.last_run}</span>}
        </div>

        <div style={{ flex: 1 }} />

        <button
          onClick={runBackup}
          disabled={running || !status?.drive_available}
          title={
            status === null ? (statusErr || 'Waiting for backup status...')
            : !status.drive_available ? 'Plug in the external drive first'
            : 'Mirror + verify raw data now'
          }
          style={{
            padding: '5px 18px', borderRadius: 4,
            border: '1px solid #22C55E',
            backgroundColor: running ? '#22C55E22' : 'transparent',
            color: running || !status?.drive_available ? '#33415588' : '#22C55E',
            cursor: running || !status?.drive_available ? 'not-allowed' : 'pointer',
            fontSize: 11, fontWeight: 700,
          }}
        >
          {running ? 'Backing up...' : 'Run Backup Now'}
        </button>
        {log.length > 0 && !running && (
          <button onClick={() => setShowLog(v => !v)} style={{
            padding: '5px 12px', borderRadius: 4, border: '1px solid #334155',
            backgroundColor: 'transparent', color: '#64748B', cursor: 'pointer', fontSize: 10,
          }}>{showLog ? 'Hide Log' : 'Log'}</button>
        )}
      </div>

      {/* Verified dirs from last run */}
      {(status?.verified_dirs?.length ?? 0) > 0 && (
        <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {status!.verified_dirs.map((d, i) => (
            <span key={i} style={{
              fontSize: 9, padding: '2px 8px', borderRadius: 3,
              color: d.includes('MISMATCH') ? '#EF4444' : '#64748B',
              border: '1px solid #1E2332', background: '#0A0D14', fontFamily: 'monospace',
            }}>{d}</span>
          ))}
        </div>
      )}

      {/* Live stream log */}
      {showLog && log.length > 0 && (
        <div ref={logRef} style={{
          marginTop: 10, backgroundColor: '#0A0D14', border: '1px solid #1E2332',
          borderRadius: 4, padding: 8, maxHeight: 200, overflowY: 'auto',
          fontFamily: 'monospace', fontSize: 10, color: '#94A3B8', whiteSpace: 'pre-wrap',
        }}>
          {log.map((line, i) => (
            <div key={i} style={{
              color: line.includes('ERROR') || line.includes('FAIL') || line.includes('MISMATCH') ? '#EF4444'
                   : line.includes('VERIFIED') || line.includes('COMPLETE') ? '#22C55E'
                   : line.startsWith('---') ? '#3B82F6'
                   : '#94A3B8',
            }}>{line || ' '}</div>
          ))}
          {running && <div style={{ color: '#F59E0B' }}>... running ...</div>}
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export function DataControlPage() {
  const { data: status, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['data_status'],
    queryFn:  fetchDataStatus,
    staleTime: 0,
    refetchOnWindowFocus: false,
  })

  // Kill any stale subprocess from a previous session on page load
  useEffect(() => { killBackend() }, [])

  if (isLoading) return (
    <div style={{ color: '#64748B', padding: 40, textAlign: 'center' }}>Scanning data modules...</div>
  )

  const acquisition  = (status?.acquisition  ?? {}) as Record<string, ModuleInfo>
  const intelligence = (status?.intelligence ?? {}) as Record<string, ModuleInfo>
  const allStatus    = { ...acquisition, ...intelligence }

  const acqOk  = Object.values(acquisition).filter(m => m.status === 'OK').length
  const intOk  = Object.values(intelligence).filter(m => m.status === 'OK').length
  const acqLen = Object.keys(acquisition).length
  const intLen = Object.keys(intelligence).length
  const total    = acqLen + intLen
  const totalOk  = acqOk + intOk
  const pct      = total > 0 ? Math.round((totalOk / total) * 100) : 0

  return (
    <div style={{ maxWidth: 1200 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
          DATA CONTROL
        </h1>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          style={{
            padding: '4px 14px', borderRadius: 4,
            border: '1px solid #334155', backgroundColor: 'transparent',
            color: isFetching ? '#22C55E' : '#64748B',
            cursor: isFetching ? 'not-allowed' : 'pointer',
            fontSize: 11, transition: 'color 0.2s',
          }}
        >
          {isFetching ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      {/* Overall health tile */}
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
            Platform Health — {totalOk}/{total} data modules operational
          </div>
          <div style={{ height: 8, backgroundColor: '#1E2332', borderRadius: 4 }}>
            <div style={{
              width: `${pct}%`, height: 8, borderRadius: 4,
              backgroundColor: pct === 100 ? '#22C55E' : pct > 70 ? '#F59E0B' : '#EF4444',
            }} />
          </div>
        </div>
        <div style={{ fontSize: 11, color: '#64748B', textAlign: 'right' }}>
          <div>Acquisition: {acqOk}/{acqLen}</div>
          <div>Intelligence: {intOk}/{intLen}</div>
        </div>
      </div>

      {/* Daily Pipeline — 3 sections: Acquisition + Intelligence + Backfill */}
      <DailyPipelinePanel allStatus={allStatus} />

      <BackfillPanel allStatus={allStatus} onRunComplete={refetch} />

      {/* Data Backup — manual trigger for backup.ps1 (Phase R1-D1) */}
      <BackupPanel />

    </div>
  )
}
