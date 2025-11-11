import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { HydrationBoundary } from '@tanstack/react-query'
import { fetchTemplates } from '@/lib/api/templates'
import TemplatesClient from './templates-client'

export default async function TemplatesPage() {
  const session = await getServerSession(authOptions)
  if (!session) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()
  await queryClient.prefetchQuery({
    queryKey: ['templates', 'available'],
    queryFn: () => fetchTemplates('available'),
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TemplatesClient />
    </HydrationBoundary>
  )
}
