'use client'

import React, { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { DashboardSection } from '@/components/ui/composition-patterns'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { cn } from '@/lib/utils'
import { OrchestratedSessionState, SourceCatalogEntry } from '@/types/generated'
import {
  useSpaceSourceCatalog,
  useSpaceDiscoverySessions,
  useCreateSpaceDiscoverySession
} from '@/lib/queries/space-discovery'
import { ValidationIssueDTO } from '@/types/generated'

const SourceCatalog = dynamic(
  () => import('@/components/data-discovery/SourceCatalog').then((mod) => ({ default: mod.SourceCatalog })),
  { ssr: false },
)

const ResultsView = dynamic(
  () => import('@/components/data-discovery/ResultsView').then((mod) => ({ default: mod.ResultsView })),
  { ssr: false },
)

interface DataDiscoveryContentProps {
  spaceId: string
  isModal?: boolean
  // Props passed from Server Component
  sessionState?: OrchestratedSessionState
  catalog?: SourceCatalogEntry[]
}

export function DataDiscoveryContent({
  spaceId,
  isModal = false,
}: DataDiscoveryContentProps) {
  // View state only (tabs/navigation)
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const [isGenerating, setIsGenerating] = useState(false)
  const [hasInitiatedCreate, setHasInitiatedCreate] = useState(false)

  // Fetch data using hooks
  const { data: catalog = [], isLoading: catalogLoading } = useSpaceSourceCatalog(spaceId)
  const { data: sessions = [], isLoading: sessionsLoading } = useSpaceDiscoverySessions(spaceId)
  const createSession = useCreateSpaceDiscoverySession(spaceId)

  // Ensure active session exists
  useEffect(() => {
    if (!sessionsLoading && sessions.length === 0 && !createSession.isPending && !hasInitiatedCreate) {
      setHasInitiatedCreate(true)
      createSession.mutate({})
    }
  }, [sessionsLoading, sessions.length, createSession, hasInitiatedCreate])

  const activeSession = sessions[0]

  // Derived state from active session
  const selectedSources = activeSession?.selected_sources || []
  const isValid = true // TODO: Implement validation logic based on session
  const validationIssues: ValidationIssueDTO[] = [] // TODO: Get from session validation

  const handleGenerateResults = () => {
    setIsGenerating(true)
    setActiveView('results')
    // In a real implementation, this would trigger a job
    setTimeout(() => setIsGenerating(false), 1000)
  }

  // Pure UI components - no business logic
  const ViewNavigation = () => (
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
        disabled={!isValid && selectedSources.length === 0}
      >
        2. Review & Test Sources
      </button>
    </div>
  )

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
      />
    )
  }

  const ResultsViewComponent = () => (
    // Placeholder for simplified results view
    // In a full implementation, this would also be a dumb component receiving state
    <div className="p-4">
       <h3 className="text-lg font-medium">Results View (Placeholder)</h3>
       <p>This view would display results for session test-session</p>
    </div>
  )

  const Content = (
    <>
      <ViewNavigation />
      {activeView === 'select' ? <SelectView /> : <ResultsViewComponent />}
    </>
  )

  // Layout components - pure UI composition
  const ModalLayout = ({ children }: { children: React.ReactNode }) => (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-hidden">
        <div className="h-full p-1">
          {children}
        </div>
      </div>
      {activeView === 'select' && (
        <div className="mt-4">
          <FloatingActionBar
            selectedCount={selectedSources.length}
            onGenerate={handleGenerateResults}
            isGenerating={isGenerating}
            disabled={!isValid}
          />
        </div>
      )}
    </div>
  )

  const StandardLayout = ({ children }: { children: React.ReactNode }) => (
    <div className="space-y-6">
      <DashboardSection
        title={activeView === 'select' ? "Select Sources" : "Review Results"}
        description="Configure your data discovery session"
      >
        {children}
      </DashboardSection>

      {activeView === 'select' && (
        <div className="mt-4">
          <FloatingActionBar
            selectedCount={selectedSources.length}
            onGenerate={handleGenerateResults}
            isGenerating={isGenerating}
            disabled={!isValid}
          />
        </div>
      )}
    </div>
  )

  const Layout = isModal ? ModalLayout : StandardLayout

  return <Layout>{Content}</Layout>
}
