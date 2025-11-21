'use client'

import dynamic from 'next/dynamic'
import { useDataDiscoveryController } from '@/hooks/use-data-discovery'
import { DashboardSection } from '@/components/ui/composition-patterns'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { cn } from '@/lib/utils'

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
}

export function DataDiscoveryContent({ spaceId, isModal = false }: DataDiscoveryContentProps) {
  const {
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
    currentSpaceId,
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
  } = useDataDiscoveryController(spaceId)

  const Content = (
    <>
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
    </>
  )

  if (isModal) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-1 overflow-hidden">
          <div className="h-full p-1">
            {Content}
          </div>
        </div>
        {activeView === 'select' && (
          <div className="mt-4">
            <FloatingActionBar
              selectedCount={selectedSources.length}
              onGenerate={handleGenerateResults}
              isGenerating={isGenerating}
            />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <DashboardSection
        title={activeView === 'select' ? 'Select Data Sources' : 'Review & Run Tests'}
        description={
          activeView === 'select'
            ? 'Browse the catalog and choose sources to test within this space.'
            : 'Individually configure, execute, and promote each selected source in this space.'
        }
      >
        {Content}
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
