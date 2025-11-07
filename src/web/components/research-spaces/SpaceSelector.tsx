"use client"

import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { Select } from '@/components/ui/select'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { useSpaceContext } from '@/components/space-context-provider'

interface SpaceSelectorProps {
  currentSpaceId?: string
  onSpaceChange?: (spaceId: string) => void
}

export function SpaceSelector({ currentSpaceId, onSpaceChange }: SpaceSelectorProps) {
  const router = useRouter()
  const { data, isLoading } = useResearchSpaces()
  const { currentSpaceId: contextSpaceId, setCurrentSpaceId } = useSpaceContext()
  const selectedSpaceId = currentSpaceId || contextSpaceId || ''

  const handleSpaceChange = (spaceId: string) => {
    setCurrentSpaceId(spaceId)
    if (onSpaceChange) {
      onSpaceChange(spaceId)
    } else {
      // Default behavior: navigate to space detail
      router.push(`/spaces/${spaceId}`)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Loading spaces...</span>
      </div>
    )
  }

  const spaces = data?.spaces || []
  const currentSpace = spaces.find((s) => s.id === selectedSpaceId)

  if (spaces.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        No spaces available
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="space-selector" className="text-sm font-medium">
        Space:
      </label>
      <Select
        id="space-selector"
        value={selectedSpaceId}
        onChange={(e) => handleSpaceChange(e.target.value)}
        className="min-w-[200px]"
      >
        {spaces.map((space) => (
          <option key={space.id} value={space.id}>
            {space.name}
          </option>
        ))}
      </Select>
      {currentSpace && (
        <span className="text-xs text-muted-foreground font-mono">
          {currentSpace.slug}
        </span>
      )}
    </div>
  )
}
