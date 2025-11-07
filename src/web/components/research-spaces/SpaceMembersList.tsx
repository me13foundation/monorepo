"use client"

import { useSpaceMembers, useRemoveMember } from '@/lib/queries/research-spaces'
import { MembershipRole } from '@/types/research-space'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { UserPlus } from 'lucide-react'
import { Loader2 } from 'lucide-react'
import { roleColors, roleLabels } from './role-utils'
import { cn } from '@/lib/utils'

interface SpaceMembersListProps {
  spaceId: string
  onInvite?: () => void
  onUpdateRole?: (membershipId: string, currentRole: MembershipRole) => void
  onRemove?: (membershipId: string) => void
  canManage?: boolean
}

export function SpaceMembersList({
  spaceId,
  onInvite,
  onUpdateRole,
  onRemove,
  canManage = false,
}: SpaceMembersListProps) {
  const { data, isLoading, error } = useSpaceMembers(spaceId)
  const removeMutation = useRemoveMember()

  const handleRemove = async (membershipId: string) => {
    if (onRemove) {
      onRemove(membershipId)
    } else {
      if (confirm('Are you sure you want to remove this member?')) {
        try {
          await removeMutation.mutateAsync({ spaceId, membershipId })
        } catch (error) {
          console.error('Failed to remove member:', error)
        }
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

  if (error) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
        <p className="text-sm text-destructive">
          Failed to load members: {error.message}
        </p>
      </div>
    )
  }

  const memberships = data?.memberships || []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Members</h2>
          <p className="text-muted-foreground text-sm">
            {memberships.length} member{memberships.length !== 1 ? 's' : ''}
          </p>
        </div>
        {canManage && onInvite && (
          <Button onClick={onInvite}>
            <UserPlus className="h-4 w-4 mr-2" />
            Invite Member
          </Button>
        )}
      </div>

      {memberships.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <p className="text-muted-foreground mb-4">No members yet.</p>
          {canManage && onInvite && (
            <Button onClick={onInvite} variant="outline">
              <UserPlus className="h-4 w-4 mr-2" />
              Invite your first member
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
                {canManage && <TableHead className="w-[100px]">Actions</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {memberships.map((membership) => (
                <TableRow key={membership.id}>
                  <TableCell className="font-medium">
                    {membership.user_id}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={cn(
                        roleColors[membership.role],
                        'text-white'
                      )}
                    >
                      {roleLabels[membership.role]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {membership.is_active ? (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        Active
                      </Badge>
                    ) : membership.joined_at ? (
                      <Badge variant="outline">Inactive</Badge>
                    ) : (
                      <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                        Pending
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {membership.joined_at
                      ? new Date(membership.joined_at).toLocaleDateString()
                      : membership.invited_at
                      ? `Invited ${new Date(membership.invited_at).toLocaleDateString()}`
                      : '-'}
                  </TableCell>
                  {canManage && (
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {membership.role !== MembershipRole.OWNER && (
                          <>
                            {onUpdateRole && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onUpdateRole(membership.id, membership.role)}
                              >
                                Change Role
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemove(membership.id)}
                              disabled={removeMutation.isPending}
                            >
                              Remove
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
