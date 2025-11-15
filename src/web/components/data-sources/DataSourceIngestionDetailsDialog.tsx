"use client"

import { Loader2 } from 'lucide-react'

import type { DataSource, IngestionJobHistoryItem } from '@/types/data-source'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useIngestionJobHistory } from '@/lib/queries/data-sources'

export type ManualIngestionSummary = {
  source_id: string
  fetched_records: number
  parsed_publications: number
  created_publications: number
  updated_publications: number
  completedAt: string
}

interface DataSourceIngestionDetailsDialogProps {
  source: DataSource | null
  summary?: ManualIngestionSummary
  open: boolean
  onOpenChange: (open: boolean) => void
}

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return 'Never'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Unknown'
  }
  return date.toLocaleString()
}

const InfoRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center justify-between text-sm">
    <span className="text-muted-foreground">{label}</span>
    <span className="text-right font-medium">{value}</span>
  </div>
)

export function DataSourceIngestionDetailsDialog({
  source,
  summary,
  open,
  onOpenChange,
}: DataSourceIngestionDetailsDialogProps) {
  const historyQuery = useIngestionJobHistory(source?.id ?? null, open && Boolean(source))
  const historyItems: IngestionJobHistoryItem[] = historyQuery.data?.items || []

  if (!source) {
    return null
  }

  const schedule = source.ingestion_schedule

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Ingestion details</DialogTitle>
          <DialogDescription>
            Review the most recent ingestion activity and schedule for <b>{source.name}</b>.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Source metadata</h3>
            <InfoRow label="Type" value={source.source_type} />
            <InfoRow label="Status" value={source.status} />
            <InfoRow label="Last ingested" value={formatTimestamp(source.last_ingested_at)} />
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Schedule</h3>
            <InfoRow label="Enabled" value={schedule?.enabled ? 'Yes' : 'No'} />
            <InfoRow
              label="Cadence"
              value={schedule?.frequency ?? 'manual'}
            />
            <InfoRow label="Timezone" value={schedule?.timezone ?? 'UTC'} />
            <InfoRow label="Next run" value={formatTimestamp(schedule?.next_run_at)} />
            <InfoRow label="Last run" value={formatTimestamp(schedule?.last_run_at)} />
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Latest manual run</h3>
            {summary ? (
              <div className="space-y-1 rounded-md border p-3">
                <InfoRow label="Completed" value={formatTimestamp(summary.completedAt)} />
                <InfoRow label="Fetched records" value={summary.fetched_records.toString()} />
                <InfoRow label="Parsed publications" value={summary.parsed_publications.toString()} />
                <InfoRow label="New publications" value={summary.created_publications.toString()} />
                <InfoRow label="Updated publications" value={summary.updated_publications.toString()} />
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No manual ingestion has been recorded during this session.
              </p>
            )}
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Recent ingestion jobs</h3>
            {historyQuery.isLoading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="size-5 animate-spin text-muted-foreground" />
              </div>
            ) : historyItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">No ingestion jobs recorded yet.</p>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[120px]">Status</TableHead>
                      <TableHead>Trigger</TableHead>
                      <TableHead>Started</TableHead>
                      <TableHead>Completed</TableHead>
                      <TableHead className="text-right">Processed</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {historyItems.map((job) => (
                      <TableRow key={job.id}>
                        <TableCell className="font-medium capitalize">{job.status}</TableCell>
                        <TableCell className="capitalize">{job.trigger}</TableCell>
                        <TableCell>{formatTimestamp(job.started_at)}</TableCell>
                        <TableCell>{formatTimestamp(job.completed_at)}</TableCell>
                        <TableCell className="text-right">
                          {job.records_processed} (+{job.records_failed}/{job.records_skipped})
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </section>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
