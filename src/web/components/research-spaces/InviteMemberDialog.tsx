"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useInviteMember } from '@/lib/queries/research-spaces'
import { inviteMemberSchema, type InviteMemberFormData } from '@/lib/schemas/research-space'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'
import { MembershipRole } from '@/types/research-space'
import { roleLabels } from './role-utils'

interface InviteMemberDialogProps {
  spaceId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function InviteMemberDialog({
  spaceId,
  open,
  onOpenChange,
  onSuccess,
}: InviteMemberDialogProps) {
  const inviteMutation = useInviteMember()

  const form = useForm<InviteMemberFormData>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: {
      user_id: '',
      role: MembershipRole.VIEWER,
    },
  })

  const onSubmit = async (data: InviteMemberFormData) => {
    try {
      await inviteMutation.mutateAsync({
        spaceId,
        data: {
          user_id: data.user_id,
          role: data.role as MembershipRole,
        },
      })
      form.reset()
      onOpenChange(false)
      onSuccess?.()
    } catch (error) {
      // Error handling is done by form validation
      console.error('Failed to invite member:', error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite Member</DialogTitle>
          <DialogDescription>
            Invite a user to join this research space. They will receive a notification.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="user_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>User ID</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="Enter user UUID"
                      className="font-mono"
                    />
                  </FormControl>
                  <FormDescription>
                    The UUID of the user to invite
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <FormControl>
                    <Select
                      {...field}
                      value={field.value}
                      onChange={(e) => field.onChange(e.target.value as MembershipRole)}
                    >
                      {Object.values(MembershipRole).map((role) => (
                        <option key={role} value={role}>
                          {roleLabels[role]}
                        </option>
                      ))}
                    </Select>
                  </FormControl>
                  <FormDescription>
                    Select the role for the new member
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={inviteMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={inviteMutation.isPending}>
                {inviteMutation.isPending && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                Send Invitation
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
