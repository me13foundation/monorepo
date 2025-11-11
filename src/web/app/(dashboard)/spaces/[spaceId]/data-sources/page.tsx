import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import { fetchResearchSpace, fetchSpaceMembers } from '@/lib/api/research-spaces'
import { HydrationBoundary } from '@tanstack/react-query'
import SpaceDataSourcesClient from '../space-data-sources-client'
import { dataSourceKeys } from '@/lib/query-keys/data-sources'
import { fetchDataSourcesBySpace } from '@/lib/api/data-sources'

interface SpaceDataSourcesPageProps {
  params: {
    spaceId: string
  }
}

export default async function SpaceDataSourcesPage({ params }: SpaceDataSourcesPageProps) {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  await Promise.allSettled([
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.detail(params.spaceId),
      queryFn: () => fetchResearchSpace(params.spaceId, token),
    }),
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.members(params.spaceId),
      queryFn: () => fetchSpaceMembers(params.spaceId, undefined, token),
    }),
    queryClient.prefetchQuery({
      queryKey: dataSourceKeys.space(params.spaceId),
      queryFn: () => fetchDataSourcesBySpace(params.spaceId, {}, token),
    }),
  ])

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <SpaceDataSourcesClient spaceId={params.spaceId} />
    </HydrationBoundary>
  )
}
