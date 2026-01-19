import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAddDiscoverySourceToSpace } from '@/lib/queries/space-discovery'
import { useSpaceDataSources } from '@/lib/queries/data-sources'
import { addDiscoverySourceToSpace } from '@/lib/api/space-discovery'
import { fetchDataSourcesBySpace } from '@/lib/api/data-sources'
import { dataSourceKeys } from '@/lib/query-keys/data-sources'

const mockUseSession = jest.fn()
const invalidateQueriesMock = jest.fn()
const refetchQueriesMock = jest.fn()

jest.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
}))

jest.mock('@/lib/api/space-discovery', () => ({
  addDiscoverySourceToSpace: jest.fn(),
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

describe('useAddDiscoverySourceToSpace', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    jest.clearAllMocks()
    queryClient = createTestQueryClient()
    // Spy on the actual methods
    jest.spyOn(queryClient, 'invalidateQueries').mockImplementation(invalidateQueriesMock)
    jest.spyOn(queryClient, 'refetchQueries').mockImplementation(refetchQueriesMock)
    mockUseSession.mockReturnValue({
      data: {
        user: { id: 'user-123', access_token: 'token-123' },
      },
      status: 'authenticated',
    })
    ;(addDiscoverySourceToSpace as jest.Mock).mockResolvedValue('source-id-123')
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('invalidates and refetches data sources queries after successful mutation', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(
      () => useAddDiscoverySourceToSpace(),
      { wrapper },
    )

    await result.current.mutateAsync({
      sessionId: 'session-123',
      catalogEntryId: 'pubmed',
      researchSpaceId: 'space-123',
      sourceConfig: { metadata: { query: 'MED13' } },
    })

    await waitFor(() => {
      // Verify invalidateQueries is called for the space-specific query
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: dataSourceKeys.space('space-123'),
      })
      // Verify refetchQueries is called with type: 'active' for immediate update
      expect(queryClient.refetchQueries).toHaveBeenCalledWith({
        queryKey: dataSourceKeys.space('space-123'),
        type: 'active',
      })
      // Verify invalidateQueries is also called for the lists query
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: dataSourceKeys.lists(),
      })
    })
  })

  it('calls the API with correct parameters', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(
      () => useAddDiscoverySourceToSpace(),
      { wrapper },
    )

    const mutationParams = {
      sessionId: 'session-456',
      catalogEntryId: 'pubmed',
      researchSpaceId: 'space-456',
      sourceConfig: { metadata: { query: 'MED13', max_results: 100 } },
    }

    await result.current.mutateAsync(mutationParams)

    expect(addDiscoverySourceToSpace).toHaveBeenCalledWith(
      'session-456',
      'pubmed',
      'space-456',
      'token-123',
      {
        metadata: { query: 'MED13', max_results: 100 },
      },
    )
  })
})

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
