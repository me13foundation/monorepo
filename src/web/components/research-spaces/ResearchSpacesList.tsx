"use client"

import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { ResearchSpaceCard } from './ResearchSpaceCard'
import { Button } from '@/components/ui/button'
import { Plus, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { Input } from '@/components/ui/input'
import { useState } from 'react'

export function ResearchSpacesList() {
  const [searchQuery, setSearchQuery] = useState('')
  const { data, isLoading, error } = useResearchSpaces()

  const filteredSpaces = data?.spaces.filter((space) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      space.name.toLowerCase().includes(query) ||
      space.slug.toLowerCase().includes(query) ||
      space.description.toLowerCase().includes(query)
    )
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Research Spaces</h1>
            <p className="text-muted-foreground mt-1">
              Manage your research workspaces and teams
            </p>
          </div>
          <Button asChild>
            <Link href="/spaces/new">
              <Plus className="h-4 w-4 mr-2" />
              Create Space
            </Link>
          </Button>
        </div>
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive mb-4">
            Failed to load research spaces: {error.message}
          </p>
          <Button asChild>
            <Link href="/spaces/new">
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Space
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Research Spaces</h1>
          <p className="text-muted-foreground mt-1">
            Manage your research workspaces and teams
          </p>
        </div>
        <Button asChild>
          <Link href="/spaces/new">
            <Plus className="h-4 w-4 mr-2" />
            Create Space
          </Link>
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search spaces by name, slug, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-sm"
          />
        </div>
      </div>

      {filteredSpaces && filteredSpaces.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <p className="text-muted-foreground mb-4">
            {searchQuery
              ? 'No spaces match your search.'
              : 'No research spaces found.'}
          </p>
          {!searchQuery && (
            <Button asChild>
              <Link href="/spaces/new">
                <Plus className="h-4 w-4 mr-2" />
                Create your first space
              </Link>
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredSpaces?.map((space) => (
            <ResearchSpaceCard key={space.id} space={space} />
          ))}
        </div>
      )}

      {data && data.total > data.spaces.length && (
        <div className="text-center text-sm text-muted-foreground">
          Showing {data.spaces.length} of {data.total} spaces
        </div>
      )}
    </div>
  )
}
