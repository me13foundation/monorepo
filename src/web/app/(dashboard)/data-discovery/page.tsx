import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { dataDiscoveryKeys } from '@/lib/query-keys/data-discovery'
import {
  fetchDataDiscoverySessions,
  fetchSessionTestResults,
  fetchSourceCatalog,
} from '@/lib/api/data-discovery'
import { HydrationBoundary } from '@tanstack/react-query'
import DataDiscoveryClient from './data-discovery-client'
import { syncDiscoverySessionState } from '@/lib/state/discovery-session-sync'
import type { DataDiscoverySession } from '@/lib/types/data-discovery'

export default async function DataDiscoveryPage() {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  // Prefetch with error handling - failures won't block page render
  const prefetchResults = await Promise.allSettled([
    queryClient.prefetchQuery({
      queryKey: dataDiscoveryKeys.catalog(undefined),
      queryFn: () => fetchSourceCatalog(token),
    }),
    queryClient.prefetchQuery({
      queryKey: dataDiscoveryKeys.sessions(),
      queryFn: () => fetchDataDiscoverySessions(token),
    }),
  ])

  // Log prefetch failures (client will retry)
  prefetchResults.forEach((result, index) => {
    if (result.status === 'rejected') {
      const queryName = index === 0 ? 'source catalog' : 'data discovery sessions'
      console.error(`[Server Prefetch] Failed to prefetch ${queryName}:`, result.reason)
      // Don't throw - let client retry
    }
  })

  const sessionsData =
    queryClient.getQueryData<DataDiscoverySession[]>(dataDiscoveryKeys.sessions()) ?? []

  const { nextSessionId, nextParameters, nextSelectedSources } =
    syncDiscoverySessionState(sessionsData)

  if (nextSessionId) {
    try {
      await queryClient.prefetchQuery({
        queryKey: dataDiscoveryKeys.sessionTests(nextSessionId),
        queryFn: () => fetchSessionTestResults(nextSessionId, token),
      })
    } catch (error) {
      console.error('[Server Prefetch] Failed to prefetch session test results:', error)
      // Don't throw - let client retry
    }
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <DataDiscoveryClient
        initialSessionId={nextSessionId}
        initialParameters={nextParameters}
        initialSelectedSources={nextSelectedSources}
      />
    </HydrationBoundary>
  )
}
