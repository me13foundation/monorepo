"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import { AxiosError } from 'axios'
import { useSpaceContext } from '@/components/space-context-provider'
import type {
  QueryParameters,
  QueryTestResult,
  SourceCatalogEntry,
} from '@/lib/types/data-discovery'
import {
  useAddDiscoverySourceToSpace,
  useExecuteDataDiscoveryTest,
  useSessionTestResults,
} from '@/lib/queries/data-discovery'
import {
  useCreateSpaceDiscoverySession,
  useSetSpaceDiscoverySelections,
  useSpaceDiscoverySessions,
  useSpaceSourceCatalog,
  useToggleSpaceDiscoverySourceSelection,
  useUpdateSpaceDiscoverySessionParameters,
} from '@/lib/queries/space-discovery'
import { syncDiscoverySessionState } from '@/lib/state/discovery-session-sync'
import { PageHero, DashboardSection } from '@/components/ui/composition-patterns'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { ParameterBar } from '@/components/data-discovery/ParameterBar'
import { SourceParameterConfigurator } from '@/components/data-discovery/SourceParameterConfigurator'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'

const SourceCatalog = dynamic(
  () => import('@/components/data-discovery/SourceCatalog').then((mod) => ({ default: mod.SourceCatalog })),
  {
    ssr: false,
  },
)

const ResultsView = dynamic(
  () => import('@/components/data-discovery/ResultsView').then((mod) => ({ default: mod.ResultsView })),
  {
    ssr: false,
  },
)

const DEFAULT_PARAMETERS: QueryParameters = {
  gene_symbol: 'MED13L',
  search_term: 'atrial septal defect',
}

interface SpaceDiscoveryClientProps {
  spaceId: string
}

export default function SpaceDiscoveryClient({ spaceId }: SpaceDiscoveryClientProps) {
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const [parameters, setParameters] = useState<QueryParameters>(DEFAULT_PARAMETERS)
  const [sourceParameters, setSourceParameters] = useState<Record<string, QueryParameters>>({})
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const createRequestedRef = useRef(false)

  const { currentSpaceId } = useSpaceContext()
  const displaySpaceName = currentSpaceId === spaceId ? 'this space' : 'the selected space'

  const catalogQuery = useSpaceSourceCatalog(spaceId)
  const sessionsQuery = useSpaceDiscoverySessions(spaceId)
  const testsQuery = useSessionTestResults(activeSessionId)
  const refetchSessions = sessionsQuery.refetch

  const createSessionMutation = useCreateSpaceDiscoverySession(spaceId)
  const updateSessionParamsMutation = useUpdateSpaceDiscoverySessionParameters(spaceId)
  const toggleSourceMutation = useToggleSpaceDiscoverySourceSelection(spaceId)
  const executeTestMutation = useExecuteDataDiscoveryTest()
  const addToSpaceMutation = useAddDiscoverySourceToSpace()
  const setSelectionsMutation = useSetSpaceDiscoverySelections(spaceId)

  const {
    mutate: createSession,
    isPending: isCreatingSession,
    isError: isCreateSessionError,
  } = createSessionMutation

  const catalog: SourceCatalogEntry[] = useMemo(
    () => catalogQuery.data ?? [],
    [catalogQuery.data],
  )
  const testResults = testsQuery.data ?? []
  const catalogError = catalogQuery.error instanceof Error ? catalogQuery.error : null

  const catalogById = useMemo(() => {
    const map = new Map<string, SourceCatalogEntry>()
    catalog.forEach((entry) => {
      map.set(entry.id, entry)
    })
    return map
  }, [catalog])

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
  ])

  useEffect(() => {
    if (isCreateSessionError) {
      createRequestedRef.current = false
    }
  }, [isCreateSessionError])

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

  const handleParametersChange = useCallback(
    (newParams: QueryParameters) => {
      setParameters(newParams)
      if (!activeSessionId) {
        return
      }
      updateSessionParamsMutation.mutate({
        sessionId: activeSessionId,
        payload: { parameters: newParams },
      })
    },
    [activeSessionId, updateSessionParamsMutation],
  )

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

  const resolveExecutionContext = useCallback(
    (sourceId: string):
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

  const handleAddResultToSpace = useCallback(
    async (result: QueryTestResult, targetSpaceId: string) => {
      if (!activeSessionId) {
        toast.error('No discovery session available')
        return
      }

      try {
        await addToSpaceMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: {
            catalog_entry_id: result.catalog_entry_id,
            research_space_id: targetSpaceId,
            source_config: {},
          },
        })
        toast.success('Source added to research space')
      } catch (error) {
        console.error(error)
        toast.error('Failed to add source to space')
      }
    },
    [activeSessionId, addToSpaceMutation],
  )

  const handleGenerateResults = useCallback(async () => {
    if (!activeSessionId || selectedSources.length === 0) {
      toast.error('Select at least one data source before generating results')
      return
    }

    const executionPayloads: Array<{ sourceId: string; parameters: QueryParameters }> = []
    for (const sourceId of selectedSources) {
      const executionContext = resolveExecutionContext(sourceId)
      if (!executionContext) {
        return
      }
      executionPayloads.push({
        sourceId,
        parameters: executionContext.parameters,
      })
    }

    setIsGenerating(true)
    try {
      for (const payload of executionPayloads) {
        await executeTestMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: {
            catalog_entry_id: payload.sourceId,
            parameters: payload.parameters,
          },
        })
      }
      setActiveView('results')
      toast.success('Data discovery tests executed')
    } catch (error) {
      console.error(error)
      toast.error('Failed to execute discovery tests')
    } finally {
      setIsGenerating(false)
    }
  }, [activeSessionId, selectedSources, executeTestMutation, resolveExecutionContext])

  return (
    <div className="space-y-6">
      <PageHero
        title="Space Discovery Workbench"
        description={`Discover, test, and activate data sources curated for ${displaySpaceName}.`}
        variant="research"
        actions={<Badge variant="secondary">Space-scoped</Badge>}
      />

      <DashboardSection
        title="Query Parameters"
        description="Define default filters and tailor query requirements for every selected data source."
      >
        <div className="space-y-4">
          <ParameterBar parameters={parameters} onParametersChange={handleParametersChange} />
          <SourceParameterConfigurator
            catalog={catalog}
            selectedSourceIds={selectedSources}
            sourceParameters={sourceParameters}
            defaultParameters={parameters}
            onChange={handleSourceParametersChange}
          />
        </div>
      </DashboardSection>

      <DashboardSection
        title={activeView === 'select' ? 'Select Data Sources' : 'View Generated Results'}
        description={
          activeView === 'select'
            ? 'Browse the catalog and choose sources to test within this space.'
            : 'Review generated outputs and promote sources into spaces.'
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
            2. View Generated Results
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
            currentSpaceId={currentSpaceId ?? spaceId}
            catalog={catalog}
            results={testResults}
            isLoading={testsQuery.isLoading}
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
  const setB = new Set(b)
  return a.every((value) => setB.has(value))
}

function isSameParameters(a: QueryParameters, b: QueryParameters) {
  return a.gene_symbol === b.gene_symbol && a.search_term === b.search_term
}

function validateParametersForSource(
  entry: SourceCatalogEntry,
  params: QueryParameters,
): { ok: boolean; message?: string } {
  const hasGene = Boolean(params.gene_symbol && params.gene_symbol.trim().length > 0)
  const hasTerm = Boolean(params.search_term && params.search_term.trim().length > 0)

  switch (entry.param_type) {
    case 'gene':
      return hasGene ? { ok: true } : { ok: false, message: 'A gene symbol is required' }
    case 'term':
      return hasTerm ? { ok: true } : { ok: false, message: 'A phenotype or search term is required' }
    case 'geneAndTerm':
      if (!hasGene && !hasTerm) {
        return { ok: false, message: 'Provide both a gene symbol and a phenotype term' }
      }
      if (!hasGene) {
        return { ok: false, message: 'A gene symbol is required for this source' }
      }
      if (!hasTerm) {
        return { ok: false, message: 'A phenotype or search term is required for this source' }
      }
      return { ok: true }
    case 'none':
    case 'api':
      return { ok: true }
    default:
      return { ok: true }
  }
}
