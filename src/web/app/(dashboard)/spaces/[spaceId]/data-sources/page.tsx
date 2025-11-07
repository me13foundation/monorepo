'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DataSourcesList } from '@/components/data-sources/DataSourcesList'
import { useSpaceContext } from '@/components/space-context-provider'
import { useParams } from 'next/navigation'
import { useEffect } from 'react'

export default function SpaceDataSourcesPage() {
  const params = useParams()
  const spaceId = params.spaceId as string
  const { setCurrentSpaceId } = useSpaceContext()

  useEffect(() => {
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }
  }, [spaceId, setCurrentSpaceId])

  return (
    <ProtectedRoute>
      <div>
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Data Sources</h1>
          <p className="text-muted-foreground mt-1">
            Manage data sources for this research space
          </p>
        </div>
        <DataSourcesList spaceId={spaceId} />
      </div>
    </ProtectedRoute>
  )
}
