import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { fetchResearchSpace, fetchSpaceMembers } from '@/lib/api/research-spaces'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { HydrationBoundary } from '@tanstack/react-query'
import SpaceDetailClient from './space-detail-client'

interface SpaceDetailPageProps {
  params: {
    spaceId: string
  }
}

export default async function SpaceDetailPage({ params }: SpaceDetailPageProps) {
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
  ])

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <SpaceDetailClient spaceId={params.spaceId} />
    </HydrationBoundary>
  )
}
