import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Header } from '@/components/navigation/Header'
import { useSignOut } from '@/hooks/use-sign-out'
import { useSpaceContext } from '@/components/space-context-provider'
import { SpaceSelector } from '@/components/research-spaces/SpaceSelector'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock dependencies
jest.mock('next-auth/react', () => ({
  useSession: jest.fn(),
}))

jest.mock('@/hooks/use-sign-out', () => ({
  useSignOut: jest.fn(),
}))

jest.mock('@/components/space-context-provider', () => ({
  useSpaceContext: jest.fn(),
}))

jest.mock('@/components/research-spaces/SpaceSelector', () => ({
  SpaceSelector: jest.fn(({ currentSpaceId }) => (
    <div data-testid="space-selector">Space Selector {currentSpaceId || 'none'}</div>
  )),
}))

jest.mock('@/components/navigation/UserMenu', () => ({
  UserMenu: () => <button data-testid="user-menu">User Menu</button>,
}))

import { useSession } from 'next-auth/react'

describe('Header Component', () => {
  const renderWithClient = (ui: React.ReactElement) =>
    render(
      <QueryClientProvider client={new QueryClient()}>
        {ui}
      </QueryClientProvider>,
    )

  const mockUseSession = useSession as jest.MockedFunction<typeof useSession>
  const mockUseSignOut = useSignOut as jest.MockedFunction<typeof useSignOut>
  const mockUseSpaceContext = useSpaceContext as jest.MockedFunction<typeof useSpaceContext>

  const mockSignOut = jest.fn()
  const mockSession = {
    user: {
      id: 'user-1',
      email: 'test@example.com',
      role: 'admin',
    },
  }

  beforeEach(() => {
    jest.clearAllMocks()

    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated',
      update: jest.fn(),
    } as any)

    mockUseSignOut.mockReturnValue({
      signOut: mockSignOut,
      isSigningOut: false,
    })

    mockUseSpaceContext.mockReturnValue({
      currentSpaceId: null,
      setCurrentSpaceId: jest.fn(),
      isLoading: false,
    })
  })

  describe('Rendering', () => {
    it('renders all navigation elements', () => {
      renderWithClient(<Header />)

      expect(screen.getByText('MED13 Admin')).toBeInTheDocument()
      expect(screen.getByTestId('space-selector')).toBeInTheDocument()
      expect(screen.getByTestId('user-menu')).toBeInTheDocument()
    })

    it('does not show Data Sources button in header (moved to dashboard)', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: 'space-123',
        setCurrentSpaceId: jest.fn(),
        isLoading: false,
      })

      renderWithClient(<Header />)

      // Data Sources button is no longer in the header
      expect(screen.queryByRole('link', { name: /data sources/i })).not.toBeInTheDocument()
    })

    it('renders UserMenu component', () => {
      renderWithClient(<Header />)

      expect(screen.getByTestId('user-menu')).toBeInTheDocument()
    })

    it('renders dashboard logo link', () => {
      renderWithClient(<Header />)

      const logoLink = screen.getByRole('link', { name: /med13 admin/i })
      expect(logoLink).toBeInTheDocument()
      expect(logoLink).toHaveAttribute('href', '/dashboard')
    })
  })

  describe('UserMenu Integration', () => {
    it('renders UserMenu component', () => {
      renderWithClient(<Header />)

      expect(screen.getByTestId('user-menu')).toBeInTheDocument()
    })
  })

  describe('Space Selector Integration', () => {
    it('passes currentSpaceId to SpaceSelector', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: 'space-456',
        setCurrentSpaceId: jest.fn(),
        isLoading: false,
      })

      renderWithClient(<Header />)

      expect(SpaceSelector).toHaveBeenCalledWith(
        { currentSpaceId: 'space-456' },
        expect.any(Object)
      )
    })

    it('passes undefined to SpaceSelector when no space is selected', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: null,
        setCurrentSpaceId: jest.fn(),
        isLoading: false,
      })

      renderWithClient(<Header />)

      expect(SpaceSelector).toHaveBeenCalledWith(
        { currentSpaceId: undefined },
        expect.any(Object)
      )
    })
  })

  describe('User Session Handling', () => {
    it('handles missing session gracefully', () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      } as any)

      renderWithClient(<Header />)

      // Should still render, but role might not be visible
      expect(screen.getByText('MED13 Admin')).toBeInTheDocument()
    })

    it('handles different user roles', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: {
            id: 'user-2',
            email: 'researcher@example.com',
            role: 'researcher',
          },
        },
        status: 'authenticated',
        update: jest.fn(),
      } as any)

      renderWithClient(<Header />)

      // UserMenu component handles role display now
      expect(screen.getByTestId('user-menu')).toBeInTheDocument()
    })
  })
})
