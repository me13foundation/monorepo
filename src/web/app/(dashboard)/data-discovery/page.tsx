import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { DataDiscoveryContent } from '@/components/data-discovery/DataDiscoveryContent'
import { fetchSessionState } from '@/app/actions/data-discovery'
import { apiClient, authHeaders } from '@/lib/api/client'
import { SourceCatalogEntry } from '@/types/generated'

// Helper to fetch catalog on server
async function fetchCatalog(token: string) {
  try {
    const response = await apiClient.get<SourceCatalogEntry[]>(
      '/data-discovery/catalog',
      authHeaders(token)
    )
    return response.data
  } catch (error) {
    console.error("Failed to fetch catalog", error)
    return []
  }
}

export default async function DataDiscoveryPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined }
}) {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect('/auth/login?error=SessionExpired')
  }

  const sessionId = typeof searchParams.session_id === 'string' ? searchParams.session_id : null

  let sessionState = undefined
  const catalog = await fetchCatalog(token)

  if (sessionId) {
    try {
      sessionState = await fetchSessionState(sessionId)
    } catch (error) {
      console.error("Failed to fetch session state:", error)
      // Fallback to empty/new session state or redirect if critical
    }
  }

  return (
    <DataDiscoveryContent
      spaceId="default" // TODO: Extract from context/params
      sessionState={sessionState}
      catalog={catalog}
    />
  )
}
