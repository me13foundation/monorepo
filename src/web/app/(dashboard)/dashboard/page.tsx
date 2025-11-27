import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { HydrationBoundary, QueryClient, dehydrate } from '@tanstack/react-query'
import { authOptions } from '@/lib/auth'
import { fetchDashboardStats, fetchRecentActivities } from '@/lib/api'
import { fetchResearchSpaces } from '@/lib/api/research-spaces'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import DashboardClient from './dashboard-client'
import { dashboardKeys } from '@/lib/query-keys/dashboard'

const RECENT_ACTIVITY_LIMIT = 5

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)

  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  // Prefetch with error handling - failures won't block page render
  const prefetchResults = await Promise.allSettled([
    queryClient.prefetchQuery({
      queryKey: dashboardKeys.stats(token),
      queryFn: () => fetchDashboardStats(token),
    }),
    queryClient.prefetchQuery({
      queryKey: dashboardKeys.activities(RECENT_ACTIVITY_LIMIT, token),
      queryFn: () => fetchRecentActivities(RECENT_ACTIVITY_LIMIT, token),
    }),
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.list(),
      queryFn: () => fetchResearchSpaces(undefined, token),
    }),
  ])

  // Log prefetch failures (client will retry)
  prefetchResults.forEach((result, index) => {
    if (result.status === 'rejected') {
      const queryNames = ['dashboard stats', 'recent activities', 'research spaces']
      const queryName = queryNames[index] || 'unknown'
      console.error(`[Server Prefetch] Failed to prefetch ${queryName}:`, result.reason)
      // Don't throw - let client retry
    }
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <DashboardClient />
    </HydrationBoundary>
  )
}
