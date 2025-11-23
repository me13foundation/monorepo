"use client"

import React, { useEffect, useMemo, useState } from 'react'
import { OrchestratedSessionState } from '@/types/generated'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Check } from 'lucide-react'
import { toast } from 'sonner'
import { ValidationFeedback } from '@/components/shared/ValidationFeedback'
import { useSetSpaceDiscoverySelections } from '@/lib/queries/space-discovery'
import { useQueryClient } from '@tanstack/react-query'
import { spaceDiscoveryKeys } from '@/lib/query-keys/space-discovery'
import type { DataDiscoverySession } from '@/lib/types/data-discovery'
import type { SourceCatalogEntry } from '@/lib/types/data-discovery'

interface SourceCatalogProps {
  entries: SourceCatalogEntry[]
  orchestratedState: OrchestratedSessionState
  spaceId: string
}

export function SourceCatalog({ entries, orchestratedState, spaceId }: SourceCatalogProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(
    () => new Set(orchestratedState.session.selected_sources),
  )
  const issues = orchestratedState.validation?.issues || []
  const isValid = orchestratedState.validation?.is_valid

  useEffect(() => {
    setSelectedIds(new Set(orchestratedState.session.selected_sources))
  }, [orchestratedState.session.selected_sources])

  const queryClient = useQueryClient()
  const setSelections = useSetSpaceDiscoverySelections(spaceId)
  const isPending = setSelections.isPending

  const categories = useMemo(() => {
    const groups: Record<string, SourceCatalogEntry[]> = {}
    entries.forEach((entry) => {
      if (!groups[entry.category]) groups[entry.category] = []
      groups[entry.category].push(entry)
    })
    return groups
  }, [entries])

  const handleToggleSource = async (sourceId: string) => {
    const previousSelection = new Set(selectedIds)
    const expectedSelection = new Set(selectedIds)

    if (expectedSelection.has(sourceId)) {
      expectedSelection.delete(sourceId)
    } else {
      expectedSelection.add(sourceId)
    }

    setSelectedIds(expectedSelection)

    try {
      const updatedSession = await setSelections.mutateAsync({
        sessionId: orchestratedState.session.id,
        sourceIds: Array.from(expectedSelection),
      })

      const updatedSelection = new Set(updatedSession.selected_sources)
      setSelectedIds(updatedSelection)

      queryClient.setQueryData<DataDiscoverySession[] | undefined>(
        spaceDiscoveryKeys.sessions(spaceId),
        (previousSessions) => {
          if (!previousSessions) {
            return [updatedSession]
          }
          return previousSessions.map((session) =>
            session.id === updatedSession.id ? updatedSession : session,
          )
        },
      )

      const expectedHasId = expectedSelection.has(sourceId)
      const updatedHasId = updatedSelection.has(sourceId)
      if (expectedHasId !== updatedHasId) {
        toast.error(
          'Selection not applied. Add the required query parameters before selecting this source.',
        )
      }
    } catch (error) {
      setSelectedIds(previousSelection)
      const message = error instanceof Error ? error.message : 'Failed to update selection'
      toast.error(message)
    }
  }

  return (
    <div className="space-y-6">
      <div data-testid="catalog-debug">CATALOG RENDERED with {entries.length} entries</div>
      {!isValid && issues.length > 0 && <ValidationFeedback issues={issues} />}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(categories).map(([category, sources]) => (
          <Card key={category} className="border-t-4 border-t-primary/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium uppercase text-muted-foreground">
                {category}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {sources.map((source) => {
                const isSelected = selectedIds.has(source.id)
                return (
                  <div
                    key={source.id}
                    onClick={() => !isPending && handleToggleSource(source.id)}
                    className={`
                      flex cursor-pointer items-center justify-between rounded-md border p-3 transition-all
                      ${
                        isSelected
                          ? 'border-primary bg-primary/10 shadow-sm'
                          : 'border-border bg-card hover:bg-accent'
                      }
                      ${isPending ? 'cursor-wait opacity-50' : ''}
                    `}
                  >
                    <div>
                      <div className="text-sm font-medium">{source.name}</div>
                      <div className="line-clamp-1 text-xs text-muted-foreground">
                        {source.description}
                      </div>
                    </div>
                    {isSelected && <Check className="size-4 text-primary" />}
                  </div>
                )
              })}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
