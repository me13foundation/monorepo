import { renderHook } from '@testing-library/react'
import {
  useAdminUserList,
  useAdminUserStats,
  useSystemAdminAccess,
} from '@/lib/queries/users'

const mockUseSession = jest.fn()
const useQueryMock = jest.fn()
const useMutationMock = jest.fn().mockReturnValue({
  mutateAsync: jest.fn(),
  isPending: false,
})
const invalidateQueriesMock = jest.fn()

jest.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
}))

jest.mock('@tanstack/react-query', () => ({
  useQuery: (options: unknown) => useQueryMock(options),
  useMutation: () => useMutationMock(),
  useQueryClient: () => ({
    invalidateQueries: invalidateQueriesMock,
  }),
}))

const fetchUsersMock = jest.fn()
const fetchUserStatisticsMock = jest.fn()

jest.mock('@/lib/api/users', () => ({
  fetchUsers: (...args: unknown[]) => fetchUsersMock(...args),
  fetchUserStatistics: (...args: unknown[]) => fetchUserStatisticsMock(...args),
  createUser: jest.fn(),
  updateUser: jest.fn(),
  deleteUser: jest.fn(),
  lockUser: jest.fn(),
  unlockUser: jest.fn(),
}))

describe('admin user query hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    useQueryMock.mockReturnValue({ data: null })
    fetchUsersMock.mockResolvedValue({ users: [], total: 0 })
    fetchUserStatisticsMock.mockResolvedValue({
      total_users: 0,
      active_users: 0,
      inactive_users: 0,
      suspended_users: 0,
      pending_verification: 0,
      by_role: {},
      recent_registrations: 0,
      recent_logins: 0,
    })
  })

  it('reports admin readiness via useSystemAdminAccess', () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { role: 'admin', access_token: 'token-123' },
      },
      status: 'authenticated',
    })

    const { result } = renderHook(() => useSystemAdminAccess())

    expect(result.current.isAdmin).toBe(true)
    expect(result.current.isReady).toBe(true)
    expect(result.current.hasToken).toBe(true)
  })

  it('disables user list queries when user is not admin', () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { role: 'researcher', access_token: 'token-abc' },
      },
      status: 'authenticated',
    })

    renderHook(() => useAdminUserList({ skip: 0, limit: 10 }))

    const call = useQueryMock.mock.calls[0][0] as { enabled: boolean }
    expect(call.enabled).toBe(false)
  })

  it('prefetches user list with admin token', async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { role: 'admin', access_token: 'token-456' },
      },
      status: 'authenticated',
    })

    renderHook(() => useAdminUserList({ skip: 5, limit: 20 }))

    const call = useQueryMock.mock.calls[0][0] as {
      enabled: boolean
      queryKey: unknown[]
      queryFn: () => Promise<unknown>
    }

    expect(call.enabled).toBe(true)
    expect(call.queryKey).toEqual([
      'users',
      'list',
      { skip: 5, limit: 20, role: undefined, status_filter: undefined },
      'token-456',
    ])

    await call.queryFn()
    expect(fetchUsersMock).toHaveBeenCalledWith(
      { skip: 5, limit: 20, role: undefined, status_filter: undefined },
      'token-456',
    )
  })

  it('queries user statistics with admin token', async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { role: 'admin', access_token: 'token-789' },
      },
      status: 'authenticated',
    })

    renderHook(() => useAdminUserStats())

    const call = useQueryMock.mock.calls[0][0] as {
      queryFn: () => Promise<unknown>
      queryKey: unknown[]
      enabled: boolean
    }

    expect(call.queryKey).toEqual(['users', 'stats', 'token-789'])
    expect(call.enabled).toBe(true)

    await call.queryFn()
    expect(fetchUserStatisticsMock).toHaveBeenCalledWith('token-789')
  })
})

