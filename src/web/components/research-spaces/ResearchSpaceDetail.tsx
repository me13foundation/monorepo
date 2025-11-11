"use client"

import { useState } from 'react'
import { useResearchSpace, useUpdateResearchSpace, useDeleteResearchSpace, useRemoveMember, useSpaceMembers } from '@/lib/queries/research-spaces'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { SpaceMembersList } from './SpaceMembersList'
import { InviteMemberDialog } from './InviteMemberDialog'
import { UpdateRoleDialog } from './UpdateRoleDialog'
import { Loader2, Settings, Trash2, Users } from 'lucide-react'
import { SpaceStatus, MembershipRole } from '@/types/research-space'
import type { ResearchSpace } from '@/types/research-space'
import { useRouter } from 'next/navigation'
import { roleColors, roleLabels, canManageMembers } from './role-utils'
import { cn } from '@/lib/utils'
import { useSession } from 'next-auth/react'

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
  const {
    data: membersData,
    isLoading: membersLoading,
    error: membersErrorRaw,
  } = useSpaceMembers(spaceId)

  const spaceData = space as ResearchSpace | undefined
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
        router.push('/spaces')
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
            <h1 className="text-3xl font-bold tracking-tight">{spaceData.name}</h1>
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
