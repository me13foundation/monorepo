'use client'

import { useEffect } from 'react'
import { useParams } from 'next/navigation'
import { useSpaceContext } from '@/components/space-context-provider'
import { DataSourcesList } from '@/components/data-sources/DataSourcesList'

export default function SpaceDataSourcesPage() {
  const params = useParams()
  const spaceId = params.spaceId as string
  const { setCurrentSpaceId } = useSpaceContext()

  useEffect(() => {
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }
  }, [spaceId, setCurrentSpaceId])

  if (!spaceId) {
    return null
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Space Data Sources</h1>
        <p className="text-muted-foreground mt-1">
          Manage the data sources that belong to this research space.
        </p>
      </div>
      <DataSourcesList spaceId={spaceId} />
    </div>
  )
}
