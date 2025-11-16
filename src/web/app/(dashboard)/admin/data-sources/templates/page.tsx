import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { HydrationBoundary } from '@tanstack/react-query'
import { fetchTemplates } from '@/lib/api/templates'
import TemplatesClient from './templates-client'

export default async function TemplatesPage() {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  // Prefetch with error handling - failures won't block page render
  try {
    await queryClient.prefetchQuery({
      queryKey: ['templates', 'available'],
      queryFn: () => fetchTemplates('available', token),
    })
  } catch (error) {
    console.error('[Server Prefetch] Failed to prefetch templates:', error)
    // Don't throw - let client retry
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TemplatesClient />
    </HydrationBoundary>
  )
}
