import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { fetchResearchSpaces } from '@/lib/api/research-spaces'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import { HydrationBoundary } from '@tanstack/react-query'
import { ResearchSpacesList } from '@/components/research-spaces/ResearchSpacesList'

export default async function SpacesPage() {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  // Prefetch with error handling - failures won't block page render
  try {
    await queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.list(),
      queryFn: () => fetchResearchSpaces(undefined, token),
    })
  } catch (error) {
    console.error('[Server Prefetch] Failed to prefetch research spaces:', error)
    // Don't throw - let client retry
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ResearchSpacesList />
    </HydrationBoundary>
  )
}
