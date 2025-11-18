import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StorageConfigurationManager } from '@/components/system-settings/StorageConfigurationManager'

const mockUseStorageConfigurations = jest.fn()
const mockUseStorageMutations = jest.fn()
const mockUseStorageMetrics = jest.fn()
const mockUseStorageHealth = jest.fn()
const mockUseStorageOverview = jest.fn()
const mockUseMaintenanceState = jest.fn()

const originalBetaFlag = process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA

let createMutation: { mutateAsync: jest.Mock; isPending: boolean }
let updateMutation: { mutateAsync: jest.Mock; isPending: boolean }
let testMutation: { mutateAsync: jest.Mock; isPending: boolean }

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('@/lib/queries/storage', () => ({
  useStorageConfigurations: () => mockUseStorageConfigurations(),
  useStorageMutations: () => mockUseStorageMutations(),
  useStorageMetrics: (id: string) => mockUseStorageMetrics(id),
  useStorageHealth: (id: string) => mockUseStorageHealth(id),
  useStorageOverview: () => mockUseStorageOverview(),
}))

jest.mock('@/lib/queries/system-status', () => ({
  useMaintenanceState: () => mockUseMaintenanceState(),
}))

describe('StorageConfigurationManager', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    createMutation = { mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false }
    updateMutation = { mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false }
    testMutation = { mutateAsync: jest.fn().mockResolvedValue({ success: true }), isPending: false }
    mockUseStorageConfigurations.mockReturnValue({
      data: {
        data: [],
        total: 0,
        page: 1,
        per_page: 100,
      },
      isLoading: false,
    })
    mockUseStorageMutations.mockReturnValue({
      createConfiguration: createMutation,
      updateConfiguration: updateMutation,
      testConfiguration: testMutation,
      deleteConfiguration: { mutateAsync: jest.fn(), isPending: false },
    })
    mockUseStorageMetrics.mockReturnValue({ data: null })
    mockUseStorageHealth.mockReturnValue({ data: null })
    mockUseStorageOverview.mockReturnValue({
      data: {
        generated_at: new Date().toISOString(),
        totals: {
          total_configurations: 0,
          enabled_configurations: 0,
          disabled_configurations: 0,
          healthy_configurations: 0,
          degraded_configurations: 0,
          offline_configurations: 0,
          total_files: 0,
          total_size_bytes: 0,
          average_error_rate: 0,
        },
        configurations: [],
      },
      isLoading: false,
    })
    mockUseMaintenanceState.mockReturnValue({
      data: { state: { is_active: true } },
      isLoading: false,
    })
    process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA = 'true'
  })

  afterAll(() => {
    if (originalBetaFlag === undefined) {
      delete process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA
    } else {
      process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA = originalBetaFlag
    }
  })

  it('renders empty state when no configurations are available', () => {
    render(<StorageConfigurationManager />)
    expect(screen.getByText(/No storage configurations found/i)).toBeInTheDocument()
  })

  it('submits the new configuration form', async () => {
    const user = userEvent.setup()
    render(<StorageConfigurationManager />)

    await user.click(screen.getByRole('button', { name: /Add Configuration/i }))
    const nameInput = screen.getByLabelText(/Name/i)
    await user.clear(nameInput)
    await user.type(nameInput, 'Local Archive')

    await user.click(screen.getByRole('button', { name: /Create Configuration/i }))

    await waitFor(() => {
      expect(createMutation.mutateAsync).toHaveBeenCalledWith({
        name: 'Local Archive',
        provider: 'local_filesystem',
        default_use_cases: ['pdf'],
        enabled: true,
        config: {
          provider: 'local_filesystem',
          base_path: '/var/med13/storage',
          create_directories: true,
          expose_file_urls: false,
        },
      })
    })
  })

  it('tests an existing configuration connection', async () => {
    const user = userEvent.setup()
    mockUseStorageConfigurations.mockReturnValue({
      data: {
        data: [
          {
            id: 'cfg-1',
            name: 'Primary Storage',
            provider: 'local_filesystem',
            config: {
              provider: 'local_filesystem',
              base_path: '/var/lib/med13',
              create_directories: true,
              expose_file_urls: false,
            },
            enabled: true,
            supported_capabilities: ['pdf', 'export'],
            default_use_cases: ['pdf'],
            metadata: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 100,
      },
      isLoading: false,
    })
    mockUseStorageMetrics.mockReturnValue({
      data: {
        configuration_id: 'cfg-1',
        total_files: 5,
        total_size_bytes: 1024,
        last_operation_at: new Date().toISOString(),
        error_rate: 0,
      },
    })
    mockUseStorageHealth.mockReturnValue({
      data: {
        configuration_id: 'cfg-1',
        provider: 'local_filesystem',
        status: 'healthy',
        last_checked_at: new Date().toISOString(),
        details: {},
      },
    })

    render(<StorageConfigurationManager />)

    await user.click(screen.getByRole('button', { name: /Test Connection/i }))

    expect(testMutation.mutateAsync).toHaveBeenCalledWith({ configurationId: 'cfg-1' })
  })

  it('blocks toggling when maintenance mode is disabled', async () => {
    const user = userEvent.setup()
    mockUseMaintenanceState.mockReturnValue({
      data: { state: { is_active: false } },
      isLoading: false,
    })
    mockUseStorageConfigurations.mockReturnValue({
      data: {
        data: [
          {
            id: 'cfg-1',
            name: 'Primary Storage',
            provider: 'local_filesystem',
            config: { provider: 'local_filesystem', base_path: '/tmp', create_directories: true, expose_file_urls: false },
            enabled: true,
            supported_capabilities: ['pdf'],
            default_use_cases: ['pdf'],
            metadata: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 100,
      },
      isLoading: false,
    })
    mockUseStorageMetrics.mockReturnValue({
      data: {
        configuration_id: 'cfg-1',
        total_files: 10,
        total_size_bytes: 1024,
        last_operation_at: new Date().toISOString(),
        error_rate: 0,
      },
    })
    mockUseStorageHealth.mockReturnValue({ data: null })

    render(<StorageConfigurationManager />)
    const toggle = screen.getByRole('switch', { name: /enabled/i })
    await user.click(toggle)

    expect(updateMutation.mutateAsync).not.toHaveBeenCalled()
  })

  it('shows maintenance confirmation when editing provider/base path without maintenance', async () => {
    const user = userEvent.setup()
    mockUseMaintenanceState.mockReturnValue({
      data: { state: { is_active: false } },
      isLoading: false,
    })
    mockUseStorageConfigurations.mockReturnValue({
      data: {
        data: [
          {
            id: 'cfg-1',
            name: 'Primary Storage',
            provider: 'local_filesystem',
            config: { provider: 'local_filesystem', base_path: '/var/med13/storage', create_directories: true, expose_file_urls: false },
            enabled: true,
            supported_capabilities: ['pdf'],
            default_use_cases: ['pdf'],
            metadata: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 100,
      },
      isLoading: false,
    })

    render(<StorageConfigurationManager />)
    await user.click(screen.getByRole('button', { name: /Add Configuration/i }))
    await user.clear(screen.getByLabelText(/Name/i))
    await user.type(screen.getByLabelText(/Name/i), 'Updated Storage')
    await user.clear(screen.getByLabelText(/Base Path/i))
    await user.type(screen.getByLabelText(/Base Path/i), '/tmp/archive')
    await user.click(screen.getByRole('button', { name: /Create Configuration/i }))

    expect(screen.getByText(/Enable maintenance mode first/i)).toBeInTheDocument()
    expect(createMutation.mutateAsync).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: /Continue without maintenance/i }))
    await waitFor(() => {
      expect(createMutation.mutateAsync).toHaveBeenCalled()
    })
  })

  it('allows creation without modal when maintenance off but provider/base path unchanged', async () => {
    const user = userEvent.setup()
    mockUseMaintenanceState.mockReturnValue({
      data: { state: { is_active: false } },
      isLoading: false,
    })
    mockUseStorageConfigurations.mockReturnValue({
      data: {
        data: [
          {
            id: 'cfg-1',
            name: 'Primary Storage',
            provider: 'local_filesystem',
            config: { provider: 'local_filesystem', base_path: '/var/med13/storage', create_directories: true, expose_file_urls: false },
            enabled: true,
            supported_capabilities: ['pdf'],
            default_use_cases: ['pdf'],
            metadata: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 100,
      },
      isLoading: false,
    })

    render(<StorageConfigurationManager />)
    await user.click(screen.getByRole('button', { name: /Add Configuration/i }))
    await user.clear(screen.getByLabelText(/Name/i))
    await user.type(screen.getByLabelText(/Name/i), 'Second Storage')
    await user.click(screen.getByRole('button', { name: /Create Configuration/i }))

    await waitFor(() => {
      expect(createMutation.mutateAsync).toHaveBeenCalled()
    })
    expect(screen.queryByText(/Enable maintenance mode first/i)).not.toBeInTheDocument()
  })
})
