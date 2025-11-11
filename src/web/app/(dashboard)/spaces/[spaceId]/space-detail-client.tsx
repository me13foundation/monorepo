'use client'

import { ResearchSpaceDetail } from '@/components/research-spaces/ResearchSpaceDetail'

export default function SpaceDetailClient({ spaceId }: { spaceId: string }) {
  return (
    <div>
      <ResearchSpaceDetail spaceId={spaceId} />
    </div>
  )
}
