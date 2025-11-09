'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useSpaceContext } from '@/components/space-context-provider'
import { useParams } from 'next/navigation'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  useResearchSpace,
  useSpaceCurationStats,
  useSpaceCurationQueue,
} from '@/lib/queries/research-spaces'
import { Loader2, FileText, CheckCircle2, Clock, AlertCircle } from 'lucide-react'

export default function SpaceCurationPage() {
  const params = useParams()
  const spaceId = params.spaceId as string
  const { setCurrentSpaceId } = useSpaceContext()
  const { data: space, isLoading: spaceLoading } = useResearchSpace(spaceId)
  const { data: stats, isLoading: statsLoading } = useSpaceCurationStats(spaceId)
  const { data: queue, isLoading: queueLoading } = useSpaceCurationQueue(spaceId, {
    limit: 10,
  })

  useEffect(() => {
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }
  }, [spaceId, setCurrentSpaceId])

  const isLoading = spaceLoading || statsLoading

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div>
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Data Curation</h1>
          <p className="text-muted-foreground mt-1">
            Review and curate data for {space?.name || 'this research space'}
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.pending ?? 0}</div>
              <p className="text-xs text-muted-foreground">Items awaiting review</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approved</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.approved ?? 0}</div>
              <p className="text-xs text-muted-foreground">Approved items</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Rejected</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.rejected ?? 0}</div>
              <p className="text-xs text-muted-foreground">Rejected items</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total ?? 0}</div>
              <p className="text-xs text-muted-foreground">Total curated items</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Curation Queue</CardTitle>
            <CardDescription>
              Review and approve data items for this research space
            </CardDescription>
          </CardHeader>
          <CardContent>
            {queueLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : queue && queue.items.length > 0 ? (
              <div className="space-y-4">
                {queue.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="font-medium">
                        {item.entity_type} - {item.entity_id}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Priority: {item.priority} • Status: {item.status}
                        {item.quality_score !== null && ` • Score: ${item.quality_score}`}
                      </div>
                    </div>
                    {item.last_updated && (
                      <div className="text-xs text-muted-foreground">
                        {new Date(item.last_updated).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No curation items yet</h3>
                <p className="text-muted-foreground mb-4">
                  Start curating data by connecting data sources and reviewing imported items.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  )
}
