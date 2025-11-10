'use client'

import { ResearchSpaceDetail } from '@/components/research-spaces/ResearchSpaceDetail'
import { useParams } from 'next/navigation'

export default function SpaceDetailPage() {
  const params = useParams()
  const spaceId = params.spaceId as string

  return (
    <div>
      <ResearchSpaceDetail spaceId={spaceId} />
    </div>
  )
}
