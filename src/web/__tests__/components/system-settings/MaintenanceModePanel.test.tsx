import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaintenanceModePanel } from '@/components/system-settings/MaintenanceModePanel'

const mockUseMaintenanceState = jest.fn()
const mockUseMaintenanceMutations = jest.fn()

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('@/lib/queries/system-status', () => ({
  useMaintenanceState: () => mockUseMaintenanceState(),
  useMaintenanceMutations: () => mockUseMaintenanceMutations(),
}))

describe('MaintenanceModePanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseMaintenanceState.mockReturnValue({
      data: { state: { is_active: false } },
      isLoading: false,
    })
    mockUseMaintenanceMutations.mockReturnValue({
      enable: { mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false },
      disable: { mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false },
    })
  })

  it('renders maintenance controls', () => {
    render(<MaintenanceModePanel />)
    expect(screen.getByRole('heading', { name: /Maintenance Mode/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Enable Maintenance Mode/i })).toBeInTheDocument()
  })

  it('invokes enable mutation', async () => {
    const user = userEvent.setup()
    render(<MaintenanceModePanel />)

    await user.click(screen.getByRole('switch', { name: /force logout/i }))
    await user.click(screen.getByRole('button', { name: /Enable Maintenance Mode/i }))

    expect(mockUseMaintenanceMutations().enable.mutateAsync).toHaveBeenCalled()
  })

  it('invokes disable mutation when active', async () => {
    const user = userEvent.setup()
    mockUseMaintenanceState.mockReturnValue({
      data: { state: { is_active: true } },
      isLoading: false,
    })
    render(<MaintenanceModePanel />)

    await user.click(screen.getByRole('button', { name: /Disable Maintenance Mode/i }))
    expect(mockUseMaintenanceMutations().disable.mutateAsync).toHaveBeenCalled()
  })
})
