"use client"

import { useState } from 'react'
import { useResearchSpace, useUpdateResearchSpace, useDeleteResearchSpace, useRemoveMember, useSpaceMembers, useSpaceCurationStats, useSpaceCurationQueue } from '@/lib/queries/research-spaces'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { SpaceMembersList } from './SpaceMembersList'
import { InviteMemberDialog } from './InviteMemberDialog'
import { UpdateRoleDialog } from './UpdateRoleDialog'
import { Loader2, Settings, Trash2, Users, Database, BarChart3, FileText } from 'lucide-react'
import { SpaceStatus, MembershipRole } from '@/types/research-space'
import type { ResearchSpace } from '@/types/research-space'
import { useRouter } from 'next/navigation'
import { canManageMembers } from './role-utils'
import { cn } from '@/lib/utils'
import { useSession } from 'next-auth/react'
import { useSpaceDataSources } from '@/lib/queries/data-sources'
import type { DataSourceListResponse } from '@/lib/api/data-sources'
import type { CurationQueueResponse } from '@/lib/api/research-spaces'
import { DashboardSection, SectionGrid, StatCard } from '@/components/ui/composition-patterns'

interface ResearchSpaceDetailProps {
  spaceId: string
  defaultTab?: string
}

const statusColors: Record<SpaceStatus, string> = {
  [SpaceStatus.ACTIVE]: 'bg-green-500',
  [SpaceStatus.INACTIVE]: 'bg-gray-500',
  [SpaceStatus.ARCHIVED]: 'bg-yellow-500',
  [SpaceStatus.SUSPENDED]: 'bg-red-500',
}

const statusLabels: Record<SpaceStatus, string> = {
  [SpaceStatus.ACTIVE]: 'Active',
  [SpaceStatus.INACTIVE]: 'Inactive',
  [SpaceStatus.ARCHIVED]: 'Archived',
  [SpaceStatus.SUSPENDED]: 'Suspended',
}

export function ResearchSpaceDetail({ spaceId, defaultTab = 'overview' }: ResearchSpaceDetailProps) {
  const router = useRouter()
  const { data: session } = useSession()
  const { data: space, isLoading } = useResearchSpace(spaceId)
  const updateMutation = useUpdateResearchSpace()
  const deleteMutation = useDeleteResearchSpace()
  const removeMutation = useRemoveMember()
  const { data: curationStats, isLoading: curationLoading } = useSpaceCurationStats(spaceId)
  const { data: curationQueue, isLoading: curationQueueLoading } = useSpaceCurationQueue(spaceId, {
    limit: 5,
  })
  const { data: dataSources, isLoading: dataSourcesLoading } = useSpaceDataSources(spaceId, {
    limit: 5,
    page: 1,
  })
  const {
    data: membersData,
    isLoading: membersLoading,
    error: membersErrorRaw,
  } = useSpaceMembers(spaceId)

  const spaceData = space as ResearchSpace | undefined
  const dataSourcesResponse = dataSources as DataSourceListResponse | undefined
  const totalDataSources = dataSourcesResponse?.total ?? 0
  const recentSources = dataSourcesResponse?.items ?? []
  const curationQueueData = curationQueue as CurationQueueResponse | undefined
  const showOnboarding = !dataSourcesLoading && totalDataSources === 0
  const hasDataSources = totalDataSources > 0
  const dataSourceStatusCounts =
    recentSources.reduce<Record<string, number>>((acc, source) => {
      const status = source.status || 'unknown'
      acc[status] = (acc[status] ?? 0) + 1
      return acc
    }, {}) ?? {}

  const [inviteDialogOpen, setInviteDialogOpen] = useState(false)
  const [updateRoleDialogOpen, setUpdateRoleDialogOpen] = useState(false)
  const [selectedMembershipId, setSelectedMembershipId] = useState<string | null>(null)
  const [selectedCurrentRole, setSelectedCurrentRole] = useState<MembershipRole | null>(null)

  const membershipList = membersData?.memberships ?? []
  const matchedMembership = membershipList.find((membership) => membership.user_id === session?.user?.id)
  const sessionRoleKey = session?.user?.role?.toUpperCase() as keyof typeof MembershipRole | undefined
  const fallbackRole = sessionRoleKey ? MembershipRole[sessionRoleKey] : undefined
  const userRole = matchedMembership?.role ?? fallbackRole ?? MembershipRole.VIEWER
  const canManage = canManageMembers(userRole)
  const membersError = membersErrorRaw instanceof Error ? membersErrorRaw : null

  const handleUpdateRole = (membershipId: string, currentRole: MembershipRole) => {
    setSelectedMembershipId(membershipId)
    setSelectedCurrentRole(currentRole)
    setUpdateRoleDialogOpen(true)
  }

  const handleRemoveMember = async (membershipId: string) => {
    if (confirm('Are you sure you want to remove this member?')) {
      try {
        await removeMutation.mutateAsync({ spaceId, membershipId })
      } catch (error) {
        console.error('Failed to remove member:', error)
      }
    }
  }

  const handleDeleteSpace = async () => {
    if (confirm('Are you sure you want to delete this space? This action cannot be undone.')) {
      try {
        await deleteMutation.mutateAsync(spaceId)
        router.push('/dashboard')
      } catch (error) {
        console.error('Failed to delete space:', error)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!spaceData) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
        <p className="text-sm text-destructive">Research space not found</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <h1 className="font-heading text-3xl font-bold tracking-tight">{spaceData.name}</h1>
            <Badge
              className={cn(
                statusColors[spaceData.status],
                'text-white'
              )}
            >
              {statusLabels[spaceData.status]}
            </Badge>
          </div>
          <p className="text-muted-foreground">{spaceData.description}</p>
          <p className="mt-1 font-mono text-sm text-muted-foreground">{spaceData.slug}</p>
        </div>
        {canManage && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Settings className="mr-2 size-4" />
              Settings
            </Button>
            {userRole === MembershipRole.OWNER && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDeleteSpace}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="mr-2 size-4" />
                Delete
              </Button>
            )}
          </div>
        )}
      </div>

      <Tabs defaultValue={defaultTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="members">
            <Users className="mr-2 size-4" />
            Members
          </TabsTrigger>
        <TabsTrigger value="settings">Settings</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-4">
        {showOnboarding && (
          <Card className="border-dashed bg-card/80">
            <CardHeader>
              <CardTitle>Welcome to your new research space</CardTitle>
              <CardDescription>
                Set up your data sources and curation workflow. This view will turn into a space
                dashboard once data starts flowing.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border p-3">
                  <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    <Database className="size-4 text-muted-foreground" />
                    Add data sources
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Connect APIs or uploads to start ingesting MED13 data.
                  </p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    <FileText className="size-4 text-muted-foreground" />
                    Curate and review
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Validate incoming records and track review status.
                  </p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    <BarChart3 className="size-4 text-muted-foreground" />
                    Explore the graph
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Visualize genes, variants, and evidence once data is ready.
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => router.push(`/spaces/${spaceId}/data-sources`)}>
                  Configure data sources
                </Button>
                <Button variant="outline" onClick={() => router.push(`/spaces/${spaceId}/curation`)}>
                  Start curation
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => router.push(`/spaces/${spaceId}/knowledge-graph`)}
                >
                  Explore graph
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {hasDataSources && (
          <>
            <SectionGrid>
              <StatCard
                title="Data Sources"
                value={totalDataSources}
                description={`Active ${dataSourceStatusCounts['active'] ?? 0} • Pending ${dataSourceStatusCounts['pending_review'] ?? 0}`}
                icon={<Database className="size-4 text-muted-foreground" />}
                isLoading={dataSourcesLoading}
              />
              <StatCard
                title="Pending Curation"
                value={curationStats?.pending ?? 0}
                description={`Approved ${curationStats?.approved ?? 0} • Rejected ${curationStats?.rejected ?? 0}`}
                icon={<FileText className="size-4 text-muted-foreground" />}
                isLoading={curationLoading}
              />
              <StatCard
                title="Total Records"
                value={(curationStats?.total ?? 0) + totalDataSources}
                description="Curation items + data sources"
                icon={<BarChart3 className="size-4 text-muted-foreground" />}
                isLoading={curationLoading || dataSourcesLoading}
              />
            </SectionGrid>

            <DashboardSection
              title="Recent Data Sources"
              description="Latest sources configured in this space"
            >
              {dataSourcesLoading ? (
                <div className="space-y-3 text-sm text-muted-foreground">
                  <div className="h-4 w-40 rounded bg-muted" />
                  <div className="h-4 w-48 rounded bg-muted" />
                  <div className="h-4 w-36 rounded bg-muted" />
                </div>
              ) : (
                <div className="space-y-3">
                  {recentSources.map((source) => (
                    <div
                      key={source.id}
                      className="flex flex-col gap-1 rounded-lg border p-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="text-sm font-semibold text-foreground">{source.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {source.source_type} • Status: {source.status}
                        </p>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Last updated {source.updated_at ? new Date(source.updated_at).toLocaleString() : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </DashboardSection>

            <DashboardSection
              title="Curation Activity"
              description="Review workload within this research space"
            >
              {curationLoading ? (
                <div className="space-y-3 text-sm text-muted-foreground">
                  <div className="h-4 w-36 rounded bg-muted" />
                  <div className="h-4 w-48 rounded bg-muted" />
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="rounded-lg border p-3">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Pending review</p>
                    <p className="text-2xl font-semibold text-foreground">{curationStats?.pending ?? 0}</p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Approved</p>
                    <p className="text-2xl font-semibold text-foreground">{curationStats?.approved ?? 0}</p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Rejected</p>
                    <p className="text-2xl font-semibold text-foreground">{curationStats?.rejected ?? 0}</p>
                  </div>
                </div>
              )}
            </DashboardSection>

            <DashboardSection
              title="Activity Feed"
              description="Latest curation queue activity for this space"
            >
              {curationQueueLoading ? (
                <div className="space-y-3 text-sm text-muted-foreground">
                  <div className="h-4 w-48 rounded bg-muted" />
                  <div className="h-4 w-36 rounded bg-muted" />
                  <div className="h-4 w-40 rounded bg-muted" />
                </div>
              ) : (curationQueueData?.items.length ?? 0) === 0 ? (
                <p className="text-sm text-muted-foreground">No recent activity yet.</p>
              ) : (
                <div className="space-y-3">
                  {curationQueueData?.items.map((item) => (
                    <div
                      key={item.id}
                      className="flex flex-col gap-1 rounded-lg border p-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="text-sm font-semibold text-foreground">
                          {item.entity_type} #{item.entity_id}
                        </p>
                        <p className="text-xs text-muted-foreground">Status: {item.status}</p>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Updated {item.last_updated ? new Date(item.last_updated).toLocaleString() : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </DashboardSection>
          </>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Space Information</CardTitle>
          </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Created</p>
                <p>{new Date(spaceData.created_at).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                <p>{new Date(spaceData.updated_at).toLocaleDateString()}</p>
              </div>
              {spaceData.tags.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium text-muted-foreground">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {spaceData.tags.map((tag) => (
                      <Badge key={tag} variant="outline">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="members" className="space-y-4">
        <SpaceMembersList
          spaceId={spaceId}
          memberships={membershipList}
          isLoading={membersLoading}
          error={membersError}
          onInvite={() => setInviteDialogOpen(true)}
          onUpdateRole={handleUpdateRole}
          onRemove={handleRemoveMember}
          canManage={canManage}
        />
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Space Settings</CardTitle>
              <CardDescription>Manage space configuration and preferences</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Settings coming soon...</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <InviteMemberDialog
        spaceId={spaceId}
        open={inviteDialogOpen}
        onOpenChange={setInviteDialogOpen}
      />

      {selectedMembershipId && selectedCurrentRole && (
        <UpdateRoleDialog
          spaceId={spaceId}
          membershipId={selectedMembershipId}
          currentRole={selectedCurrentRole}
          open={updateRoleDialogOpen}
          onOpenChange={setUpdateRoleDialogOpen}
        />
      )}
    </div>
  )
}
