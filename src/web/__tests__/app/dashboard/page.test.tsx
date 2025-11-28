import { render, screen } from '@testing-library/react'
import { ThemeProvider } from '@/components/theme-provider'
import DashboardClient from '@/app/(dashboard)/dashboard/dashboard-client'
import { SpaceStatus } from '@/types/research-space'

// Mock ThemeProvider to avoid DOM prop warnings
jest.mock('@/components/theme-provider', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
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
    expires_at: Date.now() + 3600000,
  },
  expires: '2025-12-31T00:00:00.000Z',
}

jest.mock('next-auth/react', () => ({
  useSession: () => ({
    data: mockSession,
    status: 'authenticated',
  }),
  signOut: jest.fn(),
}))

// Mock space context
const mockSetCurrentSpaceId = jest.fn()
const mockUseSpaceContext = jest.fn(() => ({
  currentSpaceId: 'space-1',
  setCurrentSpaceId: mockSetCurrentSpaceId,
  isLoading: false,
}))

jest.mock('@/components/space-context-provider', () => ({
  useSpaceContext: () => mockUseSpaceContext(),
  SpaceContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock research spaces query
const mockUseResearchSpaces = jest.fn(() => ({
  data: {
    spaces: [
      {
        id: 'space-1',
        name: 'Space One',
        slug: 'space-one',
        description: 'First space',
        status: SpaceStatus.ACTIVE,
        tags: [] as string[],
      },
      {
        id: 'space-2',
        name: 'Space Two',
        slug: 'space-two',
        description: 'Second space',
        status: SpaceStatus.ACTIVE,
        tags: [] as string[],
      },
    ],
  },
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
    </ThemeProvider>,
  )
}

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the admin console hero and description', () => {
    renderWithProviders(<DashboardClient />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Admin Console')
    expect(
      screen.getByText(/Select a research space to manage project-level data/i),
    ).toBeInTheDocument()
  })

  it('shows admin actions for creating spaces and opening system settings', () => {
    renderWithProviders(<DashboardClient />)
    expect(screen.getByRole('button', { name: /System Settings/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Space/i })).toBeInTheDocument()
  })

  it('lists research spaces the admin can access', () => {
    renderWithProviders(<DashboardClient />)
    expect(screen.getAllByText('Space One').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Space Two').length).toBeGreaterThan(0)
  })

  it('shows the current space when one is selected', () => {
    renderWithProviders(<DashboardClient />)
    expect(screen.getByText(/Current space/i)).toBeInTheDocument()
    expect(screen.getAllByText('Space One').length).toBeGreaterThan(0)
  })

  it('renders empty state when no spaces are available', () => {
    mockUseResearchSpaces.mockReturnValueOnce({
      data: {
        spaces: [] as Array<{
          id: string
          name: string
          slug: string
          description: string
          status: SpaceStatus
          tags: string[]
        }>,
      },
      isLoading: false,
    })

    renderWithProviders(<DashboardClient />)
    expect(screen.getByText(/No research spaces yet/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create your first space/i })).toBeInTheDocument()
  })
})
