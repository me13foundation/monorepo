'use client'

import type { OrchestratedSessionState, SourceCatalogEntry } from '@/types/generated'
import { DataSourcesList } from '@/components/data-sources/DataSourcesList'

interface SpaceDataSourcesClientProps {
  spaceId: string
  discoveryState: OrchestratedSessionState | null
  discoveryCatalog: SourceCatalogEntry[]
  discoveryError?: string | null
}

export default function SpaceDataSourcesClient({
  spaceId,
  discoveryState,
  discoveryCatalog,
  discoveryError,
}: SpaceDataSourcesClientProps) {
  return (
    <div className="space-y-6">
      <DataSourcesList
        spaceId={spaceId}
        discoveryState={discoveryState}
        discoveryCatalog={discoveryCatalog}
        discoveryError={discoveryError}
      />
    </div>
  )
}
