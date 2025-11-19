"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import dynamic from 'next/dynamic'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { CatalogSkeleton } from '@/components/data-discovery/CatalogSkeleton'
import { ResultsSkeleton } from '@/components/data-discovery/ResultsSkeleton'
import { ParameterBar } from '@/components/data-discovery/ParameterBar'
import { useSpaceContext } from '@/components/space-context-provider'
import type {
  AdvancedQueryParameters,
  DiscoveryPreset,
  QueryParameterCapabilities,
  QueryTestResult,
  SourceCatalogEntry,
} from '@/lib/types/data-discovery'
import {
  useAddDiscoverySourceToSpace,
  useCreateDataDiscoverySession,
  useCreatePubmedPreset,
  useDataDiscoverySessions,
  useDeletePubmedPreset,
  useDownloadPubmedPdf,
  useExecuteDataDiscoveryTest,
  usePubmedPresets,
  usePubmedSearchJob,
  useRunPubmedSearch,
  useSessionTestResults,
  useSourceCatalog,
  useToggleDataDiscoverySourceSelection,
  useSetDataDiscoverySelections,
} from '@/lib/queries/data-discovery'
import { toast } from 'sonner'
import { syncDiscoverySessionState } from '@/lib/state/discovery-session-sync'
import { PageHero, DashboardSection } from '@/components/ui/composition-patterns'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
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
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import {
  createDefaultAdvancedSettings,
  DEFAULT_ADVANCED_SETTINGS as DEFAULT_ADVANCED_SOURCE_SETTINGS,
  type SourceAdvancedSettings,
} from '@/components/data-discovery/advanced-settings'

// Code split heavy components - only load when needed
const SourceCatalog = dynamic(
  () => import('@/components/data-discovery/SourceCatalog').then((mod) => ({ default: mod.SourceCatalog })),
  {
    ssr: false,
    loading: () => <CatalogSkeleton />,
  }
)

const ResultsView = dynamic(
  () => import('@/components/data-discovery/ResultsView').then((mod) => ({ default: mod.ResultsView })),
  {
    ssr: false,
    loading: () => <ResultsSkeleton />,
  }
)

const DEFAULT_PARAMETERS: AdvancedQueryParameters = {
  gene_symbol: 'MED13L',
  search_term: 'atrial septal defect',
  date_from: null,
  date_to: null,
  publication_types: [],
  languages: [],
  sort_by: 'relevance',
  max_results: 100,
  additional_terms: null,
}

const DEFAULT_CAPABILITIES: QueryParameterCapabilities = {
  supports_date_range: true,
  supports_publication_types: true,
  supports_language_filter: true,
  supports_sort_options: true,
  supports_additional_terms: true,
  max_results_limit: 1000,
  supported_storage_use_cases: [],
  supports_variation_type: false,
  supports_clinical_significance: false,
  supports_review_status: false,
  supports_organism: false,
}

interface DataDiscoveryClientProps {
  initialSessionId: string | null
  initialParameters: AdvancedQueryParameters | null
  initialSelectedSources: string[]
}

export default function DataDiscoveryClient({
  initialSessionId,
  initialParameters,
  initialSelectedSources,
}: DataDiscoveryClientProps) {
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const [parameters, setParameters] = useState<AdvancedQueryParameters>(
    initialParameters ?? DEFAULT_PARAMETERS,
  )
  const [sourceParameters, setSourceParameters] = useState<
    Record<string, AdvancedQueryParameters>
  >({})
  const [sourceAdvancedSettings, setSourceAdvancedSettings] = useState<Record<string, SourceAdvancedSettings>>({})
  const [selectedSources, setSelectedSources] = useState<string[]>(initialSelectedSources)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(initialSessionId)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPresetDialogOpen, setPresetDialogOpen] = useState(false)
  const [newPresetName, setNewPresetName] = useState('')
  const [newPresetDescription, setNewPresetDescription] = useState('')
  const [presetScope, setPresetScope] = useState<'user' | 'space'>('user')
  const [deletingPresetId, setDeletingPresetId] = useState<string | null>(null)
  const [activeSearchJobId, setActiveSearchJobId] = useState<string | null>(null)
  const [downloadedStorageKey, setDownloadedStorageKey] = useState<string | null>(null)
  const createRequestedRef = useRef(false)

  const { currentSpaceId } = useSpaceContext()

  const catalogQuery = useSourceCatalog(
    currentSpaceId ? { research_space_id: currentSpaceId } : undefined,
  )
  const sessionsQuery = useDataDiscoverySessions()
  const testsQuery = useSessionTestResults(activeSessionId)
  const refetchSessions = sessionsQuery.refetch

  const createSessionMutation = useCreateDataDiscoverySession()
  const toggleSourceMutation = useToggleDataDiscoverySourceSelection()
  const executeTestMutation = useExecuteDataDiscoveryTest()
  const addToSpaceMutation = useAddDiscoverySourceToSpace()
  const setSelectionsMutation = useSetDataDiscoverySelections()
  const presetQueryParams = currentSpaceId ? { research_space_id: currentSpaceId } : undefined
const presetBetaEnabled = process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA === 'true'
const presetsQuery = usePubmedPresets(presetQueryParams, { enabled: presetBetaEnabled })
const presets = presetsQuery.data ?? []
const createPresetMutation = useCreatePubmedPreset()
const deletePresetMutation = useDeletePubmedPreset(presetQueryParams)
const runSearchMutation = useRunPubmedSearch()
const downloadPdfMutation = useDownloadPubmedPdf()
const activeSearchJobQuery = usePubmedSearchJob(activeSearchJobId)
  const {
    mutate: createSession,
    isPending: isCreatingSession,
    isError: isCreateSessionError,
  } = createSessionMutation

  const catalog: SourceCatalogEntry[] = useMemo(
    () => catalogQuery.data ?? [],
    [catalogQuery.data],
  )
  const catalogById = useMemo(() => {
    const map = new Map<string, SourceCatalogEntry>()
    catalog.forEach((entry) => {
      map.set(entry.id, entry)
    })
    return map
  }, [catalog])
  const testResults = testsQuery.data ?? []
  const activeCapabilities = useMemo(() => {
    if (selectedSources.length === 0) {
      return { ...DEFAULT_CAPABILITIES }
    }
    return selectedSources.reduce((acc, sourceId) => {
      const entry = catalogById.get(sourceId)
      if (!entry) {
        return acc
      }
      const caps = entry.capabilities ?? DEFAULT_CAPABILITIES
      return {
        supports_date_range: acc.supports_date_range && Boolean(caps.supports_date_range),
        supports_publication_types:
          acc.supports_publication_types && Boolean(caps.supports_publication_types),
        supports_language_filter:
          acc.supports_language_filter && Boolean(caps.supports_language_filter),
        supports_sort_options:
          acc.supports_sort_options && Boolean(caps.supports_sort_options),
        supports_additional_terms:
          acc.supports_additional_terms && Boolean(caps.supports_additional_terms),
        max_results_limit: Math.min(
          acc.max_results_limit,
          caps.max_results_limit ?? DEFAULT_CAPABILITIES.max_results_limit,
        ),
        supported_storage_use_cases: Array.from(
          new Set([
            ...acc.supported_storage_use_cases,
            ...(caps.supported_storage_use_cases ?? []),
          ]),
        ),
        supports_variation_type:
          acc.supports_variation_type || Boolean(caps.supports_variation_type),
        supports_clinical_significance:
          acc.supports_clinical_significance || Boolean(caps.supports_clinical_significance),
        supports_review_status:
          acc.supports_review_status || Boolean(caps.supports_review_status),
        supports_organism: acc.supports_organism || Boolean(caps.supports_organism),
      }
    }, { ...DEFAULT_CAPABILITIES })
  }, [selectedSources, catalogById])
  const hasPubmedSelection = useMemo(
    () => selectedSources.some((id) => catalogById.get(id)?.source_type === 'pubmed'),
    [selectedSources, catalogById],
  )
  const catalogError = catalogQuery.error instanceof Error ? catalogQuery.error : null

  useEffect(() => {
    if (!sessionsQuery.isSuccess) {
      return
    }

    const {
      nextSessionId,
      nextParameters,
      nextSelectedSources,
      shouldCreateSession: shouldCreateFromSync,
    } = syncDiscoverySessionState(sessionsQuery.data ?? [])

    if (shouldCreateFromSync) {
      setActiveSessionId(null)
      setSelectedSources([])
      if (!isCreatingSession && !createRequestedRef.current) {
        createRequestedRef.current = true
        createSession({
          name: 'Discovery Session',
          research_space_id: currentSpaceId ?? undefined,
          initial_parameters: parameters,
        })
      }
      return
    }

    createRequestedRef.current = false

    if (nextSessionId && activeSessionId !== nextSessionId) {
      setActiveSessionId(nextSessionId)
    }

    if (!areArraysEqual(selectedSources, nextSelectedSources)) {
      setSelectedSources(nextSelectedSources)
    }

    if (nextParameters && !isSameParameters(parameters, nextParameters)) {
      setParameters(nextParameters)
    }
  }, [
    sessionsQuery.isSuccess,
    sessionsQuery.data,
    activeSessionId,
    selectedSources,
    parameters,
    isCreatingSession,
    createSession,
    currentSpaceId,
  ])

  useEffect(() => {
    setParameters((current) => {
      let changed = false
      const next: AdvancedQueryParameters = { ...current }
      if (!activeCapabilities.supports_date_range) {
        if (next.date_from) {
          next.date_from = null
          changed = true
        }
        if (next.date_to) {
          next.date_to = null
          changed = true
        }
      }
      if (!activeCapabilities.supports_publication_types && next.publication_types?.length) {
        next.publication_types = []
        changed = true
      }
      if (!activeCapabilities.supports_language_filter && next.languages?.length) {
        next.languages = []
        changed = true
      }
      if (!activeCapabilities.supports_additional_terms && next.additional_terms) {
        next.additional_terms = null
        changed = true
      }
      if (!activeCapabilities.supports_sort_options && next.sort_by) {
        next.sort_by = 'relevance'
        changed = true
      }
      const maxLimit = activeCapabilities.max_results_limit ?? DEFAULT_CAPABILITIES.max_results_limit
      if ((next.max_results ?? 100) > maxLimit) {
        next.max_results = maxLimit
        changed = true
      }
      return changed ? next : current
    })
  }, [activeCapabilities])

useEffect(() => {
  if (isCreateSessionError) {
    createRequestedRef.current = false
  }
}, [isCreateSessionError])

useEffect(() => {
  if (!activeSearchJobId) {
    return
  }
  const job = activeSearchJobQuery.data
  if (!job) {
    return
  }
  if (job.status === 'failed') {
    toast.error('PubMed search failed. Please try again.')
    setActiveSearchJobId(null)
    return
  }
  if (job.status !== 'completed' || downloadPdfMutation.isPending) {
    return
  }
  const rawIds = job.result_metadata?.article_ids
  const articleIds = Array.isArray(rawIds)
    ? rawIds.map((value) => String(value))
    : []
  if (articleIds.length === 0) {
    toast.error('No PubMed articles were returned for download.')
    setActiveSearchJobId(null)
    return
  }
  ;(async () => {
    try {
      const record = await downloadPdfMutation.mutateAsync({
        job_id: job.id,
        article_id: articleIds[0],
      })
      setDownloadedStorageKey(record.key)
      toast.success(`PDF stored to ${record.key}`)
    } catch (error) {
      console.error(error)
      toast.error('Failed to store PubMed PDF.')
    } finally {
      setActiveSearchJobId(null)
    }
  })()
}, [activeSearchJobId, activeSearchJobQuery.data, downloadPdfMutation])

  const getParametersForSource = useCallback(
    (sourceId: string) => sourceParameters[sourceId] ?? parameters,
    [sourceParameters, parameters],
  )

  const handleSourceParametersChange = useCallback(
    (sourceId: string, nextParams: AdvancedQueryParameters) => {
      setSourceParameters((prev) => ({
        ...prev,
        [sourceId]: nextParams,
      }))
    },
    [],
  )

  const handleSourceAdvancedSettingsChange = useCallback(
    (sourceId: string, nextSettings: SourceAdvancedSettings) => {
      setSourceAdvancedSettings((prev) => ({
        ...prev,
        [sourceId]: nextSettings,
      }))
    },
    [],
  )

  const resolveExecutionContext = useCallback(
    (
      sourceId: string,
    ):
      | {
          parameters: AdvancedQueryParameters
          catalogEntry: SourceCatalogEntry
        }
      | null => {
      const catalogEntry = catalogById.get(sourceId)
      if (!catalogEntry) {
        toast.error('Unable to load metadata for the selected source')
        return null
      }

      const parametersForSource = getParametersForSource(sourceId)
      const validationResult = validateParametersForSource(catalogEntry, parametersForSource)

      if (!validationResult.ok) {
        toast.error(`${catalogEntry.name}: ${validationResult.message}`)
        return null
      }

      return { parameters: parametersForSource, catalogEntry }
    },
    [catalogById, getParametersForSource],
  )

  useEffect(() => {
    setSourceParameters((current) => {
      const next = { ...current }
      let changed = false

      selectedSources.forEach((sourceId) => {
        if (!next[sourceId]) {
          next[sourceId] = parameters
          changed = true
        }
      })

      Object.keys(next).forEach((sourceId) => {
        if (!selectedSources.includes(sourceId)) {
          delete next[sourceId]
          changed = true
        }
      })

      return changed ? next : current
    })
  }, [selectedSources, parameters])

  useEffect(() => {
    setSourceAdvancedSettings((current) => {
      const next = { ...current }
      let changed = false

      selectedSources.forEach((sourceId) => {
        if (!next[sourceId]) {
          next[sourceId] = createDefaultAdvancedSettings()
          changed = true
        }
      })

      Object.keys(next).forEach((sourceId) => {
        if (!selectedSources.includes(sourceId)) {
          delete next[sourceId]
          changed = true
        }
      })

      return changed ? next : current
    })
  }, [selectedSources])

  const handleToggleSource = useCallback(
    async (sourceId: string) => {
      if (!activeSessionId) {
        return
      }
      try {
        const session = await toggleSourceMutation.mutateAsync({
          sessionId: activeSessionId,
          catalogEntryId: sourceId,
        })
        setSelectedSources(session.selected_sources)
      } catch (error: unknown) {
        console.error(error)
        if (error instanceof AxiosError && error.response?.status === 404) {
          createRequestedRef.current = false
          await refetchSessions()
          toast.error('Session expired. Recreating discovery session…')
          return
        }
        toast.error('Failed to update source selection')
      }
    },
    [activeSessionId, toggleSourceMutation, refetchSessions],
  )

  const applySelectionUpdate = useCallback(
    async (nextSelections: string[]) => {
      if (!activeSessionId) {
        return
      }
      const uniqueSelections = Array.from(new Set(nextSelections))
      try {
        const session = await setSelectionsMutation.mutateAsync({
          sessionId: activeSessionId,
          sourceIds: uniqueSelections,
        })
        setSelectedSources(session.selected_sources)
      } catch (error) {
        console.error(error)
        if (error instanceof AxiosError && error.response?.status === 404) {
          createRequestedRef.current = false
          await refetchSessions()
          toast.error('Session expired. Recreating discovery session…')
          return
        }
        toast.error('Failed to update source selection')
      }
    },
    [activeSessionId, setSelectionsMutation, refetchSessions],
  )

  const handleSelectAllInCategory = useCallback(
    async (_category: string, sourceIds: string[]) => {
      if (!activeSessionId || sourceIds.length === 0) {
        return
      }
      const uniqueCategoryIds = Array.from(new Set(sourceIds))
      const allSelected = uniqueCategoryIds.every((id) => selectedSources.includes(id))
      const nextSelections = allSelected
        ? selectedSources.filter((id) => !uniqueCategoryIds.includes(id))
        : Array.from(new Set([...selectedSources, ...uniqueCategoryIds]))
      await applySelectionUpdate(nextSelections)
    },
    [activeSessionId, selectedSources, applySelectionUpdate],
  )

  const handleRunTest = useCallback(
    async (sourceId: string) => {
      if (!activeSessionId) {
        toast.error('No discovery session available')
        return
      }

      const executionContext = resolveExecutionContext(sourceId)
      if (!executionContext) {
        return
      }

      setIsGenerating(true)
      try {
        await executeTestMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: {
            catalog_entry_id: sourceId,
            parameters: executionContext.parameters,
          },
        })
        toast.success('Test execution complete')
      } catch (error) {
        console.error(error)
        toast.error('Failed to execute test')
      } finally {
        setIsGenerating(false)
      }
    },
    [activeSessionId, executeTestMutation, resolveExecutionContext],
  )

  const handleRunSingleTest = useCallback(
    async (sourceId: string) => {
      await handleRunTest(sourceId)
    },
    [handleRunTest],
  )

  const buildSourceConfigPayload = useCallback(
    (catalogEntryId: string) => {
      const settings = sourceAdvancedSettings[catalogEntryId]
      if (!settings) {
        return {}
      }
      const { scheduling, notes } = settings
      const payload: Record<string, unknown> = {
        scheduling: {
          enabled: scheduling.enabled,
          frequency: scheduling.frequency,
          timezone: scheduling.timezone || 'UTC',
          start_time: scheduling.startTime ? new Date(scheduling.startTime).toISOString() : null,
          cron_expression:
            scheduling.frequency === 'cron'
              ? scheduling.cronExpression?.trim() || null
              : null,
        },
      }
      if (notes.trim().length > 0) {
        payload.metadata = { notes: notes.trim() }
      }
      return payload
    },
    [sourceAdvancedSettings],
  )

  const handleAddResultToSpace = useCallback(
    async (result: QueryTestResult, spaceId: string) => {
      if (!activeSessionId) {
        toast.error('No discovery session available')
        return
      }

      try {
        await addToSpaceMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: {
            catalog_entry_id: result.catalog_entry_id,
            research_space_id: spaceId,
            source_config: buildSourceConfigPayload(result.catalog_entry_id),
          },
        })
        toast.success('Source added to research space')
      } catch (error) {
        console.error(error)
        toast.error('Failed to add source to space')
      }
    },
    [activeSessionId, addToSpaceMutation, buildSourceConfigPayload],
  )

  const handleGenerateResults = useCallback(() => {
    if (!activeSessionId || selectedSources.length === 0) {
      toast.error('Select at least one data source before continuing')
      return
    }
    setActiveView('results')
    toast.success('Sources added to your testing list')
  }, [activeSessionId, selectedSources])

  const handleDownloadPubmedPdfs = useCallback(async () => {
    if (!hasPubmedSelection) {
      toast.error('Select at least one PubMed source before downloading PDFs')
      return
    }
    try {
      const job = await runSearchMutation.mutateAsync({
        session_id: activeSessionId ?? undefined,
        parameters,
      })
      setDownloadedStorageKey(null)
      setActiveSearchJobId(job.id)
      toast.success('PubMed search started for PDF automation')
    } catch (error) {
      console.error(error)
      toast.error('Failed to start PubMed search')
    }
  }, [hasPubmedSelection, runSearchMutation, activeSessionId, parameters])

  const handleLoadPreset = useCallback(
    (preset: DiscoveryPreset) => {
      setParameters(preset.parameters)
      setPresetDialogOpen(false)
      toast.success(`Preset "${preset.name}" applied`)
    },
    [setParameters],
  )

  const handleDeletePreset = useCallback(
    async (presetId: string) => {
      try {
        setDeletingPresetId(presetId)
        await deletePresetMutation.mutateAsync(presetId)
        toast.success('Preset deleted')
      } catch (error) {
        console.error(error)
        toast.error('Failed to delete preset')
      } finally {
        setDeletingPresetId(null)
      }
    },
    [deletePresetMutation],
  )

  const handlePresetSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      if (!newPresetName.trim()) {
        toast.error('Preset name is required')
        return
      }
      const wantsSpaceScope = presetScope === 'space'
      if (wantsSpaceScope && !currentSpaceId) {
        toast.error('Select a research space before sharing a preset')
        return
      }
      try {
        await createPresetMutation.mutateAsync({
          name: newPresetName.trim(),
          description: newPresetDescription.trim() || null,
          scope: wantsSpaceScope ? 'space' : 'user',
          research_space_id: wantsSpaceScope ? currentSpaceId ?? undefined : undefined,
          parameters,
        })
        setNewPresetName('')
        setNewPresetDescription('')
        setPresetScope('user')
        toast.success('Preset saved')
      } catch (error) {
        console.error(error)
        toast.error('Failed to save preset')
      }
    },
    [
      createPresetMutation,
      currentSpaceId,
      newPresetDescription,
      newPresetName,
      parameters,
      presetScope,
    ],
  )

  return (
    <div className="space-y-6">
      <PageHero
        title="Data Source Discovery"
        description="Discover, test, and promote the highest-quality biomedical data sources for MED13 research workflows."
        variant="research"
        actions={<Badge variant="secondary">Workbench Beta</Badge>}
      />

      <div className="space-y-4">
        <ParameterBar
          parameters={parameters}
          onParametersChange={setParameters}
          capabilities={activeCapabilities}
        />
        {presetBetaEnabled && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-dashed border-muted-foreground/40 bg-muted/30 p-3">
            <div>
              <p className="text-sm font-semibold text-foreground">PubMed Presets</p>
              <p className="text-xs text-muted-foreground">
                Save and reuse this advanced query configuration for future discovery sessions.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-xs text-muted-foreground">
                {presetsQuery.isLoading ? 'Loading…' : `${presets.length} saved`}
              </p>
              <Button variant="outline" size="sm" onClick={() => setPresetDialogOpen(true)}>
                Manage Presets
              </Button>
            </div>
          </div>
        )}

        <div className="space-y-3 rounded-lg border border-border bg-card/50 p-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">PubMed PDF Automation</p>
              <p className="text-xs text-muted-foreground">
                Runs the current PubMed query and stores the first article PDF using the configured storage backend.
              </p>
            </div>
            <Button
              size="sm"
              onClick={handleDownloadPubmedPdfs}
              disabled={
                runSearchMutation.isPending ||
                downloadPdfMutation.isPending ||
                Boolean(activeSearchJobId) ||
                !hasPubmedSelection
              }
            >
              {runSearchMutation.isPending || Boolean(activeSearchJobId)
                ? 'Preparing PDFs…'
                : 'Download PubMed PDFs'}
            </Button>
          </div>
          {!hasPubmedSelection ? (
            <Alert>
              <AlertTitle>Waiting for PubMed source</AlertTitle>
              <AlertDescription>
                Select at least one PubMed catalog entry to enable PDF automation.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="text-xs text-muted-foreground">
              {activeSearchJobId ? (
                <span>
                  Job {activeSearchJobId.slice(0, 8)} status:{' '}
                  {activeSearchJobQuery.data?.status ?? 'queued'}…
                </span>
              ) : downloadedStorageKey ? (
                <span>Most recent PDF stored to {downloadedStorageKey}</span>
              ) : (
                <span>Select “Download PubMed PDFs” to store the latest article.</span>
              )}
            </div>
          )}
        </div>
      </div>

      <DashboardSection
        title={activeView === 'select' ? 'Select Data Sources' : 'Review & Run Tests'}
        description={
          activeView === 'select'
            ? 'Browse the catalog and choose sources to test.'
            : 'Individually configure, execute, and promote each selected source.'
        }
      >
        <div className="mb-4 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveView('select')}
            className={cn(
              'rounded-md px-4 py-2 font-medium transition-colors',
              activeView === 'select'
                ? 'bg-primary text-primary-foreground shadow'
                : 'bg-muted text-muted-foreground hover:bg-muted/80',
            )}
          >
            1. Select Data Sources
          </button>
          <button
            onClick={() => setActiveView('results')}
            className={cn(
              'rounded-md px-4 py-2 font-medium transition-colors',
              activeView === 'results'
                ? 'bg-primary text-primary-foreground shadow'
                : 'bg-muted text-muted-foreground hover:bg-muted/80',
            )}
          >
            2. Review & Test Sources
          </button>
        </div>

        {activeView === 'select' ? (
          <SourceCatalog
            catalog={catalog}
            isLoading={catalogQuery.isLoading}
            error={catalogError}
            selectedSources={selectedSources}
            onToggleSource={handleToggleSource}
            onSelectAllInCategory={handleSelectAllInCategory}
          />
        ) : (
          <ResultsView
            parameters={parameters}
            currentSpaceId={currentSpaceId}
            catalog={catalog}
            results={testResults}
            isLoading={testsQuery.isLoading}
            selectedSourceIds={selectedSources}
            sourceParameters={sourceParameters}
            advancedSettings={sourceAdvancedSettings}
            defaultParameters={parameters}
            defaultAdvancedSettings={DEFAULT_ADVANCED_SOURCE_SETTINGS}
            onUpdateSourceParameters={handleSourceParametersChange}
            onUpdateAdvancedSettings={handleSourceAdvancedSettingsChange}
            onBackToSelect={() => setActiveView('select')}
            onAddToSpace={handleAddResultToSpace}
            onRunTest={handleRunSingleTest}
          />
        )}
      </DashboardSection>

      {activeView === 'select' && (
        <FloatingActionBar
          selectedCount={selectedSources.length}
          onGenerate={handleGenerateResults}
          isGenerating={isGenerating}
        />
      )}

      {presetBetaEnabled && (
        <Dialog open={isPresetDialogOpen} onOpenChange={setPresetDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Manage PubMed Presets</DialogTitle>
              <DialogDescription>
                Apply, share, or save the current advanced query configuration for future runs.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="max-h-48 overflow-y-auto rounded-lg border border-border/60">
                {presetsQuery.isLoading ? (
                  <p className="p-3 text-sm text-muted-foreground">Loading presets…</p>
                ) : presets.length === 0 ? (
                  <p className="p-3 text-sm text-muted-foreground">
                    No presets yet. Save your first preset below.
                  </p>
                ) : (
                  <div className="divide-y divide-border">
                    {presets.map((preset) => (
                      <div key={preset.id} className="flex flex-wrap items-center justify-between gap-3 p-3">
                        <div>
                          <p className="font-medium text-foreground">{preset.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {preset.scope === 'space' ? 'Shared with research space' : 'Personal preset'}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleLoadPreset(preset)}
                          >
                            Load
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={deletingPresetId === preset.id || deletePresetMutation.isPending}
                            onClick={() => handleDeletePreset(preset.id)}
                          >
                            {deletingPresetId === preset.id ? 'Deleting…' : 'Delete'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <Separator />

              <form className="space-y-3" onSubmit={handlePresetSubmit}>
                <div>
                  <Label htmlFor="presetName" className="text-sm text-foreground">
                    Preset Name
                  </Label>
                  <Input
                    id="presetName"
                    placeholder="e.g., MED13L cardiac literature"
                    value={newPresetName}
                    onChange={(event) => setNewPresetName(event.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="presetDescription" className="text-sm text-foreground">
                    Description (optional)
                  </Label>
                  <Textarea
                    id="presetDescription"
                    rows={3}
                    value={newPresetDescription}
                    onChange={(event) => setNewPresetDescription(event.target.value)}
                    placeholder="Brief note about the filters captured in this preset."
                  />
                </div>
                <div>
                  <Label className="text-sm text-foreground">Scope</Label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant={presetScope === 'user' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setPresetScope('user')}
                    >
                      Personal
                    </Button>
                    <Button
                      type="button"
                      variant={presetScope === 'space' ? 'default' : 'outline'}
                      size="sm"
                      disabled={!currentSpaceId}
                      onClick={() => currentSpaceId && setPresetScope('space')}
                    >
                      Research Space
                    </Button>
                  </div>
                  {presetScope === 'space' && !currentSpaceId && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Join a research space to share presets.
                    </p>
                  )}
                </div>

                <DialogFooter>
                  <Button type="submit" disabled={createPresetMutation.isPending}>
                    {createPresetMutation.isPending ? 'Saving…' : 'Save Preset'}
                  </Button>
                </DialogFooter>
              </form>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

function areArraysEqual(a: string[], b: string[]) {
  if (a.length !== b.length) return false
  const sortedA = [...a].sort()
  const sortedB = [...b].sort()
  return sortedA.every((value, index) => value === sortedB[index])
}

function isSameParameters(a: AdvancedQueryParameters, b: AdvancedQueryParameters) {
  return (
    a.gene_symbol === b.gene_symbol &&
    a.search_term === b.search_term &&
    a.date_from === b.date_from &&
    a.date_to === b.date_to &&
    a.max_results === b.max_results &&
    a.sort_by === b.sort_by &&
    a.additional_terms === b.additional_terms &&
    areArraysEqual(a.publication_types ?? [], b.publication_types ?? []) &&
    areArraysEqual(a.languages ?? [], b.languages ?? [])
  )
}

function validateParametersForSource(
  entry: SourceCatalogEntry,
  params: AdvancedQueryParameters,
): { ok: boolean; message?: string } {
  const paramType = normalizeParamType(entry.param_type)
  const hasGene = Boolean(params.gene_symbol && params.gene_symbol.trim().length > 0)
  const hasTerm = Boolean(params.search_term && params.search_term.trim().length > 0)

  switch (paramType) {
    case 'gene':
      return hasGene ? { ok: true } : { ok: false, message: 'A gene symbol is required' }
    case 'term':
      return hasTerm ? { ok: true } : { ok: false, message: 'A phenotype or search term is required' }
    case 'geneAndTerm':
      if (!hasGene && !hasTerm) {
        return { ok: false, message: 'Provide both a gene symbol and a phenotype term' }
      }
      if (!hasGene) {
        return { ok: false, message: 'Gene symbol required' }
      }
      if (!hasTerm) {
        return { ok: false, message: 'Phenotype/search term required' }
      }
      return { ok: true }
    case 'none':
      return { ok: true }
    case 'api':
      return hasGene || hasTerm
        ? { ok: true }
        : {
            ok: false,
            message: 'Provide at least one parameter before running this API source',
          }
    default:
      return { ok: true }
  }
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
