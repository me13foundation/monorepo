import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SystemSettingsClient from '@/app/(dashboard)/system-settings/system-settings-client'

const mockUseSystemAdminAccess = jest.fn()
const mockUseAdminUserStats = jest.fn()
const mockUseAdminUserList = jest.fn()
const mockUseAdminUserMutations = jest.fn()

jest.mock('@/lib/queries/users', () => ({
  useSystemAdminAccess: () => mockUseSystemAdminAccess(),
  useAdminUserStats: () => mockUseAdminUserStats(),
  useAdminUserList: (params: unknown) => mockUseAdminUserList(params),
  useAdminUserMutations: () => mockUseAdminUserMutations(),
}))

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

const initialParams = { skip: 0, limit: 25 }

describe('SystemSettingsClient', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAdminUserStats.mockReturnValue({ data: null, isLoading: false })
    mockUseAdminUserList.mockReturnValue({
      data: { users: [], total: 0 },
      isLoading: false,
      isError: false,
      isRefetching: false,
      refetch: jest.fn(),
    })
    mockUseAdminUserMutations.mockReturnValue({
      isReady: true,
      createUser: { mutateAsync: jest.fn(), isPending: false },
      updateUser: { mutateAsync: jest.fn(), isPending: false },
      deleteUser: { mutateAsync: jest.fn(), isPending: false },
      lockUser: { mutateAsync: jest.fn(), isPending: false },
      unlockUser: { mutateAsync: jest.fn(), isPending: false },
    })
  })

  it('shows loading state while session status is loading', () => {
    mockUseSystemAdminAccess.mockReturnValue({
      status: 'loading',
      isAdmin: true,
      isReady: false,
      session: null,
    })

    render(<SystemSettingsClient initialParams={initialParams} />)

    expect(
      screen.getByText(/Preparing secure admin workspace/i),
    ).toBeInTheDocument()
  })

  it('shows restricted message for non-admin users', () => {
    mockUseSystemAdminAccess.mockReturnValue({
      status: 'authenticated',
      isAdmin: false,
      isReady: false,
      session: { user: { id: 'user-1' } },
    })

    render(<SystemSettingsClient initialParams={initialParams} />)

    expect(screen.getByText(/Restricted Area/i)).toBeInTheDocument()
  })

  it('renders table data and triggers suspend action', async () => {
    const lockUserMutation = { mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false }
    mockUseSystemAdminAccess.mockReturnValue({
      status: 'authenticated',
      isAdmin: true,
      isReady: true,
      session: { user: { id: 'admin-1' } },
    })
    mockUseAdminUserStats.mockReturnValue({
      data: {
        total_users: 1,
        active_users: 1,
        inactive_users: 0,
        suspended_users: 0,
        pending_verification: 0,
        by_role: { researcher: 1 },
        recent_registrations: 0,
        recent_logins: 0,
      },
      isLoading: false,
    })
    mockUseAdminUserList.mockReturnValue({
      data: {
        users: [
          {
            id: 'user-1',
            email: 'researcher@med13.org',
            username: 'researcher1',
            full_name: 'Researcher One',
            role: 'researcher',
            status: 'active',
            email_verified: true,
            last_login: '2024-01-01T00:00:00.000Z',
            created_at: '2023-01-01T00:00:00.000Z',
          },
        ],
        total: 1,
      },
      isLoading: false,
      isError: false,
      isRefetching: false,
      refetch: jest.fn(),
    })
    mockUseAdminUserMutations.mockReturnValue({
      isReady: true,
      createUser: { mutateAsync: jest.fn(), isPending: false },
      updateUser: { mutateAsync: jest.fn(), isPending: false },
      deleteUser: { mutateAsync: jest.fn(), isPending: false },
      lockUser: lockUserMutation,
      unlockUser: { mutateAsync: jest.fn(), isPending: false },
    })

    const user = userEvent.setup()
    render(<SystemSettingsClient initialParams={initialParams} />)

    expect(screen.getByText('Researcher One')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Suspend/i }))
    expect(lockUserMutation.mutateAsync).toHaveBeenCalledWith({ userId: 'user-1' })
  })

  it('creates a user from the dialog form', async () => {
    const createUserMutation = { mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false }
    mockUseSystemAdminAccess.mockReturnValue({
      status: 'authenticated',
      isAdmin: true,
      isReady: true,
      session: { user: { id: 'admin-1' } },
    })
    mockUseAdminUserMutations.mockReturnValue({
      isReady: true,
      createUser: createUserMutation,
      updateUser: { mutateAsync: jest.fn(), isPending: false },
      deleteUser: { mutateAsync: jest.fn(), isPending: false },
      lockUser: { mutateAsync: jest.fn(), isPending: false },
      unlockUser: { mutateAsync: jest.fn(), isPending: false },
    })

    const user = userEvent.setup()
    render(<SystemSettingsClient initialParams={initialParams} />)

    await user.click(screen.getByRole('button', { name: /New User/i }))
    await user.type(screen.getByLabelText(/Full name/i), 'Dr. Jane Doe')
    await user.type(screen.getByLabelText(/^Email/i), 'jane@med13.org')
    await user.type(screen.getByLabelText(/Username/i), 'jane')
    await user.type(screen.getByLabelText(/Temporary password/i), 'Password!234')

    await user.click(screen.getByRole('button', { name: /Create User/i }))

    await waitFor(() => {
      expect(createUserMutation.mutateAsync).toHaveBeenCalledWith({
        email: 'jane@med13.org',
        username: 'jane',
        full_name: 'Dr. Jane Doe',
        password: 'Password!234',
        role: 'researcher',
      })
    })
  })
})
