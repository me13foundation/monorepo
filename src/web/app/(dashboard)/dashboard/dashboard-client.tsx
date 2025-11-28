'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useSession } from 'next-auth/react'
import { Plus, FolderPlus, Settings } from 'lucide-react'
import { useSpaceContext } from '@/components/space-context-provider'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { useRouter } from 'next/navigation'
import type { ResearchSpaceListResponse } from '@/types/research-space'
import { DashboardSection, PageHero } from '@/components/ui/composition-patterns'
import { getThemeVariant } from '@/lib/theme/variants'
import { ResearchSpaceCard } from '@/components/research-spaces/ResearchSpaceCard'
import { UserRole } from '@/types/auth'

export default function DashboardClient() {
  return <DashboardContent />
}

function DashboardContent() {
  const { data: session } = useSession()
  const { currentSpaceId } = useSpaceContext()
  const { data, isLoading: spacesLoading } = useResearchSpaces()
  const router = useRouter()
  const theme = getThemeVariant('research')

  const spacesResponse = data as ResearchSpaceListResponse | undefined
  const spaces = spacesResponse?.spaces ?? []
  const hasSpaces = spaces.length > 0
  const canCreateSpace = session?.user?.role === UserRole.ADMIN
  const canAccessSystemSettings = session?.user?.role === UserRole.ADMIN
  const currentSpaceName = currentSpaceId
    ? spaces.find((space) => space.id === currentSpaceId)?.name || currentSpaceId
    : null

  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHero
        eyebrow="Admin"
        title="Admin Console"
        description="Select a research space to manage project-level data. Use system settings for platform-wide controls."
        variant="research"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {canAccessSystemSettings && (
              <Button
                variant="outline"
                onClick={() => router.push('/system-settings')}
                className="flex items-center gap-2"
              >
                <Settings className="size-4" />
                <span>System Settings</span>
              </Button>
            )}
            {canCreateSpace && (
              <Button onClick={() => router.push('/spaces/new')} className="flex items-center gap-2">
                <Plus className="size-5" />
                <span>Create Space</span>
              </Button>
            )}
          </div>
        }
      />

      {currentSpaceName && (
        <Card className="border-dashed">
          <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Current space</p>
              <p className="font-medium text-foreground">{currentSpaceName}</p>
            </div>
            <Button variant="secondary" onClick={() => router.push(`/spaces/${currentSpaceId}`)}>
              Open space
            </Button>
          </CardContent>
        </Card>
      )}

      <DashboardSection
        title="Research Spaces"
        description="Spaces you can access. Open a space to see project-specific stats, data sources, and activity."
        className={theme.card}
      >
        {spacesLoading ? (
          <div className="space-y-3 text-sm text-muted-foreground">
            <div className="h-4 w-32 rounded bg-muted" />
            <div className="h-4 w-48 rounded bg-muted" />
            <div className="h-4 w-24 rounded bg-muted" />
          </div>
        ) : hasSpaces ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {spaces.map((space) => (
              <ResearchSpaceCard
                key={space.id}
                space={space}
                onSettings={() => router.push(`/spaces/${space.id}/settings`)}
              />
            ))}
          </div>
        ) : (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center px-4 py-10 text-center sm:px-8">
              <div className="mb-4 rounded-full bg-muted p-3 sm:p-4">
                <FolderPlus className="size-6 text-muted-foreground sm:size-8" />
              </div>
              <p className="mb-2 text-lg font-semibold">No research spaces yet</p>
              <p className="mb-6 max-w-md text-sm text-muted-foreground">
                Create a space to organize MED13 research work. Data sources, records, and activity
                will live inside each space.
              </p>
              {canCreateSpace && (
                <Button onClick={() => router.push('/spaces/new')} className="flex items-center gap-2">
                  <Plus className="size-5" />
                  Create your first space
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </DashboardSection>
    </div>
  )
}
