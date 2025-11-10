"use client"

import { useState } from 'react'
import {
  ArrowLeft,
  ExternalLink,
  Terminal,
  Loader2,
  FolderOpen,
  Database,
  BrainCircuit,
  ClipboardList,
  BookOpenText,
  TestTube2,
  Users,
  Library,
  Network,
} from 'lucide-react'
import type { QueryParameters, QueryTestResult, SourceCatalogEntry } from '@/lib/types/data-discovery'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { SpaceSelectorModal } from '@/components/research-spaces/SpaceSelectorModal'

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Genomic Variant Databases': Database,
  'Gene Expression & Functional Genomics': BrainCircuit,
  'Model Organism Databases': TestTube2,
  'Protein / Pathway Databases': Network,
  'Electronic Health Records (EHRs)': ClipboardList,
  'Rare Disease Registries': Users,
  'Clinical Trial Databases': TestTube2,
  'Phenotype Ontologies & Databases': ClipboardList,
  'Scientific Literature': BookOpenText,
  'Knowledge Graphs / Integrated Platforms': Network,
  'AI Predictive Models': BrainCircuit,
}

interface ResultsViewProps {
  parameters: QueryParameters
  currentSpaceId: string | null
  catalog: SourceCatalogEntry[]
  results: QueryTestResult[]
  isLoading: boolean
  onBackToSelect: () => void
  onAddToSpace: (result: QueryTestResult, spaceId: string) => Promise<void>
  onRunTest?: (catalogEntryId: string) => Promise<void>
}

export function ResultsView({
  parameters,
  currentSpaceId,
  catalog,
  results,
  isLoading,
  onBackToSelect,
  onAddToSpace,
  onRunTest,
}: ResultsViewProps) {
  const [spaceSelectorOpen, setSpaceSelectorOpen] = useState(false)
  const [selectedResultForSpace, setSelectedResultForSpace] = useState<QueryTestResult | null>(null)
  const [addingResultId, setAddingResultId] = useState<string | null>(null)
  const [runningResultId, setRunningResultId] = useState<string | null>(null)

  const handleAddToSpaceRequest = async (result: QueryTestResult) => {
    if (currentSpaceId) {
      await handleAddToSpace(result, currentSpaceId)
      return
    }
    setSelectedResultForSpace(result)
    setSpaceSelectorOpen(true)
  }

  const handleAddToSpace = async (result: QueryTestResult, spaceId: string) => {
    try {
      setAddingResultId(result.id)
      await onAddToSpace(result, spaceId)
    } catch (error) {
      console.error('Failed to add source to space', error)
    } finally {
      setAddingResultId(null)
    }
  }

  const handleSpaceSelected = async (spaceId: string) => {
    if (selectedResultForSpace) {
      await handleAddToSpace(selectedResultForSpace, spaceId)
    }
    setSelectedResultForSpace(null)
    setSpaceSelectorOpen(false)
  }

  const handleRunResult = async (result: QueryTestResult) => {
    if (!onRunTest) return
    try {
      setRunningResultId(result.id)
      await onRunTest(result.catalog_entry_id)
    } finally {
      setRunningResultId(null)
    }
  }

  if (isLoading) {
    return (
      <Card className="py-12 text-center">
        <CardContent>
          <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading generated results...</p>
        </CardContent>
      </Card>
    )
  }

  if (results.length === 0) {
    return (
      <Card className="text-center py-12">
        <CardContent>
          <FolderOpen className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-semibold text-foreground mb-2">No Results Generated</h2>
          <p className="text-muted-foreground mb-4">
            Go back to the &ldquo;Select Data Sources&rdquo; tab to choose sources and generate results.
          </p>
          <Button onClick={onBackToSelect}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Selection
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Generated Results</span>
            <Button variant="outline" size="sm" onClick={onBackToSelect}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Selection
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {results.map((result) => (
              <ResultCard
                key={result.id}
                result={result}
                parameters={parameters}
                catalog={catalog}
                onAddToSpace={() => handleAddToSpaceRequest(result)}
                onRunTest={onRunTest ? () => handleRunResult(result) : undefined}
                isAddingToSpace={addingResultId === result.id}
                isRunningTest={runningResultId === result.id}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      <SpaceSelectorModal
        open={spaceSelectorOpen}
        onOpenChange={setSpaceSelectorOpen}
        onSpaceChange={(spaceId) => handleSpaceSelected(spaceId)}
      />
    </>
  )
}

interface ResultCardProps {
  result: QueryTestResult
  parameters: QueryParameters
  catalog: SourceCatalogEntry[]
  onAddToSpace: () => Promise<void> | void
  onRunTest?: () => Promise<void> | void
  isRunningTest: boolean
  isAddingToSpace: boolean
}

function ResultCard({
  result,
  parameters,
  catalog,
  onAddToSpace,
  onRunTest,
  isRunningTest,
  isAddingToSpace,
}: ResultCardProps) {
  const isApiResult = !result.response_url
  const catalogEntry = catalog.find((entry) => entry.id === result.catalog_entry_id)
  const displayName = catalogEntry?.name || result.catalog_entry_id
  const category = catalogEntry?.category || 'Unknown'
  const IconComponent = CATEGORY_ICONS[category] || Database

  const getStatusBadge = (status: string) => {
    const variants = {
      success: 'default' as const,
      error: 'destructive' as const,
      pending: 'secondary' as const,
      timeout: 'outline' as const,
      validation_failed: 'destructive' as const,
    }
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
        {status.replace('_', ' ')}
      </Badge>
    )
  }

  const isParamMissing =
    (Boolean(result.parameters.gene_symbol) && !parameters.gene_symbol) ||
    (Boolean(result.parameters.search_term) && !parameters.search_term)

  return (
    <Card className="border-border">
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between w-full">
          <div className="flex items-center space-x-3 mb-3 md:mb-0">
            <div className="flex-shrink-0">
              <IconComponent className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground">{displayName}</h3>
              <p className="text-xs text-muted-foreground">
                {category} • Test ID: {result.id.slice(-8)}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 flex-shrink-0">
            {getStatusBadge(result.status)}

            {isParamMissing && <span className="text-xs text-yellow-600 dark:text-yellow-400">Missing parameters</span>}

            {isApiResult ? (
              <Button
                onClick={onRunTest}
                disabled={isParamMissing || isRunningTest}
                size="sm"
                className="flex items-center space-x-2"
              >
                {isRunningTest ? <Loader2 className="w-4 h-4 animate-spin" /> : <Terminal className="w-4 h-4" />}
                <span>{isRunningTest ? 'Running...' : 'Run API'}</span>
              </Button>
            ) : result.response_url ? (
              <Button asChild variant="outline" size="sm">
                <a
                  href={result.response_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>View Response</span>
                </a>
              </Button>
            ) : null}

            <Button variant="secondary" size="sm" onClick={onAddToSpace} disabled={isParamMissing || isAddingToSpace}>
              {isAddingToSpace ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Saving...
                </>
              ) : (
                'Add to Space'
              )}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-sm">
          <div>
            <p className="text-muted-foreground">Parameters Used</p>
            <p>Gene: {result.parameters.gene_symbol || '—'}</p>
            <p>Term: {result.parameters.search_term || '—'}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Results</p>
            <p>Status: {result.status}</p>
            <p>Quality Score: {result.data_quality_score?.toFixed(2) || '—'}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Execution</p>
            <p>Time: {result.execution_time_ms ? `${result.execution_time_ms} ms` : '—'}</p>
            <p>Completed: {result.completed_at ? new Date(result.completed_at).toLocaleString() : '—'}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
