import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardPage from '@/app/dashboard/page'
import { SessionProvider } from '@/components/session-provider'
import { ThemeProvider } from '@/components/theme-provider'

// Mock NextAuth session
const mockSession = {
  user: {
    id: 'test-user-id',
    email: 'admin@med13.org',
    name: 'Test Admin',
    role: 'admin'
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
    expect(screen.getByText('Welcome back, admin@med13.org')).toBeInTheDocument()
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

    it('displays correct metric values', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('12')).toBeInTheDocument() // Data Sources
      expect(screen.getByText('1,234,567')).toBeInTheDocument() // Total Records
      expect(screen.getByText('24')).toBeInTheDocument() // Active Users
      expect(screen.getByText('98.5%')).toBeInTheDocument() // System Health
    })

    it('displays metric descriptions', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('8 active, 2 paused, 2 error')).toBeInTheDocument()
      expect(screen.getByText('+12% from last month')).toBeInTheDocument()
      expect(screen.getByText('5 admins, 19 researchers')).toBeInTheDocument()
      expect(screen.getByText('All systems operational')).toBeInTheDocument()
    })
  })

  describe('Data Sources Section', () => {
    it('renders data sources section', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('Recent Data Sources')).toBeInTheDocument()
      expect(screen.getByText('Latest data source configurations and status')).toBeInTheDocument()
    })

    it('renders sample data sources', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('ClinVar API')).toBeInTheDocument()
      expect(screen.getByText('HGMD Database')).toBeInTheDocument()
      expect(screen.getByText('OMIM CSV Upload')).toBeInTheDocument()
      expect(screen.getByText('PubMed API')).toBeInTheDocument()
    })

    it('displays data source metadata', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('API • 2 hours ago')).toBeInTheDocument()
      expect(screen.getByText('Database • 1 day ago')).toBeInTheDocument()
      expect(screen.getByText('File • 3 days ago')).toBeInTheDocument()
      expect(screen.getByText('API • 1 week ago')).toBeInTheDocument()
    })

    it('shows status badges', () => {
      renderWithProviders(<DashboardPage />)

      const activeBadges = screen.getAllByText('active')
      expect(activeBadges).toHaveLength(2) // ClinVar and HGMD

      expect(screen.getByText('error')).toBeInTheDocument() // OMIM
      expect(screen.getByText('paused')).toBeInTheDocument() // PubMed
    })
  })

  describe('System Activity Section', () => {
    it('renders system activity section', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('System Activity')).toBeInTheDocument()
      expect(screen.getByText('Recent system events and ingestion jobs')).toBeInTheDocument()
    })

    it('renders activity feed', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('Data ingestion completed')).toBeInTheDocument()
      expect(screen.getByText('Quality check failed')).toBeInTheDocument()
      expect(screen.getByText('User login')).toBeInTheDocument()
      expect(screen.getByText('Data source updated')).toBeInTheDocument()
    })

    it('displays activity metadata', () => {
      renderWithProviders(<DashboardPage />)

      expect(screen.getByText('ClinVar API • 2 hours ago')).toBeInTheDocument()
      expect(screen.getByText('OMIM CSV • 3 hours ago')).toBeInTheDocument()
      expect(screen.getByText('john.doe@example.com • 4 hours ago')).toBeInTheDocument()
      expect(screen.getByText('PubMed API • 5 hours ago')).toBeInTheDocument()
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
    expect(h3s).toHaveLength(6) // 4 metric cards + 2 sections
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
