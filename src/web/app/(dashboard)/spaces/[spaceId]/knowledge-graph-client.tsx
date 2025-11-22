'use client'

import { DashboardSection } from '@/components/ui/composition-patterns'
import { Waypoints } from 'lucide-react'

interface KnowledgeGraphClientProps {
  spaceId: string
}

export default function KnowledgeGraphClient({ spaceId }: KnowledgeGraphClientProps) {
  return (
    <div className="space-y-6">
      <DashboardSection
        title="Knowledge Graph"
        description="Explore the knowledge graph for this research space."
      >
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Waypoints className="mb-4 size-12 text-muted-foreground" />
          <h3 className="mb-2 text-lg font-semibold">Knowledge Graph</h3>
          <p className="text-muted-foreground">This page is under construction.</p>
        </div>
      </DashboardSection>
    </div>
  )
}
