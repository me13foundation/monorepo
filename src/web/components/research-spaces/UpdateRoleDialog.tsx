"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { updateMemberRoleAction } from '@/app/actions/research-spaces'
import { updateMemberRoleSchema, type UpdateMemberRoleFormData } from '@/lib/schemas/research-space'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2 } from 'lucide-react'
import { MembershipRole } from '@/types/research-space'
import { roleLabels } from './role-utils'
import { toast } from 'sonner'
import { useRouter } from 'next/navigation'

interface UpdateRoleDialogProps {
  spaceId: string
  membershipId: string
  currentRole: MembershipRole
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function UpdateRoleDialog({
  spaceId,
  membershipId,
  currentRole,
  open,
  onOpenChange,
  onSuccess,
}: UpdateRoleDialogProps) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<UpdateMemberRoleFormData>({
    resolver: zodResolver(updateMemberRoleSchema),
    defaultValues: {
      role: currentRole,
    },
  })

  const onSubmit = async (data: UpdateMemberRoleFormData) => {
    try {
      setIsSubmitting(true)
      const result = await updateMemberRoleAction(spaceId, membershipId, {
        role: data.role as MembershipRole,
      })
      if (!result.success) {
        toast.error(result.error)
        return
      }
      onOpenChange(false)
      onSuccess?.()
      if (!onSuccess) {
        router.refresh()
      }
      toast.success('Member role updated')
    } catch (error) {
      console.error('Failed to update role:', error)
      toast.error('Failed to update role')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Update Member Role</DialogTitle>
          <DialogDescription>
            Change the role for this member. This will immediately update their permissions.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <FormControl>
                    <Select
                      value={field.value}
                      onValueChange={(value) => field.onChange(value as MembershipRole)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.values(MembershipRole)
                          .filter((role) => role !== MembershipRole.OWNER)
                          .map((role) => (
                            <SelectItem key={role} value={role}>
                              {roleLabels[role]}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormDescription>
                    Select the new role for this member
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
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                Update Role
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
