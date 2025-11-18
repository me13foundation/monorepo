import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import type { Session } from 'next-auth'
import { HydrationBoundary, QueryClient, dehydrate } from '@tanstack/react-query'
import { authOptions } from '@/lib/auth'
import SystemSettingsClient from './system-settings-client'
import { fetchUsers, fetchUserStatistics } from '@/lib/api/users'
import { fetchStorageConfigurations, fetchStorageOverview } from '@/lib/api/storage'
import { fetchMaintenanceState } from '@/lib/api/system-status'
import { userKeys } from '@/lib/query-keys/users'
import { storageKeys } from '@/lib/query-keys/storage'
import { INITIAL_USER_PARAMS } from './constants'

type AdminSession = Session & {
  user?: Session['user'] & {
    role?: string
    access_token?: string
  }
}

export default async function SystemSettingsPage() {
  const isE2ETestMode = process.env.E2E_TEST_MODE === 'playwright'
  let session = (await getServerSession(authOptions)) as AdminSession | null

  if (isE2ETestMode) {
    session = {
      user: {
        id: 'playwright-admin',
        role: 'admin',
        email: 'playwright@med13.dev',
        username: 'playwright-admin',
        full_name: 'Playwright Admin',
        email_verified: true,
        name: 'Playwright Admin',
        access_token: 'playwright-token',
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      },
      expires: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    }
  }

  if (!session) {
    redirect('/auth/login?error=SessionExpired')
  }

  if (session.user?.role !== 'admin') {
    redirect('/dashboard?error=AdminOnly')
  }

  const token = session.user?.access_token
  if (!token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  const prefetched = await Promise.allSettled([
    queryClient.prefetchQuery({
      queryKey: userKeys.list(INITIAL_USER_PARAMS, token),
      queryFn: () => fetchUsers(INITIAL_USER_PARAMS, token),
    }),
    queryClient.prefetchQuery({
      queryKey: userKeys.stats(token),
      queryFn: () => fetchUserStatistics(token),
    }),
    queryClient.prefetchQuery({
      queryKey: storageKeys.list(token, 1, 100, true),
      queryFn: () =>
        fetchStorageConfigurations(
          { page: 1, per_page: 100, include_disabled: true },
          token,
        ),
    }),
    queryClient.prefetchQuery({
      queryKey: storageKeys.stats(token),
      queryFn: () => fetchStorageOverview(token),
    }),
    queryClient.prefetchQuery({
      queryKey: ['system-status', 'maintenance', token] as const,
      queryFn: () => fetchMaintenanceState(token),
    }),
  ])

  prefetched.forEach((result, index) => {
    if (result.status === 'rejected') {
      const target = ['user list', 'user stats', 'storage configurations', 'maintenance state'][index] ?? 'system setting'
      console.error(`[SystemSettingsPage] Failed to prefetch ${target}:`, result.reason)
    }
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <SystemSettingsClient initialParams={INITIAL_USER_PARAMS} />
    </HydrationBoundary>
  )
}
