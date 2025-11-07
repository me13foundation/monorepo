'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { CreateSpaceForm } from '@/components/research-spaces/CreateSpaceForm'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function NewSpacePage() {
  return (
    <ProtectedRoute>
      <div className="max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Create Research Space</CardTitle>
            <CardDescription>
              Create a new research space for your team to collaborate on data sources and curation.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CreateSpaceForm />
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  )
}
