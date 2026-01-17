"use client"

import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2 } from 'lucide-react'

import { useConfigureDataSourceSchedule, useUpdateDataSource } from '@/lib/queries/data-sources'
import type { DataSource } from '@/types/data-source'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Form, FormDescription, FormLabel } from '@/components/ui/form'
import { Switch } from '@/components/ui/switch'

import { DataSourceScheduleFields } from './DataSourceScheduleFields'

const scheduleSchema = z.object({
  enabled: z.boolean().default(false),
  frequency: z.enum(['manual', 'hourly', 'daily', 'weekly', 'monthly', 'cron']),
  startTime: z.string().optional(),
  timezone: z.string().min(1, 'Timezone is required'),
  cronExpression: z.string().optional(),
})

export type ScheduleFormValues = z.infer<typeof scheduleSchema>

interface DataSourceScheduleDialogProps {
  source: DataSource | null
  spaceId?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

function toLocalDatetimeInput(value?: string | null): string {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const pad = (num: number) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`
}

export function DataSourceScheduleDialog({
  source,
  spaceId,
  open,
  onOpenChange,
}: DataSourceScheduleDialogProps) {
  const configureSchedule = useConfigureDataSourceSchedule(spaceId)
  const updateDataSource = useUpdateDataSource(spaceId)
  const schedule = source?.ingestion_schedule

  const defaultValues = useMemo<ScheduleFormValues>(
    () => ({
      enabled: schedule?.enabled ?? false,
      frequency: schedule?.frequency ?? 'manual',
      startTime: toLocalDatetimeInput(schedule?.start_time),
      timezone: schedule?.timezone ?? 'UTC',
      cronExpression: schedule?.cron_expression ?? '',
    }),
    [schedule],
  )

  const form = useForm<ScheduleFormValues>({
    resolver: zodResolver(scheduleSchema),
    defaultValues,
  })

  useEffect(() => {
    form.reset(defaultValues)
  }, [defaultValues, form, open])

  if (!source) {
    return null
  }

  const onSubmit = async (values: ScheduleFormValues) => {
    const payload = {
      enabled: values.enabled,
      frequency: values.frequency,
      timezone: values.timezone,
      start_time: values.startTime ? new Date(values.startTime).toISOString() : null,
      cron_expression:
        values.frequency === 'cron' ? values.cronExpression?.trim() || null : null,
    }

    await configureSchedule.mutateAsync({
      sourceId: source.id,
      payload,
    })
    onOpenChange(false)
  }

  const enabled = form.watch('enabled')
  const frequency = form.watch('frequency')
  const timezone = form.watch('timezone')
  const cronExpression = form.watch('cronExpression')
  const isCron = frequency === 'cron'
  const hasScheduleBasics =
    typeof timezone === 'string' &&
    timezone.trim().length > 0 &&
    (!isCron || (cronExpression ?? '').trim().length > 0)
  const canEnableSchedule = hasScheduleBasics
  const statusToggleDisabled =
    updateDataSource.isPending || source.status === 'archived' || !hasScheduleBasics
  const statusLabel = source.status === 'active' ? 'Enabled' : 'Disabled'

  const handleStatusToggle = async (enabled: boolean) => {
    try {
      await updateDataSource.mutateAsync({
        sourceId: source.id,
        payload: { status: enabled ? 'active' : 'inactive' },
      })
    } catch (error) {
      // Error toast is handled by the mutation
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Configure ingestion schedule</DialogTitle>
          <DialogDescription>
            Control how often MED13 automatically ingests data from this source.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <DataSourceScheduleFields
              control={form.control}
              enabled={enabled}
              canEnableSchedule={canEnableSchedule}
              isCron={isCron}
            />

            <div className="rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <FormLabel>Source status</FormLabel>
                  <FormDescription>
                    Enable the source after all configuration is complete.
                  </FormDescription>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">{statusLabel}</span>
                  <Switch
                    checked={source.status === 'active'}
                    onCheckedChange={handleStatusToggle}
                    disabled={statusToggleDisabled}
                  />
                </div>
              </div>
              {statusToggleDisabled && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Complete configuration before enabling this source.
                </p>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={configureSchedule.isPending}>
                {configureSchedule.isPending && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                Save schedule
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
