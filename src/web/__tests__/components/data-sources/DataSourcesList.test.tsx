import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DataSourcesList } from '@/components/data-sources/DataSourcesList'
import { DiscoverSourcesDialog } from '@/components/data-sources/DiscoverSourcesDialog'
import { useSpaceDataSources } from '@/lib/queries/data-sources'
import type { DataSource } from '@/types/data-source'
import type { OrchestratedSessionState } from '@/types/generated'

const mockUseSession = jest.fn()
const mockRefetch = jest.fn()

jest.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
}))

jest.mock('@tanstack/react-query', () => {
  const actual = jest.requireActual('@tanstack/react-query')
  return {
    ...actual,
    useQueryClient: () => ({
      invalidateQueries: jest.fn(),
      refetchQueries: jest.fn(),
    }),
  }
})

jest.mock('@/lib/queries/data-sources', () => ({
  useSpaceDataSources: jest.fn(),
  useTriggerDataSourceIngestion: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useTestDataSourceAiConfiguration: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useCreateDataSourceInSpace: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useConfigureDataSourceSchedule: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useUpdateDataSource: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useDeleteDataSource: () => ({
    mutateAsync: jest.fn(),
    isPending: false,
  }),
  useIngestionJobHistory: () => ({
    data: { items: [] },
    isLoading: false,
    error: null,
  }),
}))

jest.mock('@/components/data-discovery/DataDiscoveryContent', () => ({
  DataDiscoveryContent: ({ onComplete }: { onComplete?: () => void }) => (
    <div>
      <button
        onClick={() => onComplete?.()}
        data-testid="mock-add-source"
      >
        Mock Add Source
      </button>
    </div>
  ),
}))

jest.mock('@/lib/components/registry', () => ({
  componentRegistry: {
    get: () => null,
  },
}))

const mockDataSources: DataSource[] = [
  {
    id: 'source-1',
    name: 'Test Source 1',
    description: 'Test description',
    source_type: 'api',
    status: 'active',
    owner_id: 'user-123',
    research_space_id: 'space-123',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

const discoveryState: OrchestratedSessionState | null = null

describe('DataSourcesList - Auto-refresh on Source Addition', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    jest.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
    mockUseSession.mockReturnValue({
      data: {
        user: { id: 'user-123', access_token: 'token-123' },
      },
      status: 'authenticated',
    })
    ;(useSpaceDataSources as jest.Mock).mockReturnValue({
      data: {
        items: mockDataSources,
        total: 1,
        page: 1,
        limit: 20,
        has_next: false,
        has_prev: false,
      },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    })
  })

  it('refetches data sources when onSourceAdded callback is triggered', async () => {
    const user = userEvent.setup()

    render(
      <QueryClientProvider client={queryClient}>
        <DataSourcesList
          spaceId="space-123"
          discoveryState={discoveryState}
          discoveryCatalog={[]}
        />
      </QueryClientProvider>,
    )

    // Open the discover dialog
    const addButton = screen.getByRole('button', { name: /add from library/i })
    await user.click(addButton)

    // Wait for dialog to open
    await waitFor(() => {
      expect(screen.getByText(/discover data sources/i)).toBeInTheDocument()
    })

    // Simulate adding a source (this would normally happen in DataDiscoveryContent)
    const mockAddButton = screen.getByTestId('mock-add-source')
    await user.click(mockAddButton)

    // Verify refetch was called
    await waitFor(() => {
      expect(mockRefetch).toHaveBeenCalled()
    })
  })

  it('displays updated data sources after refetch', async () => {
    const updatedDataSources = [
      ...mockDataSources,
      {
        id: 'source-2',
        name: 'New Source',
        description: 'Newly added source',
        source_type: 'pubmed',
        status: 'draft',
        owner_id: 'user-123',
        research_space_id: 'space-123',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]

    // Initial render with 1 source
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <DataSourcesList
          spaceId="space-123"
          discoveryState={discoveryState}
          discoveryCatalog={[]}
        />
      </QueryClientProvider>,
    )

    expect(screen.getByText('Test Source 1')).toBeInTheDocument()

    // After refetch, update the mock to return 2 sources
    ;(useSpaceDataSources as jest.Mock).mockReturnValue({
      data: {
        items: updatedDataSources,
        total: 2,
        page: 1,
        limit: 20,
        has_next: false,
        has_prev: false,
      },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    })

    // Trigger refetch via dialog
    const user = userEvent.setup()
    const addButton = screen.getByRole('button', { name: /add from library/i })
    await user.click(addButton)

    const mockAddButton = screen.getByTestId('mock-add-source')
    await user.click(mockAddButton)

    await waitFor(() => {
      expect(mockRefetch).toHaveBeenCalled()
    })

    // Rerender to simulate React Query updating after refetch
    rerender(
      <QueryClientProvider client={queryClient}>
        <DataSourcesList
          spaceId="space-123"
          discoveryState={discoveryState}
          discoveryCatalog={[]}
        />
      </QueryClientProvider>,
    )

    // Verify new source appears
    await waitFor(() => {
      expect(screen.getByText('New Source')).toBeInTheDocument()
    })
  })
})

describe('DiscoverSourcesDialog - onSourceAdded prop', () => {
  it('calls onSourceAdded callback when source is added', async () => {
    const user = userEvent.setup()
    const onSourceAdded = jest.fn()

    render(
      <DiscoverSourcesDialog
        spaceId="space-123"
        open={true}
        onOpenChange={jest.fn()}
        discoveryState={discoveryState}
        discoveryCatalog={[]}
        onSourceAdded={onSourceAdded}
      />,
    )

    // Simulate adding a source
    const mockAddButton = screen.getByTestId('mock-add-source')
    await user.click(mockAddButton)

    await waitFor(() => {
      expect(onSourceAdded).toHaveBeenCalled()
    })
  })
})
