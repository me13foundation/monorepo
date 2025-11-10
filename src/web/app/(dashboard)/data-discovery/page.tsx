"use client"

import { useCallback, useEffect, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import { DataDiscoveryHeader } from '@/components/data-discovery/DataDiscoveryHeader'
import { ParameterBar } from '@/components/data-discovery/ParameterBar'
import { SourceCatalog } from '@/components/data-discovery/SourceCatalog'
import { ResultsView } from '@/components/data-discovery/ResultsView'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { useSpaceContext } from '@/components/space-context-provider'
import type { QueryParameters, QueryTestResult } from '@/lib/types/data-discovery'
import {
  useAddDiscoverySourceToSpace,
  useCreateDataDiscoverySession,
  useDataDiscoverySessions,
  useExecuteDataDiscoveryTest,
  useSessionTestResults,
  useSourceCatalog,
  useToggleDataDiscoverySourceSelection,
  useUpdateDataDiscoverySessionParameters,
  useSetDataDiscoverySelections,
} from '@/lib/queries/data-discovery'
import { toast } from 'sonner'
import { syncDiscoverySessionState } from '@/lib/state/discovery-session-sync'

const DEFAULT_PARAMETERS: QueryParameters = {
  gene_symbol: 'MED13L',
  search_term: 'atrial septal defect',
}

export default function DataDiscoveryPage() {
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const [parameters, setParameters] = useState<QueryParameters>(DEFAULT_PARAMETERS)
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const createRequestedRef = useRef(false)

  const { currentSpaceId } = useSpaceContext()

  const catalogQuery = useSourceCatalog()
  const sessionsQuery = useDataDiscoverySessions()
  const testsQuery = useSessionTestResults(activeSessionId)
  const refetchSessions = sessionsQuery.refetch

  const createSessionMutation = useCreateDataDiscoverySession()
  const updateSessionParamsMutation = useUpdateDataDiscoverySessionParameters()
  const toggleSourceMutation = useToggleDataDiscoverySourceSelection()
  const executeTestMutation = useExecuteDataDiscoveryTest()
  const addToSpaceMutation = useAddDiscoverySourceToSpace()
  const setSelectionsMutation = useSetDataDiscoverySelections()
  const {
    mutate: createSession,
    isPending: isCreatingSession,
    isError: isCreateSessionError,
  } = createSessionMutation

  const catalog = catalogQuery.data ?? []
  const testResults = testsQuery.data ?? []
  const catalogError = catalogQuery.error instanceof Error ? catalogQuery.error : null

  // Initialize or adopt existing session
  useEffect(() => {
    if (!sessionsQuery.isSuccess) {
      return
    }

    const {
      nextSessionId,
      nextParameters,
      nextSelectedSources,
      shouldCreateSession,
    } = syncDiscoverySessionState(sessionsQuery.data ?? [])

    if (shouldCreateSession) {
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

  const handleGenerateResults = useCallback(async () => {
    if (!activeSessionId || selectedSources.length === 0) {
      toast.error('Select at least one data source before generating results')
      return
    }

    setIsGenerating(true)
    try {
      for (const sourceId of selectedSources) {
        await executeTestMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: { catalog_entry_id: sourceId },
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
  }, [activeSessionId, selectedSources, executeTestMutation])

  const handleRunSingleTest = useCallback(
    async (catalogEntryId: string) => {
      if (!activeSessionId) {
        return
      }
      try {
        await executeTestMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: { catalog_entry_id: catalogEntryId },
        })
        toast.success('Test executed')
      } catch (error) {
        console.error(error)
        toast.error('Failed to execute test')
      }
    },
    [activeSessionId, executeTestMutation],
  )

  const handleAddResultToSpace = useCallback(
    async (result: QueryTestResult, spaceId: string) => {
      if (!activeSessionId) {
        throw new Error('Session required before adding sources')
      }
      try {
        await addToSpaceMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: {
            catalog_entry_id: result.catalog_entry_id,
            research_space_id: spaceId,
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

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <DataDiscoveryHeader />

        <ParameterBar parameters={parameters} onParametersChange={handleParametersChange} />

        <div className="flex space-x-2 mb-6">
          <button
            onClick={() => setActiveView('select')}
            className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
              activeView === 'select'
                ? 'bg-card text-foreground border-b-2 border-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
          >
            1. Select Data Sources
          </button>
          <button
            onClick={() => setActiveView('results')}
            className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
              activeView === 'results'
                ? 'bg-card text-foreground border-b-2 border-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
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
            currentSpaceId={currentSpaceId}
            catalog={catalog}
            results={testResults}
            isLoading={testsQuery.isLoading}
            onBackToSelect={() => setActiveView('select')}
            onAddToSpace={handleAddResultToSpace}
            onRunTest={handleRunSingleTest}
          />
        )}
      </div>

      {activeView === 'select' && (
        <FloatingActionBar selectedCount={selectedSources.length} onGenerate={handleGenerateResults} isGenerating={isGenerating} />
      )}
    </div>
  )
}

function areArraysEqual(first: string[], second: string[]): boolean {
  if (first === second) {
    return true
  }
  if (first.length !== second.length) {
    return false
  }

  return first.every((value, index) => value === second[index])
}

function isSameParameters(left: QueryParameters, right: QueryParameters): boolean {
  return left.gene_symbol === right.gene_symbol && left.search_term === right.search_term
}
