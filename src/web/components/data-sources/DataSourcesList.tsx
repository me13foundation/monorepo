"use client"

import { useState } from 'react'
import { isAxiosError } from 'axios'
import { toast } from 'sonner'
import {
  useSpaceDataSources,
  useTriggerDataSourceIngestion,
  useTestDataSourceAiConfiguration,
  useUpdateDataSource,
  useDeleteDataSource,
} from '@/lib/queries/data-sources'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Database,
  Loader2,
  Clock,
  RefreshCw,
  Info,
  Search,
  MoreVertical,
  Trash2,
  TestTube,
} from 'lucide-react'
import { DataSourceScheduleDialog } from './DataSourceScheduleDialog'
import { DataSourceAiConfigDialog } from './DataSourceAiConfigDialog'
import { DataSourceIngestionDetailsDialog, type ManualIngestionSummary } from './DataSourceIngestionDetailsDialog'
import { DiscoverSourcesDialog } from './DiscoverSourcesDialog'
import type { DataSource } from '@/types/data-source'
import { componentRegistry } from '@/lib/components/registry'

interface DataSourcesListProps {
  spaceId: string
}

export function DataSourcesList({ spaceId }: DataSourcesListProps) {
  const { data, isLoading, error, refetch } = useSpaceDataSources(spaceId)
  const [lastSummaries, setLastSummaries] = useState<Record<string, ManualIngestionSummary>>({})
  const [detailSourceId, setDetailSourceId] = useState<string | null>(null)
  const triggerIngestion = useTriggerDataSourceIngestion(spaceId)
  const testAiConfiguration = useTestDataSourceAiConfiguration()
  const updateDataSource = useUpdateDataSource(spaceId)
  const deleteDataSource = useDeleteDataSource(spaceId)
  const [isDiscoverDialogOpen, setIsDiscoverDialogOpen] = useState(false)
  const [scheduleDialogSource, setScheduleDialogSource] = useState<DataSource | null>(null)
  const [aiConfigDialogSource, setAiConfigDialogSource] = useState<DataSource | null>(null)
  const [runningSourceId, setRunningSourceId] = useState<string | null>(null)
  const [testingSourceId, setTestingSourceId] = useState<string | null>(null)
  const [deleteSourceId, setDeleteSourceId] = useState<string | null>(null)
  const StatusBadge = componentRegistry.get<{ status: string }>('dataSource.statusBadge')
  const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null && !Array.isArray(value)
  const getErrorMessage = (error: unknown): string => {
    if (isAxiosError(error)) {
      const data = error.response?.data
      if (isRecord(data) && typeof data.detail === 'string') {
        return data.detail
      }
    }
    if (error instanceof Error) {
      return error.message
    }
    return 'Unable to test AI configuration'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-destructive">
            Failed to load data sources: {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </CardContent>
      </Card>
    )
  }

  const dataSources = data?.items || []

  const detailSource =
    dataSources.find((source) => source.id === detailSourceId) ?? null

  const handleRunNow = async (source: DataSource) => {
    try {
      setRunningSourceId(source.id)
      const summary = await triggerIngestion.mutateAsync(source.id)
      const completedAt = new Date().toISOString()
      const enrichedSummary: ManualIngestionSummary = { ...summary, completedAt }
      setLastSummaries((prev) => ({ ...prev, [source.id]: enrichedSummary }))
      toast.success(`Ingestion completed for ${source.name}`, {
        description: `${summary.created_publications} new, ${summary.updated_publications} updated publications.`,
      })
    } finally {
      setRunningSourceId(null)
    }
  }

  const handleTestAiConfiguration = async (source: DataSource) => {
    try {
      setTestingSourceId(source.id)
      const result = await testAiConfiguration.mutateAsync(source.id)
      const description = result.executed_query
        ? `Query: ${result.executed_query}`
        : undefined
      if (result.success) {
        toast.success(result.message, { description })
      } else {
        toast.error(result.message, { description })
      }
    } catch (error) {
      toast.error(getErrorMessage(error))
    } finally {
      setTestingSourceId(null)
    }
  }

  const handleRetire = async (source: DataSource) => {
    try {
      await updateDataSource.mutateAsync({
        sourceId: source.id,
        payload: {
          status: 'archived',
        },
      })
    } catch (error) {
      // Error toast is handled by the mutation
    }
  }

  const handleDelete = async () => {
    if (!deleteSourceId) return
    try {
      await deleteDataSource.mutateAsync(deleteSourceId)
      setDeleteSourceId(null)
    } catch (error) {
      // Error toast is handled by the mutation
    }
  }

  const formatScheduleLabel = (source: DataSource): string => {
    const schedule = source.ingestion_schedule
    if (!schedule || !schedule.enabled) {
      return 'Manual only'
    }
    if (schedule.frequency === 'cron') {
      return schedule.cron_expression ? `Cron (${schedule.cron_expression})` : 'Cron'
    }
    return schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)
  }

  const formatTimestamp = (value?: string | null) => {
    if (!value) {
      return 'Never'
    }
    const date = new Date(value)
    return Number.isNaN(date.getTime()) ? 'Unknown' : date.toLocaleString()
  }

  const formatRelativeTime = (value?: string | null) => {
    if (!value) {
      return 'Not scheduled'
    }
    const target = new Date(value)
    if (Number.isNaN(target.getTime())) {
      return 'Unknown'
    }
    const diffMs = target.getTime() - Date.now()
    const absMs = Math.abs(diffMs)
    const units: [number, Intl.RelativeTimeFormatUnit][] = [
      [1000, 'second'],
      [60 * 1000, 'minute'],
      [60 * 60 * 1000, 'hour'],
      [24 * 60 * 60 * 1000, 'day'],
    ]
    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
    for (let i = units.length - 1; i >= 0; i -= 1) {
      const [unitMs, unit] = units[i]
      if (absMs >= unitMs) {
        const valueInUnit = Math.round(diffMs / unitMs)
        return rtf.format(valueInUnit, unit)
      }
    }
    return 'moments away'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            {data?.total || 0} data source{data?.total !== 1 ? 's' : ''} in this space
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsDiscoverDialogOpen(true)}>
            <Search className="mr-2 size-4" />
            Add from Library
          </Button>
        </div>
      </div>

      {dataSources.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="py-12 text-center">
              <Database className="mx-auto mb-4 size-12 text-muted-foreground" />
              <h3 className="mb-2 text-lg font-semibold">No data sources added to this space yet</h3>
              <p className="mb-4 text-muted-foreground">
                Use the library to add PubMed or create a custom source from the same menu.
              </p>
              <div className="flex justify-center gap-3">
                <Button onClick={() => setIsDiscoverDialogOpen(true)}>
                  <Search className="mr-2 size-4" />
                  Add from Library
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {dataSources.map((source: DataSource) => (
            <Card key={source.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{source.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {source.description || 'No description'}
                    </CardDescription>
                  </div>
                  {StatusBadge ? (
                    <StatusBadge status={source.status} />
                  ) : (
                    <Badge variant="outline">{source.status}</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Type:</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium capitalize">{source.source_type}</span>
                      {(() => {
                        const config = isRecord(source.config) ? source.config : {}
                        const metadata = isRecord(config.metadata) ? config.metadata : {}
                        const agentConfig = isRecord(metadata.agent_config)
                          ? metadata.agent_config
                          : {}
                        if (agentConfig.is_ai_managed === true) {
                          return (
                            <Badge
                              variant="secondary"
                              className="bg-blue-100 px-1 py-0 text-[10px] uppercase text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                            >
                              AI Managed
                            </Badge>
                          )
                        }
                        return null
                      })()}
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Last ingested:</span>
                    <span className="font-medium">{formatTimestamp(source.last_ingested_at)}</span>
                  </div>
                  {source.tags && source.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {source.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                  <div className="mt-3 space-y-2 rounded-md border p-3">
                    {source.source_type === 'pubmed' && (
                      <>
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Clock className="size-4" />
                            <span>Schedule</span>
                          </div>
                          <span className="font-medium">{formatScheduleLabel(source)}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>Timezone</span>
                          <span>{source.ingestion_schedule?.timezone || 'UTC'}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>Next run</span>
                          <span>{formatRelativeTime(source.ingestion_schedule?.next_run_at)}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>Last run</span>
                          <span>{formatTimestamp(source.ingestion_schedule?.last_run_at)}</span>
                        </div>
                      </>
                    )}
                    <div className="flex flex-wrap gap-2 pt-2">
                      {source.source_type === 'pubmed' && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setScheduleDialogSource(source)}
                        >
                          Configure schedule
                        </Button>
                      )}
                      {source.source_type === 'pubmed' && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setAiConfigDialogSource(source)}
                        >
                          Configure AI
                        </Button>
                      )}
                      {source.source_type === 'pubmed' && (
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => handleTestAiConfiguration(source)}
                          disabled={testAiConfiguration.isPending && testingSourceId === source.id}
                        >
                          {testAiConfiguration.isPending && testingSourceId === source.id ? (
                            <Loader2 className="mr-2 size-4 animate-spin" />
                          ) : (
                            <TestTube className="mr-2 size-4" />
                          )}
                          Test AI
                        </Button>
                      )}
                      {source.source_type === 'pubmed' && (
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => handleRunNow(source)}
                          disabled={triggerIngestion.isPending && runningSourceId === source.id}
                        >
                          {triggerIngestion.isPending && runningSourceId === source.id ? (
                            <Loader2 className="mr-2 size-4 animate-spin" />
                          ) : (
                            <RefreshCw className="mr-2 size-4" />
                          )}
                          Run now
                        </Button>
                      )}
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        className="text-muted-foreground"
                        onClick={() => setDetailSourceId(source.id)}
                      >
                        <Info className="mr-2 size-4" />
                        View details
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            className="text-muted-foreground"
                          >
                            <MoreVertical className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            disabled={source.status === 'archived' || updateDataSource.isPending}
                            onClick={() => handleRetire(source)}
                          >
                            Retire source
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive focus:text-destructive"
                            onClick={() => setDeleteSourceId(source.id)}
                          >
                            <Trash2 className="mr-2 size-4" />
                            Remove source
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <DataSourceScheduleDialog
        spaceId={spaceId}
        source={scheduleDialogSource}
        open={Boolean(scheduleDialogSource)}
        onOpenChange={(open) => {
          if (!open) {
            setScheduleDialogSource(null)
          }
        }}
      />
      <DataSourceAiConfigDialog
        spaceId={spaceId}
        source={aiConfigDialogSource}
        open={Boolean(aiConfigDialogSource)}
        onOpenChange={(open) => {
          if (!open) {
            setAiConfigDialogSource(null)
          }
        }}
      />
      <DataSourceIngestionDetailsDialog
        source={detailSource}
        summary={detailSource ? lastSummaries[detailSource.id] : undefined}
        open={Boolean(detailSourceId)}
        onOpenChange={(open) => {
          if (!open) {
            setDetailSourceId(null)
          }
        }}
      />
      <DiscoverSourcesDialog
        spaceId={spaceId}
        open={isDiscoverDialogOpen}
        onOpenChange={setIsDiscoverDialogOpen}
        onSourceAdded={async () => {
          // Explicitly refetch the data sources list when a source is added
          await refetch()
        }}
      />
      <Dialog open={Boolean(deleteSourceId)} onOpenChange={(open) => !open && setDeleteSourceId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove data source</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove this data source? This action cannot be undone and will
              permanently delete the source from this research space.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDeleteSourceId(null)}
              disabled={deleteDataSource.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteDataSource.isPending}
            >
              {deleteDataSource.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
