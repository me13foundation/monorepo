import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import KnowledgeGraphClient from '../knowledge-graph-client'

interface KnowledgeGraphPageProps {
  params: {
    spaceId: string
  }
}

export default async function KnowledgeGraphPage({ params }: KnowledgeGraphPageProps) {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  return <KnowledgeGraphClient spaceId={params.spaceId} />
}
