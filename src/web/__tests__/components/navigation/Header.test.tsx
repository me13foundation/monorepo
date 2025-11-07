import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Header } from '@/components/navigation/Header'
import { useSignOut } from '@/hooks/use-sign-out'
import { useSpaceContext } from '@/components/space-context-provider'
import { SpaceSelector } from '@/components/research-spaces/SpaceSelector'

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

jest.mock('@/components/theme-toggle', () => ({
  ThemeToggle: () => <button data-testid="theme-toggle">Theme Toggle</button>,
}))

import { useSession } from 'next-auth/react'

describe('Header Component', () => {
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
      render(<Header />)

      expect(screen.getByText('MED13 Admin')).toBeInTheDocument()
      expect(screen.getByTestId('space-selector')).toBeInTheDocument()
      expect(screen.getByTestId('theme-toggle')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
    })

    it('displays user role correctly', () => {
      render(<Header />)

      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    it('shows Data Sources button when currentSpaceId is set', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: 'space-123',
        setCurrentSpaceId: jest.fn(),
        isLoading: false,
      })

      render(<Header />)

      const dataSourcesLink = screen.getByRole('link', { name: /data sources/i })
      expect(dataSourcesLink).toBeInTheDocument()
      expect(dataSourcesLink).toHaveAttribute('href', '/spaces/space-123/data-sources')
    })

    it('hides Data Sources button when currentSpaceId is null', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: null,
        setCurrentSpaceId: jest.fn(),
        isLoading: false,
      })

      render(<Header />)

      expect(screen.queryByRole('link', { name: /data sources/i })).not.toBeInTheDocument()
    })

    it('renders Settings link', () => {
      render(<Header />)

      const settingsLink = screen.getByRole('link', { name: /settings/i })
      expect(settingsLink).toBeInTheDocument()
      expect(settingsLink).toHaveAttribute('href', '/settings')
    })

    it('renders dashboard logo link', () => {
      render(<Header />)

      const logoLink = screen.getByRole('link', { name: /med13 admin/i })
      expect(logoLink).toBeInTheDocument()
      expect(logoLink).toHaveAttribute('href', '/dashboard')
    })
  })

  describe('Sign Out Functionality', () => {
    it('handles sign-out flow correctly', async () => {
      const user = userEvent.setup()
      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      await user.click(signOutButton)

      expect(mockSignOut).toHaveBeenCalledTimes(1)
    })

    it('shows loading state during sign-out', () => {
      mockUseSignOut.mockReturnValue({
        signOut: mockSignOut,
        isSigningOut: true,
      })

      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /signing out/i })
      expect(signOutButton).toBeInTheDocument()
      expect(signOutButton).toBeDisabled()
      expect(signOutButton).toHaveAttribute('aria-busy', 'true')
    })

    it('shows normal state when not signing out', () => {
      mockUseSignOut.mockReturnValue({
        signOut: mockSignOut,
        isSigningOut: false,
      })

      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      expect(signOutButton).toBeInTheDocument()
      expect(signOutButton).not.toBeDisabled()
      expect(signOutButton).toHaveAttribute('aria-busy', 'false')
    })
  })

  describe('Accessibility', () => {
    it('has aria-label on sign out button', () => {
      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      expect(signOutButton).toHaveAttribute('aria-label', 'Sign out')
    })

    it('updates aria-label during sign-out', () => {
      mockUseSignOut.mockReturnValue({
        signOut: mockSignOut,
        isSigningOut: true,
      })

      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /signing out/i })
      expect(signOutButton).toHaveAttribute('aria-label', 'Signing out...')
    })

    it('has aria-busy attribute on sign out button', () => {
      mockUseSignOut.mockReturnValue({
        signOut: mockSignOut,
        isSigningOut: true,
      })

      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /signing out/i })
      expect(signOutButton).toHaveAttribute('aria-busy', 'true')
    })

    it('has aria-busy false when not signing out', () => {
      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      expect(signOutButton).toHaveAttribute('aria-busy', 'false')
    })
  })

  describe('Space Selector Integration', () => {
    it('passes currentSpaceId to SpaceSelector', () => {
      mockUseSpaceContext.mockReturnValue({
        currentSpaceId: 'space-456',
        setCurrentSpaceId: jest.fn(),
        isLoading: false,
      })

      render(<Header />)

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

      render(<Header />)

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

      render(<Header />)

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

      render(<Header />)

      expect(screen.getByText('researcher')).toBeInTheDocument()
    })
  })

  describe('Button States', () => {
    it('disables sign out button during sign-out', () => {
      mockUseSignOut.mockReturnValue({
        signOut: mockSignOut,
        isSigningOut: true,
      })

      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /signing out/i })
      expect(signOutButton).toBeDisabled()
    })

    it('enables sign out button when not signing out', () => {
      render(<Header />)

      const signOutButton = screen.getByRole('button', { name: /sign out/i })
      expect(signOutButton).not.toBeDisabled()
    })
  })
})
