"use client"

import { useState, useMemo } from 'react'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { useRouter } from 'next/navigation'
import { useSpaceContext } from '@/components/space-context-provider'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader2, Search, Folder, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SpaceSelectorModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSpaceChange?: (spaceId: string) => void
}

export function SpaceSelectorModal({
  open,
  onOpenChange,
  onSpaceChange,
}: SpaceSelectorModalProps) {
  const router = useRouter()
  const { data, isLoading } = useResearchSpaces()
  const { currentSpaceId, setCurrentSpaceId } = useSpaceContext()
  const [searchQuery, setSearchQuery] = useState('')

  // Filter spaces based on search query
  const filteredSpaces = useMemo(() => {
    const spaces = data?.spaces || []
    if (!searchQuery.trim()) {
      return spaces
    }
    const query = searchQuery.toLowerCase()
    return spaces.filter(
      (space) =>
        space.name.toLowerCase().includes(query) ||
        space.slug.toLowerCase().includes(query) ||
        space.description?.toLowerCase().includes(query)
    )
  }, [data?.spaces, searchQuery])

  const handleSpaceSelect = (spaceId: string) => {
    setCurrentSpaceId(spaceId)
    if (onSpaceChange) {
      onSpaceChange(spaceId)
    } else {
      router.push(`/spaces/${spaceId}`)
    }
    onOpenChange(false)
    setSearchQuery('')
  }

  const handleCreateNew = () => {
    onOpenChange(false)
    router.push('/spaces/new')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col p-0 [&>button]:hidden w-[95vw] sm:w-full">
        <DialogHeader className="px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4 border-b">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0">
            <div>
              <DialogTitle className="text-lg sm:text-xl font-semibold">Select a space</DialogTitle>
              <DialogDescription className="sr-only">
                Choose a research space to work with or create a new one
              </DialogDescription>
            </div>
            <Button onClick={handleCreateNew} size="sm" className="w-full sm:w-auto">
              <Plus className="h-4 w-4 mr-2" />
              New space
            </Button>
          </div>
        </DialogHeader>

        <div className="flex flex-col flex-1 min-h-0">
          {/* Search Bar */}
          <div className="px-4 sm:px-6 pt-3 sm:pt-4 pb-2 sm:pb-3 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search spaces"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
                autoFocus
              />
            </div>
          </div>

          {/* Spaces List - Table-like layout */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Loading spaces...</span>
              </div>
            ) : filteredSpaces.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center px-4 sm:px-6">
                <Folder className="h-10 w-10 sm:h-12 sm:w-12 text-muted-foreground mb-4" />
                <p className="text-sm text-muted-foreground">
                  {searchQuery
                    ? 'No spaces found matching your search'
                    : 'No spaces available'}
                </p>
              </div>
            ) : (
              <div className="px-4 sm:px-6 py-2">
                {/* Table Header - Hidden on mobile */}
                <div className="hidden sm:grid grid-cols-[1fr_auto_auto] gap-4 px-3 py-2 text-xs font-medium text-muted-foreground border-b">
                  <div>Name</div>
                  <div>Type</div>
                  <div className="text-right">ID</div>
                </div>
                {/* Table Rows */}
                <div className="divide-y">
                  {filteredSpaces.map((space) => {
                    const isSelected = space.id === currentSpaceId
                    return (
                      <button
                        key={space.id}
                        onClick={() => handleSpaceSelect(space.id)}
                        className={cn(
                          'w-full flex flex-col sm:grid sm:grid-cols-[1fr_auto_auto] sm:gap-4 px-3 py-3 hover:bg-accent transition-colors text-left',
                          isSelected && 'bg-accent/50'
                        )}
                      >
                        <div className="flex flex-col min-w-0 sm:contents">
                          <div className="flex items-center gap-2 mb-1 sm:mb-0">
                            <span className="text-sm font-medium text-foreground truncate">
                              {space.name}
                            </span>
                            {isSelected && (
                              <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary whitespace-nowrap">
                                Current
                              </span>
                            )}
                          </div>
                          {space.description && (
                            <span className="text-xs text-muted-foreground truncate mb-2 sm:hidden">
                              {space.description}
                            </span>
                          )}
                        </div>
                        <div className="hidden sm:flex items-center">
                          <span className="text-xs text-muted-foreground">Space</span>
                        </div>
                        <div className="flex items-center justify-between sm:justify-end">
                          <span className="text-xs text-muted-foreground font-mono sm:hidden">
                            Slug: {space.slug}
                          </span>
                          <span className="hidden sm:inline text-xs text-muted-foreground font-mono">
                            {space.slug}
                          </span>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="px-4 sm:px-6 py-3 sm:py-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="w-full sm:w-auto">
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
