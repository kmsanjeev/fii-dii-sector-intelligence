import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API = 'http://localhost:8001'

// ── Types ─────────────────────────────────────────────────────────────────────

type UniverseStats = {
  total_symbols: number
  label_counts:  Record<string, number>
  sector_list:   string[]
  rotation_map:  Record<string, string>
}

type ScreenRow = {
  symbol:              string
  sector:              string | null
  label:               string | null
  bull_run_score:      number | null
  ml_bull_run_score:   number | null
  accumulation_score:  number | null
  ret_30d:             number | null
  ret_90d:             number | null
  ret_365d:            number | null
  confidence_score_12m: number | null
  confidence_label:    string | null
  promoter_pct:        number | null
  fii_delta:           number | null
  conviction_signal:   string | null
  rotation_signal:     string | null
  close_now:           number | null
}

type ScreenResult = { results: ScreenRow[]; total: number; returned: number }

type CompareData = { data: Record<string, Record<string, number | string | null> | null>; symbols: string[]; not_found: string[] }

type Note = { symbol: string; content: string; tags: string[]; rating: number; created_at: string; updated_at: string }
type NoteIndex = { symbol: string; rating: number; tags: string[]; updated_at: string; excerpt: string }

// ── API ───────────────────────────────────────────────────────────────────────

const fetchStats = (): Promise<UniverseStats> =>
  fetch(`${API}/api/research/universe/stats`).then(r => r.json())

const fetchNotesList = (): Promise<{ notes: NoteIndex[] }> =>
  fetch(`${API}/api/research/notes`).then(r => r.json())

const fetchNote = (sym: string): Promise<Note> =>
  fetch(`${API}/api/research/notes/${sym}`).then(r => { if (!r.ok) throw new Error('not found'); return r.json() })

async function runScreen(filters: object): Promise<ScreenResult> {
  const r = await fetch(`${API}/api/research/screen`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters),
  })
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Screen failed')
  return r.json()
}

async function fetchCompare(symbols: string[]): Promise<CompareData> {
  const r = await fetch(`${API}/api/research/compare?symbols=${symbols.join(',')}`)
  if (!r.ok) throw new Error((await r.json()).detail ?? 'Compare failed')
  return r.json()
}

async function saveNote(sym: string, content: string, tags: string[], rating: number): Promise<Note> {
  const r = await fetch(`${API}/api/research/notes/${sym}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, tags, rating }),
  })
  if (!r.ok) throw new Error('Save failed')
  return r.json()
}

async function deleteNote(sym: string): Promise<void> {
  await fetch(`${API}/api/research/notes/${sym}`, { method: 'DELETE' })
}

// ── Shared style helpers ──────────────────────────────────────────────────────

const inp: React.CSSProperties = {
  background: '#0A0D14', border: '1px solid #1E2332', borderRadius: 4,
  color: '#E2E8F0', padding: '5px 10px', fontSize: 11, outline: 'none',
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

const ROT_COLORS: Record<string, string> = {
  EARLY_ROTATION: '#22C55E', RISING: '#10B981', HOLD: '#64748B',
  DECLINING: '#EF4444', EXITING: '#DC2626',
}

function LabelBadge({ label }: { label: string | null }) {
  if (!label) return <span style={{ color: '#334155' }}>--</span>
  const c = LABEL_COLORS[label] ?? '#64748B'
  return (
    <span style={{
      background: `${c}22`, color: c, border: `1px solid ${c}44`,
      borderRadius: 3, padding: '1px 6px', fontSize: 9, fontWeight: 700,
    }}>{label.replace('_', ' ')}</span>
  )
}

function RetCell({ val }: { val: number | null }) {
  if (val == null) return <span style={{ color: '#1E2332' }}>--</span>
  const c = val > 0 ? '#22C55E' : val < 0 ? '#EF4444' : '#64748B'
  return <span style={{ color: c }}>{val > 0 ? '+' : ''}{val.toFixed(1)}%</span>
}

function Stars({ n, onChange }: { n: number; onChange?: (v: number) => void }) {
  return (
    <span>
      {[1, 2, 3, 4, 5].map(i => (
        <span key={i}
          onClick={() => onChange?.(i)}
          style={{ cursor: onChange ? 'pointer' : 'default', color: i <= n ? '#F59E0B' : '#1E2332', fontSize: 14 }}>
          *
        </span>
      ))}
    </span>
  )
}

function TabBtn({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      padding: '7px 20px', borderRadius: 4, fontSize: 11, fontWeight: 700, cursor: 'pointer',
      border: '1px solid', borderColor: active ? '#22C55E' : '#1E2332',
      background: active ? '#22C55E22' : 'transparent', color: active ? '#22C55E' : '#64748B',
    }}>{label}</button>
  )
}

function NumInput({ label, value, onChange, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string
}) {
  return (
    <div style={{ minWidth: 80 }}>
      <div style={{ color: '#64748B', fontSize: 9, marginBottom: 3 }}>{label}</div>
      <input type="number" value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder ?? ''} style={{ ...inp, width: 80 }} />
    </div>
  )
}

// ── Export helper ─────────────────────────────────────────────────────────────

function exportCsv(rows: ScreenRow[], filename: string) {
  if (!rows.length) return
  const keys = Object.keys(rows[0]) as (keyof ScreenRow)[]
  const header = keys.join(',')
  const body = rows.map(r => keys.map(k => {
    const v = r[k]
    return v == null ? '' : typeof v === 'string' && v.includes(',') ? `"${v}"` : String(v)
  }).join(',')).join('\n')
  const blob = new Blob([header + '\n' + body], { type: 'text/csv' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
  a.download = filename; a.click()
}

// ── SCREENER TAB ──────────────────────────────────────────────────────────────

type ScreenFilters = {
  labels: string[]; sectors: string[]; indices: string[]
  conviction_signal: string; fii_delta_dir: string
  min_score: string; max_score: string
  min_ml: string;    max_ml: string
  min_ret_30d: string; max_ret_30d: string
  min_ret_90d: string; max_ret_90d: string
  min_ret_365d: string; max_ret_365d: string
  min_confidence: string
  min_promoter_pct: string
  sort_by: string; sort_dir: string
}

const DEFAULT_FILTERS: ScreenFilters = {
  labels: [], sectors: [], indices: [], conviction_signal: '', fii_delta_dir: '',
  min_score: '', max_score: '', min_ml: '', max_ml: '',
  min_ret_30d: '', max_ret_30d: '', min_ret_90d: '', max_ret_90d: '',
  min_ret_365d: '', max_ret_365d: '', min_confidence: '', min_promoter_pct: '',
  sort_by: 'bull_run_score', sort_dir: 'desc',
}

function buildPayload(f: ScreenFilters) {
  const p: Record<string, unknown> = { sort_by: f.sort_by, sort_dir: f.sort_dir, limit: 500 }
  if (f.labels.length)    p.labels           = f.labels
  if (f.sectors.length)   p.sectors          = f.sectors
  if (f.indices.length)   p.indices          = f.indices
  if (f.conviction_signal) p.conviction_signal = f.conviction_signal
  if (f.fii_delta_dir)    p.fii_delta_dir    = f.fii_delta_dir
  const num = (v: string) => v !== '' ? parseFloat(v) : undefined
  if (num(f.min_score)        != null) p.min_score        = num(f.min_score)
  if (num(f.max_score)        != null) p.max_score        = num(f.max_score)
  if (num(f.min_ml)           != null) p.min_ml           = num(f.min_ml)
  if (num(f.max_ml)           != null) p.max_ml           = num(f.max_ml)
  if (num(f.min_ret_30d)      != null) p.min_ret_30d      = num(f.min_ret_30d)
  if (num(f.max_ret_30d)      != null) p.max_ret_30d      = num(f.max_ret_30d)
  if (num(f.min_ret_90d)      != null) p.min_ret_90d      = num(f.min_ret_90d)
  if (num(f.max_ret_90d)      != null) p.max_ret_90d      = num(f.max_ret_90d)
  if (num(f.min_ret_365d)     != null) p.min_ret_365d     = num(f.min_ret_365d)
  if (num(f.max_ret_365d)     != null) p.max_ret_365d     = num(f.max_ret_365d)
  if (num(f.min_confidence)   != null) p.min_confidence   = num(f.min_confidence)
  if (num(f.min_promoter_pct) != null) p.min_promoter_pct = num(f.min_promoter_pct)
  return p
}

function MultiChip({ options, selected, onChange, label }: {
  options: string[]; selected: string[]; onChange: (v: string[]) => void; label: string
}) {
  const toggle = (v: string) =>
    onChange(selected.includes(v) ? selected.filter(x => x !== v) : [...selected, v])
  return (
    <div>
      <div style={{ color: '#64748B', fontSize: 9, marginBottom: 5 }}>{label}</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {options.map(o => {
          const active = selected.includes(o)
          const c = LABEL_COLORS[o] ?? '#64748B'
          return (
            <span key={o} onClick={() => toggle(o)} style={{
              padding: '2px 8px', borderRadius: 3, fontSize: 9, fontWeight: 700,
              cursor: 'pointer', border: `1px solid ${active ? c : '#1E2332'}`,
              background: active ? `${c}22` : 'transparent', color: active ? c : '#475569',
            }}>{o.replace('_', ' ')}</span>
          )
        })}
      </div>
    </div>
  )
}

function ScreenerTab({ stats }: { stats: UniverseStats }) {
  const [filters, setFilters] = useState<ScreenFilters>(DEFAULT_FILTERS)
  const [open, setOpen] = useState(true)
  const [result, setResult] = useState<ScreenResult | null>(null)
  const [err, setErr] = useState('')

  const mut = useMutation<ScreenResult, Error, void>({
    mutationFn: () => { setErr(''); return runScreen(buildPayload(filters)) },
    onSuccess:  d => setResult(d),
    onError:    e => setErr(e.message),
  })

  const set = (k: keyof ScreenFilters) => (v: unknown) =>
    setFilters(f => ({ ...f, [k]: v }))

  const activeCount = [
    filters.labels.length, filters.sectors.length, filters.indices.length,
    filters.conviction_signal, filters.fii_delta_dir,
    filters.min_score, filters.max_score, filters.min_ml, filters.max_ml,
    filters.min_ret_30d, filters.max_ret_30d, filters.min_ret_90d, filters.max_ret_90d,
    filters.min_ret_365d, filters.max_ret_365d, filters.min_confidence, filters.min_promoter_pct,
  ].filter(Boolean).length

  const rows = result?.results ?? []

  return (
    <div>
      {/* Filter panel */}
      <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 6, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', cursor: 'pointer' }}
          onClick={() => setOpen(o => !o)}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>FILTERS</span>
            {activeCount > 0 && (
              <span style={{ background: '#22C55E22', color: '#22C55E', borderRadius: 10, padding: '1px 8px', fontSize: 9, fontWeight: 700 }}>
                {activeCount} active
              </span>
            )}
          </div>
          <span style={{ color: '#475569', fontSize: 11 }}>{open ? 'v' : '>'}</span>
        </div>

        {open && (
          <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Labels + Indices */}
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              <MultiChip label="LABEL" options={['STRONG_CANDIDATE','EMERGING','WATCHLIST','NEUTRAL','AVOID']}
                selected={filters.labels} onChange={set('labels')} />
              <MultiChip label="INDEX" options={['NIFTY50','NIFTY100','NIFTY200','NIFTY500','NIFTY_MIDCAP_100']}
                selected={filters.indices} onChange={set('indices')} />
            </div>

            {/* Sectors */}
            <div>
              <div style={{ color: '#64748B', fontSize: 9, marginBottom: 5 }}>SECTOR</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {stats.sector_list.map(s => {
                  const active = filters.sectors.includes(s)
                  const rot = stats.rotation_map[s]
                  const rc = ROT_COLORS[rot ?? ''] ?? '#1E2332'
                  return (
                    <span key={s} onClick={() => {
                      const next = active ? filters.sectors.filter(x => x !== s) : [...filters.sectors, s]
                      set('sectors')(next)
                    }} style={{
                      padding: '2px 8px', borderRadius: 3, fontSize: 9, fontWeight: 600,
                      cursor: 'pointer',
                      border: `1px solid ${active ? '#22C55E' : rc}`,
                      background: active ? '#22C55E22' : 'transparent',
                      color: active ? '#22C55E' : '#475569',
                    }}>
                      {s}
                    </span>
                  )
                })}
              </div>
            </div>

            {/* Numeric ranges */}
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <NumInput label="SCORE MIN"    value={filters.min_score}    onChange={set('min_score')} placeholder="0" />
              <NumInput label="SCORE MAX"    value={filters.max_score}    onChange={set('max_score')} placeholder="100" />
              <NumInput label="ML MIN"       value={filters.min_ml}       onChange={set('min_ml')} />
              <NumInput label="ML MAX"       value={filters.max_ml}       onChange={set('max_ml')} />
              <NumInput label="30d RET MIN%" value={filters.min_ret_30d}  onChange={set('min_ret_30d')} />
              <NumInput label="30d RET MAX%" value={filters.max_ret_30d}  onChange={set('max_ret_30d')} />
              <NumInput label="90d RET MIN%" value={filters.min_ret_90d}  onChange={set('min_ret_90d')} />
              <NumInput label="90d RET MAX%" value={filters.max_ret_90d}  onChange={set('max_ret_90d')} />
              <NumInput label="365d RET MIN%"value={filters.min_ret_365d} onChange={set('min_ret_365d')} />
              <NumInput label="365d RET MAX%"value={filters.max_ret_365d} onChange={set('max_ret_365d')} />
              <NumInput label="CONFIDENCE MIN" value={filters.min_confidence} onChange={set('min_confidence')} />
              <NumInput label="PROMOTER% MIN"  value={filters.min_promoter_pct} onChange={set('min_promoter_pct')} />
            </div>

            {/* Categorical */}
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div>
                <div style={{ color: '#64748B', fontSize: 9, marginBottom: 3 }}>FII DELTA</div>
                <select value={filters.fii_delta_dir}
                  onChange={e => set('fii_delta_dir')(e.target.value)}
                  style={{ ...inp, width: 130 }}>
                  <option value="">Any</option>
                  <option value="positive">FII Buying (+)</option>
                  <option value="negative">FII Selling (-)</option>
                </select>
              </div>
              <div>
                <div style={{ color: '#64748B', fontSize: 9, marginBottom: 3 }}>CONVICTION</div>
                <select value={filters.conviction_signal}
                  onChange={e => set('conviction_signal')(e.target.value)}
                  style={{ ...inp, width: 130 }}>
                  <option value="">Any</option>
                  <option value="BUYING">BUYING</option>
                  <option value="SELLING">SELLING</option>
                  <option value="STABLE">STABLE</option>
                </select>
              </div>
              <div>
                <div style={{ color: '#64748B', fontSize: 9, marginBottom: 3 }}>SORT BY</div>
                <select value={filters.sort_by} onChange={e => set('sort_by')(e.target.value)}
                  style={{ ...inp, width: 160 }}>
                  <option value="bull_run_score">Bull Run Score</option>
                  <option value="ml_bull_run_score">ML Score</option>
                  <option value="ret_30d">30d Return</option>
                  <option value="ret_90d">90d Return</option>
                  <option value="ret_365d">365d Return</option>
                  <option value="confidence_score_12m">Confidence Score</option>
                  <option value="fii_delta">FII Delta</option>
                  <option value="promoter_pct">Promoter %</option>
                </select>
              </div>
              <div>
                <div style={{ color: '#64748B', fontSize: 9, marginBottom: 3 }}>DIRECTION</div>
                <select value={filters.sort_dir} onChange={e => set('sort_dir')(e.target.value)}
                  style={{ ...inp, width: 90 }}>
                  <option value="desc">High First</option>
                  <option value="asc">Low First</option>
                </select>
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button onClick={() => mut.mutate()} disabled={mut.isPending} style={{
                padding: '7px 22px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                border: '1px solid #22C55E', background: 'transparent',
                color: mut.isPending ? '#334155' : '#22C55E', cursor: mut.isPending ? 'not-allowed' : 'pointer',
              }}>
                {mut.isPending ? 'Screening...' : 'Screen'}
              </button>
              <button onClick={() => { setFilters(DEFAULT_FILTERS); setResult(null) }} style={{
                padding: '7px 16px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                border: '1px solid #1E2332', background: 'transparent', color: '#475569', cursor: 'pointer',
              }}>
                Clear
              </button>
              {result && (
                <span style={{ color: '#64748B', fontSize: 10 }}>
                  {result.total} symbols matched, showing {result.returned}
                </span>
              )}
              {rows.length > 0 && (
                <button onClick={() => exportCsv(rows, 'screen_results.csv')} style={{
                  padding: '5px 14px', borderRadius: 4, fontSize: 10, fontWeight: 700,
                  border: '1px solid #1E2332', background: 'transparent', color: '#64748B', cursor: 'pointer',
                  marginLeft: 'auto',
                }}>
                  Export CSV
                </button>
              )}
            </div>
            {err && <span style={{ color: '#EF4444', fontSize: 11 }}>{err}</span>}
          </div>
        )}
      </div>

      {/* Results */}
      {rows.length > 0 && (
        <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 1000 }}>
              <thead>
                <tr>
                  <th style={th}>Symbol</th>
                  <th style={th}>Label</th>
                  <th style={{ ...th, textAlign: 'right' }}>Score</th>
                  <th style={{ ...th, textAlign: 'right' }}>ML</th>
                  <th style={{ ...th, textAlign: 'right' }}>+30d</th>
                  <th style={{ ...th, textAlign: 'right' }}>+90d</th>
                  <th style={{ ...th, textAlign: 'right' }}>+365d</th>
                  <th style={{ ...th, textAlign: 'right' }}>Conf</th>
                  <th style={{ ...th, textAlign: 'right' }}>FII Δ</th>
                  <th style={{ ...th, textAlign: 'right' }}>Prom%</th>
                  <th style={th}>Conviction</th>
                  <th style={th}>Rotation</th>
                  <th style={th}>Sector</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => {
                  const rotC = ROT_COLORS[r.rotation_signal ?? ''] ?? '#475569'
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid #1E233210' }}>
                      <td style={{ ...td, fontWeight: 700 }}>
                        <a href={`/stocks/${r.symbol}`}
                          style={{ color: '#E2E8F0', textDecoration: 'none' }}
                          onMouseOver={e => (e.currentTarget.style.color = '#22C55E')}
                          onMouseOut={e  => (e.currentTarget.style.color = '#E2E8F0')}>
                          {r.symbol}
                        </a>
                      </td>
                      <td style={td}><LabelBadge label={r.label} /></td>
                      <td style={{ ...td, textAlign: 'right', color: '#E2E8F0', fontWeight: 700 }}>
                        {r.bull_run_score?.toFixed(0) ?? '--'}
                      </td>
                      <td style={{ ...td, textAlign: 'right', color: '#94A3B8' }}>
                        {r.ml_bull_run_score?.toFixed(0) ?? '--'}
                      </td>
                      <td style={{ ...td, textAlign: 'right' }}><RetCell val={r.ret_30d} /></td>
                      <td style={{ ...td, textAlign: 'right' }}><RetCell val={r.ret_90d} /></td>
                      <td style={{ ...td, textAlign: 'right' }}><RetCell val={r.ret_365d} /></td>
                      <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                        {r.confidence_score_12m?.toFixed(0) ?? '--'}
                      </td>
                      <td style={{ ...td, textAlign: 'right' }}>
                        {r.fii_delta != null ? (
                          <span style={{ color: r.fii_delta > 0 ? '#22C55E' : '#EF4444' }}>
                            {r.fii_delta > 0 ? '+' : ''}{r.fii_delta.toFixed(2)}
                          </span>
                        ) : <span style={{ color: '#334155' }}>--</span>}
                      </td>
                      <td style={{ ...td, textAlign: 'right', color: '#64748B' }}>
                        {r.promoter_pct?.toFixed(1) ?? '--'}
                      </td>
                      <td style={{ ...td, color: '#64748B', fontSize: 10 }}>{r.conviction_signal ?? '--'}</td>
                      <td style={{ ...td }}>
                        {r.rotation_signal ? (
                          <span style={{ color: rotC, fontSize: 9, fontWeight: 700 }}>{r.rotation_signal}</span>
                        ) : <span style={{ color: '#334155' }}>--</span>}
                      </td>
                      <td style={{ ...td, color: '#475569', fontSize: 10 }}>{r.sector ?? '--'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!result && !mut.isPending && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332', borderRadius: 6,
          padding: 60, textAlign: 'center', color: '#334155', fontSize: 12,
        }}>
          Set filters above and click Screen. No filters = full 2400-symbol universe.
        </div>
      )}
    </div>
  )
}

// ── COMPARE TAB ───────────────────────────────────────────────────────────────

const COMPARE_GROUPS = [
  {
    label: 'Intelligence',
    metrics: [
      { key: 'label',            label: 'Label',          fmt: 'label' },
      { key: 'bull_run_score',   label: 'Bull Run Score', fmt: 'num0' },
      { key: 'ml_bull_run_score',label: 'ML Score',       fmt: 'num0' },
      { key: 'accumulation_score',label:'Accumulation',   fmt: 'num0' },
    ],
  },
  {
    label: 'Price Performance',
    metrics: [
      { key: 'close_now',  label: 'Price (LTP)',  fmt: 'num2' },
      { key: 'ret_30d',    label: '30d Return',   fmt: 'pct'  },
      { key: 'ret_60d',    label: '60d Return',   fmt: 'pct'  },
      { key: 'ret_90d',    label: '90d Return',   fmt: 'pct'  },
      { key: 'ret_365d',   label: '365d Return',  fmt: 'pct'  },
      { key: 'vol_ratio',  label: 'Volume Ratio', fmt: 'num2' },
    ],
  },
  {
    label: 'Shareholding',
    metrics: [
      { key: 'promoter_pct',    label: 'Promoter %',    fmt: 'num1' },
      { key: 'fii_pct',         label: 'FII %',         fmt: 'num1' },
      { key: 'dii_pct',         label: 'DII %',         fmt: 'num1' },
      { key: 'promoter_delta',  label: 'Promoter QoQ',  fmt: 'delta'},
      { key: 'fii_delta',       label: 'FII QoQ',       fmt: 'delta'},
      { key: 'conviction_signal',label:'Conviction',    fmt: 'str'  },
    ],
  },
  {
    label: 'Corporate & Sector',
    metrics: [
      { key: 'confidence_score_12m', label: 'Corp Confidence', fmt: 'num0' },
      { key: 'confidence_label',     label: 'Conf Label',      fmt: 'str'  },
      { key: 'rotation_signal',      label: 'Rotation Signal', fmt: 'str'  },
      { key: 'combined_score',       label: 'Rotation Score',  fmt: 'num1' },
      { key: 'sector',               label: 'Sector',          fmt: 'str'  },
    ],
  },
]

function fmtCell(v: number | string | null, fmt: string): React.ReactNode {
  if (v == null) return <span style={{ color: '#334155' }}>--</span>
  if (fmt === 'label') return <LabelBadge label={String(v)} />
  if (fmt === 'pct') {
    const n = Number(v)
    const c = n > 0 ? '#22C55E' : n < 0 ? '#EF4444' : '#64748B'
    return <span style={{ color: c, fontWeight: 700 }}>{n > 0 ? '+' : ''}{n.toFixed(1)}%</span>
  }
  if (fmt === 'delta') {
    const n = Number(v)
    const c = n > 0 ? '#22C55E' : n < 0 ? '#EF4444' : '#64748B'
    return <span style={{ color: c }}>{n > 0 ? '+' : ''}{n.toFixed(2)}</span>
  }
  if (fmt === 'num0') return <span style={{ color: '#E2E8F0', fontWeight: 700 }}>{Number(v).toFixed(0)}</span>
  if (fmt === 'num1') return <span style={{ color: '#94A3B8' }}>{Number(v).toFixed(1)}</span>
  if (fmt === 'num2') return <span style={{ color: '#94A3B8' }}>{Number(v).toFixed(2)}</span>
  const rotC = ROT_COLORS[String(v)] ?? '#64748B'
  const isRot = ['EARLY_ROTATION','RISING','HOLD','DECLINING','EXITING'].includes(String(v))
  return <span style={{ color: isRot ? rotC : '#94A3B8', fontSize: 10 }}>{String(v)}</span>
}

function CompareTab() {
  const [input, setInput] = useState('')
  const [symbols, setSymbols] = useState<string[]>([])
  const [data, setData] = useState<CompareData | null>(null)
  const [err, setErr] = useState('')

  const mut = useMutation<CompareData, Error, string[]>({
    mutationFn: s => { setErr(''); return fetchCompare(s) },
    onSuccess:  d => setData(d),
    onError:    e => setErr(e.message),
  })

  const addSymbol = () => {
    const s = input.trim().toUpperCase()
    if (!s || symbols.includes(s) || symbols.length >= 8) return
    const next = [...symbols, s]; setSymbols(next); setInput('')
    if (next.length >= 2) mut.mutate(next)
  }

  const removeSymbol = (s: string) => {
    const next = symbols.filter(x => x !== s); setSymbols(next)
    if (next.length >= 2) mut.mutate(next); else setData(null)
  }

  const colW = symbols.length ? `${Math.floor(60 / symbols.length)}%` : '20%'

  return (
    <div>
      {/* Symbol input */}
      <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16, marginBottom: 16 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, letterSpacing: 2, marginBottom: 12 }}>
          COMPARE SYMBOLS (up to 8)
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {symbols.map(s => (
            <span key={s} style={{
              background: '#22C55E22', color: '#22C55E', border: '1px solid #22C55E44',
              borderRadius: 4, padding: '3px 10px', fontSize: 11, fontWeight: 700,
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              {s}
              <span onClick={() => removeSymbol(s)} style={{ cursor: 'pointer', color: '#475569' }}>x</span>
            </span>
          ))}
          {symbols.length < 8 && (
            <>
              <input value={input} onChange={e => setInput(e.target.value.toUpperCase())}
                onKeyDown={e => e.key === 'Enter' && addSymbol()}
                placeholder="RELIANCE" style={{ ...inp, width: 120 }} />
              <button onClick={addSymbol} style={{
                padding: '5px 14px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                border: '1px solid #22C55E', background: 'transparent', color: '#22C55E', cursor: 'pointer',
              }}>+ Add</button>
            </>
          )}
        </div>
        {err && <div style={{ color: '#EF4444', fontSize: 11, marginTop: 8 }}>{err}</div>}
        {data?.not_found?.length ? (
          <div style={{ color: '#F59E0B', fontSize: 10, marginTop: 6 }}>
            Not in universe: {data.not_found.join(', ')}
          </div>
        ) : null}
      </div>

      {/* Comparison table */}
      {data && symbols.length >= 2 && (
        <div style={{ background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ ...th, width: '25%' }}>Metric</th>
                  {symbols.map(s => (
                    <th key={s} style={{ ...th, textAlign: 'right', width: colW, color: '#E2E8F0' }}>{s}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {COMPARE_GROUPS.map(grp => (
                  <>
                    <tr key={grp.label}>
                      <td colSpan={symbols.length + 1} style={{
                        padding: '10px 10px 4px', fontSize: 9, fontWeight: 700,
                        color: '#64748B', letterSpacing: 2, background: '#0A0D14',
                      }}>
                        {grp.label.toUpperCase()}
                      </td>
                    </tr>
                    {grp.metrics.map(m => (
                      <tr key={m.key} style={{ borderBottom: '1px solid #1E233210' }}>
                        <td style={{ ...td, color: '#64748B' }}>{m.label}</td>
                        {symbols.map(s => (
                          <td key={s} style={{ ...td, textAlign: 'right' }}>
                            {fmtCell(data.data[s]?.[m.key] ?? null, m.fmt)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {(!data || symbols.length < 2) && (
        <div style={{
          background: '#141720', border: '1px solid #1E2332', borderRadius: 6,
          padding: 60, textAlign: 'center', color: '#334155', fontSize: 12,
        }}>
          Add at least 2 symbols to compare.
        </div>
      )}
    </div>
  )
}

// ── NOTES TAB ─────────────────────────────────────────────────────────────────

function NotesTab() {
  const qc = useQueryClient()
  const [selectedSym, setSelectedSym] = useState<string | null>(null)
  const [content, setContent]         = useState('')
  const [tags, setTags]               = useState<string[]>([])
  const [tagInput, setTagInput]       = useState('')
  const [rating, setRating]           = useState(0)
  const [search, setSearch]           = useState('')
  const [msg, setMsg]                 = useState('')

  const { data: list } = useQuery({ queryKey: ['notes-list'], queryFn: fetchNotesList })

  const selectNote = async (sym: string) => {
    setSelectedSym(sym)
    setMsg('')
    try {
      const note = await fetchNote(sym)
      setContent(note.content)
      setTags(note.tags)
      setRating(note.rating)
    } catch {
      setContent(''); setTags([]); setRating(0)
    }
  }

  const newNote = () => {
    const sym = prompt('Symbol:')?.trim().toUpperCase()
    if (!sym) return
    setSelectedSym(sym); setContent(''); setTags([]); setRating(0); setMsg('')
  }

  const saveMut = useMutation({
    mutationFn: () => saveNote(selectedSym!, content, tags, rating),
    onSuccess:  () => { setMsg('Saved.'); qc.invalidateQueries({ queryKey: ['notes-list'] }) },
    onError:    e  => setMsg((e as Error).message),
  })

  const deleteMut = useMutation({
    mutationFn: () => deleteNote(selectedSym!),
    onSuccess:  () => {
      setSelectedSym(null); setContent(''); setMsg('')
      qc.invalidateQueries({ queryKey: ['notes-list'] })
    },
  })

  const addTag = () => {
    const t = tagInput.trim().toLowerCase()
    if (t && !tags.includes(t)) { setTags(prev => [...prev, t]); setTagInput('') }
  }

  const filtered = (list?.notes ?? []).filter(n =>
    n.symbol.includes(search.toUpperCase()) ||
    n.tags.some(t => t.includes(search.toLowerCase()))
  )

  return (
    <div style={{ display: 'flex', gap: 16, minHeight: 500 }}>
      {/* Index panel */}
      <div style={{ width: 240, flexShrink: 0, background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 12 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search..." style={{ ...inp, flex: 1, fontSize: 10 }} />
          <button onClick={newNote} style={{
            padding: '4px 10px', borderRadius: 4, fontSize: 10, fontWeight: 700,
            border: '1px solid #22C55E', background: 'transparent', color: '#22C55E', cursor: 'pointer',
          }}>+ New</button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {filtered.map(n => (
            <div key={n.symbol} onClick={() => selectNote(n.symbol)} style={{
              padding: '8px 10px', borderRadius: 4, cursor: 'pointer',
              background: selectedSym === n.symbol ? '#22C55E18' : 'transparent',
              border: `1px solid ${selectedSym === n.symbol ? '#22C55E44' : 'transparent'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#E2E8F0', fontSize: 11, fontWeight: 700 }}>{n.symbol}</span>
                <Stars n={n.rating} />
              </div>
              {n.excerpt && (
                <div style={{ color: '#475569', fontSize: 9, marginTop: 3, overflow: 'hidden',
                  whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{n.excerpt}</div>
              )}
              {n.tags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginTop: 4 }}>
                  {n.tags.map(t => (
                    <span key={t} style={{
                      background: '#1E2332', color: '#64748B', borderRadius: 2,
                      padding: '0 5px', fontSize: 8,
                    }}>{t}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {filtered.length === 0 && (
            <div style={{ color: '#334155', fontSize: 11, textAlign: 'center', marginTop: 24 }}>
              No notes yet. Click + New.
            </div>
          )}
        </div>
      </div>

      {/* Editor panel */}
      <div style={{ flex: 1, background: '#141720', border: '1px solid #1E2332', borderRadius: 6, padding: 16 }}>
        {selectedSym ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <a href={`/stocks/${selectedSym}`} style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, textDecoration: 'none' }}
                  onMouseOver={e => (e.currentTarget.style.color = '#22C55E')}
                  onMouseOut={e  => (e.currentTarget.style.color = '#E2E8F0')}>
                  {selectedSym}
                </a>
                <Stars n={rating} onChange={setRating} />
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} style={{
                  padding: '6px 18px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                  border: '1px solid #22C55E', background: 'transparent',
                  color: saveMut.isPending ? '#334155' : '#22C55E', cursor: saveMut.isPending ? 'not-allowed' : 'pointer',
                }}>Save</button>
                <button onClick={() => { if (confirm(`Delete note for ${selectedSym}?`)) deleteMut.mutate() }} style={{
                  padding: '6px 14px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                  border: '1px solid #EF4444', background: 'transparent', color: '#EF4444', cursor: 'pointer',
                }}>Delete</button>
              </div>
            </div>

            {/* Tags */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12 }}>
              {tags.map(t => (
                <span key={t} style={{
                  background: '#1E2332', color: '#94A3B8', borderRadius: 3,
                  padding: '2px 8px', fontSize: 10, display: 'flex', alignItems: 'center', gap: 5,
                }}>
                  {t}
                  <span onClick={() => setTags(tags.filter(x => x !== t))} style={{ cursor: 'pointer', color: '#475569' }}>x</span>
                </span>
              ))}
              <input value={tagInput} onChange={e => setTagInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addTag()}
                placeholder="add tag..." style={{ ...inp, width: 100, fontSize: 10 }} />
            </div>

            {/* Content */}
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Research notes (markdown supported)..."
              style={{
                ...inp, width: '100%', minHeight: 340, resize: 'vertical',
                fontFamily: 'monospace', fontSize: 12, lineHeight: 1.6,
                boxSizing: 'border-box',
              }}
            />
            {msg && <div style={{ color: '#22C55E', fontSize: 11, marginTop: 8 }}>{msg}</div>}
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#334155', fontSize: 12 }}>
            Select a symbol from the list or click + New.
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

type Tab = 'screener' | 'compare' | 'notes'

export function ResearchPage() {
  const [tab, setTab] = useState<Tab>('screener')

  const { data: stats, isLoading, error } = useQuery<UniverseStats>({
    queryKey: ['research-stats'],
    queryFn:  fetchStats,
    staleTime: 5 * 60_000,
  })

  return (
    <div style={{ maxWidth: 1380 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, letterSpacing: 3, margin: 0 }}>
          RESEARCH
        </h1>
        {stats && (
          <span style={{ color: '#475569', fontSize: 10 }}>
            {stats.total_symbols.toLocaleString()} symbols across {stats.sector_list.length} sectors
          </span>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <TabBtn label="Screener" active={tab === 'screener'} onClick={() => setTab('screener')} />
        <TabBtn label="Compare"  active={tab === 'compare'}  onClick={() => setTab('compare')}  />
        <TabBtn label="Notes"    active={tab === 'notes'}    onClick={() => setTab('notes')}    />
      </div>

      {isLoading && tab === 'screener' && (
        <div style={{ color: '#64748B', fontSize: 12, textAlign: 'center', padding: 40 }}>
          Loading universe...
        </div>
      )}
      {error && (
        <div style={{ color: '#EF4444', fontSize: 11 }}>
          Failed to load universe stats. Is the backend running?
        </div>
      )}

      {tab === 'screener' && stats && <ScreenerTab stats={stats} />}
      {tab === 'compare'  && <CompareTab />}
      {tab === 'notes'    && <NotesTab />}
    </div>
  )
}
