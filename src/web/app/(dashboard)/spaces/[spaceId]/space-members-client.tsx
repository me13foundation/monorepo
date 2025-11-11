'use client'

import { ResearchSpaceDetail } from '@/components/research-spaces/ResearchSpaceDetail'
import { PageHero } from '@/components/ui/composition-patterns'

export default function SpaceMembersClient({ spaceId }: { spaceId: string }) {
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
