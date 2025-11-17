"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import dynamic from 'next/dynamic'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { CatalogSkeleton } from '@/components/data-discovery/CatalogSkeleton'
import { ResultsSkeleton } from '@/components/data-discovery/ResultsSkeleton'
import { useSpaceContext } from '@/components/space-context-provider'
import type { QueryParameters, QueryTestResult, SourceCatalogEntry } from '@/lib/types/data-discovery'
import {
  useAddDiscoverySourceToSpace,
  useCreateDataDiscoverySession,
  useDataDiscoverySessions,
  useExecuteDataDiscoveryTest,
  useSessionTestResults,
  useSourceCatalog,
  useToggleDataDiscoverySourceSelection,
  useSetDataDiscoverySelections,
} from '@/lib/queries/data-discovery'
import { toast } from 'sonner'
import { syncDiscoverySessionState } from '@/lib/state/discovery-session-sync'
import { PageHero, DashboardSection } from '@/components/ui/composition-patterns'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
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

const DEFAULT_PARAMETERS: QueryParameters = {
  gene_symbol: 'MED13L',
  search_term: 'atrial septal defect',
}

interface DataDiscoveryClientProps {
  initialSessionId: string | null
  initialParameters: QueryParameters | null
  initialSelectedSources: string[]
}

export default function DataDiscoveryClient({
  initialSessionId,
  initialParameters,
  initialSelectedSources,
}: DataDiscoveryClientProps) {
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const [parameters, setParameters] = useState<QueryParameters>(initialParameters ?? DEFAULT_PARAMETERS)
  const [sourceParameters, setSourceParameters] = useState<Record<string, QueryParameters>>({})
  const [sourceAdvancedSettings, setSourceAdvancedSettings] = useState<Record<string, SourceAdvancedSettings>>({})
  const [selectedSources, setSelectedSources] = useState<string[]>(initialSelectedSources)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(initialSessionId)
  const [isGenerating, setIsGenerating] = useState(false)
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
    if (isCreateSessionError) {
      createRequestedRef.current = false
    }
  }, [isCreateSessionError])

  const getParametersForSource = useCallback(
    (sourceId: string) => sourceParameters[sourceId] ?? parameters,
    [sourceParameters, parameters],
  )

  const handleSourceParametersChange = useCallback(
    (sourceId: string, nextParams: QueryParameters) => {
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
          parameters: QueryParameters
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

  return (
    <div className="space-y-6">
      <PageHero
        title="Data Source Discovery"
        description="Discover, test, and promote the highest-quality biomedical data sources for MED13 research workflows."
        variant="research"
        actions={<Badge variant="secondary">Workbench Beta</Badge>}
      />

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
    </div>
  )
}

function areArraysEqual(a: string[], b: string[]) {
  if (a.length !== b.length) return false
  const sortedA = [...a].sort()
  const sortedB = [...b].sort()
  return sortedA.every((value, index) => value === sortedB[index])
}

function isSameParameters(a: QueryParameters, b: QueryParameters) {
  return (
    a.gene_symbol === b.gene_symbol &&
    a.search_term === b.search_term
  )
}

function validateParametersForSource(
  entry: SourceCatalogEntry,
  params: QueryParameters,
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
