"use client"

import { useState } from 'react'
import { useResearchSpace, useUpdateResearchSpace, useDeleteResearchSpace, useRemoveMember } from '@/lib/queries/research-spaces'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { SpaceMembersList } from './SpaceMembersList'
import { InviteMemberDialog } from './InviteMemberDialog'
import { UpdateRoleDialog } from './UpdateRoleDialog'
import { Loader2, Settings, Trash2, Users } from 'lucide-react'
import { SpaceStatus, MembershipRole } from '@/types/research-space'
import { useRouter } from 'next/navigation'
import { roleColors, roleLabels, canManageMembers } from './role-utils'
import { cn } from '@/lib/utils'
import { useSession } from 'next-auth/react'

interface ResearchSpaceDetailProps {
  spaceId: string
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

export function ResearchSpaceDetail({ spaceId }: ResearchSpaceDetailProps) {
  const router = useRouter()
  const { data: session } = useSession()
  const { data: space, isLoading } = useResearchSpace(spaceId)
  const updateMutation = useUpdateResearchSpace()
  const deleteMutation = useDeleteResearchSpace()
  const removeMutation = useRemoveMember()

  const [inviteDialogOpen, setInviteDialogOpen] = useState(false)
  const [updateRoleDialogOpen, setUpdateRoleDialogOpen] = useState(false)
  const [selectedMembershipId, setSelectedMembershipId] = useState<string | null>(null)
  const [selectedCurrentRole, setSelectedCurrentRole] = useState<MembershipRole | null>(null)

  // Get user's role in this space (simplified - would need actual membership query)
  // TODO: Get from membership query - for now assume viewer
  const userRole = MembershipRole.VIEWER as MembershipRole
  const canManage = canManageMembers(userRole)

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
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!space) {
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
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold tracking-tight">{space.name}</h1>
            <Badge
              className={cn(
                statusColors[space.status],
                'text-white'
              )}
            >
              {statusLabels[space.status]}
            </Badge>
          </div>
          <p className="text-muted-foreground">{space.description}</p>
          <p className="text-sm text-muted-foreground mt-1 font-mono">{space.slug}</p>
        </div>
        {canManage && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
            {userRole === MembershipRole.OWNER && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDeleteSpace}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            )}
          </div>
        )}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="members">
            <Users className="h-4 w-4 mr-2" />
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
                <p>{new Date(space.created_at).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                <p>{new Date(space.updated_at).toLocaleDateString()}</p>
              </div>
              {space.tags.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {space.tags.map((tag) => (
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
