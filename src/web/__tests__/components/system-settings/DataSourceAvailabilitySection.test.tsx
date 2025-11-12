import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataSourceAvailabilitySection } from '@/components/system-settings/DataSourceAvailabilitySection'

const mockUseAdminCatalogEntries = jest.fn()
const mockUseCatalogAvailability = jest.fn()
const mockUseCatalogAvailabilitySummaries = jest.fn()
const mockUseSetCatalogGlobalAvailability = jest.fn()
const mockUseSetCatalogProjectAvailability = jest.fn()
const mockUseClearCatalogGlobalAvailability = jest.fn()
const mockUseClearCatalogProjectAvailability = jest.fn()
const mockUseBulkSetCatalogGlobalAvailability = jest.fn()
const mockUseResearchSpaces = jest.fn()

jest.mock('@/lib/queries/data-sources', () => ({
  useAdminCatalogEntries: (...args: unknown[]) => mockUseAdminCatalogEntries(...args),
  useCatalogAvailability: (...args: unknown[]) => mockUseCatalogAvailability(...args),
  useCatalogAvailabilitySummaries: (...args: unknown[]) => mockUseCatalogAvailabilitySummaries(...args),
  useSetCatalogGlobalAvailability: () => mockUseSetCatalogGlobalAvailability(),
  useSetCatalogProjectAvailability: () => mockUseSetCatalogProjectAvailability(),
  useClearCatalogGlobalAvailability: () => mockUseClearCatalogGlobalAvailability(),
  useClearCatalogProjectAvailability: () => mockUseClearCatalogProjectAvailability(),
  useBulkSetCatalogGlobalAvailability: () => mockUseBulkSetCatalogGlobalAvailability(),
}))

jest.mock('@/lib/queries/research-spaces', () => ({
  useResearchSpaces: (...args: unknown[]) => mockUseResearchSpaces(...args),
}))

function setupDefaults() {
  mockUseAdminCatalogEntries.mockReturnValue({
    data: [
      {
        id: 'catalog-1',
        name: 'Global API',
        description: 'Primary API source',
        category: 'Genomic Variant Databases',
        subcategory: null,
        tags: [],
        param_type: 'none',
        is_active: true,
        requires_auth: false,
        usage_count: 0,
        success_rate: 0,
      },
    ],
    isLoading: false,
  })
  mockUseCatalogAvailability.mockReturnValue({
    data: {
      catalog_entry_id: 'catalog-1',
      effective_is_active: true,
      global_rule: null,
      project_rules: [],
    },
    isLoading: false,
  })
  mockUseCatalogAvailabilitySummaries.mockReturnValue({
    data: [
      {
        catalog_entry_id: 'catalog-1',
        effective_is_active: true,
        global_rule: null,
        project_rules: [],
      },
    ],
    isLoading: false,
  })
  mockUseResearchSpaces.mockReturnValue({
    data: {
      spaces: [
        {
          id: 'space-1',
          name: 'Space Alpha',
          slug: 'space-alpha',
          description: 'Test space',
          owner_id: 'user-1',
          status: 'active',
          settings: {},
          tags: [],
          created_at: '',
          updated_at: '',
        },
      ],
      total: 1,
      skip: 0,
      limit: 50,
    },
    isLoading: false,
  })
  const defaultMutation = () => ({ mutateAsync: jest.fn().mockResolvedValue(undefined), isPending: false })
  mockUseSetCatalogGlobalAvailability.mockImplementation(defaultMutation)
  mockUseSetCatalogProjectAvailability.mockImplementation(defaultMutation)
  mockUseClearCatalogGlobalAvailability.mockImplementation(defaultMutation)
  mockUseClearCatalogProjectAvailability.mockImplementation(defaultMutation)
  mockUseBulkSetCatalogGlobalAvailability.mockImplementation(defaultMutation)
}

describe('DataSourceAvailabilitySection', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    setupDefaults()
  })

  it('renders list of data sources', () => {
    render(<DataSourceAvailabilitySection />)
    expect(screen.getByText('Global API')).toBeInTheDocument()
  })

  it('opens manage dialog when button is clicked', async () => {
    const user = userEvent.setup()
    render(<DataSourceAvailabilitySection />)

    await user.click(screen.getByRole('button', { name: /manage availability/i }))
    expect(await screen.findByText(/Global availability/i)).toBeInTheDocument()
  })

  it('calls mutation when activating globally', async () => {
    const user = userEvent.setup()
    const mutateAsync = jest.fn().mockResolvedValue(undefined)
    mockUseSetCatalogGlobalAvailability.mockReturnValue({ mutateAsync, isPending: false })

    render(<DataSourceAvailabilitySection />)

    await user.click(screen.getByRole('button', { name: /manage availability/i }))
    await user.click(await screen.findByRole('button', { name: /Enable globally/i }))

    expect(mutateAsync).toHaveBeenCalledWith({ catalogEntryId: 'catalog-1', isActive: true })
  })

  it('filters data sources based on search input', async () => {
    const user = userEvent.setup()
    mockUseAdminCatalogEntries.mockReturnValue({
      data: [
        {
          id: 'catalog-1',
          name: 'Alpha Source',
          description: 'Primary alpha data',
          category: 'Genomic',
          subcategory: null,
          tags: [],
          param_type: 'none',
          is_active: true,
          requires_auth: false,
          usage_count: 0,
          success_rate: 0,
        },
        {
          id: 'catalog-2',
          name: 'Beta Source',
          description: 'Secondary beta data',
          category: 'Clinical',
          subcategory: null,
          tags: [],
          param_type: 'none',
          is_active: true,
          requires_auth: false,
          usage_count: 0,
          success_rate: 0,
        },
      ],
      isLoading: false,
    })
    mockUseCatalogAvailabilitySummaries.mockReturnValue({
      data: [
        {
          catalog_entry_id: 'catalog-1',
          effective_is_active: true,
          global_rule: null,
          project_rules: [],
        },
        {
          catalog_entry_id: 'catalog-2',
          effective_is_active: true,
          global_rule: null,
          project_rules: [],
        },
      ],
      isLoading: false,
    })

    render(<DataSourceAvailabilitySection />)

    const input = screen.getByPlaceholderText(/search by name/i)
    await user.clear(input)
    await user.type(input, 'Beta')

    expect(screen.getByText('Beta Source')).toBeInTheDocument()
    expect(screen.queryByText('Alpha Source')).not.toBeInTheDocument()
  })

  it('applies bulk enable to filtered results', async () => {
    const user = userEvent.setup()
    const mutateAsync = jest.fn().mockResolvedValue(undefined)
    mockUseBulkSetCatalogGlobalAvailability.mockReturnValue({ mutateAsync, isPending: false })
    mockUseAdminCatalogEntries.mockReturnValue({
      data: [
        {
          id: 'catalog-1',
          name: 'Alpha Source',
          description: 'Primary alpha data',
          category: 'Genomic',
          subcategory: null,
          tags: [],
          param_type: 'none',
          is_active: true,
          requires_auth: false,
          usage_count: 0,
          success_rate: 0,
        },
        {
          id: 'catalog-2',
          name: 'Beta Source',
          description: 'Secondary beta data',
          category: 'Clinical',
          subcategory: null,
          tags: [],
          param_type: 'none',
          is_active: true,
          requires_auth: false,
          usage_count: 0,
          success_rate: 0,
        },
      ],
      isLoading: false,
    })
    mockUseCatalogAvailabilitySummaries.mockReturnValue({
      data: [
        {
          catalog_entry_id: 'catalog-1',
          effective_is_active: true,
          global_rule: null,
          project_rules: [],
        },
        {
          catalog_entry_id: 'catalog-2',
          effective_is_active: true,
          global_rule: null,
          project_rules: [],
        },
      ],
      isLoading: false,
    })

    render(<DataSourceAvailabilitySection />)

    const input = screen.getByPlaceholderText(/search by name/i)
    await user.clear(input)
    await user.type(input, 'Beta')

    await user.click(screen.getByRole('button', { name: /Enable filtered/i }))
    expect(mutateAsync).toHaveBeenCalledWith({
      isActive: true,
      catalogEntryIds: ['catalog-2'],
    })
  })
})
