"use client"

import { useState } from 'react'
import { ArrowLeft, ExternalLink, Terminal, Loader2, FolderOpen, Database } from 'lucide-react'
import { useDataDiscoveryStore } from '@/lib/stores/data-discovery-store'
import { QueryParameters, QueryTestResult } from '@/lib/types/data-discovery'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { SpaceSelectorModal } from '@/components/research-spaces/SpaceSelectorModal'

interface ResultsViewProps {
  parameters: QueryParameters
  currentSpaceId: string | null
  onBackToSelect: () => void
}

export function ResultsView({ parameters, currentSpaceId, onBackToSelect }: ResultsViewProps) {
  const { testResults } = useDataDiscoveryStore()
  const [spaceSelectorOpen, setSpaceSelectorOpen] = useState(false)
  const [selectedResultForSpace, setSelectedResultForSpace] = useState<QueryTestResult | null>(null)

  const handleAddToSpace = (result: QueryTestResult) => {
    if (currentSpaceId) {
      // Add directly to current space
      handleAddToSpaceDirect(result, currentSpaceId)
    } else {
      // Show space selector
      setSelectedResultForSpace(result)
      setSpaceSelectorOpen(true)
    }
  }

  const handleAddToSpaceDirect = async (result: QueryTestResult, spaceId: string) => {
    try {
      // TODO: Implement API call to add source to space
      console.log(`Adding ${result.catalog_entry_id} to space ${spaceId}`)
      // Show success message
    } catch (error) {
      console.error('Failed to add source to space:', error)
      // Show error message
    }
  }

  const handleSpaceSelected = (spaceId: string) => {
    if (selectedResultForSpace) {
      handleAddToSpaceDirect(selectedResultForSpace, spaceId)
    }
    setSpaceSelectorOpen(false)
    setSelectedResultForSpace(null)
  }

  if (testResults.length === 0) {
    return (
      <Card className="text-center py-12">
        <CardContent>
          <FolderOpen className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-semibold text-foreground mb-2">
            No Results Generated
          </h2>
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
            {testResults.map((result) => (
              <ResultCard
                key={result.id}
                result={result}
                parameters={parameters}
                onAddToSpace={handleAddToSpace}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      <SpaceSelectorModal
        open={spaceSelectorOpen}
        onOpenChange={setSpaceSelectorOpen}
        onSpaceChange={handleSpaceSelected}
      />
    </>
  )
}

interface ResultCardProps {
  result: QueryTestResult
  parameters: QueryParameters
  onAddToSpace: (result: QueryTestResult) => void
}

function ResultCard({ result, parameters, onAddToSpace }: ResultCardProps) {
  const [isRunningApi, setIsRunningApi] = useState(false)
  const isApiResult = !result.response_url

  const handleRunApi = async () => {
    setIsRunningApi(true)
    // TODO: Implement actual API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsRunningApi(false)
  }

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
              <Database className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground">{result.catalog_entry_id}</h3>
              <p className="text-xs text-muted-foreground">Test ID: {result.id.slice(-8)}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 flex-shrink-0">
            {getStatusBadge(result.status)}

            {isParamMissing && (
              <span className="text-xs text-yellow-600 dark:text-yellow-400">
                Missing parameters
              </span>
            )}

            {/* Action Button */}
            {isApiResult ? (
              <Button
                onClick={handleRunApi}
                disabled={isParamMissing || isRunningApi}
                size="sm"
                className="flex items-center space-x-2"
              >
                {isRunningApi ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Terminal className="w-4 h-4" />
                )}
                <span>{isRunningApi ? 'Running...' : 'Run Analysis'}</span>
              </Button>
            ) : (
              <a
                href={result.response_url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className={`inline-flex items-center space-x-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  isParamMissing || !result.response_url
                    ? 'bg-muted text-muted-foreground cursor-not-allowed'
                    : 'bg-primary text-primary-foreground hover:bg-primary/90'
                }`}
                onClick={(e) => (isParamMissing || !result.response_url) && e.preventDefault()}
              >
                <span>Open Query</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            )}

            {/* Add to Space Button */}
            <Button
              onClick={() => onAddToSpace(result)}
              variant="outline"
              size="sm"
            >
              Add to Space
            </Button>
          </div>
        </div>

        {/* API Result Display */}
        {result.response_data && isApiResult && (
          <div className="mt-4 pt-4 border-t border-border">
            <h4 className="text-sm font-semibold text-foreground mb-2">
              Analysis Results:
            </h4>
            <div className="bg-muted rounded-lg p-3">
              <pre className="text-xs text-muted-foreground overflow-x-auto">
                {JSON.stringify(result.response_data, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Error Display */}
        {result.error_message && (
          <div className="mt-4 pt-4 border-t border-border">
            <h4 className="text-sm font-semibold text-destructive mb-2">
              Error:
            </h4>
            <p className="text-sm text-destructive">{result.error_message}</p>
          </div>
        )}

        {/* Metadata */}
        <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Started: {new Date(result.started_at).toLocaleTimeString()}
          </span>
          {result.execution_time_ms && (
            <span>
              Duration: {result.execution_time_ms}ms
            </span>
          )}
          {result.data_quality_score && (
            <span>
              Quality: {(result.data_quality_score * 100).toFixed(1)}%
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
