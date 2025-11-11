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
  if (!session) {
    redirect('/auth/login?error=SessionExpired')
  }

  const queryClient = new QueryClient()
  await queryClient.prefetchQuery({
    queryKey: ['template', params.templateId],
    queryFn: () => fetchTemplate(params.templateId),
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TemplateDetailClient templateId={params.templateId} />
    </HydrationBoundary>
  )
}
