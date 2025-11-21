"use client"

import { DataDiscoveryContent } from '@/components/data-discovery/DataDiscoveryContent'

interface SpaceDiscoveryClientProps {
  spaceId: string
}

export default function SpaceDiscoveryClient({ spaceId }: SpaceDiscoveryClientProps) {
  return <DataDiscoveryContent spaceId={spaceId} />
}
