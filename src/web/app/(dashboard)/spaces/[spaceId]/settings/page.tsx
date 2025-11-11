'use client'

import { useSpaceContext } from '@/components/space-context-provider'
import { useParams } from 'next/navigation'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useResearchSpace } from '@/lib/queries/research-spaces'
import { Loader2, Settings } from 'lucide-react'
import type { ResearchSpace } from '@/types/research-space'

export default function SpaceSettingsPage() {
  const params = useParams()
  const spaceId = params.spaceId as string
  const { setCurrentSpaceId } = useSpaceContext()
  const { data: space, isLoading } = useResearchSpace(spaceId)
  const spaceData = space as ResearchSpace | undefined

  useEffect(() => {
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }
  }, [spaceId, setCurrentSpaceId])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Space Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Configure settings for {spaceData?.name || 'this research space'}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="size-5" />
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
              <p className="mt-1 text-sm text-muted-foreground">{spaceData?.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium">Slug</label>
              <p className="mt-1 font-mono text-sm text-muted-foreground">{spaceData?.slug}</p>
            </div>
            {spaceData?.description && (
              <div>
                <label className="text-sm font-medium">Description</label>
                <p className="mt-1 text-sm text-muted-foreground">{spaceData.description}</p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium">Status</label>
              <p className="mt-1 text-sm capitalize text-muted-foreground">{spaceData?.status}</p>
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
  )
}
