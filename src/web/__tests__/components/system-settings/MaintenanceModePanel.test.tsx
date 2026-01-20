import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MaintenanceModePanel } from '@/components/system-settings/MaintenanceModePanel'
import type { MaintenanceModeResponse } from '@/types/system-status'

const mockEnableMaintenanceAction = jest.fn()
const mockDisableMaintenanceAction = jest.fn()

jest.mock('@/app/actions/system-status', () => ({
  enableMaintenanceAction: (...args: unknown[]) => mockEnableMaintenanceAction(...args),
  disableMaintenanceAction: (...args: unknown[]) => mockDisableMaintenanceAction(...args),
}))

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

const inactiveState: MaintenanceModeResponse = {
  state: {
    is_active: false,
    message: null,
    activated_at: null,
    activated_by: null,
    last_updated_by: null,
    last_updated_at: null,
  },
}

const activeState: MaintenanceModeResponse = {
  state: {
    is_active: true,
    message: 'Maintenance in progress',
    activated_at: new Date().toISOString(),
    activated_by: 'admin',
    last_updated_by: 'admin',
    last_updated_at: new Date().toISOString(),
  },
}

describe('MaintenanceModePanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockEnableMaintenanceAction.mockResolvedValue({ success: true, data: inactiveState })
    mockDisableMaintenanceAction.mockResolvedValue({ success: true, data: inactiveState })
  })

  it('renders maintenance controls', () => {
    render(<MaintenanceModePanel maintenanceState={inactiveState} />)
    expect(screen.getByRole('heading', { name: /Maintenance Mode/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Enable Maintenance Mode/i })).toBeInTheDocument()
  })

  it('invokes enable action', async () => {
    const user = userEvent.setup()
    render(<MaintenanceModePanel maintenanceState={inactiveState} />)

    await user.click(screen.getByRole('button', { name: /Enable Maintenance Mode/i }))

    expect(mockEnableMaintenanceAction).toHaveBeenCalledWith({
      message: null,
      force_logout_users: true,
    })
  })

  it('invokes disable action when active', async () => {
    const user = userEvent.setup()
    render(<MaintenanceModePanel maintenanceState={activeState} />)

    await user.click(screen.getByRole('button', { name: /Disable Maintenance Mode/i }))

    expect(mockDisableMaintenanceAction).toHaveBeenCalled()
  })
})
