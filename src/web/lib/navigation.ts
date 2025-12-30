/**
 * Navigation utilities for consistent URL handling across the application.
 * 
 * Provides safe navigation functions that handle SSR environments and
 * dynamic origin detection for proper port handling.
 */

/**
 * Navigates to the login page using the current origin.
 * 
 * This ensures the correct port is used regardless of NEXTAUTH_URL configuration.
 * Uses window.location.href for a full page reload to ensure clean state.
 * 
 * @throws Never throws - always navigates even in error cases
 */
export function navigateToLogin(): void {
  if (typeof window === 'undefined') {
    // SSR environment - cannot navigate
    console.warn('navigateToLogin called in SSR environment')
    return
  }

  const loginUrl = `${window.location.origin}/auth/login`
  window.location.href = loginUrl
}

