'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { ResearchSpaceDetail } from '@/components/research-spaces/ResearchSpaceDetail'
import { useParams } from 'next/navigation'

export default function SpaceDetailPage() {
  const params = useParams()
  const spaceId = params.spaceId as string

  return (
    <ProtectedRoute>
      <div>
        <ResearchSpaceDetail spaceId={spaceId} />
      </div>
    </ProtectedRoute>
  )
}
