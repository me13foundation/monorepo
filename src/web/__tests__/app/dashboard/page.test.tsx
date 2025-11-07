import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardPage from '@/app/dashboard/page'
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
    refresh_token: 'test-refresh-token',
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

// Mock ProtectedRoute to render children directly
jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>
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
    renderWithProviders(<DashboardPage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('MED13 Admin Dashboard')
  })

  it('renders the dashboard subtitle', () => {
    renderWithProviders(<DashboardPage />)
    expect(screen.getByText('Welcome back, Test Admin')).toBeInTheDocument()
  })

  it('renders theme toggle button', () => {
    renderWithProviders(<DashboardPage />)
    const themeButton = screen.getByRole('button', { name: /toggle theme/i })
    expect(themeButton).toBeInTheDocument()
  })

  it('renders action buttons', () => {
    renderWithProviders(<DashboardPage />)
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /add data source/i })).toBeInTheDocument()
  })

  describe('Statistics Cards', () => {
    it('renders all metric cards', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('Data Sources')).toBeInTheDocument()
      expect(screen.getByText('Total Records')).toBeInTheDocument()
      expect(screen.getByText('Active Users')).toBeInTheDocument()
      expect(screen.getByText('System Health')).toBeInTheDocument()
    })

    it('displays metric values from API', () => {
      renderWithProviders(<DashboardPage />)
      expect(screen.getByText('1')).toBeInTheDocument() // Data Sources (evidence count)
      expect(screen.getByText('10')).toBeInTheDocument() // Total Records
      expect(screen.getByText('2')).toBeInTheDocument() // Genes count
      expect(screen.getByText('90%')).toBeInTheDocument() // Approx approval rate
    })

    it('displays metric descriptions', () => {
      renderWithProviders(<DashboardPage />)
      expect(screen.getByText(/Approved 9/i)).toBeInTheDocument()
      expect(screen.getByText(/Total records across entities/i)).toBeInTheDocument()
      expect(screen.getByText(/Total genes in knowledge base/i)).toBeInTheDocument()
      expect(screen.getByText(/Approximate approval rate/i)).toBeInTheDocument()
    })
  })

  describe('Data Sources Section', () => {
    it('renders data sources section', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('Recent Data Sources')).toBeInTheDocument()
      expect(screen.getByText('Latest data source configurations and status')).toBeInTheDocument()
    })

    it('shows data source guidance message', () => {
      renderWithProviders(<DashboardPage />)
      expect(screen.getByText(/Connect data sources/i)).toBeInTheDocument()
    })

    // Status badges are shown when real data sources are connected; omitted in initial scaffold
  })

  describe('System Activity Section', () => {
    it('renders system activity section', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('System Activity')).toBeInTheDocument()
      expect(screen.getByText('Recent system events and ingestion jobs')).toBeInTheDocument()
    })

    it('renders activity feed', () => {
      renderWithProviders(<DashboardPage />)
      expect(screen.getByText('Ingestion finished')).toBeInTheDocument()
      expect(screen.getByText('Validation warning')).toBeInTheDocument()
    })
  })

  it('has proper semantic structure', () => {
    renderWithProviders(<DashboardPage />)

    // Check for header landmark
    expect(screen.getByRole('banner')).toBeInTheDocument()

    // Check for main content area
    expect(screen.getByRole('main')).toBeInTheDocument()

    // Check heading hierarchy
    const h1 = screen.getByRole('heading', { level: 1 })
    const h3s = screen.getAllByRole('heading', { level: 3 })
    expect(h1).toBeInTheDocument()
    expect(h3s.length).toBeGreaterThanOrEqual(4) // metric cards present
  })

  it('applies proper CSS classes', () => {
    renderWithProviders(<DashboardPage />)

    // Check main container
    const main = screen.getByRole('main')
    expect(main).toHaveClass('max-w-7xl', 'mx-auto', 'px-4', 'sm:px-6', 'lg:px-8', 'py-8')

    // Check header styling
    const header = screen.getByRole('banner')
    expect(header).toHaveClass('bg-card', 'shadow-sm', 'border-b', 'border-border')
  })

  it('is responsive with grid layouts', () => {
    renderWithProviders(<DashboardPage />)

    // Check responsive grid classes
    const statsGrid = screen.getByText('Data Sources').closest('.grid')
    expect(statsGrid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4')

    const activityGrid = screen.getByText('Recent Data Sources').closest('.grid')
    expect(activityGrid).toHaveClass('grid-cols-1', 'lg:grid-cols-2')
  })
})
