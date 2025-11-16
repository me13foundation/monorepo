import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { HydrationBoundary } from '@tanstack/react-query'
import { fetchTemplate } from '@/lib/api/templates'
import TemplateDetailClient from './template-detail-client'

interface TemplateDetailPageProps {
  params: {
    templateId: string
  }
}

export default async function TemplateDetailPage({ params }: TemplateDetailPageProps) {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()

  // Prefetch with error handling - failures won't block page render
  try {
    await queryClient.prefetchQuery({
      queryKey: ['template', params.templateId],
      queryFn: () => fetchTemplate(params.templateId, token),
    })
  } catch (error) {
    console.error('[Server Prefetch] Failed to prefetch template:', error)
    // Don't throw - let client retry
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TemplateDetailClient templateId={params.templateId} />
    </HydrationBoundary>
  )
}
