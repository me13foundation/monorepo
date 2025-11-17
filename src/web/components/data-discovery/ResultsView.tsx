"use client"

import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowLeft,
  ExternalLink,
  Terminal,
  Loader2,
  FolderOpen,
  Database,
  BrainCircuit,
  ClipboardList,
  BookOpenText,
  TestTube2,
  Users,
  Network,
  Settings2,
  KeyRound,
} from 'lucide-react'
import type {
  QueryParameters,
  QueryTestResult,
  SourceCatalogEntry,
} from '@/lib/types/data-discovery'
import {
  DEFAULT_ADVANCED_SETTINGS,
  type SourceAdvancedSettings,
} from '@/components/data-discovery/advanced-settings'
import type { ScheduleFrequency } from '@/types/data-source'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { SpaceSelectorModal } from '@/components/research-spaces/SpaceSelectorModal'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Genomic Variant Databases': Database,
  'Gene Expression & Functional Genomics': BrainCircuit,
  'Model Organism Databases': TestTube2,
  'Protein / Pathway Databases': Network,
  'Electronic Health Records (EHRs)': ClipboardList,
  'Rare Disease Registries': Users,
  'Clinical Trial Databases': TestTube2,
  'Phenotype Ontologies & Databases': ClipboardList,
  'Scientific Literature': BookOpenText,
  'Knowledge Graphs / Integrated Platforms': Network,
  'AI Predictive Models': BrainCircuit,
}

const SOURCE_TYPE_LABELS: Record<SourceCatalogEntry['source_type'], string> = {
  api: 'API',
  database: 'Database',
  file_upload: 'File Upload',
  web_scraping: 'Web Scraping',
  pubmed: 'PubMed',
}

const PARAMETER_LABELS = {
  gene: 'Gene-only',
  term: 'Phenotype-only',
  geneAndTerm: 'Gene & Phenotype',
  none: 'No Parameters',
  api: 'API-Driven',
} as const

const PARAMETER_DESCRIPTIONS = {
  gene: 'Provide a valid HGNC symbol before running queries.',
  term: 'Provide a phenotype, ontology ID, or search keyword.',
  geneAndTerm: 'Both the gene symbol and phenotype term are required.',
  none: 'This catalog entry cannot be queried directly from the workbench.',
  api: 'Parameters depend on the upstream API. Provide the values documented for this integration.',
} as const

interface ResultsViewProps {
  parameters: QueryParameters
  currentSpaceId: string | null
  catalog: SourceCatalogEntry[]
  results: QueryTestResult[]
  selectedSourceIds: string[]
  sourceParameters: Record<string, QueryParameters>
  advancedSettings: Record<string, SourceAdvancedSettings>
  defaultParameters: QueryParameters
  defaultAdvancedSettings?: SourceAdvancedSettings
  isLoading: boolean
  onBackToSelect: () => void
  onAddToSpace: (result: QueryTestResult, spaceId: string) => Promise<void>
  onRunTest?: (catalogEntryId: string) => Promise<void>
  onUpdateSourceParameters: (sourceId: string, params: QueryParameters) => void
  onUpdateAdvancedSettings: (sourceId: string, settings: SourceAdvancedSettings) => void
}

export function ResultsView({
  parameters,
  currentSpaceId,
  catalog,
  results,
  selectedSourceIds,
  sourceParameters,
  advancedSettings,
  defaultParameters,
  defaultAdvancedSettings = DEFAULT_ADVANCED_SETTINGS,
  isLoading,
  onBackToSelect,
  onAddToSpace,
  onRunTest,
  onUpdateSourceParameters,
  onUpdateAdvancedSettings,
}: ResultsViewProps) {
  const [spaceSelectorOpen, setSpaceSelectorOpen] = useState(false)
  const [selectedResultForSpace, setSelectedResultForSpace] = useState<QueryTestResult | null>(null)
  const [addingResultId, setAddingResultId] = useState<string | null>(null)
  const [runningResultId, setRunningResultId] = useState<string | null>(null)
  const [runningSourceId, setRunningSourceId] = useState<string | null>(null)
  const [configuringSourceId, setConfiguringSourceId] = useState<string | null>(null)

  const catalogById = useMemo(() => {
    const map = new Map<string, SourceCatalogEntry>()
    catalog.forEach((entry) => map.set(entry.id, entry))
    return map
  }, [catalog])

  const latestResultBySource = useMemo(() => {
    const map = new Map<string, QueryTestResult>()
    results.forEach((result) => {
      const existing = map.get(result.catalog_entry_id)
      const existingTime = existing
        ? new Date(existing.completed_at ?? existing.started_at).getTime()
        : -Infinity
      const candidateTime = new Date(result.completed_at ?? result.started_at).getTime()
      if (!existing || candidateTime >= existingTime) {
        map.set(result.catalog_entry_id, result)
      }
    })
    return map
  }, [results])

  const selectedSourcesWithMeta = useMemo(
    () =>
      selectedSourceIds
        .map((sourceId) => {
          const entry = catalogById.get(sourceId)
          if (!entry) {
            return null
          }
          return {
            entry,
            latestResult: latestResultBySource.get(sourceId) ?? null,
            parameters: sourceParameters[sourceId] ?? defaultParameters,
            advancedSettings: advancedSettings[sourceId] ?? defaultAdvancedSettings,
          }
        })
        .filter(
          (
            value,
          ): value is {
            entry: SourceCatalogEntry
            latestResult: QueryTestResult | null
            parameters: QueryParameters
            advancedSettings: SourceAdvancedSettings
          } => value !== null,
        ),
    [
      selectedSourceIds,
      catalogById,
      latestResultBySource,
      sourceParameters,
      advancedSettings,
      defaultParameters,
      defaultAdvancedSettings,
    ],
  )

  const handleAddToSpaceRequest = async (result: QueryTestResult) => {
    if (currentSpaceId) {
      await handleAddToSpace(result, currentSpaceId)
      return
    }
    setSelectedResultForSpace(result)
    setSpaceSelectorOpen(true)
  }

  const handleAddToSpace = async (result: QueryTestResult, spaceId: string) => {
    try {
      setAddingResultId(result.id)
      await onAddToSpace(result, spaceId)
    } catch (error) {
      console.error('Failed to add source to space', error)
    } finally {
      setAddingResultId(null)
    }
  }

  const handleSpaceSelected = async (spaceId: string) => {
    if (selectedResultForSpace) {
      await handleAddToSpace(selectedResultForSpace, spaceId)
    }
    setSelectedResultForSpace(null)
    setSpaceSelectorOpen(false)
  }

  const handleRunResult = async (result: QueryTestResult) => {
    if (!onRunTest) return
    try {
      setRunningResultId(result.id)
      await onRunTest(result.catalog_entry_id)
    } finally {
      setRunningResultId(null)
    }
  }

  const handleRunSelectedSource = async (sourceId: string) => {
    if (!onRunTest) return
    try {
      setRunningSourceId(sourceId)
      await onRunTest(sourceId)
    } finally {
      setRunningSourceId(null)
    }
  }

  const configuringEntry = configuringSourceId ? catalogById.get(configuringSourceId) ?? null : null
  const configuringParams =
    (configuringSourceId && (sourceParameters[configuringSourceId] ?? defaultParameters)) || defaultParameters
  const configuringAdvancedSettings =
    (configuringSourceId && (advancedSettings[configuringSourceId] ?? defaultAdvancedSettings))
    || defaultAdvancedSettings

  const renderGeneratedResultsSection = () => {
    if (isLoading) {
      return (
        <Card className="py-12 text-center">
          <CardContent>
            <Loader2 className="mx-auto mb-4 size-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Loading generated results...</p>
          </CardContent>
        </Card>
      )
    }

    if (results.length === 0) {
      return (
        <Card className="py-12 text-center">
          <CardContent>
            <FolderOpen className="mx-auto mb-4 size-16 text-muted-foreground" />
            <h2 className="mb-2 text-xl font-semibold text-foreground">Awaiting Test Runs</h2>
            <p className="mb-4 text-muted-foreground">
              Use the &ldquo;Run Test&rdquo; actions above to generate results for individual sources.
            </p>
            <Button onClick={onBackToSelect}>
              <ArrowLeft className="mr-2 size-4" />
              Back to Selection
            </Button>
          </CardContent>
        </Card>
      )
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Generated Results</span>
            <Button variant="outline" size="sm" onClick={onBackToSelect}>
              <ArrowLeft className="mr-2 size-4" />
              Back to Selection
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {results.map((result) => (
              <ResultCard
                key={result.id}
                result={result}
                parameters={parameters}
                catalog={catalog}
                onAddToSpace={() => handleAddToSpaceRequest(result)}
                onRunTest={onRunTest ? () => handleRunResult(result) : undefined}
                isAddingToSpace={addingResultId === result.id}
                isRunningTest={runningResultId === result.id}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Selected Sources</span>
            <Button variant="outline" size="sm" onClick={onBackToSelect}>
              <ArrowLeft className="mr-2 size-4" />
              Back to Selection
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedSourcesWithMeta.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Select catalog entries to build your testing list.
            </p>
          ) : (
            <div className="space-y-4">
              {selectedSourcesWithMeta.map(({ entry, latestResult, parameters: sourceParams, advancedSettings: sourceAdvanced }) => (
                <SelectedSourceCard
                  key={entry.id}
                  entry={entry}
                  latestResult={latestResult}
                  parameters={sourceParams}
                  advancedSettings={sourceAdvanced}
                  isRunning={runningSourceId === entry.id}
                  onRunTest={onRunTest ? () => handleRunSelectedSource(entry.id) : undefined}
                  onConfigure={() => setConfiguringSourceId(entry.id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {renderGeneratedResultsSection()}

      <SpaceSelectorModal
        open={spaceSelectorOpen}
        onOpenChange={setSpaceSelectorOpen}
        onSpaceChange={(spaceId) => handleSpaceSelected(spaceId)}
      />

      <SourceParameterModal
        open={Boolean(configuringEntry)}
        entry={configuringEntry}
        parameters={configuringParams}
        advancedSettings={configuringAdvancedSettings}
        defaultParameters={defaultParameters}
        defaultAdvancedSettings={defaultAdvancedSettings}
        onClose={() => setConfiguringSourceId(null)}
        onSave={(nextParams, nextAdvancedSettings) => {
          if (configuringSourceId) {
            onUpdateSourceParameters(configuringSourceId, nextParams)
            onUpdateAdvancedSettings(configuringSourceId, nextAdvancedSettings)
          }
          setConfiguringSourceId(null)
        }}
      />
    </>
  )
}

interface SelectedSourceCardProps {
  entry: SourceCatalogEntry
  latestResult: QueryTestResult | null
  parameters: QueryParameters
  advancedSettings: SourceAdvancedSettings
  isRunning: boolean
  onRunTest?: () => Promise<void> | void
  onConfigure: () => void
}

function SelectedSourceCard({
  entry,
  latestResult,
  parameters,
  advancedSettings,
  isRunning,
  onRunTest,
  onConfigure,
}: SelectedSourceCardProps) {
  const IconComponent = CATEGORY_ICONS[entry.category] || Database
  const normalizedType = normalizeParamType(entry.param_type)
  const typeLabel = SOURCE_TYPE_LABELS[entry.source_type]

  const statusBadge = latestResult ? (
    <Badge
      variant={
        latestResult.status === 'success'
          ? 'default'
          : latestResult.status === 'error' || latestResult.status === 'validation_failed'
            ? 'destructive'
            : 'secondary'
      }
    >
      {latestResult.status.replace('_', ' ')}
    </Badge>
  ) : (
    <Badge variant="outline">Not Tested</Badge>
  )

  const lastRunLabel = latestResult
    ? `Last run ${new Date(latestResult.completed_at ?? latestResult.started_at).toLocaleString()}`
    : 'Not tested yet'

  return (
    <Card className="border-border">
      <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">
          <IconComponent className="mt-1 size-5 text-primary" />
          <div>
            <h3 className="font-semibold text-foreground">{entry.name}</h3>
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span>{entry.category}</span>
              <Badge variant="outline" className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
                {SOURCE_TYPE_LABELS[entry.source_type]}
              </Badge>
              <Badge variant="secondary">{PARAMETER_LABELS[normalizedType]}</Badge>
            </div>
            <p className="text-xs text-muted-foreground">{lastRunLabel}</p>
            <p className="text-xs text-muted-foreground">
              Gene: {parameters.gene_symbol ?? '—'} • Phenotype: {parameters.search_term ?? '—'}
            </p>
            <p className="text-xs text-muted-foreground">
              Schedule:{' '}
              {advancedSettings.scheduling.enabled
                ? `${advancedSettings.scheduling.frequency.toUpperCase()} • ${advancedSettings.scheduling.timezone}`
                : 'Manual'}
            </p>
            {advancedSettings.notes && (
              <p className="line-clamp-1 text-xs text-muted-foreground">
                Notes: {advancedSettings.notes}
              </p>
            )}
          </div>
        </div>
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <div className="flex items-center gap-3">
            {statusBadge}
            <Button variant="outline" size="sm" onClick={onConfigure}>
              <Settings2 className="mr-2 size-4" />
              Configure
            </Button>
          </div>
          <Button
            size="sm"
            onClick={onRunTest}
            disabled={!onRunTest || isRunning}
            className="flex items-center gap-2"
          >
            {isRunning ? <Loader2 className="size-4 animate-spin" /> : <Terminal className="size-4" />}
            <span>{isRunning ? 'Running...' : latestResult ? 'Re-run Test' : 'Run Test'}</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

interface ResultCardProps {
  result: QueryTestResult
  parameters: QueryParameters
  catalog: SourceCatalogEntry[]
  onAddToSpace: () => Promise<void> | void
  onRunTest?: () => Promise<void> | void
  isRunningTest: boolean
  isAddingToSpace: boolean
}

function ResultCard({
  result,
  parameters,
  catalog,
  onAddToSpace,
  onRunTest,
  isRunningTest,
  isAddingToSpace,
}: ResultCardProps) {
  const isApiResult = !result.response_url
  const catalogEntry = catalog.find((entry) => entry.id === result.catalog_entry_id)
  const displayName = catalogEntry?.name || result.catalog_entry_id
  const category = catalogEntry?.category || 'Unknown'
  const typeLabel = catalogEntry ? SOURCE_TYPE_LABELS[catalogEntry.source_type] : null
  const IconComponent = CATEGORY_ICONS[category] || Database

  const getStatusBadge = (status: string) => {
    const variants = {
      success: 'default' as const,
      error: 'destructive' as const,
      pending: 'secondary' as const,
      timeout: 'outline' as const,
      validation_failed: 'destructive' as const,
    }
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
        {status.replace('_', ' ')}
      </Badge>
    )
  }

  const isParamMissing =
    (Boolean(result.parameters.gene_symbol) && !parameters.gene_symbol) ||
    (Boolean(result.parameters.search_term) && !parameters.search_term)

  return (
    <Card className="border-border">
      <CardContent className="p-4">
        <div className="flex w-full flex-col justify-between md:flex-row md:items-center">
          <div className="mb-3 flex items-center space-x-3 md:mb-0">
            <div className="shrink-0">
              <IconComponent className="size-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground">{displayName}</h3>
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span>{category}</span>
                {typeLabel && (
                  <Badge variant="outline" className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
                    {typeLabel}
                  </Badge>
                )}
                <span>• Test ID: {result.id.slice(-8)}</span>
              </div>
            </div>
          </div>

          <div className="flex shrink-0 items-center space-x-3">
            {getStatusBadge(result.status)}

            {isParamMissing && <span className="text-xs text-yellow-600 dark:text-yellow-400">Missing parameters</span>}

            {isApiResult ? (
              <Button
                onClick={onRunTest}
                disabled={isParamMissing || isRunningTest}
                size="sm"
                className="flex items-center space-x-2"
              >
                {isRunningTest ? <Loader2 className="size-4 animate-spin" /> : <Terminal className="size-4" />}
                <span>{isRunningTest ? 'Running...' : 'Run API'}</span>
              </Button>
            ) : result.response_url ? (
              <Button asChild variant="outline" size="sm">
                <a
                  href={result.response_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2"
                >
                  <ExternalLink className="size-4" />
                  <span>View Response</span>
                </a>
              </Button>
            ) : null}

            <Button variant="secondary" size="sm" onClick={onAddToSpace} disabled={isParamMissing || isAddingToSpace}>
              {isAddingToSpace ? <Loader2 className="mr-2 size-4 animate-spin" /> : <ClipboardList className="mr-2 size-4" />}
              <span>{isAddingToSpace ? 'Adding...' : 'Promote to Space'}</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface SourceParameterModalProps {
  open: boolean
  entry: SourceCatalogEntry | null
  parameters: QueryParameters
  advancedSettings: SourceAdvancedSettings
  defaultParameters: QueryParameters
  defaultAdvancedSettings: SourceAdvancedSettings
  onClose: () => void
  onSave: (params: QueryParameters, advanced: SourceAdvancedSettings) => void
}

function SourceParameterModal({
  open,
  entry,
  parameters,
  advancedSettings,
  defaultParameters,
  defaultAdvancedSettings,
  onClose,
  onSave,
}: SourceParameterModalProps) {
  const [formValues, setFormValues] = useState<QueryParameters>(parameters)
  const [advancedValues, setAdvancedValues] = useState<SourceAdvancedSettings>(advancedSettings)
  const [isDirty, setIsDirty] = useState(false)
  const previousEntryIdRef = useRef<string | null>(null)

  useEffect(() => {
    const currentEntryId = entry?.id ?? null

    if (!open) {
      previousEntryIdRef.current = currentEntryId
      setFormValues(parameters)
      setAdvancedValues(advancedSettings)
      setIsDirty(false)
      return
    }

    if (currentEntryId !== previousEntryIdRef.current) {
      previousEntryIdRef.current = currentEntryId
      setFormValues(parameters)
      setAdvancedValues(advancedSettings)
      setIsDirty(false)
      return
    }

    if (!isDirty) {
      setFormValues(parameters)
      setAdvancedValues(advancedSettings)
    }
  }, [advancedSettings, entry?.id, isDirty, open, parameters])

  if (!entry) {
    return null
  }

  const normalizedType = normalizeParamType(entry.param_type)
  const typeLabel = SOURCE_TYPE_LABELS[entry.source_type]
  const showGeneInput =
    normalizedType === 'gene' || normalizedType === 'geneAndTerm' || normalizedType === 'api'
  const showTermInput =
    normalizedType === 'term' || normalizedType === 'geneAndTerm' || normalizedType === 'api'
  const geneRequired = normalizedType === 'gene' || normalizedType === 'geneAndTerm'
  const termRequired = normalizedType === 'term' || normalizedType === 'geneAndTerm'
  const requiresParameters = normalizedType !== 'none'

  return (
    <Dialog open={open} onOpenChange={(value) => !value && onClose()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Configure {entry.name}</DialogTitle>
          <DialogDescription>
            Adjust the query parameters used when testing this catalog entry. Overrides apply only to the current
            session.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-foreground">{entry.category}</p>
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="outline" className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
                  {typeLabel}
                </Badge>
                <span>{PARAMETER_LABELS[normalizedType]}</span>
              </div>
            </div>
            {entry.requires_auth && (
              <Badge
                variant="outline"
                className="border-amber-500 text-amber-600 dark:border-amber-200 dark:text-amber-100"
              >
                <KeyRound className="mr-1 size-3" />
                Auth required
              </Badge>
            )}
          </div>

          <p className="text-sm text-muted-foreground">{PARAMETER_DESCRIPTIONS[normalizedType]}</p>

          {entry.requires_auth && (
            <Alert className="border-amber-500/50 bg-amber-50 dark:bg-amber-950/30">
              <AlertTitle className="text-sm font-semibold text-amber-900 dark:text-amber-100">
                API credential required
              </AlertTitle>
              <AlertDescription className="text-xs text-amber-900/80 dark:text-amber-50">
                Configure API keys for this vendor in System Settings → Data Sources before executing queries.
              </AlertDescription>
            </Alert>
          )}

          {!requiresParameters && (
            <Alert>
              <AlertTitle className="text-sm font-semibold">No query parameters required</AlertTitle>
              <AlertDescription className="text-xs">
                This catalog entry is informational only. Activate an associated ingestion template to run data pulls.
              </AlertDescription>
            </Alert>
          )}
          {requiresParameters && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {showGeneInput && (
                <div>
                  <Label htmlFor={`${entry.id}-gene`} className="text-xs text-muted-foreground">
                    Gene Symbol {geneRequired ? <span className="text-destructive">*</span> : null}
                  </Label>
                  <Input
                    id={`${entry.id}-gene`}
                    placeholder="e.g., MED13L"
                    value={formValues.gene_symbol ?? ''}
                    onChange={(event) => {
                      const value = event.target.value.toUpperCase()
                      setFormValues((prev) => ({
                        ...prev,
                        gene_symbol: value.trim() === '' ? null : value.trim(),
                      }))
                      setIsDirty(true)
                    }}
                    className="mt-1 bg-background"
                  />
                </div>
              )}
              {showTermInput && (
                <div>
                  <Label htmlFor={`${entry.id}-term`} className="text-xs text-muted-foreground">
                    Phenotype / Search Term {termRequired ? <span className="text-destructive">*</span> : null}
                  </Label>
                  <Input
                    id={`${entry.id}-term`}
                    placeholder="e.g., atrial septal defect"
                    value={formValues.search_term ?? ''}
                    onChange={(event) => {
                      const value = event.target.value
                      setFormValues((prev) => ({
                        ...prev,
                        search_term: value.trim() === '' ? null : value.trim(),
                      }))
                      setIsDirty(true)
                    }}
                    className="mt-1 bg-background"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        <div className="mt-6 space-y-4 rounded-lg border border-border/60 bg-muted/20 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">Scheduling (optional)</p>
              <p className="text-xs text-muted-foreground">
                Configure how often MED13 should ingest this source once promoted to a research space.
              </p>
            </div>
            <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <input
                type="checkbox"
                className="size-4 rounded border border-input"
                checked={advancedValues.scheduling.enabled}
                onChange={(event) => {
                  setAdvancedValues((prev) => ({
                    ...prev,
                    scheduling: {
                      ...prev.scheduling,
                      enabled: event.target.checked,
                    },
                  }))
                  setIsDirty(true)
                }}
              />
              Enable
            </label>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <Label className="text-xs text-muted-foreground">Frequency</Label>
              <select
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={advancedValues.scheduling.frequency}
                disabled={!advancedValues.scheduling.enabled}
                onChange={(event) => {
                  const value = event.target.value as ScheduleFrequency
                  setAdvancedValues((prev) => ({
                    ...prev,
                    scheduling: {
                      ...prev.scheduling,
                      frequency: value,
                    },
                  }))
                  setIsDirty(true)
                }}
              >
                <option value="manual">Manual</option>
                <option value="hourly">Hourly</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="cron">Cron</option>
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Timezone</Label>
              <Input
                className="mt-1 bg-background"
                placeholder="UTC"
                value={advancedValues.scheduling.timezone}
                disabled={!advancedValues.scheduling.enabled}
                onChange={(event) => {
                  setAdvancedValues((prev) => ({
                    ...prev,
                    scheduling: {
                      ...prev.scheduling,
                      timezone: event.target.value || 'UTC',
                    },
                  }))
                  setIsDirty(true)
                }}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <Label className="text-xs text-muted-foreground">Start time</Label>
              <Input
                type="datetime-local"
                className="mt-1 bg-background"
                value={advancedValues.scheduling.startTime ?? ''}
                disabled={!advancedValues.scheduling.enabled}
                onChange={(event) => {
                  setAdvancedValues((prev) => ({
                    ...prev,
                    scheduling: {
                      ...prev.scheduling,
                      startTime: event.target.value || null,
                    },
                  }))
                  setIsDirty(true)
                }}
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Cron expression</Label>
              <Input
                className="mt-1 bg-background"
                placeholder="0 0 * * *"
                value={advancedValues.scheduling.cronExpression ?? ''}
                disabled={
                  !advancedValues.scheduling.enabled ||
                  advancedValues.scheduling.frequency !== 'cron'
                }
                onChange={(event) => {
                  setAdvancedValues((prev) => ({
                    ...prev,
                    scheduling: {
                      ...prev.scheduling,
                      cronExpression: event.target.value || null,
                    },
                  }))
                  setIsDirty(true)
                }}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Only used when frequency is set to cron.
              </p>
            </div>
          </div>

          <div>
            <Label className="text-xs text-muted-foreground">Notes / Integration details</Label>
            <textarea
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              rows={3}
              placeholder="Optional notes, credentials location, mapping requirements..."
              value={advancedValues.notes}
              onChange={(event) => {
                setAdvancedValues((prev) => ({
                  ...prev,
                  notes: event.target.value,
                }))
                setIsDirty(true)
              }}
            />
          </div>
        </div>

        <DialogFooter className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              setFormValues(defaultParameters)
              setAdvancedValues(defaultAdvancedSettings)
              setIsDirty(true)
            }}
            className="justify-start sm:justify-center"
          >
            Reset to defaults
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                onSave(formValues, advancedValues)
                setIsDirty(false)
              }}
            >
              Save Configuration
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function normalizeParamType(paramType: string): 'gene' | 'term' | 'geneAndTerm' | 'none' | 'api' {
  switch (paramType) {
    case 'gene_and_term':
      return 'geneAndTerm'
    case 'gene':
    case 'term':
    case 'none':
    case 'api':
    case 'geneAndTerm':
      return paramType as 'gene' | 'term' | 'geneAndTerm' | 'none' | 'api'
    default:
      return 'geneAndTerm'
  }
}
