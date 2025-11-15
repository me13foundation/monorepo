import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { HydrationBoundary } from '@tanstack/react-query'
import { authOptions } from '@/lib/auth'
import { spaceDiscoveryKeys } from '@/lib/query-keys/space-discovery'
import { fetchSpaceSourceCatalog, fetchSpaceDiscoverySessions } from '@/lib/api/space-discovery'
import SpaceDiscoveryClient from './space-discovery-client'

interface SpaceDiscoveryPageProps {
  params: {
    spaceId: string
  }
}

export default async function SpaceDiscoveryPage({ params }: SpaceDiscoveryPageProps) {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  await Promise.allSettled([
    queryClient.prefetchQuery({
      queryKey: spaceDiscoveryKeys.catalog(params.spaceId, undefined),
      queryFn: () => fetchSpaceSourceCatalog(params.spaceId, token),
    }),
    queryClient.prefetchQuery({
      queryKey: spaceDiscoveryKeys.sessions(params.spaceId),
      queryFn: () => fetchSpaceDiscoverySessions(params.spaceId, token),
    }),
  ])

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <SpaceDiscoveryClient spaceId={params.spaceId} />
    </HydrationBoundary>
  )
}
