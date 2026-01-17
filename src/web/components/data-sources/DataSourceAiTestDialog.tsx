"use client"

import { ExternalLink } from 'lucide-react'

import type { DataSource } from '@/types/data-source'
import type {
  DataSourceAiTestFinding,
  DataSourceAiTestResult,
} from '@/lib/api/data-sources'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

interface DataSourceAiTestDialogProps {
  source: DataSource | null
  result: DataSourceAiTestResult | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return 'Unknown'
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

const FindingCard = ({ finding }: { finding: DataSourceAiTestFinding }) => {
  const primaryLink = finding.links[0]?.url
  const secondaryLinks = finding.links.slice(1)

  return (
    <div className="space-y-2 rounded-md border p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          {primaryLink ? (
            <a
              href={primaryLink}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-semibold text-primary hover:underline"
            >
              {finding.title}
            </a>
          ) : (
            <p className="text-sm font-semibold">{finding.title}</p>
          )}
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            {finding.journal && <span>{finding.journal}</span>}
            {finding.publication_date && <span>{finding.publication_date}</span>}
            {finding.pubmed_id && <span>PMID {finding.pubmed_id}</span>}
          </div>
        </div>
        {primaryLink && (
          <ExternalLink className="mt-1 size-4 text-muted-foreground" />
        )}
      </div>
      {secondaryLinks.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {secondaryLinks.map((link) => (
            <a
              key={`${link.label}-${link.url}`}
              href={link.url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
            >
              {link.label}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

export function DataSourceAiTestDialog({
  source,
  result,
  open,
  onOpenChange,
}: DataSourceAiTestDialogProps) {
  if (!source || !result) {
    return null
  }

  const statusLabel = result.success ? 'Success' : 'Needs attention'
  const modelLabel = result.model || 'Not configured'
  const executedQuery = result.executed_query
  const searchTerms = Array.isArray(result.search_terms) ? result.search_terms : []
  const findings = Array.isArray(result.findings) ? result.findings : []

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[720px]">
        <DialogHeader>
          <DialogTitle>AI test results</DialogTitle>
          <DialogDescription>
            Review the AI-generated PubMed query and sample findings for <b>{source.name}</b>.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <section className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={result.success ? 'secondary' : 'destructive'}>
                {statusLabel}
              </Badge>
              <span className="text-sm text-muted-foreground">{result.message}</span>
            </div>
            <div className="space-y-1 rounded-md border p-3">
              <InfoRow label="Model" value={modelLabel} />
              <InfoRow label="Checked at" value={formatTimestamp(result.checked_at)} />
              <InfoRow label="Fetched records" value={result.fetched_records.toString()} />
              <InfoRow label="Sample size" value={result.sample_size.toString()} />
            </div>
          </section>

          <Separator />

          <section className="space-y-3">
            <h3 className="text-sm font-semibold">Search terms</h3>
            {searchTerms.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {searchTerms.map((term) => (
                  <Badge key={term} variant="outline" className="text-xs">
                    {term}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No search terms were extracted.
              </p>
            )}
            {executedQuery && (
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">Executed query</span>
                <p className="rounded bg-muted p-2 font-mono text-xs">{executedQuery}</p>
              </div>
            )}
          </section>

          <Separator />

          <section className="space-y-3">
            <h3 className="text-sm font-semibold">Sample findings</h3>
            {findings.length > 0 ? (
              <div className="space-y-3">
                {findings.map((finding, index) => (
                  <FindingCard key={`${finding.title}-${index}`} finding={finding} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No findings were returned for this test run.
              </p>
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
