"use client"

import { useState } from 'react'
import { DataDiscoveryHeader } from '@/components/data-discovery/DataDiscoveryHeader'
import { ParameterBar } from '@/components/data-discovery/ParameterBar'
import { SourceCatalog } from '@/components/data-discovery/SourceCatalog'
import { ResultsView } from '@/components/data-discovery/ResultsView'
import { FloatingActionBar } from '@/components/data-discovery/FloatingActionBar'
import { useDataDiscoveryStore } from '@/lib/stores/data-discovery-store'
import { useSpaceContext } from '@/components/space-context-provider'
import { QueryParameters } from '@/lib/types/data-discovery'

export default function DataDiscoveryPage() {
  const [activeView, setActiveView] = useState<'select' | 'results'>('select')
  const { parameters, updateParameters, selectedSources, generateResults } = useDataDiscoveryStore()
  const { currentSpaceId } = useSpaceContext()

  const handleParametersChange = (newParams: QueryParameters) => {
    updateParameters(newParams)
  }

  const handleGenerateResults = () => {
    generateResults()
    setActiveView('results')
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <DataDiscoveryHeader />

        <ParameterBar
          parameters={parameters}
          onParametersChange={handleParametersChange}
        />

        {/* View Tabs */}
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

        {/* Main Content */}
        {activeView === 'select' ? (
          <SourceCatalog />
        ) : (
          <ResultsView
            parameters={parameters}
            currentSpaceId={currentSpaceId}
            onBackToSelect={() => setActiveView('select')}
          />
        )}
      </div>

      {/* Floating Action Bar */}
      {activeView === 'select' && (
        <FloatingActionBar
          selectedCount={selectedSources.length}
          onGenerate={handleGenerateResults}
        />
      )}
    </div>
  )
}
