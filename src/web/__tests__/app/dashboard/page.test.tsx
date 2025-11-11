import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardClient from '@/app/(dashboard)/dashboard/dashboard-client'
import { ThemeProvider } from '@/components/theme-provider'
// Mock ThemeProvider to avoid DOM prop warnings
jest.mock('@/components/theme-provider', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))
// Mock React Query dashboard hooks
jest.mock('@/lib/queries/dashboard', () => ({
  useDashboardStats: () => ({
    data: {
      pending_count: 1,
      approved_count: 9,
      rejected_count: 0,
      total_items: 10,
      entity_counts: { genes: 2, variants: 5, phenotypes: 2, evidence: 1, publications: 0 },
    },
    isLoading: false,
  }),
  useRecentActivities: () => ({
    data: {
      activities: [
        { title: 'Ingestion finished', category: 'success', icon: 'mdi:check', timestamp: new Date().toISOString() },
        { title: 'Validation warning', category: 'warning', icon: 'mdi:alert', timestamp: new Date().toISOString() },
      ],
      total: 2,
    },
    isLoading: false,
  }),
}))

// Mock NextAuth session
const mockSession = {
  user: {
    id: 'test-user-id',
    email: 'admin@med13.org',
    name: 'Test Admin',
    username: 'admin',
    full_name: 'Test Admin',
    role: 'admin',
    email_verified: true,
    access_token: 'test-access-token',
    expires_at: Date.now() + 3600000, // 1 hour from now
  },
  expires: '2025-12-31T00:00:00.000Z'
}

jest.mock('next-auth/react', () => ({
  useSession: () => ({
    data: mockSession,
    status: 'authenticated'
  }),
  signOut: jest.fn()
}))

// Mock space context
const mockSetCurrentSpaceId = jest.fn()
const mockUseSpaceContext = jest.fn(() => ({
  currentSpaceId: null as string | null,
  setCurrentSpaceId: mockSetCurrentSpaceId,
  isLoading: false,
}))

jest.mock('@/components/space-context-provider', () => ({
  useSpaceContext: () => mockUseSpaceContext(),
  SpaceContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock research spaces query
const mockUseResearchSpaces = jest.fn(() => ({
  data: { spaces: [] as Array<{ id: string; name: string; slug: string }> },
  isLoading: false,
}))

jest.mock('@/lib/queries/research-spaces', () => ({
  useResearchSpaces: () => mockUseResearchSpaces(),
}))

// Test wrapper with providers
const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      enableSystem
      disableTransitionOnChange
    >
      {component}
    </ThemeProvider>
  )
}

describe('DashboardPage', () => {
  it('renders the main dashboard heading', () => {
    renderWithProviders(<DashboardClient />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('MED13 Admin Dashboard')
  })

  it('renders the dashboard subtitle', () => {
    renderWithProviders(<DashboardClient />)
    expect(screen.getByText('Welcome back, Test Admin')).toBeInTheDocument()
  })

  // Note: Theme toggle and action buttons are now in Header component
  // These are tested separately in Header component tests

  describe('Statistics Cards', () => {
    it('renders all metric cards', () => {
      renderWithProviders(<DashboardClient />)

      expect(screen.getByText('Data Sources')).toBeInTheDocument()
      expect(screen.getByText('Total Records')).toBeInTheDocument()
      expect(screen.getByText('Genes Tracked')).toBeInTheDocument()
      expect(screen.getByText('System Health')).toBeInTheDocument()
    })

    it('displays metric values from API', () => {
      renderWithProviders(<DashboardClient />)
      expect(screen.getByText('1')).toBeInTheDocument() // Data Sources (evidence count)
      expect(screen.getByText('10')).toBeInTheDocument() // Total Records
      expect(screen.getByText('2')).toBeInTheDocument() // Genes count
      expect(screen.getByText('90%')).toBeInTheDocument() // Approx approval rate
    })

    it('displays metric descriptions', () => {
      renderWithProviders(<DashboardClient />)
      expect(screen.getByText(/Approved 9/i)).toBeInTheDocument()
      expect(screen.getByText(/Total records across entities/i)).toBeInTheDocument()
      expect(screen.getByText(/Entities in knowledge base/i)).toBeInTheDocument()
      expect(screen.getByText(/Approximate approval rate/i)).toBeInTheDocument()
    })
  })

  describe('Data Sources Section', () => {
    it('renders data sources section', () => {
      renderWithProviders(<DashboardClient />)

      expect(screen.getByText('Recent Data Sources')).toBeInTheDocument()
      expect(screen.getByText('Latest data source configurations and status')).toBeInTheDocument()
    })

    it('shows data source guidance message', () => {
      renderWithProviders(<DashboardClient />)
      expect(screen.getByText(/Connect data sources/i)).toBeInTheDocument()
    })

    // Status badges are shown when real data sources are connected; omitted in initial scaffold
  })

  describe('System Activity Section', () => {
    it('renders system activity section', () => {
      renderWithProviders(<DashboardClient />)

      expect(screen.getByText('System Activity')).toBeInTheDocument()
      expect(screen.getByText('Recent system events and ingestion jobs')).toBeInTheDocument()
    })

    it('renders activity feed', () => {
      renderWithProviders(<DashboardClient />)
      expect(screen.getByText('Ingestion finished')).toBeInTheDocument()
      expect(screen.getByText('Validation warning')).toBeInTheDocument()
    })
  })

  it('has proper semantic structure', () => {
    renderWithProviders(<DashboardClient />)

    // Check heading hierarchy
    const h1 = screen.getByRole('heading', { level: 1 })
    const h3s = screen.getAllByRole('heading', { level: 3 })
    expect(h1).toBeInTheDocument()
    expect(h3s.length).toBeGreaterThanOrEqual(4) // metric cards present
  })

  it('is responsive with grid layouts', () => {
    renderWithProviders(<DashboardClient />)

    // Check responsive grid classes
    const statsGrid = screen.getByText('Data Sources').closest('.grid')
    expect(statsGrid).toHaveClass('grid-cols-1', 'sm:grid-cols-2', 'lg:grid-cols-4')

    const activityGrid = screen.getByText('Recent Data Sources').closest('.grid')
    expect(activityGrid).toHaveClass('grid-cols-1', 'lg:grid-cols-2')
  })

  describe('Data Sources Button', () => {
    beforeEach(() => {
      jest.clearAllMocks()
    })

    it('shows Data Sources button when space is selected', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: 'space-123',
        setCurrentSpaceId: mockSetCurrentSpaceId,
        isLoading: false,
      })

      mockUseResearchSpaces.mockReturnValue({
        data: {
          spaces: [
            { id: 'space-123', name: 'Test Space', slug: 'test-space' },
          ],
        },
        isLoading: false,
      })

      renderWithProviders(<DashboardClient />)

      const dataSourcesLink = screen.getByRole('link', { name: /discover data sources/i })
      expect(dataSourcesLink).toBeInTheDocument()
      expect(dataSourcesLink).toHaveAttribute('href', '/data-discovery')
    })

    it('hides Data Sources button when no space is selected', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: null,
        setCurrentSpaceId: mockSetCurrentSpaceId,
        isLoading: false,
      })

      renderWithProviders(<DashboardClient />)

      expect(screen.queryByRole('link', { name: /data sources/i })).not.toBeInTheDocument()
    })
  })
})
