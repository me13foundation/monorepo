import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import {
  fetchResearchSpace,
  fetchSpaceMembers,
  fetchSpaceCurationStats,
  fetchSpaceCurationQueue,
} from '@/lib/api/research-spaces'
import { HydrationBoundary } from '@tanstack/react-query'
import SpaceCurationClient from '../space-curation-client'

interface SpaceCurationPageProps {
  params: {
    spaceId: string
  }
}

export default async function SpaceCurationPage({ params }: SpaceCurationPageProps) {
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
      queryKey: researchSpaceKeys.curationStats(params.spaceId),
      queryFn: () => fetchSpaceCurationStats(params.spaceId, token),
    }),
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.curationQueue(params.spaceId, { limit: 10 }),
      queryFn: () => fetchSpaceCurationQueue(params.spaceId, { limit: 10 }, token),
    }),
  ])

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <SpaceCurationClient spaceId={params.spaceId} />
    </HydrationBoundary>
  )
}
