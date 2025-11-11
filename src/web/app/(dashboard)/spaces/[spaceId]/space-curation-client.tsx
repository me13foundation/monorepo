'use client'

import { ResearchSpaceDetail } from '@/components/research-spaces/ResearchSpaceDetail'

export default function SpaceCurationClient({ spaceId }: { spaceId: string }) {
  return (
    <div className="space-y-6">
      <ResearchSpaceDetail spaceId={spaceId} defaultTab="overview" />
    </div>
  )
}
