'use client'

import { useMemo, useState, useTransition } from 'react'
import type { OrchestratedSessionState, SourceCatalogEntry } from '@/types/generated'
import { updateSourceSelection } from '@/app/actions/data-discovery'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, Loader2 } from 'lucide-react'
import { ValidationFeedback } from '@/components/shared/ValidationFeedback'
import { toast } from 'sonner'

interface DataDiscoveryClientProps {
  orchestratedState: OrchestratedSessionState
  catalog: SourceCatalogEntry[]
}

export default function DataDiscoveryClient({
  orchestratedState,
  catalog,
}: DataDiscoveryClientProps) {
  const [state, setState] = useState<OrchestratedSessionState>(orchestratedState)
  const [isPending, startTransition] = useTransition()

  const selectedIds = useMemo(() => new Set(state.session.selected_sources), [state.session.selected_sources])

  const groupedCatalog = useMemo(() => {
    const groups: Record<string, SourceCatalogEntry[]> = {}
    catalog.forEach((entry) => {
      const key = entry.category || 'Uncategorized'
      if (!groups[key]) {
        groups[key] = []
      }
      groups[key].push(entry)
    })
    return groups
  }, [catalog])

  const handleToggle = (sourceId: string) => {
    const next = new Set(selectedIds)
    if (next.has(sourceId)) {
      next.delete(sourceId)
    } else {
      next.add(sourceId)
    }

    startTransition(async () => {
      const result = await updateSourceSelection(
        state.session.id,
        Array.from(next),
        '/data-discovery',
      )

      if (!result.success || !result.state) {
        toast.error(result.error ?? 'Failed to update selection')
        return
      }

      setState(result.state)
    })
  }

  const issues = state.validation?.issues ?? []
  const isValid = state.validation?.is_valid !== false

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Data Discovery</h1>
          <p className="text-muted-foreground">
            Select sources to orchestrate searches; backend derives capabilities and validation.
          </p>
        </div>
        {!isValid && issues.length > 0 ? (
          <Badge variant="destructive">Validation issues</Badge>
        ) : (
          <Badge variant="outline">Ready</Badge>
        )}
      </div>

      {!isValid && issues.length > 0 && (
        <ValidationFeedback issues={issues} />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(groupedCatalog).map(([category, entries]) => (
          <Card key={category} className="border-t-4 border-t-primary/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium uppercase text-muted-foreground">
                {category}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {entries.map((entry) => {
                const isSelected = selectedIds.has(entry.id)
                return (
                  <button
                    key={entry.id}
                    type="button"
                    onClick={() => handleToggle(entry.id)}
                    className={`flex w-full items-center justify-between rounded-md border p-3 text-left transition-all ${
                      isSelected
                        ? 'border-primary bg-primary/10 shadow-sm'
                        : 'border-border bg-card hover:bg-accent'
                    }`}
                    disabled={isPending}
                  >
                    <div>
                      <div className="text-sm font-medium">{entry.name}</div>
                      <div className="line-clamp-1 text-xs text-muted-foreground">
                        {entry.description}
                      </div>
                    </div>
                    {isPending && isSelected ? (
                      <Loader2 className="size-4 animate-spin text-primary" />
                    ) : (
                      isSelected && <Check className="size-4 text-primary" />
                    )}
                  </button>
                )
              })}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium text-foreground">Session overview</div>
            <div>Selected sources: {state.view_context.selected_count}</div>
            <div>Total available: {state.view_context.total_available}</div>
          </div>
          <Button variant="outline" disabled={!state.view_context.can_run_search}>
            {state.view_context.can_run_search ? 'Run search (backend orchestrated)' : 'Select at least one source'}
          </Button>
        </div>
      </div>
    </div>
  )
}
