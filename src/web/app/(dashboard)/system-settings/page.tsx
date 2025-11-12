import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { HydrationBoundary, QueryClient, dehydrate } from '@tanstack/react-query'
import { authOptions } from '@/lib/auth'
import SystemSettingsClient from './system-settings-client'
import {
  fetchUsers,
  fetchUserStatistics,
  type UserListParams,
} from '@/lib/api/users'
import { userKeys } from '@/lib/query-keys/users'

export const INITIAL_USER_PARAMS: UserListParams = {
  skip: 0,
  limit: 25,
}

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
  ])

  prefetched.forEach((result, index) => {
    if (result.status === 'rejected') {
      const target = index === 0 ? 'user list' : 'user stats'
      console.error(`[SystemSettingsPage] Failed to prefetch ${target}:`, result.reason)
    }
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <SystemSettingsClient initialParams={INITIAL_USER_PARAMS} />
    </HydrationBoundary>
  )
}
