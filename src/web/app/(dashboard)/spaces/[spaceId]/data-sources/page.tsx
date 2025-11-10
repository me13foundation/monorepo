'use client'

import { useEffect } from 'react'
import { useParams } from 'next/navigation'
import { useSpaceContext } from '@/components/space-context-provider'
import { DataSourcesList } from '@/components/data-sources/DataSourcesList'
import { PageHero, DashboardSection } from '@/components/ui/composition-patterns'

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
      <PageHero
        title="Space Data Sources"
        description="Manage ingestion pipelines, review quality metrics, and keep this research space’s data sources aligned with curation goals."
        variant="research"
      />
      <DashboardSection title="Sources" description="All data sources attached to this space">
        <DataSourcesList spaceId={spaceId} />
      </DashboardSection>
    </div>
  )
}
