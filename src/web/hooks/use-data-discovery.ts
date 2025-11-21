'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import { useSpaceContext } from '@/components/space-context-provider'
import type {
  AdvancedQueryParameters,
  QueryParameterCapabilities,
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
} from '@/lib/queries/space-discovery'
import { syncDiscoverySessionState } from '@/lib/state/discovery-session-sync'
import { toast } from 'sonner'
import {
  createDefaultAdvancedSettings,
  DEFAULT_ADVANCED_SETTINGS as DEFAULT_ADVANCED_SOURCE_SETTINGS,
  type SourceAdvancedSettings,
} from '@/components/data-discovery/advanced-settings'

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
  variation_types: [],
  clinical_significance: [],
  is_reviewed: null,
  organism: null,
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

export function useDataDiscoveryController(spaceId: string) {
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const [parameters, setParameters] = useState<AdvancedQueryParameters>(DEFAULT_PARAMETERS)
  const [sourceParameters, setSourceParameters] = useState<
    Record<string, AdvancedQueryParameters>
  >({})
  const [sourceAdvancedSettings, setSourceAdvancedSettings] = useState<
    Record<string, SourceAdvancedSettings>
  >({})
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
            ...(caps.supported_storage_use_cases || []),
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
  }, [catalogById, selectedSources])

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
    setParameters((current) => {
      let changed = false
      const next: AdvancedQueryParameters = { ...current }
      // Validation logic to reset unsupported parameters
      if (!activeCapabilities.supports_date_range) {
        if (next.date_from) { next.date_from = null; changed = true }
        if (next.date_to) { next.date_to = null; changed = true }
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
      if (!activeCapabilities.supports_variation_type && next.variation_types?.length) {
        next.variation_types = []
        changed = true
      }
      if (!activeCapabilities.supports_clinical_significance && next.clinical_significance?.length) {
        next.clinical_significance = []
        changed = true
      }
      if (!activeCapabilities.supports_review_status && next.is_reviewed !== null) {
        next.is_reviewed = null
        changed = true
      }
      if (!activeCapabilities.supports_organism && next.organism) {
        next.organism = null
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
      if (!activeSessionId) return
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
      if (!activeSessionId) return
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
      if (!activeSessionId || sourceIds.length === 0) return
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
    (sourceId: string, nextParams: AdvancedQueryParameters) => {
      setSourceParameters((prev) => ({ ...prev, [sourceId]: nextParams }))
    },
    [],
  )

  const handleSourceAdvancedSettingsChange = useCallback(
    (sourceId: string, nextSettings: SourceAdvancedSettings) => {
      setSourceAdvancedSettings((prev) => ({ ...prev, [sourceId]: nextSettings }))
    },
    [],
  )

  const resolveExecutionContext = useCallback(
    (sourceId: string): { parameters: AdvancedQueryParameters; catalogEntry: SourceCatalogEntry } | null => {
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
      if (!executionContext) return
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

  const handleRunSingleTest = useCallback(async (sourceId: string) => {
    await handleRunTest(sourceId)
  }, [handleRunTest])

  const buildSourceConfigPayload = useCallback(
    (catalogEntryId: string) => {
      const settings = sourceAdvancedSettings[catalogEntryId]
      if (!settings) return {}
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

  return {
    activeView,
    setActiveView,
    catalog,
    catalogError,
    catalogQuery,
    testResults,
    testsQuery,
    selectedSources,
    handleToggleSource,
    handleSelectAllInCategory,
    currentSpaceId: currentSpaceId ?? spaceId,
    parameters,
    sourceParameters,
    sourceAdvancedSettings,
    DEFAULT_ADVANCED_SOURCE_SETTINGS,
    handleSourceParametersChange,
    handleSourceAdvancedSettingsChange,
    handleRunSingleTest,
    handleAddResultToSpace,
    handleGenerateResults,
    isGenerating,
  }
}

function areArraysEqual(a: string[], b: string[]) {
  if (a.length !== b.length) return false
  const setB = new Set(b)
  return a.every((value) => setB.has(value))
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
        return { ok: false, message: 'A gene symbol is required for this source' }
      }
      if (!hasTerm) {
        return { ok: false, message: 'A phenotype or search term is required for this source' }
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
