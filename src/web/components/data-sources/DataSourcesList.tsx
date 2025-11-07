"use client"

import { useState } from 'react'
import { useSpaceDataSources, useCreateDataSourceInSpace } from '@/lib/queries/data-sources'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Plus, Database, Loader2 } from 'lucide-react'
import { CreateDataSourceDialog } from './CreateDataSourceDialog'
import type { DataSource } from '@/types/data-source'

interface DataSourcesListProps {
  spaceId: string
}

const statusColors: Record<string, string> = {
  active: 'bg-green-500',
  inactive: 'bg-gray-500',
  draft: 'bg-yellow-500',
  error: 'bg-red-500',
  pending_review: 'bg-blue-500',
  archived: 'bg-gray-400',
}

export function DataSourcesList({ spaceId }: DataSourcesListProps) {
  const { data, isLoading, error } = useSpaceDataSources(spaceId)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-destructive">
            Failed to load data sources: {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </CardContent>
      </Card>
    )
  }

  const dataSources = data?.data_sources || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            {data?.total || 0} data source{data?.total !== 1 ? 's' : ''} in this space
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Data Source
        </Button>
      </div>

      {dataSources.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No data sources</h3>
              <p className="text-muted-foreground mb-4">
                Get started by creating your first data source for this research space.
              </p>
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Data Source
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {dataSources.map((source: DataSource) => (
            <Card key={source.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{source.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {source.description || 'No description'}
                    </CardDescription>
                  </div>
                  <Badge
                    className={`${statusColors[source.status] || 'bg-gray-500'} text-white`}
                  >
                    {source.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Type:</span>
                    <span className="font-medium">{source.source_type}</span>
                  </div>
                  {source.tags && source.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {source.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <CreateDataSourceDialog
        spaceId={spaceId}
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />
    </div>
  )
}
