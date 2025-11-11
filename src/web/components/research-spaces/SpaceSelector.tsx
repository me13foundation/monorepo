"use client"

import { useState } from 'react'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { Button } from '@/components/ui/button'
import { Loader2, ChevronDown, Folder } from 'lucide-react'
import { useSpaceContext } from '@/components/space-context-provider'
import { SpaceSelectorModal } from './SpaceSelectorModal'
import type { ResearchSpaceListResponse } from '@/types/research-space'

interface SpaceSelectorProps {
  currentSpaceId?: string
  onSpaceChange?: (spaceId: string) => void
}

export function SpaceSelector({ currentSpaceId, onSpaceChange }: SpaceSelectorProps) {
  const { data, isLoading } = useResearchSpaces()
  const { currentSpaceId: contextSpaceId } = useSpaceContext()
  const [modalOpen, setModalOpen] = useState(false)
  const selectedSpaceId = currentSpaceId || contextSpaceId || ''

  const spacesResponse = data as ResearchSpaceListResponse | undefined
  const spaces = spacesResponse?.spaces ?? []
  const currentSpace = spaces.find((space) => space.id === selectedSpaceId)

  if (isLoading) {
    return (
      <Button variant="outline" disabled>
        <Loader2 className="mr-2 size-4 animate-spin" />
        <span className="text-sm">Loading...</span>
      </Button>
    )
  }

  if (spaces.length === 0) {
    return (
      <Button variant="outline" onClick={() => setModalOpen(true)}>
        <Folder className="mr-2 size-4" />
        <span className="text-sm">No spaces</span>
        <ChevronDown className="ml-2 size-4" />
      </Button>
    )
  }

  return (
    <>
      <Button
        variant="outline"
        onClick={() => setModalOpen(true)}
        className="w-full justify-between sm:w-auto sm:min-w-[200px]"
      >
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <Folder className="size-4 shrink-0" />
          <div className="flex min-w-0 flex-1 flex-col items-start">
            <span className="w-full truncate text-sm font-medium">
              {currentSpace?.name || 'Select a space'}
            </span>
            {currentSpace && (
              <span className="hidden w-full truncate font-mono text-xs text-muted-foreground sm:block">
                {currentSpace.slug}
              </span>
            )}
          </div>
        </div>
        <ChevronDown className="ml-2 size-4 shrink-0" />
      </Button>
      <SpaceSelectorModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onSpaceChange={onSpaceChange}
      />
    </>
  )
}
