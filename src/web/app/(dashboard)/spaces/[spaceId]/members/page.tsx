'use client'

import { useSpaceContext } from '@/components/space-context-provider'
import { useParams } from 'next/navigation'
import { useEffect } from 'react'
import { ResearchSpaceDetail } from '@/components/research-spaces/ResearchSpaceDetail'
import { PageHero } from '@/components/ui/composition-patterns'

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
    <div className="space-y-6">
      <PageHero
        title="Team Management"
        description="Invite collaborators, assign roles, and manage membership for this research space."
        variant="research"
      />
      <ResearchSpaceDetail spaceId={spaceId} defaultTab="members" />
    </div>
  )
}
