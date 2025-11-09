'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useSpaceContext } from '@/components/space-context-provider'
import { useParams } from 'next/navigation'
import { useEffect } from 'react'
import { ResearchSpaceDetail } from '@/components/research-spaces/ResearchSpaceDetail'

export default function SpaceMembersPage() {
  const params = useParams()
  const spaceId = params.spaceId as string
  const { setCurrentSpaceId } = useSpaceContext()

  useEffect(() => {
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }
  }, [spaceId, setCurrentSpaceId])

  return (
    <ProtectedRoute>
      <div>
        <ResearchSpaceDetail spaceId={spaceId} defaultTab="members" />
      </div>
    </ProtectedRoute>
  )
}
