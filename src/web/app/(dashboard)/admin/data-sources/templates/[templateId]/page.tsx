import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
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

  let template = null

  try {
    template = await fetchTemplate(params.templateId, token)
  } catch (error) {
    console.error('[TemplateDetailPage] Failed to fetch template:', error)
  }

  return <TemplateDetailClient templateId={params.templateId} template={template} />
}
