'use client'

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
import type { ResearchSpace } from '@/types/research-space'
import type { CurationQueueResponse, CurationStats } from '@/lib/api/research-spaces'
import { PageHero, StatCard, DashboardSection } from '@/components/ui/composition-patterns'
import { Button } from '@/components/ui/button'

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

  const spaceData = space as ResearchSpace | undefined
  const statsData = stats as CurationStats | undefined
  const queueData = queue as CurationQueueResponse | undefined
  const isLoading = spaceLoading || statsLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const statCards = [
    {
      title: 'Pending Review',
      value: statsData?.pending ?? 0,
      description: 'Items awaiting review',
      icon: <Clock className="h-4 w-4 text-muted-foreground" />,
    },
    {
      title: 'Approved',
      value: statsData?.approved ?? 0,
      description: 'Approved items',
      icon: <CheckCircle2 className="h-4 w-4 text-muted-foreground" />,
    },
    {
      title: 'Rejected',
      value: statsData?.rejected ?? 0,
      description: 'Rejected items',
      icon: <AlertCircle className="h-4 w-4 text-muted-foreground" />,
    },
    {
      title: 'Total Curated',
      value: statsData?.total ?? 0,
      description: 'All curated submissions',
      icon: <FileText className="h-4 w-4 text-muted-foreground" />,
    },
  ]

  return (
    <div className="space-y-6">
      <PageHero
        title="Data Curation"
        description={`Review and curate data for ${spaceData?.name ?? 'this research space'}`}
        variant="research"
        actions={
          <Button variant="outline" size="sm">
            Refresh Stats
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => (
          <StatCard
            key={card.title}
            title={card.title}
            value={card.value}
            description={card.description}
            icon={card.icon}
            isLoading={statsLoading}
          />
        ))}
      </div>

      <DashboardSection
        title="Curation Queue"
        description="Review and approve data items for this research space"
      >
        {queueLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : queueData && queueData.items.length > 0 ? (
          <div className="space-y-4">
            {queueData.items.map((item) => (
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
      </DashboardSection>
    </div>
  )
}
