'use client'

import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { DashboardSection } from '@/components/ui/composition-patterns'
import { OrchestratedSessionState } from '@/types/generated'
import {
  useSpaceSourceCatalog,
  useSpaceDiscoverySessions,
  useCreateSpaceDiscoverySession,
  useAddDiscoverySourceToSpace,
} from '@/lib/queries/space-discovery'
import { useQueryClient } from '@tanstack/react-query'
import { dataSourceKeys } from '@/lib/query-keys/data-sources'
import { toast } from 'sonner'
import type { ValidationIssueDTO } from '@/types/generated'
import { Button } from '@/components/ui/button'
import type { AdvancedQueryParametersModel } from '@/types/generated'
import type { SourceCatalogEntry } from '@/lib/types/data-discovery'

const SourceCatalog = dynamic(
  () => import('@/components/data-discovery/SourceCatalog').then((mod) => ({ default: mod.SourceCatalog })),
  { ssr: false },
)

interface DataDiscoveryContentProps {
  spaceId: string
  isModal?: boolean
  // Props passed from Server Component
  sessionState?: OrchestratedSessionState
  catalog?: SourceCatalogEntry[]
  onComplete?: () => void
}

export function DataDiscoveryContent({
  spaceId,
  isModal = false,
  onComplete,
}: DataDiscoveryContentProps) {
  const [hasInitiatedCreate, setHasInitiatedCreate] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isAdding, setIsAdding] = useState(false)

  const { data: catalog = [], isLoading: catalogLoading } = useSpaceSourceCatalog(spaceId)
  const { data: sessions = [], isLoading: sessionsLoading } = useSpaceDiscoverySessions(spaceId)
  const createSession = useCreateSpaceDiscoverySession(spaceId)
  const addToSpace = useAddDiscoverySourceToSpace()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!sessionsLoading && sessions.length === 0 && !createSession.isPending && !hasInitiatedCreate) {
      setHasInitiatedCreate(true)
      createSession.mutate({
        name: 'New Discovery Session',
        initial_parameters: {
          gene_symbol: null,
          search_term: null,
        },
      })
    }
  }, [sessionsLoading, sessions.length, createSession, hasInitiatedCreate])

  const activeSession = sessions[0]

  useEffect(() => {
    const initialSelection = new Set(activeSession?.selected_sources ?? [])
    setSelectedIds(initialSelection)
  }, [activeSession?.selected_sources])

  const selectedSources = activeSession?.selected_sources || []
  const isValid = true // TODO: Implement validation logic based on session
  const validationIssues: ValidationIssueDTO[] = [] // TODO: Get from session validation
  const catalogById = React.useMemo(() => {
    const map = new Map<string, SourceCatalogEntry>()
    catalog.forEach((entry) => map.set(entry.id, entry))
    return map
  }, [catalog])

  const buildSourceConfig = (catalogEntryId: string): Record<string, unknown> => {
    const entry = catalogById.get(catalogEntryId)
    if (!activeSession || !entry) {
      return {}
    }

    if (entry.source_type === 'pubmed') {
      const params: AdvancedQueryParametersModel | undefined = activeSession.current_parameters
      const parts: string[] = []
      if (params?.gene_symbol?.trim()) {
        parts.push(params.gene_symbol.trim())
      }
      if (params?.search_term?.trim()) {
        parts.push(params.search_term.trim())
      }
      const query = parts.join(' ').trim() || 'MED13'
      return {
        metadata: {
          query,
          max_results: params?.max_results ?? 100,
          date_from: params?.date_from ?? null,
          date_to: params?.date_to ?? null,
          publication_types: params?.publication_types ?? [],
        },
      }
    }

    return {}
  }

  const handleAddSelectedToSpace = async () => {
    if (!activeSession) return
    if (selectedIds.size === 0) {
      toast.error('Select at least one source to add.')
      return
    }
    setIsAdding(true)
    const idsToPromote = Array.from(selectedIds)
    const results = await Promise.allSettled(
      idsToPromote.map((catalogEntryId) =>
        addToSpace.mutateAsync({
          sessionId: activeSession.id,
          catalogEntryId,
          researchSpaceId: spaceId,
          sourceConfig: buildSourceConfig(catalogEntryId),
          requestedBy: activeSession.owner_id,
        }),
      ),
    )

    const failed = results.filter((result) => result.status === 'rejected')
    if (failed.length === 0) {
      // Invalidate and explicitly refetch queries to update the UI immediately
      queryClient.invalidateQueries({
        queryKey: dataSourceKeys.space(spaceId),
      })
      // Explicitly refetch to ensure immediate update - this will refetch all matching queries
      queryClient.refetchQueries({
        queryKey: dataSourceKeys.space(spaceId),
        type: 'active',
      }).then(() => {
        setIsAdding(false)
        toast.success(
          idsToPromote.length === 1
            ? 'Source added to this space.'
            : `${idsToPromote.length} sources added to this space.`,
        )
        onComplete?.()
      })
    } else {
      setIsAdding(false)
      toast.error('Some sources could not be added. Please retry.')
    }
  }

  const SelectView = () => {
    if (catalogLoading || sessionsLoading) {
      return <div className="p-4 text-center text-muted-foreground">Loading...</div>
    }

    if (catalog.length === 0) {
      return <div className="p-4 text-center text-muted-foreground">No sources available</div>
    }

    if (!activeSession) {
      return <div className="p-4 text-center text-muted-foreground">Initializing session...</div>
    }

    const categoryCounts = catalog.reduce<Record<string, number>>((counts, entry) => {
      const current = counts[entry.category] ?? 0
      counts[entry.category] = current + 1
      return counts
    }, {})

    const sessionState: OrchestratedSessionState = {
      session: activeSession,
      capabilities: {},
      validation: { is_valid: isValid, issues: validationIssues },
      view_context: {
        selected_count: selectedSources.length,
        total_available: catalog.length,
        can_run_search: isValid && selectedSources.length > 0,
        categories: categoryCounts,
      },
    }

    return (
      <SourceCatalog
        entries={catalog}
        orchestratedState={sessionState}
        spaceId={spaceId}
        onSelectionChange={setSelectedIds}
      />
    )
  }

  const ModalLayout = ({ children }: { children: React.ReactNode }) => (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-hidden">
        <div className="h-full p-1">
          {children}
        </div>
      </div>
      <div className="border-t bg-background p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-muted-foreground">
            {selectedIds.size} source{selectedIds.size === 1 ? '' : 's'} selected
          </div>
          <Button
            onClick={handleAddSelectedToSpace}
            disabled={isAdding || selectedIds.size === 0 || addToSpace.isPending}
          >
            {isAdding || addToSpace.isPending ? 'Adding...' : 'Add selected to space'}
          </Button>
        </div>
      </div>
    </div>
  )

  const StandardLayout = ({ children }: { children: React.ReactNode }) => (
    <div className="space-y-6">
      <DashboardSection
        title="Select Sources"
        description="Pick sources to add directly to this research space"
      >
        {children}
      </DashboardSection>
    </div>
  )

  const Layout = isModal ? ModalLayout : StandardLayout

  return <Layout><SelectView /></Layout>
}
