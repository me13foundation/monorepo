'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useSpaceContext } from '@/components/space-context-provider'
import { useParams } from 'next/navigation'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useResearchSpace } from '@/lib/queries/research-spaces'
import { Loader2, Settings } from 'lucide-react'

export default function SpaceSettingsPage() {
  const params = useParams()
  const spaceId = params.spaceId as string
  const { setCurrentSpaceId } = useSpaceContext()
  const { data: space, isLoading } = useResearchSpace(spaceId)

  useEffect(() => {
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }
  }, [spaceId, setCurrentSpaceId])

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div>
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Space Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure settings for {space?.name || 'this research space'}
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              General Settings
            </CardTitle>
            <CardDescription>
              Manage space name, description, and basic configuration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Space Name</label>
                <p className="text-sm text-muted-foreground mt-1">{space?.name}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Slug</label>
                <p className="text-sm text-muted-foreground mt-1 font-mono">{space?.slug}</p>
              </div>
              {space?.description && (
                <div>
                  <label className="text-sm font-medium">Description</label>
                  <p className="text-sm text-muted-foreground mt-1">{space.description}</p>
                </div>
              )}
              <div>
                <label className="text-sm font-medium">Status</label>
                <p className="text-sm text-muted-foreground mt-1 capitalize">{space?.status}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Advanced Settings</CardTitle>
            <CardDescription>
              Additional configuration options (coming soon)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Advanced settings will be available in a future update.
            </p>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  )
}
