import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useSpaceDataSources } from '@/lib/queries/data-sources'
import { fetchDataSourcesBySpace } from '@/lib/api/data-sources'

const mockUseSession = jest.fn()

jest.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
}))

jest.mock('@/lib/api/data-sources', () => ({
  fetchDataSourcesBySpace: jest.fn(),
}))

// Create a test query client
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
}

describe('useSpaceDataSources', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseSession.mockReturnValue({
      data: {
        user: { id: 'user-123', access_token: 'token-123' },
      },
      status: 'authenticated',
    })
    ;(fetchDataSourcesBySpace as jest.Mock).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      has_next: false,
      has_prev: false,
    })
  })

  it('provides refetch function for manual refetching', () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(
      () => useSpaceDataSources('space-123'),
      { wrapper },
    )

    // Verify the hook returns the expected structure with refetch capability
    expect(result.current.refetch).toBeDefined()
    expect(typeof result.current.refetch).toBe('function')
  })

  it('fetches data sources for the given space', async () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(
      () => useSpaceDataSources('space-123'),
      { wrapper },
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(fetchDataSourcesBySpace).toHaveBeenCalledWith(
      'space-123',
      {},
      'token-123',
    )
  })

  it('returns refetch function for manual refetching', () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(
      () => useSpaceDataSources('space-123'),
      { wrapper },
    )

    expect(result.current.refetch).toBeDefined()
    expect(typeof result.current.refetch).toBe('function')
  })
})
