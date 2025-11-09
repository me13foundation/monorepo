'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSpaceContext } from '@/components/space-context-provider'
import { useParams } from 'next/navigation'

export default function SpaceDataSourcesPage() {
  const router = useRouter()
  const params = useParams()
  const spaceId = params.spaceId as string
  const { setCurrentSpaceId } = useSpaceContext()

  useEffect(() => {
    // Set the current space context for consistency
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }

    // Redirect to the Research Data Workbench
    router.replace('/workbench')
  }, [spaceId, setCurrentSpaceId, router])

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Redirecting to Research Data Workbench...</p>
      </div>
    </div>
  )
}
