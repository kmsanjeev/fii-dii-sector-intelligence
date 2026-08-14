import { api } from './client'

export type CaseIntakeForm = Record<string, string | null | undefined>

export async function fetchEmpiricalOverview() {
  const response = await api.get('/empirical/overview')
  return response.data
}

export async function validateEmpiricalCase(payload: CaseIntakeForm) {
  const response = await api.post('/empirical/cases/validate', payload)
  return response.data
}

export async function createEmpiricalCase(payload: CaseIntakeForm) {
  const response = await api.post('/empirical/cases', payload)
  return response.data
}

export async function previewEmpiricalImport(file: File) {
  const form = new FormData()
  form.append('file', file)
  const response = await api.post('/empirical/imports/preview', form)
  return response.data
}

export async function ingestEmpiricalImport(importId: string) {
  const response = await api.post(`/empirical/imports/${importId}/ingest`, {})
  return response.data
}

export async function fetchEmpiricalImports() {
  const response = await api.get('/empirical/imports')
  return response.data
}

export async function fetchEmpiricalCases() {
  const response = await api.get('/empirical/cases')
  return response.data
}

export async function downloadEmpiricalTemplate(kind: 'csv' | 'xlsx') {
  const response = await api.get(`/empirical/templates/${kind}`, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = kind === 'csv' ? 'VEDA_Empirical_Case_Import_Template.csv' : 'VEDA_Empirical_Case_Import_Template.xlsx'
  anchor.click()
  URL.revokeObjectURL(url)
}
