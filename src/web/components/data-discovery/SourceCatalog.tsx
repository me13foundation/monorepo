"use client"

import React from 'react'
import { SourceCatalogEntry, OrchestratedSessionState } from '@/types/generated'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Check } from 'lucide-react'
import { useTransition } from 'react'
import { updateSourceSelection } from '@/app/actions/data-discovery'
import { usePathname } from 'next/navigation'
import { toast } from 'sonner'
import { ValidationFeedback } from '@/components/shared/ValidationFeedback'

interface SourceCatalogProps {
  entries: SourceCatalogEntry[]
  orchestratedState: OrchestratedSessionState
}

export function SourceCatalog({ entries, orchestratedState }: SourceCatalogProps) {
  const [isPending, startTransition] = useTransition()
  const pathname = usePathname()

  const selectedIds = new Set(orchestratedState.session.selected_sources)
  const issues = orchestratedState.validation?.issues || []
  const isValid = orchestratedState.validation?.is_valid

  // Organize sources by category (View Logic, but simple grouping)
  const categories = React.useMemo(() => {
    const groups: Record<string, SourceCatalogEntry[]> = {}
    entries.forEach(entry => {
      if (!groups[entry.category]) groups[entry.category] = []
      groups[entry.category].push(entry)
    })
    return groups
  }, [entries])

  const handleToggleSource = (sourceId: string) => {
    startTransition(async () => {
      const newSelection = new Set(selectedIds)
      if (newSelection.has(sourceId)) {
        newSelection.delete(sourceId)
      } else {
        newSelection.add(sourceId)
      }

      const result = await updateSourceSelection(
        orchestratedState.session.id,
        Array.from(newSelection),
        pathname
      )

      if (!result.success) {
        toast.error(result.error || "Failed to update selection")
      }
    })
  }

  return (
    <div className="space-y-6">
      {/* Validation Feedback Area */}
      {!isValid && issues.length > 0 && (
        <ValidationFeedback issues={issues} />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(categories).map(([category, sources]) => (
          <Card key={category} className="border-t-4 border-t-primary/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium uppercase text-muted-foreground">
                {category}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {sources.map(source => {
                const isSelected = selectedIds.has(source.id)
                return (
                  <div
                    key={source.id}
                    onClick={() => !isPending && handleToggleSource(source.id)}
                    className={`
                      flex cursor-pointer items-center justify-between rounded-md border p-3 transition-all
                      ${isSelected
                        ? 'border-primary bg-primary/10 shadow-sm'
                        : 'border-border bg-card hover:bg-accent'}
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
