import { useState } from 'react'
import type { CSSProperties } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createEmpiricalCase,
  downloadEmpiricalTemplate,
  fetchEmpiricalCases,
  fetchEmpiricalImports,
  fetchEmpiricalOverview,
  ingestEmpiricalImport,
  previewEmpiricalImport,
  validateEmpiricalCase,
  type CaseIntakeForm,
} from '../../api/empiricalAdmin'

const fields: Array<[string, string, string?]> = [
  ['case_class', 'Case class'], ['case_family_id', 'Case family ID'], ['independent_source_family', 'Independent source family'], ['subject_name', 'Subject label'], ['subject_id', 'Subject ID'],
  ['birth_date', 'Birth date'], ['birth_time', 'Birth time'], ['birth_time_precision', 'Birth time precision'],
  ['birth_place', 'Birth place'], ['timezone', 'Timezone'], ['birth_data_source', 'Birth data source'],
  ['birth_data_quality', 'Birth data quality'], ['domain', 'Domain'], ['event_type', 'Event type'],
  ['event_start', 'Event start'], ['event_end', 'Event end'], ['event_description', 'Event description'],
  ['event_direction', 'Event direction'], ['event_verification_quality', 'Event verification'],
  ['source_type', 'Source type'], ['source_title', 'Source title'], ['source_author', 'Author'],
  ['source_publication', 'Publication'], ['source_page', 'Page'], ['source_passage_reference', 'Passage reference'],
  ['original_case_source', 'Original case source'], ['prediction_cutoff', 'Prediction cutoff'],
  ['knowledge_cutoff', 'Knowledge cutoff'], ['outcome_cutoff', 'Outcome cutoff'],
]

const initialForm: CaseIntakeForm = {
  case_class: 'HISTORICAL_DOCUMENTED', birth_time_precision: 'APPROXIMATE', birth_data_quality: 'UNVERIFIED',
  domain: 'GENERAL_TIMING', event_verification_quality: 'UNVERIFIED', source_passage_reference: 'REFERENCE_NOT_VERIFIED',
}

const surface: CSSProperties = { background: '#141720', border: '1px solid #1E2332', borderRadius: 8, padding: 14 }
const input: CSSProperties = { background: '#0A0D14', border: '1px solid #2D3348', borderRadius: 6, color: '#E2E8F0', padding: '8px 10px', fontSize: 12, width: '100%', boxSizing: 'border-box' }
const button: CSSProperties = { border: '1px solid #22C55E', color: '#22C55E', background: '#22C55E16', borderRadius: 6, padding: '8px 12px', cursor: 'pointer', fontWeight: 700, fontSize: 12 }

function Badge({ value }: { value: string }) {
  const color = value === 'ELIGIBLE' || value === 'VALID' || value === 'INGESTED' ? '#22C55E' : value.includes('ERROR') || value.includes('REJECT') ? '#EF4444' : '#F59E0B'
  return <span style={{ color, fontSize: 11, fontWeight: 700 }}>{value}</span>
}

export function EmpiricalCaseIntake() {
  const [section, setSection] = useState<'overview' | 'single' | 'bulk' | 'imports' | 'cases'>('overview')
  const [form, setForm] = useState<CaseIntakeForm>(initialForm)
  const [validation, setValidation] = useState<any>(null)
  const [preview, setPreview] = useState<any>(null)
  const [message, setMessage] = useState('')
  const queryClient = useQueryClient()
  const overview = useQuery({ queryKey: ['empirical-overview'], queryFn: fetchEmpiricalOverview })
  const imports = useQuery({ queryKey: ['empirical-imports'], queryFn: fetchEmpiricalImports, enabled: section === 'imports' })
  const cases = useQuery({ queryKey: ['empirical-cases'], queryFn: fetchEmpiricalCases, enabled: section === 'cases' })
  const validate = useMutation({ mutationFn: validateEmpiricalCase, onSuccess: setValidation })
  const create = useMutation({
    mutationFn: createEmpiricalCase,
    onSuccess: result => { setMessage(`Case ${result.status}.`); setValidation(result.validation); queryClient.invalidateQueries({ queryKey: ['empirical-overview'] }) },
    onError: error => setMessage(error instanceof Error ? error.message : 'Case could not be saved.'),
  })
  const upload = useMutation({ mutationFn: previewEmpiricalImport, onSuccess: setPreview, onError: error => setMessage(error instanceof Error ? error.message : 'Import could not be parsed.') })
  const ingest = useMutation({
    mutationFn: ingestEmpiricalImport,
    onSuccess: result => { setMessage(`Import ${result.status}. Accepted ${result.accepted}, rejected ${result.rejected}.`); queryClient.invalidateQueries({ queryKey: ['empirical-overview'] }); queryClient.invalidateQueries({ queryKey: ['empirical-imports'] }); queryClient.invalidateQueries({ queryKey: ['empirical-cases'] }) },
  })

  const setField = (key: string, value: string) => setForm(current => ({ ...current, [key]: value }))
  const submitValidation = () => validate.mutate(form)

  return <div style={{ color: '#E2E8F0' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 18 }}>
      <div><h2 style={{ fontSize: 18, margin: 0 }}>Empirical Intelligence / Case Intake</h2><p style={{ color: '#64748B', fontSize: 12, margin: '6px 0 0' }}>Governed intake only. Review and validate before cases enter the shared VEDA store.</p></div>
      <div style={{ ...surface, padding: '8px 12px', minWidth: 130 }}><div style={{ color: '#64748B', fontSize: 10 }}>Real cases</div><strong>{overview.data?.cases ?? 0}</strong><div style={{ color: '#64748B', fontSize: 10 }}>Eligible: {overview.data?.eligible ?? 0}</div></div>
    </div>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
      {(['overview', 'single', 'bulk', 'imports', 'cases'] as const).map(item => <button key={item} onClick={() => setSection(item)} style={{ ...button, borderColor: section === item ? '#22C55E' : '#2D3348', color: section === item ? '#22C55E' : '#94A3B8', background: section === item ? '#22C55E16' : 'transparent' }}>{item === 'single' ? 'Single Case' : item === 'bulk' ? 'Bulk Import' : item[0].toUpperCase() + item.slice(1)}</button>)}
    </div>

    {section === 'overview' && <div style={{ ...surface, display: 'grid', gap: 12 }}><strong>Ready for governed empirical input</strong><span style={{ color: '#94A3B8', fontSize: 13 }}>No empirical cases have been added yet.</span><div style={{ display: 'flex', gap: 8 }}><button style={button} onClick={() => setSection('single')}>Add Case</button><button style={button} onClick={() => setSection('bulk')}>Import CSV/XLSX</button><button style={button} onClick={() => downloadEmpiricalTemplate('csv')}>Download CSV template</button><button style={button} onClick={() => downloadEmpiricalTemplate('xlsx')}>Download XLSX template</button></div></div>}

    {section === 'single' && <div style={surface}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 12 }}>
        {fields.map(([key, label]) => <label key={key} style={{ display: 'grid', gap: 5, color: '#94A3B8', fontSize: 11 }}><span>{label}</span>{key === 'case_class' ? <select value={String(form[key] ?? '')} onChange={event => setField(key, event.target.value)} style={input}>{['HISTORICAL_VERIFIED', 'HISTORICAL_DOCUMENTED', 'HISTORICAL_USER_REPORTED', 'WORKED_ASTROLOGY_CASE', 'PRACTITIONER_CASE', 'PROSPECTIVE_VERIFIED', 'PROSPECTIVE_PENDING'].map(item => <option key={item}>{item}</option>)}</select> : <input value={String(form[key] ?? '')} onChange={event => setField(key, event.target.value)} style={input} placeholder={key.includes('date') || key.includes('cutoff') || key.includes('start') || key.includes('end') ? 'YYYY-MM-DD' : ''} />}</label>)}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}><button style={button} onClick={submitValidation} disabled={validate.isPending}>Validate</button><button style={button} onClick={() => create.mutate(form)} disabled={create.isPending || !validation || validation.status === 'ERROR'}>Save Case</button></div>
      {validation && <div style={{ ...surface, marginTop: 14, background: '#0A0D14' }}><div>Status: <Badge value={validation.status} /> &nbsp; Eligibility: <Badge value={validation.eligibility} /> &nbsp; Quality: <Badge value={validation.quality} /></div>{[...validation.errors, ...validation.warnings].map((item: any) => <div key={`${item.code}-${item.field}`} style={{ color: item.code.includes('ERROR') ? '#EF4444' : '#F59E0B', fontSize: 12, marginTop: 7 }}>{item.code}: {item.message}</div>)}</div>}
      {message && <p style={{ color: '#22C55E', fontSize: 12 }}>{message}</p>}
    </div>}

    {section === 'bulk' && <div style={{ display: 'grid', gap: 14 }}><div style={surface}><strong>Upload CSV or XLSX</strong><p style={{ color: '#64748B', fontSize: 12 }}>Upload is parsed and staged. Nothing is ingested until explicit approval.</p><input type="file" accept=".csv,.xlsx" onChange={event => { const file = event.target.files?.[0]; if (file) upload.mutate(file) }} /></div>{preview && <div style={surface}><div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}><div><strong>{preview.filename}</strong><div style={{ color: '#94A3B8', fontSize: 12 }}>Import {preview.import_id} / {preview.file_type}</div></div><button style={button} disabled={ingest.isPending || preview.summary.errors > 0} onClick={() => ingest.mutate(preview.import_id)}>Approve valid rows</button></div><div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginTop: 14, fontSize: 12 }}><span>Rows: {preview.summary.rows}</span><span>Valid: {preview.summary.valid}</span><span>Warnings: {preview.summary.warnings}</span><span>Errors: {preview.summary.errors}</span><span>Duplicates: {preview.summary.duplicates}</span><span>Eligible: {preview.summary.eligible}</span></div><div style={{ overflowX: 'auto', marginTop: 14 }}><table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}><thead><tr><th>Row</th><th>Status</th><th>Eligibility</th><th>Duplicate</th><th>Issues</th></tr></thead><tbody>{preview.rows.map((row: any) => <tr key={row.row_number}><td>{row.row_number}</td><td><Badge value={row.status} /></td><td>{row.validation.eligibility}</td><td>{row.validation.duplicate_state}</td><td>{row.validation.errors.concat(row.validation.warnings).map((item: any) => item.code).join(', ') || 'None'}</td></tr>)}</tbody></table></div></div>}</div>}

    {section === 'imports' && <div style={{ ...surface, overflowX: 'auto' }}><strong>Import History</strong><table style={{ width: '100%', marginTop: 12, fontSize: 12, borderCollapse: 'collapse' }}><thead><tr><th>Import</th><th>File</th><th>Rows</th><th>Status</th><th>Uploaded</th></tr></thead><tbody>{(imports.data?.imports ?? []).map((item: any) => <tr key={item.import_id}><td>{item.import_id}</td><td>{item.filename}</td><td>{item.row_count}</td><td><Badge value={item.status} /></td><td>{item.uploaded_at}</td></tr>)}</tbody></table></div>}
    {section === 'cases' && <div style={{ ...surface, overflowX: 'auto' }}><strong>Cases</strong><table style={{ width: '100%', marginTop: 12, fontSize: 12, borderCollapse: 'collapse' }}><thead><tr><th>Case ID</th><th>Subject</th><th>Class</th><th>Domain</th><th>Quality</th><th>Leakage</th></tr></thead><tbody>{(cases.data?.cases ?? []).map((item: any) => <tr key={item.case_id}><td>{item.case_id}</td><td>{item.subject_id}</td><td>{item.case_class}</td><td>{item.domain}</td><td>{item.quality}</td><td>{item.leakage_status}</td></tr>)}</tbody></table></div>}
  </div>
}
