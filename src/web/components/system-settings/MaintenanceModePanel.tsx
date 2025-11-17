"use client"

import { useState } from 'react'
import { toast } from 'sonner'
import { AlertTriangle, Loader2, Power, Shield } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { useMaintenanceMutations, useMaintenanceState } from '@/lib/queries/system-status'

export function MaintenanceModePanel() {
  const maintenanceQuery = useMaintenanceState()
  const mutations = useMaintenanceMutations()
  const [message, setMessage] = useState('')
  const [forceLogout, setForceLogout] = useState(true)

  const isActive = maintenanceQuery.data?.state.is_active ?? false
  const isLoading = maintenanceQuery.isLoading || mutations.enable.isPending || mutations.disable.isPending

  const handleEnable = async () => {
    try {
      await mutations.enable.mutateAsync({
        message: message || null,
        force_logout_users: forceLogout,
      })
      toast.success('Maintenance mode enabled')
    } catch {
      toast.error('Unable to enable maintenance mode')
    }
  }

  const handleDisable = async () => {
    try {
      await mutations.disable.mutateAsync()
      toast.success('Maintenance mode disabled')
      setMessage('')
    } catch {
      toast.error('Unable to disable maintenance mode')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="size-5 text-muted-foreground" />
          Maintenance Mode
        </CardTitle>
        <CardDescription>
          Prevent new writes and log out users before making critical storage changes.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border border-dashed p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-1 size-5 text-amber-500" />
            <div className="space-y-1">
              <p className="text-sm font-semibold">
                Storage changes should only happen during maintenance windows.
              </p>
              <p className="text-sm text-muted-foreground">
                Enabling maintenance mode signs out users (optional) and blocks write operations until disabled.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <Label htmlFor="maintenance-message">Maintenance message</Label>
          <Textarea
            id="maintenance-message"
            placeholder="Explain why maintenance is required and when service will resume."
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            disabled={isActive || isLoading}
          />
        </div>

        <div className="flex items-center justify-between rounded-md border px-4 py-3">
          <div>
            <Label htmlFor="force-logout">Force logout all users</Label>
            <p className="text-xs text-muted-foreground">
              Recommended. Only the initiating admin remains signed in to finish storage updates.
            </p>
          </div>
          <Switch
            id="force-logout"
            checked={forceLogout}
            onCheckedChange={setForceLogout}
            disabled={isActive || isLoading}
          />
        </div>

        <div className="flex flex-col gap-3 md:flex-row">
          <Button
            className="md:flex-1"
            variant={isActive ? 'outline' : 'default'}
            disabled={isLoading || isActive}
            onClick={handleEnable}
          >
            {mutations.enable.isPending ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Enabling...
              </>
            ) : (
              <>
                <Power className="mr-2 size-4" />
                Enable Maintenance Mode
              </>
            )}
          </Button>
          <Button
            className="md:flex-1"
            variant="secondary"
            disabled={isLoading || !isActive}
            onClick={handleDisable}
          >
            {mutations.disable.isPending ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Disabling...
              </>
            ) : (
              'Disable Maintenance Mode'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
