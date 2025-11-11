'use client'

import { DataSourcesList } from '@/components/data-sources/DataSourcesList'

export default function SpaceDataSourcesClient({ spaceId }: { spaceId: string }) {
  return (
    <div className="space-y-6">
      <DataSourcesList spaceId={spaceId} />
    </div>
  )
}
