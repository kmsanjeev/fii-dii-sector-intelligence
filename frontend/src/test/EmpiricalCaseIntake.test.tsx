import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { EmpiricalCaseIntake } from '../components/admin/EmpiricalCaseIntake'

const apiMock = vi.hoisted(() => ({
  fetchEmpiricalOverview: vi.fn(),
  fetchEmpiricalCases: vi.fn(),
  fetchEmpiricalImports: vi.fn(),
  validateEmpiricalCase: vi.fn(),
  createEmpiricalCase: vi.fn(),
  previewEmpiricalImport: vi.fn(),
  ingestEmpiricalImport: vi.fn(),
  downloadEmpiricalTemplate: vi.fn(),
}))

vi.mock('../api/empiricalAdmin', () => apiMock)

function renderIntake() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={client}><EmpiricalCaseIntake /></QueryClientProvider>)
}

describe('EmpiricalCaseIntake', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMock.fetchEmpiricalOverview.mockResolvedValue({ cases: 0, eligible: 0 })
    apiMock.fetchEmpiricalCases.mockResolvedValue({ cases: [] })
    apiMock.fetchEmpiricalImports.mockResolvedValue({ imports: [] })
    apiMock.validateEmpiricalCase.mockResolvedValue({ status: 'VALID', eligibility: 'UNVERIFIED', quality: 'LOW', errors: [], warnings: [] })
  })

  it('shows the governed empty state and intake navigation', async () => {
    renderIntake()
    expect(await screen.findByText('No empirical cases have been added yet.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Single Case' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Bulk Import' })).toBeInTheDocument()
  })

  it('opens single case validation without allowing unvalidated save', async () => {
    renderIntake()
    fireEvent.click(await screen.findByRole('button', { name: 'Single Case' }))
    expect(screen.getByText('Case class')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save Case' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Validate' }))
    await waitFor(() => expect(apiMock.validateEmpiricalCase).toHaveBeenCalledTimes(1))
  })
})
