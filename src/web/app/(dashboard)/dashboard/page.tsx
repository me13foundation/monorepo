import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { HydrationBoundary, QueryClient, dehydrate } from '@tanstack/react-query'
import { authOptions } from '@/lib/auth'
import { fetchResearchSpaces } from '@/lib/api/research-spaces'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import DashboardClient from './dashboard-client'
import { UserRole } from '@/types/auth'

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)

  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  if (session.user.role !== UserRole.ADMIN) {
    redirect('/spaces?error=AdminOnly')
  }

  const queryClient = new QueryClient()

  const prefetchResults = await Promise.allSettled([
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.list(),
      queryFn: () => fetchResearchSpaces(undefined, token),
    }),
  ])

  prefetchResults.forEach((result) => {
    if (result.status === 'rejected') {
      console.error('[Server Prefetch] Failed to prefetch research spaces:', result.reason)
    }
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <DashboardClient />
    </HydrationBoundary>
  )
}
