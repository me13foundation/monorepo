import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DataDiscoveryContent } from '@/components/data-discovery/DataDiscoveryContent'
import { useAddDiscoverySourceToSpace, useSpaceSourceCatalog, useSpaceDiscoverySessions } from '@/lib/queries/space-discovery'
import { dataSourceKeys } from '@/lib/query-keys/data-sources'

const mockUseSession = jest.fn()
const mockInvalidateQueries = jest.fn()
const mockRefetchQueries = jest.fn().mockResolvedValue(undefined)
const mockMutateAsync = jest.fn()

jest.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
}))

jest.mock('@/lib/queries/space-discovery', () => ({
  useSpaceSourceCatalog: jest.fn(),
  useSpaceDiscoverySessions: jest.fn(),
  useCreateSpaceDiscoverySession: () => ({
    mutate: jest.fn(),
    isPending: false,
  }),
  useAddDiscoverySourceToSpace: jest.fn(),
}))

jest.mock('@/components/data-discovery/SourceCatalog', () => ({
  SourceCatalog: ({ onSelectionChange }: { onSelectionChange: (ids: Set<string>) => void }) => (
    <div>
      <button
        onClick={() => onSelectionChange(new Set(['pubmed']))}
        data-testid="select-pubmed"
      >
        Select PubMed
      </button>
      <div data-testid="catalog-placeholder">Source Catalog</div>
    </div>
  ),
}))

const mockCatalog = [
  {
    id: 'pubmed',
    name: 'PubMed',
    description: 'Biomedical literature database',
    category: 'Scientific Literature',
    source_type: 'pubmed',
    param_type: 'gene',
    is_active: true,
    requires_auth: false,
    usage_count: 0,
    success_rate: 1.0,
    capabilities: {},
  },
]

const mockSession = {
  id: 'session-123',
  owner_id: 'user-123',
  research_space_id: 'space-123',
  selected_sources: [],
  current_parameters: {
    gene_symbol: 'MED13',
    search_term: '',
    max_results: 100,
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

describe('DataDiscoveryContent - Query Invalidation', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    jest.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
    // Mock queryClient methods
    jest.spyOn(queryClient, 'invalidateQueries').mockImplementation(mockInvalidateQueries)
    jest.spyOn(queryClient, 'refetchQueries').mockImplementation(mockRefetchQueries)
    mockUseSession.mockReturnValue({
      data: {
        user: { id: 'user-123', access_token: 'token-123' },
      },
      status: 'authenticated',
    })
    ;(useSpaceSourceCatalog as jest.Mock).mockReturnValue({
      data: mockCatalog,
      isLoading: false,
    })
    ;(useSpaceDiscoverySessions as jest.Mock).mockReturnValue({
      data: [mockSession],
      isLoading: false,
    })
    ;(useAddDiscoverySourceToSpace as jest.Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    })
    mockMutateAsync.mockResolvedValue('source-id-123')
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('invalidates and refetches data sources query when source is added', async () => {
    const user = userEvent.setup()
    const onComplete = jest.fn()

    render(
      <QueryClientProvider client={queryClient}>
        <DataDiscoveryContent
          spaceId="space-123"
          isModal={true}
          onComplete={onComplete}
        />
      </QueryClientProvider>,
    )

    // Wait for the catalog to render
    await waitFor(() => {
      expect(screen.getByTestId('catalog-placeholder')).toBeInTheDocument()
    })

    // Select a source
    const selectButton = screen.getByTestId('select-pubmed')
    await user.click(selectButton)

    // Wait for selection to update
    await waitFor(() => {
      expect(screen.getByText(/1 source selected/i)).toBeInTheDocument()
    })

    // Click "Add selected to space"
    const addButton = screen.getByRole('button', { name: /add selected to space/i })
    await user.click(addButton)

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalled()
    })

    await waitFor(() => {
      // Verify queries are invalidated
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: dataSourceKeys.space('space-123'),
      })
      // Verify queries are refetched
      expect(queryClient.refetchQueries).toHaveBeenCalledWith({
        queryKey: dataSourceKeys.space('space-123'),
        type: 'active',
      })
    })
  })

  it('calls onComplete callback after successful addition', async () => {
    const user = userEvent.setup()
    const onComplete = jest.fn()

    render(
      <QueryClientProvider client={queryClient}>
        <DataDiscoveryContent
          spaceId="space-123"
          isModal={true}
          onComplete={onComplete}
        />
      </QueryClientProvider>,
    )

    // Wait for the catalog to render
    await waitFor(() => {
      expect(screen.getByTestId('catalog-placeholder')).toBeInTheDocument()
    })

    const selectButton = screen.getByTestId('select-pubmed')
    await user.click(selectButton)

    // Wait for selection to update
    await waitFor(() => {
      expect(screen.getByText(/1 source selected/i)).toBeInTheDocument()
    })

    const addButton = screen.getByRole('button', { name: /add selected to space/i })
    await user.click(addButton)

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalled()
    })

    // Wait for refetch to complete and onComplete to be called
    await waitFor(() => {
      expect(queryClient.refetchQueries).toHaveBeenCalled()
      expect(onComplete).toHaveBeenCalled()
    }, { timeout: 3000 })
  })
})
