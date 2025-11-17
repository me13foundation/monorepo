import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { HydrationBoundary, QueryClient, dehydrate } from '@tanstack/react-query'
import { authOptions } from '@/lib/auth'
import SystemSettingsClient from './system-settings-client'
import { fetchUsers, fetchUserStatistics } from '@/lib/api/users'
import { fetchStorageConfigurations } from '@/lib/api/storage'
import { fetchMaintenanceState } from '@/lib/api/system-status'
import { userKeys } from '@/lib/query-keys/users'
import { storageKeys } from '@/lib/query-keys/storage'
import { INITIAL_USER_PARAMS } from './constants'

export default async function SystemSettingsPage() {
  const session = await getServerSession(authOptions)

  if (!session) {
    redirect('/auth/login?error=SessionExpired')
  }

  if (session.user.role !== 'admin') {
    redirect('/dashboard?error=AdminOnly')
  }

  const token = session.user.access_token
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
      queryKey: storageKeys.list(token),
      queryFn: () => fetchStorageConfigurations(token),
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
