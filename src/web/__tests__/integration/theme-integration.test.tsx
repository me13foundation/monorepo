import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardPage from '@/app/dashboard/page'

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

  it('theme toggle button appears on dashboard', () => {
    render(<DashboardPage />)
    expect(screen.getByRole('button', { name: /toggle theme/i })).toBeInTheDocument()
  })

  it('theme toggle can be clicked', async () => {
    const user = userEvent.setup()
    const mockSetTheme = jest.fn()

    mockUseTheme.mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
      themes: ['light', 'dark', 'system'],
    })

    render(<DashboardPage />)

    const toggleButton = screen.getByRole('button', { name: /toggle theme/i })
    await user.click(toggleButton)

    expect(mockSetTheme).toHaveBeenCalledWith('dark')
  })

  it('dashboard maintains functionality with theme system', () => {
    render(<DashboardPage />)

    // Verify all dashboard elements are present
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('MED13 Admin Dashboard')
    expect(screen.getByText('Data Sources')).toBeInTheDocument()
    expect(screen.getByText('Recent Data Sources')).toBeInTheDocument()
    expect(screen.getByText('System Activity')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /add data source/i })).toBeInTheDocument()
  })

  it('theme toggle has proper accessibility', () => {
    render(<DashboardPage />)
    const toggleButton = screen.getByRole('button', { name: /toggle theme/i })
    expect(screen.getByText('Toggle theme')).toHaveClass('sr-only')
  })
})
