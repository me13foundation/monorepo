import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
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

  return <SpaceCurationClient spaceId={params.spaceId} />
}
