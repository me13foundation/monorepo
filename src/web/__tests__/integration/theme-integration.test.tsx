import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardClient from '@/app/(dashboard)/dashboard/dashboard-client'

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
jest.mock('@/components/space-context-provider', () => ({
  useSpaceContext: () => ({
    currentSpaceId: null,
    setCurrentSpaceId: jest.fn(),
    isLoading: false,
  }),
  SpaceContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock research spaces query
jest.mock('@/lib/queries/research-spaces', () => ({
  useResearchSpaces: () => ({
    data: { spaces: [] },
    isLoading: false,
  }),
}))

// Mock next-themes for integration testing
jest.mock('next-themes', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useTheme: jest.fn(),
}))

import { useTheme } from 'next-themes'

describe('Theme Integration', () => {
  const mockUseTheme = useTheme as jest.MockedFunction<typeof useTheme>

  beforeEach(() => {
    mockUseTheme.mockClear()
    mockUseTheme.mockReturnValue({
      theme: 'light',
      setTheme: jest.fn(),
      themes: ['light', 'dark', 'system'],
    })
  })

  // Note: Theme toggle is now in Header component, tested separately

  it('dashboard maintains functionality with theme system', () => {
    render(<DashboardClient />)

    // Verify all dashboard elements are present
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('MED13 Admin Dashboard')
    expect(screen.getByText('Data Sources')).toBeInTheDocument()
    expect(screen.getByText('Recent Data Sources')).toBeInTheDocument()
    expect(screen.getByText('System Activity')).toBeInTheDocument()
    // Note: Action buttons are now in Header component
  })

  // Note: Theme toggle accessibility is tested in Header component tests
})
// Mock React Query dashboard hooks to avoid QueryClient in tests
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
    data: { activities: [], total: 0 },
    isLoading: false,
  }),
}))
