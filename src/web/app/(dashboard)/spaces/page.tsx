'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { ResearchSpacesList } from '@/components/research-spaces/ResearchSpacesList'

export default function SpacesPage() {
  return (
    <ProtectedRoute>
      <div>
        <ResearchSpacesList />
      </div>
    </ProtectedRoute>
  )
}
