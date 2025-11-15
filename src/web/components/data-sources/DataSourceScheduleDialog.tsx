"use client"

import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2 } from 'lucide-react'

import { useConfigureDataSourceSchedule } from '@/lib/queries/data-sources'
import type { DataSource, ScheduleFrequency } from '@/types/data-source'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'

const scheduleSchema = z.object({
  enabled: z.boolean().default(false),
  frequency: z.enum(['manual', 'hourly', 'daily', 'weekly', 'monthly', 'cron']),
  startTime: z.string().optional(),
  timezone: z.string().min(1, 'Timezone is required'),
  cronExpression: z.string().optional(),
})

type ScheduleFormValues = z.infer<typeof scheduleSchema>

const frequencyOptions: { label: string; value: ScheduleFrequency }[] = [
  { label: 'Manual', value: 'manual' },
  { label: 'Hourly', value: 'hourly' },
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Cron expression', value: 'cron' },
]

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

  const isCron = form.watch('frequency') === 'cron'

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
            <FormField
              control={form.control}
              name="enabled"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>Enable scheduling</FormLabel>
                    <FormDescription>
                      When disabled, the source only ingests when manually triggered.
                    </FormDescription>
                  </div>
                  <FormControl>
                    <input
                      type="checkbox"
                      className="size-5 rounded border border-input"
                      checked={field.value}
                      onChange={(event) => field.onChange(event.target.checked)}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="frequency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Frequency</FormLabel>
                  <FormControl>
                    <Select {...field} disabled={!form.watch('enabled')}>
                      {frequencyOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </Select>
                  </FormControl>
                  <FormDescription>
                    Choose how often MED13 should attempt ingestion.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="startTime"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Start time</FormLabel>
                  <FormControl>
                    <Input
                      type="datetime-local"
                      {...field}
                      disabled={!form.watch('enabled')}
                    />
                  </FormControl>
                  <FormDescription>
                    Optional. Defaults to immediately running on the next interval.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="timezone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Timezone</FormLabel>
                  <FormControl>
                    <Input {...field} disabled={!form.watch('enabled')} />
                  </FormControl>
                  <FormDescription>Specify the timezone for scheduler calculations.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {isCron && (
              <FormField
                control={form.control}
                name="cronExpression"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cron expression</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="0 2 * * *" disabled={!form.watch('enabled')} />
                    </FormControl>
                    <FormDescription>
                      Cron support requires a dedicated scheduler backend; use with caution.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

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
