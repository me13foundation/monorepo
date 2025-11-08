"use client"

import { useState } from 'react'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { Button } from '@/components/ui/button'
import { Loader2, ChevronDown, Folder } from 'lucide-react'
import { useSpaceContext } from '@/components/space-context-provider'
import { SpaceSelectorModal } from './SpaceSelectorModal'

interface SpaceSelectorProps {
  currentSpaceId?: string
  onSpaceChange?: (spaceId: string) => void
}

export function SpaceSelector({ currentSpaceId, onSpaceChange }: SpaceSelectorProps) {
  const { data, isLoading } = useResearchSpaces()
  const { currentSpaceId: contextSpaceId } = useSpaceContext()
  const [modalOpen, setModalOpen] = useState(false)
  const selectedSpaceId = currentSpaceId || contextSpaceId || ''

  const spaces = data?.spaces || []
  const currentSpace = spaces.find((s) => s.id === selectedSpaceId)

  if (isLoading) {
    return (
      <Button variant="outline" disabled>
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        <span className="text-sm">Loading...</span>
      </Button>
    )
  }

  if (spaces.length === 0) {
    return (
      <Button variant="outline" onClick={() => setModalOpen(true)}>
        <Folder className="h-4 w-4 mr-2" />
        <span className="text-sm">No spaces</span>
        <ChevronDown className="h-4 w-4 ml-2" />
      </Button>
    )
  }

  return (
    <>
      <Button
        variant="outline"
        onClick={() => setModalOpen(true)}
        className="w-full sm:w-auto sm:min-w-[200px] justify-between"
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Folder className="h-4 w-4 flex-shrink-0" />
          <div className="flex flex-col items-start flex-1 min-w-0">
            <span className="text-sm font-medium truncate w-full">
              {currentSpace?.name || 'Select a space'}
            </span>
            {currentSpace && (
              <span className="text-xs text-muted-foreground font-mono truncate w-full hidden sm:block">
                {currentSpace.slug}
              </span>
            )}
          </div>
        </div>
        <ChevronDown className="h-4 w-4 ml-2 flex-shrink-0" />
      </Button>
      <SpaceSelectorModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onSpaceChange={onSpaceChange}
      />
    </>
  )
}
