'use client'

import type { OrchestratedSessionState, SourceCatalogEntry } from '@/types/generated'
import type { DataSourceListResponse } from '@/lib/api/data-sources'
import { DataSourcesList } from '@/components/data-sources/DataSourcesList'

interface SpaceDataSourcesClientProps {
  spaceId: string
  dataSources: DataSourceListResponse | null
  dataSourcesError?: string | null
  discoveryState: OrchestratedSessionState | null
  discoveryCatalog: SourceCatalogEntry[]
  discoveryError?: string | null
}

export default function SpaceDataSourcesClient({
  spaceId,
  dataSources,
  dataSourcesError,
  discoveryState,
  discoveryCatalog,
  discoveryError,
}: SpaceDataSourcesClientProps) {
  return (
    <div className="space-y-6">
      <DataSourcesList
        spaceId={spaceId}
        dataSources={dataSources}
        dataSourcesError={dataSourcesError}
        discoveryState={discoveryState}
        discoveryCatalog={discoveryCatalog}
        discoveryError={discoveryError}
      />
    </div>
  )
}
