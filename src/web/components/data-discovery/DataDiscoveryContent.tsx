'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { DashboardSection } from '@/components/ui/composition-patterns'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { cn } from '@/lib/utils'
import { OrchestratedSessionState, SourceCatalogEntry } from '@/types/generated'

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
  sessionState,
  catalog = []
}: DataDiscoveryContentProps) {
  // View state only (tabs/navigation)
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const [isGenerating, setIsGenerating] = useState(false)

  // Derived from server state (no complex calculation)
  const selectedSources = sessionState?.session.selected_sources || []
  const isValid = sessionState?.validation?.is_valid ?? false
  const validationIssues = sessionState?.validation?.issues || []
  const parameters = sessionState?.session.current_parameters

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

  const SelectView = () => (
    sessionState ? (
      <SourceCatalog
        entries={catalog}
        orchestratedState={sessionState}
      />
    ) : (
      <div className="p-4 text-center text-muted-foreground">Loading session...</div>
    )
  )

  const ResultsViewComponent = () => (
    // Placeholder for simplified results view
    // In a full implementation, this would also be a dumb component receiving state
    <div className="p-4">
       <h3 className="text-lg font-medium">Results View (Placeholder)</h3>
       <p>This view would display results for session {sessionState?.session.id}</p>
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
