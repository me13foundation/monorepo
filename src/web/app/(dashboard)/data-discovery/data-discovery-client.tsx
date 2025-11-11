"use client"

import { useCallback, useEffect, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import dynamic from 'next/dynamic'
import { ParameterBar } from '@/components/data-discovery/ParameterBar'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { CatalogSkeleton } from '@/components/data-discovery/CatalogSkeleton'
import { ResultsSkeleton } from '@/components/data-discovery/ResultsSkeleton'
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
import { PageHero, DashboardSection } from '@/components/ui/composition-patterns'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

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
  const [selectedSources, setSelectedSources] = useState<string[]>(initialSelectedSources)
  const [activeSessionId, setActiveSessionId] = useState<string | null>(initialSessionId)
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

  const handleRunTest = useCallback(
    async (sourceId: string) => {
      if (!activeSessionId) {
        toast.error('No discovery session available')
        return
      }

      setIsGenerating(true)
      try {
        await executeTestMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: {
            catalog_entry_id: sourceId,
            parameters,
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
    [activeSessionId, executeTestMutation, parameters],
  )

  const handleRunSingleTest = useCallback(
    async (sourceId: string) => {
      await handleRunTest(sourceId)
    },
    [handleRunTest],
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

    setIsGenerating(true)
    try {
      for (const sourceId of selectedSources) {
        await executeTestMutation.mutateAsync({
          sessionId: activeSessionId,
          payload: {
            catalog_entry_id: sourceId,
            parameters,
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
  }, [activeSessionId, selectedSources, executeTestMutation, parameters])

  return (
    <div className="space-y-6">
      <PageHero
        title="Data Source Discovery"
        description="Discover, test, and promote the highest-quality biomedical data sources for MED13 research workflows."
        variant="research"
        actions={<Badge variant="secondary">Workbench Beta</Badge>}
      />

      <DashboardSection
        title="Query Parameters"
        description="Tune gene and phenotype filters to personalize discovery runs."
      >
        <ParameterBar parameters={parameters} onParametersChange={handleParametersChange} />
      </DashboardSection>

      <DashboardSection
        title={activeView === 'select' ? 'Select Data Sources' : 'View Generated Results'}
        description={
          activeView === 'select'
            ? 'Browse the catalog and choose sources to test.'
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
            currentSpaceId={currentSpaceId}
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
