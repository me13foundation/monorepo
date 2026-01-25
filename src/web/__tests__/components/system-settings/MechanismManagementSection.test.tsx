import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MechanismManagementSection } from '@/components/system-settings/MechanismManagementSection'
import type { PaginatedResponse } from '@/types/generated'
import type { Mechanism } from '@/types/mechanisms'

const mockCreateMechanismAction = jest.fn()
const mockUpdateMechanismAction = jest.fn()
const mockDeleteMechanismAction = jest.fn()

jest.mock('@/app/actions/mechanisms', () => ({
  createMechanismAction: (...args: unknown[]) => mockCreateMechanismAction(...args),
  updateMechanismAction: (...args: unknown[]) => mockUpdateMechanismAction(...args),
  deleteMechanismAction: (...args: unknown[]) => mockDeleteMechanismAction(...args),
}))

const refreshMock = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({ refresh: refreshMock }),
}))

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

const baseMechanism: Mechanism = {
  id: 1,
  name: 'Mediator complex disruption',
  description: 'Test mechanism',
  evidence_tier: 'strong',
  confidence_score: 0.8,
  source: 'manual_curation',
  protein_domains: [],
  phenotype_ids: [],
  phenotype_count: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

const baseResponse: PaginatedResponse<Mechanism> = {
  items: [baseMechanism],
  total: 1,
  page: 1,
  per_page: 50,
  total_pages: 1,
  has_next: false,
  has_prev: false,
}

describe('MechanismManagementSection', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockCreateMechanismAction.mockResolvedValue({
      success: true,
      data: baseMechanism,
    })
  })

  it('renders mechanisms list', () => {
    render(<MechanismManagementSection mechanisms={baseResponse} />)

    expect(screen.getByText('Mechanisms')).toBeInTheDocument()
    expect(screen.getByText('Mediator complex disruption')).toBeInTheDocument()
  })

  it('creates a mechanism from the dialog', async () => {
    const user = userEvent.setup()
    render(<MechanismManagementSection mechanisms={baseResponse} />)

    await user.click(screen.getByRole('button', { name: /Add Mechanism/i }))
    await user.type(screen.getByLabelText(/Mechanism name/i), 'Ciliary transport defect')
    await user.clear(screen.getByLabelText(/Confidence score/i))
    await user.type(screen.getByLabelText(/Confidence score/i), '0.72')

    await user.click(screen.getByRole('button', { name: /Save Mechanism/i }))

    await waitFor(() => {
      expect(mockCreateMechanismAction).toHaveBeenCalledWith({
        name: 'Ciliary transport defect',
        description: undefined,
        evidence_tier: 'supporting',
        confidence_score: 0.72,
        source: 'manual_curation',
        protein_domains: [],
        phenotype_ids: [],
      })
    })
  })
})
