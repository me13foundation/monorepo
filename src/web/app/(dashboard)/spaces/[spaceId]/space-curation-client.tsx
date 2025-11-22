'use client'

import { DashboardSection } from '@/components/ui/composition-patterns'
import { FileText } from 'lucide-react'

interface SpaceCurationClientProps {
  spaceId: string
}

export default function SpaceCurationClient({ spaceId }: SpaceCurationClientProps) {
  return (
    <div className="space-y-6">
      <DashboardSection
        title="Data Curation"
        description="Curate and review data for this research space."
      >
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <FileText className="mb-4 size-12 text-muted-foreground" />
          <h3 className="mb-2 text-lg font-semibold">Data Curation</h3>
          <p className="text-muted-foreground">This page is under construction.</p>
        </div>
      </DashboardSection>
    </div>
  )
}
